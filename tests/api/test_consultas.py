"""Consultas de punta a punta: criterios CA-030, CA-031, CA-037 y CA-038."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import Mock
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from tests.api.pasos import (
    ASESOR,
    GERENTE,
    SISTEMA,
    TECNICO,
    datos_de_orden,
    exigir,
    lista,
    pagar,
    por_cobrar,
    presentada,
    recibida,
    revisar_plazos,
)
from tests.unit.application.escenarios import AHORA, poner_hora

ZONA = ZoneInfo("America/Monterrey")
SIN_COINCIDENCIA = {
    "error": "OrdenNoEncontrada",
    "detalle": (
        "No se encontró una orden con esos datos. "
        "Revise el número de orden y las placas e intente de nuevo."
    ),
    "codigo": 404,
}


def _orden_con_placas(cliente: TestClient) -> tuple[str, str]:
    datos = datos_de_orden()
    orden = exigir(cliente.post("/api/ordenes", json=datos, headers=ASESOR), 201)
    return orden["numero_orden"], datos["placas"]


def _ingresos(cliente: TestClient) -> dict[str, str]:
    return exigir(cliente.get("/api/gerencia/ingresos-del-dia", headers=GERENTE), 200)


def test_ca_030_gerente_ve_abiertas_y_cerradas_y_filtra_por_estado(cliente: TestClient) -> None:
    abierta = recibida(cliente)
    cerrada = recibida(cliente)
    exigir(
        cliente.post(
            f"/api/ordenes/{cerrada}/cancelacion", json={"motivo": "Desistió"}, headers=ASESOR
        ),
        200,
    )

    todas = exigir(cliente.get("/api/gerencia/ordenes", headers=GERENTE), 200)
    canceladas = exigir(
        cliente.get("/api/gerencia/ordenes", params={"estado": "Cancelada"}, headers=GERENTE), 200
    )

    por_numero = {orden["numero_orden"]: orden for orden in todas}
    assert por_numero[abierta]["abierta"] is True
    assert por_numero[abierta]["estado"] == "Recibida"
    assert por_numero[cerrada]["abierta"] is False
    assert [orden["numero_orden"] for orden in canceladas] == [cerrada]


def test_ca_030_estado_desconocido_responde_422(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/gerencia/ordenes", params={"estado": "Otro"}, headers=GERENTE)

    assert respuesta.status_code == 422
    assert "Recibida" in respuesta.json()["detalle"]


def test_ca_031_ingresos_del_dia_sin_cargos_a_credito(cliente: TestClient) -> None:
    pagar(cliente, lista(cliente))
    por_cobrar(cliente)

    ingresos = _ingresos(cliente)

    assert ingresos == {"fecha": "2026-10-05", "total": "3000.00"}


def test_ca_037_consulta_publica_sin_token_muestra_solo_estado_y_fechas(
    cliente: TestClient,
) -> None:
    numero, placas = _orden_con_placas(cliente)

    respuesta = cliente.get("/api/consulta-de-estado", params={"orden": numero, "placas": placas})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"numero_orden", "estado", "fecha_ingreso", "ultima_actualizacion"}
    assert cuerpo["numero_orden"] == numero
    assert cuerpo["estado"] == "Recibida"


def test_ca_037_las_placas_se_normalizan(cliente: TestClient) -> None:
    numero, placas = _orden_con_placas(cliente)

    respuesta = cliente.get(
        "/api/consulta-de-estado", params={"orden": numero.lower(), "placas": placas.lower()}
    )

    assert respuesta.status_code == 200


def test_ca_037_la_consulta_publica_no_permite_modificar(cliente: TestClient) -> None:
    assert cliente.post("/api/consulta-de-estado").status_code == 405


def test_ca_038_datos_que_no_coinciden_responden_404_con_el_mensaje_exacto(
    cliente: TestClient,
) -> None:
    numero, _ = _orden_con_placas(cliente)

    respuesta = cliente.get(
        "/api/consulta-de-estado", params={"orden": numero, "placas": "XXX000"}
    )

    assert respuesta.status_code == 404
    assert respuesta.json() == SIN_COINCIDENCIA


def test_ca_038_orden_inexistente_responde_lo_mismo(cliente: TestClient) -> None:
    respuesta = cliente.get(
        "/api/consulta-de-estado", params={"orden": "OS-9999", "placas": "XXX000"}
    )

    assert respuesta.status_code == 404
    assert respuesta.json() == SIN_COINCIDENCIA


def test_rn_20_placas_de_otra_orden_no_revelan_nada(cliente: TestClient) -> None:
    numero, _ = _orden_con_placas(cliente)
    _, placas_ajenas = _orden_con_placas(cliente)

    respuesta = cliente.get(
        "/api/consulta-de-estado", params={"orden": numero, "placas": placas_ajenas}
    )

    assert respuesta.status_code == 404
    assert respuesta.json() == SIN_COINCIDENCIA


def test_rn_20_faltan_datos_responde_422(cliente: TestClient) -> None:
    sin_placas = cliente.get("/api/consulta-de-estado", params={"orden": "OS-0001"})
    en_blanco = cliente.get("/api/consulta-de-estado", params={"orden": " ", "placas": "ABC123"})

    assert sin_placas.status_code == 422
    assert en_blanco.status_code == 422


def test_rn_21_ingresos_usan_el_dia_de_monterrey(cliente: TestClient, reloj: Mock) -> None:
    pago_de_la_noche = datetime(2026, 10, 5, 22, 0, tzinfo=ZONA)  # ya es el día 6 en UTC
    numero = lista(cliente)
    poner_hora(reloj, pago_de_la_noche)
    pagar(cliente, numero)

    mismo_dia = _ingresos(cliente)
    poner_hora(reloj, pago_de_la_noche + timedelta(hours=3))  # ya es el día 6 en Monterrey
    dia_siguiente = _ingresos(cliente)

    assert mismo_dia == {"fecha": "2026-10-05", "total": "3000.00"}
    assert dia_siguiente == {"fecha": "2026-10-06", "total": "0.00"}


def test_revision_de_plazos_es_idempotente(cliente: TestClient, reloj: Mock) -> None:
    presentada(cliente)
    poner_hora(reloj, AHORA + timedelta(hours=49))

    primera = revisar_plazos(cliente)
    segunda = revisar_plazos(cliente)

    assert primera["alertas_de_recontacto"] == 1
    assert segunda["alertas_de_recontacto"] == 0


def test_la_revision_de_plazos_solo_acepta_al_sistema(cliente: TestClient) -> None:
    assert cliente.post("/api/revisiones/plazos").status_code == 401
    assert cliente.post("/api/revisiones/plazos", headers=TECNICO).status_code == 403
    assert cliente.post("/api/revisiones/plazos", headers=SISTEMA).status_code == 200
