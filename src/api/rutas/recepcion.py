"""Recepción del vehículo (US-001 a US-003, US-016)."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, UploadFile, status

from api.dependencias import ContenedorDeLaApp
from api.errores import FuncionNoImplementada
from api.esquemas.comunes import errores
from api.esquemas.recepcion import (
    ClienteCorregido,
    ClienteEncontrado,
    ClienteRegistrado,
    DatosDeContacto,
    ExpedienteDeOrden,
    NuevaOrden,
    NuevoCliente,
    OrdenRegistrada,
    VehiculoEncontrado,
)
from api.seguridad import SOLO_ASESOR, Asesor, requiere_rol
from application.comandos import CorregirCliente
from application.consultas.consultas import (
    BuscarClientes,
    BuscarVehiculoPorPlacas,
    ConsultarExpedienteDeOrden,
)
from application.consultas.vistas import (
    ClienteVista,
    ExpedienteDeOrdenVista,
    VehiculoConClienteVista,
)
from application.resultados import ResultadoDeCliente
from domain.clientes.cliente import TipoCliente
from domain.empleados.empleado import RolDeEmpleado

router = APIRouter(prefix="/api", tags=["Recepción"])

_LEEN_EL_EXPEDIENTE = Depends(
    requiere_rol(
        RolDeEmpleado.ASESOR, RolDeEmpleado.GERENTE, RolDeEmpleado.TECNICO, RolDeEmpleado.CAJA
    )
)


@router.get(
    "/vehiculos/{placas}",
    response_model=VehiculoEncontrado,
    summary="Buscar vehículo y cliente por placas",
    dependencies=[SOLO_ASESOR],
    responses=errores(401, 403, 404, 422),
)
def buscar_vehiculo(placas: str, contenedor: ContenedorDeLaApp) -> VehiculoConClienteVista:
    return contenedor.buscar_vehiculo_por_placas().ejecutar(BuscarVehiculoPorPlacas(placas))


@router.get(
    "/clientes",
    response_model=list[ClienteEncontrado],
    summary="Buscar la empresa de flotilla y su Responsable",
    dependencies=[SOLO_ASESOR],
    responses=errores(401, 403, 422),
)
def buscar_clientes(
    contenedor: ContenedorDeLaApp, tipo: TipoCliente | None = None, empresa: str | None = None
) -> list[ClienteVista]:
    return contenedor.buscar_clientes().ejecutar(BuscarClientes(tipo, empresa))


@router.post(
    "/clientes",
    response_model=ClienteRegistrado,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar cliente particular o de flotilla",
    dependencies=[SOLO_ASESOR],
    responses=errores(400, 401, 403, 422),
)
def registrar_cliente(datos: NuevoCliente, contenedor: ContenedorDeLaApp) -> ResultadoDeCliente:
    return contenedor.recepcion().registrar_cliente(datos.a_comando())


@router.put(
    "/clientes/{id}",
    response_model=ClienteCorregido,
    summary="Corregir el nombre, el teléfono o el correo del cliente",
    dependencies=[SOLO_ASESOR],
    responses=errores(400, 401, 403, 404, 422),
)
def corregir_cliente(
    id: str, datos: DatosDeContacto, contenedor: ContenedorDeLaApp
) -> ResultadoDeCliente:
    comando = CorregirCliente(id, datos.nombre, datos.telefono, datos.correo)
    return contenedor.recepcion().corregir_cliente(comando)


@router.post(
    "/ordenes",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar la orden de servicio",
    responses=errores(400, 401, 403, 404, 409, 422),
)
def registrar_orden(
    datos: NuevaOrden, asesor: Asesor, contenedor: ContenedorDeLaApp
) -> OrdenRegistrada:
    resultado = contenedor.recepcion().registrar_orden(datos.a_comando(asesor.id_empleado))
    return OrdenRegistrada(
        **asdict(resultado),
        mensaje=f"Orden {resultado.numero_orden} registrada correctamente.",
    )


@router.post(
    "/ordenes/{numero}/fotos",
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar foto de daños (P2)",
    dependencies=[SOLO_ASESOR],
    responses=errores(401, 403, 404, 422, 501),
)
def adjuntar_foto(numero: str, archivo: UploadFile) -> None:
    raise FuncionNoImplementada("Las fotos de daños todavía no están disponibles.")


@router.get(
    "/ordenes/{numero}",
    response_model=ExpedienteDeOrden,
    summary="Expediente completo de la orden",
    dependencies=[_LEEN_EL_EXPEDIENTE],
    responses=errores(401, 403, 404, 422),
)
def consultar_expediente(numero: str, contenedor: ContenedorDeLaApp) -> ExpedienteDeOrdenVista:
    return contenedor.consultar_expediente().ejecutar(ConsultarExpedienteDeOrden(numero))
