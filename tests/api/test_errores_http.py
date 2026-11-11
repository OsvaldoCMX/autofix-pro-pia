"""El formato único de errores y la traducción de cada error a su código (ADR-008)."""
from __future__ import annotations

import re
from collections.abc import Iterator
from enum import Enum
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException

from api.errores import (
    CODIGOS_DE_ERROR,
    TokenInvalido,
    codigo_de,
    nombre_del_campo,
    registrar_manejadores,
)
from api.esquemas.comunes import ENTERO_MAXIMO, EnteroNoNegativo, ModeloDeEntrada, TextoDeNombre
from domain.compartido.errores import ErrorDeDominio, ValorInvalido
from tests.api.pasos import ASESOR, CAJA, COMPRAS, TECNICO

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


class _Tipo(Enum):
    PARTICULAR = "Particular"
    FLOTILLA = "Flotilla"
    OTRO = "Otro"


class _Entrada(ModeloDeEntrada):
    nombre: TextoDeNombre
    libre: str = ""
    kilometraje: EnteroNoNegativo = 0
    monto: str = ""
    tipo: _Tipo | None = None


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

    @app.get("/teapot")
    def teapot() -> None:
        raise HTTPException(418, "I'm a teapot")

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
    assert respuesta.json()["detalle"] == (
        "No se recibió la información solicitada. Capture los datos e intente de nuevo."
    )


@pytest.mark.parametrize("cuerpo", [[1], 5])
def test_un_cuerpo_con_formato_incorrecto_no_dice_que_falta(
    cliente_de_prueba: TestClient, cuerpo: object
) -> None:
    respuesta = cliente_de_prueba.post("/eco", json=cuerpo)

    assert respuesta.status_code == 422
    assert "formato correcto" in respuesta.json()["detalle"]


@pytest.mark.parametrize(
    ("cuerpo", "fragmento"),
    [
        ({"nombre": "a", "kilometraje": 1.5}, "«kilometraje» debe ser un número entero"),
        ({"nombre": "a", "kilometraje": -1}, "«kilometraje» no puede ser menor que 0"),
        ({"nombre": "a", "kilometraje": ENTERO_MAXIMO + 1}, "demasiado grande"),
        ({"nombre": "a", "monto": 100}, "importe con dos decimales"),
    ],
)
def test_un_numero_invalido_explica_que_corregir(
    cliente_de_prueba: TestClient, cuerpo: dict[str, object], fragmento: str
) -> None:
    respuesta = cliente_de_prueba.post("/eco", json=cuerpo)

    assert respuesta.status_code == 422
    assert fragmento in respuesta.json()["detalle"]
    assert str(ENTERO_MAXIMO) not in respuesta.json()["detalle"]


def test_las_opciones_se_escriben_en_espanol(cliente_de_prueba: TestClient) -> None:
    respuesta = cliente_de_prueba.post("/eco", json={"nombre": "a", "tipo": "X"})

    assert respuesta.status_code == 422
    assert respuesta.json()["detalle"] == (
        "El dato «tipo de cliente» debe ser una de estas opciones: "
        "«Particular», «Flotilla» o «Otro»."
    )


@pytest.mark.parametrize(
    ("ubicacion", "nombre"),
    [
        (("motivo_de_ingreso",), "motivo de ingreso"),
        (("responsable_nombre",), "nombre del Responsable de Flotilla"),
        (("vehiculo",), "vehículo"),
        (("vehiculo", "anio"), "año del vehículo"),
        (("cliente", "telefono"), "teléfono del cliente"),
        (("trabajos",), "trabajos"),
        (("trabajos", 0), "trabajo 1"),
        (("trabajos", 0, "mano_de_obra"), "mano de obra del trabajo 1"),
        (("trabajos", 0, "refacciones", 1, "cantidad"), "cantidad de la refacción 2 del trabajo 1"),
        (("ids_trabajos", 2), "trabajos a asignar"),
        (("otro", "dato_raro"), "dato_raro de otro"),
    ],
)
def test_el_campo_se_nombra_sin_indices_ni_nombres_internos(
    ubicacion: tuple[str | int, ...], nombre: str
) -> None:
    assert nombre_del_campo(ubicacion) == nombre


def _modelos_de_entrada(base: type[ModeloDeEntrada] = ModeloDeEntrada) -> Iterator[type]:
    for modelo in base.__subclasses__():
        yield modelo
        yield from _modelos_de_entrada(modelo)


def test_ningun_campo_de_entrada_muestra_su_nombre_interno() -> None:
    campos = {
        campo
        for modelo in _modelos_de_entrada()
        if modelo.__module__.startswith("api.esquemas")
        for campo in modelo.model_fields
    }

    assert "motivo_de_ingreso" in campos  # los esquemas de la aplicación sí se revisaron
    assert [campo for campo in campos if "_" in nombre_del_campo((campo,))] == []


def test_un_nombre_de_dato_con_digitos_raros_no_rompe_la_respuesta(
    cliente_de_prueba: TestClient,
) -> None:
    respuesta = cliente_de_prueba.post("/eco", json={"nombre": "a", "²": 1})

    assert respuesta.status_code == 422
    assert "«²» no se reconoce" in respuesta.json()["detalle"]


def test_otro_error_http_no_deja_pasar_el_texto_en_ingles(cliente_de_prueba: TestClient) -> None:
    respuesta = cliente_de_prueba.get("/teapot")

    assert respuesta.status_code == 418
    assert respuesta.json() == {
        "error": "ErrorHttp",
        "detalle": "No se pudo completar la solicitud. Intente de nuevo.",
        "codigo": 418,
    }


def test_el_mensaje_de_acceso_no_usa_jerga() -> None:
    assert "token" not in TokenInvalido.mensaje.lower()


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


# ------------------------------------------------------------------ mensajes revisados (H-PIA-28)
def test_importe_negativo_dice_que_no_puede_ser_negativo(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/ordenes/OS-1/cotizaciones",
        json={"trabajos": [{"numero": 1, "descripcion": "Frenos", "mano_de_obra": "-1500.00"}]},
        headers=ASESOR,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["detalle"] == (
        "La mano de obra del trabajo 1 no puede ser negativa. "
        "Escriba la cantidad en pesos, por ejemplo 1500.00."
    )


def test_precio_de_refaccion_negativo_dice_que_no_puede_ser_negativo(
    cliente: TestClient,
) -> None:
    refaccion = {"descripcion": "Balata", "cantidad": 1, "precio_unitario": "-10.00"}
    trabajo = {"numero": 1, "descripcion": "Frenos", "mano_de_obra": "100.00"}
    respuesta = cliente.post(
        "/api/ordenes/OS-1/cotizaciones",
        json={"trabajos": [{**trabajo, "refacciones": [refaccion]}]},
        headers=ASESOR,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["detalle"] == (
        "El precio unitario de la refacción 1 del trabajo 1 no puede ser negativo. "
        "Escriba la cantidad en pesos, por ejemplo 1500.00."
    )


def test_monto_negativo_dice_que_no_puede_ser_negativo(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/ordenes/OS-1/pago", json={"monto": "-3000.00", "forma": "Tarjeta"}, headers=CAJA
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["detalle"] == (
        "El monto no puede ser negativo. Escriba la cantidad en pesos, por ejemplo 1500.00."
    )


@pytest.mark.parametrize(
    ("ruta", "encabezados", "nombre"),
    [
        ("/api/ordenes/OS-1/trabajos/abc/inicio", TECNICO, "número de trabajo"),
        ("/api/ordenes/OS-1/solicitudes-de-compra/abc/llegada", COMPRAS, "número de solicitud"),
    ],
)
def test_el_numero_de_la_direccion_se_llama_segun_la_ruta(
    cliente: TestClient, ruta: str, encabezados: dict[str, str], nombre: str
) -> None:
    respuesta = cliente.post(ruta, headers=encabezados)

    assert respuesta.status_code == 422
    assert respuesta.json()["detalle"] == f"El dato «{nombre}» debe ser un número entero."


def test_la_funcion_de_otro_puesto_lo_dice_sin_palabras_tecnicas(
    cliente: TestClient,
) -> None:
    respuesta = cliente.get("/api/gerencia/ordenes", headers=TECNICO)

    assert respuesta.status_code == 403
    assert respuesta.json()["detalle"] == (
        "Esta función es de otro puesto del taller. Pida a la persona encargada que la realice."
    )
