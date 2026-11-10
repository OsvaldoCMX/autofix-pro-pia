"""Caja y entrega de punta a punta: criterios CA-026, CA-027, CA-039 y CA-041 a CA-043."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from tests.api.pasos import (
    ASESOR,
    CAJA,
    GERENTE,
    autorizada,
    cotizada,
    decidir,
    exigir,
    expediente_de,
    lista,
    pagada,
    por_cobrar,
    trabajos,
)
from tests.unit.application.escenarios import poner_hora

ZONA = ZoneInfo("America/Monterrey")


def test_ca_026_pago_de_contado_pasa_a_pagada(cliente: TestClient) -> None:
    numero = lista(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/pago", json={"monto": "3000.00", "forma": "Efectivo"}, headers=CAJA
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "Pagada"
    assert respuesta.json()["monto"] == "3000.00"
    assert respuesta.json()["forma"] == "Efectivo"
    assert expediente_de(cliente, numero)["pago_monto"] == "3000.00"


def test_ca_026_despues_del_pago_no_se_generan_mas_cotizaciones(cliente: TestClient) -> None:
    numero = pagada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cotizaciones-adicionales",
        json=trabajos("100.00"),
        headers=ASESOR,
    )

    assert respuesta.status_code == 409


def test_ca_027_recibo_responde_501_hasta_la_fase_10(cliente: TestClient) -> None:
    numero = pagada(cliente)

    respuesta = cliente.get(f"/api/ordenes/{numero}/recibo/pdf", headers=CAJA)

    assert respuesta.status_code == 501
    assert respuesta.json()["error"] == "FuncionNoImplementada"


def test_ca_039_cargo_a_credito_pasa_a_por_cobrar(cliente: TestClient) -> None:
    numero = lista(cliente, flotilla=True)

    respuesta = cliente.post(f"/api/ordenes/{numero}/cargo-a-credito", headers=CAJA)

    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "Por Cobrar (Crédito)"
    assert respuesta.json()["monto"] == "3000.00"
    expediente = expediente_de(cliente, numero)
    assert expediente["credito_monto"] == "3000.00"
    assert expediente["credito_fecha_vencimiento"] is None


def test_ca_041_entrega_cierra_y_fija_vencimiento(cliente: TestClient) -> None:
    numero = por_cobrar(cliente)

    respuesta = cliente.post(f"/api/ordenes/{numero}/entrega", headers=ASESOR)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "Cerrada"
    assert respuesta.json()["fecha_entrega"] is not None
    assert respuesta.json()["fecha_vencimiento_credito"] == "2026-10-20"


def test_ca_041_entrega_de_orden_pagada_no_tiene_vencimiento(cliente: TestClient) -> None:
    numero = pagada(cliente)

    respuesta = cliente.post(f"/api/ordenes/{numero}/entrega", headers=ASESOR)

    assert respuesta.json()["estado"] == "Cerrada"
    assert respuesta.json()["fecha_vencimiento_credito"] is None


def test_ca_042_entrega_sin_pago_responde_409_con_el_mensaje_del_contrato(
    cliente: TestClient,
) -> None:
    numero, _ = autorizada(cliente)

    respuesta = cliente.post(f"/api/ordenes/{numero}/entrega", headers=ASESOR)

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "error": "EntregaNoPermitida",
        "detalle": (
            f"El vehículo de la orden {numero} todavía no se puede entregar: su servicio sigue "
            "en proceso (estado «Autorizada»). Cuando esté «Lista para Entrega», "
            "primero debe registrarse el pago o el cargo a crédito."
        ),
        "codigo": 409,
    }


def test_ca_043_entrega_sin_reparacion_no_genera_cobro(cliente: TestClient) -> None:
    numero, id_cotizacion = cotizada(cliente)
    decidir(cliente, id_cotizacion, [])

    respuesta = cliente.post(f"/api/ordenes/{numero}/entrega-sin-reparacion", headers=ASESOR)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "Cerrada sin Reparación"
    assert respuesta.json()["fecha_entrega"] is not None
    expediente = expediente_de(cliente, numero)
    assert expediente["pago_monto"] is None
    assert expediente["credito_monto"] is None


@pytest.mark.parametrize("monto", ["2999.99", "3000.01"])
def test_rn_16_monto_distinto_responde_409(cliente: TestClient, monto: str) -> None:
    numero = lista(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/pago", json={"monto": monto, "forma": "Tarjeta"}, headers=CAJA
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "PagoNoPermitido"


def test_rn_16_flotilla_no_paga_de_contado_responde_409(cliente: TestClient) -> None:
    numero = lista(cliente, flotilla=True)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/pago", json={"monto": "3000.00", "forma": "Tarjeta"}, headers=CAJA
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "PagoNoPermitido"


def test_rn_16_forma_de_pago_desconocida_responde_422(cliente: TestClient) -> None:
    numero = lista(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/pago", json={"monto": "3000.00", "forma": "Cheque"}, headers=CAJA
    )

    assert respuesta.status_code == 422
    assert "Efectivo" in respuesta.json()["detalle"]


def test_rn_17_credito_vence_15_dias_despues_de_la_entrega(
    cliente: TestClient, reloj: Mock
) -> None:
    numero = por_cobrar(cliente)
    poner_hora(reloj, datetime(2026, 10, 12, 23, 30, tzinfo=ZONA))  # ya es día 13 en UTC

    respuesta = exigir(cliente.post(f"/api/ordenes/{numero}/entrega", headers=ASESOR), 200)

    assert respuesta["fecha_vencimiento_credito"] == "2026-10-27"


def test_rn_18_sin_rechazo_total_no_se_entrega_sin_reparacion(cliente: TestClient) -> None:
    numero, _ = cotizada(cliente)

    respuesta = cliente.post(f"/api/ordenes/{numero}/entrega-sin-reparacion", headers=ASESOR)

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "EntregaNoPermitida"


# ------------------------------------------------------------------ corrección de la forma de pago
def test_ca_058_corrige_la_forma_sin_cambiar_monto_ni_fecha(cliente: TestClient) -> None:
    numero = pagada(cliente)
    antes = expediente_de(cliente, numero)

    respuesta = exigir(
        cliente.put(f"/api/ordenes/{numero}/pago", json={"forma": "Efectivo"}, headers=CAJA), 200
    )

    despues = expediente_de(cliente, numero)
    assert respuesta["forma"] == "Efectivo"
    assert respuesta["estado"] == "Pagada"
    assert despues["pago_monto"] == antes["pago_monto"]
    assert despues["pago_registrado_en"] == antes["pago_registrado_en"]
    assert despues["pago_forma"] == "Efectivo"


def test_rn_30_forma_de_pago_no_cambia_los_ingresos_del_dia(cliente: TestClient) -> None:
    numero = pagada(cliente)
    antes = exigir(cliente.get("/api/gerencia/ingresos-del-dia", headers=GERENTE), 200)

    exigir(
        cliente.put(f"/api/ordenes/{numero}/pago", json={"forma": "Efectivo"}, headers=CAJA), 200
    )

    assert exigir(cliente.get("/api/gerencia/ingresos-del-dia", headers=GERENTE), 200) == antes


def test_ca_058_despues_de_entregar_responde_409(cliente: TestClient) -> None:
    numero = pagada(cliente)
    exigir(cliente.post(f"/api/ordenes/{numero}/entrega", headers=ASESOR), 200)

    respuesta = exigir(
        cliente.put(f"/api/ordenes/{numero}/pago", json={"forma": "Efectivo"}, headers=CAJA), 409
    )

    assert respuesta["error"] == "CorreccionNoPermitida"
