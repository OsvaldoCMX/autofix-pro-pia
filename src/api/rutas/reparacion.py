"""Asignar, iniciar y completar los trabajos autorizados (US-006, US-008, US-020)."""
from __future__ import annotations

from fastapi import APIRouter

from api.dependencias import ContenedorDeLaApp
from api.esquemas.comunes import errores
from api.esquemas.reparacion import (
    AsignacionDeTrabajos,
    IdEnLaRuta,
    TrabajoActualizado,
    TrabajosAsignados,
)
from api.seguridad import SOLO_ASESOR, Tecnico
from application.comandos import AsignarTrabajos, CompletarTrabajo, IniciarTrabajo
from application.resultados import ResultadoDeAsignacion, ResultadoDeTrabajo

router = APIRouter(prefix="/api", tags=["Reparación"])


@router.post(
    "/ordenes/{numero}/asignacion-trabajos",
    response_model=TrabajosAsignados,
    summary="Asignar trabajos autorizados a un técnico",
    dependencies=[SOLO_ASESOR],
    responses=errores(400, 401, 403, 404, 409, 422),
)
def asignar_trabajos(
    numero: str, datos: AsignacionDeTrabajos, contenedor: ContenedorDeLaApp
) -> ResultadoDeAsignacion:
    comando = AsignarTrabajos(numero, tuple(datos.ids_trabajos), datos.tecnico)
    return contenedor.reparacion().asignar_trabajos(comando)


@router.post(
    "/ordenes/{numero}/trabajos/{id}/inicio",
    response_model=TrabajoActualizado,
    summary="Pasar un trabajo a «En Progreso»",
    responses=errores(401, 403, 404, 409, 422),
)
def iniciar_trabajo(
    numero: str, id: IdEnLaRuta, tecnico: Tecnico, contenedor: ContenedorDeLaApp
) -> ResultadoDeTrabajo:
    comando = IniciarTrabajo(numero, id, tecnico.id_empleado)
    return contenedor.reparacion().iniciar_trabajo(comando)


@router.post(
    "/ordenes/{numero}/trabajos/{id}/completado",
    response_model=TrabajoActualizado,
    summary="Pasar un trabajo a «Completado»",
    responses=errores(401, 403, 404, 409, 422),
)
def completar_trabajo(
    numero: str, id: IdEnLaRuta, tecnico: Tecnico, contenedor: ContenedorDeLaApp
) -> ResultadoDeTrabajo:
    comando = CompletarTrabajo(numero, id, tecnico.id_empleado)
    return contenedor.reparacion().completar_trabajo(comando)
