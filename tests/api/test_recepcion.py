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
    expediente_de,
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
    actualizado = {**datos["cliente"], "telefono": "81-9999-0000"}

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
    assert vehiculo["cliente"]["telefono"] == "81-9999-0000"


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
    assert encontrados[0]["responsable_telefono"] == "81-1111-0000"
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


# ------------------------------------------------------------------ correcciones (H-PIA-24)
def test_ca_055_corrige_el_cliente_y_la_decision_usa_el_nombre_nuevo(cliente: TestClient) -> None:
    numero, id_cotizacion = cotizada(cliente)
    id_cliente = expediente_de(cliente, numero)["id_cliente"]
    contacto = {"nombre": "Luis Peña Ruiz", "telefono": "81 1234 5678", "correo": "l@correo.test"}

    corregido = exigir(cliente.put(f"/api/clientes/{id_cliente}", json=contacto, headers=ASESOR), 200)
    autorizacion = {**decision([1, 2]), "nombre_del_autorizante": "Luis Peña Ruiz"}

    assert corregido == {"id_cliente": id_cliente, "tipo": "Particular", **contacto}
    exigir(
        cliente.post(
            f"/api/cotizaciones/{id_cotizacion}/decision", json=autorizacion, headers=ASESOR
        ),
        200,
    )


def test_ca_055_cliente_inexistente_responde_404(cliente: TestClient) -> None:
    respuesta = cliente.put("/api/clientes/CLI-9999", json={"nombre": "Nadie"}, headers=ASESOR)

    assert respuesta.status_code == 404


def test_ca_056_corrige_el_vehiculo_por_sus_placas(cliente: TestClient) -> None:
    datos = datos_de_orden()
    exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 201)
    correccion = {"vin": "5YJSA1E26HF000001", "marca": "Nissan", "modelo": "Sentra", "anio": 2021}

    respuesta = exigir(
        cliente.put(f"/api/vehiculos/{datos['placas']}", json=correccion, headers=ASESOR), 200
    )

    assert respuesta == {"placas": datos["placas"], **correccion}


def test_ca_056_vin_de_otro_vehiculo_responde_422(cliente: TestClient) -> None:
    primero, segundo = datos_de_orden(), datos_de_orden()
    for datos in (primero, segundo):
        exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 201)

    respuesta = exigir(
        cliente.put(
            f"/api/vehiculos/{segundo['placas']}", json=primero["vehiculo"], headers=ASESOR
        ),
        422,
    )

    assert "Ya existe un vehículo con el VIN" in respuesta["detalle"]


def test_ca_057_corrige_la_recepcion_de_una_orden_recibida(cliente: TestClient) -> None:
    numero = recibida(cliente)
    datos = {"kilometraje": 46000, "nivel_de_combustible": "Lleno", "motivo_de_ingreso": "Frenos"}

    respuesta = exigir(
        cliente.put(f"/api/ordenes/{numero}/recepcion", json=datos, headers=ASESOR), 200
    )

    assert respuesta == {"numero_orden": numero, "estado": "Recibida", **datos}
    expediente = expediente_de(cliente, numero)
    assert (expediente["kilometraje"], expediente["motivo_de_ingreso"]) == (46000, "Frenos")


def test_ca_057_despues_de_cotizar_responde_409(cliente: TestClient) -> None:
    numero, _ = cotizada(cliente)
    datos = {"kilometraje": 1, "nivel_de_combustible": "Lleno", "motivo_de_ingreso": "Frenos"}

    respuesta = exigir(
        cliente.put(f"/api/ordenes/{numero}/recepcion", json=datos, headers=ASESOR), 409
    )

    assert respuesta["error"] == "CorreccionNoPermitida"


# ------------------------------------------------------------------ datos de captura (H-PIA-25)
def test_ca_059_telefono_sin_10_digitos_responde_422(cliente: TestClient) -> None:
    datos = datos_de_orden(cliente={**CLIENTE_PARTICULAR, "telefono": "abc"})

    respuesta = exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 422)

    assert respuesta["detalle"] == "El teléfono debe tener 10 dígitos, por ejemplo 81 1234 5678."


def test_ca_059_correo_sin_forma_valida_responde_422(cliente: TestClient) -> None:
    datos = datos_de_orden(cliente={**CLIENTE_PARTICULAR, "correo": "hola"})

    respuesta = exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 422)

    assert "nombre@dominio.com" in respuesta["detalle"]


def test_ca_059_telefono_del_responsable_de_flotilla(cliente: TestClient) -> None:
    cuerpo = {**CLIENTE_DE_FLOTILLA, "empresa": "Otra Empresa", "responsable_telefono": "81-1"}

    respuesta = exigir(cliente.post("/api/clientes", json=cuerpo, headers=ASESOR), 422)

    assert respuesta["detalle"].startswith("El teléfono del Responsable de Flotilla")


def test_ca_059_anio_mayor_al_siguiente_responde_422(cliente: TestClient) -> None:
    datos = datos_de_orden()
    datos["vehiculo"] = {**datos["vehiculo"], "anio": 2099}

    respuesta = exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 422)

    assert respuesta["detalle"] == (
        "El año del vehículo no puede ser mayor a 2027. Revise el dato capturado."
    )


def test_ca_059_kilometraje_mayor_a_2_millones_responde_422(cliente: TestClient) -> None:
    datos = datos_de_orden(kilometraje=2_000_000_000)

    respuesta = exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 422)

    assert "2,000,000 km" in respuesta["detalle"]


def test_ca_059_texto_de_mas_de_1000_caracteres_responde_422(cliente: TestClient) -> None:
    datos = datos_de_orden(motivo_de_ingreso="x" * 1001)

    respuesta = exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 422)

    assert respuesta["detalle"] == (
        "El dato «motivo de ingreso» no puede tener más de 1000 caracteres."
    )


# ------------------------------------------------------------------ flotilla (H-PIA-27)
def test_ca_064_flotilla_con_rol_de_cliente_dice_el_responsable(cliente: TestClient) -> None:
    _, id_cotizacion = cotizada(cliente, flotilla=True)
    cuerpo = {**decision([1, 2], flotilla=True), "rol_del_autorizante": "Cliente"}

    respuesta = exigir(
        cliente.post(f"/api/cotizaciones/{id_cotizacion}/decision", json=cuerpo, headers=ASESOR),
        409,
    )

    assert respuesta["detalle"] == (
        "Para la flotilla de Transportes Norte, registre la decisión a nombre de su Responsable "
        "de Flotilla, Ana Torres, con el rol «Responsable de Flotilla»."
    )
