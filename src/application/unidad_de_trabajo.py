"""Unit of Work: define qué cambios se confirman juntos (ADR-002, ADR-016).

Uso en cada Application Service:

    with self._uow as uow:
        ...                 # obtiene Aggregates e invoca al dominio
        uow.confirmar()     # guarda todo junto, con la bitácora de eventos
    self._publicador.publicar(uow.eventos_confirmados())

Si ocurre un error antes de confirmar, `__exit__` deshace todos los cambios.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from types import TracebackType
from typing import Any, Self

from application.puertos import RepositorioDeAlertas
from domain.clientes.repositorio import RepositorioDeClientes
from domain.compartido.eventos import EventoDeDominio
from domain.cotizaciones.eventos import EventoDeCotizacion
from domain.cotizaciones.repositorio import RepositorioDeCotizaciones
from domain.empleados.repositorio import RepositorioDeEmpleados
from domain.ordenes.eventos import EventoDeOrden
from domain.ordenes.repositorio import RepositorioDeOrdenes
from domain.vehiculos.repositorio import RepositorioDeVehiculos


@dataclass(frozen=True)
class RegistroDeBitacora:
    """Una fila de la bitácora de eventos: evidencia de cada transición (ADR-016)."""

    tipo: str
    agregado: str
    id_agregado: str
    datos: dict[str, Any]
    ocurrido_en: datetime


def registro_de_bitacora(evento: EventoDeDominio) -> RegistroDeBitacora:
    """Traduce un evento a su registro, igual para cualquier implementación."""
    if isinstance(evento, EventoDeCotizacion):
        agregado, id_agregado = "Cotizacion", evento.id_cotizacion
    elif isinstance(evento, EventoDeOrden):
        agregado, id_agregado = "Orden", evento.numero_orden
    else:
        raise TypeError(f"Evento sin Aggregate conocido: {type(evento).__name__}")
    datos = asdict(evento)
    del datos["ocurrido_en"]
    return RegistroDeBitacora(
        type(evento).__name__,
        agregado,
        id_agregado,
        {campo: list(v) if isinstance(v, tuple) else v for campo, v in datos.items()},
        evento.ocurrido_en,
    )


class UnidadDeTrabajo(ABC):
    ordenes: RepositorioDeOrdenes
    cotizaciones: RepositorioDeCotizaciones
    clientes: RepositorioDeClientes
    vehiculos: RepositorioDeVehiculos
    empleados: RepositorioDeEmpleados
    alertas: RepositorioDeAlertas

    def __enter__(self) -> Self:
        self._confirmada = False
        self._eventos: list[EventoDeDominio] = []
        self._iniciar()
        return self

    def __exit__(
        self,
        tipo_error: type[BaseException] | None,
        error: BaseException | None,
        traza: TracebackType | None,
    ) -> None:
        if tipo_error is not None or not self._confirmada:
            self._deshacer()

    def confirmar(self) -> None:
        eventos = self._recolectar_eventos()
        self._guardar_bitacora([registro_de_bitacora(evento) for evento in eventos])
        self._confirmar()
        self._eventos = eventos
        self._confirmada = True

    def eventos_confirmados(self) -> list[EventoDeDominio]:
        return list(self._eventos)

    @abstractmethod
    def _iniciar(self) -> None: ...

    @abstractmethod
    def _recolectar_eventos(self) -> list[EventoDeDominio]: ...

    @abstractmethod
    def _guardar_bitacora(self, registros: list[RegistroDeBitacora]) -> None: ...

    @abstractmethod
    def _confirmar(self) -> None: ...

    @abstractmethod
    def _deshacer(self) -> None: ...
