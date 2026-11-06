"""Trazabilidad: cada criterio de los `.feature` y cada regla de la matriz tienen su prueba.

Lee los nombres reales de las funciones con `ast`: un comentario o un texto no cuenta como prueba.
"""
from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GHERKIN = RAIZ / "docs" / "gherkin"
MATRIZ = RAIZ / "docs" / "trazabilidad" / "matriz-trazabilidad.md"
PRUEBAS = RAIZ / "tests"
CRITERIOS_ESPERADOS = {f"CA-{numero:03d}" for numero in range(1, 47)}
REGLAS_ESPERADAS = {f"RN-{numero:02d}" for numero in range(1, 25)}


def criterios_de_los_feature() -> set[str]:
    return {
        criterio
        for archivo in GHERKIN.glob("*.feature")
        for criterio in re.findall(r"CA-\d{3}", archivo.read_text(encoding="utf-8"))
    }


def reglas_de_la_matriz() -> set[str]:
    return set(re.findall(r"^\| (RN-\d{2}) \|", _matriz(), flags=re.MULTILINE))


def _matriz() -> str:
    return MATRIZ.read_text(encoding="utf-8")


def nombres_de_pruebas(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    return {
        nodo.name
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.FunctionDef) and nodo.name.startswith("test_")
    }


def pruebas_del_repositorio() -> set[str]:
    return {nombre for archivo in PRUEBAS.rglob("test_*.py") for nombre in nombres_de_pruebas(archivo)}


def sin_prueba(identificadores: Iterable[str], nombres: set[str]) -> list[str]:
    """`CA-044` necesita una prueba `test_ca_044_…`; `RN-07`, una `test_rn_07_…`."""
    return sorted(
        identificador
        for identificador in identificadores
        if not any(nombre.startswith(_prefijo(identificador)) for nombre in nombres)
    )


def _prefijo(identificador: str) -> str:
    tipo, numero = identificador.split("-")
    return f"test_{tipo.lower()}_{numero}_"


def test_cada_criterio_de_los_feature_tiene_prueba() -> None:
    criterios = criterios_de_los_feature()

    assert criterios == CRITERIOS_ESPERADOS
    assert sin_prueba(criterios, pruebas_del_repositorio()) == []


def test_cada_regla_tiene_prueba() -> None:
    reglas = reglas_de_la_matriz()

    assert reglas == REGLAS_ESPERADAS
    assert sin_prueba(reglas, pruebas_del_repositorio()) == []


def test_la_matriz_apunta_a_pruebas_que_existen() -> None:
    referencias = re.findall(r"(tests/[\w/]+\.py)::(test_ca_\d{3}_)\*", _matriz())

    assert {prefijo for _, prefijo in referencias} == {
        _prefijo(criterio) for criterio in CRITERIOS_ESPERADOS
    }
    faltantes = [
        f"{ruta}::{prefijo}*"
        for ruta, prefijo in referencias
        if not any(n.startswith(prefijo) for n in nombres_de_pruebas(RAIZ / ruta))
    ]
    assert faltantes == []


def test_la_verificacion_detecta_un_criterio_sin_prueba() -> None:
    nombres = {"test_ca_001_registra_la_orden", "test_ca_0021_no_es_del_criterio_002"}

    assert sin_prueba({"CA-001", "CA-002"}, nombres) == ["CA-002"]


def test_la_verificacion_detecta_una_regla_sin_prueba() -> None:
    assert sin_prueba({"RN-01", "RN-02"}, {"test_rn_01_algo"}) == ["RN-02"]
