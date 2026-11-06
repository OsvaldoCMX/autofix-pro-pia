"""Cada prueba de integración recibe una base limpia: SQLite en memoria o PostgreSQL local."""
from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine

from infrastructure.base_de_datos.motor import URL_DE_SQLITE_EN_MEMORIA, crear_motor
from tests.integration.apoyo_base import (
    ServidorNoPermitido,
    crear_esquema,
    ejecutar_script,
    eliminar_esquema,
    preparar_base,
    url_con_esquema,
    url_de_postgresql_para_pruebas,
)
from tests.unit.application.escenarios import EMPLEADOS


@pytest.fixture(scope="session")
def url_postgresql() -> str | None:
    try:
        return url_de_postgresql_para_pruebas()
    except ServidorNoPermitido as error:
        pytest.exit(str(error), returncode=2)


@pytest.fixture(scope="session")
def motor_postgresql(url_postgresql: str | None) -> Iterator[Engine | None]:
    """Un solo esquema privado por ejecución, creado con el `01_esquema.sql` real."""
    if url_postgresql is None:
        yield None
        return
    esquema = f"pruebas_{os.getpid()}"
    crear_esquema(url_postgresql, esquema)
    motor = crear_motor(url_con_esquema(url_postgresql, esquema))
    try:
        ejecutar_script(motor, "01_esquema.sql")
        yield motor
    finally:
        motor.dispose()
        eliminar_esquema(url_postgresql, esquema)


@pytest.fixture
def motor(motor_postgresql: Engine | None) -> Iterator[Engine]:
    if motor_postgresql is not None:
        preparar_base(motor_postgresql, EMPLEADOS)
        yield motor_postgresql
        assert motor_postgresql.pool.checkedout() == 0, "Una prueba dejó una conexión abierta."
        return
    sqlite = crear_motor(URL_DE_SQLITE_EN_MEMORIA)
    preparar_base(sqlite, EMPLEADOS)
    yield sqlite
    sqlite.dispose()
