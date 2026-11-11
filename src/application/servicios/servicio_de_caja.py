"""Pago de contado, su corrección y cargo a crédito (US-014, US-022, CA-026, CA-039, CA-058)."""
from __future__ import annotations

from application.comandos import CorregirFormaDePago, RegistrarCargoACredito, RegistrarPago
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import ResultadoDeCargoACredito, ResultadoDePago
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.compartido.valores import Dinero, NumeroOrden
from domain.ordenes.valores import Pago


class ServicioDeCaja:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador

    def registrar_pago(self, comando: RegistrarPago) -> ResultadoDePago:
        pago = Pago(Dinero(comando.monto), comando.forma, self._reloj.ahora())
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.registrar_pago(pago)
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDePago(
            str(orden.numero),
            orden.estado.value,
            str(pago.monto.monto),
            pago.forma.value,
            pago.registrado_en,
        )

    def corregir_forma_de_pago(self, comando: CorregirFormaDePago) -> ResultadoDePago:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.corregir_forma_de_pago(comando.forma, self._reloj.ahora())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        pago = orden.pago
        assert pago is not None
        return ResultadoDePago(
            str(orden.numero),
            orden.estado.value,
            str(pago.monto.monto),
            pago.forma.value,
            pago.registrado_en,
        )

    def registrar_cargo_a_credito(
        self, comando: RegistrarCargoACredito
    ) -> ResultadoDeCargoACredito:
        ahora = self._reloj.ahora()
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.registrar_cargo_a_credito(ahora)
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeCargoACredito(
            str(orden.numero), orden.estado.value, str(orden.total_autorizado.monto), ahora
        )
