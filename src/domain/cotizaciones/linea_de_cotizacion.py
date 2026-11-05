"""Entidad interna del Aggregate Cotización."""
from __future__ import annotations

from enum import Enum

from domain.compartido.errores import ValorInvalido
from domain.compartido.valores import Dinero, texto_requerido
from domain.cotizaciones.valores import RefaccionCotizada


class DecisionDeLinea(Enum):
    AUTORIZADA = "Autorizada"
    NO_AUTORIZADO = "No Autorizado"


class LineaDeCotizacion:
    """Trabajo propuesto (mano de obra) con sus refacciones; es la unidad que el cliente autoriza."""

    def __init__(
        self,
        numero: int,
        descripcion: str,
        mano_de_obra: Dinero,
        refacciones: tuple[RefaccionCotizada, ...] = (),
    ) -> None:
        if numero < 1:
            raise ValorInvalido("El número de línea empieza en 1.")
        self.numero = numero
        self.descripcion = texto_requerido(
            descripcion, "Cada trabajo de la cotización debe tener descripción."
        )
        self.mano_de_obra = mano_de_obra
        self.refacciones = tuple(refacciones)
        self.decision: DecisionDeLinea | None = None

    @property
    def subtotal(self) -> Dinero:
        total = self.mano_de_obra
        for refaccion in self.refacciones:
            total = total + refaccion.importe
        return total
