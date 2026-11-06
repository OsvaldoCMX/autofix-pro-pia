"""Genera trazabilidad/matriz-trazabilidad.md + .xlsx y api/README.md desde datos.py y rutas.py."""
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from rutas import RUTAS, validar_rutas

from datos import AREA_DE_PRUEBA, CA, NECESIDADES, REGLAS, TRAZA_NECESIDAD, US, area_de, validar

DOCS = Path(sys.argv[1])
validar()
validar_rutas()

RN_COMPONENTE = {
    "RN-01": ("Empleado (RolDeEmpleado.ASESOR) + `requiere_rol` en la API", "ADR-012"),
    "RN-02": ("`OrdenDeServicio.marcar_cotizada` → `DiagnosticoRequerido`", "ADR-001"),
    "RN-03": ("`OrdenDeServicio.registrar_diagnostico` → `DiagnosticoNoModificable`", "ADR-001"),
    "RN-04": ("Specification E1 `RequiereAprobacionGerencial`", "ADR-005, ADR-006"),
    "RN-05": ("`Cotizacion.rechazar_por_gerente` / `ajustar`", "ADR-007"),
    "RN-06": ("`MAQUINA_DE_COTIZACION` (presentar solo desde «Pendiente de Autorización del Cliente»)", "ADR-007"),
    "RN-07": ("Specification E2 `AutorizanteValido` + `VerificadorDeAutorizante`", "ADR-006"),
    "RN-08": ("`OrdenDeServicio.aplicar_decision` / `asignar_trabajos`, `Trabajo`", "ADR-007"),
    "RN-09": ("Specification E6 `PuedeSolicitarRefaccion`", "ADR-006"),
    "RN-10": ("`MAQUINA_DE_ORDEN` + `registrar_llegada_de_refaccion`", "ADR-007"),
    "RN-11": ("Specification E7 `RequiereAlertaDeRefaccion` + `CalendarioHabil` + `ServicioDeRevisionDePlazos`", "ADR-006, ADR-015"),
    "RN-12": ("Specification E8 `RequiereRecontacto` + `ServicioDeRevisionDePlazos`", "ADR-006, ADR-015"),
    "RN-13": ("`OrdenDeServicio.registrar_salida` / `confirmar_firma_de_nota` / `reactivar`", "ADR-007"),
    "RN-14": ("Specification E5 `PuedeIniciarTrabajo`", "ADR-006, ADR-012"),
    "RN-15": ("`OrdenDeServicio.completar_trabajo` / `aplicar_decision` (adicional)", "ADR-007"),
    "RN-16": ("`OrdenDeServicio.registrar_pago` / `registrar_cargo_a_credito`, `Pago`, `Dinero`", "ADR-001"),
    "RN-17": ("`CargoACredito.fecha_vencimiento` (fijada en `entregar`)", "ADR-001"),
    "RN-18": ("Specification E3 `PuedeEntregarse`", "ADR-006"),
    "RN-19": ("Specification E4 `PuedeCancelarse` + `Cancelacion`", "ADR-006, ADR-007"),
    "RN-20": ("Consulta `ConsultarEstadoDeOrden` (lector CQRS)", "ADR-003"),
    "RN-21": ("Consulta `ConsultarIngresosDelDia`", "ADR-003"),
    "RN-22": ("`MaquinaDeEstados` (Orden, Cotización, Trabajo, Solicitud)", "ADR-007"),
    "RN-23": ("Value Objects `Dinero`, `RefaccionCotizada`; validación Pydantic (422); restricciones `CHECK` de la base", "ADR-008, ADR-013"),
    "RN-24": ("`Cotizacion.generar` (`TipoCotizacion.ADICIONAL`, `VersionCotizacion`)", "ADR-001"),
}
assert set(RN_COMPONENTE) == set(REGLAS)

ESPECS = [
    ("E1", "RequiereAprobacionGerencial", "EsCotizacionInicial AND TotalMayorAlUmbral($15,000)", "AND", "RN-04", "CA-005, CA-007, CA-016"),
    ("E2", "AutorizanteValido", "(EsClienteParticular AND AutorizaElCliente) OR (EsClienteDeFlotilla AND AutorizaSuResponsableDeFlotilla)", "AND, OR", "RN-07", "CA-010, CA-029"),
    ("E3", "PuedeEntregarse", "EstaPagada OR EstaPorCobrarACredito OR (EstaCotizada AND TieneRechazoTotal)", "OR, AND", "RN-18", "CA-041, CA-042, CA-043"),
    ("E4", "PuedeCancelarse", "EstaRecibida OR EstaEnDiagnostico", "OR", "RN-19", "CA-044, CA-045"),
    ("E5", "PuedeIniciarTrabajo", "TrabajoPendiente AND AsignadoAlTecnico AND NOT OrdenPausadaPorRetiro", "AND, NOT", "RN-14", "CA-014, CA-046"),
    ("E6", "PuedeSolicitarRefaccion", "TrabajoAutorizado AND (OrdenAutorizada OR OrdenEnReparacion OR OrdenEnEsperaDeRefaccion)", "AND, OR", "RN-09", "CA-019, CA-020"),
    ("E7", "RequiereAlertaDeRefaccion", "SolicitudPendiente AND MasDeDiasHabiles(3) AND NOT ClienteYaAvisado", "AND, NOT", "RN-11", "CA-023"),
    ("E8", "RequiereRecontacto", "PendienteDeAutorizacion AND FuePresentada AND MasDeHorasDesdeElUltimoContacto(48)", "AND", "RN-12", "CA-040"),
]


def necesidades_de(ca_id):
    return [n for n, (_u, cas, _b) in TRAZA_NECESIDAD.items() if ca_id in cas]


def prueba_de(c):
    return f"{AREA_DE_PRUEBA[area_de(c['us'])]}::test_{c['id'].lower().replace('-', '_')}_*"


def cas_de_regla(rn):
    return [c["id"] for c in CA.values() if rn in c["reglas"]]


def rn_num(rn):
    return rn.split("-")[1]


filas_ca = []
for c in CA.values():
    filas_ca.append([c["id"], c["nombre"], c["us"], ", ".join(necesidades_de(c["id"])), c["bpmn"],
                     ", ".join(c["reglas"]), c["dominio"], c["servicio"], c["ruta"], c["rol"],
                     prueba_de(c), c["prioridad"], c["cambio"] or ""])
CAB_CA = ["CA", "Criterio", "US", "Necesidad", "BPMN", "Regla(s)", "Componentes del dominio",
          "Servicio / consulta", "Ruta API", "Rol", "Prueba prevista", "Prioridad", "Hallazgo v3.0"]

filas_rn = []
for rn, (texto, fuente) in REGLAS.items():
    comp, adr = RN_COMPONENTE[rn]
    filas_rn.append([rn, texto, fuente, ", ".join(cas_de_regla(rn)), comp, adr, f"tests/**/test_rn_{rn_num(rn)}_*"])
CAB_RN = ["RN", "Regla de negocio", "Fuente (BRD)", "Criterios", "Componente", "ADR", "Prueba prevista"]

# ============================================================================ markdown
T = DOCS / "trazabilidad"
T.mkdir(parents=True, exist_ok=True)


def tabla(cab, filas):
    out = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for f in filas:
        out.append("| " + " | ".join(str(x).replace("|", "\\|") for x in f) + " |")
    return out


p1 = sum(1 for c in CA.values() if c["prioridad"] == "P1")
md = ["# Matriz de trazabilidad — AutoFix Pro (PIA v3.0)\n",
      "Relaciona **BRD → regla de negocio → componente → prueba**, como pide el paquete del profesor, y cada criterio de aceptación con su User Story, necesidad, fase del BPMN, ruta de la API y rol. Se genera con los scripts de `scripts/docs/` desde la misma fuente que `user-stories.md` y los `.feature`, así que los textos y conteos coinciden.\n",
      f"**Conteos:** {len(NECESIDADES)} necesidades · {len(US)} User Stories · {len(CA)} criterios · {len(REGLAS)} reglas de negocio · {len(ESPECS)} Specifications · {len(RUTAS)} rutas de API.\n",
      "La columna **Prueba prevista** usa la convención `test_ca_0XX_…` / `test_rn_XX_…` (ver `architecture/decisiones-tecnicas.md` §7). Al terminar la implementación se reemplaza por el nombre real de la prueba y su resultado (✔/✘), y se agrega la evidencia de cobertura.\n",
      "## 1. Necesidades → User Stories → criterios → BPMN\n"]
md += tabla(["Necesidad", "Descripción", "Prioridad", "User Stories", "Criterios", "BPMN"],
            [[n, d, p, ", ".join(TRAZA_NECESIDAD[n][0]), ", ".join(TRAZA_NECESIDAD[n][1]), TRAZA_NECESIDAD[n][2]]
             for n, d, p in NECESIDADES])
md += ["", "## 2. Reglas de negocio\n",
       "Cada regla viene del BRD (o de un hallazgo documentado) y tiene un componente responsable y una prueba.\n"]
md += tabla(CAB_RN, filas_rn)
md += ["", "## 3. Specifications\n"]
md += tabla(["#", "Specification", "Composición", "Operadores", "Regla", "Criterios"], [list(e) for e in ESPECS])
md += ["", "Operadores cubiertos: **AND** (E1, E2, E3, E5, E6, E7, E8), **OR** (E2, E3, E4, E6) y **NOT** (E5, E7).", "",
       "## 4. Matriz por criterio de aceptación\n"]
md += tabla(CAB_CA, filas_ca)
md += ["", f"**Prioridad:** {p1} criterios son P1 completos; la parte P2 (PDF y fotos) se omitió por decisión del equipo y sus rutas responden 501 (ver `architecture/decisiones-tecnicas.md` §8). CA-027 no está implementado; CA-002, CA-005 y CA-024 están implementados, salvo sus fotos o su PDF.\n"]
(T / "matriz-trazabilidad.md").write_text("\n".join(md) + "\n", encoding="utf-8")

# ============================================================================ xlsx
wb = Workbook()
FILL = PatternFill("solid", fgColor="1F4E78")
FILL2 = PatternFill("solid", fgColor="DDEBF7")
BORDE = Border(*(Side(style="thin", color="BFBFBF"),) * 4)


def hoja(ws, titulo, cab, filas, anchos):
    ws.title = titulo
    ws.append(cab)
    for f in filas:
        ws.append([str(x).replace("`", "") for x in f])
    for i, w in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for celda in ws[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = FILL
        celda.alignment = Alignment(wrap_text=True, vertical="center")
    for fila in ws.iter_rows(min_row=2):
        for celda in fila:
            celda.alignment = Alignment(wrap_text=True, vertical="top")
            celda.border = BORDE
        fila[0].font = Font(bold=True)
        fila[0].fill = FILL2
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions


hoja(wb.active, "Matriz por CA", CAB_CA, filas_ca, [9, 30, 9, 11, 26, 14, 45, 32, 38, 16, 40, 14, 11])
hoja(wb.create_sheet(), "Reglas de negocio", CAB_RN, filas_rn, [8, 60, 26, 30, 50, 16, 26])
hoja(wb.create_sheet(), "Necesidades", ["Necesidad", "Descripción", "Prioridad", "User Stories", "Criterios", "BPMN"],
     [[n, d, p, ", ".join(TRAZA_NECESIDAD[n][0]), ", ".join(TRAZA_NECESIDAD[n][1]), TRAZA_NECESIDAD[n][2]]
      for n, d, p in NECESIDADES], [11, 60, 10, 30, 45, 40])
hoja(wb.create_sheet(), "User Stories", ["US", "Rol", "User Story", "Criterios", "Archivo Gherkin"],
     [[u, r, t, ", ".join(c["id"] for c in CA.values() if c["us"] == u), f"{area_de(u)}.feature"] for u, (r, t) in US.items()],
     [9, 18, 80, 30, 30])
hoja(wb.create_sheet(), "Specifications", ["#", "Specification", "Composición", "Operadores", "Regla", "Criterios"],
     [list(e) for e in ESPECS], [6, 30, 70, 12, 10, 30])
hoja(wb.create_sheet(), "Rutas API", ["Método", "Ruta", "Rol", "Descripción", "Éxito", "Errores", "Caso de uso", "Criterios", "Prioridad", "Área"],
     [[m, r, rol, d, ok, err, s, ", ".join(cas), p, a] for m, r, rol, d, ok, err, s, cas, p, a in RUTAS],
     [8, 50, 18, 50, 7, 22, 38, 30, 9, 16])
wb.save(T / "matriz-trazabilidad.xlsx")

# ============================================================================ api/README.md
A = DOCS / "api"
A.mkdir(parents=True, exist_ok=True)
api = ["# API REST — contrato planeado (PIA)\n",
       "Contrato de la API que se implementa con FastAPI (ADR-008). Cuando la API esté lista, FastAPI genera el contrato real en `/openapi.json` y Swagger UI en `/docs`; se exporta una copia a `docs/api/openapi.json` (`python -m api.exportar_openapi` o `curl http://localhost:8000/openapi.json -o docs/api/openapi.json`).\n",
       "## Convenciones\n",
       "- Base: `http://localhost:8000` (Docker Compose) y la URL de Render en producción. Prefijo `/api`.",
       "- Autenticación: `Authorization: Bearer <token>` del empleado (ADR-012). Públicas: `/health`, `/docs`, `/openapi.json`, `/api/consulta-de-estado`.",
       "- Errores con el formato `{\"error\": \"<TipoDeError>\", \"detalle\": \"<mensaje para el usuario>\", \"codigo\": <http>}`.",
       "- **201** crea · **200** acción o consulta · **400** JSON mal formado · **401** sin token o token inválido · **403** rol no permitido o trabajo de otro técnico · **404** no existe · **409** regla o transición violada · **422** dato inválido · **501** función P2 aún no implementada.",
       "- Además de los errores que lista cada ruta, cualquier ruta con cuerpo JSON responde **400** si está mal formado, y cualquier ruta que reciba datos (cuerpo, ruta o parámetros) responde **422** si uno es inválido. FastAPI lee el JSON antes de revisar el token: un JSON mal formado responde 400 aunque falte el token.",
       "- Importes como texto con dos decimales (`\"1500.00\"`); fechas ISO 8601 con zona horaria.\n",
       f"## Rutas ({len(RUTAS)})\n"]
areas = []
for r in RUTAS:
    if r[9] not in areas:
        areas.append(r[9])
for area in areas:
    api.append(f"### {area}\n")
    api += tabla(["Método", "Ruta", "Rol", "Descripción", "Éxito", "Errores", "Caso de uso", "Criterios", "Prioridad"],
                 [[m, f"`{r}`", rol, d, ok, err, f"`{s}`" if s != "—" else s, ", ".join(cas) or "—", p]
                  for m, r, rol, d, ok, err, s, cas, p, a in RUTAS if a == area])
    api.append("")
api += ["## Ejemplos\n",
        "**Registrar una orden** (`POST /api/ordenes`, token de Asesor) → respuesta `201` con el mensaje de éxito de CA-001:\n",
        "```json\n{\"numero_orden\": \"OS-0001\", \"estado\": \"Recibida\", \"id_cliente\": \"CLI-0001\", \"placas\": \"ABC123\",\n \"fecha_ingreso\": \"2026-10-05T15:00:00Z\", \"mensaje\": \"Orden OS-0001 registrada correctamente.\"}\n```\n",
        "**Generar la cotización inicial** (`POST /api/ordenes/AUT-O007/cotizaciones`, token de Asesor):\n",
        "```json\n{\n  \"trabajos\": [\n    {\"numero\": 1, \"descripcion\": \"Afinación 07 (AUT-P007) x1\", \"mano_de_obra\": \"785.00\", \"refacciones\": []},\n    {\"numero\": 2, \"descripcion\": \"Cambio aceite 12 (AUT-P012) x2\", \"mano_de_obra\": \"2280.00\", \"refacciones\": []}\n  ]\n}\n```\n",
        "Respuesta `201`:\n",
        "```json\n{\"id\": \"COT-0001\", \"numero_orden\": \"AUT-O007\", \"version\": \"v.1\", \"tipo\": \"Inicial\",\n \"estado\": \"Pendiente de Autorización del Cliente\", \"total\": \"3065.00\"}\n```\n",
        "**Entregar sin pago registrado** (`POST /api/ordenes/AUT-O006/entrega` con la orden «Autorizada») → `409`:\n",
        "```json\n{\"error\": \"EntregaNoPermitida\", \"codigo\": 409,\n \"detalle\": \"No se puede entregar el vehículo de la orden AUT-O006 (estado «Autorizada»): primero debe registrarse el pago o el cargo a crédito.\"}\n```\n",
        "**Consulta pública con datos que no coinciden** (`GET /api/consulta-de-estado?orden=AUT-O007&placas=XXX000`) → `404`:\n",
        "```json\n{\"error\": \"OrdenNoEncontrada\", \"detalle\": \"No se encontró una orden con esos datos\", \"codigo\": 404}\n```\n",
        "Los importes del ejemplo salen de los datos del profesor: AUT-O007 tiene AUT-P007 × 1 ($785.00) y AUT-P012 × 2 ($1,140.00) = $785.00 + $2,280.00 = **$3,065.00**.\n",
        "**Cotizar una orden con un servicio inhabilitado** (`POST /api/ordenes/AUT-O005/cotizaciones`, D-05 y H-PIA-19) → `422`, y la orden sigue «En Diagnóstico»:\n",
        "```json\n{\"error\": \"ValorInvalido\", \"codigo\": 422,\n \"detalle\": \"No se puede cotizar la orden AUT-O005: incluye servicios inhabilitados (AUT-P011).\"}\n```"]
(A / "README.md").write_text("\n".join(api) + "\n", encoding="utf-8")
print("ok", len(filas_ca), len(filas_rn), len(RUTAS))
