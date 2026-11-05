"""ServicioDeAutorizacion (US-006, US-016)."""
from __future__ import annotations

import pytest

from application.comandos import CompletarTrabajo, IniciarTrabajo, RegistrarDecisionDelCliente
from domain.compartido.errores import (
    AutorizanteNoValido,
    CotizacionNoEncontrada,
    OperacionDeCotizacionNoPermitida,
    ValorInvalido,
)
from domain.cotizaciones.eventos import CotizacionAutorizada, CotizacionRechazadaPorCliente
from domain.cotizaciones.valores import RolDeAutorizante
from domain.ordenes.estados import EstadoTrabajo
from domain.ordenes.eventos import OrdenAutorizada
from tests.unit.application.escenarios import (
    AHORA,
    TECNICO,
    Taller,
    con_adicional,
    cotizada,
    decidir,
)


def test_ca_010_autorizacion_total(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller)

    resultado = decidir(taller, id_cotizacion, (1, 2))

    assert resultado.estado_cotizacion == "Autorizada"
    assert resultado.estado_orden == "Autorizada"
    assert resultado.trabajos_autorizados == ("Trabajo 1", "Trabajo 2")
    assert resultado.trabajos_no_autorizados == ()
    decision = taller.datos.cotizaciones[id_cotizacion].decision
    assert (decision.autorizante.nombre, decision.registrada_en) == ("Luis Peña", AHORA)
    assert len(taller.datos.ordenes[numero].trabajos) == 2
    tipos = [type(evento) for evento in taller.publicador.publicar.call_args.args[0]]
    assert CotizacionAutorizada in tipos
    assert OrdenAutorizada in tipos


def test_ca_010_autorizacion_parcial_marca_no_autorizados(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller)

    resultado = decidir(taller, id_cotizacion, (1,))

    assert resultado.estado_cotizacion == "Autorizada Parcialmente"
    assert resultado.estado_orden == "Autorizada"
    assert resultado.trabajos_no_autorizados == ("Trabajo 2",)
    estados = [trabajo.estado for trabajo in taller.datos.ordenes[numero].trabajos]
    assert estados == [EstadoTrabajo.PENDIENTE, EstadoTrabajo.NO_AUTORIZADO]


def test_ca_012_rechazo_total_deja_la_orden_cotizada(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller)

    resultado = decidir(taller, id_cotizacion, ())

    orden = taller.datos.ordenes[numero]
    assert resultado.estado_cotizacion == "Rechazada"
    assert resultado.estado_orden == "Cotizada"
    assert orden.rechazo_total is True
    tipos = [type(evento) for evento in taller.publicador.publicar.call_args.args[0]]
    assert tipos == [CotizacionRechazadaPorCliente]


def test_ca_017_adicional_agrega_trabajos_pendientes(taller: Taller) -> None:
    numero, id_adicional = con_adicional(taller)

    resultado = decidir(taller, id_adicional, (1, 2))

    orden = taller.datos.ordenes[numero]
    assert resultado.estado_cotizacion == "Autorizada"
    assert resultado.estado_orden == "En Reparación"
    assert [trabajo.estado.value for trabajo in orden.trabajos[2:]] == ["Pendiente", "Pendiente"]
    assert orden.adicionales_pendientes == 0
    eventos = taller.publicador.publicar.call_args.args[0]
    autorizada = next(e for e in eventos if isinstance(e, CotizacionAutorizada))
    assert autorizada.es_adicional is True


def test_ca_018_adicional_rechazada_pasa_a_lista(taller: Taller) -> None:
    numero, id_adicional = con_adicional(taller)
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 2, TECNICO))
    taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 1, TECNICO))
    taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 2, TECNICO))

    resultado = decidir(taller, id_adicional, ())

    orden = taller.datos.ordenes[numero]
    assert resultado.estado_cotizacion == "Rechazada"
    assert resultado.estado_orden == "Lista para Entrega"
    assert [t.estado.value for t in orden.trabajos[2:]] == ["No Autorizado", "No Autorizado"]
    assert str(orden.total_autorizado.monto) == "3000.00"


def test_ca_018_adicional_rechazada_con_trabajos_abiertos_sigue_en_reparacion(
    taller: Taller,
) -> None:
    _, id_adicional = con_adicional(taller)

    resultado = decidir(taller, id_adicional, ())

    assert resultado.estado_orden == "En Reparación"


def test_ca_029_conductor_no_autoriza(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller, flotilla=True)

    with pytest.raises(AutorizanteNoValido, match="Responsable de Flotilla"):
        taller.autorizacion.registrar_decision(
            RegistrarDecisionDelCliente(
                id_cotizacion, (1, 2), "Pedro el conductor", RolDeAutorizante.CLIENTE
            )
        )

    assert taller.datos.ordenes[numero].estado.value == "Cotizada"


def test_ca_029_decision_a_nombre_del_responsable_de_flotilla(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, flotilla=True)

    resultado = decidir(taller, id_cotizacion, (1, 2), flotilla=True)

    assert resultado.estado_orden == "Autorizada"
    assert taller.datos.cotizaciones[id_cotizacion].decision.autorizante.nombre == "Ana Torres"


def test_rn_07_autorizante_invalido_no_cambia_nada(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller)
    taller.publicador.publicar.reset_mock()

    with pytest.raises(AutorizanteNoValido):
        taller.autorizacion.registrar_decision(
            RegistrarDecisionDelCliente(
                id_cotizacion, (1,), "Otra persona", RolDeAutorizante.CLIENTE
            )
        )

    assert taller.datos.cotizaciones[id_cotizacion].decision is None
    assert taller.datos.ordenes[numero].trabajos == ()
    taller.publicador.publicar.assert_not_called()


def test_rn_08_no_autorizados_no_suman_al_total(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller)

    decidir(taller, id_cotizacion, (2,))

    assert str(taller.datos.ordenes[numero].total_autorizado.monto) == "2000.00"


def test_rn_22_segunda_decision_se_rechaza(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller)
    decidir(taller, id_cotizacion, (1, 2))

    with pytest.raises(OperacionDeCotizacionNoPermitida):
        decidir(taller, id_cotizacion, (1,))


def test_rn_22_linea_inexistente_no_cambia_nada(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller)

    with pytest.raises(ValorInvalido, match="no tiene los trabajos"):
        decidir(taller, id_cotizacion, (1, 9))

    assert taller.datos.cotizaciones[id_cotizacion].decision is None
    assert taller.datos.ordenes[numero].estado.value == "Cotizada"


def test_cotizacion_inexistente_no_recibe_decision(taller: Taller) -> None:
    with pytest.raises(CotizacionNoEncontrada):
        decidir(taller, "COT-9999", (1,))
