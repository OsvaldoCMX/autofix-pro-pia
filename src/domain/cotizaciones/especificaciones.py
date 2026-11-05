"""Specifications E1 y E8 del Aggregate Cotización (modelo-de-dominio.md §4)."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from domain.compartido.especificacion import Especificacion
from domain.compartido.valores import Dinero
from domain.cotizaciones.estados import EstadoCotizacion
from domain.cotizaciones.valores import TipoCotizacion

if TYPE_CHECKING:
    from domain.cotizaciones.cotizacion import Cotizacion

UMBRAL_DE_APROBACION_GERENCIAL = Dinero(Decimal(15000))
HORAS_PARA_RECONTACTO = 48


class EsCotizacionInicial(Especificacion["Cotizacion"]):
    def es_satisfecha_por(self, candidato: Cotizacion) -> bool:
        return candidato.tipo is TipoCotizacion.INICIAL


class TotalMayorAlUmbral(Especificacion["Cotizacion"]):
    def __init__(self, umbral: Dinero) -> None:
        self._umbral = umbral

    def es_satisfecha_por(self, candidato: Cotizacion) -> bool:
        return candidato.total > self._umbral


class RequiereAprobacionGerencial(Especificacion["Cotizacion"]):
    """E1 · RN-04: cotización inicial mayor a $15,000 MXN."""

    def __init__(self) -> None:
        self._regla = EsCotizacionInicial() & TotalMayorAlUmbral(UMBRAL_DE_APROBACION_GERENCIAL)

    def es_satisfecha_por(self, candidato: Cotizacion) -> bool:
        return self._regla.es_satisfecha_por(candidato)


class PendienteDeAutorizacion(Especificacion["Cotizacion"]):
    def es_satisfecha_por(self, candidato: Cotizacion) -> bool:
        return candidato.estado is EstadoCotizacion.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE


class FuePresentada(Especificacion["Cotizacion"]):
    def es_satisfecha_por(self, candidato: Cotizacion) -> bool:
        return candidato.fecha_presentacion is not None


class MasDeHorasDesdeElUltimoContacto(Especificacion["Cotizacion"]):
    def __init__(self, horas: int, fecha_de_revision: datetime) -> None:
        self._plazo = timedelta(hours=horas)
        self._fecha_de_revision = fecha_de_revision

    def es_satisfecha_por(self, candidato: Cotizacion) -> bool:
        ultimo_contacto = candidato.ultimo_contacto
        if ultimo_contacto is None:
            return False
        return self._fecha_de_revision - ultimo_contacto > self._plazo


class RequiereRecontacto(Especificacion["Cotizacion"]):
    """E8 · RN-12: presentada, sin respuesta y con más de 48 horas desde el último contacto."""

    def __init__(self, fecha_de_revision: datetime) -> None:
        self._regla = (
            PendienteDeAutorizacion()
            & FuePresentada()
            & MasDeHorasDesdeElUltimoContacto(HORAS_PARA_RECONTACTO, fecha_de_revision)
        )

    def es_satisfecha_por(self, candidato: Cotizacion) -> bool:
        return self._regla.es_satisfecha_por(candidato)
