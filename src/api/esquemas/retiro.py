"""Esquemas del retiro anticipado con Nota de Responsabilidad (US-013)."""
from __future__ import annotations

from datetime import datetime

from api.esquemas.comunes import ModeloDeSalida


class NotaDeResponsabilidad(ModeloDeSalida):
    numero_orden: str
    estado: str
    fecha_salida: datetime
    firmada: bool
