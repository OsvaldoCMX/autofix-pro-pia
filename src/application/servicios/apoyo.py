"""Comprobaciones que comparten varios servicios."""
from __future__ import annotations

from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.compartido.errores import ValorInvalido
from domain.empleados.empleado import RolDeEmpleado


def exigir_tecnico(uow: UnidadDeTrabajo, id_empleado: str) -> None:
    """Solo se asignan órdenes y trabajos a un empleado con rol Técnico (CA-035, CA-036)."""
    empleado = uow.empleados.obtener(id_empleado)
    if not empleado.tiene_rol(RolDeEmpleado.TECNICO):
        raise ValorInvalido(f"{empleado.nombre} no es Técnico: no se le puede asignar trabajo.")
