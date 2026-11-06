"""Las fixtures de la base viven en `tests/conftest.py`; aquí se arma el taller sobre ella."""
from __future__ import annotations

import pytest
from sqlalchemy import Engine

from tests.integration.apoyo_base import TallerEnBase
from tests.unit.application.escenarios import Taller


@pytest.fixture
def taller_en_base(motor: Engine) -> TallerEnBase:
    return TallerEnBase(motor)


@pytest.fixture(params=["memoria", "base_de_datos"])
def taller(request: pytest.FixtureRequest) -> Taller:
    """Las pruebas de contrato reciben esta fixture y corren una vez con cada implementación."""
    if request.param == "memoria":
        return Taller()
    return TallerEnBase(request.getfixturevalue("motor"))
