"""Entrega del vehículo y cierre de la orden (US-024, CA-041 a CA-043).

Usa la hora del taller porque el vencimiento del crédito se cuenta desde el día de la entrega en
Monterrey: en UTC, una entrega de la noche ya sería del día siguiente (RN-17).
"""
from __future__ import annotations

from application.comandos import EntregarSinReparacion, RegistrarEntrega
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import ResultadoDeEntrega
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.compartido.valores import NumeroOrden
from domain.ordenes.orden_de_servicio import OrdenDeServicio


class ServicioDeEntrega:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador

    def entregar(self, comando: RegistrarEntrega) -> ResultadoDeEntrega:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.entregar(self._reloj.ahora_en_el_taller())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return _resultado(orden)

    def entregar_sin_reparacion(self, comando: EntregarSinReparacion) -> ResultadoDeEntrega:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.entregar_sin_reparacion(self._reloj.ahora_en_el_taller())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return _resultado(orden)


def _resultado(orden: OrdenDeServicio) -> ResultadoDeEntrega:
    cargo = orden.cargo_a_credito
    return ResultadoDeEntrega(
        str(orden.numero),
        orden.estado.value,
        orden.fecha_entrega,
        cargo.fecha_vencimiento if cargo else None,
    )
