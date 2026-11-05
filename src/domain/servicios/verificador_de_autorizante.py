"""Domain Service: ¿quién puede autorizar una cotización? (US-006, US-016, CA-029).

La regla necesita datos de dos Aggregates (el Cliente y la decisión sobre la Cotización), por
eso no pertenece a ninguno de los dos.
"""
from __future__ import annotations

from domain.clientes.cliente import Cliente
from domain.clientes.especificaciones import AutorizanteValido
from domain.compartido.errores import AutorizanteNoValido
from domain.cotizaciones.valores import Autorizante


class VerificadorDeAutorizante:
    def __init__(self) -> None:
        self._regla = AutorizanteValido()

    def verificar(self, cliente: Cliente, autorizante: Autorizante) -> None:
        if self._regla.es_satisfecha_por((cliente, autorizante)):
            return
        if cliente.es_de_flotilla:
            raise AutorizanteNoValido(
                f"Para la flotilla de {cliente.empresa} solo puede autorizar "
                "su Responsable de Flotilla; el conductor no puede autorizar."
            )
        raise AutorizanteNoValido(
            f"La decisión debe registrarse a nombre del cliente {cliente.nombre}."
        )
