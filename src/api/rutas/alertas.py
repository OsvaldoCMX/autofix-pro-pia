"""Alertas internas del empleado que hace la petición (modelo-de-dominio.md §6)."""
from __future__ import annotations

from fastapi import APIRouter

from api.dependencias import ContenedorDeLaApp
from api.esquemas.alertas import AlertaDelEmpleado
from api.esquemas.comunes import errores
from api.seguridad import CualquierEmpleado
from application.consultas.consultas import ListarAlertas
from application.puertos import AlertaInterna

router = APIRouter(prefix="/api", tags=["Consultas"])


@router.get(
    "/alertas",
    response_model=list[AlertaDelEmpleado],
    summary="Alertas internas del empleado",
    responses=errores(401, 403),
)
def listar_alertas(
    empleado: CualquierEmpleado, contenedor: ContenedorDeLaApp
) -> list[AlertaInterna]:
    consulta = ListarAlertas(empleado.id_empleado, empleado.rol)
    return contenedor.listar_alertas().ejecutar(consulta)
