"""Composition Root: único lugar de `api` que decide qué implementación se usa (ADR-004).

Cada método entrega un objeto nuevo con su propia Unidad de Trabajo: FastAPI atiende las peticiones
en varios hilos y una Unidad de Trabajo guarda el estado de una sola operación.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, TypeVar

from fastapi import Depends, Request
from sqlalchemy import Engine

from api.seguridad import DirectorioDeTokens
from application.consultas.consultas import (
    ManejadorBuscarClientes,
    ManejadorBuscarVehiculoPorPlacas,
    ManejadorConsultarCotizacion,
    ManejadorConsultarEstadoDeOrden,
    ManejadorConsultarExpedienteDeOrden,
    ManejadorConsultarIngresosDelDia,
    ManejadorConsultarPanelDelTecnico,
    ManejadorListarAlertas,
    ManejadorListarCotizacionesPendientesDeAprobacion,
    ManejadorListarOrdenes,
    ManejadorListarSolicitudesPendientes,
    ManejadorListarTecnicos,
)
from application.consultas.lector import LectorDeOrdenes
from application.manejadores.alertas import ManejadoresDeAlertas
from application.puertos import PublicadorDeEventos, Reloj
from application.servicios.servicio_de_aprobacion_gerencial import ServicioDeAprobacionGerencial
from application.servicios.servicio_de_autorizacion import ServicioDeAutorizacion
from application.servicios.servicio_de_caja import ServicioDeCaja
from application.servicios.servicio_de_cancelacion import ServicioDeCancelacion
from application.servicios.servicio_de_cotizacion import ServicioDeCotizacion
from application.servicios.servicio_de_diagnostico import ServicioDeDiagnostico
from application.servicios.servicio_de_entrega import ServicioDeEntrega
from application.servicios.servicio_de_recepcion import ServicioDeRecepcion
from application.servicios.servicio_de_refacciones import ServicioDeRefacciones
from application.servicios.servicio_de_reparacion import ServicioDeReparacion
from application.servicios.servicio_de_retiro import ServicioDeRetiro
from application.servicios.servicio_de_revision_de_plazos import ServicioDeRevisionDePlazos
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.empleados.empleado import Empleado, RolDeEmpleado
from infrastructure.base_de_datos.lector import LectorDeOrdenesSqlAlchemy
from infrastructure.base_de_datos.motor import crear_motor
from infrastructure.base_de_datos.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from infrastructure.config import Configuracion
from infrastructure.eventos.publicador_en_proceso import PublicadorEnProceso
from infrastructure.memoria.almacen import AlmacenEnMemoria
from infrastructure.memoria.lector import LectorEnMemoria
from infrastructure.memoria.unidad_de_trabajo import UnidadDeTrabajoEnMemoria
from infrastructure.reloj import RelojDelSistema

S = TypeVar("S")

# Tabla de decisiones-tecnicas.md §6; las mismas filas de database/02_datos_iniciales.sql.
EMPLEADOS_POR_VARIABLE = {
    "TOKEN_ASESOR": Empleado("EMP-001", "Laura Méndez", RolDeEmpleado.ASESOR),
    "TOKEN_TECNICO": Empleado("EMP-002", "Carlos Ruiz", RolDeEmpleado.TECNICO),
    "TOKEN_TECNICO_2": Empleado("EMP-003", "Diego Salinas", RolDeEmpleado.TECNICO),
    "TOKEN_GERENTE": Empleado("EMP-004", "Patricia Garza", RolDeEmpleado.GERENTE),
    "TOKEN_COMPRAS": Empleado("EMP-005", "Jorge Treviño", RolDeEmpleado.COMPRAS),
    "TOKEN_CAJA": Empleado("EMP-006", "Sofía Leal", RolDeEmpleado.CAJA),
}
VARIABLE_DE_SISTEMA = "TOKEN_SISTEMA"


class ConfiguracionIncompleta(Exception):
    """La aplicación no debe arrancar con esta configuración."""


@dataclass(frozen=True)
class Contenedor:
    configuracion: Configuracion
    fabrica_de_uow: Callable[[], UnidadDeTrabajo]
    lector: LectorDeOrdenes
    reloj: Reloj
    publicador: PublicadorDeEventos
    directorio_de_tokens: DirectorioDeTokens

    def _servicio(self, tipo: type[S]) -> S:
        return tipo(self.fabrica_de_uow(), self.reloj, self.publicador)

    # ---------------------------------------------------------------- casos de uso
    def recepcion(self) -> ServicioDeRecepcion:
        return self._servicio(ServicioDeRecepcion)

    def cancelacion(self) -> ServicioDeCancelacion:
        return self._servicio(ServicioDeCancelacion)

    def diagnostico(self) -> ServicioDeDiagnostico:
        return self._servicio(ServicioDeDiagnostico)

    def cotizacion(self) -> ServicioDeCotizacion:
        return self._servicio(ServicioDeCotizacion)

    def aprobacion_gerencial(self) -> ServicioDeAprobacionGerencial:
        return self._servicio(ServicioDeAprobacionGerencial)

    def autorizacion(self) -> ServicioDeAutorizacion:
        return self._servicio(ServicioDeAutorizacion)

    def reparacion(self) -> ServicioDeReparacion:
        return self._servicio(ServicioDeReparacion)

    def refacciones(self) -> ServicioDeRefacciones:
        return self._servicio(ServicioDeRefacciones)

    def retiro(self) -> ServicioDeRetiro:
        return self._servicio(ServicioDeRetiro)

    def caja(self) -> ServicioDeCaja:
        return self._servicio(ServicioDeCaja)

    def entrega(self) -> ServicioDeEntrega:
        return self._servicio(ServicioDeEntrega)

    def revision_de_plazos(self) -> ServicioDeRevisionDePlazos:
        return ServicioDeRevisionDePlazos(self.fabrica_de_uow(), self.lector, self.reloj)

    # ---------------------------------------------------------------- consultas
    def buscar_vehiculo_por_placas(self) -> ManejadorBuscarVehiculoPorPlacas:
        return ManejadorBuscarVehiculoPorPlacas(self.lector)

    def buscar_clientes(self) -> ManejadorBuscarClientes:
        return ManejadorBuscarClientes(self.lector)

    def listar_tecnicos(self) -> ManejadorListarTecnicos:
        return ManejadorListarTecnicos(self.lector)

    def consultar_panel_del_tecnico(self) -> ManejadorConsultarPanelDelTecnico:
        return ManejadorConsultarPanelDelTecnico(self.lector)

    def listar_solicitudes_pendientes(self) -> ManejadorListarSolicitudesPendientes:
        return ManejadorListarSolicitudesPendientes(self.lector, self.reloj)

    def listar_cotizaciones_por_aprobar(
        self,
    ) -> ManejadorListarCotizacionesPendientesDeAprobacion:
        return ManejadorListarCotizacionesPendientesDeAprobacion(self.lector)

    def consultar_cotizacion(self) -> ManejadorConsultarCotizacion:
        return ManejadorConsultarCotizacion(self.lector)

    def consultar_expediente(self) -> ManejadorConsultarExpedienteDeOrden:
        return ManejadorConsultarExpedienteDeOrden(self.lector)

    def listar_ordenes(self) -> ManejadorListarOrdenes:
        return ManejadorListarOrdenes(self.lector)

    def consultar_ingresos_del_dia(self) -> ManejadorConsultarIngresosDelDia:
        return ManejadorConsultarIngresosDelDia(self.lector, self.reloj)

    def consultar_estado_de_orden(self) -> ManejadorConsultarEstadoDeOrden:
        return ManejadorConsultarEstadoDeOrden(self.lector)

    def listar_alertas(self) -> ManejadorListarAlertas:
        return ManejadorListarAlertas(self.lector)


def crear_contenedor(
    configuracion: Configuracion | None = None,
    reloj: Reloj | None = None,
    motor: Engine | None = None,
) -> Contenedor:
    """`motor` permite a las pruebas compartir la base que ya prepararon."""
    configuracion = configuracion or Configuracion.desde_entorno()
    fabrica_de_uow, lector = _adaptadores(configuracion, motor)
    return Contenedor(
        configuracion,
        fabrica_de_uow,
        lector,
        reloj or RelojDelSistema(configuracion.zona_horaria),
        _publicador(fabrica_de_uow),
        _directorio_de_tokens(configuracion),
    )


def _adaptadores(
    configuracion: Configuracion, motor: Engine | None
) -> tuple[Callable[[], UnidadDeTrabajo], LectorDeOrdenes]:
    if motor is None and configuracion.database_url:
        motor = crear_motor(configuracion.database_url)
    if motor is not None:
        return (lambda: UnidadDeTrabajoSqlAlchemy(motor)), LectorDeOrdenesSqlAlchemy(motor)
    if configuracion.app_env == "produccion":
        raise ConfiguracionIncompleta(
            "Falta DATABASE_URL: en producción la aplicación no arranca sin base de datos."
        )
    almacen = AlmacenEnMemoria(EMPLEADOS_POR_VARIABLE.values())
    return (lambda: UnidadDeTrabajoEnMemoria(almacen)), LectorEnMemoria(almacen)


def _publicador(fabrica_de_uow: Callable[[], UnidadDeTrabajo]) -> PublicadorDeEventos:
    publicador = PublicadorEnProceso()
    for tipo, manejador in ManejadoresDeAlertas(fabrica_de_uow).suscripciones().items():
        publicador.suscribir(tipo, manejador)
    return publicador


def _directorio_de_tokens(configuracion: Configuracion) -> DirectorioDeTokens:
    tokens = configuracion.tokens
    return DirectorioDeTokens(
        {
            tokens[variable]: empleado
            for variable, empleado in EMPLEADOS_POR_VARIABLE.items()
            if variable in tokens
        },
        tokens.get(VARIABLE_DE_SISTEMA),
    )


def obtener_contenedor(request: Request) -> Contenedor:
    return request.app.state.contenedor


ContenedorDeLaApp = Annotated[Contenedor, Depends(obtener_contenedor)]
