"""Esquemas de las consultas del Gerente y del cliente (US-017, US-018, US-021)."""
from __future__ import annotations

from datetime import date, datetime

from api.esquemas.comunes import ModeloDeSalida


class OrdenResumida(ModeloDeSalida):
    numero_orden: str
    estado: str
    abierta: bool
    id_cliente: str
    placas: str
    fecha_ingreso: datetime
    ultima_actualizacion: datetime


class IngresosDelDia(ModeloDeSalida):
    fecha: date
    total: str


class EstadoParaElCliente(ModeloDeSalida):
    """Lo único que ve el cliente en la consulta pública (CA-037)."""

    numero_orden: str
    estado: str
    fecha_ingreso: datetime
    ultima_actualizacion: datetime
