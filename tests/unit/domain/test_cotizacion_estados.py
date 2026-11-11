"""Tabla de estados de la Cotización (modelo-de-dominio.md §5.2 y Glosario §2)."""
from __future__ import annotations

from itertools import product

import pytest

from domain.cotizaciones.estados import MAQUINA_DE_COTIZACION, EstadoCotizacion
from tests.unit.domain.apoyo_esquema import valores_del_check

_E = EstadoCotizacion

PERMITIDAS = {
    (_E.PENDIENTE_DE_APROBACION_GERENCIAL, _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE),
    (_E.PENDIENTE_DE_APROBACION_GERENCIAL, _E.REQUIERE_AJUSTE),
    (_E.REQUIERE_AJUSTE, _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE),
    # H-PIA-30: un ajuste que sube el total rechazado regresa al Gerente.
    (_E.REQUIERE_AJUSTE, _E.PENDIENTE_DE_APROBACION_GERENCIAL),
    # v3.1 (H-PIA-21): una corrección que vuelve a superar $15,000 regresa al Gerente.
    (_E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE, _E.PENDIENTE_DE_APROBACION_GERENCIAL),
    (_E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE, _E.AUTORIZADA),
    (_E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE, _E.AUTORIZADA_PARCIALMENTE),
    (_E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE, _E.RECHAZADA),
}


@pytest.mark.parametrize(("actual", "nuevo"), list(product(_E, repeat=2)))
def test_rn_22_cotizacion_recorre_todas_las_parejas(
    actual: EstadoCotizacion, nuevo: EstadoCotizacion
) -> None:
    assert MAQUINA_DE_COTIZACION.permite(actual, nuevo) is ((actual, nuevo) in PERMITIDAS)


@pytest.mark.parametrize("final", [_E.AUTORIZADA, _E.AUTORIZADA_PARCIALMENTE, _E.RECHAZADA])
def test_rn_22_estados_finales_de_la_cotizacion(final: EstadoCotizacion) -> None:
    assert MAQUINA_DE_COTIZACION.es_final(final)


def test_estados_de_cotizacion_son_los_del_glosario_y_la_base() -> None:
    assert {estado.value for estado in _E} == {
        "Pendiente de Aprobación Gerencial",
        "Requiere Ajuste",
        "Pendiente de Autorización del Cliente",
        "Autorizada",
        "Autorizada Parcialmente",
        "Rechazada",
    }
    assert {estado.value for estado in _E} == valores_del_check("cotizaciones", "estado")
