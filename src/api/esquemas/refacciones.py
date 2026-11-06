"""Esquemas de solicitudes de compra y lista de Compras (US-010 a US-012)."""
from __future__ import annotations

from datetime import datetime

from api.esquemas.comunes import (
    EnteroPositivo,
    ModeloDeEntrada,
    ModeloDeSalida,
    TextoDeRefaccion,
)


class NuevaSolicitud(ModeloDeEntrada):
    id_trabajo: EnteroPositivo
    refaccion: TextoDeRefaccion
    cantidad: EnteroPositivo


class SolicitudActualizada(ModeloDeSalida):
    numero_orden: str
    id_solicitud: int
    estado_solicitud: str
    estado_orden: str


class SolicitudPendiente(ModeloDeSalida):
    numero_orden: str
    id_solicitud: int
    refaccion: str
    cantidad: int
    fecha_solicitud: datetime
    dias_habiles_transcurridos: int
