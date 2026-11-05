"""Repository del Aggregate Empleado (interfaz del dominio)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.empleados.empleado import Empleado


class RepositorioDeEmpleados(ABC):
    @abstractmethod
    def obtener(self, id_empleado: str) -> Empleado:
        """Devuelve el empleado o lanza `EmpleadoNoEncontrado`."""
