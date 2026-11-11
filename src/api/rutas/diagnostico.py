"""Asignación del técnico, diagnóstico, fallas adicionales y panel (US-007, US-019, US-020)."""
from __future__ import annotations

from fastapi import APIRouter, status

from api.dependencias import ContenedorDeLaApp
from api.esquemas.comunes import EstadoDeLaOrden, errores
from api.esquemas.diagnostico import (
    AsignacionDeDiagnostico,
    DatosDeDiagnostico,
    DatosDeFallaAdicional,
    DiagnosticoRegistrado,
    FallaAdicionalRegistrada,
    OrdenDelPanel,
    TecnicoDelTaller,
)
from api.seguridad import SOLO_ASESOR, Tecnico
from application.comandos import (
    AsignarTecnicoParaDiagnostico,
    RegistrarDiagnostico,
    ReportarFallaAdicional,
)
from application.consultas.consultas import ConsultarPanelDelTecnico, ListarTecnicos
from application.consultas.vistas import OrdenDelPanelVista, TecnicoVista
from application.resultados import (
    ResultadoDeDiagnostico,
    ResultadoDeEstado,
    ResultadoDeFallaAdicional,
)

router = APIRouter(prefix="/api", tags=["Diagnóstico"])


@router.post(
    "/ordenes/{numero}/asignacion-diagnostico",
    response_model=EstadoDeLaOrden,
    summary="Asignar técnico para el diagnóstico",
    dependencies=[SOLO_ASESOR],
    responses=errores(400, 401, 403, 404, 409, 422),
)
def asignar_tecnico(
    numero: str, datos: AsignacionDeDiagnostico, contenedor: ContenedorDeLaApp
) -> ResultadoDeEstado:
    comando = AsignarTecnicoParaDiagnostico(numero, datos.tecnico)
    return contenedor.diagnostico().asignar_tecnico(comando)


@router.post(
    "/ordenes/{numero}/diagnostico",
    response_model=DiagnosticoRegistrado,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar el diagnóstico",
    responses=errores(400, 401, 403, 404, 409, 422),
)
def registrar_diagnostico(
    numero: str, datos: DatosDeDiagnostico, tecnico: Tecnico, contenedor: ContenedorDeLaApp
) -> ResultadoDeDiagnostico:
    comando = RegistrarDiagnostico(
        numero, tecnico.id_empleado, datos.fallas, datos.recomendaciones
    )
    return contenedor.diagnostico().registrar_diagnostico(comando)


@router.post(
    "/ordenes/{numero}/fallas-adicionales",
    response_model=FallaAdicionalRegistrada,
    status_code=status.HTTP_201_CREATED,
    summary="Reportar una falla adicional",
    responses=errores(400, 401, 403, 404, 409, 422),
)
def reportar_falla_adicional(
    numero: str, datos: DatosDeFallaAdicional, tecnico: Tecnico, contenedor: ContenedorDeLaApp
) -> ResultadoDeFallaAdicional:
    comando = ReportarFallaAdicional(numero, tecnico.id_empleado, datos.descripcion)
    return contenedor.diagnostico().reportar_falla_adicional(comando)


@router.get(
    "/tecnicos",
    response_model=list[TecnicoDelTaller],
    summary="Técnicos del taller (clave y nombre) para asignarlos",
    dependencies=[SOLO_ASESOR],
    responses=errores(401, 403),
)
def listar_tecnicos(contenedor: ContenedorDeLaApp) -> list[TecnicoVista]:
    return contenedor.listar_tecnicos().ejecutar(ListarTecnicos())


@router.get(
    "/tecnicos/me/panel",
    response_model=list[OrdenDelPanel],
    summary="Órdenes y trabajos asignados, en orden de la fila",
    responses=errores(401, 403),
)
def consultar_panel(tecnico: Tecnico, contenedor: ContenedorDeLaApp) -> list[OrdenDelPanelVista]:
    consulta = ConsultarPanelDelTecnico(tecnico.id_empleado)
    return contenedor.consultar_panel_del_tecnico().ejecutar(consulta)
