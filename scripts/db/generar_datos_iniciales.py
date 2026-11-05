"""Genera database/02_datos_iniciales.sql y database/03_verificacion.sql desde los CSV del profesor.

Uso: python scripts/db/generar_datos_iniciales.py datos/profesor database
Carga SOLO el estado inicial (todas las órdenes «Recibida»): los cambios de estado se hacen
con el código del sistema, como pide el paquete del profesor (ADR-013).
"""
import csv
import sys
from decimal import Decimal
from pathlib import Path

DATOS, SALIDA = Path(sys.argv[1]), Path(sys.argv[2])


def leer(nombre):
    with open(DATOS / nombre, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def q(texto):
    return "'" + str(texto).replace("'", "''") + "'"


actores = leer("actores.csv")
catalogo = leer("catalogo.csv")
operaciones = leer("operaciones.csv")
detalle = leer("detalle_operaciones.csv")
por_actor = {a["actor_id"]: a for a in actores}

EMPLEADOS = [("EMP-001", "Laura Méndez", "Asesor"), ("EMP-002", "Carlos Ruiz", "Técnico"),
             ("EMP-003", "Diego Salinas", "Técnico"), ("EMP-004", "Patricia Garza", "Gerente"),
             ("EMP-005", "Jorge Treviño", "Compras"), ("EMP-006", "Sofía Leal", "Caja")]

o = ["-- =============================================================================",
     "-- AutoFix Pro · Datos iniciales (PIA v3.0)",
     "-- Generado por scripts/db/generar_datos_iniciales.py desde datos/profesor/*.csv",
     "-- (paquete 06_AutoFix_Pro/01_Alumno, datos FICTICIOS). Ejecutar después de 01_esquema.sql.",
     "-- Solo el estado inicial: las 60 órdenes quedan «Recibida»; los cambios de estado se hacen con la API.",
     "-- Conversión documentada en docs/datos-profesor/README.md y ADR-013.",
     "-- =============================================================================", "", "BEGIN;", "",
     "-- Empleados de demostración (los tokens van en variables de entorno, no aquí)",
     "INSERT INTO empleados (id, nombre, rol) VALUES"]
o.append(",\n".join(f"    ({q(i)}, {q(n)}, {q(r)})" for i, n, r in EMPLEADOS) + ";")

o += ["", f"-- Clientes particulares ({len(actores)} propietarios de actores.csv; teléfono y correo ficticios)",
      "INSERT INTO clientes (id, nombre, telefono, correo, tipo) VALUES"]
filas = []
for a in actores:
    n = int(a["actor_id"].split("C")[-1])
    filas.append(f"    ({q(a['actor_id'])}, {q(a['nombre'])}, {q(f'81-0000-{n:04d}')}, "
                 f"{q(a['actor_id'].lower() + '@ejemplo.test')}, 'Particular')")
o.append(",\n".join(filas) + ";")

o += ["", f"-- Vehículos ficticios: uno por operación, placas derivadas de «referencia» ({len(operaciones)})",
      "INSERT INTO vehiculos (placas, vin, marca, modelo, anio, id_cliente) VALUES"]
filas = []
for op in operaciones:
    n = int(op["operacion_id"].split("O")[-1])
    placas = op["referencia"].replace("_", "").upper()
    filas.append(f"    ({q(placas)}, {q(f'AUT{n:014d}')}, 'Ficticia', 'Referencia', 2020, {q(op['actor_id'])})")
o.append(",\n".join(filas) + ";")

o += ["", f"-- Órdenes de Servicio en estado inicial «Recibida» ({len(operaciones)}); folio = operacion_id",
      "INSERT INTO ordenes (numero, id_cliente, es_cliente_de_flotilla, placas, asesor, motivo_de_ingreso, estado,",
      "                     fecha_ingreso, ultima_actualizacion, fecha_ingreso_a_fila) VALUES"]
filas = []
for op in operaciones:
    fecha = f"{op['fecha_solicitud']} 09:00:00-06:00"
    placas = op["referencia"].replace("_", "").upper()
    filas.append(f"    ({q(op['operacion_id'])}, {q(op['actor_id'])}, FALSE, {q(placas)}, 'EMP-001', "
                 f"{q('Servicio de referencia ' + op['referencia'])}, 'Recibida', {q(fecha)}, {q(fecha)}, {q(fecha)})")
o.append(",\n".join(filas) + ";")

o += ["", f"-- Catálogo de referencia del profesor ({len(catalogo)} servicios)",
      "INSERT INTO catalogo_servicios (recurso_id, descripcion, precio_mxn, capacidad_o_stock, habilitado) VALUES"]
o.append(",\n".join(f"    ({q(c['recurso_id'])}, {q(c['descripcion'])}, {Decimal(c['precio_mxn']):.2f}, "
                    f"{int(c['capacidad_o_stock'])}, {'TRUE' if c['habilitado'] == '1' else 'FALSE'})" for c in catalogo) + ";")

o += ["", f"-- Detalle de referencia de cada operación ({len(detalle)} líneas)",
      "INSERT INTO servicios_solicitados (numero_orden, recurso_id, cantidad) VALUES"]
o.append(",\n".join(f"    ({q(d['operacion_id'])}, {q(d['recurso_id'])}, {int(d['cantidad'])})" for d in detalle) + ";")

o += ["", "-- Columnas del profesor sin equivalente en el BRD (solo referencia para los oráculos)",
      "INSERT INTO referencia_operaciones_profesor (numero_orden, actor_activo, actor_preferente, promocion_activa, autorizado, referencia) VALUES"]
filas = []
for op in operaciones:
    a = por_actor[op["actor_id"]]
    b = lambda v: "TRUE" if v == "1" else "FALSE"  # noqa: E731
    filas.append(f"    ({q(op['operacion_id'])}, {b(a['activo'])}, {b(a['es_preferente'])}, {b(op['promocion_activa'])}, "
                 f"{b(op['autorizado'])}, {q(op['referencia'])})")
o.append(",\n".join(filas) + ";")
o += ["", "COMMIT;", ""]
(SALIDA / "02_datos_iniciales.sql").write_text("\n".join(o), encoding="utf-8")

totales = {}
for d in detalle:
    precio = Decimal(next(c["precio_mxn"] for c in catalogo if c["recurso_id"] == d["recurso_id"]))
    totales[d["operacion_id"]] = totales.get(d["operacion_id"], Decimal("0")) + precio * int(d["cantidad"])
suma = sum(totales.values())
v = ["-- AutoFix Pro · Verificación de la carga (ejecutar después de 01 y 02). Cada fila muestra lo obtenido y lo esperado.",
     "SELECT 'empleados' AS tabla, COUNT(*) AS obtenido, 6 AS esperado FROM empleados",
     f"UNION ALL SELECT 'clientes', COUNT(*), {len(actores)} FROM clientes",
     f"UNION ALL SELECT 'vehiculos', COUNT(*), {len(operaciones)} FROM vehiculos",
     f"UNION ALL SELECT 'ordenes «Recibida»', COUNT(*), {len(operaciones)} FROM ordenes WHERE estado = 'Recibida'",
     f"UNION ALL SELECT 'catalogo_servicios', COUNT(*), {len(catalogo)} FROM catalogo_servicios",
     f"UNION ALL SELECT 'servicios inhabilitados', COUNT(*), {sum(1 for c in catalogo if c['habilitado'] != '1')} FROM catalogo_servicios WHERE NOT habilitado",
     f"UNION ALL SELECT 'servicios_solicitados', COUNT(*), {len(detalle)} FROM servicios_solicitados",
     f"UNION ALL SELECT 'órdenes sin detalle', COUNT(*), {len(operaciones) - len(totales)} FROM ordenes o WHERE NOT EXISTS (SELECT 1 FROM servicios_solicitados s WHERE s.numero_orden = o.numero)",
     f"UNION ALL SELECT 'no autorizadas', COUNT(*), {sum(1 for op in operaciones if op['autorizado'] != '1')} FROM referencia_operaciones_profesor WHERE NOT autorizado",
     "UNION ALL SELECT 'secuencias', COUNT(*), 3 FROM secuencias;",
     "",
     f"-- Total de referencia de todas las operaciones (precio × cantidad): debe dar {suma:.2f}",
     "SELECT SUM(c.precio_mxn * s.cantidad) AS total_referencia FROM servicios_solicitados s JOIN catalogo_servicios c USING (recurso_id);",
     "",
     f"-- Operación con mayor total: debe ser {max(totales, key=totales.get)} con {max(totales.values()):.2f}",
     "SELECT s.numero_orden, SUM(c.precio_mxn * s.cantidad) AS total FROM servicios_solicitados s JOIN catalogo_servicios c USING (recurso_id)",
     "GROUP BY s.numero_orden ORDER BY total DESC LIMIT 1;", ""]
(SALIDA / "03_verificacion.sql").write_text("\n".join(v), encoding="utf-8")
print("ok", len(actores), len(operaciones), len(detalle), f"{suma:.2f}")
