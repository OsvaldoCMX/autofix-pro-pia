"""La carga real de `02_datos_iniciales.sql` por la API: lo mismo que se verá en Swagger."""
from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from api.dependencias import crear_contenedor
from api.main import crear_app
from application.puertos import Reloj
from infrastructure.config import Configuracion
from tests.api.pasos import ASESOR, TOKENS, expediente_de
from tests.datos_profesor.adaptador import leer_operaciones
from tests.datos_profesor.conftest import LUNES_DESPUES_DE_LAS_SOLICITUDES
from tests.datos_profesor.flujos import Flujo
from tests.unit.application.escenarios import poner_hora


@pytest.fixture
def cliente_con_datos_iniciales(base_con_datos_iniciales: Engine) -> TestClient:
    reloj = Mock(spec=Reloj)
    poner_hora(reloj, LUNES_DESPUES_DE_LAS_SOLICITUDES)
    configuracion = Configuracion(app_env="pruebas", tokens=TOKENS)
    return TestClient(crear_app(crear_contenedor(configuracion, reloj, base_con_datos_iniciales)))


def test_carga_sql_real_rechaza_servicio_inhabilitado(
    cliente_con_datos_iniciales: TestClient,
) -> None:
    operacion = leer_operaciones()["AUT-O005"]
    flujo = Flujo(cliente_con_datos_iniciales, operacion)

    resultado = flujo.ejecutar(flujo.aprobar)

    assert (resultado.estado_final, resultado.http) == ("En Diagnóstico", 422)
    assert resultado.error == "ValorInvalido"
    assert "AUT-P011" in (resultado.detalle or "")


def test_carga_sql_real_cotiza_el_ejemplo_del_contrato(
    cliente_con_datos_iniciales: TestClient,
) -> None:
    operacion = leer_operaciones()["AUT-O007"]
    flujo = Flujo(cliente_con_datos_iniciales, operacion)

    resultado = flujo.ejecutar(flujo.aprobar)

    assert (resultado.estado_final, resultado.http) == ("Autorizada", 200)
    assert flujo.total == "3065.00"
    assert expediente_de(cliente_con_datos_iniciales, "AUT-O007")["estado"] == "Autorizada"
    assert cliente_con_datos_iniciales.get("/api/ordenes/AUT-O008", headers=ASESOR).status_code == 200
