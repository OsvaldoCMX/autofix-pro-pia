"""Domain Events del Aggregate Orden de Servicio (modelo-de-dominio.md §6).

Los datos son textos, números y booleanos para poder guardarlos en la bitácora como JSON.
"""
from __future__ import annotations

from dataclasses import dataclass

from domain.compartido.eventos import EventoDeDominio


@dataclass(frozen=True)
class EventoDeOrden(EventoDeDominio):
    numero_orden: str


@dataclass(frozen=True)
class OrdenRecibida(EventoDeOrden):
    id_cliente: str
    placas: str
    asesor: str


@dataclass(frozen=True)
class TecnicoAsignadoParaDiagnostico(EventoDeOrden):
    tecnico: str


@dataclass(frozen=True)
class DatosDeRecepcionCorregidos(EventoDeOrden):
    """El asesor corrigió el kilometraje, el combustible o el motivo (RN-29, H-PIA-24)."""

    kilometraje: int
    nivel_de_combustible: str
    motivo_de_ingreso: str


@dataclass(frozen=True)
class TecnicoDeDiagnosticoReasignado(EventoDeOrden):
    """El asesor cambió al técnico antes del diagnóstico (RN-28, H-PIA-23)."""

    tecnico_anterior: str
    tecnico: str


@dataclass(frozen=True)
class DiagnosticoRegistrado(EventoDeOrden):
    tecnico: str
    asesor: str


@dataclass(frozen=True)
class OrdenAutorizada(EventoDeOrden):
    id_cotizacion: str


@dataclass(frozen=True)
class TrabajosAsignados(EventoDeOrden):
    ids_trabajos: tuple[int, ...]
    tecnico: str


@dataclass(frozen=True)
class TrabajoIniciado(EventoDeOrden):
    id_trabajo: int
    tecnico: str


@dataclass(frozen=True)
class FallaAdicionalReportada(EventoDeOrden):
    id_falla: int
    descripcion: str
    asesor: str


@dataclass(frozen=True)
class SolicitudDeCompraCreada(EventoDeOrden):
    id_solicitud: int
    id_trabajo: int
    refaccion: str
    cantidad: int


@dataclass(frozen=True)
class RefaccionDisponible(EventoDeOrden):
    id_solicitud: int
    tecnico: str | None
    asesor: str


@dataclass(frozen=True)
class ClienteAvisadoDelRetraso(EventoDeOrden):
    id_solicitud: int


@dataclass(frozen=True)
class VehiculoRetirado(EventoDeOrden):
    pass


@dataclass(frozen=True)
class OrdenReactivada(EventoDeOrden):
    estado: str


@dataclass(frozen=True)
class OrdenListaParaEntrega(EventoDeOrden):
    asesor: str


@dataclass(frozen=True)
class PagoRegistrado(EventoDeOrden):
    monto: str
    forma: str


@dataclass(frozen=True)
class FormaDePagoCorregida(EventoDeOrden):
    """Caja corrigió la forma de pago antes de la entrega (RN-30, H-PIA-24)."""

    forma_anterior: str
    forma: str


@dataclass(frozen=True)
class CargoACreditoRegistrado(EventoDeOrden):
    monto: str


@dataclass(frozen=True)
class VehiculoEntregado(EventoDeOrden):
    sin_reparacion: bool = False
    vence: str | None = None


@dataclass(frozen=True)
class OrdenCancelada(EventoDeOrden):
    motivo: str
    asesor: str
