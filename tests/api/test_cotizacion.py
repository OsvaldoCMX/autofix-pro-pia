"""Cotización de punta a punta: criterios CA-005 a CA-009 y CA-040."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.api.pasos import (
    ASESOR,
    GERENTE,
    alertas_de,
    cotizada,
    diagnosticada,
    exigir,
    expediente_de,
    por_aprobar,
    presentada,
    recibida,
    revisar_plazos,
    tipos_de_alertas,
    trabajos,
)
from tests.integration.apoyo_base import registrar_servicios_de_orden
from tests.unit.application.escenarios import AHORA, poner_hora

PENDIENTE_DEL_CLIENTE = "Pendiente de Autorización del Cliente"
PENDIENTE_DEL_GERENTE = "Pendiente de Aprobación Gerencial"
EJEMPLO_DEL_CONTRATO = {
    "trabajos": [
        {
            "numero": 1,
            "descripcion": "Afinación 07 (AUT-P007) x1",
            "mano_de_obra": "785.00",
            "refacciones": [],
        },
        {
            "numero": 2,
            "descripcion": "Cambio aceite 12 (AUT-P012) x2",
            "mano_de_obra": "2280.00",
            "refacciones": [],
        },
    ]
}


def test_ca_005_genera_cotizacion_inicial_como_el_ejemplo_del_contrato(
    cliente: TestClient,
) -> None:
    numero = diagnosticada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cotizaciones", json=EJEMPLO_DEL_CONTRATO, headers=ASESOR
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "id": "COT-0001",
        "numero_orden": numero,
        "version": "v.1",
        "tipo": "Inicial",
        "estado": PENDIENTE_DEL_CLIENTE,
        "total": "3065.00",
    }
    assert expediente_de(cliente, numero)["estado"] == "Cotizada"


def test_ca_005_detalle_muestra_desglose_y_pdf_responde_501(cliente: TestClient) -> None:
    numero = diagnosticada(cliente)
    cuerpo = {
        "trabajos": [
            {
                "numero": 1,
                "descripcion": "Cambio de balatas",
                "mano_de_obra": "500.00",
                "refacciones": [
                    {"descripcion": "Balata", "cantidad": 2, "precio_unitario": "250.50"}
                ],
            }
        ]
    }
    creada = exigir(
        cliente.post(f"/api/ordenes/{numero}/cotizaciones", json=cuerpo, headers=ASESOR), 201
    )

    detalle = exigir(cliente.get(f"/api/cotizaciones/{creada['id']}", headers=ASESOR), 200)

    assert detalle["total"] == "1001.00"
    assert detalle["generada_en"].endswith(("Z", "+00:00"))
    linea = detalle["lineas"][0]
    assert linea["subtotal"] == "1001.00"
    assert linea["refacciones"][0]["importe"] == "501.00"
    assert cliente.get(f"/api/cotizaciones/{creada['id']}/pdf", headers=ASESOR).status_code == 501


def test_ca_006_presentar_registra_la_fecha(cliente: TestClient) -> None:
    _, id_cotizacion = cotizada(cliente)

    respuesta = cliente.post(f"/api/cotizaciones/{id_cotizacion}/presentacion", headers=ASESOR)

    assert respuesta.status_code == 200
    assert respuesta.json()["fecha_presentacion"].endswith("Z")
    assert respuesta.json()["estado"] == PENDIENTE_DEL_CLIENTE


def test_ca_006_presentar_dos_veces_responde_409(cliente: TestClient) -> None:
    _, id_cotizacion = presentada(cliente)

    respuesta = cliente.post(f"/api/cotizaciones/{id_cotizacion}/presentacion", headers=ASESOR)

    assert respuesta.status_code == 409


def test_ca_007_mayor_a_15000_pide_gerente_impide_presentar_y_alerta(
    cliente: TestClient,
) -> None:
    _, id_cotizacion = por_aprobar(cliente)

    pendientes = exigir(
        cliente.get("/api/gerencia/cotizaciones-por-aprobar", headers=GERENTE), 200
    )
    presentacion = cliente.post(
        f"/api/cotizaciones/{id_cotizacion}/presentacion", headers=ASESOR
    )

    assert [c["id_cotizacion"] for c in pendientes] == [id_cotizacion]
    assert pendientes[0]["total"] == "20000.00"
    assert presentacion.status_code == 409
    assert "AprobacionGerencialRequerida" in tipos_de_alertas(cliente, GERENTE)


def test_ca_008_gerente_aprueba_y_alerta_al_asesor(cliente: TestClient) -> None:
    _, id_cotizacion = por_aprobar(cliente)

    respuesta = cliente.post(
        f"/api/cotizaciones/{id_cotizacion}/revision-gerencial",
        json={"aprobada": True},
        headers=GERENTE,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == PENDIENTE_DEL_CLIENTE
    assert respuesta.json()["fecha_aprobacion_gerencial"].endswith("Z")
    assert "CotizacionAprobadaPorGerente" in tipos_de_alertas(cliente, ASESOR)
    assert exigir(cliente.get("/api/gerencia/cotizaciones-por-aprobar", headers=GERENTE), 200) == []


def test_ca_009_gerente_rechaza_y_ajuste_no_regresa_a_revision(cliente: TestClient) -> None:
    _, id_cotizacion = por_aprobar(cliente)

    rechazo = exigir(
        cliente.post(
            f"/api/cotizaciones/{id_cotizacion}/revision-gerencial",
            json={"aprobada": False, "observaciones": "Revisar la mano de obra"},
            headers=GERENTE,
        ),
        200,
    )
    ajuste = exigir(
        cliente.put(
            f"/api/cotizaciones/{id_cotizacion}/lineas",
            json=trabajos("18000.00"),
            headers=ASESOR,
        ),
        200,
    )

    assert rechazo["estado"] == "Requiere Ajuste"
    assert ajuste["estado"] == PENDIENTE_DEL_CLIENTE
    assert ajuste["total"] == "18000.00"
    alerta = next(
        alerta
        for alerta in alertas_de(cliente, ASESOR)
        if alerta["tipo"] == "CotizacionRechazadaPorGerente"
    )
    assert "Revisar la mano de obra" in alerta["mensaje"]


def test_ca_040_revision_alerta_a_las_48_horas_y_recontacto_reinicia_el_plazo(
    cliente: TestClient, reloj: Mock
) -> None:
    _, id_cotizacion = presentada(cliente)
    poner_hora(reloj, AHORA + timedelta(hours=49))

    primera = revisar_plazos(cliente)
    recontacto = cliente.post(f"/api/cotizaciones/{id_cotizacion}/recontactos", headers=ASESOR)
    poner_hora(reloj, AHORA + timedelta(hours=96))
    antes_del_plazo = revisar_plazos(cliente)
    poner_hora(reloj, AHORA + timedelta(hours=98))
    despues_del_plazo = revisar_plazos(cliente)

    assert primera == {"alertas_de_refaccion": 0, "alertas_de_recontacto": 1}
    assert recontacto.status_code == 201
    assert recontacto.json()["estado"] == PENDIENTE_DEL_CLIENTE
    assert antes_del_plazo["alertas_de_recontacto"] == 0
    assert despues_del_plazo["alertas_de_recontacto"] == 1
    assert tipos_de_alertas(cliente, ASESOR).count("CotizacionSinRespuesta") == 2


def test_ca_040_recontacto_sin_presentar_responde_409(cliente: TestClient) -> None:
    _, id_cotizacion = cotizada(cliente)

    respuesta = cliente.post(f"/api/cotizaciones/{id_cotizacion}/recontactos", headers=ASESOR)

    assert respuesta.status_code == 409


def test_rn_02_no_se_cotiza_sin_diagnostico_responde_409(cliente: TestClient) -> None:
    numero = recibida(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cotizaciones", json=trabajos("1000.00"), headers=ASESOR
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "DiagnosticoRequerido"


def test_rn_04_exactamente_15000_no_requiere_gerente(cliente: TestClient) -> None:
    numero = diagnosticada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cotizaciones", json=trabajos("15000.00"), headers=ASESOR
    )

    assert respuesta.json()["estado"] == PENDIENTE_DEL_CLIENTE


def test_rn_04_un_centavo_mas_requiere_gerente(cliente: TestClient) -> None:
    numero = diagnosticada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cotizaciones", json=trabajos("15000.01"), headers=ASESOR
    )

    assert respuesta.json()["estado"] == PENDIENTE_DEL_GERENTE


def test_rn_05_rechazo_sin_observaciones_responde_422(cliente: TestClient) -> None:
    _, id_cotizacion = por_aprobar(cliente)

    respuesta = cliente.post(
        f"/api/cotizaciones/{id_cotizacion}/revision-gerencial",
        json={"aprobada": False, "observaciones": "  "},
        headers=GERENTE,
    )

    assert respuesta.status_code == 422
    assert "observaciones" in respuesta.json()["detalle"]


def test_rn_06_pendiente_de_gerente_no_se_presenta_responde_409(cliente: TestClient) -> None:
    _, id_cotizacion = por_aprobar(cliente)

    respuesta = cliente.post(f"/api/cotizaciones/{id_cotizacion}/presentacion", headers=ASESOR)

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "OperacionDeCotizacionNoPermitida"


def test_rn_12_antes_de_48_horas_no_hay_alerta(cliente: TestClient, reloj: Mock) -> None:
    presentada(cliente)
    poner_hora(reloj, AHORA + timedelta(hours=48))

    resultado = revisar_plazos(cliente)

    assert resultado["alertas_de_recontacto"] == 0


@pytest.mark.parametrize("importe", ["-1.00", 1500.0, 1500, "1500", "15.5", "abc", "12345678901.00"])
def test_rn_23_importe_negativo_o_numerico_responde_422(
    cliente: TestClient, importe: object
) -> None:
    numero = diagnosticada(cliente)
    cuerpo = {"trabajos": [{"numero": 1, "descripcion": "T", "mano_de_obra": importe}]}

    respuesta = cliente.post(f"/api/ordenes/{numero}/cotizaciones", json=cuerpo, headers=ASESOR)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "ValorInvalido"


def test_rn_23_cantidad_cero_responde_422(cliente: TestClient) -> None:
    numero = diagnosticada(cliente)
    cuerpo = {
        "trabajos": [
            {
                "numero": 1,
                "descripcion": "T",
                "mano_de_obra": "10.00",
                "refacciones": [
                    {"descripcion": "Balata", "cantidad": 0, "precio_unitario": "1.00"}
                ],
            }
        ]
    }

    respuesta = cliente.post(f"/api/ordenes/{numero}/cotizaciones", json=cuerpo, headers=ASESOR)

    assert respuesta.status_code == 422


def test_rn_23_cotizacion_sin_trabajos_responde_422(cliente: TestClient) -> None:
    numero = diagnosticada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cotizaciones", json={"trabajos": []}, headers=ASESOR
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "CotizacionSinTrabajos"
    assert expediente_de(cliente, numero)["estado"] == "En Diagnóstico"


def test_cotizacion_inexistente_responde_404(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/cotizaciones/COT-9999", headers=ASESOR)

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "CotizacionNoEncontrada"



def test_servicio_inhabilitado_responde_422_y_la_orden_sigue_en_diagnostico(
    cliente: TestClient, motor: Engine
) -> None:
    """D-05: aunque las líneas sean texto libre, esa orden no se cotiza."""
    numero = diagnosticada(cliente)
    registrar_servicios_de_orden(motor, numero, ("AUT-P001",), ("AUT-P011",))

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cotizaciones", json=trabajos("1000.00"), headers=ASESOR
    )

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert (cuerpo["error"], cuerpo["codigo"]) == ("ValorInvalido", 422)
    assert "AUT-P011" in cuerpo["detalle"]
    assert expediente_de(cliente, numero)["estado"] == "En Diagnóstico"
