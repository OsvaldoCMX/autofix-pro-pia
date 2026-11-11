"""Value Objects del Aggregate Cotización (modelo-de-dominio.md §3)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from domain.compartido.errores import ValorInvalido
from domain.compartido.valores import Dinero, texto_requerido
from domain.cotizaciones.estados import EstadoCotizacion


class TipoCotizacion(Enum):
    INICIAL = "Inicial"
    ADICIONAL = "Adicional"


class RolDeAutorizante(Enum):
    CLIENTE = "Cliente"
    RESPONSABLE_DE_FLOTILLA = "Responsable de Flotilla"


@dataclass(frozen=True)
class VersionCotizacion:
    """La cotización inicial es v.1; las adicionales son v.2, v.3… (RN-24)."""

    numero: int

    def __post_init__(self) -> None:
        if self.numero < 1:
            raise ValorInvalido("La versión de una cotización empieza en 1.")

    def __str__(self) -> str:
        return f"v.{self.numero}"


@dataclass(frozen=True)
class RefaccionCotizada:
    """Refacción incluida en una línea de cotización."""

    descripcion: str
    cantidad: int
    precio_unitario: Dinero

    def __post_init__(self) -> None:
        descripcion = texto_requerido(self.descripcion, "La refacción debe tener descripción.")
        object.__setattr__(self, "descripcion", descripcion)
        if self.cantidad <= 0:
            raise ValorInvalido("La cantidad de una refacción debe ser mayor a cero.")

    @property
    def importe(self) -> Dinero:
        return self.precio_unitario.por(self.cantidad)


@dataclass(frozen=True)
class Autorizante:
    """Persona a cuyo nombre se registra la decisión (CA-010, CA-029)."""

    nombre: str
    rol: RolDeAutorizante

    def __post_init__(self) -> None:
        nombre = texto_requerido(self.nombre, "Debe indicarse el nombre de quien autoriza.")
        object.__setattr__(self, "nombre", nombre)


@dataclass(frozen=True)
class TrabajoDecidido:
    """Resultado de decidir una línea: lo que la Orden necesita para crear su Trabajo."""

    numero_linea: int
    descripcion: str
    importe: Dinero


@dataclass(frozen=True)
class DecisionDelCliente:
    """Decisión registrada sobre una cotización (US-006)."""

    id_cotizacion: str
    autorizados: tuple[TrabajoDecidido, ...]
    no_autorizados: tuple[TrabajoDecidido, ...]
    autorizante: Autorizante
    registrada_en: datetime
    tipo_cotizacion: TipoCotizacion

    @property
    def es_rechazo_total(self) -> bool:
        return not self.autorizados


@dataclass(frozen=True)
class Recontacto:
    """El asesor volvió a contactar al cliente; el plazo de 48 horas cuenta desde aquí (CA-040)."""

    asesor: str
    registrado_en: datetime

    def __post_init__(self) -> None:
        asesor = texto_requerido(self.asesor, "Debe indicarse el asesor que hizo el recontacto.")
        object.__setattr__(self, "asesor", asesor)


@dataclass(frozen=True)
class CorreccionDeCotizacion:
    """Una corrección del asesor antes de la decisión del cliente (RN-25, H-PIA-21).

    Guarda lo que cambió y lo que la cotización tenía antes de corregirse (ADR-018).
    """

    asesor: str
    registrada_en: datetime
    motivo: str
    total_anterior: Dinero
    total_nuevo: Dinero
    estado_anterior: EstadoCotizacion
    estado_nuevo: EstadoCotizacion
    fecha_presentacion_anterior: datetime | None
    fecha_aprobacion_gerencial_anterior: datetime | None

    def __post_init__(self) -> None:
        asesor = texto_requerido(self.asesor, "Debe indicarse el asesor que corrige la cotización.")
        motivo = texto_requerido(self.motivo, "Capture el motivo de la corrección de la cotización.")
        object.__setattr__(self, "asesor", asesor)
        object.__setattr__(self, "motivo", motivo)
