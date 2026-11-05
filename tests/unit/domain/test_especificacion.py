"""Combinadores de la clase base Especificacion (ADR-006)."""
from __future__ import annotations

from itertools import product

import pytest

from domain.compartido.especificacion import Especificacion


class _Fija(Especificacion[object]):
    """Pieza que siempre responde lo mismo, para recorrer las tablas de verdad."""

    def __init__(self, respuesta: bool) -> None:
        self._respuesta = respuesta

    def es_satisfecha_por(self, candidato: object) -> bool:
        return self._respuesta


class _EsMayorQue(Especificacion[int]):
    def __init__(self, limite: int) -> None:
        self._limite = limite

    def es_satisfecha_por(self, candidato: int) -> bool:
        return candidato > self._limite


class _SumaMayorQue(Especificacion[tuple[int, int]]):
    def __init__(self, limite: int) -> None:
        self._limite = limite

    def es_satisfecha_por(self, candidato: tuple[int, int]) -> bool:
        return sum(candidato) > self._limite


CANDIDATO = object()
VALORES = (True, False)


@pytest.mark.parametrize(("a", "b"), list(product(VALORES, repeat=2)))
def test_especificacion_y_tabla_de_verdad(a: bool, b: bool) -> None:
    assert _Fija(a).y(_Fija(b)).es_satisfecha_por(CANDIDATO) is (a and b)


@pytest.mark.parametrize(("a", "b"), list(product(VALORES, repeat=2)))
def test_especificacion_o_tabla_de_verdad(a: bool, b: bool) -> None:
    assert _Fija(a).o(_Fija(b)).es_satisfecha_por(CANDIDATO) is (a or b)


@pytest.mark.parametrize("a", VALORES)
def test_especificacion_no_invierte(a: bool) -> None:
    assert _Fija(a).no().es_satisfecha_por(CANDIDATO) is (not a)


@pytest.mark.parametrize(("a", "b"), list(product(VALORES, repeat=2)))
def test_operadores_equivalen_a_los_metodos(a: bool, b: bool) -> None:
    izquierda, derecha = _Fija(a), _Fija(b)

    assert (izquierda & derecha).es_satisfecha_por(CANDIDATO) is izquierda.y(
        derecha
    ).es_satisfecha_por(CANDIDATO)
    assert (izquierda | derecha).es_satisfecha_por(CANDIDATO) is izquierda.o(
        derecha
    ).es_satisfecha_por(CANDIDATO)
    assert (~izquierda).es_satisfecha_por(CANDIDATO) is izquierda.no().es_satisfecha_por(CANDIDATO)


@pytest.mark.parametrize(("a", "b", "c"), list(product(VALORES, repeat=3)))
def test_combinacion_and_or_not_tabla_de_verdad(a: bool, b: bool, c: bool) -> None:
    combinada = (_Fija(a) & _Fija(b)) | ~_Fija(c)

    assert combinada.es_satisfecha_por(CANDIDATO) is ((a and b) or (not c))


def test_acepta_candidato_compuesto() -> None:
    assert _SumaMayorQue(5).es_satisfecha_por((3, 4)) is True
    assert (_EsMayorQue(5) & ~_EsMayorQue(10)).es_satisfecha_por(7) is True
    assert (_EsMayorQue(5) & ~_EsMayorQue(10)).es_satisfecha_por(11) is False


def test_la_base_es_abstracta() -> None:
    with pytest.raises(TypeError):
        Especificacion()
