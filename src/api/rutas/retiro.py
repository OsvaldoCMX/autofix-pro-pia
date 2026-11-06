"""Retiro anticipado con Nota de Responsabilidad y reactivación (US-013, CA-024, CA-025)."""
from __future__ import annotations

from fastapi import APIRouter, status

from api.dependencias import ContenedorDeLaApp
from api.errores import FuncionNoImplementada
from api.esquemas.comunes import EstadoDeLaOrden, errores
from api.esquemas.retiro import NotaDeResponsabilidad
from api.seguridad import SOLO_ASESOR
from application.comandos import ConfirmarFirmaDeNota, ReactivarOrden, RegistrarSalida
from application.resultados import ResultadoDeEstado, ResultadoDeNota

router = APIRouter(prefix="/api", tags=["Retiro anticipado"], dependencies=[SOLO_ASESOR])


@router.post(
    "/ordenes/{numero}/retiro",
    response_model=NotaDeResponsabilidad,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar la salida del vehículo y generar la Nota de Responsabilidad",
    responses=errores(401, 403, 404, 409),
)
def registrar_salida(numero: str, contenedor: ContenedorDeLaApp) -> ResultadoDeNota:
    return contenedor.retiro().registrar_salida(RegistrarSalida(numero))


@router.get(
    "/ordenes/{numero}/nota-de-responsabilidad/pdf",
    summary="PDF de la Nota de Responsabilidad (P2)",
    responses=errores(401, 403, 404, 409, 501),
)
def pdf_de_nota(numero: str) -> None:
    raise FuncionNoImplementada("El PDF de la Nota de Responsabilidad todavía no está disponible.")


@router.post(
    "/ordenes/{numero}/retiro/firma",
    response_model=EstadoDeLaOrden,
    summary="Confirmar la firma de la nota",
    responses=errores(401, 403, 404, 409),
)
def confirmar_firma(numero: str, contenedor: ContenedorDeLaApp) -> ResultadoDeEstado:
    return contenedor.retiro().confirmar_firma(ConfirmarFirmaDeNota(numero))


@router.post(
    "/ordenes/{numero}/reactivacion",
    response_model=EstadoDeLaOrden,
    summary="Reactivar la orden cuando el vehículo regresa",
    responses=errores(401, 403, 404, 409),
)
def reactivar(numero: str, contenedor: ContenedorDeLaApp) -> ResultadoDeEstado:
    return contenedor.retiro().reactivar(ReactivarOrden(numero))
