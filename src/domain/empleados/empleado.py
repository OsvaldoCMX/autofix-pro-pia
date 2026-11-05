"""Aggregate Empleado (raíz: Empleado)."""
from __future__ import annotations

from enum import Enum

from domain.compartido.errores import ValorInvalido
from domain.compartido.valores import texto_requerido


class RolDeEmpleado(Enum):
    ASESOR = "Asesor"
    TECNICO = "Técnico"
    GERENTE = "Gerente"
    COMPRAS = "Compras"
    CAJA = "Caja"


class Empleado:
    """Invariante: cada empleado tiene exactamente un rol."""

    def __init__(self, id_empleado: str, nombre: str, rol: RolDeEmpleado) -> None:
        if not isinstance(rol, RolDeEmpleado):
            raise ValorInvalido("El empleado debe tener exactamente un rol del taller.")
        self.id_empleado = id_empleado
        self.nombre = texto_requerido(nombre, "El empleado debe tener nombre.")
        self.rol = rol

    def tiene_rol(self, rol: RolDeEmpleado) -> bool:
        return self.rol is rol
