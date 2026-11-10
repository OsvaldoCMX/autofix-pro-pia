"""Inicio de sesión de la página: quién es el empleado de la clave de acceso (ADR-017)."""
from __future__ import annotations

from fastapi import APIRouter

from api.esquemas.comunes import errores
from api.esquemas.sesion import SesionDelEmpleado
from api.seguridad import EmpleadoDeLaSesion

router = APIRouter(prefix="/api", tags=["Sesión"])


@router.get(
    "/sesion",
    response_model=SesionDelEmpleado,
    summary="Nombre y puesto del empleado de la clave de acceso",
    responses=errores(401, 403),
)
def consultar_sesion(empleado: EmpleadoDeLaSesion) -> SesionDelEmpleado:
    return SesionDelEmpleado.del_empleado(empleado)
