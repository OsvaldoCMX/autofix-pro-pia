"""Generar, presentar, revisar, ajustar, corregir y recontactar cotizaciones (US-004 a US-026)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from api.dependencias import ContenedorDeLaApp
from api.errores import FuncionNoImplementada
from api.esquemas.comunes import errores
from api.esquemas.cotizaciones import (
    CotizacionDetallada,
    CotizacionPorAprobar,
    CotizacionRegistrada,
    DatosDeCorreccion,
    DatosDeCotizacion,
    DatosDeRevision,
    RecontactoRegistrado,
)
from api.seguridad import SOLO_ASESOR, SOLO_GERENTE, Asesor, requiere_rol
from application.comandos import (
    AjustarCotizacion,
    CorregirCotizacion,
    GenerarCotizacion,
    PresentarCotizacion,
    RegistrarRecontacto,
    RevisarCotizacion,
)
from application.consultas.consultas import (
    ConsultarCotizacion,
    ListarCotizacionesPendientesDeAprobacion,
)
from application.consultas.vistas import CotizacionPendienteVista, CotizacionVista
from application.resultados import ResultadoDeCotizacion, ResultadoDeRecontacto
from domain.empleados.empleado import RolDeEmpleado

router = APIRouter(prefix="/api", tags=["Cotización"])

_LEEN_LA_COTIZACION = Depends(requiere_rol(RolDeEmpleado.ASESOR, RolDeEmpleado.GERENTE))


@router.post(
    "/ordenes/{numero}/cotizaciones",
    response_model=CotizacionRegistrada,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    summary="Generar la cotización inicial (v.1)",
    dependencies=[SOLO_ASESOR],
    responses=errores(400, 401, 403, 404, 409, 422),
)
def generar_inicial(
    numero: str, datos: DatosDeCotizacion, contenedor: ContenedorDeLaApp
) -> ResultadoDeCotizacion:
    comando = GenerarCotizacion(numero, datos.a_trabajos())
    return contenedor.cotizacion().generar_inicial(comando)


@router.post(
    "/ordenes/{numero}/cotizaciones-adicionales",
    response_model=CotizacionRegistrada,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    summary="Generar una cotización adicional (v.2, v.3…)",
    dependencies=[SOLO_ASESOR],
    responses=errores(400, 401, 403, 404, 409, 422),
)
def generar_adicional(
    numero: str, datos: DatosDeCotizacion, contenedor: ContenedorDeLaApp
) -> ResultadoDeCotizacion:
    comando = GenerarCotizacion(numero, datos.a_trabajos())
    return contenedor.cotizacion().generar_adicional(comando)


@router.get(
    "/cotizaciones/{id}",
    response_model=CotizacionDetallada,
    summary="Detalle de la cotización",
    dependencies=[_LEEN_LA_COTIZACION],
    responses=errores(401, 403, 404, 422),
)
def consultar_cotizacion(id: str, contenedor: ContenedorDeLaApp) -> CotizacionVista:
    return contenedor.consultar_cotizacion().ejecutar(ConsultarCotizacion(id))


@router.get(
    "/cotizaciones/{id}/pdf",
    summary="PDF de la cotización (P2)",
    dependencies=[SOLO_ASESOR],
    responses=errores(401, 403, 404, 422, 501),
)
def pdf_de_cotizacion(id: str) -> None:
    raise FuncionNoImplementada("El PDF de la cotización todavía no está disponible.")


@router.post(
    "/cotizaciones/{id}/presentacion",
    response_model=CotizacionRegistrada,
    response_model_exclude_none=True,
    summary="Marcar como presentada (inicia las 48 h)",
    dependencies=[SOLO_ASESOR],
    responses=errores(401, 403, 404, 409, 422),
)
def presentar(id: str, contenedor: ContenedorDeLaApp) -> ResultadoDeCotizacion:
    return contenedor.cotizacion().presentar(PresentarCotizacion(id))


@router.post(
    "/cotizaciones/{id}/revision-gerencial",
    response_model=CotizacionRegistrada,
    response_model_exclude_none=True,
    summary="Aprobar o rechazar una cotización mayor a $15,000",
    dependencies=[SOLO_GERENTE],
    responses=errores(400, 401, 403, 404, 409, 422),
)
def revisar(
    id: str, datos: DatosDeRevision, contenedor: ContenedorDeLaApp
) -> ResultadoDeCotizacion:
    comando = RevisarCotizacion(id, datos.aprobada, datos.observaciones)
    return contenedor.aprobacion_gerencial().revisar(comando)


@router.put(
    "/cotizaciones/{id}/lineas",
    response_model=CotizacionRegistrada,
    response_model_exclude_none=True,
    summary="Guardar la cotización ajustada según el Gerente",
    dependencies=[SOLO_ASESOR],
    responses=errores(400, 401, 403, 404, 409, 422),
)
def ajustar(
    id: str, datos: DatosDeCotizacion, contenedor: ContenedorDeLaApp
) -> ResultadoDeCotizacion:
    comando = AjustarCotizacion(id, datos.a_trabajos())
    return contenedor.cotizacion().ajustar(comando)


@router.post(
    "/cotizaciones/{id}/correcciones",
    response_model=CotizacionRegistrada,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    summary="Corregir una cotización que espera al Gerente o al cliente",
    responses=errores(400, 401, 403, 404, 409, 422),
)
def corregir(
    id: str, datos: DatosDeCorreccion, asesor: Asesor, contenedor: ContenedorDeLaApp
) -> ResultadoDeCotizacion:
    comando = CorregirCotizacion(id, datos.a_trabajos(), datos.motivo, asesor.id_empleado)
    return contenedor.cotizacion().corregir(comando)


@router.post(
    "/cotizaciones/{id}/recontactos",
    response_model=RecontactoRegistrado,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar el recontacto al cliente (48 h)",
    responses=errores(401, 403, 404, 409, 422),
)
def registrar_recontacto(
    id: str, asesor: Asesor, contenedor: ContenedorDeLaApp
) -> ResultadoDeRecontacto:
    comando = RegistrarRecontacto(id, asesor.id_empleado)
    return contenedor.cotizacion().registrar_recontacto(comando)


@router.get(
    "/gerencia/cotizaciones-por-aprobar",
    response_model=list[CotizacionPorAprobar],
    summary="Cotizaciones en «Pendiente de Aprobación Gerencial»",
    dependencies=[SOLO_GERENTE],
    responses=errores(401, 403),
)
def cotizaciones_por_aprobar(contenedor: ContenedorDeLaApp) -> list[CotizacionPendienteVista]:
    consulta = ListarCotizacionesPendientesDeAprobacion()
    return contenedor.listar_cotizaciones_por_aprobar().ejecutar(consulta)
