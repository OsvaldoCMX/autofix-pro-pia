"""Verifica la regla de dependencias entre capas: api -> application -> domain.

infrastructure puede usar application y domain. Solo api/dependencias.py (Composition Root)
decide qué implementación se usa, así que es el único archivo de api que importa infrastructure.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
CAPAS = ("domain", "application", "infrastructure", "api")
COMPOSITION_ROOT = "dependencias.py"

PROHIBIDOS = {
    "domain": {"application", "infrastructure", "api", "fastapi", "pydantic", "sqlalchemy"},
    "application": {"infrastructure", "api", "fastapi", "sqlalchemy"},
    "infrastructure": {"api"},
}


def _paquete_actual(archivo: Path, raiz: Path) -> list[str]:
    relativo = archivo.relative_to(raiz)
    return list(relativo.parts[:-1])


def importaciones_de(archivo: Path, raiz: Path) -> set[str]:
    """Devuelve el primer nombre de cada módulo importado, resolviendo los imports relativos."""
    paquete = _paquete_actual(archivo, raiz)
    modulos: set[str] = set()
    for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level == 0:
                modulos.add((nodo.module or "").split(".")[0])
                continue
            base = paquete[: max(len(paquete) - (nodo.level - 1), 0)]
            destinos = [nodo.module] if nodo.module else [alias.name for alias in nodo.names]
            modulos.update((base + destino.split("."))[0] for destino in destinos)
    return modulos


def violaciones(capa: str, prohibidos: set[str], raiz: Path = SRC) -> dict[str, set[str]]:
    resultado: dict[str, set[str]] = {}
    for archivo in (raiz / capa).rglob("*.py"):
        encontrados = importaciones_de(archivo, raiz) & prohibidos
        if encontrados:
            resultado[str(archivo.relative_to(raiz))] = encontrados
    return resultado


def violaciones_del_composition_root(raiz: Path = SRC) -> dict[str, set[str]]:
    todas = violaciones("api", {"infrastructure"}, raiz)
    permitido = str(Path("api") / COMPOSITION_ROOT)
    return {archivo: modulos for archivo, modulos in todas.items() if archivo != permitido}


def _crear_modulo(raiz: Path, ruta: str, contenido: str) -> None:
    archivo = raiz / ruta
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(contenido, encoding="utf-8")


@pytest.mark.parametrize("capa", CAPAS)
def test_la_capa_existe_y_tiene_modulos(capa: str) -> None:
    assert list((SRC / capa).rglob("*.py")), f"src/{capa} no tiene módulos que revisar"


@pytest.mark.parametrize(("capa", "prohibidos"), PROHIBIDOS.items())
def test_la_capa_respeta_la_regla_de_dependencias(capa: str, prohibidos: set[str]) -> None:
    assert violaciones(capa, prohibidos) == {}


def test_solo_el_composition_root_importa_infrastructure() -> None:
    assert violaciones_del_composition_root() == {}


@pytest.mark.parametrize(
    "contenido",
    [
        "import fastapi\n",
        "import sqlalchemy.orm\n",
        "from pydantic import BaseModel\n",
        "from infrastructure.memoria import repositorios\n",
        "from ...infrastructure import config\n",
        "from ... import api\n",
    ],
)
def test_el_detector_encuentra_imports_prohibidos(tmp_path: Path, contenido: str) -> None:
    _crear_modulo(tmp_path, "domain/ordenes/modulo.py", contenido)

    assert violaciones("domain", PROHIBIDOS["domain"], tmp_path)


def test_el_detector_resuelve_un_import_relativo_a_la_capa_correcta(tmp_path: Path) -> None:
    _crear_modulo(tmp_path, "domain/ordenes/modulo.py", "from ...infrastructure import config\n")
    _crear_modulo(tmp_path, "domain/ordenes/interno.py", "from ..infrastructure import config\n")

    encontrados = violaciones("domain", PROHIBIDOS["domain"], tmp_path)

    assert encontrados == {str(Path("domain/ordenes/modulo.py")): {"infrastructure"}}


@pytest.mark.parametrize(
    "contenido",
    [
        "import api_externa\n",
        "from decimal import Decimal\n",
        "from domain.compartido import valores\n",
        "from . import valores\n",
        "from ..compartido import valores\n",
    ],
)
def test_el_detector_acepta_imports_permitidos(tmp_path: Path, contenido: str) -> None:
    _crear_modulo(tmp_path, "domain/ordenes/modulo.py", contenido)

    assert violaciones("domain", PROHIBIDOS["domain"], tmp_path) == {}


def test_el_composition_root_puede_importar_infrastructure(tmp_path: Path) -> None:
    _crear_modulo(tmp_path, "api/dependencias.py", "from infrastructure import config\n")

    assert violaciones_del_composition_root(tmp_path) == {}


def test_otro_archivo_de_api_no_puede_importar_infrastructure(tmp_path: Path) -> None:
    _crear_modulo(tmp_path, "api/rutas/recepcion.py", "from infrastructure import config\n")

    assert violaciones_del_composition_root(tmp_path) == {
        str(Path("api/rutas/recepcion.py")): {"infrastructure"}
    }
