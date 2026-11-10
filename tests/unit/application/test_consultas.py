"""Consultas (CQRS) con el lector en memoria (ADR-003)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from application.comandos import (
    AsignarTrabajos,
    CancelarOrden,
    GenerarCotizacion,
    PresentarCotizacion,
    ReactivarOrden,
    RefaccionPropuesta,
    RegistrarLlegadaDeRefaccion,
    RegistrarPago,
    ReportarFallaAdicional,
    TrabajoPropuesto,
)
from application.consultas.consultas import (
    BuscarClientes,
    BuscarVehiculoPorPlacas,
    ConsultarCotizacion,
    ConsultarEstadoDeOrden,
    ConsultarExpedienteDeOrden,
    ConsultarIngresosDelDia,
    ConsultarPanelDelTecnico,
    ListarAlertas,
    ListarCotizacionesPendientesDeAprobacion,
    ListarOrdenes,
    ListarSolicitudesPendientes,
    ManejadorBuscarClientes,
    ManejadorBuscarVehiculoPorPlacas,
    ManejadorConsultarCotizacion,
    ManejadorConsultarEstadoDeOrden,
    ManejadorConsultarExpedienteDeOrden,
    ManejadorConsultarIngresosDelDia,
    ManejadorConsultarPanelDelTecnico,
    ManejadorListarAlertas,
    ManejadorListarCotizacionesPendientesDeAprobacion,
    ManejadorListarOrdenes,
    ManejadorListarSolicitudesPendientes,
)
from application.puertos import AlertaInterna
from domain.clientes.cliente import TipoCliente
from domain.compartido.errores import (
    CotizacionNoEncontrada,
    OrdenNoEncontrada,
    ValorInvalido,
    VehiculoNoEncontrado,
)
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes.estados import EstadoOrden
from domain.ordenes.valores import FormaDePago
from infrastructure.memoria.lector import LectorEnMemoria
from tests.unit.application.escenarios import (
    AHORA,
    ASESOR,
    OTRO_TECNICO,
    TECNICO,
    TOTAL_DE_DOS_TRABAJOS,
    Taller,
    asignada,
    autorizada,
    cotizada,
    diagnosticada,
    en_diagnostico,
    en_espera,
    en_reparacion,
    lista,
    pagada,
    pausada,
    poner_hora,
    por_cobrar,
    recibida,
)


def _lector(taller: Taller) -> LectorEnMemoria:
    return LectorEnMemoria(taller.almacen)


def _panel(taller: Taller, tecnico: str = TECNICO) -> list:
    return ManejadorConsultarPanelDelTecnico(_lector(taller)).ejecutar(
        ConsultarPanelDelTecnico(tecnico)
    )


def _ingresos(taller: Taller) -> str:
    consulta = ManejadorConsultarIngresosDelDia(_lector(taller), taller.reloj)
    return consulta.ejecutar(ConsultarIngresosDelDia()).total


# ------------------------------------------------------------------ recepción
def test_ca_003_busca_vehiculo_y_cliente(taller: Taller) -> None:
    recibida(taller)

    vista = ManejadorBuscarVehiculoPorPlacas(_lector(taller)).ejecutar(
        BuscarVehiculoPorPlacas("abc-001")
    )

    assert (vista.placas, vista.marca, vista.anio) == ("ABC001", "Nissan", 2020)
    assert vista.cliente.nombre == "Luis Peña"
    assert vista.cliente.responsable_nombre is None


def test_ca_003_busqueda_por_placas_trae_la_orden_abierta(taller: Taller) -> None:
    numero = recibida(taller)

    vista = ManejadorBuscarVehiculoPorPlacas(_lector(taller)).ejecutar(
        BuscarVehiculoPorPlacas("ABC001")
    )

    assert vista.orden_abierta is not None
    assert (vista.orden_abierta.numero_orden, vista.orden_abierta.estado) == (numero, "Recibida")


def test_ca_003_busqueda_por_placas_sin_orden_abierta(taller: Taller) -> None:
    numero = recibida(taller)
    taller.cancelacion.cancelar(CancelarOrden(numero, "El cliente desiste", ASESOR))

    vista = ManejadorBuscarVehiculoPorPlacas(_lector(taller)).ejecutar(
        BuscarVehiculoPorPlacas("ABC001")
    )

    assert vista.orden_abierta is None


def test_ca_004_placas_no_registradas(taller: Taller) -> None:
    with pytest.raises(VehiculoNoEncontrado, match="XYZ999"):
        ManejadorBuscarVehiculoPorPlacas(_lector(taller)).ejecutar(
            BuscarVehiculoPorPlacas("XYZ-999")
        )


def test_ca_028_busca_flotilla_y_responsable(taller: Taller) -> None:
    recibida(taller)
    recibida(taller, flotilla=True)

    vistas = ManejadorBuscarClientes(_lector(taller)).ejecutar(
        BuscarClientes(TipoCliente.FLOTILLA, "transportes")
    )

    assert [vista.empresa for vista in vistas] == ["Transportes Norte"]
    assert vistas[0].responsable_nombre == "Ana Torres"
    assert vistas[0].responsable_correo == "ana@norte.test"


def test_ca_028_empresa_que_no_existe_no_devuelve_clientes(taller: Taller) -> None:
    recibida(taller, flotilla=True)

    vistas = ManejadorBuscarClientes(_lector(taller)).ejecutar(
        BuscarClientes(TipoCliente.FLOTILLA, "Otra")
    )

    assert vistas == []


def test_buscar_clientes_sin_filtros_los_devuelve_todos(taller: Taller) -> None:
    recibida(taller)
    recibida(taller, flotilla=True)

    assert len(ManejadorBuscarClientes(_lector(taller)).ejecutar(BuscarClientes())) == 2


# ------------------------------------------------------------------ panel del técnico
def test_ca_035_orden_aparece_en_el_panel(taller: Taller) -> None:
    numero = en_diagnostico(taller)

    panel = _panel(taller)

    assert [vista.numero_orden for vista in panel] == [numero]
    assert panel[0].diagnostico_asignado is True
    assert panel[0].trabajos == ()
    assert _panel(taller, OTRO_TECNICO) == []


def test_ca_036_trabajos_pendientes_en_el_panel(taller: Taller) -> None:
    numero = asignada(taller)

    panel = _panel(taller)

    assert panel[0].numero_orden == numero
    assert panel[0].diagnostico_asignado is False
    assert [trabajo.estado for trabajo in panel[0].trabajos] == ["Pendiente", "Pendiente"]


def test_ca_013_panel_en_orden_de_fila(taller: Taller) -> None:
    poner_hora(taller.reloj, AHORA + timedelta(hours=2))
    reciente = en_diagnostico(taller)
    poner_hora(taller.reloj, AHORA)
    antigua = en_diagnostico(taller)

    assert [vista.numero_orden for vista in _panel(taller)] == [antigua, reciente]


def test_ca_025_reactivada_queda_al_final_de_la_fila(taller: Taller) -> None:
    primera = pausada(taller)
    segunda = asignada(taller)
    taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(primera, 1))
    poner_hora(taller.reloj, AHORA + timedelta(days=1))
    taller.retiro.reactivar(ReactivarOrden(primera))

    assert [vista.numero_orden for vista in _panel(taller)] == [segunda, primera]


def test_ca_024_orden_pausada_sale_del_panel(taller: Taller) -> None:
    pausada(taller)

    assert _panel(taller) == []


def test_ca_044_cancelada_sale_del_panel(taller: Taller) -> None:
    numero = en_diagnostico(taller)
    taller.cancelacion.cancelar(CancelarOrden(numero, "Desistió", ASESOR))

    assert _panel(taller) == []


def test_ca_013_panel_no_muestra_trabajos_terminados(taller: Taller) -> None:
    lista(taller)

    assert _panel(taller) == []


def test_ca_013_panel_solo_muestra_los_trabajos_de_ese_tecnico(taller: Taller) -> None:
    numero, _ = autorizada(taller)
    taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1,), TECNICO))
    taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (2,), OTRO_TECNICO))

    assert [trabajo.id for trabajo in _panel(taller)[0].trabajos] == [1]
    assert [trabajo.id for trabajo in _panel(taller, OTRO_TECNICO)[0].trabajos] == [2]


# ------------------------------------------------------------------ compras
def test_ca_021_solicitudes_con_dias_habiles(taller: Taller) -> None:
    numero = en_espera(taller)
    # Del lunes 5 al lunes 12 de octubre: 5 días hábiles.
    poner_hora(taller.reloj, AHORA + timedelta(days=7))

    vistas = ManejadorListarSolicitudesPendientes(_lector(taller), taller.reloj).ejecutar(
        ListarSolicitudesPendientes()
    )

    assert len(vistas) == 1
    assert vistas[0].numero_orden == numero
    assert (vistas[0].refaccion, vistas[0].cantidad) == ("Balatas", 2)
    assert vistas[0].fecha_solicitud == AHORA
    assert vistas[0].dias_habiles_transcurridos == 5


def test_ca_021_solicitud_que_ya_llego_no_aparece(taller: Taller) -> None:
    numero = en_espera(taller)
    taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))

    vistas = ManejadorListarSolicitudesPendientes(_lector(taller), taller.reloj).ejecutar(
        ListarSolicitudesPendientes()
    )

    assert vistas == []


# ------------------------------------------------------------------ cotizaciones
def test_ca_007_lista_cotizaciones_por_aprobar(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller, importes=("20000.00",))
    cotizada(taller)

    vistas = ManejadorListarCotizacionesPendientesDeAprobacion(_lector(taller)).ejecutar(
        ListarCotizacionesPendientesDeAprobacion()
    )

    assert [(v.id_cotizacion, v.numero_orden, v.version, v.total) for v in vistas] == [
        (id_cotizacion, numero, "v.1", "20000.00")
    ]


def test_ca_005_detalle_de_cotizacion(taller: Taller) -> None:
    numero = diagnosticada(taller)
    trabajo = TrabajoPropuesto(
        1, "Balatas", Decimal("500.00"), (RefaccionPropuesta("Juego", 2, Decimal("100.00")),)
    )
    resultado = taller.cotizacion.generar_inicial(GenerarCotizacion(numero, (trabajo,)))

    vista = ManejadorConsultarCotizacion(_lector(taller)).ejecutar(
        ConsultarCotizacion(resultado.id)
    )

    assert (vista.version, vista.tipo, vista.total) == ("v.1", "Inicial", "700.00")
    linea = vista.lineas[0]
    assert (linea.mano_de_obra, linea.subtotal, linea.decision) == ("500.00", "700.00", None)
    assert linea.refacciones[0].importe == "200.00"


def test_cotizacion_inexistente(taller: Taller) -> None:
    with pytest.raises(CotizacionNoEncontrada):
        ManejadorConsultarCotizacion(_lector(taller)).ejecutar(ConsultarCotizacion("COT-9999"))


# ------------------------------------------------------------------ expediente
def test_expediente_reune_cotizaciones_trabajos_solicitudes_y_pago(taller: Taller) -> None:
    numero = pagada(taller)

    vista = ManejadorConsultarExpedienteDeOrden(_lector(taller)).ejecutar(
        ConsultarExpedienteDeOrden(numero)
    )

    assert vista.estado == "Pagada"
    assert vista.kilometraje == 45000
    assert vista.nivel_de_combustible == "1/2"
    assert vista.diagnostico_fallas == "Balatas gastadas"
    assert vista.total_autorizado == "3000.00"
    assert (vista.pago_monto, vista.pago_forma) == ("3000.00", "Tarjeta")
    assert [c.version for c in vista.cotizaciones] == ["v.1"]
    assert [t.estado for t in vista.trabajos] == ["Completado", "Completado"]
    assert vista.cotizaciones[0].autorizante == "Luis Peña"


def test_expediente_de_orden_con_solicitud_y_nota(taller: Taller) -> None:
    numero = pausada(taller)

    vista = ManejadorConsultarExpedienteDeOrden(_lector(taller)).ejecutar(
        ConsultarExpedienteDeOrden(numero)
    )

    assert vista.solicitudes[0].refaccion == "Balatas"
    assert vista.nota_firmada is True
    assert vista.pago_monto is None


def test_expediente_de_orden_recien_recibida(taller: Taller) -> None:
    numero = recibida(taller)

    vista = ManejadorConsultarExpedienteDeOrden(_lector(taller)).ejecutar(
        ConsultarExpedienteDeOrden(numero)
    )

    assert vista.diagnostico_fallas is None
    assert vista.nota_firmada is False
    assert vista.cotizaciones == ()


def test_expediente_de_orden_cancelada(taller: Taller) -> None:
    numero = recibida(taller)
    taller.cancelacion.cancelar(CancelarOrden(numero, "Desistió", ASESOR))

    vista = ManejadorConsultarExpedienteDeOrden(_lector(taller)).ejecutar(
        ConsultarExpedienteDeOrden(numero)
    )

    assert vista.cancelacion_motivo == "Desistió"


def test_expediente_con_credito_y_falla_adicional(taller: Taller) -> None:
    numero = en_reparacion(taller)
    taller.diagnostico.reportar_falla_adicional(ReportarFallaAdicional(numero, TECNICO, "Fuga"))
    con_credito = por_cobrar(taller)

    falla = ManejadorConsultarExpedienteDeOrden(_lector(taller)).ejecutar(
        ConsultarExpedienteDeOrden(numero)
    ).fallas_adicionales[0]
    credito = ManejadorConsultarExpedienteDeOrden(_lector(taller)).ejecutar(
        ConsultarExpedienteDeOrden(con_credito)
    )

    assert falla.descripcion == "Fuga"
    assert credito.credito_monto == "3000.00"
    assert credito.credito_fecha_vencimiento is None


def test_expediente_de_orden_inexistente(taller: Taller) -> None:
    with pytest.raises(OrdenNoEncontrada):
        ManejadorConsultarExpedienteDeOrden(_lector(taller)).ejecutar(
            ConsultarExpedienteDeOrden("OS-9999")
        )


# ------------------------------------------------------------------ gerencia
def test_ca_030_lista_abiertas_y_cerradas(taller: Taller) -> None:
    abierta = recibida(taller)
    cerrada = recibida(taller)
    taller.cancelacion.cancelar(CancelarOrden(cerrada, "Desistió", ASESOR))

    vistas = ManejadorListarOrdenes(_lector(taller)).ejecutar(ListarOrdenes())

    assert {(v.numero_orden, v.estado, v.abierta) for v in vistas} == {
        (abierta, "Recibida", True),
        (cerrada, "Cancelada", False),
    }


def test_ca_030_filtra_por_estado(taller: Taller) -> None:
    recibida(taller)
    numero = en_diagnostico(taller)

    vistas = ManejadorListarOrdenes(_lector(taller)).ejecutar(
        ListarOrdenes(EstadoOrden.EN_DIAGNOSTICO)
    )

    assert [vista.numero_orden for vista in vistas] == [numero]


def test_ca_031_suma_pagos_de_hoy(taller: Taller) -> None:
    pagada(taller)
    pagada(taller)

    assert _ingresos(taller) == "6000.00"


def test_ca_031_sin_pagos_da_cero(taller: Taller) -> None:
    assert _ingresos(taller) == "0.00"


def test_rn_21_excluye_cargos_a_credito(taller: Taller) -> None:
    pagada(taller)
    por_cobrar(taller)

    assert _ingresos(taller) == "3000.00"


def test_rn_21_usa_el_dia_de_monterrey(taller: Taller) -> None:
    numero = lista(taller)
    # 23:30 del 5 de octubre en Monterrey: en UTC ya es 6 de octubre.
    poner_hora(taller.reloj, datetime(2026, 10, 6, 5, 30, tzinfo=UTC))
    taller.caja.registrar_pago(RegistrarPago(numero, TOTAL_DE_DOS_TRABAJOS, FormaDePago.EFECTIVO))

    # 00:30 del 6 de octubre en Monterrey: ya es otro día.
    poner_hora(taller.reloj, datetime(2026, 10, 6, 6, 30, tzinfo=UTC))
    assert _ingresos(taller) == "0.00"

    # Mediodía del 5 de octubre en Monterrey: el pago de la noche pertenece a este día.
    poner_hora(taller.reloj, datetime(2026, 10, 5, 18, 0, tzinfo=UTC))
    assert _ingresos(taller) == "3000.00"


# ------------------------------------------------------------------ consulta pública
def test_ca_037_muestra_estado_y_fechas(taller: Taller) -> None:
    numero = recibida(taller)

    vista = ManejadorConsultarEstadoDeOrden(_lector(taller)).ejecutar(
        ConsultarEstadoDeOrden(numero.lower(), "abc 001")
    )

    assert vista.numero_orden == numero
    assert vista.estado == "Recibida"
    assert vista.fecha_ingreso == AHORA
    assert vista.ultima_actualizacion == AHORA


MENSAJE_SIN_COINCIDENCIA = (
    "No se encontró una orden con esos datos. "
    "Revise el número de orden y las placas e intente de nuevo."
)


def test_ca_038_no_coincide_con_mensaje_exacto(taller: Taller) -> None:
    with pytest.raises(OrdenNoEncontrada) as error:
        ManejadorConsultarEstadoDeOrden(_lector(taller)).ejecutar(
            ConsultarEstadoDeOrden("OS-9999", "XXX000")
        )

    assert str(error.value) == MENSAJE_SIN_COINCIDENCIA


def test_rn_20_folio_valido_con_otras_placas_no_revela_nada(taller: Taller) -> None:
    numero = recibida(taller)

    with pytest.raises(OrdenNoEncontrada) as error:
        ManejadorConsultarEstadoDeOrden(_lector(taller)).ejecutar(
            ConsultarEstadoDeOrden(numero, "XXX000")
        )

    assert str(error.value) == MENSAJE_SIN_COINCIDENCIA


def test_rn_20_datos_vacios_son_invalidos(taller: Taller) -> None:
    with pytest.raises(ValorInvalido):
        ManejadorConsultarEstadoDeOrden(_lector(taller)).ejecutar(
            ConsultarEstadoDeOrden(" ", "ABC001")
        )


# ------------------------------------------------------------------ alertas
def _agregar_alertas(taller: Taller, *alertas: AlertaInterna) -> None:
    with taller.uow() as uow:
        for alerta in alertas:
            uow.alertas.agregar(alerta)
        uow.confirmar()


def test_ca_032_listar_alertas_del_empleado(taller: Taller) -> None:
    propia = AlertaInterna("Prueba", "Para el asesor", AHORA, destinatario=ASESOR)
    ajena = AlertaInterna("Prueba", "Para el técnico", AHORA, destinatario=TECNICO)
    _agregar_alertas(taller, propia, ajena)

    alertas = ManejadorListarAlertas(_lector(taller)).ejecutar(
        ListarAlertas(ASESOR, RolDeEmpleado.ASESOR)
    )

    assert alertas == [propia]


def test_ca_007_listar_alertas_por_rol(taller: Taller) -> None:
    al_rol = AlertaInterna(
        "Prueba", "Para los gerentes", AHORA, destinatario_rol=RolDeEmpleado.GERENTE
    )
    _agregar_alertas(taller, al_rol)

    gerente = ManejadorListarAlertas(_lector(taller)).ejecutar(
        ListarAlertas("EMP-004", RolDeEmpleado.GERENTE)
    )
    asesor = ManejadorListarAlertas(_lector(taller)).ejecutar(
        ListarAlertas(ASESOR, RolDeEmpleado.ASESOR)
    )

    assert gerente == [al_rol]
    assert asesor == []


# ------------------------------------------------------------------ candidatas de los plazos
def test_rn_11_ordenes_con_solicitudes_pendientes(taller: Taller) -> None:
    recibida(taller)
    con_pendiente = en_espera(taller)

    assert [str(n) for n in _lector(taller).ordenes_con_solicitudes_pendientes()] == [con_pendiente]


def test_rn_12_cotizaciones_presentadas_sin_decision(taller: Taller) -> None:
    cotizada(taller)
    _, presentada = cotizada(taller)
    taller.cotizacion.presentar(PresentarCotizacion(presentada))

    assert _lector(taller).cotizaciones_presentadas_sin_decision() == [presentada]


