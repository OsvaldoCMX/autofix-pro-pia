"""Reparación y refacciones de punta a punta: CA-014, CA-015, CA-019 a CA-025 y CA-046."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from tests.api.pasos import (
    ASESOR,
    COMPRAS,
    OTRO_TECNICO,
    TECNICO,
    asignada,
    asignar,
    autorizada,
    completar,
    en_espera,
    en_reparacion,
    exigir,
    expediente_de,
    iniciar,
    panel_de,
    pausada,
    recibida,
    revisar_plazos,
    solicitar,
    tipos_de_alertas,
)
from tests.unit.application.escenarios import AHORA, poner_hora

ZONA = ZoneInfo("America/Monterrey")


def _pendientes(cliente: TestClient) -> list[dict[str, object]]:
    return exigir(cliente.get("/api/compras/solicitudes-pendientes", headers=COMPRAS), 200)


def _llegada(cliente: TestClient, numero: str, id_solicitud: int) -> dict[str, object]:
    return exigir(
        cliente.post(
            f"/api/ordenes/{numero}/solicitudes-de-compra/{id_solicitud}/llegada", headers=COMPRAS
        ),
        200,
    )


def test_ca_014_iniciar_trabajo_pasa_la_orden_a_en_reparacion(cliente: TestClient) -> None:
    numero = asignada(cliente)

    respuesta = cliente.post(f"/api/ordenes/{numero}/trabajos/1/inicio", headers=TECNICO)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "numero_orden": numero,
        "id_trabajo": 1,
        "estado_trabajo": "En Progreso",
        "estado_orden": "En Reparación",
    }


def test_ca_015_ultimo_trabajo_deja_lista_para_entrega_y_alerta(cliente: TestClient) -> None:
    numero = en_reparacion(cliente)
    iniciar(cliente, numero, 2)
    completar(cliente, numero, 1)

    respuesta = cliente.post(f"/api/ordenes/{numero}/trabajos/2/completado", headers=TECNICO)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado_trabajo"] == "Completado"
    assert respuesta.json()["estado_orden"] == "Lista para Entrega"
    assert "OrdenListaParaEntrega" in tipos_de_alertas(cliente, ASESOR)


def test_ca_046_vehiculo_retirado_no_se_trabaja_responde_409(cliente: TestClient) -> None:
    numero, _ = pausada(cliente)

    respuesta = cliente.post(f"/api/ordenes/{numero}/trabajos/1/inicio", headers=TECNICO)

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "TrabajoNoPermitido"
    assert "no está en el taller" in respuesta.json()["detalle"]


def test_ca_019_solicitud_aparece_en_compras_y_orden_en_espera(cliente: TestClient) -> None:
    numero = asignada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/solicitudes-de-compra",
        json={"id_trabajo": 2, "refaccion": "Balatas", "cantidad": 2},
        headers=TECNICO,
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["estado_solicitud"] == "Solicitada"
    assert respuesta.json()["estado_orden"] == "En Espera de Refacción"
    pendientes = _pendientes(cliente)
    assert [p["numero_orden"] for p in pendientes] == [numero]
    assert expediente_de(cliente, numero)["solicitudes"][0]["fecha_solicitud"] is not None


def test_ca_020_refaccion_de_trabajo_no_autorizado_responde_409(cliente: TestClient) -> None:
    numero, _ = autorizada(cliente, lineas=(1,))

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/solicitudes-de-compra",
        json={"id_trabajo": 2, "refaccion": "Balatas", "cantidad": 1},
        headers=TECNICO,
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "TrabajoNoAutorizado"


def test_ca_021_lista_pendientes_con_dias_habiles(cliente: TestClient, reloj: Mock) -> None:
    numero, id_solicitud = en_espera(cliente)
    poner_hora(reloj, AHORA + timedelta(days=2))

    pendiente = _pendientes(cliente)[0]

    assert pendiente == {
        "numero_orden": numero,
        "id_solicitud": id_solicitud,
        "refaccion": "Balatas",
        "cantidad": 2,
        "fecha_solicitud": pendiente["fecha_solicitud"],
        "dias_habiles_transcurridos": 2,
    }


def test_ca_022_llegada_regresa_estado_y_alerta_a_tecnico_y_asesor(cliente: TestClient) -> None:
    numero, id_solicitud = en_espera(cliente)

    resultado = _llegada(cliente, numero, id_solicitud)

    assert resultado["estado_solicitud"] == "Disponible"
    assert resultado["estado_orden"] == "Autorizada"
    assert _pendientes(cliente) == []
    assert "RefaccionDisponible" in tipos_de_alertas(cliente, ASESOR)
    assert "RefaccionDisponible" in tipos_de_alertas(cliente, TECNICO)


def test_ca_023_revision_alerta_y_aviso_evita_repetirla(cliente: TestClient, reloj: Mock) -> None:
    numero, id_solicitud = en_espera(cliente)
    poner_hora(reloj, AHORA + timedelta(days=4))

    primera = revisar_plazos(cliente)
    repetida = revisar_plazos(cliente)
    aviso = cliente.post(
        f"/api/ordenes/{numero}/solicitudes-de-compra/{id_solicitud}/aviso-al-cliente",
        headers=ASESOR,
    )
    poner_hora(reloj, AHORA + timedelta(days=5))
    despues_del_aviso = revisar_plazos(cliente)

    assert primera["alertas_de_refaccion"] == 1
    assert repetida["alertas_de_refaccion"] == 0
    assert aviso.status_code == 200
    assert despues_del_aviso["alertas_de_refaccion"] == 0
    assert tipos_de_alertas(cliente, ASESOR).count("RefaccionRetrasada") == 1
    solicitud = expediente_de(cliente, numero)["solicitudes"][0]
    assert solicitud["fecha_aviso_al_cliente"] is not None


def test_ca_024_retiro_con_firma_pausa_y_saca_de_la_fila(cliente: TestClient) -> None:
    numero, _ = en_espera(cliente)

    salida = cliente.post(f"/api/ordenes/{numero}/retiro", headers=ASESOR)
    pdf = cliente.get(f"/api/ordenes/{numero}/nota-de-responsabilidad/pdf", headers=ASESOR)
    firma = cliente.post(f"/api/ordenes/{numero}/retiro/firma", headers=ASESOR)

    assert salida.status_code == 201
    assert salida.json()["firmada"] is False
    assert pdf.status_code == 501
    assert firma.status_code == 200
    assert firma.json()["estado"] == "Pausada por Retiro de Vehículo"
    assert expediente_de(cliente, numero)["nota_firmada"] is True
    assert panel_de(cliente, TECNICO) == []


def test_ca_025_reactivar_deja_la_orden_al_final_de_la_fila(
    cliente: TestClient, reloj: Mock
) -> None:
    pausada_primero, _ = pausada(cliente)
    poner_hora(reloj, AHORA + timedelta(hours=1))
    otra = asignada(cliente)
    poner_hora(reloj, AHORA + timedelta(hours=2))

    respuesta = cliente.post(f"/api/ordenes/{pausada_primero}/reactivacion", headers=ASESOR)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "En Espera de Refacción"
    assert [orden["numero_orden"] for orden in panel_de(cliente, TECNICO)] == [
        otra,
        pausada_primero,
    ]


def test_ca_025_reactivar_con_las_refacciones_completas_regresa_a_autorizada(
    cliente: TestClient,
) -> None:
    numero, id_solicitud = pausada(cliente)
    resultado = _llegada(cliente, numero, id_solicitud)
    assert resultado["estado_orden"] == "Pausada por Retiro de Vehículo"

    respuesta = cliente.post(f"/api/ordenes/{numero}/reactivacion", headers=ASESOR)

    assert respuesta.json()["estado"] == "Autorizada"


def test_rn_09_compras_solo_ve_trabajos_autorizados(cliente: TestClient) -> None:
    numero, _ = autorizada(cliente, lineas=(1,))

    rechazada = cliente.post(
        f"/api/ordenes/{numero}/solicitudes-de-compra",
        json={"id_trabajo": 2, "refaccion": "Balatas", "cantidad": 1},
        headers=TECNICO,
    )

    assert rechazada.status_code == 409
    assert _pendientes(cliente) == []


def test_rn_10_sigue_en_espera_si_falta_una_refaccion(cliente: TestClient) -> None:
    numero, primera = en_espera(cliente)
    segunda = solicitar(cliente, numero, 1)

    resultado = _llegada(cliente, numero, primera)

    assert resultado["estado_orden"] == "En Espera de Refacción"
    assert _llegada(cliente, numero, segunda)["estado_orden"] == "Autorizada"


def test_rn_11_con_3_dias_habiles_no_hay_alerta(cliente: TestClient, reloj: Mock) -> None:
    en_espera(cliente)
    poner_hora(reloj, AHORA + timedelta(days=3))

    assert revisar_plazos(cliente)["alertas_de_refaccion"] == 0


def test_rn_11_los_fines_de_semana_no_cuentan(cliente: TestClient, reloj: Mock) -> None:
    jueves = datetime(2026, 10, 8, 10, 0, tzinfo=ZONA)
    poner_hora(reloj, jueves)
    en_espera(cliente)
    poner_hora(reloj, jueves + timedelta(days=5))  # martes: solo 3 días hábiles

    assert revisar_plazos(cliente)["alertas_de_refaccion"] == 0


def test_rn_13_sin_firma_no_se_pausa(cliente: TestClient) -> None:
    numero, _ = en_espera(cliente)
    exigir(cliente.post(f"/api/ordenes/{numero}/retiro", headers=ASESOR), 201)

    assert expediente_de(cliente, numero)["estado"] == "En Espera de Refacción"
    assert expediente_de(cliente, numero)["nota_firmada"] is False


def test_rn_13_firmar_sin_registrar_la_salida_responde_409(cliente: TestClient) -> None:
    numero, _ = en_espera(cliente)

    assert cliente.post(f"/api/ordenes/{numero}/retiro/firma", headers=ASESOR).status_code == 409


def test_rn_14_trabajo_de_otro_tecnico_responde_403(cliente: TestClient) -> None:
    numero = asignada(cliente)

    inicio = cliente.post(f"/api/ordenes/{numero}/trabajos/1/inicio", headers=OTRO_TECNICO)

    assert inicio.status_code == 403
    assert inicio.json()["error"] == "TrabajoDeOtroTecnico"


def test_rn_14_completar_el_trabajo_de_otro_tecnico_responde_403(cliente: TestClient) -> None:
    numero = en_reparacion(cliente)

    respuesta = cliente.post(f"/api/ordenes/{numero}/trabajos/1/completado", headers=OTRO_TECNICO)

    assert respuesta.status_code == 403


def test_rn_15_refaccion_pendiente_impide_completar_el_ultimo(cliente: TestClient) -> None:
    numero = en_reparacion(cliente)
    iniciar(cliente, numero, 2)
    completar(cliente, numero, 2)
    solicitar(cliente, numero, 1)

    respuesta = cliente.post(f"/api/ordenes/{numero}/trabajos/1/completado", headers=TECNICO)

    assert respuesta.status_code == 409
    assert "refacciones pendientes" in respuesta.json()["detalle"]


def test_rn_22_saltar_estado_responde_409(cliente: TestClient) -> None:
    numero = recibida(cliente)

    respuesta = cliente.post(f"/api/ordenes/{numero}/retiro", headers=ASESOR)

    assert respuesta.status_code == 409


@pytest.mark.parametrize("sufijo", ["trabajos/9/inicio", "trabajos/9/completado"])
def test_trabajo_inexistente_responde_404(cliente: TestClient, sufijo: str) -> None:
    numero = asignada(cliente)

    respuesta = cliente.post(f"/api/ordenes/{numero}/{sufijo}", headers=TECNICO)

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "TrabajoNoEncontrado"


def test_solicitud_inexistente_responde_404(cliente: TestClient) -> None:
    numero = asignada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/solicitudes-de-compra/9/llegada", headers=COMPRAS
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "SolicitudNoEncontrada"


@pytest.mark.parametrize("id_trabajo", ["abc", "0", "2147483648"])
def test_id_de_trabajo_invalido_responde_422(cliente: TestClient, id_trabajo: str) -> None:
    numero = asignada(cliente)

    respuesta = cliente.post(f"/api/ordenes/{numero}/trabajos/{id_trabajo}/inicio", headers=TECNICO)

    assert respuesta.status_code == 422
    assert respuesta.json()["error"] == "ValorInvalido"


def test_asignar_sin_seleccion_responde_422(cliente: TestClient) -> None:
    numero, _ = autorizada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/asignacion-trabajos",
        json={"ids_trabajos": [], "tecnico": "EMP-002"},
        headers=ASESOR,
    )

    assert respuesta.status_code == 422


def test_asignar_a_otro_tecnico_lo_cambia_de_panel(cliente: TestClient) -> None:
    numero, _ = autorizada(cliente)

    asignar(cliente, numero, (1,), "EMP-003")

    assert panel_de(cliente, TECNICO) == []
    assert [orden["numero_orden"] for orden in panel_de(cliente, OTRO_TECNICO)] == [numero]


# ------------------------------------------------------------------ refacción repetida (H-PIA-26)
def test_ca_062_doble_clic_en_solicitar_refaccion_responde_409(cliente: TestClient) -> None:
    numero = asignada(cliente)
    cuerpo = {"id_trabajo": 1, "refaccion": "Balata", "cantidad": 1}
    url = f"/api/ordenes/{numero}/solicitudes-de-compra"
    exigir(cliente.post(url, json=cuerpo, headers=TECNICO), 201)

    respuesta = exigir(cliente.post(url, json=cuerpo, headers=TECNICO), 409)

    assert "ya está solicitada y Compras la está gestionando" in respuesta["detalle"]
    pendientes = exigir(cliente.get("/api/compras/solicitudes-pendientes", headers=COMPRAS), 200)
    assert [s["numero_orden"] for s in pendientes].count(numero) == 1
