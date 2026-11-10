"""Recepción de punta a punta: criterios CA-001 a CA-004, CA-028 y CA-029."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from domain.servicios.verificador_de_orden_unica import VerificadorDeOrdenUnica
from tests.api.pasos import (
    ASESOR,
    CAJA,
    CLIENTE_DE_FLOTILLA,
    CLIENTE_PARTICULAR,
    GERENTE,
    ID_ASESOR,
    TECNICO,
    cotizada,
    datos_de_orden,
    decision,
    exigir,
    recibida,
)

JPEG = {"archivo": ("dano.jpg", b"\xff\xd8\xff", "image/jpeg")}


def test_ca_001_registra_vehiculo_nuevo_y_abre_orden_recibida(cliente: TestClient) -> None:
    primera = cliente.post("/api/ordenes", json=datos_de_orden(), headers=ASESOR)
    segunda = cliente.post("/api/ordenes", json=datos_de_orden(), headers=ASESOR)

    assert primera.status_code == 201
    cuerpo = primera.json()
    assert cuerpo["estado"] == "Recibida"
    assert cuerpo["mensaje"] == f"Orden {cuerpo['numero_orden']} registrada correctamente."
    assert cuerpo["fecha_ingreso"].endswith("Z")
    assert segunda.json()["numero_orden"] != cuerpo["numero_orden"]


def test_ca_001_la_orden_queda_a_nombre_del_asesor_del_token(cliente: TestClient) -> None:
    numero = recibida(cliente)

    expediente = exigir(cliente.get(f"/api/ordenes/{numero}", headers=ASESOR), 200)

    assert expediente["asesor"] == ID_ASESOR


def test_ca_001_el_cuerpo_no_puede_elegir_otro_asesor(cliente: TestClient) -> None:
    cuerpo = datos_de_orden(asesor="EMP-003")

    respuesta = cliente.post("/api/ordenes", json=cuerpo, headers=ASESOR)

    assert respuesta.status_code == 422


def test_ca_002_guarda_kilometraje_y_combustible_en_el_expediente(cliente: TestClient) -> None:
    numero = recibida(cliente)

    expediente = exigir(cliente.get(f"/api/ordenes/{numero}", headers=ASESOR), 200)

    assert expediente["kilometraje"] == 45000
    assert expediente["nivel_de_combustible"] == "1/2"


def test_ca_002_foto_de_danos_responde_501_hasta_la_fase_10(cliente: TestClient) -> None:
    numero = recibida(cliente)

    respuesta = cliente.post(f"/api/ordenes/{numero}/fotos", files=JPEG, headers=ASESOR)

    assert respuesta.status_code == 501
    assert respuesta.json()["codigo"] == 501


def test_ca_003_encuentra_cliente_recurrente_por_placas(cliente: TestClient) -> None:
    datos = datos_de_orden()
    exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 201)

    vehiculo = exigir(cliente.get(f"/api/vehiculos/{datos['placas']}", headers=ASESOR), 200)

    assert vehiculo["vin"] == datos["vehiculo"]["vin"]
    assert vehiculo["marca"] == "Nissan"
    assert vehiculo["cliente"]["nombre"] == CLIENTE_PARTICULAR["nombre"]
    assert vehiculo["cliente"]["correo"] == CLIENTE_PARTICULAR["correo"]


def test_ca_003_orden_con_placas_existentes_reutiliza_y_actualiza(cliente: TestClient) -> None:
    datos = datos_de_orden()
    primera = exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 201)
    # Cliente recurrente: su visita anterior ya terminó (RN-27).
    cancelacion = {"motivo": "Visita anterior"}
    exigir(
        cliente.post(
            f"/api/ordenes/{primera['numero_orden']}/cancelacion", json=cancelacion, headers=ASESOR
        ),
        200,
    )
    actualizado = {**datos["cliente"], "telefono": "81-9999"}

    segunda = exigir(
        cliente.post(
            "/api/ordenes",
            json={**datos, "cliente": actualizado, "vehiculo": None},
            headers=ASESOR,
        ),
        201,
    )

    assert segunda["id_cliente"] == primera["id_cliente"]
    assert segunda["numero_orden"] != primera["numero_orden"]
    vehiculo = exigir(cliente.get(f"/api/vehiculos/{datos['placas']}", headers=ASESOR), 200)
    assert vehiculo["cliente"]["telefono"] == "81-9999"


def test_ca_004_placas_no_registradas_responde_404_y_permite_crear_desde_cero(
    cliente: TestClient,
) -> None:
    datos = datos_de_orden()

    busqueda = cliente.get(f"/api/vehiculos/{datos['placas']}", headers=ASESOR)

    assert busqueda.status_code == 404
    assert busqueda.json()["error"] == "VehiculoNoEncontrado"
    assert cliente.post("/api/ordenes", json=datos, headers=ASESOR).status_code == 201


def test_ca_004_placas_nuevas_sin_datos_del_vehiculo_responde_422(cliente: TestClient) -> None:
    cuerpo = datos_de_orden(vehiculo=None)

    respuesta = cliente.post("/api/ordenes", json=cuerpo, headers=ASESOR)

    assert respuesta.status_code == 422
    assert "capture los datos del vehículo" in respuesta.json()["detalle"]


def test_ca_028_registra_flotilla_con_responsable_y_la_encuentra_por_empresa(
    cliente: TestClient,
) -> None:
    registrado = exigir(cliente.post("/api/clientes", json=CLIENTE_DE_FLOTILLA, headers=ASESOR), 201)

    encontrados = exigir(
        cliente.get(
            "/api/clientes",
            params={"tipo": "Flotilla", "empresa": "Transportes Norte"},
            headers=ASESOR,
        ),
        200,
    )

    assert registrado["responsable_nombre"] == "Ana Torres"
    assert [c["id_cliente"] for c in encontrados] == [registrado["id_cliente"]]
    assert encontrados[0]["responsable_telefono"] == "81-1111"
    assert encontrados[0]["responsable_correo"] == "ana@norte.test"


def test_ca_028_empresa_existente_no_se_duplica(cliente: TestClient) -> None:
    primero = exigir(cliente.post("/api/clientes", json=CLIENTE_DE_FLOTILLA, headers=ASESOR), 201)
    segundo = exigir(cliente.post("/api/clientes", json=CLIENTE_DE_FLOTILLA, headers=ASESOR), 201)

    assert segundo["id_cliente"] == primero["id_cliente"]


def test_ca_028_flotilla_sin_responsable_responde_422(cliente: TestClient) -> None:
    cuerpo = {"nombre": "Sin Responsable SA", "tipo": "Flotilla", "empresa": "Sin Responsable"}

    respuesta = cliente.post("/api/clientes", json=cuerpo, headers=ASESOR)

    assert respuesta.status_code == 422
    assert "Responsable de Flotilla" in respuesta.json()["detalle"]


def test_ca_029_flotilla_rechaza_al_conductor_como_autorizante(cliente: TestClient) -> None:
    _, id_cotizacion = cotizada(cliente, flotilla=True)

    conductor = cliente.post(
        f"/api/cotizaciones/{id_cotizacion}/decision",
        json={
            "lineas_autorizadas": [1, 2],
            "nombre_del_autorizante": "Conductor del Camión",
            "rol_del_autorizante": "Cliente",
        },
        headers=ASESOR,
    )
    responsable = cliente.post(
        f"/api/cotizaciones/{id_cotizacion}/decision",
        json=decision([1, 2], flotilla=True),
        headers=ASESOR,
    )

    assert conductor.status_code == 409
    assert conductor.json()["error"] == "AutorizanteNoValido"
    assert responsable.status_code == 200
    detalle = exigir(cliente.get(f"/api/cotizaciones/{id_cotizacion}", headers=ASESOR), 200)
    assert detalle["autorizante"] == "Ana Torres"


def test_buscar_clientes_con_tipo_desconocido_responde_422(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/clientes", params={"tipo": "Otro"}, headers=ASESOR)

    assert respuesta.status_code == 422
    assert "Particular" in respuesta.json()["detalle"]


@pytest.mark.parametrize("encabezados", [TECNICO, GERENTE, CAJA])
def test_rn_01_solo_el_asesor_registra_clientes_vehiculos_y_ordenes(
    cliente: TestClient, encabezados: dict[str, str]
) -> None:
    assert cliente.post(
        "/api/ordenes", json=datos_de_orden(), headers=encabezados
    ).status_code == 403
    assert cliente.post(
        "/api/clientes", json=CLIENTE_PARTICULAR, headers=encabezados
    ).status_code == 403


def test_rn_01_sin_token_no_se_registra_nada(cliente: TestClient) -> None:
    assert cliente.post("/api/ordenes", json=datos_de_orden()).status_code == 401


def test_rn_23_kilometraje_negativo_responde_422(cliente: TestClient) -> None:
    cuerpo = datos_de_orden(kilometraje=-1)

    respuesta = cliente.post("/api/ordenes", json=cuerpo, headers=ASESOR)

    assert respuesta.status_code == 422
    assert "kilometraje" in respuesta.json()["detalle"]


def test_json_mal_formado_con_y_sin_token_responde_400(cliente: TestClient) -> None:
    tipo = {"Content-Type": "application/json"}

    con_token = cliente.post("/api/ordenes", content="{mal", headers={**ASESOR, **tipo})
    sin_token = cliente.post("/api/ordenes", content="{mal", headers=tipo)

    assert con_token.status_code == 400
    assert sin_token.status_code == 400


def test_un_cuerpo_invalido_sin_token_responde_401(cliente: TestClient) -> None:
    assert cliente.post("/api/ordenes", json={}).status_code == 401


def test_cliente_inexistente_responde_404(cliente: TestClient) -> None:
    cuerpo = datos_de_orden(id_cliente="NO-EXISTE", cliente=None)

    respuesta = cliente.post("/api/ordenes", json=cuerpo, headers=ASESOR)

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "ClienteNoEncontrado"


def test_vin_de_otro_vehiculo_responde_422(cliente: TestClient) -> None:
    datos = datos_de_orden()
    exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 201)
    otro = datos_de_orden()
    otro["vehiculo"] = datos["vehiculo"]

    respuesta = cliente.post("/api/ordenes", json=otro, headers=ASESOR)

    assert respuesta.status_code == 422
    assert "VIN" in respuesta.json()["detalle"]


def test_placas_con_caracteres_invalidos_responden_422(cliente: TestClient) -> None:
    assert cliente.get("/api/vehiculos/ABC!123", headers=ASESOR).status_code == 422


def test_expediente_de_orden_inexistente_responde_404(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/ordenes/OS-9999", headers=ASESOR)

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "OrdenNoEncontrada"


def test_el_caracter_nulo_en_la_ruta_responde_422(cliente: TestClient) -> None:
    assert cliente.get("/api/ordenes/OS%000001", headers=ASESOR).status_code == 422


@pytest.mark.parametrize("encabezados", [ASESOR, GERENTE, TECNICO, CAJA])
def test_roles_que_leen_el_expediente(
    cliente: TestClient, encabezados: dict[str, str]
) -> None:
    numero = recibida(cliente)

    assert cliente.get(f"/api/ordenes/{numero}", headers=encabezados).status_code == 200


def test_ca_052_no_abre_segunda_orden_del_mismo_vehiculo(cliente: TestClient) -> None:
    datos = datos_de_orden()
    primera = exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 201)

    segunda = exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 409)

    assert segunda["error"] == "VehiculoConOrdenAbierta"
    assert segunda["detalle"] == (
        f"El vehículo con placas {primera['placas']} ya tiene abierta la orden "
        f"{primera['numero_orden']} (estado «Recibida»). Ábrala en lugar de registrar otra."
    )


def test_rn_27_si_la_base_rechaza_la_segunda_orden_responde_el_mismo_409(
    cliente: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dos clics al mismo tiempo: los dos pasan la revisión y la base rechaza el segundo."""
    datos = datos_de_orden()
    primera = exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 201)
    monkeypatch.setattr(VerificadorDeOrdenUnica, "verificar", lambda *_: None)

    segunda = exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 409)

    assert segunda["error"] == "VehiculoConOrdenAbierta"
    assert primera["numero_orden"] in segunda["detalle"]
    assert "Ábrala en lugar de registrar otra." in segunda["detalle"]
