"""Estados de la Cotización y su máquina de estados (modelo-de-dominio.md §5.2)."""
from __future__ import annotations

from enum import Enum

from domain.compartido.maquina_de_estados import MaquinaDeEstados


class EstadoCotizacion(Enum):
    PENDIENTE_DE_APROBACION_GERENCIAL = "Pendiente de Aprobación Gerencial"
    REQUIERE_AJUSTE = "Requiere Ajuste"
    PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE = "Pendiente de Autorización del Cliente"
    AUTORIZADA = "Autorizada"
    AUTORIZADA_PARCIALMENTE = "Autorizada Parcialmente"
    RECHAZADA = "Rechazada"


_E = EstadoCotizacion

MAQUINA_DE_COTIZACION: MaquinaDeEstados[EstadoCotizacion] = MaquinaDeEstados(
    "La cotización",
    {
        _E.PENDIENTE_DE_APROBACION_GERENCIAL: {
            _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE,
            _E.REQUIERE_AJUSTE,
        },
        _E.REQUIERE_AJUSTE: {_E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE},
        # Corregir una cotización que vuelve a superar $15,000 la regresa al Gerente (H-PIA-21).
        _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE: {
            _E.PENDIENTE_DE_APROBACION_GERENCIAL,
            _E.AUTORIZADA,
            _E.AUTORIZADA_PARCIALMENTE,
            _E.RECHAZADA,
        },
    },
    finales={_E.AUTORIZADA, _E.AUTORIZADA_PARCIALMENTE, _E.RECHAZADA},
)
