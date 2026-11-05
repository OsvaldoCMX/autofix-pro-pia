"""Repository del Aggregate Orden de Servicio (interfaz del dominio)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.compartido.valores import NumeroOrden
from domain.ordenes.orden_de_servicio import OrdenDeServicio


class RepositorioDeOrdenes(ABC):
    @abstractmethod
    def obtener(self, numero: NumeroOrden) -> OrdenDeServicio:
        """Devuelve la orden o lanza `OrdenNoEncontrada`."""

    @abstractmethod
    def agregar(self, orden: OrdenDeServicio) -> None: ...

    @abstractmethod
    def guardar(self, orden: OrdenDeServicio) -> None: ...

    @abstractmethod
    def siguiente_numero(self) -> NumeroOrden: ...
