"""Esquemas de asignación, diagnóstico y panel del técnico (US-007, US-019, US-020)."""
from __future__ import annotations

from datetime import datetime

from api.esquemas.comunes import ModeloDeEntrada, ModeloDeSalida, TextoDeIdentificador
from api.esquemas.recepcion import TrabajoDeOrden


class AsignacionDeDiagnostico(ModeloDeEntrada):
    tecnico: TextoDeIdentificador


class DatosDeDiagnostico(ModeloDeEntrada):
    fallas: str
    recomendaciones: str


class DatosDeFallaAdicional(ModeloDeEntrada):
    descripcion: str


class DiagnosticoRegistrado(ModeloDeSalida):
    numero_orden: str
    estado: str
    tecnico: str
    registrado_en: datetime


class FallaAdicionalRegistrada(ModeloDeSalida):
    numero_orden: str
    id_falla: int
    descripcion: str
    reportada_en: datetime


class OrdenDelPanel(ModeloDeSalida):
    numero_orden: str
    estado: str
    placas: str
    motivo_de_ingreso: str
    fecha_ingreso_a_fila: datetime
    diagnostico_asignado: bool
    trabajos: list[TrabajoDeOrden]
