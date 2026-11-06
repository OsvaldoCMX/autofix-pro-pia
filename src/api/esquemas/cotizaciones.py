"""Esquemas de cotización (US-004, US-005, US-023)."""
from __future__ import annotations

from datetime import datetime

from api.esquemas.comunes import ModeloDeSalida


class RefaccionDeLinea(ModeloDeSalida):
    descripcion: str
    cantidad: int
    precio_unitario: str
    importe: str


class LineaDetallada(ModeloDeSalida):
    numero: int
    descripcion: str
    mano_de_obra: str
    refacciones: list[RefaccionDeLinea]
    subtotal: str
    decision: str | None


class CotizacionDetallada(ModeloDeSalida):
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
    lineas: list[LineaDetallada]
