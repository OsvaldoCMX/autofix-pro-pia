"""Esquemas de la cancelación de la orden (US-025)."""
from __future__ import annotations

from api.esquemas.comunes import ModeloDeEntrada


class DatosDeCancelacion(ModeloDeEntrada):
    motivo: str
