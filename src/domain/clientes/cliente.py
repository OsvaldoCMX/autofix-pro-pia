"""Aggregate Cliente (raíz: Cliente)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.compartido.errores import ValorInvalido
from domain.compartido.valores import texto_requerido


class TipoCliente(Enum):
    PARTICULAR = "Particular"
    FLOTILLA = "Flotilla"


@dataclass(frozen=True)
class ResponsableDeFlotilla:
    """Contacto de la empresa que autoriza; no usa el sistema (Glosario)."""

    nombre: str
    telefono: str
    correo: str

    def __post_init__(self) -> None:
        for campo, mensaje in (
            ("nombre", "El Responsable de Flotilla debe tener nombre."),
            ("telefono", "El Responsable de Flotilla debe tener teléfono."),
            ("correo", "El Responsable de Flotilla debe tener correo."),
        ):
            object.__setattr__(self, campo, texto_requerido(getattr(self, campo), mensaje))


class Cliente:
    """Invariante: un cliente de flotilla siempre tiene empresa y Responsable de Flotilla."""

    def __init__(
        self,
        id_cliente: str,
        nombre: str,
        tipo: TipoCliente,
        telefono: str | None = None,
        correo: str | None = None,
        empresa: str | None = None,
        responsable: ResponsableDeFlotilla | None = None,
    ) -> None:
        if tipo is TipoCliente.FLOTILLA and (not (empresa or "").strip() or responsable is None):
            raise ValorInvalido(
                "Un cliente de flotilla requiere su empresa y su Responsable de Flotilla."
            )
        self.id_cliente = id_cliente
        self.nombre = texto_requerido(nombre, "El cliente debe tener nombre.")
        self.tipo = tipo
        self.telefono = telefono
        self.correo = correo
        self.empresa = empresa
        self.responsable = responsable

    @property
    def es_de_flotilla(self) -> bool:
        return self.tipo is TipoCliente.FLOTILLA

    def actualizar_contacto(self, nombre: str, telefono: str | None, correo: str | None) -> None:
        """El asesor confirma o corrige los datos de un cliente recurrente (CA-003)."""
        self.nombre = texto_requerido(nombre, "El cliente debe tener nombre.")
        self.telefono = telefono
        self.correo = correo
