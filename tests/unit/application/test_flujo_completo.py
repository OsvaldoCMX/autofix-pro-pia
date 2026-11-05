"""Flujo completo con los servicios, las consultas y las alertas reales armados juntos."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from application.comandos import (
    AsignarTecnicoParaDiagnostico,
    AsignarTrabajos,
    CompletarTrabajo,
    DatosDeVehiculo,
    GenerarCotizacion,
    IniciarTrabajo,
    PresentarCotizacion,
    RegistrarCargoACredito,
    RegistrarCliente,
    RegistrarDiagnostico,
    RegistrarEntrega,
    RegistrarLlegadaDeRefaccion,
    RegistrarOrden,
    RegistrarPago,
    ReportarFallaAdicional,
    RevisarCotizacion,
    SolicitarRefaccion,
)
from application.consultas.consultas import (
    ConsultarEstadoDeOrden,
    ConsultarIngresosDelDia,
    ManejadorConsultarEstadoDeOrden,
    ManejadorConsultarIngresosDelDia,
)
from application.manejadores.alertas import ManejadoresDeAlertas
from domain.ordenes.valores import FormaDePago, NivelDeCombustible
from infrastructure.eventos.publicador_en_proceso import PublicadorEnProceso
from infrastructure.memoria.lector import LectorEnMemoria
from tests.unit.application.escenarios import (
    AHORA,
    ASESOR,
    FLOTILLA,
    PARTICULAR,
    TECNICO,
    Taller,
    decidir,
    poner_hora,
    trabajos,
)


@pytest.fixture
def taller() -> Taller:
    publicador = PublicadorEnProceso()
    armado = Taller(publicador)
    for tipo, manejador in ManejadoresDeAlertas(armado.uow).suscripciones().items():
        publicador.suscribir(tipo, manejador)
    return armado


def _recibir(taller: Taller, cliente: RegistrarCliente, placas: str, vin: str) -> str:
    return taller.recepcion.registrar_orden(
        RegistrarOrden(
            ASESOR,
            placas,
            "Ruido al frenar",
            45000,
            NivelDeCombustible.TRES_CUARTOS,
            DatosDeVehiculo(vin, "Nissan", "Versa", 2020),
            cliente=cliente,
        )
    ).numero_orden


def _hasta_el_diagnostico(taller: Taller, numero: str) -> None:
    taller.diagnostico.asignar_tecnico(AsignarTecnicoParaDiagnostico(numero, TECNICO))
    taller.diagnostico.registrar_diagnostico(
        RegistrarDiagnostico(numero, TECNICO, "Balatas gastadas", "Cambiar balatas")
    )


def _estado(taller: Taller, numero: str) -> str:
    return taller.datos.ordenes[numero].estado.value


def _tipos_en_bitacora(taller: Taller) -> set[str]:
    return {registro.tipo for registro in taller.datos.bitacora}


def test_flujo_completo_orden_particular(taller: Taller) -> None:
    numero = _recibir(taller, PARTICULAR, "ABC-123", "1HGCM82633A004352")
    _hasta_el_diagnostico(taller, numero)

    cotizacion = taller.cotizacion.generar_inicial(
        GenerarCotizacion(numero, trabajos("10000.00", "8000.00"))
    )
    assert cotizacion.estado == "Pendiente de Aprobación Gerencial"
    taller.aprobacion.revisar(RevisarCotizacion(cotizacion.id, aprobada=True))
    taller.cotizacion.presentar(PresentarCotizacion(cotizacion.id))
    decision = decidir(taller, cotizacion.id, (1, 2))
    assert decision.estado_orden == "Autorizada"

    taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1, 2), TECNICO))
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 1, TECNICO))
    assert _estado(taller, numero) == "En Reparación"

    taller.refacciones.solicitar(SolicitarRefaccion(numero, 1, "Balatas", 2))
    assert _estado(taller, numero) == "En Espera de Refacción"
    taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))
    assert _estado(taller, numero) == "En Reparación"

    taller.diagnostico.reportar_falla_adicional(ReportarFallaAdicional(numero, TECNICO, "Fuga"))
    adicional = taller.cotizacion.generar_adicional(GenerarCotizacion(numero, trabajos("500.00")))
    assert adicional.version == "v.2"
    decidir(taller, adicional.id, (1,))
    taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (3,), TECNICO))

    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 2, TECNICO))
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 3, TECNICO))
    for id_trabajo in (1, 2, 3):
        taller.reparacion.completar_trabajo(CompletarTrabajo(numero, id_trabajo, TECNICO))
    assert _estado(taller, numero) == "Lista para Entrega"

    pago = taller.caja.registrar_pago(
        RegistrarPago(numero, Decimal("18500.00"), FormaDePago.TARJETA)
    )
    assert (pago.estado, pago.monto) == ("Pagada", "18500.00")

    entrega = taller.entrega.entregar(RegistrarEntrega(numero))
    assert entrega.estado == "Cerrada"
    assert entrega.fecha_vencimiento_credito is None

    lector = LectorEnMemoria(taller.almacen)
    consulta = ManejadorConsultarEstadoDeOrden(lector).ejecutar(
        ConsultarEstadoDeOrden(numero, "abc123")
    )
    ingresos = ManejadorConsultarIngresosDelDia(lector, taller.reloj).ejecutar(
        ConsultarIngresosDelDia()
    )
    assert consulta.estado == "Cerrada"
    assert ingresos.total == "18500.00"
    assert {
        "OrdenRecibida",
        "DiagnosticoRegistrado",
        "CotizacionGenerada",
        "AprobacionGerencialRequerida",
        "CotizacionAprobadaPorGerente",
        "CotizacionPresentada",
        "CotizacionAutorizada",
        "OrdenAutorizada",
        "TrabajosAsignados",
        "TrabajoIniciado",
        "SolicitudDeCompraCreada",
        "RefaccionDisponible",
        "FallaAdicionalReportada",
        "OrdenListaParaEntrega",
        "PagoRegistrado",
        "VehiculoEntregado",
    } <= _tipos_en_bitacora(taller)
    assert {alerta.tipo for alerta in taller.datos.alertas} == {
        "DiagnosticoRegistrado",
        "AprobacionGerencialRequerida",
        "CotizacionAprobadaPorGerente",
        "RefaccionDisponible",
        "FallaAdicionalReportada",
        "CotizacionAutorizada",
        "OrdenListaParaEntrega",
    }


def test_flujo_completo_orden_de_flotilla(taller: Taller) -> None:
    numero = _recibir(taller, FLOTILLA, "XYZ-999", "2HGCM82633A004353")
    assert taller.datos.ordenes[numero].es_cliente_de_flotilla is True
    _hasta_el_diagnostico(taller, numero)

    cotizacion = taller.cotizacion.generar_inicial(GenerarCotizacion(numero, trabajos("5000.00")))
    taller.cotizacion.presentar(PresentarCotizacion(cotizacion.id))
    decidir(taller, cotizacion.id, (1,), flotilla=True)
    taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1,), TECNICO))
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 1, TECNICO))
    taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 1, TECNICO))

    cargo = taller.caja.registrar_cargo_a_credito(RegistrarCargoACredito(numero))
    assert (cargo.estado, cargo.monto) == ("Por Cobrar (Crédito)", "5000.00")

    poner_hora(taller.reloj, AHORA + timedelta(days=1))
    entrega = taller.entrega.entregar(RegistrarEntrega(numero))

    assert entrega.estado == "Cerrada"
    assert entrega.fecha_vencimiento_credito == date(2026, 10, 21)
    ingresos = ManejadorConsultarIngresosDelDia(
        LectorEnMemoria(taller.almacen), taller.reloj
    ).ejecutar(ConsultarIngresosDelDia())
    assert ingresos.total == "0.00"
    assert "CargoACreditoRegistrado" in _tipos_en_bitacora(taller)
