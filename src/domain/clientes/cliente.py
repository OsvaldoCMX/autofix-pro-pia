"""Aggregate Cliente (raíz: Cliente)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.compartido.errores import EmpresaYaRegistrada, ValorInvalido
from domain.compartido.valores import Correo, Telefono, texto_requerido


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

    def coincide_con(self, nombre: str | None, telefono: str | None, correo: str | None) -> bool:
        """Los datos que no se capturaron no cuentan; los demás se comparan sin formato."""
        capturados = (
            (nombre, self.nombre, _sin_espacios_de_mas),
            (telefono, self.telefono, _solo_digitos),
            (correo, self.correo, _sin_espacios_de_mas),
        )
        return all(
            not (dato or "").strip() or limpiar(dato or "") == limpiar(registrado)
            for dato, registrado, limpiar in capturados
        )

    @classmethod
    def capturar(cls, nombre: str, telefono: str, correo: str) -> ResponsableDeFlotilla:
        """Al registrarlo se revisa también la forma del teléfono y del correo (RN-31)."""
        responsable = cls(nombre, telefono, correo)
        return cls(
            responsable.nombre,
            Telefono(responsable.telefono, "El teléfono del Responsable de Flotilla").valor,
            Correo(responsable.correo, "El correo del Responsable de Flotilla").valor,
        )


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

    @classmethod
    def registrar(
        cls,
        id_cliente: str,
        nombre: str,
        tipo: TipoCliente,
        telefono: str | None = None,
        correo: str | None = None,
        empresa: str | None = None,
        responsable: ResponsableDeFlotilla | None = None,
    ) -> Cliente:
        """Cliente nuevo capturado por el asesor: revisa el teléfono y el correo (RN-31)."""
        return cls(
            id_cliente,
            nombre,
            tipo,
            Telefono.capturado(telefono),
            Correo.capturado(correo),
            empresa,
            responsable,
        )

    def exigir_mismo_responsable(
        self, nombre: str | None, telefono: str | None, correo: str | None
    ) -> None:
        """CA-065: registrar otra vez la empresa no cambia en silencio a su Responsable."""
        responsable = self.responsable
        if responsable is None or responsable.coincide_con(nombre, telefono, correo):
            return
        raise EmpresaYaRegistrada(
            f"La empresa «{self.empresa}» ya está registrada con su Responsable de Flotilla "
            f"{responsable.nombre} (teléfono {responsable.telefono}). Use ese registro."
        )

    @property
    def es_de_flotilla(self) -> bool:
        return self.tipo is TipoCliente.FLOTILLA

    def actualizar_contacto(self, nombre: str, telefono: str | None, correo: str | None) -> None:
        """El asesor confirma o corrige los datos de un cliente (CA-003, CA-055, RN-31)."""
        nombre_limpio = texto_requerido(nombre, "El cliente debe tener nombre.")
        telefono_limpio = Telefono.capturado(telefono)
        correo_limpio = Correo.capturado(correo)
        self.nombre, self.telefono, self.correo = nombre_limpio, telefono_limpio, correo_limpio


def _sin_espacios_de_mas(texto: str) -> str:
    return " ".join(texto.split()).casefold()


def _solo_digitos(texto: str) -> str:
    return "".join(caracter for caracter in texto if caracter.isdigit())

