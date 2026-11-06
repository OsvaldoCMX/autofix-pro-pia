"""Consultas del Gerente y consulta pública del cliente (US-017, US-018, US-021)."""
from __future__ import annotations

from fastapi import APIRouter

from api.dependencias import ContenedorDeLaApp
from api.esquemas.comunes import errores
from api.esquemas.consultas import EstadoParaElCliente, IngresosDelDia, OrdenResumida
from api.seguridad import SOLO_GERENTE
from application.consultas.consultas import (
    ConsultarEstadoDeOrden,
    ConsultarIngresosDelDia,
    ListarOrdenes,
)
from application.consultas.vistas import (
    EstadoDeOrdenVista,
    IngresosDelDiaVista,
    OrdenResumenVista,
)
from domain.ordenes.estados import EstadoOrden

router = APIRouter(prefix="/api", tags=["Consultas"])


@router.get(
    "/gerencia/ordenes",
    response_model=list[OrdenResumida],
    summary="Listado de órdenes abiertas y cerradas",
    dependencies=[SOLO_GERENTE],
    responses=errores(401, 403, 422),
)
def listar_ordenes(
    contenedor: ContenedorDeLaApp, estado: EstadoOrden | None = None
) -> list[OrdenResumenVista]:
    return contenedor.listar_ordenes().ejecutar(ListarOrdenes(estado))


@router.get(
    "/gerencia/ingresos-del-dia",
    response_model=IngresosDelDia,
    summary="Total de pagos de contado de hoy",
    dependencies=[SOLO_GERENTE],
    responses=errores(401, 403),
)
def ingresos_del_dia(contenedor: ContenedorDeLaApp) -> IngresosDelDiaVista:
    return contenedor.consultar_ingresos_del_dia().ejecutar(ConsultarIngresosDelDia())


@router.get(
    "/consulta-de-estado",
    response_model=EstadoParaElCliente,
    summary="Consulta pública del cliente (sin token)",
    responses=errores(404, 422),
)
def consulta_de_estado(
    orden: str, placas: str, contenedor: ContenedorDeLaApp
) -> EstadoDeOrdenVista:
    return contenedor.consultar_estado_de_orden().ejecutar(ConsultarEstadoDeOrden(orden, placas))
