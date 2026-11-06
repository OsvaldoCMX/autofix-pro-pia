"""Entrega del vehículo y cierre de la orden (US-024, CA-041 a CA-043)."""
from __future__ import annotations

from fastapi import APIRouter

from api.dependencias import ContenedorDeLaApp
from api.esquemas.comunes import errores
from api.esquemas.entrega import EntregaRegistrada
from api.seguridad import SOLO_ASESOR
from application.comandos import EntregarSinReparacion, RegistrarEntrega
from application.resultados import ResultadoDeEntrega

router = APIRouter(prefix="/api", tags=["Entrega"], dependencies=[SOLO_ASESOR])


@router.post(
    "/ordenes/{numero}/entrega",
    response_model=EntregaRegistrada,
    summary="Entregar el vehículo y cerrar la orden",
    responses=errores(401, 403, 404, 409),
)
def entregar(numero: str, contenedor: ContenedorDeLaApp) -> ResultadoDeEntrega:
    return contenedor.entrega().entregar(RegistrarEntrega(numero))


@router.post(
    "/ordenes/{numero}/entrega-sin-reparacion",
    response_model=EntregaRegistrada,
    summary="Entregar sin reparación tras un rechazo total",
    responses=errores(401, 403, 404, 409),
)
def entregar_sin_reparacion(numero: str, contenedor: ContenedorDeLaApp) -> ResultadoDeEntrega:
    return contenedor.entrega().entregar_sin_reparacion(EntregarSinReparacion(numero))
