"""Specifications E1 y E8 con casos verdaderos y falsos (modelo-de-dominio.md §4)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from domain.compartido.valores import Dinero, NumeroOrden
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.especificaciones import (
    EsCotizacionInicial,
    FuePresentada,
    MasDeHorasDesdeElUltimoContacto,
    PendienteDeAutorizacion,
    RequiereAprobacionGerencial,
    RequiereRecontacto,
    TotalMayorAlUmbral,
)
from domain.cotizaciones.linea_de_cotizacion import LineaDeCotizacion
from domain.cotizaciones.valores import (
    Autorizante,
    RolDeAutorizante,
    TipoCotizacion,
    VersionCotizacion,
)

INICIO = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
UMBRAL = "15000.00"


def _cotizacion(
    total: str = "1000.00", tipo: TipoCotizacion = TipoCotizacion.INICIAL, version: int = 1
) -> Cotizacion:
    linea = LineaDeCotizacion(1, "Cambio de balatas", Dinero(Decimal(total)))
    return Cotizacion.generar(
        "COT-1", NumeroOrden("OS-1"), tipo, VersionCotizacion(version), [linea], INICIO
    )


def _presentada() -> Cotizacion:
    cotizacion = _cotizacion()
    cotizacion.marcar_presentada(INICIO)
    return cotizacion


def test_ca_007_e1_inicial_mayor_al_umbral() -> None:
    assert RequiereAprobacionGerencial().es_satisfecha_por(_cotizacion("15000.01"))


def test_ca_005_e1_inicial_igual_al_umbral_no_requiere() -> None:
    assert not RequiereAprobacionGerencial().es_satisfecha_por(_cotizacion(UMBRAL))


def test_ca_016_e1_adicional_nunca_requiere() -> None:
    adicional = _cotizacion("90000.00", TipoCotizacion.ADICIONAL, 2)

    assert not RequiereAprobacionGerencial().es_satisfecha_por(adicional)


def test_rn_04_e1_cada_pieza_se_evalua_por_separado() -> None:
    adicional = _cotizacion("90000.00", TipoCotizacion.ADICIONAL, 2)
    umbral = TotalMayorAlUmbral(Dinero(Decimal(UMBRAL)))

    assert EsCotizacionInicial().es_satisfecha_por(_cotizacion())
    assert not EsCotizacionInicial().es_satisfecha_por(adicional)
    assert umbral.es_satisfecha_por(adicional)
    assert not umbral.es_satisfecha_por(_cotizacion(UMBRAL))


def test_ca_040_e8_mas_de_48_horas_desde_presentacion() -> None:
    revision = INICIO + timedelta(hours=48, seconds=1)

    assert RequiereRecontacto(revision).es_satisfecha_por(_presentada())


def test_ca_040_e8_exactamente_48_horas_aun_no_vence() -> None:
    assert not RequiereRecontacto(INICIO + timedelta(hours=48)).es_satisfecha_por(_presentada())


def test_ca_040_e8_cuenta_desde_el_ultimo_recontacto() -> None:
    cotizacion = _presentada()
    cotizacion.registrar_recontacto("EMP-001", INICIO + timedelta(hours=49))

    assert not RequiereRecontacto(INICIO + timedelta(hours=60)).es_satisfecha_por(cotizacion)
    assert RequiereRecontacto(INICIO + timedelta(hours=98)).es_satisfecha_por(cotizacion)


@pytest.mark.parametrize(
    ("pendiente", "presentada", "vencida", "esperado"),
    [
        (True, True, True, True),
        (True, True, False, False),
        (True, False, True, False),
        (False, False, False, False),
    ],
)
def test_rn_12_e8_tabla_de_verdad(
    pendiente: bool, presentada: bool, vencida: bool, esperado: bool
) -> None:
    cotizacion = _cotizacion("20000.00") if not pendiente else _cotizacion()
    if presentada:
        cotizacion.marcar_presentada(INICIO)
    horas = 49 if vencida else 1
    revision = INICIO + timedelta(hours=horas)

    assert RequiereRecontacto(revision).es_satisfecha_por(cotizacion) is esperado


def test_rn_12_e8_autorizada_ya_no_requiere_recontacto() -> None:
    cotizacion = _presentada()
    cotizacion.registrar_decision({1}, Autorizante("Luis", RolDeAutorizante.CLIENTE), INICIO)

    assert not RequiereRecontacto(INICIO + timedelta(hours=99)).es_satisfecha_por(cotizacion)


def test_rn_12_e8_cada_pieza_se_evalua_por_separado() -> None:
    sin_presentar = _cotizacion()
    con_gerente = _cotizacion("20000.00")
    vencido = MasDeHorasDesdeElUltimoContacto(48, INICIO + timedelta(hours=49))

    assert PendienteDeAutorizacion().es_satisfecha_por(sin_presentar)
    assert not PendienteDeAutorizacion().es_satisfecha_por(con_gerente)
    assert FuePresentada().es_satisfecha_por(_presentada())
    assert not FuePresentada().es_satisfecha_por(sin_presentar)
    assert vencido.es_satisfecha_por(_presentada())
    assert not vencido.es_satisfecha_por(sin_presentar)
