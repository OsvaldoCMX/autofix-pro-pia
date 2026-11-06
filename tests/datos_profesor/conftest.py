"""La aplicación completa sobre la base de pruebas, con el reloj después de todas las solicitudes."""
from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from api.dependencias import crear_contenedor
from api.main import crear_app
from application.puertos import Reloj
from infrastructure.config import Configuracion
from tests.api.pasos import TOKENS
from tests.datos_profesor.adaptador import DATOS, RAIZ, leer_csv
from tests.datos_profesor.reporte import Reporte
from tests.unit.application.escenarios import poner_hora

LUNES_DESPUES_DE_LAS_SOLICITUDES = datetime(2026, 10, 26, 15, 0, tzinfo=UTC)
REPORTES = RAIZ / "reportes"
COLUMNAS_DE_CASOS = [
    "caso_id",
    "operacion_id",
    "tipo_prueba",
    "regla_a_verificar",
    "resultado_alumno",
    "instrucciones",
    "esperado_autofix",
    "referencia_profesor",
    "referencia_obtenida",
    "diferencia",
    "coincide",
    "prueba",
    "mensaje_del_dominio",
]
COLUMNAS_DE_TRANSICIONES = [
    "caso_id",
    "operacion_id",
    "accion_sugerida",
    "estado_inicial",
    "resultado_alumno",
    "instrucciones",
    "estado_final",
    "evento_o_excepcion",
    "http",
    "coincide",
    "prueba",
    "mensaje_del_dominio",
]


@pytest.fixture
def cliente(motor: Engine) -> TestClient:
    reloj = Mock(spec=Reloj)
    poner_hora(reloj, LUNES_DESPUES_DE_LAS_SOLICITUDES)
    configuracion = Configuracion(app_env="pruebas", tokens=TOKENS)
    return TestClient(crear_app(crear_contenedor(configuracion, reloj, motor)))


def _reporte(archivo: str, columnas: list[str], origen: str) -> Iterator[Reporte]:
    casos = [fila["caso_id"] for fila in leer_csv(DATOS / origen)]
    reporte = Reporte(REPORTES / archivo, columnas, casos)
    yield reporte
    reporte.escribir_si_esta_completo()


@pytest.fixture(scope="session")
def reporte_de_casos() -> Iterator[Reporte]:
    yield from _reporte("resultados_casos.csv", COLUMNAS_DE_CASOS, "casos_prueba.csv")


@pytest.fixture(scope="session")
def reporte_de_transiciones() -> Iterator[Reporte]:
    yield from _reporte(
        "resultados_transiciones.csv", COLUMNAS_DE_TRANSICIONES, "transiciones_prueba.csv"
    )
