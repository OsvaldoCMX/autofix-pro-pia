"""El formato único de errores y la traducción de cada error a su código (ADR-008)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.errores import CODIGOS_DE_ERROR, codigo_de, registrar_manejadores
from api.esquemas.comunes import ModeloDeEntrada, TextoDeNombre
from domain.compartido.errores import ErrorDeDominio, ValorInvalido

MODELO_DE_DOMINIO = Path(__file__).resolve().parents[2] / "docs/architecture/modelo-de-dominio.md"
MENSAJE_SECRETO = "postgresql://usuario:clave-secreta@servidor/base"


def _subclases_de_error() -> set[type[ErrorDeDominio]]:
    return {
        tipo for tipo in ErrorDeDominio.__subclasses__() if tipo.__module__ == ErrorDeDominio.__module__
    }


def _codigos_documentados() -> dict[str, int]:
    """Lee la tabla de `modelo-de-dominio.md` §7."""
    seccion = MODELO_DE_DOMINIO.read_text(encoding="utf-8").split("## 7. Errores del dominio")[1]
    codigos: dict[str, int] = {}
    for errores, codigo in re.findall(r"^\| (`.+?) \| .+ \| (\d{3}) \|$", seccion, re.MULTILINE):
        for nombre in re.findall(r"`(\w+)`", errores):
            codigos[nombre] = int(codigo)
    return codigos


class _Entrada(ModeloDeEntrada):
    nombre: TextoDeNombre
    libre: str = ""


@pytest.fixture
def cliente_de_prueba() -> TestClient:
    app = FastAPI()
    registrar_manejadores(app)

    @app.post("/eco")
    def eco(entrada: _Entrada) -> dict[str, str]:
        return {"nombre": entrada.nombre}

    @app.get("/invalido")
    def invalido() -> None:
        raise ValorInvalido("El dato no sirve.")

    @app.get("/fallo")
    def fallo() -> None:
        raise RuntimeError(MENSAJE_SECRETO)

    return TestClient(app, raise_server_exceptions=False)


def test_cada_error_del_dominio_tiene_su_codigo() -> None:
    assert _subclases_de_error() == set(CODIGOS_DE_ERROR)


def test_los_codigos_coinciden_con_el_modelo_de_dominio() -> None:
    assert {tipo.__name__: codigo for tipo, codigo in CODIGOS_DE_ERROR.items()} == (
        _codigos_documentados()
    )


def test_un_error_de_dominio_sin_tabla_es_una_regla_violada() -> None:
    class ErrorNuevo(ErrorDeDominio):
        pass

    assert codigo_de(ErrorNuevo()) == 409


def test_un_error_de_dominio_usa_el_formato_unico(cliente_de_prueba: TestClient) -> None:
    respuesta = cliente_de_prueba.get("/invalido")

    assert respuesta.status_code == 422
    assert respuesta.json() == {
        "error": "ValorInvalido",
        "detalle": "El dato no sirve.",
        "codigo": 422,
    }


def test_json_mal_formado_responde_400(cliente_de_prueba: TestClient) -> None:
    respuesta = cliente_de_prueba.post(
        "/eco", content="{mal", headers={"Content-Type": "application/json"}
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["error"] == "JsonMalFormado"
    assert respuesta.json()["codigo"] == 400


@pytest.mark.parametrize(
    ("cuerpo", "fragmento"),
    [
        ({}, "Falta el dato «nombre»"),
        ({"nombre": "x" * 121}, "más de 120 caracteres"),
        ({"nombre": 5}, "debe ser texto"),
        ({"nombre": "a", "otro": 1}, "«otro» no se reconoce"),
        ({"nombre": "a\x00b"}, "caracteres no válidos"),
    ],
)
def test_un_dato_invalido_responde_422_en_espanol(
    cliente_de_prueba: TestClient, cuerpo: dict[str, object], fragmento: str
) -> None:
    respuesta = cliente_de_prueba.post("/eco", json=cuerpo)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "ValorInvalido"
    assert fragmento in respuesta.json()["detalle"]


def test_sin_cuerpo_responde_422(cliente_de_prueba: TestClient) -> None:
    respuesta = cliente_de_prueba.post("/eco")

    assert respuesta.status_code == 422
    assert respuesta.json()["detalle"] == "Falta el cuerpo de la petición."


def test_un_dato_desconocido_con_sustituto_suelto_no_rompe_la_respuesta(
    cliente_de_prueba: TestClient,
) -> None:
    barra = chr(92)
    cuerpo = '{"nombre": "a", "' + barra + 'ud800": 1}'

    respuesta = cliente_de_prueba.post(
        "/eco", content=cuerpo, headers={"Content-Type": "application/json"}
    )

    assert respuesta.status_code == 422


@pytest.mark.parametrize("campo", ["nombre", "libre"])
def test_un_sustituto_suelto_en_el_texto_responde_422(
    cliente_de_prueba: TestClient, campo: str
) -> None:
    barra = chr(92)
    texto = '"' + barra + 'ud800"'
    cuerpo = f'{{"nombre": "a", "{campo}": {texto}}}' if campo == "libre" else (
        '{"nombre": ' + texto + "}"
    )

    respuesta = cliente_de_prueba.post(
        "/eco", content=cuerpo, headers={"Content-Type": "application/json"}
    )

    assert respuesta.status_code == 422
    assert "caracteres no válidos" in respuesta.json()["detalle"]


def test_ruta_inexistente_usa_el_formato_unico(cliente: TestClient) -> None:
    respuesta = cliente.get("/no-existe")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "RutaNoEncontrada"
    assert respuesta.json()["codigo"] == 404


def test_metodo_no_permitido_usa_el_formato_unico(cliente: TestClient) -> None:
    respuesta = cliente.post("/health")

    assert respuesta.status_code == 405
    assert respuesta.json()["error"] == "MetodoNoPermitido"


def test_un_error_inesperado_no_revela_detalles(cliente_de_prueba: TestClient) -> None:
    respuesta = cliente_de_prueba.get("/fallo")

    assert respuesta.status_code == 500
    assert respuesta.json()["error"] == "ErrorInterno"
    assert "clave-secreta" not in respuesta.text


def test_el_caracter_nulo_en_los_parametros_responde_422(cliente: TestClient) -> None:
    respuesta = cliente.get("/health?dato=a%00b")

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "ValorInvalido"
