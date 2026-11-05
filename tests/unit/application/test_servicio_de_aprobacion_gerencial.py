"""ServicioDeAprobacionGerencial (US-005) y el ajuste de la cotización (CA-009)."""
from __future__ import annotations

import pytest

from application.comandos import AjustarCotizacion, PresentarCotizacion, RevisarCotizacion
from domain.compartido.errores import OperacionDeCotizacionNoPermitida, ValorInvalido
from domain.cotizaciones.eventos import (
    CotizacionAprobadaPorGerente,
    CotizacionRechazadaPorGerente,
)
from tests.unit.application.escenarios import AHORA, Taller, cotizada, trabajos

ALTO_MONTO = ("20000.00",)


def test_ca_008_aprueba_y_guarda_fecha(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=ALTO_MONTO)

    resultado = taller.aprobacion.revisar(RevisarCotizacion(id_cotizacion, aprobada=True))

    assert resultado.estado == "Pendiente de Autorización del Cliente"
    assert resultado.fecha_aprobacion_gerencial == AHORA
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [CotizacionAprobadaPorGerente]


def test_ca_008_ya_aprobada_se_puede_presentar(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=ALTO_MONTO)
    taller.aprobacion.revisar(RevisarCotizacion(id_cotizacion, aprobada=True))

    resultado = taller.cotizacion.presentar(PresentarCotizacion(id_cotizacion))

    assert resultado.fecha_presentacion == AHORA


def test_ca_008_aprobar_dos_veces_se_rechaza(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=ALTO_MONTO)
    taller.aprobacion.revisar(RevisarCotizacion(id_cotizacion, aprobada=True))

    with pytest.raises(OperacionDeCotizacionNoPermitida):
        taller.aprobacion.revisar(RevisarCotizacion(id_cotizacion, aprobada=True))


def test_ca_009_rechaza_con_observaciones(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=ALTO_MONTO)

    resultado = taller.aprobacion.revisar(
        RevisarCotizacion(id_cotizacion, aprobada=False, observaciones="Reducir mano de obra")
    )

    assert resultado.estado == "Requiere Ajuste"
    cotizacion = taller.datos.cotizaciones[id_cotizacion]
    assert cotizacion.observaciones_del_gerente == "Reducir mano de obra"
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [CotizacionRechazadaPorGerente]


def test_rn_05_rechazo_sin_observaciones_es_invalido(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=ALTO_MONTO)

    with pytest.raises(ValorInvalido, match="observaciones"):
        taller.aprobacion.revisar(RevisarCotizacion(id_cotizacion, aprobada=False))

    assert taller.datos.cotizaciones[id_cotizacion].estado.value == (
        "Pendiente de Aprobación Gerencial"
    )


def test_ca_009_ajusta_lineas_sin_volver_a_revision(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=ALTO_MONTO)
    taller.aprobacion.revisar(
        RevisarCotizacion(id_cotizacion, aprobada=False, observaciones="Reducir")
    )

    resultado = taller.cotizacion.ajustar(
        AjustarCotizacion(id_cotizacion, trabajos("16000.00"))
    )

    assert resultado.estado == "Pendiente de Autorización del Cliente"
    assert resultado.total == "16000.00"
