"""Repository del Aggregate Cliente (interfaz del dominio)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.clientes.cliente import Cliente


class RepositorioDeClientes(ABC):
    @abstractmethod
    def obtener(self, id_cliente: str) -> Cliente:
        """Devuelve el cliente o lanza `ClienteNoEncontrado`."""

    @abstractmethod
    def agregar(self, cliente: Cliente) -> None: ...

    @abstractmethod
    def guardar(self, cliente: Cliente) -> None: ...

    @abstractmethod
    def buscar_flotilla(self, empresa: str) -> Cliente | None:
        """Devuelve el cliente de flotilla de esa empresa, si ya está registrado (CA-028)."""
