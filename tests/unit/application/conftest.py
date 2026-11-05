"""Cada prueba de aplicación recibe un taller nuevo, sin datos compartidos."""
from __future__ import annotations

import pytest

from tests.unit.application.escenarios import Taller


@pytest.fixture
def taller() -> Taller:
    return Taller()
