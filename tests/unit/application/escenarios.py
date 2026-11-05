"""Arma la aplicación en memoria para las pruebas, como lo hará el Composition Root."""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock
from zoneinfo import ZoneInfo

from application.puertos import PublicadorDeEventos, Reloj
from domain.empleados.empleado import Empleado, RolDeEmpleado
from infrastructure.memoria.almacen import AlmacenEnMemoria, DatosEnMemoria
from infrastructure.memoria.unidad_de_trabajo import UnidadDeTrabajoEnMemoria

ZONA_DEL_TALLER = ZoneInfo("America/Monterrey")
AHORA = datetime(2026, 10, 5, 15, 0, tzinfo=UTC)  # lunes
ASESOR = "EMP-001"
TECNICO = "EMP-002"
OTRO_TECNICO = "EMP-003"
GERENTE = "EMP-004"
COMPRAS = "EMP-005"
CAJA = "EMP-006"
EMPLEADOS = (
    Empleado(ASESOR, "Laura Méndez", RolDeEmpleado.ASESOR),
    Empleado(TECNICO, "Carlos Ruiz", RolDeEmpleado.TECNICO),
    Empleado(OTRO_TECNICO, "Diego Salinas", RolDeEmpleado.TECNICO),
    Empleado(GERENTE, "Patricia Garza", RolDeEmpleado.GERENTE),
    Empleado(COMPRAS, "Jorge Treviño", RolDeEmpleado.COMPRAS),
    Empleado(CAJA, "Sofía Leal", RolDeEmpleado.CAJA),
)


def poner_hora(reloj: Mock, fecha: datetime) -> None:
    reloj.ahora.return_value = fecha.astimezone(UTC)
    reloj.ahora_en_el_taller.return_value = fecha.astimezone(ZONA_DEL_TALLER)


class Taller:
    """Almacén con los 6 empleados, reloj falso y publicador simulado."""

    def __init__(self, publicador: PublicadorDeEventos | None = None) -> None:
        self.almacen = AlmacenEnMemoria(EMPLEADOS)
        self.reloj = Mock(spec=Reloj)
        poner_hora(self.reloj, AHORA)
        self.publicador = publicador or Mock(spec=PublicadorDeEventos)

    def uow(self) -> UnidadDeTrabajoEnMemoria:
        return UnidadDeTrabajoEnMemoria(self.almacen)

    @property
    def datos(self) -> DatosEnMemoria:
        return self.almacen.datos
