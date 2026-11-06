"""Fuente única del esquema de la base de datos de AutoFix Pro (PostgreSQL 16 / Supabase).

Genera:
  database/01_esquema.sql                       (tablas, restricciones, índices, comentarios, RLS)
  docs/architecture/diagramas/modelo-de-datos.puml
  docs/architecture/modelo-de-datos.md

Uso: python scripts/db/esquema.py .        (desde la raíz del repositorio)
"""
import sys
from pathlib import Path

RAIZ = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

ESTADOS_ORDEN = ["Recibida", "En Diagnóstico", "Cotizada", "Autorizada", "En Reparación", "En Espera de Refacción",
                 "Pausada por Retiro de Vehículo", "Lista para Entrega", "Pagada", "Por Cobrar (Crédito)", "Cerrada",
                 "Cerrada sin Reparación", "Cancelada"]
ESTADOS_COTIZACION = ["Pendiente de Aprobación Gerencial", "Requiere Ajuste", "Pendiente de Autorización del Cliente",
                      "Autorizada", "Autorizada Parcialmente", "Rechazada"]
ESTADOS_TRABAJO = ["Pendiente", "En Progreso", "Completado", "No Autorizado"]
ESTADOS_SOLICITUD = ["Solicitada", "Disponible"]
ROLES = ["Asesor", "Técnico", "Gerente", "Compras", "Caja"]
COMBUSTIBLE = ["Reserva", "1/4", "1/2", "3/4", "Lleno"]
FORMAS_DE_PAGO = ["Efectivo", "Tarjeta", "Transferencia"]


def lista(valores):
    return ", ".join("'" + v.replace("'", "''") + "'" for v in valores)


# Cada columna: (nombre, tipo, nulo, por_defecto, comentario)
# Cada tabla: nombre, descripción, columnas, pk, fks [(cols, tabla, cols_ref, on_delete)], uniques, checks, índices
T = []


def tabla(nombre, descripcion, columnas, pk, fks=(), uniques=(), checks=(), indices=(), grupo="Dominio"):
    T.append(dict(nombre=nombre, descripcion=descripcion, columnas=columnas, pk=pk, fks=list(fks),
                  uniques=list(uniques), checks=list(checks), indices=list(indices), grupo=grupo))


TS = "TIMESTAMPTZ"
MXN = "NUMERIC(12,2)"

tabla("empleados", "Empleados del taller (Aggregate Empleado). Los tokens de acceso NO se guardan aquí: vienen de variables de entorno (ADR-012).", [
    ("id", "VARCHAR(20)", False, None, "Identificador del empleado (EMP-001…)"),
    ("nombre", "VARCHAR(120)", False, None, "Nombre completo"),
    ("rol", "VARCHAR(20)", False, None, "RolDeEmpleado"),
], ["id"], checks=[f"rol IN ({lista(ROLES)})"])

tabla("clientes", "Clientes particulares o de flotilla (Aggregate Cliente).", [
    ("id", "VARCHAR(20)", False, None, "Identificador (AUT-C001 en los datos del profesor)"),
    ("nombre", "VARCHAR(120)", False, None, "Nombre del cliente o razón social"),
    ("telefono", "VARCHAR(20)", True, None, "Teléfono de contacto"),
    ("correo", "VARCHAR(120)", True, None, "Correo de contacto"),
    ("tipo", "VARCHAR(20)", False, "'Particular'", "TipoCliente: Particular o Flotilla"),
    ("empresa", "VARCHAR(120)", True, None, "Empresa (solo flotilla)"),
    ("responsable_nombre", "VARCHAR(120)", True, None, "Responsable de Flotilla (solo flotilla)"),
    ("responsable_telefono", "VARCHAR(20)", True, None, "Teléfono del Responsable de Flotilla"),
    ("responsable_correo", "VARCHAR(120)", True, None, "Correo del Responsable de Flotilla"),
], ["id"], checks=[
    "tipo IN ('Particular', 'Flotilla')",
    "tipo = 'Particular' OR (empresa IS NOT NULL AND responsable_nombre IS NOT NULL)",
], indices=[("ix_clientes_empresa", "empresa")])

tabla("vehiculos", "Vehículos (Aggregate Vehículo). Las placas se guardan normalizadas: mayúsculas, sin espacios ni guiones.", [
    ("placas", "VARCHAR(15)", False, None, "Placas normalizadas (Value Object Placas)"),
    ("vin", "CHAR(17)", False, None, "Número de serie VIN (17 caracteres, sin I, O ni Q)"),
    ("marca", "VARCHAR(60)", False, None, "Marca"),
    ("modelo", "VARCHAR(60)", False, None, "Modelo"),
    ("anio", "SMALLINT", False, None, "Año del modelo"),
    ("id_cliente", "VARCHAR(20)", False, None, "Propietario"),
], ["placas"], fks=[(["id_cliente"], "clientes", ["id"], "RESTRICT")], uniques=[["vin"]], checks=[
    "placas ~ '^[A-Z0-9]+$'", "vin ~ '^[A-HJ-NPR-Z0-9]{17}$'", "anio BETWEEN 1900 AND 2100"],
    indices=[("ix_vehiculos_cliente", "id_cliente")])

tabla("ordenes", "Órdenes de Servicio (Aggregate Orden de Servicio). Los Value Objects (recepción, diagnóstico, nota, pago, crédito, cancelación) se guardan como columnas.", [
    ("numero", "VARCHAR(20)", False, None, "Folio (NumeroOrden): OS-0001… o AUT-O001 en los datos del profesor"),
    ("id_cliente", "VARCHAR(20)", False, None, "Cliente"),
    ("es_cliente_de_flotilla", "BOOLEAN", False, "FALSE", "Copia del tipo de cliente al registrar la orden"),
    ("placas", "VARCHAR(15)", False, None, "Vehículo"),
    ("asesor", "VARCHAR(20)", False, None, "Asesor que registró la orden (recibe sus alertas)"),
    ("motivo_de_ingreso", "TEXT", False, None, "Motivo de ingreso"),
    ("kilometraje", "INTEGER", True, None, "Estado de recepción: kilometraje (sin dato en las órdenes importadas)"),
    ("nivel_combustible", "VARCHAR(10)", True, None, "Estado de recepción: nivel de combustible"),
    ("estado", "VARCHAR(40)", False, "'Recibida'", "EstadoOrden (13 estados del Glosario)"),
    ("fecha_ingreso", TS, False, None, "Fecha y hora de ingreso"),
    ("ultima_actualizacion", TS, False, None, "Última actualización (consulta del cliente, CA-037)"),
    ("tecnico_de_diagnostico", "VARCHAR(20)", True, None, "Técnico asignado al diagnóstico (CA-035)"),
    ("diagnostico_fallas", "TEXT", True, None, "Diagnóstico: fallas encontradas (CA-032)"),
    ("diagnostico_recomendaciones", "TEXT", True, None, "Diagnóstico: trabajos y refacciones recomendados"),
    ("diagnostico_registrado_en", TS, True, None, "Diagnóstico: fecha y hora"),
    ("cotizada", "BOOLEAN", False, "FALSE", "Ya tiene cotización (el diagnóstico ya no cambia, CA-033)"),
    ("rechazo_total", "BOOLEAN", False, "FALSE", "El cliente rechazó toda la cotización (CA-012)"),
    ("adicionales_pendientes", "SMALLINT", False, "0", "Cotizaciones adicionales sin decisión (CA-015, CA-018)"),
    ("fecha_ingreso_a_fila", TS, True, None, "Lugar en la fila de trabajo (CA-013, CA-025)"),
    ("estado_antes_de_espera", "VARCHAR(40)", True, None, "Estado al que regresa al llegar las refacciones (CA-022)"),
    ("nota_fecha_salida", TS, True, None, "Nota de Responsabilidad: salida del vehículo (CA-024)"),
    ("nota_firmada", "BOOLEAN", False, "FALSE", "Nota de Responsabilidad firmada"),
    ("nota_fecha_firma", TS, True, None, "Fecha de la firma"),
    ("pago_monto", MXN, True, None, "Pago de contado (CA-026)"),
    ("pago_forma", "VARCHAR(20)", True, None, "Forma de pago"),
    ("pago_registrado_en", TS, True, None, "Fecha del pago (ingresos del día, CA-031)"),
    ("recibo_numero", "VARCHAR(20)", True, None, "Número del recibo interno (CA-027)"),
    ("credito_monto", MXN, True, None, "Cargo a crédito de flotilla (CA-039)"),
    ("credito_registrado_en", TS, True, None, "Fecha del cargo"),
    ("credito_fecha_vencimiento", "DATE", True, None, "Vencimiento = entrega + 15 días naturales (CA-041)"),
    ("fecha_entrega", TS, True, None, "Entrega del vehículo (CA-041, CA-043)"),
    ("cancelacion_motivo", "TEXT", True, None, "Motivo de la cancelación (CA-044)"),
    ("cancelacion_registrada_en", TS, True, None, "Fecha de la cancelación"),
    ("cancelacion_asesor", "VARCHAR(20)", True, None, "Asesor que canceló"),
], ["numero"], fks=[(["id_cliente"], "clientes", ["id"], "RESTRICT"), (["placas"], "vehiculos", ["placas"], "RESTRICT"),
                    (["asesor"], "empleados", ["id"], "RESTRICT"), (["tecnico_de_diagnostico"], "empleados", ["id"], "RESTRICT"),
                    (["cancelacion_asesor"], "empleados", ["id"], "RESTRICT")],
    uniques=[["recibo_numero"]], checks=[
    f"estado IN ({lista(ESTADOS_ORDEN)})",
    "estado_antes_de_espera IS NULL OR estado_antes_de_espera IN ('Autorizada', 'En Reparación')",
    "kilometraje IS NULL OR kilometraje >= 0",
    f"nivel_combustible IS NULL OR nivel_combustible IN ({lista(COMBUSTIBLE)})",
    "adicionales_pendientes >= 0",
    f"pago_forma IS NULL OR pago_forma IN ({lista(FORMAS_DE_PAGO)})",
    "pago_monto IS NULL OR pago_monto >= 0",
    "credito_monto IS NULL OR credito_monto >= 0",
    "NOT (pago_monto IS NOT NULL AND credito_monto IS NOT NULL)",
    "estado <> 'Cancelada' OR cancelacion_motivo IS NOT NULL",
], indices=[("ix_ordenes_estado", "estado"), ("ix_ordenes_cliente", "id_cliente"), ("ix_ordenes_placas", "placas"),
            ("ix_ordenes_pago_fecha", "pago_registrado_en")])

tabla("trabajos", "Trabajos de la orden (entidad interna). Se crean al registrar la decisión del cliente.", [
    ("numero_orden", "VARCHAR(20)", False, None, "Orden"),
    ("id", "INTEGER", False, None, "Número del trabajo dentro de la orden (1, 2, …)"),
    ("descripcion", "TEXT", False, None, "Descripción"),
    ("importe", MXN, False, None, "Importe (mano de obra + refacciones de la línea)"),
    ("estado", "VARCHAR(20)", False, "'Pendiente'", "EstadoTrabajo"),
    ("tecnico", "VARCHAR(20)", True, None, "Técnico asignado (CA-036)"),
    ("id_cotizacion", "VARCHAR(20)", True, None, "Cotización de donde salió"),
    ("numero_linea", "INTEGER", True, None, "Línea de la cotización de donde salió"),
], ["numero_orden", "id"], fks=[(["numero_orden"], "ordenes", ["numero"], "CASCADE"), (["tecnico"], "empleados", ["id"], "RESTRICT")],
    checks=[f"estado IN ({lista(ESTADOS_TRABAJO)})", "importe >= 0", "id >= 1"],
    indices=[("ix_trabajos_tecnico", "tecnico")])

tabla("solicitudes_de_compra", "Solicitudes de compra de refacciones (entidad interna de la orden).", [
    ("numero_orden", "VARCHAR(20)", False, None, "Orden"),
    ("id", "INTEGER", False, None, "Número de la solicitud dentro de la orden"),
    ("id_trabajo", "INTEGER", False, None, "Trabajo autorizado al que pertenece (CA-020)"),
    ("refaccion", "VARCHAR(200)", False, None, "Descripción de la refacción"),
    ("cantidad", "INTEGER", False, None, "Cantidad"),
    ("fecha_solicitud", TS, False, None, "Desde aquí corren los 3 días hábiles (CA-023)"),
    ("estado", "VARCHAR(20)", False, "'Solicitada'", "EstadoSolicitud"),
    ("fecha_llegada", TS, True, None, "Llegada de la refacción (CA-022)"),
    ("fecha_aviso_al_cliente", TS, True, None, "Aviso de retraso al cliente (CA-023)"),
], ["numero_orden", "id"], fks=[(["numero_orden"], "ordenes", ["numero"], "CASCADE"),
                                (["numero_orden", "id_trabajo"], "trabajos", ["numero_orden", "id"], "RESTRICT")],
    checks=[f"estado IN ({lista(ESTADOS_SOLICITUD)})", "cantidad > 0"], indices=[("ix_solicitudes_estado", "estado")])

tabla("fallas_adicionales", "Fallas adicionales reportadas durante la reparación (CA-034).", [
    ("numero_orden", "VARCHAR(20)", False, None, "Orden"),
    ("id", "INTEGER", False, None, "Número de la falla dentro de la orden"),
    ("descripcion", "TEXT", False, None, "Descripción de la falla"),
    ("tecnico", "VARCHAR(20)", False, None, "Técnico que la reportó"),
    ("reportada_en", TS, False, None, "Fecha y hora"),
], ["numero_orden", "id"], fks=[(["numero_orden"], "ordenes", ["numero"], "CASCADE"), (["tecnico"], "empleados", ["id"], "RESTRICT")])

tabla("fotos_de_danos", "Fotos de daños visibles al recibir el vehículo (CA-002, ADR-014). Máximo 5 MB, JPEG o PNG.", [
    ("id", "BIGSERIAL", False, None, "Identificador"),
    ("numero_orden", "VARCHAR(20)", False, None, "Orden"),
    ("nombre_archivo", "VARCHAR(200)", False, None, "Nombre original"),
    ("tipo_mime", "VARCHAR(20)", False, None, "image/jpeg o image/png"),
    ("tamano_bytes", "INTEGER", False, None, "Tamaño"),
    ("contenido", "BYTEA", False, None, "Bytes de la imagen"),
    ("subida_en", TS, False, "NOW()", "Fecha"),
], ["id"], fks=[(["numero_orden"], "ordenes", ["numero"], "CASCADE")],
    checks=["tipo_mime IN ('image/jpeg', 'image/png')", "tamano_bytes BETWEEN 1 AND 5242880"],
    indices=[("ix_fotos_orden", "numero_orden")])

tabla("cotizaciones", "Cotizaciones (Aggregate Cotización). La inicial es v.1; las adicionales v.2 en adelante.", [
    ("id", "VARCHAR(20)", False, None, "Identificador (COT-0001…)"),
    ("numero_orden", "VARCHAR(20)", False, None, "Orden"),
    ("tipo", "VARCHAR(20)", False, None, "TipoCotizacion: Inicial o Adicional"),
    ("version", "SMALLINT", False, None, "VersionCotizacion"),
    ("estado", "VARCHAR(50)", False, None, "EstadoCotizacion (6 estados)"),
    ("total", MXN, False, None, "Suma de las líneas (dato derivado para las consultas)"),
    ("generada_en", TS, False, None, "Fecha de generación"),
    ("fecha_aprobacion_gerencial", TS, True, None, "Aprobación del Gerente (CA-008)"),
    ("observaciones_del_gerente", "TEXT", True, None, "Observaciones del rechazo gerencial (CA-009)"),
    ("fecha_presentacion", TS, True, None, "Presentación al cliente (inicia las 48 h, CA-006)"),
    ("decision_autorizante", "VARCHAR(120)", True, None, "Nombre de quien decidió (CA-010)"),
    ("decision_rol", "VARCHAR(30)", True, None, "Cliente o Responsable de Flotilla (CA-029)"),
    ("decision_registrada_en", TS, True, None, "Fecha y hora de la decisión"),
], ["id"], fks=[(["numero_orden"], "ordenes", ["numero"], "CASCADE")], uniques=[["numero_orden", "version"]], checks=[
    "tipo IN ('Inicial', 'Adicional')",
    "(tipo = 'Inicial' AND version = 1) OR (tipo = 'Adicional' AND version >= 2)",
    f"estado IN ({lista(ESTADOS_COTIZACION)})",
    "total >= 0",
    "decision_rol IS NULL OR decision_rol IN ('Cliente', 'Responsable de Flotilla')",
], indices=[("ix_cotizaciones_estado", "estado")])

tabla("lineas_de_cotizacion", "Líneas de la cotización (entidad interna): cada trabajo propuesto con su mano de obra.", [
    ("id_cotizacion", "VARCHAR(20)", False, None, "Cotización"),
    ("numero", "INTEGER", False, None, "Número de la línea (1, 2, …)"),
    ("descripcion", "TEXT", False, None, "Trabajo propuesto"),
    ("mano_de_obra", MXN, False, None, "Importe de mano de obra"),
    ("decision", "VARCHAR(20)", True, None, "Autorizada o No Autorizado (CA-010)"),
], ["id_cotizacion", "numero"], fks=[(["id_cotizacion"], "cotizaciones", ["id"], "CASCADE")],
    checks=["numero >= 1", "mano_de_obra >= 0", "decision IS NULL OR decision IN ('Autorizada', 'No Autorizado')"])

tabla("refacciones_cotizadas", "Refacciones de cada línea de cotización (Value Object RefaccionCotizada).", [
    ("id", "BIGSERIAL", False, None, "Identificador"),
    ("id_cotizacion", "VARCHAR(20)", False, None, "Cotización"),
    ("numero_linea", "INTEGER", False, None, "Línea"),
    ("posicion", "INTEGER", False, None, "Orden dentro de la línea"),
    ("descripcion", "VARCHAR(200)", False, None, "Refacción"),
    ("cantidad", "INTEGER", False, None, "Cantidad"),
    ("precio_unitario", MXN, False, None, "Precio unitario"),
], ["id"], fks=[(["id_cotizacion", "numero_linea"], "lineas_de_cotizacion", ["id_cotizacion", "numero"], "CASCADE")],
    checks=["cantidad > 0", "precio_unitario >= 0"])

tabla("recontactos", "Recontactos al cliente por cotizaciones sin respuesta (CA-040).", [
    ("id", "BIGSERIAL", False, None, "Identificador"),
    ("id_cotizacion", "VARCHAR(20)", False, None, "Cotización"),
    ("asesor", "VARCHAR(20)", False, None, "Asesor que recontactó"),
    ("registrado_en", TS, False, None, "Fecha y hora (el plazo de 48 h vuelve a contar)"),
], ["id"], fks=[(["id_cotizacion"], "cotizaciones", ["id"], "CASCADE"), (["asesor"], "empleados", ["id"], "RESTRICT")])

tabla("alertas_internas", "Alertas internas del panel de cada empleado (no son correos ni SMS).", [
    ("id", "BIGSERIAL", False, None, "Identificador"),
    ("destinatario", "VARCHAR(20)", True, None, "Empleado destinatario (o NULL si va a todo un rol)"),
    ("destinatario_rol", "VARCHAR(20)", True, None, "Rol destinatario (p. ej. todos los Gerentes)"),
    ("tipo", "VARCHAR(50)", False, None, "Tipo de alerta (AprobacionGerencialRequerida, RefaccionRetrasada, …)"),
    ("mensaje", "TEXT", False, None, "Texto para el usuario"),
    ("numero_orden", "VARCHAR(20)", True, None, "Orden relacionada"),
    ("id_cotizacion", "VARCHAR(20)", True, None, "Cotización relacionada"),
    ("clave", "VARCHAR(120)", True, None, "Evita alertas duplicadas en la revisión de plazos (ADR-015)"),
    ("creada_en", TS, False, "NOW()", "Fecha"),
    ("leida", "BOOLEAN", False, "FALSE", "Si ya se leyó"),
], ["id"], fks=[(["destinatario"], "empleados", ["id"], "SET NULL"), (["numero_orden"], "ordenes", ["numero"], "CASCADE"),
                (["id_cotizacion"], "cotizaciones", ["id"], "CASCADE")], uniques=[["clave"]], checks=[
    "destinatario IS NOT NULL OR destinatario_rol IS NOT NULL",
    f"destinatario_rol IS NULL OR destinatario_rol IN ({lista(ROLES)})"],
    indices=[("ix_alertas_destinatario", "destinatario, leida"), ("ix_alertas_rol", "destinatario_rol, leida")])

tabla("eventos", "Bitácora de Domain Events (ADR-016): evidencia de transiciones y pruebas.", [
    ("id", "BIGSERIAL", False, None, "Identificador"),
    ("tipo", "VARCHAR(60)", False, None, "Nombre del evento (OrdenCancelada, CotizacionAutorizada, …)"),
    ("agregado", "VARCHAR(30)", False, None, "Orden o Cotizacion"),
    ("id_agregado", "VARCHAR(20)", False, None, "Folio o id de la cotización"),
    ("datos", "JSONB", False, "'{}'::jsonb", "Datos del evento"),
    ("ocurrido_en", TS, False, None, "Cuándo ocurrió"),
    ("registrado_en", TS, False, "NOW()", "Cuándo se guardó"),
], ["id"], indices=[("ix_eventos_agregado", "id_agregado"), ("ix_eventos_tipo", "tipo")])

tabla("secuencias", "Folios consecutivos (OS-0001, COT-0001, REC-0001, CLI-0001); se revierten con la transacción.", [
    ("nombre", "VARCHAR(30)", False, None, "orden, cotizacion, recibo, cliente"),
    ("ultimo_valor", "INTEGER", False, "0", "Último número usado"),
], ["nombre"], checks=["ultimo_valor >= 0"], grupo="Soporte")

tabla("catalogo_servicios", "Catálogo de referencia del profesor (catalogo.csv). No es parte del dominio: sirve para armar cotizaciones de demostración y para rechazar las órdenes con servicios inhabilitados con el puerto `CatalogoDeServicios` (ADR-013, H-PIA-19).", [
    ("recurso_id", "VARCHAR(20)", False, None, "AUT-P001…"),
    ("descripcion", "VARCHAR(120)", False, None, "Servicio"),
    ("precio_mxn", MXN, False, None, "Precio unitario"),
    ("capacidad_o_stock", "INTEGER", False, None, "Dato del profesor sin uso en AutoFix (D-03)"),
    ("habilitado", "BOOLEAN", False, None, "Un servicio inhabilitado no se puede cotizar (D-05)"),
], ["recurso_id"], checks=["precio_mxn >= 0", "capacidad_o_stock >= 0"], grupo="Datos del profesor")

tabla("servicios_solicitados", "Detalle de referencia de cada operación del profesor (detalle_operaciones.csv).", [
    ("numero_orden", "VARCHAR(20)", False, None, "Orden (operacion_id)"),
    ("recurso_id", "VARCHAR(20)", False, None, "Servicio del catálogo"),
    ("cantidad", "INTEGER", False, None, "Cantidad"),
], ["numero_orden", "recurso_id"], fks=[(["numero_orden"], "ordenes", ["numero"], "CASCADE"),
                                        (["recurso_id"], "catalogo_servicios", ["recurso_id"], "RESTRICT")],
    checks=["cantidad > 0"], grupo="Datos del profesor")

tabla("referencia_operaciones_profesor", "Columnas del profesor sin equivalente en el BRD, guardadas solo como referencia para los oráculos (D-01, D-02).", [
    ("numero_orden", "VARCHAR(20)", False, None, "Orden (operacion_id)"),
    ("actor_activo", "BOOLEAN", False, None, "actores.activo (D-01: AutoFix no lo usa)"),
    ("actor_preferente", "BOOLEAN", False, None, "actores.es_preferente (D-02)"),
    ("promocion_activa", "BOOLEAN", False, None, "operaciones.promocion_activa (D-02)"),
    ("autorizado", "BOOLEAN", False, None, "operaciones.autorizado: 1 = autoriza todo; 0 = rechazo total"),
    ("referencia", "VARCHAR(30)", False, None, "operaciones.referencia"),
], ["numero_orden"], fks=[(["numero_orden"], "ordenes", ["numero"], "CASCADE")], grupo="Datos del profesor")


def sql():
    o = ["-- =============================================================================",
         "-- AutoFix Pro · Esquema de la base de datos (PostgreSQL 16 / Supabase) · PIA v3.0",
         "-- Generado por scripts/db/esquema.py — no editar a mano: cambie esquema.py y regenere.",
         "--",
         "-- Cómo usarlo:",
         "--   · Supabase: SQL Editor → New query → pegar TODO el archivo → Run.",
         "--   · Docker Compose: se ejecuta solo al crear el volumen de la base (docker-entrypoint-initdb.d).",
         "-- ATENCIÓN: borra y vuelve a crear las tablas de AutoFix Pro (los datos son ficticios).",
         "-- Después ejecute 02_datos_iniciales.sql.",
         "-- =============================================================================", "",
         "BEGIN;", ""]
    for t in reversed(T):
        o.append(f"DROP TABLE IF EXISTS {t['nombre']} CASCADE;")
    o.append("")
    for t in T:
        o.append(f"-- {t['descripcion']}")
        lineas = []
        for c, tipo, nulo, defecto, _com in t["columnas"]:
            linea = f"    {c:<28} {tipo}"
            if not nulo:
                linea += " NOT NULL"
            if defecto is not None:
                linea += f" DEFAULT {defecto}"
            lineas.append(linea)
        lineas.append(f"    CONSTRAINT pk_{t['nombre']} PRIMARY KEY ({', '.join(t['pk'])})")
        for cols in t["uniques"]:
            lineas.append(f"    CONSTRAINT uq_{t['nombre']}_{'_'.join(cols)} UNIQUE ({', '.join(cols)})")
        for cols, ref, rcols, accion in t["fks"]:
            lineas.append(f"    CONSTRAINT fk_{t['nombre']}_{'_'.join(cols)} FOREIGN KEY ({', '.join(cols)}) "
                          f"REFERENCES {ref} ({', '.join(rcols)}) ON DELETE {accion}")
        for i, ch in enumerate(t["checks"], 1):
            lineas.append(f"    CONSTRAINT ck_{t['nombre']}_{i} CHECK ({ch})")
        o.append(f"CREATE TABLE {t['nombre']} (")
        o.append(",\n".join(lineas))
        o.append(");")
        for nombre, cols in t["indices"]:
            o.append(f"CREATE INDEX {nombre} ON {t['nombre']} ({cols});")
        o.append(f"COMMENT ON TABLE {t['nombre']} IS '{t['descripcion'].replace(chr(39), chr(39) * 2)}';")
        for c, _tipo, _n, _d, com in t["columnas"]:
            o.append(f"COMMENT ON COLUMN {t['nombre']}.{c} IS '{com.replace(chr(39), chr(39) * 2)}';")
        o.append("")
    o += ["-- Folios iniciales", "INSERT INTO secuencias (nombre, ultimo_valor) VALUES ('orden', 0), ('cotizacion', 0), ('recibo', 0), ('cliente', 0);", "",
          "-- Seguridad para Supabase: la aplicación se conecta con el usuario dueño de las tablas (que no",
          "-- está sujeto a RLS). Activar RLS sin políticas impide leer o escribir estas tablas desde la",
          "-- Data API pública de Supabase con las llaves anon/authenticated. En PostgreSQL local no estorba."]
    for t in T:
        o.append(f"ALTER TABLE {t['nombre']} ENABLE ROW LEVEL SECURITY;")
    o += ["", "COMMIT;", ""]
    return "\n".join(o)


def puml():
    o = ["@startuml modelo-de-datos", "skinparam defaultFontName Arial", "skinparam defaultFontSize 11", "skinparam shadowing false",
         "skinparam dpi 150", "skinparam linetype ortho", "hide circle", "hide methods", "left to right direction",
         "title Modelo de datos — AutoFix Pro (PostgreSQL / Supabase) · PIA v3.0", ""]
    colores = {"Dominio": "#EEF5FF", "Soporte": "#F4F6F6", "Datos del profesor": "#FEF9E7"}
    for t in T:
        o.append(f"entity \"{t['nombre']}\" as {t['nombre']} {colores[t['grupo']]} {{")
        fk_cols = {c for cols, *_r in t["fks"] for c in cols}
        for c, tipo, _nulo, _d, _com in t["columnas"]:
            if c in t["pk"]:
                o.append(f"  * <b>{c}</b> : {tipo} <<PK>>")
        o.append("  --")
        for c, tipo, nulo, _d, _com in t["columnas"]:
            if c in t["pk"]:
                continue
            marca = "*" if not nulo else " "
            fk = " <<FK>>" if c in fk_cols else ""
            o.append(f"  {marca} {c} : {tipo}{fk}")
        o.append("}")
    o.append("")
    vistos = set()
    for t in T:
        for _cols, ref, _rc, _acc in t["fks"]:
            if (t["nombre"], ref) in vistos:
                continue
            vistos.add((t["nombre"], ref))
            o.append(f"{ref} ||--o{{ {t['nombre']}")
    o += ["", "legend bottom", "  Azul: tablas del dominio · Gris: soporte · Amarillo: datos de referencia del profesor (ADR-013).",
          "  * = obligatorio · PK = llave primaria · FK = llave foránea. Detalle de columnas en docs/architecture/modelo-de-datos.md",
          "endlegend", "@enduml", ""]
    return "\n".join(o)


def md():
    o = ["# Modelo de datos — AutoFix Pro (PIA v3.0)\n",
         "Esquema oficial de la base de datos (PostgreSQL 16 en Docker y en **Supabase**, ADR-009). Lo genera `scripts/db/esquema.py`, que también produce `database/01_esquema.sql` y el diagrama `diagramas/modelo-de-datos.png`.\n",
         "**Reglas del mapeo:** cada Aggregate tiene su tabla raíz (`ordenes`, `cotizaciones`, `clientes`, `vehiculos`, `empleados`); las entidades internas tienen llave compuesta con el folio de su raíz; los Value Objects se guardan como columnas. Importes en `NUMERIC(12,2)` (pesos con centavos, se leen como `Decimal`) y fechas en `TIMESTAMPTZ` (UTC). Los nombres de estado son los del Glosario y la base los valida con `CHECK`. Las reglas de negocio **no** se programan en la base: viven en el dominio; la base solo protege la integridad (llaves, tipos y valores permitidos).\n",
         "**Implementación:** `src/infrastructure/base_de_datos/tablas.py` (SQLAlchemy) debe tener exactamente estas tablas y columnas; una prueba de integración con PostgreSQL lo verifica. En las pruebas sin Docker se usa SQLite con `metadata.create_all()`.\n",
         "![Modelo de datos](diagramas/modelo-de-datos.png)\n",
         f"## Tablas ({len(T)})\n"]
    for grupo in ["Dominio", "Soporte", "Datos del profesor"]:
        o.append(f"### {grupo}\n")
        for t in [x for x in T if x["grupo"] == grupo]:
            o.append(f"#### `{t['nombre']}`\n")
            o.append(t["descripcion"] + "\n")
            o.append("| Columna | Tipo | Nulo | Descripción |\n|---|---|---|---|")
            for c, tipo, nulo, d, com in t["columnas"]:
                clave = " (PK)" if c in t["pk"] else ""
                o.append(f"| `{c}`{clave} | {tipo} | {'sí' if nulo else 'no'} | {com}{' · por defecto ' + d if d else ''} |")
            extra = []
            for cols, ref, rc, _acc in t["fks"]:
                extra.append(f"FK ({', '.join(cols)}) → `{ref}` ({', '.join(rc)})")
            for cols in t["uniques"]:
                extra.append(f"UNIQUE ({', '.join(cols)})")
            for ch in t["checks"]:
                extra.append(f"CHECK `{ch}`")
            if extra:
                o.append("\n" + " · ".join(extra) + "\n")
            else:
                o.append("")
    o += ["## Scripts\n",
          "| Archivo | Qué hace |\n|---|---|",
          "| `database/01_esquema.sql` | Borra y crea todas las tablas, restricciones, índices, comentarios y activa RLS (protección de la Data API de Supabase). |",
          "| `database/02_datos_iniciales.sql` | Carga los 6 empleados de demostración y los datos del profesor en su estado inicial (40 clientes, 60 vehículos, 60 órdenes «Recibida», 20 servicios, 117 líneas de detalle). Lo genera `scripts/db/generar_datos_iniciales.py`. |",
          "| `database/03_verificacion.sql` | Consultas para comprobar que todo se cargó (conteos esperados). |"]
    return "\n".join(o) + "\n"


(RAIZ / "database").mkdir(exist_ok=True)
(RAIZ / "database/01_esquema.sql").write_text(sql(), encoding="utf-8")
(RAIZ / "docs/architecture/diagramas/modelo-de-datos.puml").write_text(puml(), encoding="utf-8")
(RAIZ / "docs/architecture/modelo-de-datos.md").write_text(md(), encoding="utf-8")
print("ok", len(T), "tablas")
