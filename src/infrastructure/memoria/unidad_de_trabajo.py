"""Unit of Work en memoria: trabaja sobre una copia y solo al confirmar reemplaza los datos.

Si una regla falla a la mitad, la copia se descarta: ningún Aggregate ni folio queda a medias.
"""
from __future__ import annotations

import copy

from application.unidad_de_trabajo import RegistroDeBitacora, UnidadDeTrabajo, eventos_de
from domain.compartido.eventos import EventoDeDominio, RaizDeAgregado
from infrastructure.memoria.almacen import AlmacenEnMemoria, DatosEnMemoria
from infrastructure.memoria.repositorios import (
    RepositorioDeAlertasEnMemoria,
    RepositorioDeClientesEnMemoria,
    RepositorioDeCotizacionesEnMemoria,
    RepositorioDeEmpleadosEnMemoria,
    RepositorioDeOrdenesEnMemoria,
    RepositorioDeVehiculosEnMemoria,
)


class UnidadDeTrabajoEnMemoria(UnidadDeTrabajo):
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self._almacen = almacen

    def _iniciar(self) -> None:
        self._copia: DatosEnMemoria = copy.deepcopy(self._almacen.datos)
        self._vistos: list[RaizDeAgregado] = []
        self.ordenes = RepositorioDeOrdenesEnMemoria(self._copia, self._vistos)
        self.cotizaciones = RepositorioDeCotizacionesEnMemoria(self._copia, self._vistos)
        self.clientes = RepositorioDeClientesEnMemoria(self._copia)
        self.vehiculos = RepositorioDeVehiculosEnMemoria(self._copia)
        self.empleados = RepositorioDeEmpleadosEnMemoria(self._copia)
        self.alertas = RepositorioDeAlertasEnMemoria(self._copia)

    def _recolectar_eventos(self) -> list[EventoDeDominio]:
        return eventos_de(self._vistos)

    def _guardar_bitacora(self, registros: list[RegistroDeBitacora]) -> None:
        self._copia.bitacora.extend(registros)

    def _confirmar(self) -> None:
        self._almacen.datos = self._copia

    def _deshacer(self) -> None:
        self._vistos = []
