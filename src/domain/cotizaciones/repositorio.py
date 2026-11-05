"""Repository del Aggregate Cotización (interfaz del dominio)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.compartido.valores import NumeroOrden
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.valores import VersionCotizacion


class RepositorioDeCotizaciones(ABC):
    @abstractmethod
    def obtener(self, id_cotizacion: str) -> Cotizacion:
        """Devuelve la cotización o lanza `CotizacionNoEncontrada`."""

    @abstractmethod
    def agregar(self, cotizacion: Cotizacion) -> None: ...

    @abstractmethod
    def guardar(self, cotizacion: Cotizacion) -> None: ...

    @abstractmethod
    def de_la_orden(self, numero: NumeroOrden) -> list[Cotizacion]:
        """Devuelve las cotizaciones de la orden, de la versión menor a la mayor."""

    @abstractmethod
    def siguiente_version(self, numero: NumeroOrden) -> VersionCotizacion:
        """Devuelve la versión que le toca a la próxima cotización de la orden (RN-24)."""

    @abstractmethod
    def siguiente_id(self) -> str:
        """Devuelve el folio de la próxima cotización (COT-0001, COT-0002…)."""
