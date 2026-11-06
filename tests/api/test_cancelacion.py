"""Cancelación de punta a punta: criterios CA-044 y CA-045."""
from __future__ import annotations

from fastapi.testclient import TestClient

from tests.api.pasos import ASESOR, TECNICO, cotizada, en_diagnostico, exigir, panel_de, recibida


def test_ca_044_cancela_orden_recibida_con_motivo(cliente: TestClient) -> None:
    numero = recibida(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cancelacion", json={"motivo": "Desistió"}, headers=ASESOR
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {"numero_orden": numero, "estado": "Cancelada"}
    expediente = exigir(cliente.get(f"/api/ordenes/{numero}", headers=ASESOR), 200)
    assert expediente["cancelacion_motivo"] == "Desistió"
    assert expediente["pago_monto"] is None
    assert expediente["credito_monto"] is None


def test_ca_044_quita_la_orden_del_panel_del_tecnico(cliente: TestClient) -> None:
    numero = en_diagnostico(cliente)
    assert [orden["numero_orden"] for orden in panel_de(cliente, TECNICO)] == [numero]

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cancelacion", json={"motivo": "Desistió"}, headers=ASESOR
    )

    assert respuesta.status_code == 200
    assert panel_de(cliente, TECNICO) == []


def test_ca_045_orden_con_cotizacion_no_se_cancela_responde_409(cliente: TestClient) -> None:
    numero, _ = cotizada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cancelacion", json={"motivo": "Desistió"}, headers=ASESOR
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "CancelacionNoPermitida"
    assert "se registra el rechazo total" in respuesta.json()["detalle"]


def test_rn_19_cancelar_sin_motivo_responde_422(cliente: TestClient) -> None:
    numero = recibida(cliente)

    sin_dato = cliente.post(f"/api/ordenes/{numero}/cancelacion", json={}, headers=ASESOR)
    en_blanco = cliente.post(
        f"/api/ordenes/{numero}/cancelacion", json={"motivo": "   "}, headers=ASESOR
    )

    assert sin_dato.status_code == 422
    assert en_blanco.status_code == 422


def test_cancelar_orden_inexistente_responde_404(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/ordenes/OS-9999/cancelacion", json={"motivo": "Desistió"}, headers=ASESOR
    )

    assert respuesta.status_code == 404


def test_solo_el_asesor_cancela(cliente: TestClient) -> None:
    numero = recibida(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cancelacion", json={"motivo": "Desistió"}, headers=TECNICO
    )

    assert respuesta.status_code == 403
