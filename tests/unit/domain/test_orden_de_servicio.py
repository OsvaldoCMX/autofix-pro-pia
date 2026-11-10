"""Aggregate Orden de Servicio: una prueba por fila de modelo-de-dominio.md §5.1 y sus eventos."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from domain.compartido.errores import (
    CancelacionNoPermitida,
    CorreccionNoPermitida,
    DiagnosticoNoModificable,
    DiagnosticoRequerido,
    EntregaNoPermitida,
    PagoNoPermitido,
    SolicitudNoEncontrada,
    SolicitudNoPermitida,
    TrabajoDeOtroTecnico,
    TrabajoNoAutorizado,
    TrabajoNoEncontrado,
    TrabajoNoPermitido,
    TransicionDeEstadoNoPermitida,
    ValorInvalido,
)
from domain.compartido.valores import Dinero
from domain.ordenes import eventos as ev
from domain.ordenes.especificaciones import RequiereAlertaDeRefaccion
from domain.ordenes.estados import EstadoOrden, EstadoSolicitud, EstadoTrabajo
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.valores import (
    Diagnostico,
    EstadoDeRecepcion,
    FormaDePago,
    NivelDeCombustible,
    Pago,
)
from tests.unit.domain import constructores as c

_O = EstadoOrden
_T = EstadoTrabajo
DESPUES = c.DESPUES


def _pago(monto: str = "1000.00") -> Pago:
    return Pago(Dinero(Decimal(monto)), FormaDePago.TARJETA, DESPUES)


# ------------------------------------------------------------------ recepción


def test_ca_001_registra_orden_recibida() -> None:
    orden = c.recibida()

    assert orden.estado is _O.RECIBIDA
    assert str(orden.numero) == "OS-1"
    assert orden.fecha_ingreso == c.INICIO
    assert orden.ultima_actualizacion == c.INICIO
    assert orden.extraer_eventos() == [
        ev.OrdenRecibida(c.INICIO, "OS-1", "CLI-1", "ABC123", c.ASESOR)
    ]


def test_ca_001_motivo_de_ingreso_es_obligatorio() -> None:
    with pytest.raises(ValorInvalido, match="motivo"):
        OrdenDeServicio.registrar(
            c.recibida().numero,
            "CLI-1",
            False,
            c.recibida().placas,
            c.ASESOR,
            "  ",
            c.RECEPCION,
            c.INICIO,
        )


def test_ca_002_guarda_estado_de_recepcion() -> None:
    recepcion = c.recibida().estado_de_recepcion

    assert recepcion == EstadoDeRecepcion(45000, NivelDeCombustible.MEDIO)
    assert recepcion is not None and recepcion.fotos == ()


def test_rn_23_kilometraje_negativo_se_rechaza() -> None:
    with pytest.raises(ValorInvalido, match="kilometraje"):
        EstadoDeRecepcion(-1, NivelDeCombustible.LLENO)


def test_ca_013_la_orden_entra_a_la_fila_al_registrarse() -> None:
    assert c.recibida().fecha_ingreso_a_fila == c.INICIO


# ------------------------------------------------------------------ diagnóstico


def test_ca_035_asigna_tecnico_de_diagnostico() -> None:
    orden = c.sin_eventos(c.recibida())

    orden.asignar_tecnico_para_diagnostico(c.TECNICO, DESPUES)

    assert orden.estado is _O.EN_DIAGNOSTICO
    assert orden.tecnico_de_diagnostico == c.TECNICO
    assert orden.ultima_actualizacion == DESPUES
    assert orden.extraer_eventos() == [
        ev.TecnicoAsignadoParaDiagnostico(DESPUES, "OS-1", c.TECNICO)
    ]


def test_ca_032_registra_diagnostico_con_fecha() -> None:
    orden = c.sin_eventos(c.en_diagnostico())
    diagnostico = Diagnostico(" Balatas gastadas ", " Cambiarlas ", c.TECNICO, DESPUES)

    orden.registrar_diagnostico(diagnostico)

    assert orden.diagnostico == Diagnostico("Balatas gastadas", "Cambiarlas", c.TECNICO, DESPUES)
    assert orden.ultima_actualizacion == DESPUES
    assert orden.extraer_eventos() == [
        ev.DiagnosticoRegistrado(DESPUES, "OS-1", c.TECNICO, c.ASESOR)
    ]


def test_ca_032_diagnostico_exige_fallas() -> None:
    with pytest.raises(ValorInvalido, match="fallas"):
        Diagnostico("  ", "Cambiarlas", c.TECNICO, DESPUES)


def test_rn_02_solo_el_tecnico_asignado_registra_el_diagnostico() -> None:
    orden = c.en_diagnostico()

    with pytest.raises(TrabajoDeOtroTecnico):
        orden.registrar_diagnostico(c.diagnostico(c.OTRO_TECNICO))

    assert orden.diagnostico is None


def test_rn_02_diagnostico_exige_orden_en_diagnostico() -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida, match="En Diagnóstico"):
        c.recibida().registrar_diagnostico(c.diagnostico())


def test_rn_03_antes_de_cotizar_el_diagnostico_se_puede_corregir() -> None:
    orden = c.diagnosticada()
    corregido = Diagnostico("Disco dañado", "Cambiar disco", c.TECNICO, DESPUES)

    orden.registrar_diagnostico(corregido)

    assert orden.diagnostico == corregido


def test_rn_02_no_se_cotiza_sin_diagnostico() -> None:
    orden = c.en_diagnostico()

    with pytest.raises(DiagnosticoRequerido):
        orden.marcar_cotizada(DESPUES)

    assert orden.estado is _O.EN_DIAGNOSTICO


def test_ca_005_marcar_cotizada_cambia_la_orden() -> None:
    orden = c.diagnosticada()

    orden.marcar_cotizada(DESPUES)

    assert orden.estado is _O.COTIZADA
    assert orden.cotizada
    assert orden.ultima_actualizacion == DESPUES


def test_ca_033_diagnostico_no_cambia_despues_de_cotizar() -> None:
    orden = c.cotizada()
    original = orden.diagnostico

    with pytest.raises(DiagnosticoNoModificable):
        orden.registrar_diagnostico(Diagnostico("Otra", "", c.TECNICO, DESPUES))

    assert orden.diagnostico == original


def test_rn_03_mensaje_indica_falla_adicional() -> None:
    with pytest.raises(DiagnosticoNoModificable, match="falla adicional"):
        c.cotizada().registrar_diagnostico(c.diagnostico())


def test_ca_034_reporta_falla_adicional() -> None:
    orden = c.sin_eventos(c.en_reparacion())

    falla = orden.reportar_falla_adicional(" Fuga de aceite ", c.TECNICO, DESPUES)

    assert orden.fallas_adicionales == (falla,)
    assert (falla.id, falla.descripcion, falla.tecnico) == (1, "Fuga de aceite", c.TECNICO)
    assert falla.reportada_en == DESPUES
    assert orden.ultima_actualizacion == DESPUES
    assert orden.extraer_eventos() == [
        ev.FallaAdicionalReportada(DESPUES, "OS-1", 1, "Fuga de aceite", c.ASESOR)
    ]


def test_ca_034_falla_exige_descripcion() -> None:
    orden = c.en_reparacion()

    with pytest.raises(ValorInvalido, match="descripción"):
        orden.reportar_falla_adicional("  ", c.TECNICO, DESPUES)

    assert orden.fallas_adicionales == ()


@pytest.mark.parametrize("constructor", [c.autorizada, c.en_espera, c.lista])
def test_ca_034_falla_solo_con_orden_en_reparacion(constructor: c.Constructor) -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida, match="En Reparación"):
        constructor().reportar_falla_adicional("Fuga", c.TECNICO, DESPUES)


# ------------------------------------------------------------------ decisión y asignación


def test_ca_010_autorizacion_crea_trabajos_y_autoriza_orden() -> None:
    orden = c.sin_eventos(c.cotizada())

    orden.aplicar_decision(c.decision(autorizados=1, no_autorizados=1))

    assert orden.estado is _O.AUTORIZADA
    assert [trabajo.estado for trabajo in orden.trabajos] == [_T.PENDIENTE, _T.NO_AUTORIZADO]
    assert orden.trabajos[0].id_cotizacion == "COT-1"
    assert orden.trabajos[1].numero_linea == 2
    assert orden.total_autorizado == c.IMPORTE
    assert orden.extraer_eventos() == [ev.OrdenAutorizada(c.INICIO, "OS-1", "COT-1")]


@pytest.mark.parametrize("constructor", [c.recibida, c.en_diagnostico, c.autorizada])
def test_rn_22_decision_inicial_exige_orden_cotizada(constructor: c.Constructor) -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida, match="Cotizada"):
        constructor().aplicar_decision(c.decision())


def test_ca_012_rechazo_total_deja_la_orden_cotizada() -> None:
    orden = c.con_rechazo_total()

    assert orden.estado is _O.COTIZADA
    assert orden.rechazo_total
    assert orden.trabajos == ()


def test_ca_012_rechazo_total_impide_asignar() -> None:
    with pytest.raises(TrabajoNoAutorizado, match="no tiene trabajos autorizados"):
        c.con_rechazo_total().asignar_trabajos([1], c.TECNICO, DESPUES)


def test_ca_011_solo_asigna_trabajos_autorizados() -> None:
    orden = c.autorizada(trabajos=1, no_autorizados=1)

    with pytest.raises(TrabajoNoAutorizado, match="Trabajo 2"):
        orden.asignar_trabajos([2], c.OTRO_TECNICO, DESPUES)

    assert orden.trabajos[1].tecnico is None


def test_ca_036_asigna_trabajos_pendientes() -> None:
    orden = c.cotizada()
    orden.aplicar_decision(c.decision(autorizados=2))
    c.sin_eventos(orden)

    orden.asignar_trabajos([1, 2], c.OTRO_TECNICO, DESPUES)

    assert [trabajo.tecnico for trabajo in orden.trabajos] == [c.OTRO_TECNICO, c.OTRO_TECNICO]
    assert all(trabajo.estado is _T.PENDIENTE for trabajo in orden.trabajos)
    assert orden.ultima_actualizacion == DESPUES
    assert orden.extraer_eventos() == [
        ev.TrabajosAsignados(DESPUES, "OS-1", (1, 2), c.OTRO_TECNICO)
    ]


def test_ca_036_un_trabajo_pendiente_se_puede_reasignar() -> None:
    orden = c.autorizada()

    orden.asignar_trabajos([1], c.OTRO_TECNICO, DESPUES)

    assert orden.trabajos[0].tecnico == c.OTRO_TECNICO


def test_rn_08_no_autorizado_no_se_asigna() -> None:
    orden = c.autorizada(trabajos=1, no_autorizados=1)

    with pytest.raises(TrabajoNoAutorizado):
        orden.asignar_trabajos([1, 2], c.OTRO_TECNICO, DESPUES)

    assert orden.trabajos[0].tecnico == c.TECNICO


def test_rn_08_trabajo_iniciado_no_se_reasigna() -> None:
    with pytest.raises(TrabajoNoPermitido, match="En Progreso"):
        c.en_reparacion().asignar_trabajos([1], c.OTRO_TECNICO, DESPUES)


def test_rn_08_seleccion_vacia_se_rechaza() -> None:
    with pytest.raises(ValorInvalido, match="al menos un trabajo"):
        c.autorizada().asignar_trabajos([], c.TECNICO, DESPUES)


def test_rn_08_trabajo_inexistente() -> None:
    with pytest.raises(TrabajoNoEncontrado, match="9"):
        c.autorizada().asignar_trabajos([9], c.TECNICO, DESPUES)


def test_rn_14_no_se_asigna_con_el_vehiculo_fuera() -> None:
    with pytest.raises(TrabajoNoPermitido, match="no está en el taller"):
        c.pausada().asignar_trabajos([1], c.OTRO_TECNICO, DESPUES)


# ------------------------------------------------------------------ iniciar y completar


def test_ca_014_iniciar_pasa_a_en_reparacion() -> None:
    orden = c.sin_eventos(c.autorizada())

    orden.iniciar_trabajo(1, c.TECNICO, DESPUES)

    assert orden.estado is _O.EN_REPARACION
    assert orden.trabajos[0].estado is _T.EN_PROGRESO
    assert orden.ultima_actualizacion == DESPUES
    assert orden.extraer_eventos() == [ev.TrabajoIniciado(DESPUES, "OS-1", 1, c.TECNICO)]


def test_ca_014_segundo_trabajo_deja_la_orden_en_reparacion() -> None:
    orden = c.en_reparacion(trabajos=2)

    orden.iniciar_trabajo(2, c.TECNICO, DESPUES)

    assert orden.estado is _O.EN_REPARACION
    assert orden.trabajos[1].estado is _T.EN_PROGRESO


def test_ca_014_en_espera_se_inicia_y_cambia_el_estado_de_regreso() -> None:
    orden = c.en_espera(trabajos=2)
    assert orden.estado_antes_de_espera is _O.AUTORIZADA

    orden.iniciar_trabajo(2, c.TECNICO, DESPUES)

    assert orden.estado is _O.EN_ESPERA_DE_REFACCION
    assert orden.estado_antes_de_espera is _O.EN_REPARACION


def test_rn_14_otro_tecnico_no_inicia() -> None:
    orden = c.autorizada()

    with pytest.raises(TrabajoDeOtroTecnico):
        orden.iniciar_trabajo(1, c.OTRO_TECNICO, DESPUES)

    assert orden.trabajos[0].estado is _T.PENDIENTE
    assert orden.estado is _O.AUTORIZADA


def test_rn_14_trabajo_sin_tecnico_no_se_inicia() -> None:
    orden = c.cotizada()
    orden.aplicar_decision(c.decision())

    with pytest.raises(TrabajoDeOtroTecnico):
        orden.iniciar_trabajo(1, c.TECNICO, DESPUES)


def test_ca_046_no_inicia_con_vehiculo_retirado() -> None:
    orden = c.pausada()

    with pytest.raises(TrabajoNoPermitido, match="no está en el taller"):
        orden.iniciar_trabajo(1, c.TECNICO, DESPUES)

    assert orden.trabajos[0].estado is _T.PENDIENTE


def test_rn_14_trabajo_ya_iniciado_no_se_inicia_otra_vez() -> None:
    with pytest.raises(TrabajoNoPermitido, match="En Progreso"):
        c.en_reparacion().iniciar_trabajo(1, c.TECNICO, DESPUES)


def test_rn_08_trabajo_no_autorizado_no_se_inicia() -> None:
    orden = c.autorizada(trabajos=1, no_autorizados=1)
    orden.trabajos[1].asignar(c.TECNICO)

    with pytest.raises(TrabajoNoPermitido, match="No Autorizado"):
        orden.iniciar_trabajo(2, c.TECNICO, DESPUES)


def test_ca_015_ultimo_trabajo_deja_lista_para_entrega() -> None:
    orden = c.sin_eventos(c.en_reparacion())

    orden.completar_trabajo(1, c.TECNICO, DESPUES)

    assert orden.estado is _O.LISTA_PARA_ENTREGA
    assert orden.trabajos[0].estado is _T.COMPLETADO
    assert orden.extraer_eventos() == [ev.OrdenListaParaEntrega(DESPUES, "OS-1", c.ASESOR)]


def test_ca_015_no_autorizados_no_cuentan_para_quedar_lista() -> None:
    orden = c.autorizada(trabajos=1, no_autorizados=1)
    orden.iniciar_trabajo(1, c.TECNICO, DESPUES)

    orden.completar_trabajo(1, c.TECNICO, DESPUES)

    assert orden.estado is _O.LISTA_PARA_ENTREGA


def test_ca_015_falta_otro_trabajo_sigue_en_reparacion() -> None:
    orden = c.sin_eventos(c.en_reparacion(trabajos=2))

    orden.completar_trabajo(1, c.TECNICO, DESPUES)

    assert orden.estado is _O.EN_REPARACION
    assert orden.ultima_actualizacion == DESPUES
    assert orden.extraer_eventos() == []


def test_ca_015_adicional_pendiente_impide_lista() -> None:
    orden = c.en_reparacion()
    orden.registrar_cotizacion_adicional_pendiente(DESPUES)

    orden.completar_trabajo(1, c.TECNICO, DESPUES)

    assert orden.estado is _O.EN_REPARACION


def test_rn_14_otro_tecnico_no_completa() -> None:
    orden = c.en_reparacion()

    with pytest.raises(TrabajoDeOtroTecnico):
        orden.completar_trabajo(1, c.OTRO_TECNICO, DESPUES)

    assert orden.trabajos[0].estado is _T.EN_PROGRESO


def test_rn_14_no_se_completa_con_el_vehiculo_fuera() -> None:
    orden = c.pausada(iniciada=True)

    with pytest.raises(TrabajoNoPermitido, match="no está en el taller"):
        orden.completar_trabajo(1, c.TECNICO, DESPUES)

    assert orden.trabajos[0].estado is _T.EN_PROGRESO


def test_rn_22_trabajo_pendiente_no_se_completa() -> None:
    orden = c.en_reparacion(trabajos=2)

    with pytest.raises(TransicionDeEstadoNoPermitida, match="aún no se inicia"):
        orden.completar_trabajo(2, c.TECNICO, DESPUES)


def test_rn_15_completar_con_solicitud_pendiente_se_rechaza_sin_cambios() -> None:
    orden = c.en_reparacion()
    orden.crear_solicitud_de_compra(1, "Balatas", 1, c.INICIO)
    c.sin_eventos(orden)

    with pytest.raises(TransicionDeEstadoNoPermitida, match="refacciones pendientes"):
        orden.completar_trabajo(1, c.TECNICO, DESPUES)

    assert orden.trabajos[0].estado is _T.EN_PROGRESO
    assert orden.estado is _O.EN_ESPERA_DE_REFACCION
    assert orden.extraer_eventos() == []


def test_rn_15_en_espera_se_completa_si_queda_otro_trabajo_abierto() -> None:
    orden = c.en_reparacion(trabajos=2)
    orden.crear_solicitud_de_compra(2, "Balatas", 1, c.INICIO)

    orden.completar_trabajo(1, c.TECNICO, DESPUES)

    assert orden.trabajos[0].estado is _T.COMPLETADO
    assert orden.estado is _O.EN_ESPERA_DE_REFACCION


def test_trabajo_inexistente_al_iniciar() -> None:
    with pytest.raises(TrabajoNoEncontrado):
        c.autorizada().iniciar_trabajo(9, c.TECNICO, DESPUES)


# ------------------------------------------------------------------ cotización adicional


def test_rn_24_adicional_solo_con_orden_en_reparacion() -> None:
    orden = c.autorizada()

    with pytest.raises(TransicionDeEstadoNoPermitida, match="En Reparación"):
        orden.registrar_cotizacion_adicional_pendiente(DESPUES)

    assert orden.adicionales_pendientes == 0


def test_ca_016_registra_la_adicional_pendiente() -> None:
    orden = c.en_reparacion()

    orden.registrar_cotizacion_adicional_pendiente(DESPUES)

    assert orden.adicionales_pendientes == 1
    assert orden.ultima_actualizacion == DESPUES


def test_ca_017_adicional_agrega_trabajos_pendientes() -> None:
    orden = c.en_reparacion()
    orden.registrar_cotizacion_adicional_pendiente(DESPUES)

    orden.aplicar_decision(c.adicional(autorizados=1))

    assert orden.estado is _O.EN_REPARACION
    assert orden.adicionales_pendientes == 0
    assert orden.trabajos[1].estado is _T.PENDIENTE
    assert orden.trabajos[1].id_cotizacion == "COT-2"
    assert orden.total_autorizado == Dinero(Decimal("2000.00"))


def test_ca_018_adicional_rechazada_marca_no_autorizado() -> None:
    orden = c.en_reparacion(trabajos=2)
    orden.registrar_cotizacion_adicional_pendiente(DESPUES)

    orden.aplicar_decision(c.adicional(autorizados=0, no_autorizados=1))

    assert orden.estado is _O.EN_REPARACION
    assert orden.trabajos[2].estado is _T.NO_AUTORIZADO
    assert orden.total_autorizado == Dinero(Decimal("2000.00"))


def test_ca_018_adicional_rechazada_con_todo_completado_queda_lista() -> None:
    orden = c.en_reparacion()
    orden.registrar_cotizacion_adicional_pendiente(DESPUES)
    orden.completar_trabajo(1, c.TECNICO, DESPUES)
    c.sin_eventos(orden)

    orden.aplicar_decision(c.adicional(autorizados=0, no_autorizados=1))

    assert orden.estado is _O.LISTA_PARA_ENTREGA
    assert orden.extraer_eventos() == [ev.OrdenListaParaEntrega(c.INICIO, "OS-1", c.ASESOR)]


def test_ca_015_con_dos_adicionales_espera_la_segunda_decision() -> None:
    orden = c.en_reparacion()
    orden.registrar_cotizacion_adicional_pendiente(DESPUES)
    orden.registrar_cotizacion_adicional_pendiente(DESPUES)
    orden.completar_trabajo(1, c.TECNICO, DESPUES)

    orden.aplicar_decision(c.adicional(autorizados=0, no_autorizados=1))

    assert orden.estado is _O.EN_REPARACION
    assert orden.adicionales_pendientes == 1


def test_rn_22_decision_adicional_sin_adicional_pendiente_se_rechaza() -> None:
    orden = c.en_reparacion()

    with pytest.raises(TransicionDeEstadoNoPermitida, match="adicional"):
        orden.aplicar_decision(c.adicional())

    assert len(orden.trabajos) == 1


# ------------------------------------------------------------------ refacciones


def test_ca_019_crea_solicitud_y_pone_en_espera() -> None:
    orden = c.sin_eventos(c.autorizada())

    solicitud = orden.crear_solicitud_de_compra(1, " Balatas ", 2, DESPUES)

    assert orden.estado is _O.EN_ESPERA_DE_REFACCION
    assert orden.solicitudes == (solicitud,)
    assert solicitud.estado is EstadoSolicitud.SOLICITADA
    assert (solicitud.id_trabajo, solicitud.refaccion, solicitud.cantidad) == (1, "Balatas", 2)
    assert solicitud.fecha_solicitud == DESPUES
    assert orden.extraer_eventos() == [
        ev.SolicitudDeCompraCreada(DESPUES, "OS-1", 1, 1, "Balatas", 2)
    ]


def test_ca_019_desde_en_reparacion_tambien_pone_en_espera() -> None:
    orden = c.en_reparacion()

    orden.crear_solicitud_de_compra(1, "Balatas", 2, DESPUES)

    assert orden.estado is _O.EN_ESPERA_DE_REFACCION
    assert orden.estado_antes_de_espera is _O.EN_REPARACION


def test_ca_019_segunda_solicitud_sigue_en_espera() -> None:
    orden = c.en_espera()

    segunda = orden.crear_solicitud_de_compra(1, "Discos", 1, DESPUES)

    assert segunda.id == 2
    assert orden.estado is _O.EN_ESPERA_DE_REFACCION
    assert orden.ultima_actualizacion == DESPUES


def test_ca_020_trabajo_no_autorizado_no_solicita() -> None:
    orden = c.autorizada(trabajos=1, no_autorizados=1)

    with pytest.raises(TrabajoNoAutorizado, match="no fue autorizado"):
        orden.crear_solicitud_de_compra(2, "Balatas", 1, DESPUES)

    assert orden.solicitudes == ()
    assert orden.estado is _O.AUTORIZADA


def test_rn_09_trabajo_completado_no_solicita() -> None:
    orden = c.en_reparacion(trabajos=2)
    orden.completar_trabajo(1, c.TECNICO, DESPUES)

    with pytest.raises(SolicitudNoPermitida, match="Completado"):
        orden.crear_solicitud_de_compra(1, "Balatas", 1, DESPUES)

    assert orden.estado is _O.EN_REPARACION


def test_rn_09_todo_completado_con_adicional_pendiente_no_se_atasca() -> None:
    orden = c.en_reparacion()
    orden.registrar_cotizacion_adicional_pendiente(DESPUES)
    orden.completar_trabajo(1, c.TECNICO, DESPUES)

    with pytest.raises(SolicitudNoPermitida):
        orden.crear_solicitud_de_compra(1, "Balatas", 1, DESPUES)

    orden.aplicar_decision(c.adicional(autorizados=0, no_autorizados=1))
    assert orden.estado is _O.LISTA_PARA_ENTREGA


@pytest.mark.parametrize("constructor", [c.pausada, c.lista, c.pagada])
def test_rn_09_orden_en_estado_invalido_no_solicita(constructor: c.Constructor) -> None:
    with pytest.raises(SolicitudNoPermitida):
        constructor().crear_solicitud_de_compra(1, "Balatas", 1, DESPUES)


@pytest.mark.parametrize(("refaccion", "cantidad"), [("Balatas", 0), ("Balatas", -1), ("  ", 1)])
def test_rn_23_cantidad_invalida_en_solicitud(refaccion: str, cantidad: int) -> None:
    orden = c.autorizada()

    with pytest.raises(ValorInvalido):
        orden.crear_solicitud_de_compra(1, refaccion, cantidad, DESPUES)

    assert orden.estado is _O.AUTORIZADA
    assert orden.solicitudes == ()


def test_ca_022_ultima_llegada_regresa_a_autorizada() -> None:
    orden = c.sin_eventos(c.en_espera())

    orden.registrar_llegada_de_refaccion(1, DESPUES)

    assert orden.estado is _O.AUTORIZADA
    assert orden.solicitudes[0].estado is EstadoSolicitud.DISPONIBLE
    assert orden.solicitudes[0].fecha_llegada == DESPUES
    assert orden.estado_antes_de_espera is None
    assert orden.extraer_eventos() == [
        ev.RefaccionDisponible(DESPUES, "OS-1", 1, c.TECNICO, c.ASESOR)
    ]


def test_ca_022_con_trabajo_iniciado_regresa_a_en_reparacion() -> None:
    orden = c.en_espera(trabajos=2)
    orden.iniciar_trabajo(2, c.TECNICO, DESPUES)

    orden.registrar_llegada_de_refaccion(1, DESPUES)

    assert orden.estado is _O.EN_REPARACION


def test_rn_10_sigue_en_espera_con_otra_pendiente() -> None:
    orden = c.en_espera()
    orden.crear_solicitud_de_compra(1, "Discos", 1, DESPUES)

    orden.registrar_llegada_de_refaccion(1, DESPUES)

    assert orden.estado is _O.EN_ESPERA_DE_REFACCION
    assert orden.solicitudes[1].esta_pendiente


def test_rn_22_llegada_repetida_se_rechaza() -> None:
    orden = c.en_espera()
    orden.crear_solicitud_de_compra(1, "Discos", 1, DESPUES)
    orden.registrar_llegada_de_refaccion(1, DESPUES)

    with pytest.raises(TransicionDeEstadoNoPermitida, match="«Balatas» ya estaba registrada"):
        orden.registrar_llegada_de_refaccion(1, DESPUES)


def test_solicitud_inexistente() -> None:
    with pytest.raises(SolicitudNoEncontrada, match="9"):
        c.en_espera().registrar_llegada_de_refaccion(9, DESPUES)


def test_ca_023_aviso_guarda_fecha_y_apaga_e7() -> None:
    orden = c.sin_eventos(c.en_espera())
    revision = c.INICIO + timedelta(days=10)
    assert RequiereAlertaDeRefaccion(revision).es_satisfecha_por(orden.solicitudes[0])

    orden.registrar_aviso_al_cliente(1, DESPUES)

    assert orden.solicitudes[0].fecha_aviso_al_cliente == DESPUES
    assert orden.solicitudes[0].estado is EstadoSolicitud.SOLICITADA
    assert orden.ultima_actualizacion == DESPUES
    assert not RequiereAlertaDeRefaccion(revision).es_satisfecha_por(orden.solicitudes[0])
    assert orden.extraer_eventos() == [ev.ClienteAvisadoDelRetraso(DESPUES, "OS-1", 1)]


def test_ca_023_aviso_una_sola_vez() -> None:
    orden = c.en_espera()
    orden.registrar_aviso_al_cliente(1, c.INICIO)

    with pytest.raises(SolicitudNoPermitida, match="ya estaba"):
        orden.registrar_aviso_al_cliente(1, DESPUES)

    assert orden.solicitudes[0].fecha_aviso_al_cliente == c.INICIO


def test_ca_023_no_se_avisa_si_la_refaccion_ya_llego() -> None:
    orden = c.en_espera()
    orden.registrar_llegada_de_refaccion(1, DESPUES)

    with pytest.raises(SolicitudNoPermitida, match="ya llegó"):
        orden.registrar_aviso_al_cliente(1, DESPUES)


# ------------------------------------------------------------------ retiro anticipado


def test_ca_024_salida_genera_nota_sin_cambiar_estado() -> None:
    orden = c.sin_eventos(c.en_espera())

    nota = orden.registrar_salida(DESPUES)

    assert orden.estado is _O.EN_ESPERA_DE_REFACCION
    assert orden.nota_de_responsabilidad == nota
    assert (nota.fecha_salida, nota.firmada, nota.fecha_firma) == (DESPUES, False, None)
    assert orden.extraer_eventos() == []


def test_rn_13_salida_solo_en_espera_de_refaccion() -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida, match="En Espera de Refacción"):
        c.autorizada().registrar_salida(DESPUES)


def test_rn_13_nueva_salida_reemplaza_la_nota_sin_firmar() -> None:
    orden = c.en_espera()
    orden.registrar_salida(c.INICIO)

    nota = orden.registrar_salida(DESPUES)

    assert nota.fecha_salida == DESPUES


def test_ca_024_firma_pausa_y_saca_de_la_fila() -> None:
    orden = c.en_espera()
    orden.registrar_salida(c.INICIO)
    c.sin_eventos(orden)

    orden.confirmar_firma_de_nota(DESPUES)

    nota = orden.nota_de_responsabilidad
    assert orden.estado is _O.PAUSADA_POR_RETIRO_DE_VEHICULO
    assert orden.fecha_ingreso_a_fila is None
    assert nota is not None and nota.firmada and nota.fecha_firma == DESPUES
    assert orden.extraer_eventos() == [ev.VehiculoRetirado(DESPUES, "OS-1")]


def test_rn_13_firma_sin_nota_se_rechaza() -> None:
    orden = c.en_espera()

    with pytest.raises(TransicionDeEstadoNoPermitida, match="registrarse la salida"):
        orden.confirmar_firma_de_nota(DESPUES)

    assert orden.estado is _O.EN_ESPERA_DE_REFACCION


def test_rn_13_nota_se_descarta_si_la_orden_sale_de_la_espera() -> None:
    orden = c.en_espera()
    orden.registrar_salida(c.INICIO)

    orden.registrar_llegada_de_refaccion(1, DESPUES)
    orden.crear_solicitud_de_compra(1, "Discos", 1, DESPUES)

    assert orden.nota_de_responsabilidad is None
    with pytest.raises(TransicionDeEstadoNoPermitida, match="registrarse la salida"):
        orden.confirmar_firma_de_nota(DESPUES)


def test_rn_22_firma_fuera_de_espera_se_rechaza() -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida, match="Autorizada"):
        c.autorizada().confirmar_firma_de_nota(DESPUES)


def test_ca_022_llegada_con_orden_pausada_no_cambia_el_estado() -> None:
    orden = c.pausada()

    orden.registrar_llegada_de_refaccion(1, DESPUES)

    assert orden.estado is _O.PAUSADA_POR_RETIRO_DE_VEHICULO
    assert orden.solicitudes[0].estado is EstadoSolicitud.DISPONIBLE
    assert orden.nota_de_responsabilidad is not None


def test_ca_025_reactiva_a_espera() -> None:
    orden = c.sin_eventos(c.pausada())

    orden.reactivar(DESPUES)

    assert orden.estado is _O.EN_ESPERA_DE_REFACCION
    assert orden.extraer_eventos() == [
        ev.OrdenReactivada(DESPUES, "OS-1", "En Espera de Refacción")
    ]


def test_ca_025_reactiva_a_autorizada() -> None:
    orden = c.pausada()
    orden.registrar_llegada_de_refaccion(1, DESPUES)

    orden.reactivar(DESPUES)

    assert orden.estado is _O.AUTORIZADA


def test_ca_025_reactiva_a_en_reparacion() -> None:
    orden = c.pausada(iniciada=True)
    assert orden.estado_antes_de_espera is _O.EN_REPARACION
    orden.registrar_llegada_de_refaccion(1, DESPUES)

    orden.reactivar(DESPUES)

    assert orden.estado is _O.EN_REPARACION


def test_rn_13_reactivar_da_nueva_fecha_de_fila() -> None:
    orden = c.pausada()

    orden.reactivar(DESPUES)

    assert orden.fecha_ingreso_a_fila == DESPUES
    assert orden.fecha_ingreso_a_fila != orden.fecha_ingreso


def test_rn_13_solo_se_reactiva_una_orden_pausada() -> None:
    orden = c.en_espera()

    with pytest.raises(TransicionDeEstadoNoPermitida, match="Pausada por Retiro"):
        orden.reactivar(DESPUES)


# ------------------------------------------------------------------ caja


def test_ca_026_pago_del_total() -> None:
    orden = c.sin_eventos(c.lista())
    pago = _pago()

    orden.registrar_pago(pago)

    assert orden.estado is _O.PAGADA
    assert orden.pago == pago
    assert orden.ultima_actualizacion == DESPUES
    assert orden.extraer_eventos() == [
        ev.PagoRegistrado(DESPUES, "OS-1", "1000.00", "Tarjeta")
    ]


@pytest.mark.parametrize("monto", ["999.99", "1000.01"])
def test_rn_16_monto_distinto_se_rechaza(monto: str) -> None:
    orden = c.lista()

    with pytest.raises(PagoNoPermitido, match="total autorizado"):
        orden.registrar_pago(_pago(monto))

    assert orden.estado is _O.LISTA_PARA_ENTREGA
    assert orden.pago is None


def test_rn_16_flotilla_no_paga_de_contado() -> None:
    orden = c.lista(flotilla=True)

    with pytest.raises(PagoNoPermitido, match="cargo a crédito"):
        orden.registrar_pago(_pago())

    assert orden.estado is _O.LISTA_PARA_ENTREGA


def test_rn_22_no_se_paga_antes_de_estar_lista() -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida):
        c.en_reparacion().registrar_pago(_pago())


def test_rn_16_costos_no_cambian_despues_del_pago() -> None:
    orden = c.pagada()

    with pytest.raises(TransicionDeEstadoNoPermitida):
        orden.aplicar_decision(c.adicional())
    with pytest.raises(TransicionDeEstadoNoPermitida):
        orden.registrar_cotizacion_adicional_pendiente(DESPUES)

    assert orden.total_autorizado == c.IMPORTE


def test_ca_039_cargo_a_credito_sin_vencimiento() -> None:
    orden = c.sin_eventos(c.lista(flotilla=True))

    orden.registrar_cargo_a_credito(DESPUES)

    cargo = orden.cargo_a_credito
    assert orden.estado is _O.POR_COBRAR_CREDITO
    assert cargo is not None
    assert (cargo.monto, cargo.registrado_en) == (c.IMPORTE, DESPUES)
    assert cargo.fecha_vencimiento is None
    assert orden.extraer_eventos() == [ev.CargoACreditoRegistrado(DESPUES, "OS-1", "1000.00")]


def test_rn_16_particular_no_usa_cargo_a_credito() -> None:
    orden = c.lista()

    with pytest.raises(PagoNoPermitido, match="flotilla"):
        orden.registrar_cargo_a_credito(DESPUES)

    assert orden.cargo_a_credito is None


def test_rn_16_costos_no_cambian_despues_del_cargo() -> None:
    orden = c.por_cobrar()

    with pytest.raises(TransicionDeEstadoNoPermitida):
        orden.aplicar_decision(c.adicional())

    assert orden.total_autorizado == c.IMPORTE


# ------------------------------------------------------------------ entrega


def test_ca_041_entrega_cierra_orden() -> None:
    orden = c.sin_eventos(c.pagada())

    orden.entregar(DESPUES)

    assert orden.estado is _O.CERRADA
    assert orden.fecha_entrega == DESPUES
    assert orden.extraer_eventos() == [ev.VehiculoEntregado(DESPUES, "OS-1")]


def test_rn_17_vence_15_dias_despues_de_la_entrega() -> None:
    orden = c.sin_eventos(c.por_cobrar())

    orden.entregar(DESPUES)

    cargo = orden.cargo_a_credito
    assert orden.estado is _O.CERRADA
    assert cargo is not None and cargo.fecha_vencimiento == date(2026, 10, 21)
    assert orden.extraer_eventos() == [
        ev.VehiculoEntregado(DESPUES, "OS-1", vence="2026-10-21")
    ]


def test_rn_17_el_vencimiento_usa_la_fecha_local_de_la_entrega() -> None:
    monterrey = timezone(timedelta(hours=-6))
    # 02:00 UTC del 7 de octubre todavía es 6 de octubre en Monterrey.
    entrega = datetime(2026, 10, 7, 2, 0, tzinfo=UTC).astimezone(monterrey)
    orden = c.por_cobrar()

    orden.entregar(entrega)

    assert orden.cargo_a_credito is not None
    assert orden.cargo_a_credito.fecha_vencimiento == date(2026, 10, 21)


@pytest.mark.parametrize("constructor", [c.recibida, c.autorizada, c.lista, c.cotizada])
def test_ca_042_sin_pago_no_se_entrega(constructor: c.Constructor) -> None:
    orden = constructor()
    estado = orden.estado

    with pytest.raises(EntregaNoPermitida, match="primero debe registrarse el pago"):
        orden.entregar(DESPUES)

    assert orden.estado is estado
    assert orden.fecha_entrega is None


def test_rn_18_mensaje_nombra_la_orden_y_su_estado() -> None:
    with pytest.raises(EntregaNoPermitida) as error:
        c.autorizada().entregar(DESPUES)

    assert str(error.value) == (
        "El vehículo de la orden OS-1 todavía no se puede entregar: su servicio sigue "
        "en proceso (estado «Autorizada»). Cuando esté «Lista para Entrega», "
        "primero debe registrarse el pago o el cargo a crédito."
    )


def test_rn_18_rechazo_total_se_entrega_sin_cobro() -> None:
    orden = c.cerrada_sin_reparacion()

    assert orden.pago is None
    assert orden.cargo_a_credito is None
    assert orden.total_autorizado == Dinero.cero()


def test_rn_18_rechazo_total_no_usa_la_entrega_normal() -> None:
    orden = c.con_rechazo_total()

    with pytest.raises(TransicionDeEstadoNoPermitida, match="«Entregar sin reparación»"):
        orden.entregar(DESPUES)


def test_ca_043_entrega_sin_reparacion() -> None:
    orden = c.sin_eventos(c.con_rechazo_total())

    orden.entregar_sin_reparacion(DESPUES)

    assert orden.estado is _O.CERRADA_SIN_REPARACION
    assert orden.fecha_entrega == DESPUES
    assert orden.extraer_eventos() == [
        ev.VehiculoEntregado(DESPUES, "OS-1", sin_reparacion=True)
    ]


def test_ca_043_cotizada_sin_rechazo_no_se_entrega_sin_reparacion() -> None:
    with pytest.raises(EntregaNoPermitida):
        c.cotizada().entregar_sin_reparacion(DESPUES)


def test_rn_18_orden_pagada_no_se_entrega_sin_reparacion() -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida, match="registre la entrega normal"):
        c.pagada().entregar_sin_reparacion(DESPUES)


# ------------------------------------------------------------------ cancelación


def test_ca_044_cancela_orden_recibida_con_motivo() -> None:
    orden = c.sin_eventos(c.recibida())

    orden.cancelar(" El cliente desistió ", c.ASESOR, DESPUES)

    cancelacion = orden.cancelacion
    assert orden.estado is _O.CANCELADA
    assert cancelacion is not None
    assert cancelacion.motivo == "El cliente desistió"
    assert (cancelacion.registrada_en, cancelacion.asesor) == (DESPUES, c.ASESOR)
    assert orden.pago is None and orden.cargo_a_credito is None
    assert orden.extraer_eventos() == [
        ev.OrdenCancelada(DESPUES, "OS-1", "El cliente desistió", c.ASESOR)
    ]


def test_ca_044_cancela_en_diagnostico_y_saca_de_la_fila() -> None:
    orden = c.en_diagnostico()

    orden.cancelar("Ya no quiere", c.ASESOR, DESPUES)

    assert orden.estado is _O.CANCELADA
    assert orden.fecha_ingreso_a_fila is None


@pytest.mark.parametrize("motivo", ["", "   "])
def test_rn_19_motivo_vacio_se_rechaza(motivo: str) -> None:
    orden = c.recibida()

    with pytest.raises(ValorInvalido, match="motivo"):
        orden.cancelar(motivo, c.ASESOR, DESPUES)

    assert orden.estado is _O.RECIBIDA


def test_ca_045_cotizada_no_se_cancela_y_sugiere_el_rechazo_total() -> None:
    orden = c.cotizada()

    with pytest.raises(CancelacionNoPermitida, match="se registra el rechazo total"):
        orden.cancelar("Ya no quiere", c.ASESOR, DESPUES)

    assert orden.estado is _O.COTIZADA
    assert orden.cancelacion is None


def test_ca_045_con_rechazo_total_no_se_cancela_y_orienta_a_la_entrega() -> None:
    orden = c.con_rechazo_total()

    with pytest.raises(CancelacionNoPermitida, match="«Entregar sin reparación»"):
        orden.cancelar("Ya no quiere", c.ASESOR, DESPUES)

    assert orden.estado is _O.COTIZADA
    assert orden.cancelacion is None


@pytest.mark.parametrize("constructor", [c.autorizada, c.en_reparacion, c.pagada])
def test_ca_045_con_trabajos_autorizados_no_se_cancela_ni_sugiere_rechazo(
    constructor: c.Constructor,
) -> None:
    orden = constructor()
    estado = orden.estado

    with pytest.raises(CancelacionNoPermitida, match="ya autorizó trabajos") as error:
        orden.cancelar("Ya no quiere", c.ASESOR, DESPUES)

    assert "rechazo total" not in str(error.value)
    assert orden.estado is estado
    assert orden.cancelacion is None


@pytest.mark.parametrize(
    ("constructor", "fragmento"),
    [
        (c.cancelada, "ya está cancelada"),
        (c.cerrada, "ya está cerrada"),
        (c.cerrada_sin_reparacion, "ya está cerrada"),
    ],
)
def test_rn_19_orden_terminada_no_se_cancela_ni_sugiere_rechazo(
    constructor: c.Constructor, fragmento: str
) -> None:
    orden = constructor()

    with pytest.raises(CancelacionNoPermitida, match=fragmento) as error:
        orden.cancelar("Ya no quiere", c.ASESOR, DESPUES)

    assert "rechazo total" not in str(error.value)


# ------------------------------------------------------------------ mensajes según el estado


@pytest.mark.parametrize(
    ("constructor", "fragmento"),
    [
        (c.cancelada, "está cancelada"),
        (c.cerrada, "ya fue entregado"),
        (c.cerrada_sin_reparacion, "ya fue entregado"),
    ],
)
def test_ca_042_orden_terminada_no_pide_registrar_el_pago(
    constructor: c.Constructor, fragmento: str
) -> None:
    with pytest.raises(EntregaNoPermitida, match=fragmento) as error:
        constructor().entregar(DESPUES)

    assert "pago" not in str(error.value)


def test_ca_042_orden_lista_pide_el_pago_en_caja() -> None:
    with pytest.raises(EntregaNoPermitida, match="cargo a crédito en Caja"):
        c.lista().entregar(DESPUES)


def test_ca_042_cotizada_sin_decision_explica_que_falta_la_del_cliente() -> None:
    with pytest.raises(EntregaNoPermitida, match="el cliente aún no decide"):
        c.cotizada().entregar(DESPUES)


@pytest.mark.parametrize(
    ("constructor", "fragmento"),
    [
        (c.cancelada, "no genera ningún cobro"),
        (c.cerrada, "no hay cobro pendiente"),
        (c.cerrada_sin_reparacion, "no hay cobro pendiente"),
        (c.pagada, "ya tiene su pago registrado"),
        (c.por_cobrar, "ya tiene registrado un cargo a crédito"),
        (c.autorizada, "debe estar «Lista para Entrega» y ahora está en «Autorizada»"),
    ],
)
def test_rn_22_cobro_en_estado_incorrecto_explica_la_situacion(
    constructor: c.Constructor, fragmento: str
) -> None:
    orden = constructor()
    estado = orden.estado

    with pytest.raises(TransicionDeEstadoNoPermitida, match=fragmento):
        orden.registrar_pago(c.pago_del_total())
    with pytest.raises(TransicionDeEstadoNoPermitida, match=fragmento):
        orden.registrar_cargo_a_credito(DESPUES)

    assert orden.estado is estado


def test_rn_22_asignar_tecnico_a_orden_no_recibida_explica_el_estado() -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida, match="OS-1 está en «Cancelada»"):
        c.cancelada().asignar_tecnico_para_diagnostico(c.TECNICO, DESPUES)


def test_rn_22_cotizar_dos_veces_avisa_que_ya_tiene_cotizacion() -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida, match="ya tiene su cotización inicial"):
        c.cotizada().marcar_cotizada(DESPUES)


def test_rn_22_cotizar_en_otro_estado_explica_el_estado() -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida, match="OS-1 está en «Autorizada»"):
        c.autorizada().marcar_cotizada(DESPUES)


def test_rn_22_completar_dos_veces_avisa_que_ya_esta_completado() -> None:
    orden = c.en_reparacion(trabajos=2)
    orden.iniciar_trabajo(2, c.TECNICO, DESPUES)
    orden.completar_trabajo(1, c.TECNICO, DESPUES)

    with pytest.raises(TransicionDeEstadoNoPermitida, match="ya está completado"):
        orden.completar_trabajo(1, c.TECNICO, DESPUES)


# ------------------------------------------------------------------ estados finales y flujos


@pytest.mark.parametrize("constructor", [c.cerrada, c.cerrada_sin_reparacion, c.cancelada])
def test_rn_22_una_orden_final_no_cambia(constructor: c.Constructor) -> None:
    orden = constructor()
    estado = orden.estado

    with pytest.raises(TransicionDeEstadoNoPermitida):
        orden.asignar_tecnico_para_diagnostico(c.TECNICO, DESPUES)
    with pytest.raises(CancelacionNoPermitida):
        orden.cancelar("Otra vez", c.ASESOR, DESPUES)
    with pytest.raises(EntregaNoPermitida):
        orden.entregar(DESPUES)

    assert orden.estado is estado


def test_rn_22_recorre_el_flujo_completo_de_una_orden_particular() -> None:
    orden = c.recibida()
    orden.asignar_tecnico_para_diagnostico(c.TECNICO, c.INICIO)
    orden.registrar_diagnostico(c.diagnostico())
    orden.marcar_cotizada(c.INICIO)
    orden.aplicar_decision(c.decision())
    orden.asignar_trabajos([1], c.TECNICO, c.INICIO)
    orden.iniciar_trabajo(1, c.TECNICO, c.INICIO)
    orden.crear_solicitud_de_compra(1, "Balatas", 2, c.INICIO)
    orden.registrar_salida(c.INICIO)
    orden.confirmar_firma_de_nota(c.INICIO)
    orden.registrar_llegada_de_refaccion(1, c.INICIO)
    orden.reactivar(c.INICIO)
    orden.reportar_falla_adicional("Fuga", c.TECNICO, c.INICIO)
    orden.completar_trabajo(1, c.TECNICO, c.INICIO)
    orden.registrar_pago(c.pago_del_total())
    orden.entregar(c.INICIO)

    assert orden.estado is _O.CERRADA
    assert [type(evento).__name__ for evento in orden.extraer_eventos()] == [
        "OrdenRecibida",
        "TecnicoAsignadoParaDiagnostico",
        "DiagnosticoRegistrado",
        "OrdenAutorizada",
        "TrabajosAsignados",
        "TrabajoIniciado",
        "SolicitudDeCompraCreada",
        "VehiculoRetirado",
        "RefaccionDisponible",
        "OrdenReactivada",
        "FallaAdicionalReportada",
        "OrdenListaParaEntrega",
        "PagoRegistrado",
        "VehiculoEntregado",
    ]


def test_valores_de_recepcion_son_inmutables() -> None:
    with pytest.raises(FrozenInstanceError):
        c.RECEPCION.kilometraje = 1  # type: ignore[misc]


# ------------------------------------------------------------------ cambio de técnico (H-PIA-23)
def test_ca_054_cambia_el_tecnico_sin_cambiar_el_estado() -> None:
    orden = c.sin_eventos(c.en_diagnostico())

    orden.asignar_tecnico_para_diagnostico(c.OTRO_TECNICO, DESPUES)

    assert orden.estado is _O.EN_DIAGNOSTICO
    assert orden.tecnico_de_diagnostico == c.OTRO_TECNICO
    eventos = orden.extraer_eventos()
    assert [type(evento) for evento in eventos] == [ev.TecnicoDeDiagnosticoReasignado]
    assert (eventos[0].tecnico_anterior, eventos[0].tecnico) == (c.TECNICO, c.OTRO_TECNICO)


def test_ca_054_con_diagnostico_ya_no_se_cambia() -> None:
    orden = c.diagnosticada()

    with pytest.raises(CorreccionNoPermitida, match="ya está registrado"):
        orden.asignar_tecnico_para_diagnostico(c.OTRO_TECNICO, DESPUES)

    assert orden.tecnico_de_diagnostico == c.TECNICO


def test_rn_28_asignar_al_mismo_tecnico_no_registra_nada() -> None:
    orden = c.sin_eventos(c.en_diagnostico())

    orden.asignar_tecnico_para_diagnostico(c.TECNICO, DESPUES)

    assert orden.extraer_eventos() == []


def test_rn_28_despues_de_cotizar_el_mensaje_dice_cuando_si_se_puede() -> None:
    orden = c.cotizada()

    with pytest.raises(TransicionDeEstadoNoPermitida, match="antes del diagnóstico"):
        orden.asignar_tecnico_para_diagnostico(c.OTRO_TECNICO, DESPUES)


# ------------------------------------------------------------------ corrección de recepción (H-PIA-24)
@pytest.mark.parametrize("constructor", [c.recibida, c.en_diagnostico])
def test_ca_057_corrige_la_recepcion_sin_cambiar_el_estado(constructor: c.Constructor) -> None:
    orden = c.sin_eventos(constructor())
    estado = orden.estado
    nueva = EstadoDeRecepcion(46000, NivelDeCombustible.LLENO)

    orden.corregir_datos_de_recepcion(nueva, "  Ruido al frenar y vibración  ", DESPUES)

    assert orden.estado is estado
    assert orden.estado_de_recepcion == nueva
    assert orden.motivo_de_ingreso == "Ruido al frenar y vibración"
    assert [type(e) for e in orden.extraer_eventos()] == [ev.DatosDeRecepcionCorregidos]


@pytest.mark.parametrize("constructor", [c.cotizada, c.autorizada, c.cancelada])
def test_rn_29_recepcion_no_se_corrige_despues_de_cotizar(constructor: c.Constructor) -> None:
    orden = constructor()
    anterior = orden.estado_de_recepcion

    with pytest.raises(CorreccionNoPermitida, match="antes de la cotización"):
        orden.corregir_datos_de_recepcion(
            EstadoDeRecepcion(1, NivelDeCombustible.RESERVA), "Otro", DESPUES
        )

    assert orden.estado_de_recepcion == anterior


def test_rn_29_motivo_vacio_no_se_corrige() -> None:
    orden = c.recibida()

    with pytest.raises(ValorInvalido):
        orden.corregir_datos_de_recepcion(c.RECEPCION, "   ", DESPUES)


# ------------------------------------------------------------------ corrección de la forma de pago
def test_ca_058_corrige_la_forma_de_pago_de_una_orden_pagada() -> None:
    orden = c.sin_eventos(c.pagada())
    pago = orden.pago
    assert pago is not None

    orden.corregir_forma_de_pago(FormaDePago.TRANSFERENCIA, DESPUES)

    assert orden.estado is _O.PAGADA
    assert orden.pago == Pago(pago.monto, FormaDePago.TRANSFERENCIA, pago.registrado_en)
    (evento,) = orden.extraer_eventos()
    assert isinstance(evento, ev.FormaDePagoCorregida)
    assert (evento.forma_anterior, evento.forma) == ("Efectivo", "Transferencia")


def test_rn_30_la_misma_forma_no_registra_nada() -> None:
    orden = c.sin_eventos(c.pagada())

    orden.corregir_forma_de_pago(FormaDePago.EFECTIVO, DESPUES)

    assert orden.extraer_eventos() == []


def test_rn_30_entregada_ya_no_se_corrige() -> None:
    orden = c.cerrada()

    with pytest.raises(CorreccionNoPermitida, match="ya se entregó"):
        orden.corregir_forma_de_pago(FormaDePago.EFECTIVO, DESPUES)


@pytest.mark.parametrize("constructor", [c.lista, c.por_cobrar])
def test_rn_30_sin_pago_de_contado_no_hay_que_corregir(constructor: c.Constructor) -> None:
    with pytest.raises(CorreccionNoPermitida, match="no tiene un pago de contado"):
        constructor().corregir_forma_de_pago(FormaDePago.EFECTIVO, DESPUES)
