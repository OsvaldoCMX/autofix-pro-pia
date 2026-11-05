"""Value Objects compartidos: se definen por su valor, son inmutables y validan su propia regla."""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from domain.compartido.errores import ValorInvalido

_CENTAVOS = Decimal("0.01")
_IMPORTE_MAXIMO = Decimal("9999999999.99")  # NUMERIC(12,2) en la base de datos
_LARGO_MAXIMO_DE_PLACAS = 15  # VARCHAR(15) en la base de datos
_FORMATO_DE_PLACAS = re.compile(r"[A-Z0-9]+")
_FORMATO_DE_VIN = re.compile(r"[A-HJ-NPR-Z0-9]{17}")


def _a_decimal_finito(monto: Decimal | int | str) -> Decimal:
    if isinstance(monto, bool | float):
        raise ValorInvalido("Un importe debe capturarse como número decimal exacto.")
    try:
        decimal = Decimal(monto)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValorInvalido(f"El importe «{monto}» no es un número válido.") from error
    if not decimal.is_finite():
        raise ValorInvalido(f"El importe «{monto}» no es un número válido.")
    return decimal


def _redondear(monto: Decimal) -> Decimal:
    try:
        redondeado = monto.quantize(_CENTAVOS, rounding=ROUND_HALF_UP)
    except InvalidOperation as error:
        raise ValorInvalido("El importe excede el máximo permitido.") from error
    if redondeado > _IMPORTE_MAXIMO:
        raise ValorInvalido("El importe excede el máximo permitido.")
    return redondeado


@dataclass(frozen=True, order=True)
class Dinero:
    """Importe en pesos mexicanos (MXN), con dos decimales. Nunca es negativo."""

    monto: Decimal

    def __post_init__(self) -> None:
        monto = _a_decimal_finito(self.monto)
        if monto < 0:
            raise ValorInvalido("Un importe en MXN no puede ser negativo.")
        object.__setattr__(self, "monto", _redondear(monto))

    @staticmethod
    def cero() -> Dinero:
        return Dinero(Decimal(0))

    def __add__(self, otro: Dinero) -> Dinero:
        return Dinero(self.monto + otro.monto)

    def por(self, cantidad: int) -> Dinero:
        return Dinero(self.monto * cantidad)

    def __str__(self) -> str:
        return f"${self.monto:,.2f} MXN"


@dataclass(frozen=True)
class NumeroOrden:
    """Folio único de la Orden de Servicio; se guarda en mayúsculas."""

    valor: str

    def __post_init__(self) -> None:
        normalizado = self.valor.strip().upper()
        if not normalizado:
            raise ValorInvalido("El número de orden no puede estar vacío.")
        object.__setattr__(self, "valor", normalizado)

    def __str__(self) -> str:
        return self.valor


@dataclass(frozen=True)
class Placas:
    """Placas del vehículo, normalizadas: mayúsculas, sin espacios ni guiones."""

    valor: str

    def __post_init__(self) -> None:
        normalizado = "".join(self.valor.replace("-", " ").split()).upper()
        if not normalizado:
            raise ValorInvalido("Las placas no pueden estar vacías.")
        if not _FORMATO_DE_PLACAS.fullmatch(normalizado):
            raise ValorInvalido("Las placas solo pueden tener letras de la A a la Z y números.")
        if len(normalizado) > _LARGO_MAXIMO_DE_PLACAS:
            raise ValorInvalido(
                f"Las placas no pueden tener más de {_LARGO_MAXIMO_DE_PLACAS} caracteres."
            )
        object.__setattr__(self, "valor", normalizado)

    def __str__(self) -> str:
        return self.valor


@dataclass(frozen=True)
class VIN:
    """Número de serie del vehículo: 17 caracteres alfanuméricos, sin I, O ni Q."""

    valor: str

    def __post_init__(self) -> None:
        normalizado = self.valor.strip().upper()
        if not _FORMATO_DE_VIN.fullmatch(normalizado):
            raise ValorInvalido("El VIN debe tener 17 caracteres alfanuméricos, sin I, O ni Q.")
        object.__setattr__(self, "valor", normalizado)

    def __str__(self) -> str:
        return self.valor
