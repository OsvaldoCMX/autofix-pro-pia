"""Cada prueba de API recibe la aplicación completa, sobre una base limpia y con reloj falso."""
from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from api.dependencias import Contenedor, crear_contenedor
from api.main import crear_app
from application.puertos import Reloj
from infrastructure.config import Configuracion
from tests.api.pasos import TOKENS
from tests.unit.application.escenarios import AHORA, poner_hora


@pytest.fixture
def reloj() -> Mock:
    falso = Mock(spec=Reloj)
    poner_hora(falso, AHORA)
    return falso


@pytest.fixture
def contenedor(motor: Engine, reloj: Mock) -> Contenedor:
    return crear_contenedor(Configuracion(app_env="pruebas", tokens=TOKENS), reloj, motor)


@pytest.fixture
def cliente(contenedor: Contenedor) -> TestClient:
    return TestClient(crear_app(contenedor))
