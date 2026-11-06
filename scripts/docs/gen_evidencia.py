"""Genera docs/trazabilidad/evidencia-pruebas.md corriendo pytest con cobertura.

Uso, desde la raíz y con una base local desechable (nunca Supabase):
    python scripts/docs/gen_evidencia.py

Si alguna prueba falla o la cobertura baja de 80 %, no escribe nada.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[2]
MATRIZ = RAIZ / "docs" / "trazabilidad" / "matriz-trazabilidad.md"
DESTINO = RAIZ / "docs" / "trazabilidad" / "evidencia-pruebas.md"
NOMBRE_CON_ID = re.compile(r"^test_(ca_\d{3}|rn_\d{2})_")
ZONA_HORARIA = ZoneInfo("America/Monterrey")

# La Fase 10 se omitió (decisiones-tecnicas.md §8): una prueba que comprueba el 501 no es
# evidencia de que la función exista, así que estos criterios no se presentan como cumplidos.
ESTADO_POR_OMISION_P2 = {
    "CA-002": "Parcial: datos de ingreso sí; fotos de daños no (la ruta responde 501).",
    "CA-005": "Parcial: cotización sí; PDF no (la ruta responde 501).",
    "CA-024": "Parcial: retiro y firma sí; PDF de la nota no (la ruta responde 501).",
    "CA-027": "No implementado: la prueba solo comprueba que la ruta responde 501.",
}


@dataclass
class Evidencia:
    aprobadas: int = 0
    omitidas: int = 0
    pruebas: set[str] = field(default_factory=set)


def correr_pruebas(junit: Path, cobertura: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            f"--junitxml={junit}",
            "--cov=src",
            "--cov-branch",
            f"--cov-report=json:{cobertura}",
            "--cov-fail-under=80",
        ],
        cwd=RAIZ,
        env={**os.environ, "APP_ENV": "pruebas"},
        check=True,
    )


def leer_casos(junit: Path) -> list[ET.Element]:
    return list(ET.parse(junit).getroot().iter("testcase"))


def evidencia_por_id(casos: list[ET.Element]) -> dict[str, Evidencia]:
    evidencia: dict[str, Evidencia] = defaultdict(Evidencia)
    for caso in casos:
        nombre = caso.attrib["name"].split("[")[0]
        coincidencia = NOMBRE_CON_ID.match(nombre)
        if coincidencia is None:
            continue
        identificador = coincidencia.group(1).upper().replace("_", "-")
        registro = evidencia[identificador]
        if caso.find("skipped") is not None:
            registro.omitidas += 1
        else:
            registro.aprobadas += 1
        archivo = caso.attrib["classname"].replace(".", "/")
        registro.pruebas.add(f"`{archivo}.py::{nombre}`")
    return evidencia


def titulos_de_la_matriz(prefijo: str) -> dict[str, str]:
    patron = rf"^\| ({prefijo}-\d+) \| ([^|]+?) \|"
    texto = MATRIZ.read_text(encoding="utf-8")
    return dict(re.findall(patron, texto, flags=re.MULTILINE))


def resultado(identificador: str, registro: Evidencia) -> str:
    conteo = f"aprobadas: {registro.aprobadas}"
    if registro.omitidas:
        conteo += f", omitidas: {registro.omitidas}"
    nota = ESTADO_POR_OMISION_P2.get(identificador)
    return f"{nota} ({conteo})" if nota else f"Cubierto ({conteo})"


def tabla(titulos: dict[str, str], evidencia: dict[str, Evidencia]) -> list[str]:
    faltantes = [identificador for identificador in titulos if identificador not in evidencia]
    if faltantes:
        raise SystemExit(f"Sin prueba: {', '.join(faltantes)}")
    filas = ["| ID | Descripción | Resultado | Pruebas |", "|---|---|---|---|"]
    for identificador, titulo in titulos.items():
        registro = evidencia[identificador]
        pruebas = "<br>".join(sorted(registro.pruebas))
        filas.append(
            f"| {identificador} | {titulo} | {resultado(identificador, registro)} | {pruebas} |"
        )
    return filas


def contar_en(casos: list[ET.Element], paquete: str) -> int:
    return sum(1 for caso in casos if caso.attrib["classname"].startswith(paquete))


def motor_de_pruebas() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if "supabase" in url.lower():
        raise SystemExit("DATABASE_URL apunta a Supabase: las pruebas nunca corren contra ella.")
    return "PostgreSQL local" if url.startswith("postgresql") else "SQLite en memoria"


def documento(casos: list[ET.Element], cobertura: dict, motor: str) -> str:
    evidencia = evidencia_por_id(casos)
    omitidas = sum(1 for caso in casos if caso.find("skipped") is not None)
    totales = cobertura["totals"]
    fecha = datetime.now(ZONA_HORARIA).strftime("%d/%m/%Y %H:%M")
    lineas = [
        "# Evidencia de pruebas",
        "",
        "Generado por `scripts/docs/gen_evidencia.py`; no se edita a mano.",
        "",
        "## Resumen",
        "",
        f"- **Ejecución:** {fecha} (America/Monterrey), con {motor}.",
        f"- **Pruebas:** {len(casos) - omitidas} aprobadas, {omitidas} omitidas, 0 fallidas.",
        f"- **Cobertura:** {totales['percent_covered']:.2f} % con ramas "
        f"({totales['covered_lines']} de {totales['num_statements']} líneas, "
        f"{totales['covered_branches']} de {totales['num_branches']} ramas).",
        f"- **Datos del profesor:** {contar_en(casos, 'tests.datos_profesor')} pruebas; "
        "los resultados están en `reportes/`.",
        "",
        "**Alcance:** la Fase 10 (PDF y fotos de daños) se omitió por decisión del equipo. "
        "CA-027 no está implementado, y CA-002, CA-005 y CA-024 están implementados salvo sus "
        "fotos o su PDF. Las tablas lo indican en «Resultado».",
        "",
        "## Criterios de aceptación",
        "",
        *tabla(titulos_de_la_matriz("CA"), evidencia),
        "",
        "## Reglas de negocio",
        "",
        *tabla(titulos_de_la_matriz("RN"), evidencia),
        "",
    ]
    return "\n".join(lineas)


def main() -> None:
    motor = motor_de_pruebas()
    with tempfile.TemporaryDirectory() as carpeta:
        junit = Path(carpeta) / "pruebas.xml"
        cobertura = Path(carpeta) / "cobertura.json"
        try:
            correr_pruebas(junit, cobertura)
        except subprocess.CalledProcessError as error:
            raise SystemExit("Las pruebas no pasaron: no se generó la evidencia.") from error
        contenido = documento(
            leer_casos(junit), json.loads(cobertura.read_text(encoding="utf-8")), motor
        )
    DESTINO.write_text(contenido, encoding="utf-8", newline="\n")
    print(f"Escrito: {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
