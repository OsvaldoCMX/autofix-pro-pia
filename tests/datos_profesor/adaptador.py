"""Adapter: convierte los CSV del profesor al modelo propio (ADR-013, datos-profesor §2).

Las pruebas no dependen de `02_datos_iniciales.sql`: cada una carga solo su operación en una base
limpia, con las mismas reglas de conversión que ese script.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, insert

from domain.clientes.cliente import Cliente, TipoCliente
from domain.compartido.valores import VIN, NumeroOrden, Placas
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.vehiculos.vehiculo import Vehiculo
from infrastructure.base_de_datos.tablas import catalogo_servicios, servicios_solicitados
from infrastructure.base_de_datos.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from tests.unit.application.escenarios import ASESOR, ZONA_DEL_TALLER

RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "datos" / "profesor"
ORACULOS = RAIZ / "docs" / "datos-profesor"
HORA_DE_INGRESO = time(9, 0)
ACTIVADO = "1"


def leer_csv(ruta: Path) -> list[dict[str, str]]:
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo))


@dataclass(frozen=True)
class LineaDelProfesor:
    recurso_id: str
    descripcion: str
    precio: Decimal
    cantidad: int
    habilitado: bool

    @property
    def importe(self) -> Decimal:
        return self.precio * self.cantidad

    @property
    def descripcion_de_trabajo(self) -> str:
        return f"{self.descripcion} ({self.recurso_id}) x{self.cantidad}"


@dataclass(frozen=True)
class OperacionDelProfesor:
    operacion_id: str
    actor_id: str
    nombre_del_actor: str
    actor_activo: bool
    actor_preferente: bool
    promocion_activa: bool
    autorizado: bool
    fecha_solicitud: date
    referencia: str
    lineas: tuple[LineaDelProfesor, ...]

    @property
    def total(self) -> Decimal:
        return sum((linea.importe for linea in self.lineas), Decimal("0.00"))

    @property
    def ids_de_trabajos(self) -> list[int]:
        return list(range(1, len(self.lineas) + 1))

    @property
    def fecha_de_ingreso(self) -> datetime:
        local = datetime.combine(self.fecha_solicitud, HORA_DE_INGRESO, ZONA_DEL_TALLER)
        return local.astimezone(UTC)

    def trabajos(self) -> dict[str, list[dict[str, Any]]]:
        """Cuerpo de `POST /api/ordenes/{numero}/cotizaciones`: precio × cantidad, con `Decimal`."""
        return {
            "trabajos": [
                {
                    "numero": numero,
                    "descripcion": linea.descripcion_de_trabajo,
                    "mano_de_obra": f"{linea.importe:.2f}",
                }
                for numero, linea in enumerate(self.lineas, start=1)
            ]
        }


@cache
def leer_operaciones() -> dict[str, OperacionDelProfesor]:
    actores = {fila["actor_id"]: fila for fila in leer_csv(DATOS / "actores.csv")}
    catalogo = {fila["recurso_id"]: fila for fila in leer_csv(DATOS / "catalogo.csv")}
    lineas: dict[str, list[LineaDelProfesor]] = {}
    for fila in leer_csv(DATOS / "detalle_operaciones.csv"):
        servicio = catalogo[fila["recurso_id"]]
        lineas.setdefault(fila["operacion_id"], []).append(
            LineaDelProfesor(
                fila["recurso_id"],
                servicio["descripcion"],
                Decimal(servicio["precio_mxn"]),
                int(fila["cantidad"]),
                servicio["habilitado"] == ACTIVADO,
            )
        )
    return {
        fila["operacion_id"]: _operacion(fila, actores[fila["actor_id"]], lineas)
        for fila in leer_csv(DATOS / "operaciones.csv")
    }


def _operacion(
    fila: dict[str, str], actor: dict[str, str], lineas: dict[str, list[LineaDelProfesor]]
) -> OperacionDelProfesor:
    return OperacionDelProfesor(
        fila["operacion_id"],
        fila["actor_id"],
        actor["nombre"],
        actor["activo"] == ACTIVADO,
        actor["es_preferente"] == ACTIVADO,
        fila["promocion_activa"] == ACTIVADO,
        fila["autorizado"] == ACTIVADO,
        date.fromisoformat(fila["fecha_solicitud"]),
        fila["referencia"],
        tuple(lineas.get(fila["operacion_id"], ())),
    )


def cargar_operacion(motor: Engine, operacion: OperacionDelProfesor) -> None:
    """Deja la orden «Recibida», sin eventos: es el estado inicial, igual que la carga SQL."""
    placas = Placas(operacion.referencia.replace("_", "-"))
    with UnidadDeTrabajoSqlAlchemy(motor) as uow:
        uow.clientes.agregar(_cliente(operacion))
        uow.vehiculos.agregar(
            Vehiculo(placas, _vin(operacion), "Ficticia", "Referencia", 2020, operacion.actor_id)
        )
        uow.ordenes.agregar(
            OrdenDeServicio(
                NumeroOrden(operacion.operacion_id),
                operacion.actor_id,
                False,
                placas,
                ASESOR,
                f"Servicio de referencia {operacion.referencia}",
                operacion.fecha_de_ingreso,
            )
        )
        uow.confirmar()
    _cargar_servicios(motor, operacion)


def _cliente(operacion: OperacionDelProfesor) -> Cliente:
    consecutivo = operacion.actor_id.removeprefix("AUT-C")
    return Cliente(
        operacion.actor_id,
        operacion.nombre_del_actor,
        TipoCliente.PARTICULAR,
        f"81-0000-{int(consecutivo):04d}",
        f"{operacion.actor_id.lower()}@ejemplo.test",
    )


def _vin(operacion: OperacionDelProfesor) -> VIN:
    return VIN(f"AUT{int(operacion.operacion_id.removeprefix('AUT-O')):014d}")


def _cargar_servicios(motor: Engine, operacion: OperacionDelProfesor) -> None:
    if not operacion.lineas:
        return
    with motor.begin() as conexion:
        conexion.execute(
            insert(catalogo_servicios),
            [
                {
                    "recurso_id": linea.recurso_id,
                    "descripcion": linea.descripcion,
                    "precio_mxn": linea.precio,
                    "capacidad_o_stock": linea.cantidad,
                    "habilitado": linea.habilitado,
                }
                for linea in operacion.lineas
            ],
        )
        conexion.execute(
            insert(servicios_solicitados),
            [
                {
                    "numero_orden": operacion.operacion_id,
                    "recurso_id": linea.recurso_id,
                    "cantidad": linea.cantidad,
                }
                for linea in operacion.lineas
            ],
        )
