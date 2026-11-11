"""Corrección de una cotización antes de la decisión del cliente (H-PIA-21, ADR-018)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from domain.compartido.errores import (
    CotizacionSinTrabajos,
    OperacionDeCotizacionNoPermitida,
    ValorInvalido,
)
from domain.compartido.valores import Dinero, NumeroOrden
from domain.cotizaciones import eventos as ev
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.especificaciones import RequiereRecontacto
from domain.cotizaciones.estados import EstadoCotizacion
from domain.cotizaciones.linea_de_cotizacion import LineaDeCotizacion
from domain.cotizaciones.valores import (
    Autorizante,
    RolDeAutorizante,
    TipoCotizacion,
    VersionCotizacion,
)

_E = EstadoCotizacion
INICIO = datetime(2026, 11, 9, 9, 0, tzinfo=UTC)
NUMERO = NumeroOrden("OS-1")
ASESOR = "EMP-001"


def _linea(monto: str, numero: int = 1) -> LineaDeCotizacion:
    return LineaDeCotizacion(numero, f"Trabajo {numero}", Dinero(Decimal(monto)))


def _inicial(monto: str) -> Cotizacion:
    cotizacion = Cotizacion.generar(
        "COT-1", NUMERO, TipoCotizacion.INICIAL, VersionCotizacion(1), [_linea(monto)], INICIO
    )
    cotizacion.extraer_eventos()
    return cotizacion


def _adicional(monto: str) -> Cotizacion:
    cotizacion = Cotizacion.generar(
        "COT-2", NUMERO, TipoCotizacion.ADICIONAL, VersionCotizacion(2), [_linea(monto)], INICIO
    )
    cotizacion.extraer_eventos()
    return cotizacion


def _horas(horas: int) -> datetime:
    return INICIO + timedelta(hours=horas)


def _corregir(cotizacion: Cotizacion, monto: str, horas: int = 5, motivo: str = "Importe mal"):
    return cotizacion.corregir([_linea(monto)], motivo, ASESOR, _horas(horas))


def _eventos(cotizacion: Cotizacion) -> list[type]:
    return [type(evento) for evento in cotizacion.extraer_eventos()]


def test_ca_047_corrige_conserva_numero_version_y_queda_sin_presentar() -> None:
    cotizacion = _inicial("3000.00")
    cotizacion.marcar_presentada(_horas(1))
    cotizacion.extraer_eventos()

    _corregir(cotizacion, "2500.00")

    assert (cotizacion.id, str(cotizacion.version)) == ("COT-1", "v.1")
    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert cotizacion.total == Dinero(Decimal("2500.00"))
    assert cotizacion.fecha_presentacion is None
    assert _eventos(cotizacion) == [ev.CotizacionCorregida]


def test_ca_047_corregida_se_puede_presentar_otra_vez() -> None:
    cotizacion = _inicial("3000.00")
    cotizacion.marcar_presentada(_horas(1))
    _corregir(cotizacion, "2500.00")

    cotizacion.marcar_presentada(_horas(6))

    assert cotizacion.fecha_presentacion == _horas(6)


def test_rn_25_guarda_historial_con_totales_y_fechas_anteriores() -> None:
    cotizacion = _inicial("3000.00")
    cotizacion.marcar_presentada(_horas(1))

    correccion = _corregir(cotizacion, "2500.00", motivo="  Mano de obra mal capturada  ")

    assert cotizacion.correcciones == (correccion,)
    assert correccion.asesor == ASESOR
    assert correccion.registrada_en == _horas(5)
    assert correccion.motivo == "Mano de obra mal capturada"
    assert correccion.total_anterior == Dinero(Decimal("3000.00"))
    assert correccion.total_nuevo == Dinero(Decimal("2500.00"))
    assert correccion.estado_anterior is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert correccion.estado_nuevo is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert correccion.fecha_presentacion_anterior == _horas(1)
    assert correccion.fecha_aprobacion_gerencial_anterior is None


def test_ca_048_correccion_arriba_de_15000_regresa_al_gerente_y_borra_aprobacion() -> None:
    cotizacion = _inicial("20000.00")
    cotizacion.aprobar_por_gerente(_horas(1))
    cotizacion.marcar_presentada(_horas(2))
    cotizacion.extraer_eventos()

    correccion = _corregir(cotizacion, "21000.00")

    assert cotizacion.estado is _E.PENDIENTE_DE_APROBACION_GERENCIAL
    assert cotizacion.fecha_aprobacion_gerencial is None
    assert correccion.fecha_aprobacion_gerencial_anterior == _horas(1)
    assert _eventos(cotizacion) == [ev.CotizacionCorregida, ev.AprobacionGerencialRequerida]
    with pytest.raises(OperacionDeCotizacionNoPermitida):
        cotizacion.marcar_presentada(_horas(6))


def test_ca_048_ajustada_que_se_corrige_arriba_de_15000_regresa_al_gerente() -> None:
    """RN-05 solo protege el ajuste que pidió el Gerente; la corrección cambia el monto."""
    cotizacion = _inicial("20000.00")
    cotizacion.rechazar_por_gerente("Revise la mano de obra", _horas(1))
    cotizacion.ajustar([_linea("18000.00")], _horas(2))
    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE

    _corregir(cotizacion, "18500.00")

    assert cotizacion.estado is _E.PENDIENTE_DE_APROBACION_GERENCIAL
    assert cotizacion.observaciones_del_gerente == "Revise la mano de obra"


def test_rn_26_corregir_vuelve_a_evaluar_e1_y_conserva_aprobacion_si_baja() -> None:
    cotizacion = _inicial("20000.00")
    cotizacion.aprobar_por_gerente(_horas(1))

    _corregir(cotizacion, "14000.00")

    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert cotizacion.fecha_aprobacion_gerencial == _horas(1)


def test_ca_049_en_revision_sigue_arriba_y_no_cambia_de_estado() -> None:
    cotizacion = _inicial("20000.00")

    correccion = _corregir(cotizacion, "25000.00")

    assert cotizacion.estado is _E.PENDIENTE_DE_APROBACION_GERENCIAL
    assert correccion.estado_anterior is correccion.estado_nuevo
    assert cotizacion.total == Dinero(Decimal("25000.00"))
    assert _eventos(cotizacion) == [ev.CotizacionCorregida]


def test_ca_049_en_revision_baja_de_15000_pasa_al_cliente() -> None:
    cotizacion = _inicial("20000.00")

    _corregir(cotizacion, "15000.00")

    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert cotizacion.fecha_presentacion is None


def test_rn_25_adicional_se_corrige_y_sigue_con_el_cliente() -> None:
    cotizacion = _adicional("30000.00")

    _corregir(cotizacion, "45000.00")

    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE


def test_ca_050_no_se_corrige_en_requiere_ajuste() -> None:
    cotizacion = _inicial("20000.00")
    cotizacion.rechazar_por_gerente("Revise la mano de obra", _horas(1))

    with pytest.raises(OperacionDeCotizacionNoPermitida, match="guarde la cotización ajustada"):
        _corregir(cotizacion, "18000.00")

    assert cotizacion.correcciones == ()


@pytest.mark.parametrize("autorizadas", [(1,), ()])
def test_ca_050_no_se_corrige_ya_decidida(autorizadas: tuple[int, ...]) -> None:
    cotizacion = _inicial("3000.00")
    cotizacion.registrar_decision(
        autorizadas, Autorizante("Luis Peña", RolDeAutorizante.CLIENTE), _horas(1)
    )

    with pytest.raises(OperacionDeCotizacionNoPermitida, match="cotización adicional"):
        _corregir(cotizacion, "2000.00")


@pytest.mark.parametrize("motivo", ["", "   "])
def test_ca_050_motivo_obligatorio(motivo: str) -> None:
    cotizacion = _inicial("3000.00")

    with pytest.raises(ValorInvalido, match="motivo"):
        _corregir(cotizacion, "2500.00", motivo=motivo)

    assert cotizacion.total == Dinero(Decimal("3000.00"))


def test_rn_25_sin_trabajos_no_cambia_nada() -> None:
    cotizacion = _inicial("20000.00")

    with pytest.raises(CotizacionSinTrabajos):
        cotizacion.corregir([], "Sin trabajos", ASESOR, _horas(5))

    assert cotizacion.estado is _E.PENDIENTE_DE_APROBACION_GERENCIAL
    assert cotizacion.correcciones == ()


def test_ca_051_e8_ignora_recontactos_anteriores_a_la_nueva_presentacion() -> None:
    cotizacion = _inicial("3000.00")
    cotizacion.marcar_presentada(_horas(0))
    cotizacion.registrar_recontacto(ASESOR, _horas(50))
    _corregir(cotizacion, "2500.00", horas=60)

    assert cotizacion.ultimo_contacto is None
    assert not RequiereRecontacto(_horas(200)).es_satisfecha_por(cotizacion)

    cotizacion.marcar_presentada(_horas(70))

    assert len(cotizacion.recontactos) == 1
    assert cotizacion.ultimo_contacto == _horas(70)
    assert not RequiereRecontacto(_horas(118)).es_satisfecha_por(cotizacion)
    assert RequiereRecontacto(_horas(119)).es_satisfecha_por(cotizacion)


def test_ca_051_cuenta_los_recontactos_posteriores_a_la_nueva_presentacion() -> None:
    cotizacion = _inicial("3000.00")
    cotizacion.marcar_presentada(_horas(0))
    _corregir(cotizacion, "2500.00", horas=1)
    cotizacion.marcar_presentada(_horas(2))
    cotizacion.registrar_recontacto(ASESOR, _horas(60))

    assert cotizacion.ultimo_contacto == _horas(60)


# ------------------------------------------------------------------ trabajos de $0.00 (RN-32)
def test_ca_060_no_se_genera_con_un_trabajo_de_0() -> None:
    mensaje = "^El trabajo 2 vale \\$0.00: capture su mano de obra o sus refacciones.$"
    with pytest.raises(ValorInvalido, match=mensaje):
        Cotizacion.generar(
            "COT-1",
            NUMERO,
            TipoCotizacion.INICIAL,
            VersionCotizacion(1),
            [_linea("100.00"), _linea("0.00", numero=2)],
            INICIO,
        )


@pytest.mark.parametrize("accion", ["ajustar", "corregir"])
def test_rn_32_ajustar_y_corregir_tambien_exigen_importe(accion: str) -> None:
    cotizacion = _inicial("20000.00")
    if accion == "ajustar":
        cotizacion.rechazar_por_gerente("Revise", _horas(1))
        with pytest.raises(ValorInvalido, match="vale \\$0.00"):
            cotizacion.ajustar([_linea("0.00")], _horas(2))
    else:
        with pytest.raises(ValorInvalido, match="vale \\$0.00"):
            _corregir(cotizacion, "0.00")
    assert cotizacion.total == Dinero(Decimal("20000.00"))


def test_rn_32_reconstruir_acepta_cotizaciones_guardadas_de_0() -> None:
    """Las cotizaciones de $0.00 que ya existían se siguen leyendo (condición del equipo)."""
    cotizacion = Cotizacion("COT-9", NUMERO, TipoCotizacion.INICIAL, VersionCotizacion(1),
                            [_linea("0.00")], INICIO)

    assert cotizacion.total == Dinero.cero()
