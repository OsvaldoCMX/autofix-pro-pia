"""Lleva una orden a cualquier estado usando solo sus métodos públicos."""
from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

from domain.compartido.valores import Dinero, NumeroOrden, Placas
from domain.cotizaciones.valores import (
    Autorizante,
    DecisionDelCliente,
    RolDeAutorizante,
    TipoCotizacion,
    TrabajoDecidido,
)
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.valores import (
    Diagnostico,
    EstadoDeRecepcion,
    FormaDePago,
    NivelDeCombustible,
    Pago,
)

INICIO = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
DESPUES = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)
ASESOR = "EMP-001"
TECNICO = "EMP-002"
OTRO_TECNICO = "EMP-003"
CLIENTE = Autorizante("Luis Peña", RolDeAutorizante.CLIENTE)
RECEPCION = EstadoDeRecepcion(45000, NivelDeCombustible.MEDIO)
IMPORTE = Dinero(Decimal("1000.00"))

Constructor = Callable[[], OrdenDeServicio]


def decision(
    autorizados: int = 1,
    no_autorizados: int = 0,
    tipo: TipoCotizacion = TipoCotizacion.INICIAL,
    id_cotizacion: str = "COT-1",
) -> DecisionDelCliente:
    lineas = [
        TrabajoDecidido(numero, f"Trabajo {numero}", IMPORTE)
        for numero in range(1, autorizados + no_autorizados + 1)
    ]
    return DecisionDelCliente(
        id_cotizacion,
        tuple(lineas[:autorizados]),
        tuple(lineas[autorizados:]),
        CLIENTE,
        INICIO,
        tipo,
    )


def adicional(autorizados: int = 1, no_autorizados: int = 0) -> DecisionDelCliente:
    return decision(autorizados, no_autorizados, TipoCotizacion.ADICIONAL, "COT-2")


def recibida(flotilla: bool = False) -> OrdenDeServicio:
    return OrdenDeServicio.registrar(
        NumeroOrden("OS-1"),
        "CLI-1",
        flotilla,
        Placas("ABC-123"),
        ASESOR,
        "Ruido al frenar",
        RECEPCION,
        INICIO,
    )


def en_diagnostico(flotilla: bool = False) -> OrdenDeServicio:
    orden = recibida(flotilla)
    orden.asignar_tecnico_para_diagnostico(TECNICO, INICIO)
    return orden


def diagnostico(tecnico: str = TECNICO) -> Diagnostico:
    return Diagnostico("Balatas gastadas", "Cambiar balatas", tecnico, INICIO)


def diagnosticada(flotilla: bool = False) -> OrdenDeServicio:
    orden = en_diagnostico(flotilla)
    orden.registrar_diagnostico(diagnostico())
    return orden


def cotizada(flotilla: bool = False) -> OrdenDeServicio:
    orden = diagnosticada(flotilla)
    orden.marcar_cotizada(INICIO)
    return orden


def con_rechazo_total() -> OrdenDeServicio:
    orden = cotizada()
    orden.aplicar_decision(decision(autorizados=0, no_autorizados=2))
    return orden


def autorizada(
    trabajos: int = 1, no_autorizados: int = 0, flotilla: bool = False
) -> OrdenDeServicio:
    """Todos los trabajos autorizados quedan asignados a `TECNICO`."""
    orden = cotizada(flotilla)
    orden.aplicar_decision(decision(trabajos, no_autorizados))
    orden.asignar_trabajos(range(1, trabajos + 1), TECNICO, INICIO)
    return orden


def en_reparacion(trabajos: int = 1, flotilla: bool = False) -> OrdenDeServicio:
    """El trabajo 1 queda «En Progreso»."""
    orden = autorizada(trabajos, flotilla=flotilla)
    orden.iniciar_trabajo(1, TECNICO, INICIO)
    return orden


def en_espera(trabajos: int = 1) -> OrdenDeServicio:
    """Tiene la solicitud 1 pendiente, del trabajo 1, y ningún trabajo iniciado."""
    orden = autorizada(trabajos)
    orden.crear_solicitud_de_compra(1, "Balatas", 2, INICIO)
    return orden


def pausada(iniciada: bool = False) -> OrdenDeServicio:
    orden = en_reparacion() if iniciada else autorizada()
    orden.crear_solicitud_de_compra(1, "Balatas", 2, INICIO)
    orden.registrar_salida(INICIO)
    orden.confirmar_firma_de_nota(INICIO)
    return orden


def lista(flotilla: bool = False) -> OrdenDeServicio:
    orden = en_reparacion(flotilla=flotilla)
    orden.completar_trabajo(1, TECNICO, INICIO)
    return orden


def pago_del_total() -> Pago:
    return Pago(IMPORTE, FormaDePago.EFECTIVO, INICIO)


def pagada() -> OrdenDeServicio:
    orden = lista()
    orden.registrar_pago(pago_del_total())
    return orden


def por_cobrar() -> OrdenDeServicio:
    orden = lista(flotilla=True)
    orden.registrar_cargo_a_credito(INICIO)
    return orden


def cerrada() -> OrdenDeServicio:
    orden = pagada()
    orden.entregar(INICIO)
    return orden


def cerrada_sin_reparacion() -> OrdenDeServicio:
    orden = con_rechazo_total()
    orden.entregar_sin_reparacion(INICIO)
    return orden


def cancelada() -> OrdenDeServicio:
    orden = recibida()
    orden.cancelar("El cliente desistió", ASESOR, INICIO)
    return orden


def sin_eventos(orden: OrdenDeServicio) -> OrdenDeServicio:
    orden.extraer_eventos()
    return orden
