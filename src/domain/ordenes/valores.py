"""Value Objects del Aggregate Orden de Servicio (modelo-de-dominio.md §3)."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from enum import Enum

from domain.compartido.errores import ValorInvalido
from domain.compartido.valores import Dinero, texto_requerido

DIAS_DE_CREDITO = 15


class NivelDeCombustible(Enum):
    RESERVA = "Reserva"
    UN_CUARTO = "1/4"
    MEDIO = "1/2"
    TRES_CUARTOS = "3/4"
    LLENO = "Lleno"


class FormaDePago(Enum):
    EFECTIVO = "Efectivo"
    TARJETA = "Tarjeta"
    TRANSFERENCIA = "Transferencia"


@dataclass(frozen=True)
class EstadoDeRecepcion:
    """Estado del vehículo al ingresar. Las fotos de daños son opcionales (CA-002)."""

    kilometraje: int
    nivel_de_combustible: NivelDeCombustible
    fotos: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kilometraje < 0:
            raise ValorInvalido("El kilometraje no puede ser negativo.")


@dataclass(frozen=True)
class Diagnostico:
    """Informe del técnico: fallas, recomendaciones, técnico y fecha y hora (CA-032)."""

    fallas: str
    recomendaciones: str
    tecnico: str
    registrado_en: datetime

    def __post_init__(self) -> None:
        fallas = texto_requerido(self.fallas, "El diagnóstico debe describir las fallas.")
        object.__setattr__(self, "fallas", fallas)
        object.__setattr__(self, "recomendaciones", self.recomendaciones.strip())


@dataclass(frozen=True)
class Pago:
    """Pago de contado de un cliente particular (CA-026)."""

    monto: Dinero
    forma: FormaDePago
    registrado_en: datetime


@dataclass(frozen=True)
class CargoACredito:
    """Crédito de flotilla: el vencimiento queda pendiente hasta la entrega (CA-039, CA-041)."""

    monto: Dinero
    registrado_en: datetime
    fecha_vencimiento: date | None = None

    def con_vencimiento(self, fecha_de_entrega: datetime) -> CargoACredito:
        vencimiento = fecha_de_entrega.date() + timedelta(days=DIAS_DE_CREDITO)
        return replace(self, fecha_vencimiento=vencimiento)


@dataclass(frozen=True)
class NotaDeResponsabilidad:
    """Se genera al registrar la salida y se firma en papel (CA-024)."""

    fecha_salida: datetime
    firmada: bool = False
    fecha_firma: datetime | None = None

    def firmar(self, fecha: datetime) -> NotaDeResponsabilidad:
        return replace(self, firmada=True, fecha_firma=fecha)


@dataclass(frozen=True)
class Cancelacion:
    """Motivo, fecha y hora, y asesor que canceló la orden (CA-044)."""

    motivo: str
    registrada_en: datetime
    asesor: str

    def __post_init__(self) -> None:
        motivo = texto_requerido(self.motivo, "La cancelación debe indicar el motivo.")
        object.__setattr__(self, "motivo", motivo)
