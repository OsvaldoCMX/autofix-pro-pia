"""Solicitudes de compra, llegada de refacciones y aviso al cliente (US-010 a US-012)."""
from __future__ import annotations

from application.comandos import (
    RegistrarAvisoAlCliente,
    RegistrarLlegadaDeRefaccion,
    SolicitarRefaccion,
)
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import ResultadoDeSolicitud
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.compartido.valores import NumeroOrden
from domain.ordenes.orden_de_servicio import OrdenDeServicio


class ServicioDeRefacciones:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador

    def solicitar(self, comando: SolicitarRefaccion) -> ResultadoDeSolicitud:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            solicitud = orden.crear_solicitud_de_compra(
                comando.id_trabajo, comando.refaccion, comando.cantidad, self._reloj.ahora()
            )
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return _resultado(orden, solicitud.id)

    def registrar_llegada(self, comando: RegistrarLlegadaDeRefaccion) -> ResultadoDeSolicitud:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.registrar_llegada_de_refaccion(comando.id_solicitud, self._reloj.ahora())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return _resultado(orden, comando.id_solicitud)

    def registrar_aviso_al_cliente(self, comando: RegistrarAvisoAlCliente) -> ResultadoDeSolicitud:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.registrar_aviso_al_cliente(comando.id_solicitud, self._reloj.ahora())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return _resultado(orden, comando.id_solicitud)


def _resultado(orden: OrdenDeServicio, id_solicitud: int) -> ResultadoDeSolicitud:
    solicitud = next(solicitud for solicitud in orden.solicitudes if solicitud.id == id_solicitud)
    return ResultadoDeSolicitud(
        str(orden.numero), solicitud.id, solicitud.estado.value, orden.estado.value
    )
