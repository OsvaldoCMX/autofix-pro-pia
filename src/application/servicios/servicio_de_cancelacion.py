"""Cancelación de la orden antes de la cotización (US-025, CA-044, CA-045)."""
from __future__ import annotations

from application.comandos import CancelarOrden
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import ResultadoDeEstado
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.compartido.valores import NumeroOrden


class ServicioDeCancelacion:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador

    def cancelar(self, comando: CancelarOrden) -> ResultadoDeEstado:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.cancelar(comando.motivo, comando.asesor, self._reloj.ahora())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeEstado(str(orden.numero), orden.estado.value)
