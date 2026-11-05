"""Alertas internas y traducción de eventos a la bitácora (ADR-016)."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application.puertos import AlertaInterna
from application.unidad_de_trabajo import registro_de_bitacora
from domain.compartido.errores import ValorInvalido
from domain.compartido.eventos import EventoDeDominio
from domain.cotizaciones.eventos import CotizacionPresentada
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes.eventos import TrabajosAsignados

AHORA = datetime(2026, 10, 5, 15, 0, tzinfo=UTC)


def test_alerta_exige_destinatario_o_rol() -> None:
    with pytest.raises(ValorInvalido, match="empleado o a un rol"):
        AlertaInterna("Prueba", "Mensaje", AHORA)


def test_alerta_a_todo_un_rol() -> None:
    alerta = AlertaInterna("Prueba", "Mensaje", AHORA, destinatario_rol=RolDeEmpleado.GERENTE)

    assert alerta.destinatario is None
    assert alerta.leida is False


def test_registro_de_un_evento_de_orden_queda_listo_para_json() -> None:
    registro = registro_de_bitacora(TrabajosAsignados(AHORA, "OS-0001", (1, 2), "EMP-002"))

    assert (registro.tipo, registro.agregado, registro.id_agregado) == (
        "TrabajosAsignados",
        "Orden",
        "OS-0001",
    )
    assert registro.datos == {
        "numero_orden": "OS-0001",
        "ids_trabajos": [1, 2],
        "tecnico": "EMP-002",
    }
    assert registro.ocurrido_en == AHORA


def test_registro_de_un_evento_de_cotizacion_usa_su_id() -> None:
    registro = registro_de_bitacora(CotizacionPresentada(AHORA, "COT-0001", "OS-0001"))

    assert (registro.agregado, registro.id_agregado) == ("Cotizacion", "COT-0001")


def test_evento_sin_aggregate_conocido_se_rechaza() -> None:
    with pytest.raises(TypeError, match="EventoDeDominio"):
        registro_de_bitacora(EventoDeDominio(AHORA))
