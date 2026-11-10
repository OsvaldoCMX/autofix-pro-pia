"""Repository del Aggregate Vehículo (interfaz del dominio)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.compartido.valores import Placas
from domain.vehiculos.vehiculo import Vehiculo


class RepositorioDeVehiculos(ABC):
    @abstractmethod
    def por_placas(self, placas: Placas) -> Vehiculo:
        """Devuelve el vehículo o lanza `VehiculoNoEncontrado`."""

    @abstractmethod
    def agregar(self, vehiculo: Vehiculo) -> None: ...

    @abstractmethod
    def guardar(self, vehiculo: Vehiculo) -> None: ...

    @abstractmethod
    def cambiar_placas(self, anteriores: Placas, nuevas: Placas) -> Vehiculo:
        """RN-35: cambia la identidad del vehículo y la de sus órdenes a la vez.

        Lanza `VehiculoNoEncontrado` si no existe y `CorreccionNoPermitida` si las placas
        nuevas ya son de otro vehículo."""
