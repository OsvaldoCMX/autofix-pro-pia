"""Tipos y reglas que comparten los esquemas de la API (ADR-008).

Los límites repiten los de `database/01_esquema.sql`: un texto más largo que su columna debe
responder 422 aquí, no 500 al guardarse en PostgreSQL. Una prueba los compara con `tablas.py`.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from domain.compartido.errores import ValorInvalido

LARGO_DE_NOMBRE = 120  # clientes.nombre, clientes.correo, cotizaciones.decision_autorizante…
LARGO_DE_TELEFONO = 20  # clientes.telefono, clientes.responsable_telefono
LARGO_DE_IDENTIFICADOR = 20  # clientes.id, empleados.id
LARGO_DE_MARCA = 60  # vehiculos.marca, vehiculos.modelo
LARGO_DE_VIN = 17  # vehiculos.vin
LARGO_DE_REFACCION = 200  # solicitudes_de_compra.refaccion, refacciones_cotizadas.descripcion
ENTERO_MAXIMO = 2_147_483_647  # INTEGER de PostgreSQL
ANIO_MINIMO = 1900  # CHECK de vehiculos.anio
ANIO_MAXIMO = 2100
PATRON_DE_IMPORTE = r"^[0-9]{1,10}\.[0-9]{2}$"  # NUMERIC(12,2), siempre como texto

TextoDeNombre = Annotated[str, StringConstraints(max_length=LARGO_DE_NOMBRE)]
TextoDeTelefono = Annotated[str, StringConstraints(max_length=LARGO_DE_TELEFONO)]
TextoDeIdentificador = Annotated[str, StringConstraints(max_length=LARGO_DE_IDENTIFICADOR)]
TextoDeMarca = Annotated[str, StringConstraints(max_length=LARGO_DE_MARCA)]
TextoDeVin = Annotated[str, StringConstraints(max_length=LARGO_DE_VIN)]
TextoDeRefaccion = Annotated[str, StringConstraints(max_length=LARGO_DE_REFACCION)]
Importe = Annotated[
    str,
    StringConstraints(pattern=PATRON_DE_IMPORTE),
    Field(description="Importe como texto con dos decimales.", examples=["1500.00"]),
]
EnteroPositivo = Annotated[int, Field(ge=1, le=ENTERO_MAXIMO)]
EnteroNoNegativo = Annotated[int, Field(ge=0, le=ENTERO_MAXIMO)]


def tiene_caracteres_no_validos(texto: str) -> bool:
    """El carácter nulo y los sustitutos sueltos no se pueden guardar en PostgreSQL."""
    return any(caracter == "\x00" or "\ud800" <= caracter <= "\udfff" for caracter in texto)


class ModeloDeEntrada(BaseModel):
    """Base de los cuerpos JSON: rechaza datos desconocidos y caracteres que no se pueden guardar."""

    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="after")
    @classmethod
    def _sin_caracteres_no_validos(cls, valor: Any) -> Any:
        if isinstance(valor, str) and tiene_caracteres_no_validos(valor):
            raise ValueError("contiene caracteres no válidos")
        return valor


class ModeloDeSalida(BaseModel):
    """Base de las respuestas: se arman desde los DTO de la capa de aplicación."""

    model_config = ConfigDict(from_attributes=True)


class RespuestaDeError(BaseModel):
    """Formato único de los errores de la API."""

    error: str
    detalle: str
    codigo: int


_DESCRIPCIONES = {
    400: "JSON mal formado.",
    401: "Falta el token o no es válido.",
    403: "Rol no permitido o trabajo de otro técnico.",
    404: "No existe.",
    409: "Viola una regla o transición del negocio.",
    422: "Un dato es inválido.",
    501: "Función P2 aún no implementada.",
}


def errores(*codigos: int) -> dict[int | str, dict[str, Any]]:
    """Declara en Swagger los errores de una ruta, con el formato único."""
    return {
        codigo: {"model": RespuestaDeError, "description": _DESCRIPCIONES[codigo]}
        for codigo in codigos
    }


def rechazar_caracteres_no_validos(request: Request) -> None:
    """Revisa la ruta y los parámetros, que no pasan por `ModeloDeEntrada`."""
    textos = [request.scope["path"], *(valor for _, valor in request.query_params.multi_items())]
    if any(tiene_caracteres_no_validos(texto) for texto in textos):
        raise ValorInvalido("La petición contiene caracteres no válidos.")
