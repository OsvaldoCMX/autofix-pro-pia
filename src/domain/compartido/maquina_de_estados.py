"""Máquina de estados genérica: una tabla por objeto con estado (ADR-007)."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import Enum
from typing import Generic, TypeVar

from domain.compartido.errores import TransicionDeEstadoNoPermitida

E = TypeVar("E", bound=Enum)


class MaquinaDeEstados(Generic[E]):
    """Guarda las transiciones permitidas y rechaza cualquier otra combinación."""

    def __init__(
        self,
        nombre: str,
        transiciones: Mapping[E, Iterable[E]],
        finales: Iterable[E],
    ) -> None:
        self._nombre = nombre
        self._transiciones = {
            estado: frozenset(destinos) for estado, destinos in transiciones.items()
        }
        self._finales = frozenset(finales)
        for estado in self._finales:
            if self._transiciones.get(estado):
                raise ValueError(f"El estado final «{estado.value}» no puede tener destinos.")

    def permite(self, actual: E, nuevo: E) -> bool:
        return nuevo in self._transiciones.get(actual, frozenset())

    def es_final(self, estado: E) -> bool:
        return estado in self._finales

    def validar(self, actual: E, nuevo: E) -> None:
        if not self.permite(actual, nuevo):
            raise TransicionDeEstadoNoPermitida(
                f"{self._nombre} no puede pasar de «{actual.value}» a «{nuevo.value}». "
                "Revise su estado actual."
            )
