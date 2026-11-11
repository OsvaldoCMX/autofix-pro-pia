"""Specification E2 `AutorizanteValido` (modelo-de-dominio.md §4)."""
from __future__ import annotations

from typing import TypeAlias

from domain.clientes.cliente import Cliente
from domain.compartido.especificacion import Especificacion
from domain.cotizaciones.valores import Autorizante, RolDeAutorizante

ClienteYAutorizante: TypeAlias = tuple[Cliente, Autorizante]


def _mismo_nombre(uno: str, otro: str) -> bool:
    """Sin distinguir mayúsculas ni espacios repetidos o en los extremos; los acentos sí cuentan
    («Luis Pena» no es «Luis Peña») (CA-063, H-PIA-27)."""
    return " ".join(uno.split()).casefold() == " ".join(otro.split()).casefold()


class EsClienteParticular(Especificacion[ClienteYAutorizante]):
    def es_satisfecha_por(self, candidato: ClienteYAutorizante) -> bool:
        return not candidato[0].es_de_flotilla


class EsClienteDeFlotilla(Especificacion[ClienteYAutorizante]):
    def es_satisfecha_por(self, candidato: ClienteYAutorizante) -> bool:
        return candidato[0].es_de_flotilla


class AutorizaElCliente(Especificacion[ClienteYAutorizante]):
    def es_satisfecha_por(self, candidato: ClienteYAutorizante) -> bool:
        cliente, autorizante = candidato
        return autorizante.rol is RolDeAutorizante.CLIENTE and _mismo_nombre(
            autorizante.nombre, cliente.nombre
        )


class AutorizaSuResponsableDeFlotilla(Especificacion[ClienteYAutorizante]):
    def es_satisfecha_por(self, candidato: ClienteYAutorizante) -> bool:
        cliente, autorizante = candidato
        responsable = cliente.responsable
        return (
            responsable is not None
            and autorizante.rol is RolDeAutorizante.RESPONSABLE_DE_FLOTILLA
            and _mismo_nombre(autorizante.nombre, responsable.nombre)
        )


class AutorizanteValido(Especificacion[ClienteYAutorizante]):
    """E2 · RN-07: el cliente particular o el Responsable de Flotilla; nunca el conductor."""

    def __init__(self) -> None:
        self._regla = (EsClienteParticular() & AutorizaElCliente()) | (
            EsClienteDeFlotilla() & AutorizaSuResponsableDeFlotilla()
        )

    def es_satisfecha_por(self, candidato: ClienteYAutorizante) -> bool:
        return self._regla.es_satisfecha_por(candidato)
