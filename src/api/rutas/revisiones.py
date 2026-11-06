"""Revisión de plazos de 3 días hábiles y 48 horas; la llama un workflow programado (ADR-015)."""
from __future__ import annotations

from fastapi import APIRouter

from api.dependencias import ContenedorDeLaApp
from api.esquemas.comunes import errores
from api.esquemas.revisiones import RevisionDePlazos
from api.seguridad import SOLO_SISTEMA
from application.resultados import ResultadoDeRevisionDePlazos

router = APIRouter(prefix="/api", tags=["Sistema"])


@router.post(
    "/revisiones/plazos",
    response_model=RevisionDePlazos,
    summary="Revisión de plazos",
    dependencies=[SOLO_SISTEMA],
    responses=errores(401, 403),
)
def revisar_plazos(contenedor: ContenedorDeLaApp) -> ResultadoDeRevisionDePlazos:
    return contenedor.revision_de_plazos().revisar()
