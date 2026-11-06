"""Reglas de los oráculos, armadas con `Especificacion` solo dentro del arnés (ADR-013, D-01, D-02).

No van en el dominio: activo, preferente y promoción no son requisitos de AutoFix Pro.
`VALIDAR_OPERACION` es la regla de AutoFix contra la que se compara el flujo real.
"""
from __future__ import annotations

from decimal import Decimal

from domain.compartido.especificacion import Especificacion
from tests.datos_profesor.adaptador import OperacionDelProfesor

MINIMO_DEL_BENEFICIO = Decimal("1500.00")


class ActorActivo(Especificacion[OperacionDelProfesor]):
    def es_satisfecha_por(self, candidato: OperacionDelProfesor) -> bool:
        return candidato.actor_activo


class TieneDetalle(Especificacion[OperacionDelProfesor]):
    def es_satisfecha_por(self, candidato: OperacionDelProfesor) -> bool:
        return bool(candidato.lineas)


class ServiciosHabilitados(Especificacion[OperacionDelProfesor]):
    def es_satisfecha_por(self, candidato: OperacionDelProfesor) -> bool:
        return all(linea.habilitado for linea in candidato.lineas)


class Autorizado(Especificacion[OperacionDelProfesor]):
    def es_satisfecha_por(self, candidato: OperacionDelProfesor) -> bool:
        return candidato.autorizado


class EsPreferente(Especificacion[OperacionDelProfesor]):
    def es_satisfecha_por(self, candidato: OperacionDelProfesor) -> bool:
        return candidato.actor_preferente


class TotalAlMenos(Especificacion[OperacionDelProfesor]):
    def __init__(self, minimo: Decimal) -> None:
        self._minimo = minimo

    def es_satisfecha_por(self, candidato: OperacionDelProfesor) -> bool:
        return candidato.total >= self._minimo


class PromocionActiva(Especificacion[OperacionDelProfesor]):
    def es_satisfecha_por(self, candidato: OperacionDelProfesor) -> bool:
        return candidato.promocion_activa


PUEDE_PROCESARSE = ActorActivo() & TieneDetalle() & Autorizado()
BENEFICIO_REFERENCIA = (
    EsPreferente() & TotalAlMenos(MINIMO_DEL_BENEFICIO) & ~PromocionActiva()
)
VALIDAR_OPERACION = TieneDetalle() & ServiciosHabilitados() & Autorizado()
