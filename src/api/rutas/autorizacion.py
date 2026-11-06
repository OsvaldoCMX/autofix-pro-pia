"""Registrar la decisión del cliente o del Responsable de Flotilla (US-006, US-009, US-016)."""
from __future__ import annotations

from fastapi import APIRouter

from api.dependencias import ContenedorDeLaApp
from api.esquemas.autorizacion import DatosDeDecision, DecisionRegistrada
from api.esquemas.comunes import errores
from api.seguridad import SOLO_ASESOR
from application.resultados import ResultadoDeDecision

router = APIRouter(prefix="/api", tags=["Autorización"])


@router.post(
    "/cotizaciones/{id}/decision",
    response_model=DecisionRegistrada,
    summary="Registrar la decisión del cliente o del Responsable de Flotilla",
    dependencies=[SOLO_ASESOR],
    responses=errores(400, 401, 403, 404, 409, 422),
)
def registrar_decision(
    id: str, datos: DatosDeDecision, contenedor: ContenedorDeLaApp
) -> ResultadoDeDecision:
    return contenedor.autorizacion().registrar_decision(datos.a_comando(id))
