"""Seguridad con un token fijo por empleado y una dependencia por rol (ADR-012).

Sistema no es un empleado: solo tiene acceso a la revisión de plazos (ADR-015).
"""
from __future__ import annotations

import secrets
from collections.abc import Callable, Mapping
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.errores import CLAVE_DEL_SISTEMA, RolNoPermitido, TokenInvalido
from domain.empleados.empleado import Empleado, RolDeEmpleado

_esquema_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="TokenDeEmpleado",
    description="Token del empleado (variables TOKEN_ASESOR, TOKEN_TECNICO, …).",
)
Credenciales = Annotated[HTTPAuthorizationCredentials | None, Depends(_esquema_bearer)]


def _coincide(token: str, esperado: str) -> bool:
    """Compara bytes: `compare_digest` lanza un error si un texto no es ASCII."""
    return secrets.compare_digest(token.encode("utf-8"), esperado.encode("utf-8"))


class DirectorioDeTokens:
    def __init__(self, empleados: Mapping[str, Empleado], token_de_sistema: str | None) -> None:
        self._empleados = empleados
        self._token_de_sistema = token_de_sistema

    def empleado_del_token(self, token: str) -> Empleado | None:
        encontrado = None
        for esperado, empleado in self._empleados.items():
            if _coincide(token, esperado):
                encontrado = empleado
        return encontrado

    def es_del_sistema(self, token: str) -> bool:
        return self._token_de_sistema is not None and _coincide(token, self._token_de_sistema)


def _directorio(request: Request) -> DirectorioDeTokens:
    return request.app.state.contenedor.directorio_de_tokens


def _token(credenciales: HTTPAuthorizationCredentials | None) -> str:
    if credenciales is None:
        raise TokenInvalido()
    return credenciales.credentials


def _empleado(
    request: Request, credenciales: HTTPAuthorizationCredentials | None, error_de_sistema: str | None
) -> Empleado:
    """401 si el token falta o no es válido; 403 si es el de Sistema, que no es un empleado."""
    directorio = _directorio(request)
    token = _token(credenciales)
    empleado = directorio.empleado_del_token(token)
    if empleado is None:
        if directorio.es_del_sistema(token):
            raise RolNoPermitido(error_de_sistema)
        raise TokenInvalido()
    return empleado


def requiere_rol(*roles: RolDeEmpleado) -> Callable[..., Empleado]:
    """Entrega el empleado del token: 401 si falta o no es válido, 403 si su rol no puede pasar."""

    def dependencia(request: Request, credenciales: Credenciales) -> Empleado:
        empleado = _empleado(request, credenciales, None)
        if empleado.rol not in roles:
            raise RolNoPermitido()
        return empleado

    return dependencia


def requiere_empleado(request: Request, credenciales: Credenciales) -> Empleado:
    """Inicio de sesión de la página: con la clave de Sistema dice que no es de un empleado."""
    return _empleado(request, credenciales, CLAVE_DEL_SISTEMA)


def requiere_sistema(request: Request, credenciales: Credenciales) -> None:
    directorio = _directorio(request)
    token = _token(credenciales)
    if directorio.es_del_sistema(token):
        return
    if directorio.empleado_del_token(token) is not None:
        raise RolNoPermitido()
    raise TokenInvalido()


Asesor = Annotated[Empleado, Depends(requiere_rol(RolDeEmpleado.ASESOR))]
Tecnico = Annotated[Empleado, Depends(requiere_rol(RolDeEmpleado.TECNICO))]
Gerente = Annotated[Empleado, Depends(requiere_rol(RolDeEmpleado.GERENTE))]
Compras = Annotated[Empleado, Depends(requiere_rol(RolDeEmpleado.COMPRAS))]
Caja = Annotated[Empleado, Depends(requiere_rol(RolDeEmpleado.CAJA))]
CualquierEmpleado = Annotated[Empleado, Depends(requiere_rol(*RolDeEmpleado))]
EmpleadoDeLaSesion = Annotated[Empleado, Depends(requiere_empleado)]
SOLO_ASESOR = Depends(requiere_rol(RolDeEmpleado.ASESOR))
SOLO_TECNICO = Depends(requiere_rol(RolDeEmpleado.TECNICO))
SOLO_GERENTE = Depends(requiere_rol(RolDeEmpleado.GERENTE))
SOLO_COMPRAS = Depends(requiere_rol(RolDeEmpleado.COMPRAS))
SOLO_CAJA = Depends(requiere_rol(RolDeEmpleado.CAJA))
SOLO_SISTEMA = Depends(requiere_sistema)
