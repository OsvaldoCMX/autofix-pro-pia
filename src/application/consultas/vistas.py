"""Vistas de lectura (DTO): modelos planos que no exponen los Aggregates (ADR-003).

Los importes viajan como texto con dos decimales («1500.00»).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class ClienteVista:
    id_cliente: str
    nombre: str
    tipo: str
    telefono: str | None
    correo: str | None
    empresa: str | None
    responsable_nombre: str | None
    responsable_telefono: str | None
    responsable_correo: str | None


@dataclass(frozen=True)
class VehiculoConClienteVista:
    placas: str
    vin: str
    marca: str
    modelo: str
    anio: int
    cliente: ClienteVista


@dataclass(frozen=True)
class TrabajoVista:
    id: int
    descripcion: str
    importe: str
    estado: str
    tecnico: str | None


@dataclass(frozen=True)
class OrdenDelPanelVista:
    numero_orden: str
    estado: str
    placas: str
    motivo_de_ingreso: str
    fecha_ingreso_a_fila: datetime
    diagnostico_asignado: bool
    trabajos: tuple[TrabajoVista, ...]


@dataclass(frozen=True)
class SolicitudVista:
    numero_orden: str
    id: int
    id_trabajo: int
    refaccion: str
    cantidad: int
    estado: str
    fecha_solicitud: datetime
    fecha_llegada: datetime | None
    fecha_aviso_al_cliente: datetime | None


@dataclass(frozen=True)
class SolicitudPendienteVista:
    numero_orden: str
    id_solicitud: int
    refaccion: str
    cantidad: int
    fecha_solicitud: datetime
    dias_habiles_transcurridos: int


@dataclass(frozen=True)
class CotizacionPendienteVista:
    id_cotizacion: str
    numero_orden: str
    version: str
    total: str


@dataclass(frozen=True)
class RefaccionVista:
    descripcion: str
    cantidad: int
    precio_unitario: str
    importe: str


@dataclass(frozen=True)
class LineaVista:
    numero: int
    descripcion: str
    mano_de_obra: str
    refacciones: tuple[RefaccionVista, ...]
    subtotal: str
    decision: str | None


@dataclass(frozen=True)
class CotizacionVista:
    id: str
    numero_orden: str
    tipo: str
    version: str
    estado: str
    total: str
    generada_en: datetime
    fecha_aprobacion_gerencial: datetime | None
    observaciones_del_gerente: str | None
    fecha_presentacion: datetime | None
    autorizante: str | None
    fecha_decision: datetime | None
    lineas: tuple[LineaVista, ...]


@dataclass(frozen=True)
class FallaAdicionalVista:
    id: int
    descripcion: str
    tecnico: str
    reportada_en: datetime


@dataclass(frozen=True)
class ExpedienteDeOrdenVista:
    numero_orden: str
    estado: str
    id_cliente: str
    placas: str
    asesor: str
    motivo_de_ingreso: str
    fecha_ingreso: datetime
    ultima_actualizacion: datetime
    kilometraje: int | None
    nivel_de_combustible: str | None
    tecnico_de_diagnostico: str | None
    diagnostico_fallas: str | None
    diagnostico_recomendaciones: str | None
    rechazo_total: bool
    total_autorizado: str
    pago_monto: str | None
    pago_forma: str | None
    pago_registrado_en: datetime | None
    credito_monto: str | None
    credito_fecha_vencimiento: date | None
    nota_fecha_salida: datetime | None
    nota_firmada: bool
    fecha_entrega: datetime | None
    cancelacion_motivo: str | None
    cotizaciones: tuple[CotizacionVista, ...]
    trabajos: tuple[TrabajoVista, ...]
    solicitudes: tuple[SolicitudVista, ...]
    fallas_adicionales: tuple[FallaAdicionalVista, ...]


@dataclass(frozen=True)
class OrdenResumenVista:
    numero_orden: str
    estado: str
    abierta: bool
    id_cliente: str
    placas: str
    fecha_ingreso: datetime
    ultima_actualizacion: datetime


@dataclass(frozen=True)
class IngresosDelDiaVista:
    fecha: date
    total: str


@dataclass(frozen=True)
class EstadoDeOrdenVista:
    """Lo único que ve el cliente en la consulta pública (CA-037)."""

    numero_orden: str
    estado: str
    fecha_ingreso: datetime
    ultima_actualizacion: datetime
