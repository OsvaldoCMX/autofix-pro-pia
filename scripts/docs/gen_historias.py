"""Genera docs/user-stories.md y docs/gherkin/*.feature desde datos.py."""
import sys
from pathlib import Path

from datos import AREAS, CA, NECESIDADES, TRAZA_NECESIDAD, US, area_de, validar

DOCS = Path(sys.argv[1])
n_nec, n_us, n_ca, n_rn = validar()

CAMBIOS_CA = {
    "H-PIA-01": "nuevo criterio (cancelación antes de la cotización)",
    "H-PIA-02": "el crédito se cuenta desde la entrega",
    "H-PIA-06": "nuevo criterio (no se trabaja un vehículo retirado)",
    "H-PIA-07": "regreso a «En Reparación» si ya había trabajos iniciados",
    "H-PIA-10": "precisión del seguimiento de la alerta",
    "H-PIA-11": "el recibo también se puede generar con la orden cerrada",
    "H-PIA-12": "la orden no queda lista mientras haya una cotización adicional sin decisión",
}
# criterios cuyo TEXTO cambió en v3.0 (los demás hallazgos afectan el modelo, no la redacción)
TEXTO_CAMBIADO = {"CA-015", "CA-018", "CA-022", "CA-023", "CA-025", "CA-027", "CA-039", "CA-040", "CA-041",
                  "CA-044", "CA-045", "CA-046"}
# criterios de la revisión del 09/11/2026 (v3.1): hallazgos H-PIA-21 en adelante
NUEVOS_V31 = {c["id"] for c in CA.values() if c["cambio"] and int(c["cambio"].split("-")[-1]) >= 21}


def cas_de(us):
    return [c for c in CA.values() if c["us"] == us]


def bloque_md(c):
    lineas = []
    for kw, texto in c["pasos"]:
        lineas.append(f"**{kw}** {texto}")
    return "<br>".join(lineas)


# ============================================================================ user-stories.md
md = []
md.append("# User Stories y Criterios de Aceptación — AutoFix Pro\n")
md.append("**Materia:** Componentes de Lógica de Negocio · FIME UANL · **Equipo 6**  ")
md.append("**Versión:** 3.1 (revisión del 09/11/2026)\n")
md.append("| Versión | Fecha | Cambios |\n|---|---|---|")
md.append("| 1.0 | 03/09/2026 | Unidad 2: 18 User Stories y sus criterios. |")
md.append("| 2.0 | 10/2026 | Unidad 3: hallazgos H-U2-01 a H-U2-03 (se agregaron US-019 a US-024); 24 User Stories y 43 criterios. |")
md.append("| 3.0 | 04/11/2026 | PIA: US-025 (cancelación), CA-044 a CA-046, crédito desde la entrega y precisiones en CA-015, CA-018, CA-022, CA-023, CA-025, CA-027, CA-039, CA-040 y CA-041. Los criterios ahora también están en Gherkin formal (`gherkin/*.feature`). Detalle en `registro-de-cambios.md`. |")
md.append("| 3.1 | 09/11/2026 | Revisión del profesor como usuario del taller: correcciones de datos mal capturados y prevención de registros repetidos (H-PIA-21 en adelante, necesidad N-16, desde US-026 y CA-047). Los criterios marcados **(v3.1)** son nuevos; los que tienen la marca «Planeado» en la matriz de trazabilidad todavía no se construyen. |\n")
md.append(
    "Este documento contiene las User Stories derivadas del levantamiento de requerimientos del sistema "
    "de gestión de taller AutoFix Pro. Cada historia representa una funcionalidad que el sistema debe "
    "proporcionar a un rol específico para resolver los problemas de la operación actual (AS-IS), como la "
    "falta de evidencia en las autorizaciones o la falta de visibilidad del estado de las reparaciones.\n")
md.append(
    "Las historias siguen el formato *Como… quiero… para…* y cada criterio de aceptación está escrito en "
    "Gherkin (*Dado / Cuando / Entonces / Y*). Los mismos criterios, palabra por palabra, están en los "
    "archivos `docs/gherkin/*.feature` con las etiquetas `@US-xxx` y `@CA-xxx`, para que cada escenario se "
    "pueda relacionar con su prueba automatizada (convención `test_ca_0XX_…`). Los nombres de estados, roles "
    "y términos son los del [Glosario del Dominio](glosario.md).\n")
md.append(f"**Resumen:** {n_nec} necesidades · {n_us} User Stories · {n_ca} criterios de aceptación · "
          f"{len(AREAS)} archivos `.feature`.\n")

md.append("## 1. Trazabilidad con el BRD\n")
md.append("| ID Necesidad | Descripción de la necesidad | User Stories vinculadas |\n|---|---|---|")
for nid, desc, _prio in NECESIDADES:
    md.append(f"| {nid} | {desc} | {', '.join(TRAZA_NECESIDAD[nid][0])} |")

md.append("\n## 2. Listado de User Stories\n")
md.append("| ID | Rol | User Story | Archivo Gherkin |\n|---|---|---|---|")
for uid, (rol, texto) in US.items():
    md.append(f"| {uid} | {rol} | {texto} | `{area_de(uid)}.feature` |")

md.append("\n## 3. Criterios de aceptación en Gherkin\n")
md.append("Los criterios marcados con **(v3.0)** se agregaron o se precisaron en el PIA y los marcados con "
          "**(v3.1)** salen de la revisión del 09/11/2026; el hallazgo que lo justifica se indica entre paréntesis.\n")
for uid, (_rol, texto) in US.items():
    md.append(f"### {uid}\n")
    md.append(f"> {texto}\n")
    md.append("| ID | Criterio de aceptación |\n|---|---|")
    for c in cas_de(uid):
        marca = ""
        if c["id"] in TEXTO_CAMBIADO:
            marca = f" **(v3.0, {c['cambio']})**"
        elif c["id"] in NUEVOS_V31:
            marca = f" **(v3.1, {c['cambio']})**"
        md.append(f"| **{c['id']}**<br>{c['nombre']}{marca} | {bloque_md(c)} |")
    md.append("")

md.append("## 4. Validación y trazabilidad\n")
md.append("| ID Necesidad | User Stories relacionadas | Criterios de aceptación | Proceso modelado en BPMN |\n|---|---|---|---|")
for nid, _d, _p in NECESIDADES:
    us_, cas, bpmn = TRAZA_NECESIDAD[nid]
    md.append(f"| {nid} | {', '.join(us_)} | {', '.join(cas)} | {bpmn} |")
md.append("\nLa trazabilidad completa de cada criterio hasta la regla de negocio, el componente, la ruta de la API "
          "y la prueba está en [trazabilidad/matriz-trazabilidad.md](trazabilidad/matriz-trazabilidad.md).\n")
md.append("## 5. Bibliografía\n")
md.append("- Cohn, M. (2004). *User stories applied: For agile software development*. Addison-Wesley.")
md.append("- Evans, E. (2003). *Domain-driven design: Tackling complexity in the heart of software*. Addison-Wesley Professional.")
md.append("- Lee, C. (2023). *The art of crafting user stories* (1st ed.). Packt Publishing.")
md.append("- SmartBear. (s. f.). *Gherkin reference*. Cucumber. https://cucumber.io/docs/gherkin/reference/")
md.append("- Vernon, V. (2013). *Implementing domain-driven design*. Addison-Wesley Professional.")
(DOCS / "user-stories.md").write_text("\n".join(md) + "\n", encoding="utf-8")

# ============================================================================ .feature
GH = DOCS / "gherkin"
GH.mkdir(parents=True, exist_ok=True)
indice = ["# Escenarios Gherkin — AutoFix Pro\n",
          "Cada archivo agrupa las User Stories de un área del proceso. Cada **Escenario** es un criterio de "
          "aceptación con el mismo texto que `../user-stories.md` y lleva las etiquetas `@US-xxx` y `@CA-xxx`.\n",
          "Los archivos usan `# language: es`, por lo que las palabras clave están en español "
          "(`Característica`, `Escenario`, `Dado`, `Cuando`, `Entonces`, `Y`). Se pueden ejecutar con "
          "`pytest-bdd` o `behave`, o servir como especificación para las pruebas `test_ca_0XX_…` "
          "(ver `../architecture/decisiones-tecnicas.md`).\n",
          "| Archivo | Característica | User Stories | Escenarios |\n|---|---|---|---|"]
total = 0
for clave, titulo, desc, lista in AREAS:
    f = ["# language: es", f"@{clave.split('_', 1)[1].replace('_', '-')}", f"Característica: {titulo}",
         f"  {desc}", "", "  User Stories de esta característica:"]
    for uid in lista:
        f.append(f"    {uid}: {US[uid][1]}")
    n_esc = 0
    for uid in lista:
        f.append("")
        f.append(f"  # ---------------------------------------------------------------- {uid} ({US[uid][0]})")
        for c in cas_de(uid):
            f.append("")
            etiquetas = f"@{uid} @{c['id']}"
            if c["id"] in TEXTO_CAMBIADO:
                etiquetas += " @v3"
            elif c["id"] in NUEVOS_V31:
                etiquetas += " @v3.1"
            f.append(f"  {etiquetas}")
            f.append(f"  Escenario: {c['id']} {c['nombre']}")
            for kw, texto in c["pasos"]:
                f.append(f"    {kw} {texto}")
            n_esc += 1
    total += n_esc
    (GH / f"{clave}.feature").write_text("\n".join(f) + "\n", encoding="utf-8")
    indice.append(f"| `{clave}.feature` | {titulo} | {', '.join(lista)} | {n_esc} |")
indice.append(f"| **Total** | {len(AREAS)} características | {len(US)} | **{total}** |")
indice.append("\nLa etiqueta `@v3` marca los escenarios que se agregaron o precisaron en el PIA y `@v3.1`, los de "
              "la revisión del 09/11/2026 (H-PIA-21 en adelante).")
(GH / "README.md").write_text("\n".join(indice) + "\n", encoding="utf-8")
assert total == n_ca
print("ok", n_us, n_ca, total)
