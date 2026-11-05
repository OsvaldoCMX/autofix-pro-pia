"""Reacciones a los Domain Events: crean alertas internas (modelo-de-dominio.md §6, ADR-016).

Corren después de confirmar, cada una en su propia Unidad de Trabajo. Pueden leer la orden para
saber a quién avisar, pero no modifican ningún Aggregate.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from application.puertos import AlertaInterna
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.compartido.eventos import EventoDeDominio
from domain.compartido.valores import NumeroOrden
from domain.cotizaciones import eventos as ev_cot
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes import eventos as ev_ord

FabricaDeUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]


class ManejadoresDeAlertas:
    def __init__(self, fabrica_de_uow: FabricaDeUnidadDeTrabajo) -> None:
        self._fabrica_de_uow = fabrica_de_uow

    def suscripciones(self) -> dict[type[EventoDeDominio], Callable[[Any], None]]:
        """Qué evento atiende cada manejador; el Composition Root los registra en el publicador."""
        return {
            ev_ord.DiagnosticoRegistrado: self.diagnostico_registrado,
            ev_cot.AprobacionGerencialRequerida: self.aprobacion_requerida,
            ev_cot.CotizacionAprobadaPorGerente: self.cotizacion_aprobada,
            ev_cot.CotizacionRechazadaPorGerente: self.cotizacion_rechazada,
            ev_cot.CotizacionAutorizada: self.cotizacion_autorizada,
            ev_ord.FallaAdicionalReportada: self.falla_adicional_reportada,
            ev_ord.RefaccionDisponible: self.refaccion_disponible,
            ev_ord.OrdenListaParaEntrega: self.orden_lista,
        }

    def diagnostico_registrado(self, evento: ev_ord.DiagnosticoRegistrado) -> None:
        self._avisar_a(
            evento,
            evento.asesor,
            f"La orden {evento.numero_orden} ya tiene diagnóstico: está lista para cotizar.",
        )

    def aprobacion_requerida(self, evento: ev_cot.AprobacionGerencialRequerida) -> None:
        mensaje = (
            f"La cotización {evento.id_cotizacion} de la orden {evento.numero_orden} "
            f"(${evento.total}) requiere su aprobación."
        )
        with self._fabrica_de_uow() as uow:
            uow.alertas.agregar(
                _alerta(evento, mensaje, destinatario_rol=RolDeEmpleado.GERENTE)
            )
            uow.confirmar()

    def cotizacion_aprobada(self, evento: ev_cot.CotizacionAprobadaPorGerente) -> None:
        self._avisar_al_asesor_de_la_orden(
            evento,
            f"El Gerente aprobó la cotización {evento.id_cotizacion}: ya puede presentarse.",
        )

    def cotizacion_rechazada(self, evento: ev_cot.CotizacionRechazadaPorGerente) -> None:
        self._avisar_al_asesor_de_la_orden(
            evento,
            f"El Gerente rechazó la cotización {evento.id_cotizacion}: {evento.observaciones}",
        )

    def cotizacion_autorizada(self, evento: ev_cot.CotizacionAutorizada) -> None:
        """Solo la adicional avisa: a cada técnico con trabajos asignados en la orden (CA-017)."""
        if not evento.es_adicional:
            return
        mensaje = (
            f"El cliente autorizó la cotización adicional {evento.id_cotizacion} "
            f"de la orden {evento.numero_orden}."
        )
        with self._fabrica_de_uow() as uow:
            orden = uow.ordenes.obtener(NumeroOrden(evento.numero_orden))
            tecnicos = {trabajo.tecnico for trabajo in orden.trabajos if trabajo.tecnico}
            for tecnico in sorted(tecnicos):
                uow.alertas.agregar(_alerta(evento, mensaje, destinatario=tecnico))
            uow.confirmar()

    def falla_adicional_reportada(self, evento: ev_ord.FallaAdicionalReportada) -> None:
        self._avisar_a(
            evento,
            evento.asesor,
            f"Se reportó una falla adicional en la orden {evento.numero_orden}: "
            f"{evento.descripcion}. Genere la cotización adicional.",
        )

    def refaccion_disponible(self, evento: ev_ord.RefaccionDisponible) -> None:
        mensaje = f"Llegó una refacción de la orden {evento.numero_orden}."
        if evento.tecnico is not None:
            self._avisar_a(evento, evento.tecnico, mensaje)
        self._avisar_a(evento, evento.asesor, mensaje)

    def orden_lista(self, evento: ev_ord.OrdenListaParaEntrega) -> None:
        self._avisar_a(
            evento, evento.asesor, f"La orden {evento.numero_orden} está lista para entrega."
        )

    def _avisar_a(self, evento: ev_ord.EventoDeOrden, destinatario: str, mensaje: str) -> None:
        with self._fabrica_de_uow() as uow:
            uow.alertas.agregar(_alerta(evento, mensaje, destinatario=destinatario))
            uow.confirmar()

    def _avisar_al_asesor_de_la_orden(
        self, evento: ev_cot.EventoDeCotizacion, mensaje: str
    ) -> None:
        with self._fabrica_de_uow() as uow:
            orden = uow.ordenes.obtener(NumeroOrden(evento.numero_orden))
            uow.alertas.agregar(_alerta(evento, mensaje, destinatario=orden.asesor))
            uow.confirmar()


def _alerta(
    evento: ev_ord.EventoDeOrden | ev_cot.EventoDeCotizacion,
    mensaje: str,
    destinatario: str | None = None,
    destinatario_rol: RolDeEmpleado | None = None,
) -> AlertaInterna:
    return AlertaInterna(
        type(evento).__name__,
        mensaje,
        evento.ocurrido_en,
        destinatario,
        destinatario_rol,
        evento.numero_orden,
        getattr(evento, "id_cotizacion", None),
    )
