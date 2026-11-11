"""Puerto de lectura: solo consulta, separado de los Repositories (ADR-003, SOLID-I)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from application.consultas.vistas import (
    ClienteVista,
    CotizacionPendienteVista,
    CotizacionVista,
    EstadoDeOrdenVista,
    ExpedienteDeOrdenVista,
    OrdenDelPanelVista,
    OrdenResumenVista,
    SolicitudVista,
    TecnicoVista,
    VehiculoConClienteVista,
)
from application.puertos import AlertaInterna
from domain.clientes.cliente import TipoCliente
from domain.compartido.valores import NumeroOrden, Placas
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes.estados import EstadoOrden


class LectorDeOrdenes(ABC):
    @abstractmethod
    def vehiculo_por_placas(self, placas: Placas) -> VehiculoConClienteVista | None: ...

    @abstractmethod
    def clientes(self, tipo: TipoCliente | None, empresa: str | None) -> list[ClienteVista]: ...

    @abstractmethod
    def panel_del_tecnico(self, id_tecnico: str) -> list[OrdenDelPanelVista]:
        """Órdenes con lugar en la fila que tiene asignadas, de la más antigua a la más reciente."""

    @abstractmethod
    def tecnicos(self) -> list[TecnicoVista]:
        """Empleados con rol Técnico, por su clave (CA-053, RN-28)."""

    @abstractmethod
    def solicitudes_pendientes(self) -> list[SolicitudVista]: ...

    @abstractmethod
    def cotizaciones_pendientes_de_aprobacion(self) -> list[CotizacionPendienteVista]: ...

    @abstractmethod
    def cotizacion(self, id_cotizacion: str) -> CotizacionVista | None: ...

    @abstractmethod
    def expediente(self, numero: NumeroOrden) -> ExpedienteDeOrdenVista | None: ...

    @abstractmethod
    def ordenes(self, estado: EstadoOrden | None) -> list[OrdenResumenVista]: ...

    @abstractmethod
    def total_de_pagos_entre(self, desde: datetime, hasta: datetime) -> Decimal:
        """Suma los pagos de contado con `desde <= fecha < hasta`; no incluye créditos (RN-21)."""

    @abstractmethod
    def estado_de_orden(self, numero: NumeroOrden, placas: Placas) -> EstadoDeOrdenVista | None:
        """Solo responde si el folio y las placas coinciden (RN-20)."""

    @abstractmethod
    def alertas_de(self, id_empleado: str, rol: RolDeEmpleado) -> list[AlertaInterna]:
        """Alertas dirigidas al empleado o a su rol, de la más antigua a la más reciente."""

    @abstractmethod
    def ordenes_con_solicitudes_pendientes(self) -> list[NumeroOrden]:
        """Candidatas de la revisión de plazos para E7 (ADR-015)."""

    @abstractmethod
    def cotizaciones_presentadas_sin_decision(self) -> list[str]:
        """Candidatas de la revisión de plazos para E8 (ADR-015)."""
