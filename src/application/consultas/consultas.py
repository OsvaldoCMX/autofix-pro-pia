"""Queries (CQRS) y sus manejadores (ADR-003). Solo leen: nunca modifican un Aggregate."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from application.consultas.lector import LectorDeOrdenes
from application.consultas.vistas import (
    ClienteVista,
    CotizacionPendienteVista,
    CotizacionVista,
    EstadoDeOrdenVista,
    ExpedienteDeOrdenVista,
    IngresosDelDiaVista,
    OrdenDelPanelVista,
    OrdenResumenVista,
    SolicitudPendienteVista,
    VehiculoConClienteVista,
)
from application.puertos import AlertaInterna, Reloj
from domain.clientes.cliente import TipoCliente
from domain.compartido.calendario import CalendarioHabil
from domain.compartido.errores import (
    CotizacionNoEncontrada,
    OrdenNoEncontrada,
    VehiculoNoEncontrado,
)
from domain.compartido.valores import Dinero, NumeroOrden, Placas
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes.estados import EstadoOrden

MENSAJE_SIN_COINCIDENCIA = (
    "No se encontró una orden con esos datos. "
    "Revise el número de orden y las placas e intente de nuevo."
)


# ------------------------------------------------------------------ recepción
@dataclass(frozen=True)
class BuscarVehiculoPorPlacas:
    placas: str


class ManejadorBuscarVehiculoPorPlacas:
    def __init__(self, lector: LectorDeOrdenes) -> None:
        self._lector = lector

    def ejecutar(self, consulta: BuscarVehiculoPorPlacas) -> VehiculoConClienteVista:
        placas = Placas(consulta.placas)
        vista = self._lector.vehiculo_por_placas(placas)
        if vista is None:
            raise VehiculoNoEncontrado(
                f"No hay un vehículo con las placas {placas}. "
                "Revíselas o registre el vehículo."
            )
        return vista


@dataclass(frozen=True)
class BuscarClientes:
    tipo: TipoCliente | None = None
    empresa: str | None = None


class ManejadorBuscarClientes:
    def __init__(self, lector: LectorDeOrdenes) -> None:
        self._lector = lector

    def ejecutar(self, consulta: BuscarClientes) -> list[ClienteVista]:
        return self._lector.clientes(consulta.tipo, consulta.empresa)


# ------------------------------------------------------------------ técnico
@dataclass(frozen=True)
class ConsultarPanelDelTecnico:
    id_tecnico: str


class ManejadorConsultarPanelDelTecnico:
    def __init__(self, lector: LectorDeOrdenes) -> None:
        self._lector = lector

    def ejecutar(self, consulta: ConsultarPanelDelTecnico) -> list[OrdenDelPanelVista]:
        return self._lector.panel_del_tecnico(consulta.id_tecnico)


# ------------------------------------------------------------------ compras
@dataclass(frozen=True)
class ListarSolicitudesPendientes:
    pass


class ManejadorListarSolicitudesPendientes:
    def __init__(self, lector: LectorDeOrdenes, reloj: Reloj) -> None:
        self._lector = lector
        self._reloj = reloj
        self._calendario = CalendarioHabil()

    def ejecutar(self, consulta: ListarSolicitudesPendientes) -> list[SolicitudPendienteVista]:
        ahora = self._reloj.ahora_en_el_taller()
        return [
            SolicitudPendienteVista(
                solicitud.numero_orden,
                solicitud.id,
                solicitud.refaccion,
                solicitud.cantidad,
                solicitud.fecha_solicitud,
                self._calendario.dias_habiles_entre(
                    solicitud.fecha_solicitud.astimezone(ahora.tzinfo).date(), ahora.date()
                ),
            )
            for solicitud in self._lector.solicitudes_pendientes()
        ]


# ------------------------------------------------------------------ cotizaciones
@dataclass(frozen=True)
class ListarCotizacionesPendientesDeAprobacion:
    pass


class ManejadorListarCotizacionesPendientesDeAprobacion:
    def __init__(self, lector: LectorDeOrdenes) -> None:
        self._lector = lector

    def ejecutar(
        self, consulta: ListarCotizacionesPendientesDeAprobacion
    ) -> list[CotizacionPendienteVista]:
        return self._lector.cotizaciones_pendientes_de_aprobacion()


@dataclass(frozen=True)
class ConsultarCotizacion:
    id_cotizacion: str


class ManejadorConsultarCotizacion:
    def __init__(self, lector: LectorDeOrdenes) -> None:
        self._lector = lector

    def ejecutar(self, consulta: ConsultarCotizacion) -> CotizacionVista:
        vista = self._lector.cotizacion(consulta.id_cotizacion)
        if vista is None:
            raise CotizacionNoEncontrada(
                f"No se encontró la cotización {consulta.id_cotizacion}. "
                "Revise el número e intente de nuevo."
            )
        return vista


# ------------------------------------------------------------------ órdenes
@dataclass(frozen=True)
class ConsultarExpedienteDeOrden:
    numero_orden: str


class ManejadorConsultarExpedienteDeOrden:
    def __init__(self, lector: LectorDeOrdenes) -> None:
        self._lector = lector

    def ejecutar(self, consulta: ConsultarExpedienteDeOrden) -> ExpedienteDeOrdenVista:
        numero = NumeroOrden(consulta.numero_orden)
        vista = self._lector.expediente(numero)
        if vista is None:
            raise OrdenNoEncontrada(
                f"No se encontró la orden de servicio {numero}. "
                "Revise el número e intente de nuevo."
            )
        return vista


@dataclass(frozen=True)
class ListarOrdenes:
    estado: EstadoOrden | None = None


class ManejadorListarOrdenes:
    def __init__(self, lector: LectorDeOrdenes) -> None:
        self._lector = lector

    def ejecutar(self, consulta: ListarOrdenes) -> list[OrdenResumenVista]:
        return self._lector.ordenes(consulta.estado)


@dataclass(frozen=True)
class ConsultarIngresosDelDia:
    pass


class ManejadorConsultarIngresosDelDia:
    """«Hoy» es el día en la zona del taller, aunque los pagos se guarden en UTC (RN-21)."""

    def __init__(self, lector: LectorDeOrdenes, reloj: Reloj) -> None:
        self._lector = lector
        self._reloj = reloj

    def ejecutar(self, consulta: ConsultarIngresosDelDia) -> IngresosDelDiaVista:
        ahora = self._reloj.ahora_en_el_taller()
        inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        total = self._lector.total_de_pagos_entre(inicio, inicio + timedelta(days=1))
        return IngresosDelDiaVista(ahora.date(), str(Dinero(total).monto))


@dataclass(frozen=True)
class ConsultarEstadoDeOrden:
    numero_orden: str
    placas: str


class ManejadorConsultarEstadoDeOrden:
    def __init__(self, lector: LectorDeOrdenes) -> None:
        self._lector = lector

    def ejecutar(self, consulta: ConsultarEstadoDeOrden) -> EstadoDeOrdenVista:
        vista = self._lector.estado_de_orden(
            NumeroOrden(consulta.numero_orden), Placas(consulta.placas)
        )
        if vista is None:
            raise OrdenNoEncontrada(MENSAJE_SIN_COINCIDENCIA)
        return vista


# ------------------------------------------------------------------ alertas
@dataclass(frozen=True)
class ListarAlertas:
    id_empleado: str
    rol: RolDeEmpleado


class ManejadorListarAlertas:
    def __init__(self, lector: LectorDeOrdenes) -> None:
        self._lector = lector

    def ejecutar(self, consulta: ListarAlertas) -> list[AlertaInterna]:
        return self._lector.alertas_de(consulta.id_empleado, consulta.rol)
