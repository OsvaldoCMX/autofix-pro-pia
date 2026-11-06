"""Esquemas de la asignación y ejecución de los trabajos (US-006, US-008, US-020)."""
from __future__ import annotations

from typing import Annotated

from fastapi import Path

from api.esquemas.comunes import (
    ENTERO_MAXIMO,
    EnteroPositivo,
    ModeloDeEntrada,
    ModeloDeSalida,
    TextoDeIdentificador,
)

IdEnLaRuta = Annotated[int, Path(ge=1, le=ENTERO_MAXIMO)]


class AsignacionDeTrabajos(ModeloDeEntrada):
    ids_trabajos: list[EnteroPositivo]
    tecnico: TextoDeIdentificador


class TrabajosAsignados(ModeloDeSalida):
    numero_orden: str
    estado: str
    ids_trabajos: list[int]
    tecnico: str


class TrabajoActualizado(ModeloDeSalida):
    numero_orden: str
    id_trabajo: int
    estado_trabajo: str
    estado_orden: str
