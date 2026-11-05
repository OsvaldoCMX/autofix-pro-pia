"""ServicioDeEntrega (US-024)."""
from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from application.comandos import EntregarSinReparacion, RegistrarEntrega
from domain.compartido.errores import (
    EntregaNoPermitida,
    OrdenNoEncontrada,
    TransicionDeEstadoNoPermitida,
)
from domain.ordenes.eventos import VehiculoEntregado
from tests.unit.application.escenarios import (
    AHORA,
    Taller,
    autorizada,
    cotizada,
    decidir,
    lista,
    pagada,
    poner_hora,
    por_cobrar,
)


def test_ca_041_entrega_orden_pagada(taller: Taller) -> None:
    numero = pagada(taller)

    resultado = taller.entrega.entregar(RegistrarEntrega(numero))

    assert resultado.estado == "Cerrada"
    assert resultado.fecha_entrega == AHORA
    assert resultado.fecha_vencimiento_credito is None
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [VehiculoEntregado]


def test_ca_041_credito_fija_vencimiento(taller: Taller) -> None:
    numero = por_cobrar(taller)

    resultado = taller.entrega.entregar(RegistrarEntrega(numero))

    assert resultado.estado == "Cerrada"
    assert resultado.fecha_vencimiento_credito == date(2026, 10, 20)


def test_rn_17_vencimiento_usa_la_fecha_del_taller(taller: Taller) -> None:
    numero = por_cobrar(taller)
    # 19:00 del 5 de octubre en Monterrey: en UTC ya es 6 de octubre.
    poner_hora(taller.reloj, datetime(2026, 10, 6, 1, 0, tzinfo=UTC))

    resultado = taller.entrega.entregar(RegistrarEntrega(numero))

    assert resultado.fecha_vencimiento_credito == date(2026, 10, 20)
    assert resultado.fecha_entrega == datetime(2026, 10, 6, 1, 0, tzinfo=UTC)


def test_ca_042_sin_pago_se_rechaza(taller: Taller) -> None:
    numero = lista(taller)

    with pytest.raises(EntregaNoPermitida, match="pago o el cargo a crédito"):
        taller.entrega.entregar(RegistrarEntrega(numero))

    assert taller.datos.ordenes[numero].fecha_entrega is None


def test_ca_042_orden_autorizada_no_se_entrega(taller: Taller) -> None:
    numero, _ = autorizada(taller)

    with pytest.raises(EntregaNoPermitida):
        taller.entrega.entregar(RegistrarEntrega(numero))


def test_ca_043_entrega_sin_reparacion(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller)
    decidir(taller, id_cotizacion, ())

    resultado = taller.entrega.entregar_sin_reparacion(EntregarSinReparacion(numero))

    orden = taller.datos.ordenes[numero]
    assert resultado.estado == "Cerrada sin Reparación"
    assert resultado.fecha_entrega == AHORA
    assert orden.pago is None
    assert orden.cargo_a_credito is None
    evento = taller.publicador.publicar.call_args.args[0][0]
    assert evento.sin_reparacion is True


def test_ca_043_sin_rechazo_total_no_se_entrega_sin_reparacion(taller: Taller) -> None:
    numero, _ = cotizada(taller)

    with pytest.raises(EntregaNoPermitida):
        taller.entrega.entregar_sin_reparacion(EntregarSinReparacion(numero))


def test_rn_18_rechazo_total_no_usa_entrega_normal(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller)
    decidir(taller, id_cotizacion, ())

    with pytest.raises(TransicionDeEstadoNoPermitida):
        taller.entrega.entregar(RegistrarEntrega(numero))

    assert taller.datos.ordenes[numero].estado.value == "Cotizada"


def test_orden_inexistente_no_se_entrega(taller: Taller) -> None:
    with pytest.raises(OrdenNoEncontrada):
        taller.entrega.entregar(RegistrarEntrega("OS-9999"))
