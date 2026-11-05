"""Patrón Specification: reglas pequeñas y puras que se combinan con AND, OR y NOT (ADR-006)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Especificacion(ABC, Generic[T]):
    """Regla del negocio que un candidato cumple o no."""

    @abstractmethod
    def es_satisfecha_por(self, candidato: T) -> bool: ...

    def y(self, otra: Especificacion[T]) -> Especificacion[T]:
        return _EspecificacionY(self, otra)

    def o(self, otra: Especificacion[T]) -> Especificacion[T]:
        return _EspecificacionO(self, otra)

    def no(self) -> Especificacion[T]:
        return _EspecificacionNo(self)

    def __and__(self, otra: Especificacion[T]) -> Especificacion[T]:
        return self.y(otra)

    def __or__(self, otra: Especificacion[T]) -> Especificacion[T]:
        return self.o(otra)

    def __invert__(self) -> Especificacion[T]:
        return self.no()


class _EspecificacionY(Especificacion[T]):
    def __init__(self, izquierda: Especificacion[T], derecha: Especificacion[T]) -> None:
        self._izquierda = izquierda
        self._derecha = derecha

    def es_satisfecha_por(self, candidato: T) -> bool:
        return self._izquierda.es_satisfecha_por(candidato) and self._derecha.es_satisfecha_por(
            candidato
        )


class _EspecificacionO(Especificacion[T]):
    def __init__(self, izquierda: Especificacion[T], derecha: Especificacion[T]) -> None:
        self._izquierda = izquierda
        self._derecha = derecha

    def es_satisfecha_por(self, candidato: T) -> bool:
        return self._izquierda.es_satisfecha_por(candidato) or self._derecha.es_satisfecha_por(
            candidato
        )


class _EspecificacionNo(Especificacion[T]):
    def __init__(self, especificacion: Especificacion[T]) -> None:
        self._especificacion = especificacion

    def es_satisfecha_por(self, candidato: T) -> bool:
        return not self._especificacion.es_satisfecha_por(candidato)
