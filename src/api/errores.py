"""Traduce cada error a su código HTTP y al formato `{error, detalle, codigo}` (ADR-008)."""
from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.esquemas.comunes import ENTERO_MAXIMO
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
    dominio.VehiculoConOrdenAbierta: 409,
    dominio.CorreccionNoPermitida: 409,
    dominio.OrdenNoEncontrada: 404,
    dominio.CotizacionNoEncontrada: 404,
    dominio.ClienteNoEncontrado: 404,
    dominio.VehiculoNoEncontrado: 404,
    dominio.EmpleadoNoEncontrado: 404,
    dominio.TrabajoNoEncontrado: 404,
    dominio.SolicitudNoEncontrada: 404,
}
_CODIGO_POR_DEFECTO = 409

_IMPORTE_CON_DECIMALES = (
    "El dato «{campo}» debe ser un importe con dos decimales, por ejemplo \"1500.00\"."
)
_NUMERO_DEMASIADO_GRANDE = "El número de «{campo}» es demasiado grande. Revise el dato."
_MENSAJES_DE_VALIDACION = {
    "missing": "Falta el dato «{campo}». Captúrelo e intente de nuevo.",
    "extra_forbidden": "El dato «{campo}» no se reconoce. Quítelo e intente de nuevo.",
    "string_too_long": "El dato «{campo}» no puede tener más de {max_length} caracteres.",
    "string_type": "El dato «{campo}» debe ser texto.",
    "string_pattern_mismatch": _IMPORTE_CON_DECIMALES,
    "greater_than_equal": (
        "El dato «{campo}» no puede ser menor que {ge}. Corríjalo e intente de nuevo."
    ),
    "less_than_equal": "El dato «{campo}» no puede ser mayor que {le}.",
    "int_parsing": "El dato «{campo}» debe ser un número entero.",
    "int_type": "El dato «{campo}» debe ser un número entero.",
    "int_from_float": "El dato «{campo}» debe ser un número entero.",
    "int_parsing_size": _NUMERO_DEMASIADO_GRANDE,
    "bool_type": "El dato «{campo}» debe ser verdadero o falso.",
    "bool_parsing": "El dato «{campo}» debe ser verdadero o falso.",
    "enum": "El dato «{campo}» debe ser una de estas opciones: {expected}.",
    "value_error": "El dato «{campo}» contiene caracteres no válidos.",
    "string_unicode": "El dato «{campo}» contiene caracteres no válidos.",
}
_MENSAJE_DE_VALIDACION_GENERAL = "El dato «{campo}» no es válido. Revíselo e intente de nuevo."
_SIN_CUERPO = "No se recibió la información solicitada. Capture los datos e intente de nuevo."
_FORMATO_INCORRECTO = (
    "La información enviada no tiene el formato correcto. Revísela e intente de nuevo."
)
_MENSAJES_DE_HTTP = {
    404: (
        "RutaNoEncontrada",
        "No encontramos lo que busca. Revise la dirección e intente de nuevo.",
    ),
    405: (
        "MetodoNoPermitido",
        "Esta función no se puede usar de esa manera. Revise la dirección e intente de nuevo.",
    ),
}
_MENSAJE_DE_HTTP_GENERAL = "No se pudo completar la solicitud. Intente de nuevo."
_MENSAJE_INESPERADO = (
    "Ocurrió un problema inesperado y no se pudo completar la operación. "
    "Intente de nuevo en unos minutos."
)

_NOMBRES_DE_CAMPO = {
    "motivo_de_ingreso": "motivo de ingreso",
    "nivel_de_combustible": "nivel de combustible",
    "anio": "año",
    "vin": "VIN",
    "telefono": "teléfono",
    "id_cliente": "clave del cliente",
    "responsable_nombre": "nombre del Responsable de Flotilla",
    "responsable_telefono": "teléfono del Responsable de Flotilla",
    "responsable_correo": "correo del Responsable de Flotilla",
    "nombre_del_autorizante": "nombre de quien autoriza",
    "rol_del_autorizante": "rol de quien autoriza",
    "orden": "número de orden",
    "id": "número de registro",
    "mano_de_obra": "mano de obra",
    "precio_unitario": "precio unitario",
    "forma": "forma de pago",
    "tipo": "tipo de cliente",
    "descripcion": "descripción",
    "tecnico": "técnico",
    "refaccion": "refacción",
    "id_trabajo": "trabajo",
    "ids_trabajos": "trabajos a asignar",
    "lineas_autorizadas": "trabajos autorizados",
    "aprobada": "decisión del Gerente",
    "numero": "número de trabajo",
    "archivo": "foto",
}
# Dato que contiene a otros: cómo se nombra solo y cómo se une con lo que contiene.
_CONTENEDORES = {
    "vehiculo": ("vehículo", "del vehículo"),
    "cliente": ("cliente", "del cliente"),
    "trabajos": ("trabajo {posicion}", "del trabajo {posicion}"),
    "refacciones": ("refacción {posicion}", "de la refacción {posicion}"),
}
_CAMPOS_DE_IMPORTE = {"monto", "mano_de_obra", "precio_unitario"}


class ErrorDeAcceso(Exception):
    """El problema es quién hace la petición, no una regla del negocio."""

    codigo = 401
    mensaje = (
        "No pudimos identificarlo: falta su clave de acceso o no es válida. "
        "Revísela e intente de nuevo."
    )


class TokenInvalido(ErrorDeAcceso):
    pass


class RolNoPermitido(ErrorDeAcceso):
    codigo = 403
    mensaje = "Su rol no tiene permiso para usar esta función. Pida apoyo al área encargada."


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
    ubicacion = error["loc"][1:]  # el primero es body, query o path
    if not ubicacion:
        return _SIN_CUERPO if error["type"] == "missing" else _FORMATO_INCORRECTO
    # El nombre de un dato desconocido viene del cliente: podría no poder escribirse como UTF-8.
    campo = nombre_del_campo(ubicacion).encode("utf-8", "replace").decode("utf-8")
    contexto = dict(error.get("ctx", {}))
    if "expected" in contexto:
        contexto["expected"] = _opciones_en_espanol(contexto["expected"])
    return _plantilla_de(error["type"], ubicacion, contexto).format(campo=campo, **contexto)


def nombre_del_campo(ubicacion: Sequence[str | int]) -> str:
    """`trabajos, 0, mano_de_obra` se muestra como «mano de obra del trabajo 1»."""
    tramos: list[tuple[str, int | None]] = []
    for parte in ubicacion:
        if isinstance(parte, int) and tramos:
            tramos[-1] = (tramos[-1][0], parte + 1)  # Pydantic cuenta desde 0; el usuario, desde 1
        else:
            tramos.append((str(parte), None))
    *contenedores, (campo, posicion) = tramos
    nombre = _nombre_solo(campo, posicion)
    for contenedor, en_posicion in reversed(contenedores):
        union = _CONTENEDORES.get(contenedor, ("", f"de {contenedor}"))[1]
        nombre = f"{nombre} {union.format(posicion=en_posicion)}"
    return nombre


def _nombre_solo(campo: str, posicion: int | None) -> str:
    solo = _CONTENEDORES.get(campo, ("",))[0]
    if solo and (posicion is not None or "{posicion}" not in solo):
        return solo.format(posicion=posicion)
    return _NOMBRES_DE_CAMPO.get(campo, campo)


def _plantilla_de(tipo: str, ubicacion: Sequence[str | int], contexto: Mapping[str, Any]) -> str:
    if tipo == "string_type" and ubicacion[-1] in _CAMPOS_DE_IMPORTE:
        return _IMPORTE_CON_DECIMALES
    if tipo == "less_than_equal" and contexto.get("le") == ENTERO_MAXIMO:
        return _NUMERO_DEMASIADO_GRANDE
    return _MENSAJES_DE_VALIDACION.get(tipo, _MENSAJE_DE_VALIDACION_GENERAL)


def _opciones_en_espanol(esperado: str) -> str:
    """Pydantic escribe `'A', 'B' or 'C'`; aquí queda «A», «B» o «C»."""
    return re.sub(r"'([^']*)'", r"«\1»", esperado).replace(" or ", " o ")


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
        return respuesta_de_error("JsonMalFormado", _FORMATO_INCORRECTO, 400)
    return respuesta_de_error("ValorInvalido", mensaje_de_validacion(problemas[0]), 422)


def _error_http(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, StarletteHTTPException)
    nombre, detalle = _MENSAJES_DE_HTTP.get(
        error.status_code, ("ErrorHttp", _MENSAJE_DE_HTTP_GENERAL)
    )
    return respuesta_de_error(nombre, detalle, error.status_code)


def _error_inesperado(_: Request, error: Exception) -> JSONResponse:
    """El detalle queda en la bitácora; el usuario nunca ve datos internos."""
    _bitacora.error("Error inesperado", exc_info=error)
    return respuesta_de_error("ErrorInterno", _MENSAJE_INESPERADO, 500)
