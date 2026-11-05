"""Arma la aplicación en memoria para las pruebas, como lo hará el Composition Root."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TypeVar
from unittest.mock import Mock
from zoneinfo import ZoneInfo

from application.comandos import (
    AsignarTecnicoParaDiagnostico,
    DatosDeVehiculo,
    RegistrarCliente,
    RegistrarDiagnostico,
    RegistrarOrden,
)
from application.puertos import PublicadorDeEventos, Reloj
from application.servicios.servicio_de_cancelacion import ServicioDeCancelacion
from application.servicios.servicio_de_diagnostico import ServicioDeDiagnostico
from application.servicios.servicio_de_recepcion import ServicioDeRecepcion
from domain.clientes.cliente import TipoCliente
from domain.empleados.empleado import Empleado, RolDeEmpleado
from domain.ordenes.valores import NivelDeCombustible
from infrastructure.memoria.almacen import AlmacenEnMemoria, DatosEnMemoria
from infrastructure.memoria.unidad_de_trabajo import UnidadDeTrabajoEnMemoria

S = TypeVar("S")

PARTICULAR = RegistrarCliente("Luis Peña", telefono="81-2222", correo="luis@correo.test")
FLOTILLA = RegistrarCliente(
    "Transportes Norte SA",
    TipoCliente.FLOTILLA,
    "81-3333",
    "contacto@norte.test",
    "Transportes Norte",
    "Ana Torres",
    "81-1111",
    "ana@norte.test",
)
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

    def _armar(self, servicio: type[S]) -> S:
        return servicio(self.uow(), self.reloj, self.publicador)

    @property
    def recepcion(self) -> ServicioDeRecepcion:
        return self._armar(ServicioDeRecepcion)

    @property
    def cancelacion(self) -> ServicioDeCancelacion:
        return self._armar(ServicioDeCancelacion)

    @property
    def diagnostico(self) -> ServicioDeDiagnostico:
        return self._armar(ServicioDeDiagnostico)


# ------------------------------------------------------------------ pasos para llegar a un estado
def recibida(taller: Taller, flotilla: bool = False) -> str:
    consecutivo = len(taller.datos.ordenes) + 1
    resultado = taller.recepcion.registrar_orden(
        RegistrarOrden(
            ASESOR,
            f"ABC{consecutivo:03d}",
            "Ruido al frenar",
            45000,
            NivelDeCombustible.MEDIO,
            DatosDeVehiculo(f"1HGCM82633A{consecutivo:06d}", "Nissan", "Versa", 2020),
            cliente=FLOTILLA if flotilla else PARTICULAR,
        )
    )
    return resultado.numero_orden


def en_diagnostico(taller: Taller, flotilla: bool = False, tecnico: str = TECNICO) -> str:
    numero = recibida(taller, flotilla)
    taller.diagnostico.asignar_tecnico(AsignarTecnicoParaDiagnostico(numero, tecnico))
    return numero


def diagnosticada(taller: Taller, flotilla: bool = False, tecnico: str = TECNICO) -> str:
    numero = en_diagnostico(taller, flotilla, tecnico)
    taller.diagnostico.registrar_diagnostico(
        RegistrarDiagnostico(numero, tecnico, "Balatas gastadas", "Cambiar balatas")
    )
    return numero
