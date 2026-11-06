"""Esquemas del pago de contado y del cargo a crédito (US-014, US-015, US-022)."""
from __future__ import annotations

from datetime import datetime

from api.esquemas.comunes import Importe, ModeloDeEntrada, ModeloDeSalida
from domain.ordenes.valores import FormaDePago


class DatosDePago(ModeloDeEntrada):
    monto: Importe
    forma: FormaDePago


class PagoRegistrado(ModeloDeSalida):
    numero_orden: str
    estado: str
    monto: str
    forma: str
    registrado_en: datetime


class CargoRegistrado(ModeloDeSalida):
    numero_orden: str
    estado: str
    monto: str
    registrado_en: datetime
