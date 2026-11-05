"""Registrar la decisión del cliente (US-006, US-009, US-016; CA-010, CA-012, CA-017, CA-018).

Modifica dos Aggregates: la Unidad de Trabajo guarda los dos cambios juntos o ninguno (ADR-002).
"""
from __future__ import annotations

from application.comandos import RegistrarDecisionDelCliente
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import ResultadoDeDecision
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.cotizaciones.valores import Autorizante
from domain.servicios.verificador_de_autorizante import VerificadorDeAutorizante


class ServicioDeAutorizacion:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador
        self._verificador = VerificadorDeAutorizante()

    def registrar_decision(self, comando: RegistrarDecisionDelCliente) -> ResultadoDeDecision:
        autorizante = Autorizante(comando.nombre_del_autorizante, comando.rol_del_autorizante)
        with self._uow as uow:
            cotizacion = uow.cotizaciones.obtener(comando.id_cotizacion)
            orden = uow.ordenes.obtener(cotizacion.numero_orden)
            cliente = uow.clientes.obtener(orden.id_cliente)
            self._verificador.verificar(cliente, autorizante)
            decision = cotizacion.registrar_decision(
                comando.lineas_autorizadas, autorizante, self._reloj.ahora()
            )
            orden.aplicar_decision(decision)
            uow.cotizaciones.guardar(cotizacion)
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeDecision(
            cotizacion.id,
            cotizacion.estado.value,
            orden.estado.value,
            tuple(trabajo.descripcion for trabajo in decision.autorizados),
            tuple(trabajo.descripcion for trabajo in decision.no_autorizados),
        )
