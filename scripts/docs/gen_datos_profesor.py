"""Analiza el paquete 06_AutoFix_Pro (01_Alumno) y genera docs/datos-profesor/ con oráculos propios."""
import csv
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

DATOS = Path(sys.argv[1])
SALIDA = Path(sys.argv[2]) / "datos-profesor"
SALIDA.mkdir(parents=True, exist_ok=True)


def leer(nombre):
    with open(DATOS / nombre, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


actores = {a["actor_id"]: a for a in leer("actores.csv")}
catalogo = {c["recurso_id"]: c for c in leer("catalogo.csv")}
operaciones = leer("operaciones.csv")
detalle = leer("detalle_operaciones.csv")
casos = leer("casos_prueba.csv")
transiciones = leer("transiciones_prueba.csv")

lineas = {}
for d in detalle:
    lineas.setdefault(d["operacion_id"], []).append(d)

UMBRAL = Decimal("15000")
info = {}
for o in operaciones:
    oid = o["operacion_id"]
    ls = lineas.get(oid, [])
    total = sum((Decimal(catalogo[d["recurso_id"]]["precio_mxn"]) * int(d["cantidad"]) for d in ls), Decimal("0.00"))
    inhab = sorted({d["recurso_id"] for d in ls if catalogo[d["recurso_id"]]["habilitado"] != "1"})
    act = actores[o["actor_id"]]
    info[oid] = dict(
        actor=o["actor_id"], activo=act["activo"] == "1", preferente=act["es_preferente"] == "1",
        promo=o["promocion_activa"] == "1", autorizado=o["autorizado"] == "1", n=len(ls), total=total,
        inhabilitados=inhab, referencia=o["referencia"], fecha=o["fecha_solicitud"],
        excede_stock=[d["recurso_id"] for d in ls if int(d["cantidad"]) > int(catalogo[d["recurso_id"]]["capacidad_o_stock"])],
    )


def ref_procesable(i):
    return i["activo"] and i["n"] > 0 and i["autorizado"]


def autofix_procesable(i):
    return i["n"] > 0 and not i["inhabilitados"] and i["autorizado"]


def ref_beneficio(i):
    return i["preferente"] and i["total"] >= Decimal("1500") and not i["promo"]


def motivo_autofix(i):
    if i["n"] == 0:
        return "Sin detalle: la cotización no se genera (422 CotizacionSinTrabajos)"
    if i["inhabilitados"]:
        return f"Servicio inhabilitado {', '.join(i['inhabilitados'])}: dato inválido (422 ValorInvalido)"
    if not i["autorizado"]:
        return "autorizado=0: rechazo total (CA-012); no se puede reparar"
    return "Detalle válido y autorizado: se puede reparar"


def dif_validar(i):
    r, a = ref_procesable(i), autofix_procesable(i)
    if r == a:
        return ""
    if not i["activo"] and a:
        return "D-01: AutoFix no maneja clientes inactivos"
    if i["inhabilitados"] and r:
        return "D-05: AutoFix rechaza servicios inhabilitados"
    return "revisar"


def placas(ref):
    return ref.replace("_", "-")


# ----------------------------------------------------------------------------- oráculos de casos
filas_casos = []
for c in casos:
    i = info[c["operacion_id"]]
    if c["tipo_prueba"] == "validar_operacion":
        filas_casos.append(dict(
            caso_id=c["caso_id"], operacion_id=c["operacion_id"], tipo_prueba=c["tipo_prueba"],
            referencia_profesor="VERDADERO" if ref_procesable(i) else "FALSO",
            esperado_autofix="VERDADERO" if autofix_procesable(i) else "FALSO",
            regla_autofix="TieneDetalle AND ServiciosHabilitados AND Autorizado",
            diferencia=dif_validar(i), explicacion=motivo_autofix(i)))
    else:
        filas_casos.append(dict(
            caso_id=c["caso_id"], operacion_id=c["operacion_id"], tipo_prueba=c["tipo_prueba"],
            referencia_profesor="VERDADERO" if ref_beneficio(i) else "FALSO",
            esperado_autofix="FALSO",
            regla_autofix="RequiereAprobacionGerencial = EsCotizacionInicial AND Total > $15,000",
            diferencia="D-02: AutoFix no tiene clientes preferentes ni promociones",
            explicacion=f"Total ${i['total']:,.2f} ≤ $15,000: no requiere Gerente"))
with open(SALIDA / "oraculos_casos.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(filas_casos[0]))
    w.writeheader()
    w.writerows(filas_casos)


# ----------------------------------------------------------------------------- oráculos de transiciones
def oraculo_transicion(accion, oid):
    i = info[oid]
    if accion == "cancelar":
        return ("Cancelar con motivo desde «Recibida» (E4)", "Cancelada", "OrdenCancelada", "200")
    if accion == "saltar_estado":
        return ("Intentar entregar una orden «Recibida» (saltar a «Cerrada»)", "Recibida",
                "EntregaNoPermitida (E3 no se cumple)", "409")
    pasos = "Asignar técnico → diagnóstico → generar cotización"
    if i["n"] == 0:
        return (pasos, "En Diagnóstico", "CotizacionSinTrabajos (sin detalle)", "422")
    if i["inhabilitados"]:
        return (pasos, "En Diagnóstico", f"ValorInvalido (servicio {', '.join(i['inhabilitados'])} inhabilitado)", "422")
    pasos += " → presentar → registrar decisión"
    if accion == "aprobar":
        if i["autorizado"]:
            return (pasos + " (autoriza todo)", "Autorizada", "CotizacionAutorizada + OrdenAutorizada", "200")
        return (pasos + " (rechazo total)", "Cotizada", "CotizacionRechazadaPorCliente", "200")
    if accion == "repetir_aprobacion":
        final = "Autorizada" if i["autorizado"] else "Cotizada"
        return (pasos + " dos veces", final,
                "OperacionDeCotizacionNoPermitida (la decisión ya está registrada)", "409")
    if accion == "completar":
        if not i["autorizado"]:
            return (pasos + " (rechazo total) → asignar trabajos", "Cotizada",
                    "TrabajoNoAutorizado (no hay trabajos autorizados)", "409")
        return (pasos + " → asignar y completar trabajos → pago → entrega", "Cerrada",
                "VehiculoEntregado (cadena completa de eventos)", "200")
    raise ValueError(accion)


filas_tr = []
for t in transiciones:
    flujo, final, evento, http = oraculo_transicion(t["accion_sugerida"], t["operacion_id"])
    filas_tr.append(dict(caso_id=t["caso_id"], operacion_id=t["operacion_id"], accion=t["accion_sugerida"],
                         flujo_autofix=flujo, estado_final_esperado=final, evento_o_excepcion=evento, http=http))
with open(SALIDA / "oraculos_transiciones.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(filas_tr[0]))
    w.writeheader()
    w.writerows(filas_tr)

# ----------------------------------------------------------------------------- estadísticas
inactivos = sorted(a for a, x in actores.items() if x["activo"] != "1")
preferentes = sorted(a for a, x in actores.items() if x["es_preferente"] == "1")
ops_inactivos = [o for o, i in info.items() if not i["activo"]]
ops_no_aut = [o for o, i in info.items() if not i["autorizado"]]
ops_promo = [o for o, i in info.items() if i["promo"]]
ops_inhab = [o for o, i in info.items() if i["inhabilitados"]]
ops_sin = [o for o, i in info.items() if i["n"] == 0]
maxop = max(info, key=lambda o: info[o]["total"])
ge1500 = sum(1 for i in info.values() if i["total"] >= Decimal("1500"))
gt15000 = sum(1 for i in info.values() if i["total"] > UMBRAL)
inhab_cat = [c for c, x in catalogo.items() if x["habilitado"] != "1"]
cv = Counter(f["referencia_profesor"] == f["esperado_autofix"] for f in filas_casos if f["tipo_prueba"] == "validar_operacion")
ref_true_v = sum(1 for f in filas_casos if f["tipo_prueba"] == "validar_operacion" and f["referencia_profesor"] == "VERDADERO")
af_true_v = sum(1 for f in filas_casos if f["tipo_prueba"] == "validar_operacion" and f["esperado_autofix"] == "VERDADERO")
ref_true_b = sum(1 for f in filas_casos if f["tipo_prueba"] == "evaluar_beneficio" and f["referencia_profesor"] == "VERDADERO")
fechas = sorted(i["fecha"] for i in info.values())


def lista(xs):
    return ", ".join(xs) if xs else "—"


md = f"""# Datos del profesor (paquete «06_AutoFix_Pro») — adaptación y oráculos

El paquete `06_AutoFix_Pro/01_Alumno` es el «Data Center» del PIA: datos **ficticios** para cargar, probar y demostrar el sistema. El propio paquete aclara que su flujo y sus reglas son un **modelo de pruebas propuesto** y que, si difieren de los requerimientos del equipo, se deben **documentar las diferencias y adaptar fixtures y oráculos, sin reemplazar los requerimientos propios**. Este documento hace exactamente eso (ADR-013, hallazgo H-PIA-03).

> La carpeta `02_Docente` no se usa ni se incluye en el repositorio (indicación del paquete).

## 1. Contenido

| Archivo | Registros | Uso en AutoFix Pro |
|---|---|---|
| `actores.csv` | {len(actores)} propietarios (`AUT-C001`…) | Clientes **Particulares** |
| `catalogo.csv` | {len(catalogo)} servicios (`AUT-P001`…) | Catálogo de referencia para armar las líneas de la cotización |
| `operaciones.csv` | {len(operaciones)} operaciones, todas `RECIBIDA` ({fechas[0]} a {fechas[-1]}) | Órdenes de Servicio «Recibida» |
| `detalle_operaciones.csv` | {len(detalle)} líneas | Líneas de la cotización inicial (precio × cantidad) |
| `casos_prueba.csv` | {len(casos)} casos (60 `validar_operacion` + 60 `evaluar_beneficio`) | Pruebas de reglas con oráculos propios (sección 5) |
| `transiciones_prueba.csv` | {len(transiciones)} casos (`completar`, `cancelar`, `repetir_aprobacion`, `saltar_estado`, `aprobar` × 4) | Pruebas de la máquina de estados (sección 6) |

Formato: CSV UTF-8 **con BOM** (leer con `encoding="utf-8-sig"`), importes en MXN con dos decimales (convertir con `Decimal`, nunca `float`), fechas ISO 8601.

## 2. Cómo se cargan (`database/02_datos_iniciales.sql`)

| Dato del profesor | Se convierte en | Regla de conversión |
|---|---|---|
| `actor_id`, `nombre` | `clientes` (Particular): id y nombre | Teléfono y correo no vienen: se generan valores ficticios reconocibles (`81-0000-0001`, `aut-c001@ejemplo.test`). |
| `ciudad` | — | Informativo; no forma parte del modelo. |
| `operacion_id` | `NumeroOrden` (folio) | El folio es el mismo id (`AUT-O001`), para que los casos se puedan cruzar. |
| `fecha_solicitud` | `fecha_ingreso` | A las 09:00 de Monterrey, guardada en UTC. |
| `referencia` (`PIA_AUT_001`) | `Placas` del vehículo y motivo de ingreso | Placas = `PIA-AUT-001` (el Value Object las normaliza a `PIAAUT001`); motivo = «Servicio de referencia PIA_AUT_001». |
| — | `Vehiculo` | Uno por operación: marca «Ficticia», modelo «Referencia», año 2020, VIN `AUT` + 14 dígitos del número de operación. |
| `estado_inicial` = `RECIBIDA` | `EstadoOrden.RECIBIDA` | Sin cambios; los cambios de estado se hacen **con el código** (casos de uso), como pide el paquete. |
| `detalle` (`recurso_id`, `cantidad`) | `LineaDeCotizacion` | Descripción = descripción del catálogo + id; mano de obra = `precio_mxn × cantidad` con `Decimal`. Cantidad > 0. |
| `habilitado` = 0 | Error de dato (422) | Un servicio inhabilitado no se puede cotizar: la cotización de esa orden no se genera. |
| `autorizado` | Decisión del cliente | 1 = autoriza todos los trabajos; 0 = **no autoriza ninguno** (rechazo total, CA-012). |
| `activo`, `es_preferente`, `promocion_activa`, `capacidad_o_stock` | — | Sin equivalente en el BRD (ver diferencias D-01 a D-03). |

El script lo genera `scripts/db/generar_datos_iniciales.py` y además registra los 6 empleados de demostración (ADR-012). Solo carga el **estado inicial**: las 60 órdenes quedan «Recibida» y los cambios de estado se hacen con la API, así que todas las reglas del dominio aplican también a los datos del profesor. El catálogo y el detalle quedan en `catalogo_servicios` y `servicios_solicitados`, y las columnas sin equivalente (`activo`, `es_preferente`, `promocion_activa`, `autorizado`) en `referencia_operaciones_profesor`, solo como referencia. Kilometraje y combustible quedan vacíos (no vienen en los datos).

## 3. Diferencias entre el modelo propuesto y AutoFix Pro

| ID | Modelo del profesor | AutoFix Pro (BRD propio) | Decisión |
|---|---|---|---|
| D-01 | `puede_procesarse` exige **actor activo**. | El BRD no maneja clientes inactivos: un cliente recurrente siempre se atiende (US-003). | Se ignora `activo`. Las {len(ops_inactivos)} operaciones de actores inactivos se procesan si cumplen lo demás. |
| D-02 | `beneficio_referencia`: preferente AND total ≥ 1500 AND NOT promoción. | Fuera de alcance: «No se manejan descuentos, promociones ni clientes preferentes» (BRD §5). | No se agrega al dominio. La regla propia comparable (composición AND sobre el total) es `RequiereAprobacionGerencial`. La regla del profesor se evalúa solo como **referencia** en el arnés de pruebas con la clase `Especificacion`. |
| D-03 | `capacidad_o_stock` por servicio. | «El sistema no controla existencias de inventario» (Glosario, Verificación de Disponibilidad). | Se ignora. Ninguna línea excede la capacidad ({len([o for o, i in info.items() if i['excede_stock']])} casos), así que no cambia ningún resultado. |
| D-04 | 5 estados: RECIBIDA → DIAGNOSTICADA → EN_REPARACION → ENTREGADA; CANCELADA desde RECIBIDA. | 13 estados de orden (Glosario §2). | Equivalencias: RECIBIDA = «Recibida»; DIAGNOSTICADA ≈ «En Diagnóstico» con diagnóstico registrado; EN_REPARACION = «En Reparación»; ENTREGADA = «Cerrada»; CANCELADA = «Cancelada» (agregada en v3.0 por H-PIA-01, también desde «En Diagnóstico»). |
| D-05 | La regla de ejemplo no menciona `habilitado`, pero el paquete pide «validar disponibilidad». | Un servicio inhabilitado es un dato inválido. | `validar_operacion` de AutoFix = TieneDetalle AND ServiciosHabilitados AND Autorizado. |
| D-06 | Precondición «técnico disponible». | El asesor asigna un técnico (CA-035); no hay agenda de técnicos en el BRD. | En las pruebas se asigna siempre el Técnico 1 de demostración. |
| D-07 | Un actor = «propietario». | Clientes particulares o de flotilla. | Todos los propietarios se cargan como particulares; las flotillas se prueban con fixtures propios (CA-028, CA-029, CA-039). |

## 4. Anomalías detectadas en los datos (y cómo se prueban)

| Anomalía | Operaciones | Resultado esperado en AutoFix |
|---|---|---|
| Actores inactivos ({lista(inactivos)}) | {len(ops_inactivos)}: {lista(ops_inactivos)} | Se procesan (D-01). |
| No autorizadas (`autorizado` = 0) | {len(ops_no_aut)}: {lista(ops_no_aut)} | Rechazo total: cotización «Rechazada», orden «Cotizada»; no se pueden asignar trabajos (409); se entregan sin reparación. |
| Servicio inhabilitado ({lista(inhab_cat)}) | {len(ops_inhab)}: {lista(ops_inhab)} | La cotización no se genera (422); la orden queda «En Diagnóstico». |
| Sin líneas de detalle | {len(ops_sin)}: {lista(ops_sin)} | La cotización no se genera (422 `CotizacionSinTrabajos`). |
| Promoción activa | {len(ops_promo)}: {lista(ops_promo)} | Sin efecto en AutoFix (D-02). |
| Ninguna supera $15,000 MXN | máximo {maxop} = ${info[maxop]['total']:,.2f}; {ge1500} de 60 son ≥ $1,500 | La aprobación gerencial (CA-007 a CA-009) se prueba con fixtures propios (p. ej. una cotización de $16,500.00) y con la matriz PIA de la U5. |
| Clientes preferentes ({lista(preferentes)}) | — | Sin efecto en AutoFix (D-02). |

`AUT-O040` combina tres anomalías (actor inactivo, no autorizada y servicio inhabilitado): en AutoFix gana la validación del dato (422 por el servicio inhabilitado), porque la cotización ni siquiera se puede generar.

## 5. Oráculos de `casos_prueba.csv`

Archivo completo: [`oraculos_casos.csv`](oraculos_casos.csv) (120 filas: referencia del profesor, resultado esperado en AutoFix, regla, diferencia y explicación). Resumen:

| Tipo de prueba | Regla del profesor (referencia) | Regla de AutoFix | Verdaderos (profesor) | Verdaderos (AutoFix) | Coinciden |
|---|---|---|---|---|---|
| `validar_operacion` | activo AND detalle AND autorización | TieneDetalle AND ServiciosHabilitados AND Autorizado | {ref_true_v} | {af_true_v} | {cv[True]} de 60 (las {cv[False]} diferencias son D-01 o D-05) |
| `evaluar_beneficio` | preferente AND total ≥ 1500 AND NOT promoción | No aplica (D-02); se registra `RequiereAprobacionGerencial` | {ref_true_b} | 0 | Diferencia documentada (D-02) |

La prueba `tests/datos_profesor/test_casos_prueba.py` recorre los 120 casos, compara el resultado con este oráculo y escribe `reportes/resultados_casos.csv` con las columnas del profesor (`resultado_alumno` = resultado obtenido) más la evidencia (nombre de la prueba y mensaje del dominio).

## 6. Oráculos de `transiciones_prueba.csv`

Interpretación de las acciones sugeridas con los casos de uso de AutoFix:

- **completar**: flujo completo hasta entregar el vehículo (asignar técnico → diagnóstico → cotización → presentar → decisión → asignar y completar trabajos → pago → entrega).
- **cancelar**: cancelación con motivo desde «Recibida» (US-025).
- **repetir_aprobacion**: registrar dos veces la decisión del cliente sobre la misma cotización.
- **saltar_estado**: intentar entregar una orden que sigue «Recibida».
- **aprobar**: flujo hasta registrar la decisión del cliente.

| Caso | Operación | Acción | Flujo en AutoFix | Estado final esperado | Evento o excepción | HTTP |
|---|---|---|---|---|---|---|
""" + "\n".join(f"| {r['caso_id']} | {r['operacion_id']} | {r['accion']} | {r['flujo_autofix']} | {r['estado_final_esperado']} | {r['evento_o_excepcion']} | {r['http']} |" for r in filas_tr) + """

Archivo: [`oraculos_transiciones.csv`](oraculos_transiciones.csv). La prueba `tests/datos_profesor/test_transiciones.py` ejecuta cada caso, compara con el oráculo y escribe `reportes/resultados_transiciones.csv` con el estado final, los eventos de la bitácora o la excepción y su código HTTP.

## 7. Totales calculados (muestra)

| Operación | Detalle | Total (Decimal) |
|---|---|---|
""" + "\n".join(
    f"| {o} | " + " + ".join(f"{d['recurso_id']} × {d['cantidad']}" for d in lineas.get(o, [])) + f" | ${info[o]['total']:,.2f} |"
    for o in ["AUT-O001", "AUT-O005", "AUT-O007", "AUT-O008", "AUT-O013"]) + """

Los totales de las 60 operaciones están en `oraculos_casos.csv` (columna «explicacion» de `evaluar_beneficio`).
"""
(SALIDA / "README.md").write_text(md, encoding="utf-8")
print("ok", len(filas_casos), len(filas_tr), cv, ref_true_v, af_true_v, ref_true_b)
