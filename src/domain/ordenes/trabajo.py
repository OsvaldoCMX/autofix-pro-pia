"""Entidad interna de la orden: servicio de mano de obra autorizado o no (Glosario: Trabajo)."""
from __future__ import annotations

from domain.compartido.valores import Dinero
from domain.ordenes.estados import MAQUINA_DE_TRABAJO, EstadoTrabajo

_T = EstadoTrabajo


class Trabajo:
    def __init__(
        self,
        id_trabajo: int,
        descripcion: str,
        importe: Dinero,
        estado: EstadoTrabajo = _T.PENDIENTE,
        id_cotizacion: str | None = None,
        numero_linea: int | None = None,
    ) -> None:
        self.id = id_trabajo
        self.descripcion = descripcion
        self.importe = importe
        self.estado = estado
        self.tecnico: str | None = None
        self.id_cotizacion = id_cotizacion
        self.numero_linea = numero_linea

    @property
    def esta_autorizado(self) -> bool:
        return self.estado is not _T.NO_AUTORIZADO

    @property
    def fue_iniciado(self) -> bool:
        return self.estado in (_T.EN_PROGRESO, _T.COMPLETADO)

    @property
    def esta_completado(self) -> bool:
        return self.estado is _T.COMPLETADO

    def asignar(self, tecnico: str) -> None:
        """La asignación no cambia el estado del trabajo (modelo-de-dominio.md §5.3)."""
        self.tecnico = tecnico

    def iniciar(self) -> None:
        self._cambiar_estado(_T.EN_PROGRESO)

    def completar(self) -> None:
        self._cambiar_estado(_T.COMPLETADO)

    def _cambiar_estado(self, nuevo: EstadoTrabajo) -> None:
        MAQUINA_DE_TRABAJO.validar(self.estado, nuevo)
        self.estado = nuevo
