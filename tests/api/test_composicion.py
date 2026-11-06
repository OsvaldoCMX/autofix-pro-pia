"""Composition Root, tokens y arranque de la aplicación (ADR-012, decisiones-tecnicas.md §3 y §6)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from api.dependencias import (
    EMPLEADOS_POR_VARIABLE,
    VARIABLE_DE_SISTEMA,
    ConfiguracionIncompleta,
    crear_contenedor,
)
from api.errores import registrar_manejadores
from api.main import crear_app
from api.seguridad import requiere_rol, requiere_sistema
from domain.empleados.empleado import RolDeEmpleado
from infrastructure.base_de_datos.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from infrastructure.config import VARIABLES_DE_TOKEN, Configuracion
from infrastructure.memoria.unidad_de_trabajo import UnidadDeTrabajoEnMemoria
from tests.api.pasos import ASESOR, CAJA, SISTEMA, TOKENS

RAIZ = Path(__file__).resolve().parents[2]
URL_LOCAL = "postgresql+psycopg://autofix:ejemplo@localhost:5432/autofix"


@pytest.fixture
def cliente_con_roles() -> TestClient:
    contenedor = crear_contenedor(Configuracion(app_env="pruebas", tokens=TOKENS))
    app = FastAPI()
    app.state.contenedor = contenedor
    registrar_manejadores(app)

    @app.get("/solo-asesor", dependencies=[Depends(requiere_rol(RolDeEmpleado.ASESOR))])
    def solo_asesor() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/solo-sistema", dependencies=[Depends(requiere_sistema)])
    def solo_sistema() -> dict[str, bool]:
        return {"ok": True}

    return TestClient(app)


# ------------------------------------------------------------------ arranque
def test_sin_base_en_desarrollo_usa_memoria_con_los_empleados() -> None:
    contenedor = crear_contenedor(Configuracion(app_env="desarrollo"))

    uow = contenedor.fabrica_de_uow()

    assert isinstance(uow, UnidadDeTrabajoEnMemoria)
    with uow:
        assert uow.empleados.obtener("EMP-001").nombre == "Laura Méndez"


def test_sin_base_en_produccion_no_arranca() -> None:
    with pytest.raises(ConfiguracionIncompleta, match="DATABASE_URL"):
        crear_contenedor(Configuracion(app_env="produccion"))


def test_con_url_usa_la_base_de_datos_sin_conectarse_al_armarse() -> None:
    contenedor = crear_contenedor(Configuracion(app_env="produccion", database_url=URL_LOCAL))

    assert isinstance(contenedor.fabrica_de_uow(), UnidadDeTrabajoSqlAlchemy)


def test_cada_servicio_recibe_su_propia_unidad_de_trabajo() -> None:
    contenedor = crear_contenedor(Configuracion())

    assert contenedor.fabrica_de_uow() is not contenedor.fabrica_de_uow()


def test_la_zona_horaria_de_la_configuracion_llega_al_reloj() -> None:
    contenedor = crear_contenedor(Configuracion(zona_horaria="America/Mexico_City"))

    assert str(contenedor.reloj.ahora_en_el_taller().tzinfo) == "America/Mexico_City"


def test_crear_app_sin_contenedor_lee_el_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("APP_ENV", "pruebas")

    respuesta = TestClient(crear_app()).get("/health")

    assert respuesta.status_code == 200


def test_salud_es_publica(cliente: TestClient) -> None:
    respuesta = cliente.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


# ------------------------------------------------------------------ empleados y tokens
def test_los_empleados_coinciden_con_los_datos_iniciales() -> None:
    sql = (RAIZ / "database/02_datos_iniciales.sql").read_text(encoding="utf-8")
    filas = re.findall(r"\('(EMP-\d{3})', '([^']+)', '([^']+)'\)", sql)

    esperados = {
        (empleado.id_empleado, empleado.nombre, empleado.rol.value)
        for empleado in EMPLEADOS_POR_VARIABLE.values()
    }
    assert set(filas) == esperados


def test_los_tokens_coinciden_con_las_decisiones_tecnicas() -> None:
    documento = (RAIZ / "docs/architecture/decisiones-tecnicas.md").read_text(encoding="utf-8")
    filas = re.findall(r"^\| (EMP-\d{3}) \| .+ \| .+ \| `(TOKEN_\w+)` \|$", documento, re.MULTILINE)

    assert {variable: id_empleado for id_empleado, variable in filas} == {
        variable: empleado.id_empleado for variable, empleado in EMPLEADOS_POR_VARIABLE.items()
    }


def test_cada_variable_de_token_tiene_quien_la_use() -> None:
    assert set(VARIABLES_DE_TOKEN) == {*EMPLEADOS_POR_VARIABLE, VARIABLE_DE_SISTEMA}


# ------------------------------------------------------------------ seguridad
def test_rol_correcto_pasa(cliente_con_roles: TestClient) -> None:
    assert cliente_con_roles.get("/solo-asesor", headers=ASESOR).status_code == 200


def test_sin_token_responde_401_con_su_encabezado(cliente_con_roles: TestClient) -> None:
    respuesta = cliente_con_roles.get("/solo-asesor")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"] == "TokenInvalido"
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"


def test_token_equivocado_responde_401(cliente_con_roles: TestClient) -> None:
    respuesta = cliente_con_roles.get(
        "/solo-asesor", headers={"Authorization": "Bearer otro-token"}
    )

    assert respuesta.status_code == 401


def test_token_no_ascii_responde_401_y_no_500(cliente_con_roles: TestClient) -> None:
    respuesta = cliente_con_roles.get(
        "/solo-asesor", headers={"Authorization": "Bearer señal".encode("latin-1")}
    )

    assert respuesta.status_code == 401


def test_otro_esquema_de_autorizacion_responde_401(cliente_con_roles: TestClient) -> None:
    respuesta = cliente_con_roles.get("/solo-asesor", headers={"Authorization": "Basic abc"})

    assert respuesta.status_code == 401


def test_rol_equivocado_responde_403(cliente_con_roles: TestClient) -> None:
    respuesta = cliente_con_roles.get("/solo-asesor", headers=CAJA)

    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "RolNoPermitido"


def test_el_token_de_sistema_no_es_de_un_empleado(cliente_con_roles: TestClient) -> None:
    assert cliente_con_roles.get("/solo-asesor", headers=SISTEMA).status_code == 403


def test_el_sistema_pasa_a_su_ruta(cliente_con_roles: TestClient) -> None:
    assert cliente_con_roles.get("/solo-sistema", headers=SISTEMA).status_code == 200


def test_un_empleado_no_entra_a_la_ruta_del_sistema(cliente_con_roles: TestClient) -> None:
    assert cliente_con_roles.get("/solo-sistema", headers=ASESOR).status_code == 403


@pytest.mark.parametrize("encabezados", [{}, {"Authorization": "Bearer otro-token"}])
def test_la_ruta_del_sistema_rechaza_tokens_invalidos(
    cliente_con_roles: TestClient, encabezados: dict[str, str]
) -> None:
    assert cliente_con_roles.get("/solo-sistema", headers=encabezados).status_code == 401


def test_sin_tokens_configurados_nadie_entra() -> None:
    contenedor = crear_contenedor(Configuracion(app_env="pruebas"))

    assert contenedor.directorio_de_tokens.empleado_del_token("") is None
    assert not contenedor.directorio_de_tokens.es_del_sistema("")
