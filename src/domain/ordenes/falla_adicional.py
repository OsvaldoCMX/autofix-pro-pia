"""Entidad interna de la orden: avería que el técnico descubre durante la reparación (CA-034)."""
from __future__ import annotations

from datetime import datetime

from domain.compartido.valores import texto_requerido


class FallaAdicional:
    def __init__(
        self, id_falla: int, descripcion: str, tecnico: str, reportada_en: datetime
    ) -> None:
        self.id = id_falla
        self.descripcion = texto_requerido(
            descripcion, "La falla adicional debe tener descripción."
        )
        self.tecnico = tecnico
        self.reportada_en = reportada_en
