"""Cotización de punta a punta: criterios CA-005 a CA-009, CA-040 y la corrección (CA-047 a CA-051)."""
from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.api.pasos import (
    ASESOR,
    GERENTE,
    ID_ASESOR,
    alertas_de,
    autorizada,
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


# ------------------------------------------------------------------ corrección (H-PIA-21)

def _correccion(*importes: str, motivo: str = "Mano de obra mal capturada") -> dict[str, Any]:
    return {**trabajos(*importes), "motivo": motivo}


def _corregir(cliente: TestClient, id_cotizacion: str, cuerpo: dict[str, Any]) -> Any:
    return cliente.post(f"/api/cotizaciones/{id_cotizacion}/correcciones", json=cuerpo, headers=ASESOR)


def _detalle(cliente: TestClient, id_cotizacion: str) -> dict[str, Any]:
    return exigir(cliente.get(f"/api/cotizaciones/{id_cotizacion}", headers=ASESOR), 200)


def test_ca_047_corrige_conserva_numero_version_y_queda_sin_presentar(
    cliente: TestClient,
) -> None:
    _, id_cotizacion = presentada(cliente)

    respuesta = exigir(_corregir(cliente, id_cotizacion, _correccion("800.00", "2000.00")), 201)

    assert respuesta["id"] == id_cotizacion
    assert respuesta["version"] == "v.1"
    assert respuesta["estado"] == PENDIENTE_DEL_CLIENTE
    assert respuesta["total"] == "2800.00"
    assert "fecha_presentacion" not in respuesta
    exigir(cliente.post(f"/api/cotizaciones/{id_cotizacion}/presentacion", headers=ASESOR), 200)


def test_ca_047_el_historial_aparece_en_la_cotizacion_y_el_expediente(
    cliente: TestClient,
) -> None:
    numero, id_cotizacion = presentada(cliente)
    exigir(_corregir(cliente, id_cotizacion, _correccion("2500.00")), 201)

    (correccion,) = _detalle(cliente, id_cotizacion)["correcciones"]

    assert correccion["asesor"] == ID_ASESOR
    assert correccion["motivo"] == "Mano de obra mal capturada"
    assert (correccion["total_anterior"], correccion["total_nuevo"]) == ("3000.00", "2500.00")
    assert correccion["estado_anterior"] == correccion["estado_nuevo"] == PENDIENTE_DEL_CLIENTE
    assert correccion["fecha_presentacion_anterior"] is not None
    assert expediente_de(cliente, numero)["cotizaciones"][0]["correcciones"] == [correccion]


def test_ca_048_correccion_arriba_de_15000_regresa_al_gerente_y_le_avisa(
    cliente: TestClient,
) -> None:
    _, id_cotizacion = por_aprobar(cliente)
    revision = {"aprobada": True}
    exigir(
        cliente.post(
            f"/api/cotizaciones/{id_cotizacion}/revision-gerencial", json=revision, headers=GERENTE
        ),
        200,
    )

    respuesta = exigir(_corregir(cliente, id_cotizacion, _correccion("21000.00")), 201)

    assert respuesta["estado"] == PENDIENTE_DEL_GERENTE
    assert "fecha_aprobacion_gerencial" not in respuesta
    assert tipos_de_alertas(cliente, GERENTE).count("AprobacionGerencialRequerida") == 2
    presentar = cliente.post(f"/api/cotizaciones/{id_cotizacion}/presentacion", headers=ASESOR)
    assert presentar.status_code == 409


def test_ca_049_en_revision_baja_de_15000_pasa_al_cliente(cliente: TestClient) -> None:
    _, id_cotizacion = por_aprobar(cliente)

    respuesta = exigir(_corregir(cliente, id_cotizacion, _correccion("14000.00")), 201)

    assert respuesta["estado"] == PENDIENTE_DEL_CLIENTE


def test_ca_049_en_revision_sigue_arriba_y_no_cambia_de_estado(cliente: TestClient) -> None:
    _, id_cotizacion = por_aprobar(cliente)

    respuesta = exigir(_corregir(cliente, id_cotizacion, _correccion("22000.00")), 201)

    assert respuesta["estado"] == PENDIENTE_DEL_GERENTE
    assert respuesta["total"] == "22000.00"


def test_ca_050_no_se_corrige_en_requiere_ajuste(cliente: TestClient) -> None:
    _, id_cotizacion = por_aprobar(cliente)
    rechazo = {"aprobada": False, "observaciones": "Revise la mano de obra"}
    exigir(
        cliente.post(
            f"/api/cotizaciones/{id_cotizacion}/revision-gerencial", json=rechazo, headers=GERENTE
        ),
        200,
    )

    respuesta = exigir(_corregir(cliente, id_cotizacion, _correccion("18000.00")), 409)

    assert "guarde la cotización ajustada" in respuesta["detalle"]


def test_ca_050_no_se_corrige_ya_decidida(cliente: TestClient) -> None:
    _, id_cotizacion = autorizada(cliente)

    respuesta = exigir(_corregir(cliente, id_cotizacion, _correccion("100.00")), 409)

    assert "cotización adicional" in respuesta["detalle"]


def test_ca_050_motivo_obligatorio(cliente: TestClient) -> None:
    _, id_cotizacion = cotizada(cliente)

    sin_motivo = exigir(_corregir(cliente, id_cotizacion, trabajos("100.00")), 422)
    en_blanco = exigir(_corregir(cliente, id_cotizacion, _correccion("100.00", motivo="  ")), 422)

    assert "motivo" in sin_motivo["detalle"]
    assert "motivo" in en_blanco["detalle"]
    assert _detalle(cliente, id_cotizacion)["total"] == "3000.00"


def test_ca_050_cotizacion_inexistente_responde_404(cliente: TestClient) -> None:
    exigir(_corregir(cliente, "COT-9999", _correccion("100.00")), 404)


def test_ca_051_sin_alerta_hasta_volver_a_presentar(cliente: TestClient, reloj: Mock) -> None:
    _, id_cotizacion = presentada(cliente)
    poner_hora(reloj, AHORA + timedelta(hours=49))
    exigir(cliente.post(f"/api/cotizaciones/{id_cotizacion}/recontactos", headers=ASESOR), 201)
    exigir(_corregir(cliente, id_cotizacion, _correccion("2500.00")), 201)

    poner_hora(reloj, AHORA + timedelta(hours=200))
    sin_presentar = revisar_plazos(cliente)
    exigir(cliente.post(f"/api/cotizaciones/{id_cotizacion}/presentacion", headers=ASESOR), 200)
    poner_hora(reloj, AHORA + timedelta(hours=247))
    antes_del_plazo = revisar_plazos(cliente)
    poner_hora(reloj, AHORA + timedelta(hours=249))
    despues_del_plazo = revisar_plazos(cliente)

    assert sin_presentar["alertas_de_recontacto"] == 0
    assert antes_del_plazo["alertas_de_recontacto"] == 0
    assert despues_del_plazo["alertas_de_recontacto"] == 1


# ------------------------------------------------------------------ trabajos de $0.00 (H-PIA-25)
def test_ca_060_un_trabajo_de_0_responde_422(cliente: TestClient) -> None:
    numero = diagnosticada(cliente)

    respuesta = exigir(
        cliente.post(
            f"/api/ordenes/{numero}/cotizaciones", json=trabajos("100.00", "0.00"), headers=ASESOR
        ),
        422,
    )

    assert respuesta["detalle"] == (
        "El trabajo 2 («Trabajo 2») vale $0.00: capture su mano de obra o sus refacciones."
    )
