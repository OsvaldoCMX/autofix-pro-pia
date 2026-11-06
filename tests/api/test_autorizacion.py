"""Autorización de punta a punta: criterios CA-010 a CA-012 y CA-016 a CA-018."""
from __future__ import annotations

from fastapi.testclient import TestClient

from tests.api.pasos import (
    ASESOR,
    AUTORIZANTE_PARTICULAR,
    cotizada,
    decision,
    exigir,
    expediente_de,
)


def test_ca_010_autorizacion_parcial_registra_autorizante_y_no_autorizados(
    cliente: TestClient,
) -> None:
    numero, id_cotizacion = cotizada(cliente)

    respuesta = cliente.post(
        f"/api/cotizaciones/{id_cotizacion}/decision", json=decision([1]), headers=ASESOR
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id_cotizacion": id_cotizacion,
        "estado_cotizacion": "Autorizada Parcialmente",
        "estado_orden": "Autorizada",
        "trabajos_autorizados": ["Trabajo 1"],
        "trabajos_no_autorizados": ["Trabajo 2"],
    }
    detalle = exigir(cliente.get(f"/api/cotizaciones/{id_cotizacion}", headers=ASESOR), 200)
    assert detalle["autorizante"] == AUTORIZANTE_PARTICULAR[0]
    assert detalle["fecha_decision"] is not None
    estados = {t["descripcion"]: t["estado"] for t in expediente_de(cliente, numero)["trabajos"]}
    assert estados == {"Trabajo 1": "Pendiente", "Trabajo 2": "No Autorizado"}


def test_ca_010_autorizacion_total_deja_la_cotizacion_autorizada(cliente: TestClient) -> None:
    _, id_cotizacion = cotizada(cliente)

    respuesta = cliente.post(
        f"/api/cotizaciones/{id_cotizacion}/decision", json=decision([1, 2]), headers=ASESOR
    )

    assert respuesta.json()["estado_cotizacion"] == "Autorizada"


def test_rn_07_autorizante_invalido_responde_409(cliente: TestClient) -> None:
    _, id_cotizacion = cotizada(cliente)

    respuesta = cliente.post(
        f"/api/cotizaciones/{id_cotizacion}/decision",
        json={
            "lineas_autorizadas": [1],
            "nombre_del_autorizante": "Otra Persona",
            "rol_del_autorizante": "Cliente",
        },
        headers=ASESOR,
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "AutorizanteNoValido"


def test_rol_de_autorizante_desconocido_responde_422(cliente: TestClient) -> None:
    _, id_cotizacion = cotizada(cliente)

    respuesta = cliente.post(
        f"/api/cotizaciones/{id_cotizacion}/decision",
        json={
            "lineas_autorizadas": [1],
            "nombre_del_autorizante": "Luis Peña",
            "rol_del_autorizante": "Conductor",
        },
        headers=ASESOR,
    )

    assert respuesta.status_code == 422
