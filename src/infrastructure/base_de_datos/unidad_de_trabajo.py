"""Unit of Work con SQLAlchemy: una conexión y una transacción por operación (ADR-002, ADR-016).

Los Aggregates y la bitácora de eventos se confirman juntos. Cerrar la conexión deshace lo que no
se haya confirmado; por eso `_deshacer` también sirve si el propio commit falla.
"""
from __future__ import annotations

from sqlalchemy import Connection, Engine, RootTransaction, insert

from application.unidad_de_trabajo import (
    RegistroDeBitacora,
    UnidadDeTrabajo,
    eventos_de,
)
from domain.compartido.eventos import EventoDeDominio, RaizDeAgregado
from infrastructure.base_de_datos.repositorios import (
    RepositorioDeAlertasSqlAlchemy,
    RepositorioDeClientesSqlAlchemy,
    RepositorioDeCotizacionesSqlAlchemy,
    RepositorioDeEmpleadosSqlAlchemy,
    RepositorioDeOrdenesSqlAlchemy,
    RepositorioDeVehiculosSqlAlchemy,
)
from infrastructure.base_de_datos.tablas import eventos


class UnidadDeTrabajoSqlAlchemy(UnidadDeTrabajo):
    def __init__(self, motor: Engine) -> None:
        self._motor = motor

    def _iniciar(self) -> None:
        self._conexion: Connection = self._motor.connect()
        self._transaccion: RootTransaction = self._conexion.begin()
        self._vistos: list[RaizDeAgregado] = []
        self.ordenes = RepositorioDeOrdenesSqlAlchemy(self._conexion, self._vistos)
        self.cotizaciones = RepositorioDeCotizacionesSqlAlchemy(self._conexion, self._vistos)
        self.clientes = RepositorioDeClientesSqlAlchemy(self._conexion)
        self.vehiculos = RepositorioDeVehiculosSqlAlchemy(self._conexion)
        self.empleados = RepositorioDeEmpleadosSqlAlchemy(self._conexion)
        self.alertas = RepositorioDeAlertasSqlAlchemy(self._conexion)

    def _recolectar_eventos(self) -> list[EventoDeDominio]:
        return eventos_de(self._vistos)

    def _guardar_bitacora(self, registros: list[RegistroDeBitacora]) -> None:
        if registros:
            self._conexion.execute(
                insert(eventos),
                [
                    {
                        "tipo": registro.tipo,
                        "agregado": registro.agregado,
                        "id_agregado": registro.id_agregado,
                        "datos": registro.datos,
                        "ocurrido_en": registro.ocurrido_en,
                    }
                    for registro in registros
                ],
            )

    def _confirmar(self) -> None:
        self._transaccion.commit()
        self._conexion.close()

    def _deshacer(self) -> None:
        self._conexion.close()
