"""Trazabilidad: cada criterio de los `.feature` y cada regla de la matriz tienen su prueba.

Lee los nombres reales de las funciones con `ast`: un comentario o un texto no cuenta como prueba.

Un criterio o una regla con la marca «Planeado» en la matriz está aprobado (Fase 13) pero todavía
no se construye: no se le exige prueba y, al revés, no puede tenerla. Así, quien lo construya en la
Fase 14 tiene que quitar la marca en `scripts/docs/datos.py` y regenerar la matriz.
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
CRITERIOS_ESPERADOS = {f"CA-{numero:03d}" for numero in range(1, 59)}
REGLAS_ESPERADAS = {f"RN-{numero:02d}" for numero in range(1, 31)}
MARCA_DE_PLANEADO = "Planeado"


def criterios_de_los_feature() -> set[str]:
    return {
        criterio
        for archivo in GHERKIN.glob("*.feature")
        for criterio in re.findall(r"CA-\d{3}", archivo.read_text(encoding="utf-8"))
    }


def reglas_de_la_matriz() -> set[str]:
    return set(re.findall(r"^\| (RN-\d{2}) \|", _matriz(), flags=re.MULTILINE))


def planeados_de_la_matriz(tipo: str, texto: str | None = None) -> set[str]:
    """Identificadores (`CA` o `RN`) cuya fila de la matriz lleva la marca «Planeado»."""
    filas = re.findall(rf"^\| ({tipo}-\d+) \|(.*)$", texto or _matriz(), flags=re.MULTILINE)
    return {identificador for identificador, resto in filas if MARCA_DE_PLANEADO in resto}


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


def con_prueba(identificadores: Iterable[str], nombres: set[str]) -> list[str]:
    """Los planeados que ya tienen prueba: hay que quitarles la marca."""
    lista = list(identificadores)
    return sorted(set(lista) - set(sin_prueba(lista, nombres)))


def _prefijo(identificador: str) -> str:
    tipo, numero = identificador.split("-")
    return f"test_{tipo.lower()}_{numero}_"


def test_cada_criterio_de_los_feature_tiene_prueba() -> None:
    criterios = criterios_de_los_feature()
    planeados = planeados_de_la_matriz("CA")
    nombres = pruebas_del_repositorio()

    assert criterios == CRITERIOS_ESPERADOS
    assert planeados <= criterios
    assert sin_prueba(criterios - planeados, nombres) == []
    assert con_prueba(planeados, nombres) == [], "Quite la marca «Planeado» en datos.py"


def test_cada_regla_tiene_prueba() -> None:
    reglas = reglas_de_la_matriz()
    planeadas = planeados_de_la_matriz("RN")
    nombres = pruebas_del_repositorio()

    assert reglas == REGLAS_ESPERADAS
    assert planeadas <= reglas
    assert sin_prueba(reglas - planeadas, nombres) == []
    assert con_prueba(planeadas, nombres) == [], "Quite la marca «Planeado» en datos.py"


def test_la_matriz_apunta_a_pruebas_que_existen() -> None:
    referencias = re.findall(r"(tests/[\w/]+\.py)::(test_ca_\d{3}_)\*", _matriz())
    planeados = {_prefijo(criterio) for criterio in planeados_de_la_matriz("CA")}

    assert {prefijo for _, prefijo in referencias} == {
        _prefijo(criterio) for criterio in CRITERIOS_ESPERADOS
    }
    faltantes = [
        f"{ruta}::{prefijo}*"
        for ruta, prefijo in referencias
        if prefijo not in planeados
        and not any(n.startswith(prefijo) for n in nombres_de_pruebas(RAIZ / ruta))
    ]
    assert faltantes == []


def test_la_verificacion_detecta_un_criterio_sin_prueba() -> None:
    nombres = {"test_ca_001_registra_la_orden", "test_ca_0021_no_es_del_criterio_002"}

    assert sin_prueba({"CA-001", "CA-002"}, nombres) == ["CA-002"]


def test_la_verificacion_detecta_una_regla_sin_prueba() -> None:
    assert sin_prueba({"RN-01", "RN-02"}, {"test_rn_01_algo"}) == ["RN-02"]


def test_la_verificacion_detecta_un_planeado_que_ya_tiene_prueba() -> None:
    nombres = {"test_ca_047_corrige_la_cotizacion"}

    assert con_prueba({"CA-047", "CA-048"}, nombres) == ["CA-047"]


def test_la_marca_de_planeado_se_lee_de_la_fila_de_la_matriz() -> None:
    texto = "| CA-046 | Algo | P1 |  |\n| CA-047 | Otro | P1 · Planeado | H-PIA-21 |\n"

    assert planeados_de_la_matriz("CA", texto) == {"CA-047"}
