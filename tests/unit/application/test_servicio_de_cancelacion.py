"""ServicioDeCancelacion (US-025)."""
from __future__ import annotations

import pytest

from application.comandos import CancelarOrden
from domain.compartido.errores import CancelacionNoPermitida, OrdenNoEncontrada, ValorInvalido
from domain.ordenes.eventos import OrdenCancelada
from tests.unit.application.escenarios import (
    AHORA,
    ASESOR,
    Taller,
    cotizada,
    en_diagnostico,
    recibida,
)


def test_ca_044_cancela_orden_recibida_con_motivo(taller: Taller) -> None:
    numero = recibida(taller)
    taller.publicador.publicar.reset_mock()

    resultado = taller.cancelacion.cancelar(CancelarOrden(numero, "El cliente desistió", ASESOR))

    orden = taller.datos.ordenes[numero]
    assert resultado.estado == "Cancelada"
    assert orden.cancelacion.motivo == "El cliente desistió"
    assert orden.cancelacion.registrada_en == AHORA
    assert orden.fecha_ingreso_a_fila is None
    assert orden.pago is None
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [OrdenCancelada]


def test_ca_044_cancela_orden_en_diagnostico(taller: Taller) -> None:
    numero = en_diagnostico(taller)

    resultado = taller.cancelacion.cancelar(CancelarOrden(numero, "Ya no lo requiere", ASESOR))

    assert resultado.estado == "Cancelada"


def test_ca_045_no_cancela_orden_cotizada(taller: Taller) -> None:
    numero, _ = cotizada(taller)

    with pytest.raises(CancelacionNoPermitida, match="rechazo total"):
        taller.cancelacion.cancelar(CancelarOrden(numero, "El cliente desistió", ASESOR))

    assert taller.datos.ordenes[numero].estado.value == "Cotizada"


def test_rn_19_cancelacion_sin_motivo_es_invalida(taller: Taller) -> None:
    numero = recibida(taller)

    with pytest.raises(ValorInvalido, match="motivo"):
        taller.cancelacion.cancelar(CancelarOrden(numero, "   ", ASESOR))

    assert taller.datos.ordenes[numero].estado.value == "Recibida"


def test_orden_inexistente_no_se_cancela(taller: Taller) -> None:
    with pytest.raises(OrdenNoEncontrada):
        taller.cancelacion.cancelar(CancelarOrden("OS-9999", "Motivo", ASESOR))
