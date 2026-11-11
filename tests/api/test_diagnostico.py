"""Diagnóstico de punta a punta: criterios CA-013 y CA-032 a CA-036."""
from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import Mock

from fastapi.testclient import TestClient

from tests.api.pasos import (
    ASESOR,
    DIAGNOSTICO,
    GERENTE,
    ID_ASESOR,
    ID_OTRO_TECNICO,
    ID_TECNICO,
    OTRO_TECNICO,
    SISTEMA,
    TECNICO,
    alertas_de,
    autorizada,
    cotizada,
    diagnosticada,
    en_diagnostico,
    en_reparacion,
    exigir,
    expediente_de,
    panel_de,
    recibida,
)
from tests.unit.application.escenarios import AHORA, poner_hora


def test_ca_035_asignar_tecnico_pasa_a_en_diagnostico_y_aparece_en_su_panel(
    cliente: TestClient,
) -> None:
    numero = recibida(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/asignacion-diagnostico",
        json={"tecnico": ID_TECNICO},
        headers=ASESOR,
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {"numero_orden": numero, "estado": "En Diagnóstico"}
    panel = panel_de(cliente, TECNICO)
    assert [orden["numero_orden"] for orden in panel] == [numero]
    assert panel[0]["diagnostico_asignado"] is True
    assert panel_de(cliente, OTRO_TECNICO) == []


def test_ca_035_asignar_a_quien_no_es_tecnico_responde_422(cliente: TestClient) -> None:
    numero = recibida(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/asignacion-diagnostico",
        json={"tecnico": ID_ASESOR},
        headers=ASESOR,
    )

    assert respuesta.status_code == 422
    assert "no es Técnico" in respuesta.json()["detalle"]


def test_ca_035_asignar_a_un_empleado_inexistente_responde_404(cliente: TestClient) -> None:
    numero = recibida(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/asignacion-diagnostico",
        json={"tecnico": "EMP-999"},
        headers=ASESOR,
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["error"] == "EmpleadoNoEncontrado"


def test_ca_032_registra_diagnostico_y_alerta_al_asesor(cliente: TestClient) -> None:
    numero = en_diagnostico(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/diagnostico", json=DIAGNOSTICO, headers=TECNICO
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["tecnico"] == ID_TECNICO
    assert respuesta.json()["registrado_en"].endswith("Z")
    assert expediente_de(cliente, numero)["diagnostico_fallas"] == DIAGNOSTICO["fallas"]
    alerta = alertas_de(cliente, ASESOR)[0]
    assert alerta["tipo"] == "DiagnosticoRegistrado"
    assert "lista para cotizar" in alerta["mensaje"]
    assert alerta["numero_orden"] == numero


def test_ca_032_otro_tecnico_no_registra_el_diagnostico_responde_403(
    cliente: TestClient,
) -> None:
    numero = en_diagnostico(cliente, tecnico=ID_OTRO_TECNICO)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/diagnostico", json=DIAGNOSTICO, headers=TECNICO
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["error"] == "TrabajoDeOtroTecnico"


def test_ca_033_diagnostico_no_cambia_despues_de_cotizar_responde_409(
    cliente: TestClient,
) -> None:
    numero, _ = cotizada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/diagnostico", json=DIAGNOSTICO, headers=TECNICO
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "DiagnosticoNoModificable"


def test_rn_03_mensaje_indica_registrar_falla_adicional(cliente: TestClient) -> None:
    numero, _ = cotizada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/diagnostico", json=DIAGNOSTICO, headers=TECNICO
    )

    assert "falla adicional" in respuesta.json()["detalle"]


def test_ca_034_falla_adicional_se_vincula_y_alerta_al_asesor(cliente: TestClient) -> None:
    numero = en_reparacion(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/fallas-adicionales",
        json={"descripcion": "Fuga de aceite"},
        headers=TECNICO,
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["id_falla"] == 1
    falla = expediente_de(cliente, numero)["fallas_adicionales"][0]
    assert falla["descripcion"] == "Fuga de aceite"
    assert falla["tecnico"] == ID_TECNICO
    alerta = next(
        alerta for alerta in alertas_de(cliente, ASESOR) if alerta["tipo"] == "FallaAdicionalReportada"
    )
    assert "cotización adicional" in alerta["mensaje"]


def test_ca_036_trabajos_asignados_aparecen_pendientes_en_el_panel(cliente: TestClient) -> None:
    numero, _ = autorizada(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/asignacion-trabajos",
        json={"ids_trabajos": [1, 2], "tecnico": ID_OTRO_TECNICO},
        headers=ASESOR,
    )

    assert respuesta.status_code == 200
    panel = panel_de(cliente, OTRO_TECNICO)
    assert [trabajo["id"] for trabajo in panel[0]["trabajos"]] == [1, 2]
    assert {trabajo["estado"] for trabajo in panel[0]["trabajos"]} == {"Pendiente"}


def test_ca_013_panel_ordenado_por_la_fila_de_trabajo(cliente: TestClient, reloj: Mock) -> None:
    primera = en_diagnostico(cliente)
    poner_hora(reloj, AHORA + timedelta(hours=1))
    segunda = en_diagnostico(cliente)

    panel = panel_de(cliente, TECNICO)

    assert [orden["numero_orden"] for orden in panel] == [primera, segunda]


def test_el_panel_es_solo_para_tecnicos(cliente: TestClient) -> None:
    assert cliente.get("/api/tecnicos/me/panel", headers=ASESOR).status_code == 403


def test_falla_adicional_fuera_de_reparacion_responde_409(cliente: TestClient) -> None:
    numero = recibida(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/fallas-adicionales",
        json={"descripcion": "Fuga de aceite"},
        headers=TECNICO,
    )

    assert respuesta.status_code == 409


def test_alertas_solo_del_empleado_y_de_su_rol(cliente: TestClient) -> None:
    numero = en_diagnostico(cliente)
    cliente.post(f"/api/ordenes/{numero}/diagnostico", json=DIAGNOSTICO, headers=TECNICO)

    assert len(alertas_de(cliente, ASESOR)) == 1
    assert alertas_de(cliente, GERENTE) == []
    assert alertas_de(cliente, TECNICO) == []


def test_las_alertas_exigen_token_de_empleado(cliente: TestClient) -> None:
    assert cliente.get("/api/alertas").status_code == 401
    assert cliente.get("/api/alertas", headers=SISTEMA).status_code == 403


def test_ca_053_el_asesor_ve_la_lista_de_tecnicos(cliente: TestClient) -> None:
    tecnicos = exigir(cliente.get("/api/tecnicos", headers=ASESOR), 200)

    assert tecnicos == [
        {"id_empleado": "EMP-002", "nombre": "Carlos Ruiz"},
        {"id_empleado": "EMP-003", "nombre": "Diego Salinas"},
    ]


def test_rn_28_la_lista_no_incluye_otros_puestos(cliente: TestClient) -> None:
    tecnicos = exigir(cliente.get("/api/tecnicos", headers=ASESOR), 200)

    assert {tecnico["id_empleado"] for tecnico in tecnicos}.isdisjoint(
        {"EMP-001", "EMP-004", "EMP-005", "EMP-006"}
    )


def _asignar(cliente: TestClient, numero: str, tecnico: str) -> Any:
    return cliente.post(
        f"/api/ordenes/{numero}/asignacion-diagnostico", json={"tecnico": tecnico}, headers=ASESOR
    )


def test_ca_054_sale_del_panel_del_anterior_y_aparece_en_el_nuevo(cliente: TestClient) -> None:
    numero = en_diagnostico(cliente)

    respuesta = exigir(_asignar(cliente, numero, ID_OTRO_TECNICO), 200)

    assert respuesta["estado"] == "En Diagnóstico"
    assert numero not in [orden["numero_orden"] for orden in panel_de(cliente, TECNICO)]
    assert numero in [orden["numero_orden"] for orden in panel_de(cliente, OTRO_TECNICO)]
    assert expediente_de(cliente, numero)["tecnico_de_diagnostico"] == ID_OTRO_TECNICO


def test_ca_054_con_diagnostico_responde_409_y_no_cambia(cliente: TestClient) -> None:
    numero = diagnosticada(cliente)

    respuesta = exigir(_asignar(cliente, numero, ID_OTRO_TECNICO), 409)

    assert respuesta["error"] == "CorreccionNoPermitida"
    assert respuesta["detalle"] == (
        f"El diagnóstico de la orden {numero} ya está registrado; ya no se puede cambiar el técnico."
    )
    assert expediente_de(cliente, numero)["tecnico_de_diagnostico"] == ID_TECNICO


# ------------------------------------------------------------------ recomendaciones opcionales (H-PIA-28)
def test_el_diagnostico_sin_recomendaciones_se_registra(cliente: TestClient) -> None:
    numero = en_diagnostico(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/diagnostico", json={"fallas": "Balatas gastadas"}, headers=TECNICO
    )

    assert respuesta.status_code == 201
    assert expediente_de(cliente, numero)["diagnostico_recomendaciones"] == ""
