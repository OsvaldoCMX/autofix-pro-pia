"""Tablas de la Orden, el Trabajo y la Solicitud (modelo-de-dominio.md §5.1 y §5.3)."""
from __future__ import annotations

from itertools import product

import pytest

from domain.compartido.errores import TransicionDeEstadoNoPermitida
from domain.ordenes.estados import (
    MAQUINA_DE_ORDEN,
    MAQUINA_DE_SOLICITUD,
    MAQUINA_DE_TRABAJO,
    EstadoOrden,
    EstadoSolicitud,
    EstadoTrabajo,
)
from domain.ordenes.valores import FormaDePago, NivelDeCombustible
from tests.unit.domain.apoyo_esquema import valores_del_check

_O = EstadoOrden
_T = EstadoTrabajo
_S = EstadoSolicitud

ORDEN_PERMITIDAS = {
    (_O.RECIBIDA, _O.EN_DIAGNOSTICO),
    (_O.RECIBIDA, _O.CANCELADA),
    (_O.EN_DIAGNOSTICO, _O.COTIZADA),
    (_O.EN_DIAGNOSTICO, _O.CANCELADA),
    (_O.COTIZADA, _O.AUTORIZADA),
    (_O.COTIZADA, _O.CERRADA_SIN_REPARACION),
    (_O.AUTORIZADA, _O.EN_REPARACION),
    (_O.AUTORIZADA, _O.EN_ESPERA_DE_REFACCION),
    (_O.EN_REPARACION, _O.EN_ESPERA_DE_REFACCION),
    (_O.EN_REPARACION, _O.LISTA_PARA_ENTREGA),
    (_O.EN_ESPERA_DE_REFACCION, _O.AUTORIZADA),
    (_O.EN_ESPERA_DE_REFACCION, _O.EN_REPARACION),
    (_O.EN_ESPERA_DE_REFACCION, _O.PAUSADA_POR_RETIRO_DE_VEHICULO),
    (_O.PAUSADA_POR_RETIRO_DE_VEHICULO, _O.EN_ESPERA_DE_REFACCION),
    (_O.PAUSADA_POR_RETIRO_DE_VEHICULO, _O.AUTORIZADA),
    (_O.PAUSADA_POR_RETIRO_DE_VEHICULO, _O.EN_REPARACION),
    (_O.LISTA_PARA_ENTREGA, _O.PAGADA),
    (_O.LISTA_PARA_ENTREGA, _O.POR_COBRAR_CREDITO),
    (_O.PAGADA, _O.CERRADA),
    (_O.POR_COBRAR_CREDITO, _O.CERRADA),
}
TRABAJO_PERMITIDAS = {(_T.PENDIENTE, _T.EN_PROGRESO), (_T.EN_PROGRESO, _T.COMPLETADO)}
SOLICITUD_PERMITIDAS = {(_S.SOLICITADA, _S.DISPONIBLE)}


@pytest.mark.parametrize(("actual", "nuevo"), list(product(_O, repeat=2)))
def test_rn_22_orden_recorre_todas_las_parejas(actual: EstadoOrden, nuevo: EstadoOrden) -> None:
    assert MAQUINA_DE_ORDEN.permite(actual, nuevo) is ((actual, nuevo) in ORDEN_PERMITIDAS)


@pytest.mark.parametrize(("actual", "nuevo"), list(product(_T, repeat=2)))
def test_rn_22_trabajo_recorre_todas_las_parejas(
    actual: EstadoTrabajo, nuevo: EstadoTrabajo
) -> None:
    assert MAQUINA_DE_TRABAJO.permite(actual, nuevo) is ((actual, nuevo) in TRABAJO_PERMITIDAS)


@pytest.mark.parametrize(("actual", "nuevo"), list(product(_S, repeat=2)))
def test_rn_22_solicitud_recorre_todas_las_parejas(
    actual: EstadoSolicitud, nuevo: EstadoSolicitud
) -> None:
    assert MAQUINA_DE_SOLICITUD.permite(actual, nuevo) is ((actual, nuevo) in SOLICITUD_PERMITIDAS)


def test_rn_22_rechaza_saltar_de_recibida_a_autorizada() -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida, match="«Recibida» a «Autorizada»"):
        MAQUINA_DE_ORDEN.validar(_O.RECIBIDA, _O.AUTORIZADA)


@pytest.mark.parametrize("final", [_O.CERRADA, _O.CERRADA_SIN_REPARACION, _O.CANCELADA])
def test_rn_22_estados_finales_no_tienen_salida(final: EstadoOrden) -> None:
    assert MAQUINA_DE_ORDEN.es_final(final)
    assert not any(MAQUINA_DE_ORDEN.permite(final, destino) for destino in _O)


def test_rn_22_estados_finales_de_trabajo_y_solicitud() -> None:
    assert MAQUINA_DE_TRABAJO.es_final(_T.COMPLETADO)
    assert MAQUINA_DE_TRABAJO.es_final(_T.NO_AUTORIZADO)
    assert MAQUINA_DE_SOLICITUD.es_final(_S.DISPONIBLE)


def test_estados_de_orden_son_los_del_glosario_y_la_base() -> None:
    glosario = {
        "Recibida",
        "En Diagnóstico",
        "Cotizada",
        "Autorizada",
        "En Reparación",
        "En Espera de Refacción",
        "Pausada por Retiro de Vehículo",
        "Lista para Entrega",
        "Pagada",
        "Por Cobrar (Crédito)",
        "Cerrada",
        "Cerrada sin Reparación",
        "Cancelada",
    }
    assert {estado.value for estado in _O} == glosario
    assert glosario == valores_del_check("ordenes", "estado")


def test_estados_de_trabajo_y_solicitud_son_los_del_glosario_y_la_base() -> None:
    trabajo = {"Pendiente", "En Progreso", "Completado", "No Autorizado"}
    assert {estado.value for estado in _T} == trabajo
    assert trabajo == valores_del_check("trabajos", "estado")
    assert {estado.value for estado in _S} == {"Solicitada", "Disponible"}
    assert {estado.value for estado in _S} == valores_del_check("solicitudes_de_compra", "estado")


def test_catalogos_de_la_orden_coinciden_con_la_base() -> None:
    assert {nivel.value for nivel in NivelDeCombustible} == valores_del_check(
        "ordenes", "nivel_combustible"
    )
    assert {forma.value for forma in FormaDePago} == valores_del_check("ordenes", "pago_forma")
