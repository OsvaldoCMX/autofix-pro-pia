"""Almacén en memoria: hace el papel de la base de datos y solo guarda datos confirmados."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from application.puertos import AlertaInterna
from application.unidad_de_trabajo import RegistroDeBitacora
from domain.clientes.cliente import Cliente
from domain.cotizaciones.cotizacion import Cotizacion
from domain.empleados.empleado import Empleado
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.vehiculos.vehiculo import Vehiculo


@dataclass
class DatosEnMemoria:
    ordenes: dict[str, OrdenDeServicio] = field(default_factory=dict)
    cotizaciones: dict[str, Cotizacion] = field(default_factory=dict)
    clientes: dict[str, Cliente] = field(default_factory=dict)
    vehiculos: dict[str, Vehiculo] = field(default_factory=dict)
    empleados: dict[str, Empleado] = field(default_factory=dict)
    alertas: list[AlertaInterna] = field(default_factory=list)
    bitacora: list[RegistroDeBitacora] = field(default_factory=list)
    ultimo_folio_de_orden: int = 0
    ultimo_folio_de_cotizacion: int = 0
    ultimo_folio_de_cliente: int = 0


class AlmacenEnMemoria:
    def __init__(self, empleados: Iterable[Empleado] = ()) -> None:
        self.datos = DatosEnMemoria(
            empleados={empleado.id_empleado: empleado for empleado in empleados}
        )
