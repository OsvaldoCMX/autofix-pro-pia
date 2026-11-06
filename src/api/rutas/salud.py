"""Salud del servicio: la usan Render y Docker Compose (ADR-010, ADR-011)."""
from __future__ import annotations

from fastapi import APIRouter

from api.esquemas.comunes import ModeloDeSalida

router = APIRouter(tags=["Sistema"])


class RespuestaDeSalud(ModeloDeSalida):
    estado: str


@router.get("/health", summary="Salud del servicio")
def salud() -> RespuestaDeSalud:
    return RespuestaDeSalud(estado="ok")
