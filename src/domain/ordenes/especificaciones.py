"""Specifications E3 a E7 del Aggregate Orden de Servicio (modelo-de-dominio.md §4)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, ClassVar, TypeAlias

from domain.compartido.calendario import CalendarioHabil
from domain.compartido.especificacion import Especificacion
from domain.ordenes.estados import EstadoOrden, EstadoTrabajo
from domain.ordenes.solicitud_de_compra import SolicitudDeCompra
from domain.ordenes.trabajo import Trabajo

if TYPE_CHECKING:
    from domain.ordenes.orden_de_servicio import OrdenDeServicio

TrabajoDeLaOrden: TypeAlias = tuple["OrdenDeServicio", Trabajo]

DIAS_HABILES_DE_ESPERA = 3


class _OrdenEnEstado(Especificacion["OrdenDeServicio"]):
    estado: ClassVar[EstadoOrden]

    def es_satisfecha_por(self, candidato: OrdenDeServicio) -> bool:
        return candidato.estado is self.estado


class EstaPagada(_OrdenEnEstado):
    estado = EstadoOrden.PAGADA


class EstaPorCobrarACredito(_OrdenEnEstado):
    estado = EstadoOrden.POR_COBRAR_CREDITO


class EstaCotizada(_OrdenEnEstado):
    estado = EstadoOrden.COTIZADA


class EstaRecibida(_OrdenEnEstado):
    estado = EstadoOrden.RECIBIDA


class EstaEnDiagnostico(_OrdenEnEstado):
    estado = EstadoOrden.EN_DIAGNOSTICO


class TieneRechazoTotal(Especificacion["OrdenDeServicio"]):
    def es_satisfecha_por(self, candidato: OrdenDeServicio) -> bool:
        return candidato.rechazo_total


class PuedeEntregarse(Especificacion["OrdenDeServicio"]):
    """E3 · RN-18: con pago, con cargo a crédito o tras un rechazo total."""

    def __init__(self) -> None:
        self._regla = (
            EstaPagada() | EstaPorCobrarACredito() | (EstaCotizada() & TieneRechazoTotal())
        )

    def es_satisfecha_por(self, candidato: OrdenDeServicio) -> bool:
        return self._regla.es_satisfecha_por(candidato)


class PuedeCancelarse(Especificacion["OrdenDeServicio"]):
    """E4 · RN-19: solo antes de tener cotización."""

    def __init__(self) -> None:
        self._regla = EstaRecibida() | EstaEnDiagnostico()

    def es_satisfecha_por(self, candidato: OrdenDeServicio) -> bool:
        return self._regla.es_satisfecha_por(candidato)


class _OrdenDelTrabajoEnEstado(Especificacion[TrabajoDeLaOrden]):
    estado: ClassVar[EstadoOrden]

    def es_satisfecha_por(self, candidato: TrabajoDeLaOrden) -> bool:
        return candidato[0].estado is self.estado


class OrdenPausadaPorRetiro(_OrdenDelTrabajoEnEstado):
    estado = EstadoOrden.PAUSADA_POR_RETIRO_DE_VEHICULO


class OrdenAutorizada(_OrdenDelTrabajoEnEstado):
    estado = EstadoOrden.AUTORIZADA


class OrdenEnReparacion(_OrdenDelTrabajoEnEstado):
    estado = EstadoOrden.EN_REPARACION


class OrdenEnEsperaDeRefaccion(_OrdenDelTrabajoEnEstado):
    estado = EstadoOrden.EN_ESPERA_DE_REFACCION


class TrabajoPendiente(Especificacion[TrabajoDeLaOrden]):
    def es_satisfecha_por(self, candidato: TrabajoDeLaOrden) -> bool:
        return candidato[1].estado is EstadoTrabajo.PENDIENTE


class AsignadoAlTecnico(Especificacion[TrabajoDeLaOrden]):
    def __init__(self, tecnico: str) -> None:
        self._tecnico = tecnico

    def es_satisfecha_por(self, candidato: TrabajoDeLaOrden) -> bool:
        return candidato[1].tecnico == self._tecnico


class TrabajoAutorizado(Especificacion[TrabajoDeLaOrden]):
    """El cliente lo autorizó y sigue abierto: un trabajo completado ya no necesita piezas."""

    def es_satisfecha_por(self, candidato: TrabajoDeLaOrden) -> bool:
        return candidato[1].estado in (EstadoTrabajo.PENDIENTE, EstadoTrabajo.EN_PROGRESO)


class PuedeIniciarTrabajo(Especificacion[TrabajoDeLaOrden]):
    """E5 · RN-14: pendiente, de ese técnico y con el vehículo en el taller."""

    def __init__(self, tecnico: str) -> None:
        self._regla = TrabajoPendiente() & AsignadoAlTecnico(tecnico) & ~OrdenPausadaPorRetiro()

    def es_satisfecha_por(self, candidato: TrabajoDeLaOrden) -> bool:
        return self._regla.es_satisfecha_por(candidato)


class PuedeSolicitarRefaccion(Especificacion[TrabajoDeLaOrden]):
    """E6 · RN-09: solo de trabajos autorizados y con la orden en reparación o por iniciarla."""

    def __init__(self) -> None:
        self._regla = TrabajoAutorizado() & (
            OrdenAutorizada() | OrdenEnReparacion() | OrdenEnEsperaDeRefaccion()
        )

    def es_satisfecha_por(self, candidato: TrabajoDeLaOrden) -> bool:
        return self._regla.es_satisfecha_por(candidato)


class SolicitudPendiente(Especificacion[SolicitudDeCompra]):
    def es_satisfecha_por(self, candidato: SolicitudDeCompra) -> bool:
        return candidato.esta_pendiente


class ClienteYaAvisado(Especificacion[SolicitudDeCompra]):
    def es_satisfecha_por(self, candidato: SolicitudDeCompra) -> bool:
        return candidato.fecha_aviso_al_cliente is not None


class MasDeDiasHabiles(Especificacion[SolicitudDeCompra]):
    """Cuenta los días en la zona horaria de `fecha_de_revision`."""

    def __init__(
        self, dias: int, fecha_de_revision: datetime, calendario: CalendarioHabil
    ) -> None:
        self._dias = dias
        self._fecha_de_revision = fecha_de_revision
        self._calendario = calendario

    def es_satisfecha_por(self, candidato: SolicitudDeCompra) -> bool:
        zona = self._fecha_de_revision.tzinfo
        inicio = candidato.fecha_solicitud.astimezone(zona).date()
        transcurridos = self._calendario.dias_habiles_entre(inicio, self._fecha_de_revision.date())
        return transcurridos > self._dias


class RequiereAlertaDeRefaccion(Especificacion[SolicitudDeCompra]):
    """E7 · RN-11: sigue «Solicitada» después de 3 días hábiles y aún no se avisa al cliente."""

    def __init__(
        self, fecha_de_revision: datetime, calendario: CalendarioHabil | None = None
    ) -> None:
        self._regla = (
            SolicitudPendiente()
            & MasDeDiasHabiles(
                DIAS_HABILES_DE_ESPERA, fecha_de_revision, calendario or CalendarioHabil()
            )
            & ~ClienteYaAvisado()
        )

    def es_satisfecha_por(self, candidato: SolicitudDeCompra) -> bool:
        return self._regla.es_satisfecha_por(candidato)
