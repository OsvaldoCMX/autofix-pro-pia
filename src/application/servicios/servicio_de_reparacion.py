"""Asignar, iniciar y completar los trabajos autorizados (US-006, US-008, US-020)."""
from __future__ import annotations

from application.comandos import AsignarTrabajos, CompletarTrabajo, IniciarTrabajo
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import ResultadoDeAsignacion, ResultadoDeTrabajo
from application.servicios.apoyo import exigir_tecnico
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.compartido.valores import NumeroOrden
from domain.ordenes.orden_de_servicio import OrdenDeServicio


class ServicioDeReparacion:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador

    def asignar_trabajos(self, comando: AsignarTrabajos) -> ResultadoDeAsignacion:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            exigir_tecnico(uow, comando.tecnico)
            orden.asignar_trabajos(comando.ids_trabajos, comando.tecnico, self._reloj.ahora())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeAsignacion(
            str(orden.numero), orden.estado.value, comando.ids_trabajos, comando.tecnico
        )

    def iniciar_trabajo(self, comando: IniciarTrabajo) -> ResultadoDeTrabajo:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.iniciar_trabajo(comando.id_trabajo, comando.tecnico, self._reloj.ahora())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return _resultado(orden, comando.id_trabajo)

    def completar_trabajo(self, comando: CompletarTrabajo) -> ResultadoDeTrabajo:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.completar_trabajo(comando.id_trabajo, comando.tecnico, self._reloj.ahora())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return _resultado(orden, comando.id_trabajo)


def _resultado(orden: OrdenDeServicio, id_trabajo: int) -> ResultadoDeTrabajo:
    trabajo = next(trabajo for trabajo in orden.trabajos if trabajo.id == id_trabajo)
    return ResultadoDeTrabajo(
        str(orden.numero), trabajo.id, trabajo.estado.value, orden.estado.value
    )
