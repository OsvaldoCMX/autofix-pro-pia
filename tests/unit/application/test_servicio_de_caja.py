"""ServicioDeCaja (US-014, US-022)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from application.comandos import RegistrarCargoACredito, RegistrarPago
from domain.compartido.errores import (
    OrdenNoEncontrada,
    PagoNoPermitido,
    TransicionDeEstadoNoPermitida,
    ValorInvalido,
)
from domain.ordenes.eventos import CargoACreditoRegistrado, PagoRegistrado
from domain.ordenes.valores import FormaDePago
from tests.unit.application.escenarios import (
    AHORA,
    TOTAL_DE_DOS_TRABAJOS,
    Taller,
    en_reparacion,
    lista,
    pagada,
)


@pytest.mark.parametrize("forma", list(FormaDePago))
def test_ca_026_pago_pasa_a_pagada(taller: Taller, forma: FormaDePago) -> None:
    numero = lista(taller)

    resultado = taller.caja.registrar_pago(RegistrarPago(numero, TOTAL_DE_DOS_TRABAJOS, forma))

    assert resultado.estado == "Pagada"
    assert resultado.monto == "3000.00"
    assert resultado.forma == forma.value
    assert resultado.registrado_en == AHORA
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [PagoRegistrado]


def test_rn_16_monto_distinto_se_rechaza(taller: Taller) -> None:
    numero = lista(taller)

    with pytest.raises(PagoNoPermitido, match="total autorizado"):
        taller.caja.registrar_pago(RegistrarPago(numero, Decimal("2999.99"), FormaDePago.EFECTIVO))

    assert taller.datos.ordenes[numero].pago is None


def test_rn_16_monto_negativo_es_invalido(taller: Taller) -> None:
    numero = lista(taller)

    with pytest.raises(ValorInvalido, match="negativo"):
        taller.caja.registrar_pago(RegistrarPago(numero, Decimal("-1.00"), FormaDePago.EFECTIVO))


def test_rn_16_flotilla_no_paga_de_contado(taller: Taller) -> None:
    numero = lista(taller, flotilla=True)

    with pytest.raises(PagoNoPermitido, match="cargo a crédito"):
        taller.caja.registrar_pago(
            RegistrarPago(numero, TOTAL_DE_DOS_TRABAJOS, FormaDePago.EFECTIVO)
        )


def test_rn_16_particular_no_usa_cargo_a_credito(taller: Taller) -> None:
    numero = lista(taller)

    with pytest.raises(PagoNoPermitido, match="flotilla"):
        taller.caja.registrar_cargo_a_credito(RegistrarCargoACredito(numero))


def test_rn_16_despues_del_pago_no_se_cobra_otra_vez(taller: Taller) -> None:
    numero = pagada(taller)

    with pytest.raises(TransicionDeEstadoNoPermitida):
        taller.caja.registrar_pago(
            RegistrarPago(numero, TOTAL_DE_DOS_TRABAJOS, FormaDePago.EFECTIVO)
        )


def test_rn_22_pago_antes_de_lista_para_entrega_se_rechaza(taller: Taller) -> None:
    numero = en_reparacion(taller)

    with pytest.raises(TransicionDeEstadoNoPermitida):
        taller.caja.registrar_pago(
            RegistrarPago(numero, TOTAL_DE_DOS_TRABAJOS, FormaDePago.EFECTIVO)
        )


def test_ca_039_cargo_sin_vencimiento_todavia(taller: Taller) -> None:
    numero = lista(taller, flotilla=True)

    resultado = taller.caja.registrar_cargo_a_credito(RegistrarCargoACredito(numero))

    cargo = taller.datos.ordenes[numero].cargo_a_credito
    assert resultado.estado == "Por Cobrar (Crédito)"
    assert resultado.monto == "3000.00"
    assert resultado.registrado_en == AHORA
    assert cargo.fecha_vencimiento is None
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [CargoACreditoRegistrado]


def test_orden_inexistente_no_recibe_pago(taller: Taller) -> None:
    with pytest.raises(OrdenNoEncontrada):
        taller.caja.registrar_pago(
            RegistrarPago("OS-9999", TOTAL_DE_DOS_TRABAJOS, FormaDePago.EFECTIVO)
        )
