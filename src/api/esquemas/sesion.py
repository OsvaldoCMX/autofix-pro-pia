"""Respuesta del inicio de sesión de la página (ADR-017, interfaz-web.md §3)."""
from __future__ import annotations

from api.esquemas.comunes import ModeloDeSalida
from domain.empleados.empleado import Empleado, RolDeEmpleado

# Nombre del puesto como lo escribe el Glosario (§1); el rol es el valor que usa el código.
PUESTOS = {
    RolDeEmpleado.ASESOR: "Asesor de Servicio",
    RolDeEmpleado.TECNICO: "Técnico",
    RolDeEmpleado.GERENTE: "Gerente de Taller",
    RolDeEmpleado.COMPRAS: "Personal de Compras",
    RolDeEmpleado.CAJA: "Personal de Caja",
}


class SesionDelEmpleado(ModeloDeSalida):
    id_empleado: str
    nombre: str
    rol: str
    puesto: str

    @classmethod
    def del_empleado(cls, empleado: Empleado) -> SesionDelEmpleado:
        return cls(
            id_empleado=empleado.id_empleado,
            nombre=empleado.nombre,
            rol=empleado.rol.value,
            puesto=PUESTOS[empleado.rol],
        )
