"""Compara la API real con el contrato de `docs/api/README.md`: sus rutas y sus roles.

Las rutas con la marca «Planeado» en la columna Prioridad están aprobadas (Fase 13) pero todavía
no existen: se comprueba que sigan sin existir, y la Fase 14 quita la marca al construir cada una.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from api.dependencias import crear_contenedor
from api.exportar_openapi import exportar
from api.main import crear_app
from infrastructure.config import Configuracion
from tests.api.pasos import ASESOR, CAJA, COMPRAS, GERENTE, SISTEMA, TECNICO, TOKENS

CONTRATO = Path(__file__).resolve().parents[2] / "docs/api/README.md"
OPENAPI = CONTRATO.parent / "openapi.json"
TOTAL_DE_RUTAS = 49
MARCA_DE_PLANEADO = "Planeado"
TOKENS_POR_ROL = {
    "Asesor": ASESOR,
    "Técnico": TECNICO,
    "Gerente": GERENTE,
    "Compras": COMPRAS,
    "Caja": CAJA,
    "Sistema": SISTEMA,
}
EMPLEADOS = ("Asesor", "Técnico", "Gerente", "Compras", "Caja")
PARAMETROS = {"{numero}": "OS-9999", "{id}": "1", "{placas}": "ABC123"}
FOTO = {"archivo": ("dano.jpg", b"\xff\xd8\xff", "image/jpeg")}


@dataclass(frozen=True)
class Ruta:
    metodo: str
    ruta: str
    roles: tuple[str, ...]
    exito: int
    errores: tuple[int, ...]
    prioridad: str

    @property
    def es_publica(self) -> bool:
        return not self.roles

    @property
    def url(self) -> str:
        url = self.ruta
        for parametro, valor in PARAMETROS.items():
            url = url.replace(parametro, valor)
        return url

    @property
    def es_planeada(self) -> bool:
        return MARCA_DE_PLANEADO in self.prioridad

    def __str__(self) -> str:
        return f"{self.metodo} {self.ruta}"


def _roles(texto: str) -> tuple[str, ...]:
    if texto == "Público":
        return ()
    if texto == "Cualquier empleado":
        return EMPLEADOS
    return tuple(rol.strip() for rol in texto.split(","))


def _leer_contrato() -> list[Ruta]:
    rutas = []
    for linea in CONTRATO.read_text(encoding="utf-8").splitlines():
        columnas = [columna.strip() for columna in linea.strip("|").split("|")]
        if len(columnas) != 9 or columnas[0] not in ("GET", "POST", "PUT"):
            continue
        metodo, ruta, rol, _, exito, errores, _, _, prioridad = columnas
        codigos = tuple(int(codigo) for codigo in errores.split(",") if codigo.strip().isdigit())
        rutas.append(
            Ruta(metodo, ruta.strip("`").split("?")[0], _roles(rol), int(exito), codigos, prioridad)
        )
    return rutas


CONTRATO_COMPLETO = _leer_contrato()
PLANEADAS = [ruta for ruta in CONTRATO_COMPLETO if ruta.es_planeada]
RUTAS = [ruta for ruta in CONTRATO_COMPLETO if not ruta.es_planeada]
PROTEGIDAS = [ruta for ruta in RUTAS if not ruta.es_publica]
ACCESOS_PROHIBIDOS = [
    (ruta, rol) for ruta in PROTEGIDAS for rol in TOKENS_POR_ROL if rol not in ruta.roles
]
ACCESOS_PERMITIDOS = [(ruta, rol) for ruta in PROTEGIDAS for rol in ruta.roles]


def _pedir(cliente: TestClient, ruta: Ruta, encabezados: dict[str, str] | None = None) -> Any:
    return cliente.request(ruta.metodo, ruta.url, headers=encabezados)


@pytest.fixture(scope="module")
def cliente() -> TestClient:
    """Aquí solo importan las rutas y la seguridad: se comparte una aplicación en memoria."""
    contenedor = crear_contenedor(Configuracion(app_env="pruebas", tokens=TOKENS))
    return TestClient(crear_app(contenedor))


@pytest.fixture(scope="module")
def documento(cliente: TestClient) -> dict[str, Any]:
    return cliente.get("/openapi.json").json()


def _operacion(documento: dict[str, Any], ruta: Ruta) -> dict[str, Any]:
    return documento["paths"][ruta.ruta][ruta.metodo.lower()]


def test_openapi_exportado_esta_al_dia(documento: dict[str, Any]) -> None:
    exportado = json.loads(OPENAPI.read_text(encoding="utf-8"))

    assert exportado == documento, "Ejecute: python -m api.exportar_openapi"


def test_exportar_escribe_un_json_valido(tmp_path: Path) -> None:
    destino = tmp_path / "openapi.json"

    exportar(destino)

    assert len(json.loads(destino.read_text(encoding="utf-8"))["paths"]) > 0


def test_el_contrato_tiene_todas_sus_rutas() -> None:
    assert len(CONTRATO_COMPLETO) == TOTAL_DE_RUTAS


def _expuestas(documento: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (metodo.upper(), ruta)
        for ruta, operaciones in documento["paths"].items()
        for metodo in operaciones
    }


def test_la_api_expone_exactamente_las_rutas_del_contrato(documento: dict[str, Any]) -> None:
    assert _expuestas(documento) == {(ruta.metodo, ruta.ruta) for ruta in RUTAS}


def test_las_rutas_planeadas_todavia_no_existen(documento: dict[str, Any]) -> None:
    construidas = {(r.metodo, r.ruta) for r in PLANEADAS} & _expuestas(documento)

    assert construidas == set(), "Quite la marca «Planeado» en scripts/docs/rutas.py"


@pytest.mark.parametrize("ruta", RUTAS, ids=str)
def test_cada_ruta_declara_su_exito_y_sus_errores(documento: dict[str, Any], ruta: Ruta) -> None:
    respuestas = _operacion(documento, ruta)["responses"]

    assert str(ruta.exito) in respuestas
    assert {str(codigo) for codigo in ruta.errores} <= set(respuestas)


@pytest.mark.parametrize("ruta", RUTAS, ids=str)
def test_cada_error_declarado_usa_el_formato_unico(documento: dict[str, Any], ruta: Ruta) -> None:
    respuestas = _operacion(documento, ruta)["responses"]

    for codigo, respuesta in respuestas.items():
        if int(codigo) >= 400:
            esquema = respuesta["content"]["application/json"]["schema"]
            assert esquema["$ref"].endswith("/RespuestaDeError"), f"{ruta} declara {codigo}"


@pytest.mark.parametrize("ruta", PROTEGIDAS, ids=str)
def test_rn_01_cada_ruta_protegida_sin_token_responde_401(
    cliente: TestClient, ruta: Ruta
) -> None:
    respuesta = _pedir(cliente, ruta)

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == 401


@pytest.mark.parametrize(("ruta", "rol"), ACCESOS_PROHIBIDOS, ids=lambda valor: str(valor))
def test_rn_01_cada_rol_no_permitido_responde_403(
    cliente: TestClient, ruta: Ruta, rol: str
) -> None:
    respuesta = _pedir(cliente, ruta, TOKENS_POR_ROL[rol])

    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "RolNoPermitido"


@pytest.mark.parametrize(("ruta", "rol"), ACCESOS_PERMITIDOS, ids=lambda valor: str(valor))
def test_rn_01_cada_rol_permitido_pasa_la_seguridad(
    cliente: TestClient, ruta: Ruta, rol: str
) -> None:
    respuesta = _pedir(cliente, ruta, TOKENS_POR_ROL[rol])

    assert respuesta.status_code not in (401, 403), respuesta.text


@pytest.mark.parametrize("ruta", [r for r in RUTAS if r.es_publica], ids=str)
def test_las_rutas_publicas_no_piden_token(
    cliente: TestClient, documento: dict[str, Any], ruta: Ruta
) -> None:
    assert _pedir(cliente, ruta).status_code not in (401, 403)
    assert "security" not in _operacion(documento, ruta)


def test_docs_y_openapi_son_publicos(cliente: TestClient) -> None:
    assert cliente.get("/docs").status_code == 200
    assert cliente.get("/openapi.json").status_code == 200


@pytest.mark.parametrize("ruta", [r for r in RUTAS if r.prioridad == "P2"], ids=str)
def test_las_rutas_p2_responden_501(cliente: TestClient, ruta: Ruta) -> None:
    archivos = FOTO if ruta.metodo == "POST" else None

    respuesta = cliente.request(
        ruta.metodo, ruta.url, headers=TOKENS_POR_ROL[ruta.roles[0]], files=archivos
    )

    assert respuesta.status_code == 501
    assert respuesta.json()["error"] == "FuncionNoImplementada"


def test_las_rutas_p2_siguen_exigiendo_el_rol(cliente: TestClient) -> None:
    assert cliente.get("/api/ordenes/OS-9999/recibo/pdf", headers=ASESOR).status_code == 403


def test_swagger_tiene_el_boton_authorize(documento: dict[str, Any]) -> None:
    esquemas = documento["components"]["securitySchemes"]

    assert esquemas["TokenDeEmpleado"]["type"] == "http"
    assert esquemas["TokenDeEmpleado"]["scheme"] == "bearer"


@pytest.mark.parametrize("ruta", PROTEGIDAS, ids=str)
def test_las_rutas_protegidas_piden_el_token_en_swagger(
    documento: dict[str, Any], ruta: Ruta
) -> None:
    assert _operacion(documento, ruta)["security"] == [{"TokenDeEmpleado": []}]
