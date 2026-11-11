"""Estados de la Orden, el Trabajo y la Solicitud de Compra (modelo-de-dominio.md §5)."""
from __future__ import annotations

from enum import Enum

from domain.compartido.maquina_de_estados import MaquinaDeEstados


class EstadoOrden(Enum):
    RECIBIDA = "Recibida"
    EN_DIAGNOSTICO = "En Diagnóstico"
    COTIZADA = "Cotizada"
    AUTORIZADA = "Autorizada"
    EN_REPARACION = "En Reparación"
    EN_ESPERA_DE_REFACCION = "En Espera de Refacción"
    PAUSADA_POR_RETIRO_DE_VEHICULO = "Pausada por Retiro de Vehículo"
    LISTA_PARA_ENTREGA = "Lista para Entrega"
    PAGADA = "Pagada"
    POR_COBRAR_CREDITO = "Por Cobrar (Crédito)"
    CERRADA = "Cerrada"
    CERRADA_SIN_REPARACION = "Cerrada sin Reparación"
    CANCELADA = "Cancelada"


class EstadoTrabajo(Enum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En Progreso"
    COMPLETADO = "Completado"
    NO_AUTORIZADO = "No Autorizado"


class EstadoSolicitud(Enum):
    SOLICITADA = "Solicitada"
    DISPONIBLE = "Disponible"


_O = EstadoOrden
_T = EstadoTrabajo
_S = EstadoSolicitud

# Una orden en cualquier otro estado está abierta (Glosario, «Listado de órdenes» y «Orden Abierta»).
# La condición del índice `uq_ordenes_una_abierta_por_vehiculo` usa esta misma lista (RN-27).
ESTADOS_DE_ORDEN_CERRADA: frozenset[EstadoOrden] = frozenset(
    {_O.CERRADA, _O.CERRADA_SIN_REPARACION, _O.CANCELADA}
)


def esta_abierta(estado: EstadoOrden) -> bool:
    return estado not in ESTADOS_DE_ORDEN_CERRADA


MAQUINA_DE_ORDEN: MaquinaDeEstados[EstadoOrden] = MaquinaDeEstados(
    "La orden",
    {
        _O.RECIBIDA: {_O.EN_DIAGNOSTICO, _O.CANCELADA},
        _O.EN_DIAGNOSTICO: {_O.COTIZADA, _O.CANCELADA},
        _O.COTIZADA: {_O.AUTORIZADA, _O.CERRADA_SIN_REPARACION},
        _O.AUTORIZADA: {_O.EN_REPARACION, _O.EN_ESPERA_DE_REFACCION},
        _O.EN_REPARACION: {_O.EN_ESPERA_DE_REFACCION, _O.LISTA_PARA_ENTREGA},
        _O.EN_ESPERA_DE_REFACCION: {
            _O.AUTORIZADA,
            _O.EN_REPARACION,
            _O.PAUSADA_POR_RETIRO_DE_VEHICULO,
        },
        _O.PAUSADA_POR_RETIRO_DE_VEHICULO: {
            _O.EN_ESPERA_DE_REFACCION,
            _O.AUTORIZADA,
            _O.EN_REPARACION,
        },
        _O.LISTA_PARA_ENTREGA: {_O.PAGADA, _O.POR_COBRAR_CREDITO},
        _O.PAGADA: {_O.CERRADA},
        _O.POR_COBRAR_CREDITO: {_O.CERRADA},
    },
    finales=ESTADOS_DE_ORDEN_CERRADA,
)

MAQUINA_DE_TRABAJO: MaquinaDeEstados[EstadoTrabajo] = MaquinaDeEstados(
    "El trabajo",
    {_T.PENDIENTE: {_T.EN_PROGRESO}, _T.EN_PROGRESO: {_T.COMPLETADO}},
    finales={_T.COMPLETADO, _T.NO_AUTORIZADO},
)

MAQUINA_DE_SOLICITUD: MaquinaDeEstados[EstadoSolicitud] = MaquinaDeEstados(
    "La solicitud de compra",
    {_S.SOLICITADA: {_S.DISPONIBLE}},
    finales={_S.DISPONIBLE},
)
