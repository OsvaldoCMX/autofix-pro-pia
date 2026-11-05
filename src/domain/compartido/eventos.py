"""Base para Domain Events y raíces de Aggregate (ADR-016)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.compartido.errores import ValorInvalido


@dataclass(frozen=True)
class EventoDeDominio:
    """Hecho del negocio que ya ocurrió (se nombra en pasado)."""

    ocurrido_en: datetime

    def __post_init__(self) -> None:
        if self.ocurrido_en.utcoffset() is None:
            raise ValorInvalido("La fecha de un evento debe tener zona horaria.")


class RaizDeAgregado:
    """Acumula los eventos del Aggregate hasta que la Unidad de Trabajo los extrae."""

    def __init__(self) -> None:
        self._eventos: list[EventoDeDominio] = []

    def _registrar(self, evento: EventoDeDominio) -> None:
        self._eventos.append(evento)

    def extraer_eventos(self) -> list[EventoDeDominio]:
        eventos, self._eventos = self._eventos, []
        return eventos
