"""Solicitudes de compra, llegada de refacciones y aviso al cliente (US-010 a US-012)."""
from __future__ import annotations

from fastapi import APIRouter, status

from api.dependencias import ContenedorDeLaApp
from api.esquemas.comunes import errores
from api.esquemas.refacciones import NuevaSolicitud, SolicitudActualizada, SolicitudPendiente
from api.esquemas.reparacion import IdEnLaRuta
from api.seguridad import SOLO_ASESOR, SOLO_COMPRAS, SOLO_TECNICO
from application.comandos import (
    RegistrarAvisoAlCliente,
    RegistrarLlegadaDeRefaccion,
    SolicitarRefaccion,
)
from application.consultas.consultas import ListarSolicitudesPendientes
from application.consultas.vistas import SolicitudPendienteVista
from application.resultados import ResultadoDeSolicitud

router = APIRouter(prefix="/api", tags=["Refacciones"])


@router.post(
    "/ordenes/{numero}/solicitudes-de-compra",
    response_model=SolicitudActualizada,
    status_code=status.HTTP_201_CREATED,
    summary="Crear solicitud de compra de una refacción no disponible",
    dependencies=[SOLO_TECNICO],
    responses=errores(400, 401, 403, 404, 409, 422),
)
def solicitar(
    numero: str, datos: NuevaSolicitud, contenedor: ContenedorDeLaApp
) -> ResultadoDeSolicitud:
    comando = SolicitarRefaccion(numero, datos.id_trabajo, datos.refaccion, datos.cantidad)
    return contenedor.refacciones().solicitar(comando)


@router.get(
    "/compras/solicitudes-pendientes",
    response_model=list[SolicitudPendiente],
    summary="Solicitudes «Solicitada» con días hábiles transcurridos",
    dependencies=[SOLO_COMPRAS],
    responses=errores(401, 403),
)
def solicitudes_pendientes(contenedor: ContenedorDeLaApp) -> list[SolicitudPendienteVista]:
    return contenedor.listar_solicitudes_pendientes().ejecutar(ListarSolicitudesPendientes())


@router.post(
    "/ordenes/{numero}/solicitudes-de-compra/{id}/llegada",
    response_model=SolicitudActualizada,
    summary="Registrar la llegada de la refacción",
    dependencies=[SOLO_COMPRAS],
    responses=errores(401, 403, 404, 409, 422),
)
def registrar_llegada(
    numero: str, id: IdEnLaRuta, contenedor: ContenedorDeLaApp
) -> ResultadoDeSolicitud:
    return contenedor.refacciones().registrar_llegada(RegistrarLlegadaDeRefaccion(numero, id))


@router.post(
    "/ordenes/{numero}/solicitudes-de-compra/{id}/aviso-al-cliente",
    response_model=SolicitudActualizada,
    summary="Registrar que se avisó al cliente del retraso",
    dependencies=[SOLO_ASESOR],
    responses=errores(401, 403, 404, 409, 422),
)
def registrar_aviso_al_cliente(
    numero: str, id: IdEnLaRuta, contenedor: ContenedorDeLaApp
) -> ResultadoDeSolicitud:
    comando = RegistrarAvisoAlCliente(numero, id)
    return contenedor.refacciones().registrar_aviso_al_cliente(comando)
