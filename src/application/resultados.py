"""DTO que devuelven los casos de uso: no exponen los Aggregates (ADR-003).

Los importes viajan como texto con dos decimales («1500.00»).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class ResultadoDeCliente:
    id_cliente: str
    nombre: str
    tipo: str
    empresa: str | None
    responsable_nombre: str | None
    telefono: str | None = None
    correo: str | None = None


@dataclass(frozen=True)
class ResultadoDeRecepcion:
    numero_orden: str
    estado: str
    kilometraje: int
    nivel_de_combustible: str
    motivo_de_ingreso: str


@dataclass(frozen=True)
class ResultadoDeVehiculo:
    placas: str
    vin: str
    marca: str
    modelo: str
    anio: int


@dataclass(frozen=True)
class ResultadoDeOrden:
    numero_orden: str
    estado: str
    id_cliente: str
    placas: str
    fecha_ingreso: datetime


@dataclass(frozen=True)
class ResultadoDeEstado:
    """Para las acciones cuyo único resultado es el nuevo estado de la orden."""

    numero_orden: str
    estado: str


@dataclass(frozen=True)
class ResultadoDeDiagnostico:
    numero_orden: str
    estado: str
    tecnico: str
    registrado_en: datetime


@dataclass(frozen=True)
class ResultadoDeFallaAdicional:
    numero_orden: str
    id_falla: int
    descripcion: str
    reportada_en: datetime


@dataclass(frozen=True)
class ResultadoDeCotizacion:
    id: str
    numero_orden: str
    version: str
    tipo: str
    estado: str
    total: str
    fecha_presentacion: datetime | None = None
    fecha_aprobacion_gerencial: datetime | None = None


@dataclass(frozen=True)
class ResultadoDeRecontacto:
    id_cotizacion: str
    estado: str
    registrado_en: datetime


@dataclass(frozen=True)
class ResultadoDeDecision:
    id_cotizacion: str
    estado_cotizacion: str
    estado_orden: str
    trabajos_autorizados: tuple[str, ...]
    trabajos_no_autorizados: tuple[str, ...]


@dataclass(frozen=True)
class ResultadoDeAsignacion:
    numero_orden: str
    estado: str
    ids_trabajos: tuple[int, ...]
    tecnico: str


@dataclass(frozen=True)
class ResultadoDeTrabajo:
    numero_orden: str
    id_trabajo: int
    estado_trabajo: str
    estado_orden: str


@dataclass(frozen=True)
class ResultadoDeSolicitud:
    numero_orden: str
    id_solicitud: int
    estado_solicitud: str
    estado_orden: str


@dataclass(frozen=True)
class ResultadoDeNota:
    numero_orden: str
    estado: str
    fecha_salida: datetime
    firmada: bool


@dataclass(frozen=True)
class ResultadoDePago:
    numero_orden: str
    estado: str
    monto: str
    forma: str
    registrado_en: datetime


@dataclass(frozen=True)
class ResultadoDeCargoACredito:
    numero_orden: str
    estado: str
    monto: str
    registrado_en: datetime


@dataclass(frozen=True)
class ResultadoDeEntrega:
    numero_orden: str
    estado: str
    fecha_entrega: datetime
    fecha_vencimiento_credito: date | None = None


@dataclass(frozen=True)
class ResultadoDeRevisionDePlazos:
    alertas_de_refaccion: int
    alertas_de_recontacto: int
