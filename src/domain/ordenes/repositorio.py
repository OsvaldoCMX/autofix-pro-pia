"""Repository del Aggregate Orden de Servicio (interfaz del dominio)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.compartido.valores import NumeroOrden, Placas
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

    @abstractmethod
    def abierta_del_vehiculo(self, placas: Placas) -> OrdenDeServicio | None:
        """La orden abierta del vehículo, si tiene una (RN-27)."""
