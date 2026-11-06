"""Esquemas de la decisión del cliente o del Responsable de Flotilla (US-006, US-009, US-016)."""
from __future__ import annotations

from api.esquemas.comunes import (
    EnteroPositivo,
    ModeloDeEntrada,
    ModeloDeSalida,
    TextoDeNombre,
)
from application.comandos import RegistrarDecisionDelCliente
from domain.cotizaciones.valores import RolDeAutorizante


class DatosDeDecision(ModeloDeEntrada):
    """Una lista vacía de líneas autorizadas es el rechazo total."""

    lineas_autorizadas: list[EnteroPositivo]
    nombre_del_autorizante: TextoDeNombre
    rol_del_autorizante: RolDeAutorizante

    def a_comando(self, id_cotizacion: str) -> RegistrarDecisionDelCliente:
        return RegistrarDecisionDelCliente(
            id_cotizacion,
            tuple(self.lineas_autorizadas),
            self.nombre_del_autorizante,
            self.rol_del_autorizante,
        )


class DecisionRegistrada(ModeloDeSalida):
    id_cotizacion: str
    estado_cotizacion: str
    estado_orden: str
    trabajos_autorizados: list[str]
    trabajos_no_autorizados: list[str]
