"""Retiro anticipado con Nota de Responsabilidad y reactivación (US-013, CA-024, CA-025)."""
from __future__ import annotations

from application.comandos import ConfirmarFirmaDeNota, ReactivarOrden, RegistrarSalida
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import ResultadoDeEstado, ResultadoDeNota
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.compartido.valores import NumeroOrden


class ServicioDeRetiro:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador

    def registrar_salida(self, comando: RegistrarSalida) -> ResultadoDeNota:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            nota = orden.registrar_salida(self._reloj.ahora())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeNota(
            str(orden.numero), orden.estado.value, nota.fecha_salida, nota.firmada
        )

    def confirmar_firma(self, comando: ConfirmarFirmaDeNota) -> ResultadoDeEstado:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.confirmar_firma_de_nota(self._reloj.ahora())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeEstado(str(orden.numero), orden.estado.value)

    def reactivar(self, comando: ReactivarOrden) -> ResultadoDeEstado:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.reactivar(self._reloj.ahora())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeEstado(str(orden.numero), orden.estado.value)
