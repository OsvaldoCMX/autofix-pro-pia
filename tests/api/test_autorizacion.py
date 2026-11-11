"""Autorización de punta a punta: criterios CA-010 a CA-012 y CA-016 a CA-018."""
from __future__ import annotations

from fastapi.testclient import TestClient

from tests.api.pasos import (
    ASESOR,
    AUTORIZANTE_PARTICULAR,
    ID_TECNICO,
    TECNICO,
    asignar,
    autorizada,
    completar,
    con_adicional,
    cotizada,
    decidir,
    decision,
    en_reparacion,
    exigir,
    expediente_de,
    iniciar,
    tipos_de_alertas,
    trabajos,
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


def test_ca_011_solo_se_asignan_trabajos_autorizados(cliente: TestClient) -> None:
    numero, _ = autorizada(cliente, lineas=(1,))

    no_autorizado = cliente.post(
        f"/api/ordenes/{numero}/asignacion-trabajos",
        json={"ids_trabajos": [2], "tecnico": ID_TECNICO},
        headers=ASESOR,
    )
    autorizado = cliente.post(
        f"/api/ordenes/{numero}/asignacion-trabajos",
        json={"ids_trabajos": [1], "tecnico": ID_TECNICO},
        headers=ASESOR,
    )

    assert no_autorizado.status_code == 409
    assert no_autorizado.json()["error"] == "TrabajoNoAutorizado"
    assert autorizado.status_code == 200
    assert autorizado.json()["ids_trabajos"] == [1]


def test_ca_012_rechazo_total_impide_asignar_y_habilita_entrega_sin_reparacion(
    cliente: TestClient,
) -> None:
    numero, id_cotizacion = cotizada(cliente)

    resultado = decidir(cliente, id_cotizacion, [])
    asignacion = cliente.post(
        f"/api/ordenes/{numero}/asignacion-trabajos",
        json={"ids_trabajos": [1], "tecnico": ID_TECNICO},
        headers=ASESOR,
    )

    assert resultado["estado_cotizacion"] == "Rechazada"
    assert asignacion.status_code == 409
    assert asignacion.json()["error"] == "TrabajoNoAutorizado"
    assert expediente_de(cliente, numero)["rechazo_total"] is True


def test_ca_016_adicional_es_v2_sin_gerente_y_no_cambia_la_original(cliente: TestClient) -> None:
    numero, id_original = autorizada(cliente)
    asignar(cliente, numero)
    iniciar(cliente, numero)
    original = exigir(cliente.get(f"/api/cotizaciones/{id_original}", headers=ASESOR), 200)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cotizaciones-adicionales",
        json=trabajos("20000.00"),
        headers=ASESOR,
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["tipo"] == "Adicional"
    assert respuesta.json()["version"] == "v.2"
    assert respuesta.json()["estado"] == "Pendiente de Autorización del Cliente"
    assert exigir(cliente.get(f"/api/cotizaciones/{id_original}", headers=ASESOR), 200) == original


def test_ca_017_adicional_autorizada_agrega_trabajos_y_alerta_al_tecnico(
    cliente: TestClient,
) -> None:
    numero, id_adicional = con_adicional(cliente)

    resultado = decidir(cliente, id_adicional, [1, 2])

    assert resultado["estado_cotizacion"] == "Autorizada"
    nuevos = expediente_de(cliente, numero)["trabajos"][2:]
    assert [trabajo["estado"] for trabajo in nuevos] == ["Pendiente", "Pendiente"]
    assert "CotizacionAutorizada" in tipos_de_alertas(cliente, TECNICO)


def test_ca_018_adicional_rechazada_pasa_a_lista_si_los_originales_terminaron(
    cliente: TestClient,
) -> None:
    numero, id_adicional = con_adicional(cliente)
    iniciar(cliente, numero, 2)
    completar(cliente, numero, 1)
    completar(cliente, numero, 2)
    assert expediente_de(cliente, numero)["estado"] == "En Reparación"

    resultado = decidir(cliente, id_adicional, [])

    assert resultado["estado_cotizacion"] == "Rechazada"
    assert resultado["estado_orden"] == "Lista para Entrega"
    nuevos = expediente_de(cliente, numero)["trabajos"][2:]
    assert [trabajo["estado"] for trabajo in nuevos] == ["No Autorizado", "No Autorizado"]


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


def test_rn_08_trabajo_no_autorizado_no_se_inicia(cliente: TestClient) -> None:
    numero, _ = autorizada(cliente, lineas=(1,))

    respuesta = cliente.post(f"/api/ordenes/{numero}/trabajos/2/inicio", headers=TECNICO)

    assert respuesta.status_code == 403  # sin técnico asignado, modelo-de-dominio.md §7
    assert expediente_de(cliente, numero)["trabajos"][1]["estado"] == "No Autorizado"


def test_rn_24_segunda_adicional_es_v3(cliente: TestClient) -> None:
    numero, id_adicional = con_adicional(cliente)
    decidir(cliente, id_adicional, [1])  # RN-33: la v.2 ya tiene decisión

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/cotizaciones-adicionales",
        json=trabajos("100.00"),
        headers=ASESOR,
    )

    assert respuesta.json()["version"] == "v.3"


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


# ------------------------------------------------------------------ una adicional a la vez (H-PIA-26)
def test_ca_061_doble_clic_en_adicional_responde_409(cliente: TestClient) -> None:
    numero = en_reparacion(cliente)
    url = f"/api/ordenes/{numero}/cotizaciones-adicionales"
    exigir(cliente.post(url, json=trabajos("500.00"), headers=ASESOR), 201)

    respuesta = exigir(cliente.post(url, json=trabajos("500.00"), headers=ASESOR), 409)

    assert respuesta["detalle"] == (
        "La cotización adicional v.2 todavía espera la decisión del cliente; "
        "registre esa decisión antes de generar otra."
    )


# ------------------------------------------------------------------ nombre del autorizante (H-PIA-27)
def test_ca_063_el_nombre_con_espacios_de_mas_se_acepta(cliente: TestClient) -> None:
    _, id_cotizacion = cotizada(cliente)
    cuerpo = {**decision([1, 2]), "nombre_del_autorizante": "  luis   PEÑA "}

    respuesta = exigir(
        cliente.post(f"/api/cotizaciones/{id_cotizacion}/decision", json=cuerpo, headers=ASESOR),
        200,
    )

    assert respuesta["estado_cotizacion"] == "Autorizada"
