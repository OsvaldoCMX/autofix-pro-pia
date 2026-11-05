"""Alertas generadas por cada Domain Event (modelo-de-dominio.md §6, ADR-016).

Usan el publicador real, armado como lo hará el Composition Root.
"""
from __future__ import annotations

import pytest

from application.comandos import (
    AsignarTrabajos,
    CompletarTrabajo,
    GenerarCotizacion,
    IniciarTrabajo,
    RegistrarLlegadaDeRefaccion,
    RegistrarPago,
    ReportarFallaAdicional,
    RevisarCotizacion,
    SolicitarRefaccion,
)
from application.manejadores.alertas import ManejadoresDeAlertas
from application.puertos import AlertaInterna
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes.valores import FormaDePago
from infrastructure.eventos.publicador_en_proceso import PublicadorEnProceso
from tests.unit.application.escenarios import (
    AHORA,
    ASESOR,
    OTRO_TECNICO,
    TECNICO,
    TOTAL_DE_DOS_TRABAJOS,
    Taller,
    autorizada,
    con_adicional,
    cotizada,
    decidir,
    diagnosticada,
    en_espera,
    en_reparacion,
    lista,
    trabajos,
)


@pytest.fixture
def taller() -> Taller:
    publicador = PublicadorEnProceso()
    armado = Taller(publicador)
    for tipo, manejador in ManejadoresDeAlertas(armado.uow).suscripciones().items():
        publicador.suscribir(tipo, manejador)
    return armado


def _alertas(taller: Taller, tipo: str) -> list[AlertaInterna]:
    return [alerta for alerta in taller.datos.alertas if alerta.tipo == tipo]


def test_ca_032_avisa_al_asesor(taller: Taller) -> None:
    numero = diagnosticada(taller)

    alerta = _alertas(taller, "DiagnosticoRegistrado")[0]

    assert alerta.destinatario == ASESOR
    assert alerta.numero_orden == numero
    assert "lista para cotizar" in alerta.mensaje
    assert alerta.creada_en == AHORA


def test_ca_007_avisa_a_los_gerentes(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=("20000.00",))

    alerta = _alertas(taller, "AprobacionGerencialRequerida")[0]

    assert alerta.destinatario is None
    assert alerta.destinatario_rol is RolDeEmpleado.GERENTE
    assert alerta.id_cotizacion == id_cotizacion
    assert "requiere su aprobación" in alerta.mensaje


def test_ca_005_cotizacion_sin_gerente_no_genera_esa_alerta(taller: Taller) -> None:
    cotizada(taller)

    assert _alertas(taller, "AprobacionGerencialRequerida") == []


def test_ca_008_avisa_al_asesor(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=("20000.00",))

    taller.aprobacion.revisar(RevisarCotizacion(id_cotizacion, aprobada=True))

    alerta = _alertas(taller, "CotizacionAprobadaPorGerente")[0]
    assert alerta.destinatario == ASESOR
    assert "ya puede presentarse" in alerta.mensaje


def test_ca_009_avisa_con_observaciones(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=("20000.00",))

    taller.aprobacion.revisar(
        RevisarCotizacion(id_cotizacion, aprobada=False, observaciones="Reducir mano de obra")
    )

    alerta = _alertas(taller, "CotizacionRechazadaPorGerente")[0]
    assert alerta.destinatario == ASESOR
    assert "Reducir mano de obra" in alerta.mensaje


def test_ca_017_avisa_a_cada_tecnico_asignado(taller: Taller) -> None:
    numero, _ = autorizada(taller)
    taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1,), TECNICO))
    taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (2,), OTRO_TECNICO))
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 1, TECNICO))

    adicional = taller.cotizacion.generar_adicional(
        GenerarCotizacion(numero, trabajos("500.00"))
    )

    decidir(taller, adicional.id, (1,))

    alertas = _alertas(taller, "CotizacionAutorizada")
    assert [alerta.destinatario for alerta in alertas] == [TECNICO, OTRO_TECNICO]
    assert {alerta.id_cotizacion for alerta in alertas} == {adicional.id}


def test_ca_017_tecnico_con_varios_trabajos_recibe_una_sola_alerta(taller: Taller) -> None:
    _, id_adicional = con_adicional(taller)

    decidir(taller, id_adicional, (1, 2))

    assert [a.destinatario for a in _alertas(taller, "CotizacionAutorizada")] == [TECNICO]


def test_cotizacion_inicial_autorizada_no_genera_alerta(taller: Taller) -> None:
    autorizada(taller)

    assert _alertas(taller, "CotizacionAutorizada") == []


def test_ca_034_avisa_al_asesor(taller: Taller) -> None:
    numero = en_reparacion(taller)

    taller.diagnostico.reportar_falla_adicional(
        ReportarFallaAdicional(numero, TECNICO, "Fuga de aceite")
    )

    alerta = _alertas(taller, "FallaAdicionalReportada")[0]
    assert alerta.destinatario == ASESOR
    assert "Fuga de aceite" in alerta.mensaje
    assert "cotización adicional" in alerta.mensaje


def test_ca_022_avisa_al_tecnico_y_al_asesor(taller: Taller) -> None:
    numero = en_espera(taller)

    taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))

    destinatarios = [a.destinatario for a in _alertas(taller, "RefaccionDisponible")]
    assert destinatarios == [TECNICO, ASESOR]


def test_ca_022_trabajo_sin_tecnico_solo_avisa_al_asesor(taller: Taller) -> None:
    numero, _ = autorizada(taller)
    taller.refacciones.solicitar(SolicitarRefaccion(numero, 1, "Balatas", 1))

    taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))

    assert [a.destinatario for a in _alertas(taller, "RefaccionDisponible")] == [ASESOR]


def test_ca_015_avisa_al_asesor(taller: Taller) -> None:
    numero = en_reparacion(taller)
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 2, TECNICO))
    taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 1, TECNICO))
    assert _alertas(taller, "OrdenListaParaEntrega") == []

    taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 2, TECNICO))

    alerta = _alertas(taller, "OrdenListaParaEntrega")[0]
    assert alerta.destinatario == ASESOR
    assert "lista para entrega" in alerta.mensaje


def test_eventos_de_bitacora_no_generan_alerta(taller: Taller) -> None:
    numero = lista(taller)
    antes = len(taller.datos.alertas)

    taller.caja.registrar_pago(RegistrarPago(numero, TOTAL_DE_DOS_TRABAJOS, FormaDePago.EFECTIVO))

    assert len(taller.datos.alertas) == antes
    assert "PagoRegistrado" in [registro.tipo for registro in taller.datos.bitacora]


def test_los_manejadores_no_modifican_la_orden(taller: Taller) -> None:
    numero = diagnosticada(taller)

    orden = taller.datos.ordenes[numero]

    assert orden.estado.value == "En Diagnóstico"
    assert len([r for r in taller.datos.bitacora if r.tipo == "DiagnosticoRegistrado"]) == 1
