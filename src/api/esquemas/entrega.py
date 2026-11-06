"""Esquemas de la entrega del vehículo (US-024)."""
from __future__ import annotations

from datetime import date, datetime

from api.esquemas.comunes import ModeloDeSalida


class EntregaRegistrada(ModeloDeSalida):
    numero_orden: str
    estado: str
    fecha_entrega: datetime
    fecha_vencimiento_credito: date | None
