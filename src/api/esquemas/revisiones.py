"""Esquemas de la revisión periódica de plazos (ADR-015)."""
from __future__ import annotations

from api.esquemas.comunes import ModeloDeSalida


class RevisionDePlazos(ModeloDeSalida):
    alertas_de_refaccion: int
    alertas_de_recontacto: int
