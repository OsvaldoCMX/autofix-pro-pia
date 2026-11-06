"""Esquemas de las alertas internas del panel de cada empleado."""
from __future__ import annotations

from datetime import datetime

from api.esquemas.comunes import ModeloDeSalida


class AlertaDelEmpleado(ModeloDeSalida):
    tipo: str
    mensaje: str
    creada_en: datetime
    numero_orden: str | None
    id_cotizacion: str | None
    leida: bool
