"""Domain Events del Aggregate Cotización (modelo-de-dominio.md §6).

Los datos son textos, números y booleanos para poder guardarlos en la bitácora como JSON.
"""
from __future__ import annotations

from dataclasses import dataclass

from domain.compartido.eventos import EventoDeDominio


@dataclass(frozen=True)
class EventoDeCotizacion(EventoDeDominio):
    id_cotizacion: str
    numero_orden: str


@dataclass(frozen=True)
class CotizacionGenerada(EventoDeCotizacion):
    version: str
    total: str


@dataclass(frozen=True)
class AprobacionGerencialRequerida(EventoDeCotizacion):
    total: str


@dataclass(frozen=True)
class CotizacionAprobadaPorGerente(EventoDeCotizacion):
    pass


@dataclass(frozen=True)
class CotizacionRechazadaPorGerente(EventoDeCotizacion):
    observaciones: str


@dataclass(frozen=True)
class CotizacionAjustada(EventoDeCotizacion):
    total: str


@dataclass(frozen=True)
class CotizacionPresentada(EventoDeCotizacion):
    pass


@dataclass(frozen=True)
class RecontactoRegistrado(EventoDeCotizacion):
    asesor: str


@dataclass(frozen=True)
class CotizacionAutorizada(EventoDeCotizacion):
    parcial: bool
    es_adicional: bool
    autorizante: str


@dataclass(frozen=True)
class CotizacionRechazadaPorCliente(EventoDeCotizacion):
    es_adicional: bool
    autorizante: str
