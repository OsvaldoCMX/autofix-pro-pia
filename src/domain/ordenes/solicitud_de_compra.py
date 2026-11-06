"""Entidad interna de la orden: petición de una refacción no disponible (US-010)."""
from __future__ import annotations

from datetime import datetime

from domain.compartido.errores import (
    SolicitudNoPermitida,
    TransicionDeEstadoNoPermitida,
    ValorInvalido,
)
from domain.compartido.valores import texto_requerido
from domain.ordenes.estados import MAQUINA_DE_SOLICITUD, EstadoSolicitud

_S = EstadoSolicitud


class SolicitudDeCompra:
    def __init__(
        self,
        id_solicitud: int,
        id_trabajo: int,
        refaccion: str,
        cantidad: int,
        fecha_solicitud: datetime,
    ) -> None:
        if cantidad <= 0:
            raise ValorInvalido("La cantidad de la refacción debe ser mayor a cero.")
        self.id = id_solicitud
        self.id_trabajo = id_trabajo
        self.refaccion = texto_requerido(refaccion, "La solicitud debe describir la refacción.")
        self.cantidad = cantidad
        self.fecha_solicitud = fecha_solicitud
        self.estado = _S.SOLICITADA
        self.fecha_llegada: datetime | None = None
        self.fecha_aviso_al_cliente: datetime | None = None

    @property
    def esta_pendiente(self) -> bool:
        return self.estado is _S.SOLICITADA

    def marcar_disponible(self, fecha: datetime) -> None:
        if not self.esta_pendiente:
            raise TransicionDeEstadoNoPermitida(
                f"La llegada de la refacción «{self.refaccion}» ya estaba registrada."
            )
        MAQUINA_DE_SOLICITUD.validar(self.estado, _S.DISPONIBLE)
        self.estado = _S.DISPONIBLE
        self.fecha_llegada = fecha

    def registrar_aviso_al_cliente(self, fecha: datetime) -> None:
        """El aviso por retraso no cambia el estado de la solicitud (modelo-de-dominio.md §5.3)."""
        if not self.esta_pendiente:
            raise SolicitudNoPermitida("La refacción ya llegó: no hay retraso que avisar.")
        if self.fecha_aviso_al_cliente is not None:
            raise SolicitudNoPermitida("El aviso al cliente ya estaba registrado.")
        self.fecha_aviso_al_cliente = fecha
