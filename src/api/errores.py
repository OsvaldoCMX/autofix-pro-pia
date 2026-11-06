"""Traduce cada error a su código HTTP y al formato `{error, detalle, codigo}` (ADR-008)."""
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from domain.compartido import errores as dominio

_bitacora = logging.getLogger(__name__)

CODIGOS_DE_ERROR: dict[type[dominio.ErrorDeDominio], int] = {
    dominio.ValorInvalido: 422,
    dominio.CotizacionSinTrabajos: 422,
    dominio.TransicionDeEstadoNoPermitida: 409,
    dominio.OperacionDeCotizacionNoPermitida: 409,
    dominio.DiagnosticoRequerido: 409,
    dominio.DiagnosticoNoModificable: 409,
    dominio.AutorizanteNoValido: 409,
    dominio.TrabajoNoAutorizado: 409,
    dominio.SolicitudNoPermitida: 409,
    dominio.TrabajoNoPermitido: 409,
    dominio.TrabajoDeOtroTecnico: 403,
    dominio.PagoNoPermitido: 409,
    dominio.EntregaNoPermitida: 409,
    dominio.CancelacionNoPermitida: 409,
    dominio.OrdenNoEncontrada: 404,
    dominio.CotizacionNoEncontrada: 404,
    dominio.ClienteNoEncontrado: 404,
    dominio.VehiculoNoEncontrado: 404,
    dominio.EmpleadoNoEncontrado: 404,
    dominio.TrabajoNoEncontrado: 404,
    dominio.SolicitudNoEncontrada: 404,
}
_CODIGO_POR_DEFECTO = 409

_MENSAJES_DE_VALIDACION = {
    "missing": "Falta el dato «{campo}».",
    "extra_forbidden": "El dato «{campo}» no se reconoce.",
    "string_too_long": "El dato «{campo}» no puede tener más de {max_length} caracteres.",
    "string_type": "El dato «{campo}» debe ser texto.",
    "string_pattern_mismatch": (
        "El dato «{campo}» debe ser un importe con dos decimales, por ejemplo \"1500.00\"."
    ),
    "greater_than_equal": "El dato «{campo}» no puede ser menor que {ge}.",
    "less_than_equal": "El dato «{campo}» no puede ser mayor que {le}.",
    "int_parsing": "El dato «{campo}» debe ser un número entero.",
    "int_type": "El dato «{campo}» debe ser un número entero.",
    "bool_type": "El dato «{campo}» debe ser verdadero o falso.",
    "bool_parsing": "El dato «{campo}» debe ser verdadero o falso.",
    "enum": "El dato «{campo}» debe ser una de estas opciones: {expected}.",
    "value_error": "El dato «{campo}» contiene caracteres no válidos.",
    "string_unicode": "El dato «{campo}» contiene caracteres no válidos.",
}
_MENSAJE_DE_VALIDACION_GENERAL = "El dato «{campo}» no es válido."
_MENSAJES_DE_HTTP = {
    404: ("RutaNoEncontrada", "La ruta solicitada no existe."),
    405: ("MetodoNoPermitido", "La ruta no admite este método."),
}


class ErrorDeAcceso(Exception):
    """El problema es quién hace la petición, no una regla del negocio."""

    codigo = 401
    mensaje = "Falta el token de acceso o no es válido."


class TokenInvalido(ErrorDeAcceso):
    pass


class RolNoPermitido(ErrorDeAcceso):
    codigo = 403
    mensaje = "Su rol no tiene permiso para usar esta función."


class FuncionNoImplementada(Exception):
    """Rutas P2 que se construyen en la Fase 10 (decisiones-tecnicas.md §8)."""


def respuesta_de_error(
    error: str, detalle: str, codigo: int, encabezados: Mapping[str, str] | None = None
) -> JSONResponse:
    return JSONResponse(
        {"error": error, "detalle": detalle, "codigo": codigo},
        status_code=codigo,
        headers=encabezados,
    )


def codigo_de(error: dominio.ErrorDeDominio) -> int:
    return CODIGOS_DE_ERROR.get(type(error), _CODIGO_POR_DEFECTO)


def mensaje_de_validacion(error: Mapping[str, Any]) -> str:
    """Pydantic escribe en inglés: el usuario del taller recibe el mensaje en español."""
    ubicacion = [str(parte) for parte in error["loc"][1:]]  # el primero es body, query o path
    if not ubicacion:
        return "Falta el cuerpo de la petición."
    # El nombre de un dato desconocido viene del cliente: podría no poder escribirse como UTF-8.
    campo = ".".join(ubicacion).encode("utf-8", "replace").decode("utf-8")
    plantilla = _MENSAJES_DE_VALIDACION.get(error["type"], _MENSAJE_DE_VALIDACION_GENERAL)
    return plantilla.format(campo=campo, **error.get("ctx", {}))


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(dominio.ErrorDeDominio, _error_de_dominio)
    app.add_exception_handler(ErrorDeAcceso, _error_de_acceso)
    app.add_exception_handler(FuncionNoImplementada, _funcion_no_implementada)
    app.add_exception_handler(RequestValidationError, _error_de_validacion)
    app.add_exception_handler(StarletteHTTPException, _error_http)
    app.add_exception_handler(Exception, _error_inesperado)


def _error_de_dominio(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, dominio.ErrorDeDominio)
    return respuesta_de_error(type(error).__name__, str(error), codigo_de(error))


def _error_de_acceso(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, ErrorDeAcceso)
    encabezados = {"WWW-Authenticate": "Bearer"} if error.codigo == 401 else None
    return respuesta_de_error(type(error).__name__, error.mensaje, error.codigo, encabezados)


def _funcion_no_implementada(_: Request, error: Exception) -> JSONResponse:
    return respuesta_de_error(type(error).__name__, str(error), 501)


def _error_de_validacion(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)
    problemas = error.errors()
    if any(problema["type"] == "json_invalid" for problema in problemas):
        return respuesta_de_error("JsonMalFormado", "El cuerpo de la petición no es JSON válido.", 400)
    return respuesta_de_error("ValorInvalido", mensaje_de_validacion(problemas[0]), 422)


def _error_http(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, StarletteHTTPException)
    nombre, detalle = _MENSAJES_DE_HTTP.get(error.status_code, ("ErrorHttp", str(error.detail)))
    return respuesta_de_error(nombre, detalle, error.status_code)


def _error_inesperado(_: Request, error: Exception) -> JSONResponse:
    """El detalle queda en la bitácora; el usuario nunca ve datos internos."""
    _bitacora.error("Error inesperado", exc_info=error)
    return respuesta_de_error("ErrorInterno", "Ocurrió un error inesperado. Intente de nuevo.", 500)
