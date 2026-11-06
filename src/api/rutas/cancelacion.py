"""Cancelación de la orden antes de la cotización (US-025)."""
from __future__ import annotations

from fastapi import APIRouter

from api.dependencias import ContenedorDeLaApp
from api.esquemas.cancelacion import DatosDeCancelacion
from api.esquemas.comunes import EstadoDeLaOrden, errores
from api.seguridad import Asesor
from application.comandos import CancelarOrden
from application.resultados import ResultadoDeEstado

router = APIRouter(prefix="/api", tags=["Cancelación"])


@router.post(
    "/ordenes/{numero}/cancelacion",
    response_model=EstadoDeLaOrden,
    summary="Cancelar la orden con motivo",
    responses=errores(400, 401, 403, 404, 409, 422),
)
def cancelar(
    numero: str, datos: DatosDeCancelacion, asesor: Asesor, contenedor: ContenedorDeLaApp
) -> ResultadoDeEstado:
    comando = CancelarOrden(numero, datos.motivo, asesor.id_empleado)
    return contenedor.cancelacion().cancelar(comando)
