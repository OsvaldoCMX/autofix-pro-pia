"""Specifications E3 a E7 con casos verdaderos y falsos (modelo-de-dominio.md §4)."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from domain.compartido.calendario import CalendarioHabil
from domain.ordenes.especificaciones import (
    AsignadoAlTecnico,
    ClienteYaAvisado,
    MasDeDiasHabiles,
    PuedeCancelarse,
    PuedeEntregarse,
    PuedeIniciarTrabajo,
    PuedeSolicitarRefaccion,
    RequiereAlertaDeRefaccion,
    SolicitudPendiente,
    TrabajoAutorizado,
    TrabajoDeLaOrden,
    TrabajoPendiente,
)
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.solicitud_de_compra import SolicitudDeCompra
from tests.unit.domain import constructores as c

# El lunes 5 de octubre de 2026; el jueves 8 van 3 días hábiles y el viernes 9 van 4.
LUNES = datetime(2026, 10, 5, 15, 0, tzinfo=UTC)
JUEVES = datetime(2026, 10, 8, 15, 0, tzinfo=UTC)
VIERNES = datetime(2026, 10, 9, 15, 0, tzinfo=UTC)
MONTERREY = timezone(timedelta(hours=-6))


def _solicitud(fecha: datetime = LUNES) -> SolicitudDeCompra:
    return SolicitudDeCompra(1, 1, "Balatas", 2, fecha)


# ------------------------------------------------------------------ E3 PuedeEntregarse


@pytest.mark.parametrize("constructor", [c.pagada, c.por_cobrar])
def test_ca_041_e3_con_pago_o_cargo_a_credito(constructor: c.Constructor) -> None:
    assert PuedeEntregarse().es_satisfecha_por(constructor())


@pytest.mark.parametrize(
    "constructor",
    [c.recibida, c.en_diagnostico, c.cotizada, c.autorizada, c.en_reparacion, c.lista],
)
def test_ca_042_e3_sin_pago_ni_cargo(constructor: c.Constructor) -> None:
    assert not PuedeEntregarse().es_satisfecha_por(constructor())


def test_ca_043_e3_cotizada_con_rechazo_total() -> None:
    assert PuedeEntregarse().es_satisfecha_por(c.con_rechazo_total())


# ------------------------------------------------------------------ E4 PuedeCancelarse


@pytest.mark.parametrize("constructor", [c.recibida, c.en_diagnostico])
def test_ca_044_e4_antes_de_la_cotizacion(constructor: c.Constructor) -> None:
    assert PuedeCancelarse().es_satisfecha_por(constructor())


@pytest.mark.parametrize(
    "constructor",
    [
        c.cotizada,
        c.con_rechazo_total,
        c.autorizada,
        c.en_reparacion,
        c.lista,
        c.pagada,
        c.cancelada,
    ],
)
def test_ca_045_e4_despues_de_la_cotizacion(constructor: c.Constructor) -> None:
    assert not PuedeCancelarse().es_satisfecha_por(constructor())


# ------------------------------------------------------------------ E5 PuedeIniciarTrabajo


def _orden_y_trabajo(orden: OrdenDeServicio) -> TrabajoDeLaOrden:
    return orden, orden.trabajos[0]


def test_ca_014_e5_pendiente_y_de_su_tecnico() -> None:
    candidato = _orden_y_trabajo(c.autorizada())

    assert PuedeIniciarTrabajo(c.TECNICO).es_satisfecha_por(candidato)


def test_ca_014_e5_otro_tecnico_no_cumple() -> None:
    candidato = _orden_y_trabajo(c.autorizada())

    assert not PuedeIniciarTrabajo(c.OTRO_TECNICO).es_satisfecha_por(candidato)


def test_ca_014_e5_trabajo_ya_iniciado_no_cumple() -> None:
    candidato = _orden_y_trabajo(c.en_reparacion())

    assert not PuedeIniciarTrabajo(c.TECNICO).es_satisfecha_por(candidato)


def test_ca_046_e5_vehiculo_retirado_no_cumple() -> None:
    candidato = _orden_y_trabajo(c.pausada())

    assert not PuedeIniciarTrabajo(c.TECNICO).es_satisfecha_por(candidato)


def test_rn_14_e5_cada_pieza_se_evalua_por_separado() -> None:
    orden = c.autorizada()
    candidato = (orden, orden.trabajos[0])

    assert TrabajoPendiente().es_satisfecha_por(candidato)
    assert AsignadoAlTecnico(c.TECNICO).es_satisfecha_por(candidato)
    assert not AsignadoAlTecnico(c.OTRO_TECNICO).es_satisfecha_por(candidato)


# ------------------------------------------------------------------ E6 PuedeSolicitarRefaccion


@pytest.mark.parametrize("constructor", [c.autorizada, c.en_reparacion, c.en_espera])
def test_ca_019_e6_trabajo_autorizado_y_orden_en_curso(constructor: c.Constructor) -> None:
    orden = constructor()

    assert PuedeSolicitarRefaccion().es_satisfecha_por((orden, orden.trabajos[0]))


def test_ca_020_e6_trabajo_no_autorizado_no_cumple() -> None:
    orden = c.autorizada(trabajos=1, no_autorizados=1)

    assert not PuedeSolicitarRefaccion().es_satisfecha_por((orden, orden.trabajos[1]))


def test_rn_09_e6_trabajo_completado_no_cumple() -> None:
    orden = c.en_reparacion(trabajos=2)
    orden.completar_trabajo(1, c.TECNICO, c.INICIO)

    assert not TrabajoAutorizado().es_satisfecha_por((orden, orden.trabajos[0]))
    assert not PuedeSolicitarRefaccion().es_satisfecha_por((orden, orden.trabajos[0]))
    assert PuedeSolicitarRefaccion().es_satisfecha_por((orden, orden.trabajos[1]))


def test_rn_09_e6_orden_pausada_no_cumple() -> None:
    orden = c.pausada()

    assert not PuedeSolicitarRefaccion().es_satisfecha_por((orden, orden.trabajos[0]))


# ------------------------------------------------------------------ E7 RequiereAlertaDeRefaccion


def test_ca_023_e7_mas_de_3_dias_habiles_sin_aviso() -> None:
    assert RequiereAlertaDeRefaccion(VIERNES).es_satisfecha_por(_solicitud())


def test_ca_023_e7_exactamente_3_dias_habiles_no_alerta() -> None:
    assert not RequiereAlertaDeRefaccion(JUEVES).es_satisfecha_por(_solicitud())


def test_ca_023_e7_con_aviso_registrado_no_alerta() -> None:
    solicitud = _solicitud()
    solicitud.registrar_aviso_al_cliente(JUEVES)

    assert ClienteYaAvisado().es_satisfecha_por(solicitud)
    assert not RequiereAlertaDeRefaccion(VIERNES).es_satisfecha_por(solicitud)


def test_ca_023_e7_refaccion_que_ya_llego_no_alerta() -> None:
    solicitud = _solicitud()
    solicitud.marcar_disponible(JUEVES)

    assert not SolicitudPendiente().es_satisfecha_por(solicitud)
    assert not RequiereAlertaDeRefaccion(VIERNES).es_satisfecha_por(solicitud)


def test_rn_11_e7_cuenta_solo_dias_habiles() -> None:
    jueves_previo = datetime(2026, 10, 1, 15, 0, tzinfo=UTC)
    martes = datetime(2026, 10, 6, 15, 0, tzinfo=UTC)
    miercoles = datetime(2026, 10, 7, 15, 0, tzinfo=UTC)

    # Del jueves al martes hay 5 días naturales, pero solo 3 hábiles (vie, lun, mar).
    assert not RequiereAlertaDeRefaccion(martes).es_satisfecha_por(_solicitud(jueves_previo))
    assert RequiereAlertaDeRefaccion(miercoles).es_satisfecha_por(_solicitud(jueves_previo))


def test_rn_11_e7_cuenta_en_la_zona_de_la_fecha_de_revision() -> None:
    # 01:00 UTC del viernes 9 todavía es jueves 8 en Monterrey: van 3 días hábiles, no 4.
    revision_en_monterrey = datetime(2026, 10, 9, 1, 0, tzinfo=UTC).astimezone(MONTERREY)

    assert not RequiereAlertaDeRefaccion(revision_en_monterrey).es_satisfecha_por(_solicitud())


def test_rn_11_e7_solicitud_de_noche_cuenta_desde_el_dia_local() -> None:
    # 02:00 UTC del miércoles 7 todavía es martes 6 por la noche en Monterrey.
    solicitud = _solicitud(datetime(2026, 10, 7, 2, 0, tzinfo=UTC))
    viernes = datetime(2026, 10, 9, 15, 0, tzinfo=MONTERREY)
    lunes = datetime(2026, 10, 12, 15, 0, tzinfo=MONTERREY)

    assert not RequiereAlertaDeRefaccion(viernes).es_satisfecha_por(solicitud)
    assert RequiereAlertaDeRefaccion(lunes).es_satisfecha_por(solicitud)


def test_rn_11_e7_acepta_otro_calendario() -> None:
    class _CalendarioDeUnDia(CalendarioHabil):
        def dias_habiles_entre(self, inicio: date, fin: date) -> int:
            return 1

    regla = MasDeDiasHabiles(3, VIERNES, _CalendarioDeUnDia())

    assert not regla.es_satisfecha_por(_solicitud())
