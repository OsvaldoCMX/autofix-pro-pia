"""Aggregate Cotización: reglas, transiciones y eventos (modelo-de-dominio.md §2.2 y §5.2)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from domain.compartido.errores import (
    CotizacionSinTrabajos,
    OperacionDeCotizacionNoPermitida,
    ValorInvalido,
)
from domain.compartido.valores import Dinero, NumeroOrden
from domain.cotizaciones import eventos as ev
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.especificaciones import EsCotizacionInicial
from domain.cotizaciones.estados import EstadoCotizacion
from domain.cotizaciones.linea_de_cotizacion import DecisionDeLinea, LineaDeCotizacion
from domain.cotizaciones.valores import (
    Autorizante,
    Recontacto,
    RefaccionCotizada,
    RolDeAutorizante,
    TipoCotizacion,
    TrabajoDecidido,
    VersionCotizacion,
)
from tests.unit.domain.apoyo_esquema import valores_del_check

_E = EstadoCotizacion
INICIO = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
DESPUES = INICIO + timedelta(hours=1)
CLIENTE = Autorizante("Luis Peña", RolDeAutorizante.CLIENTE)
NUMERO = NumeroOrden("OS-1")


def _pesos(monto: str) -> Dinero:
    return Dinero(Decimal(monto))


def _linea(numero: int = 1, monto: str = "1000.00") -> LineaDeCotizacion:
    return LineaDeCotizacion(numero, f"Trabajo {numero}", _pesos(monto))


def _inicial(*lineas: LineaDeCotizacion) -> Cotizacion:
    return Cotizacion.generar(
        "COT-1",
        NUMERO,
        TipoCotizacion.INICIAL,
        VersionCotizacion(1),
        lineas or [_linea()],
        INICIO,
    )


def _adicional(monto: str = "90000.00") -> Cotizacion:
    return Cotizacion.generar(
        "COT-2",
        NUMERO,
        TipoCotizacion.ADICIONAL,
        VersionCotizacion(2),
        [_linea(monto=monto)],
        INICIO,
    )


def _con_gerente() -> Cotizacion:
    return _inicial(_linea(monto="20000.00"))


def _eventos_nuevos(cotizacion: Cotizacion) -> list[type]:
    return [type(evento) for evento in cotizacion.extraer_eventos()]


def _sin_eventos(cotizacion: Cotizacion) -> Cotizacion:
    cotizacion.extraer_eventos()
    return cotizacion


# ------------------------------------------------------------------ generar


def test_ca_005_genera_inicial_v1_con_total() -> None:
    refaccion = RefaccionCotizada("Balatas", 2, _pesos("450.00"))
    cotizacion = _inicial(
        LineaDeCotizacion(1, "Frenos", _pesos("800.00"), (refaccion,)),
        _linea(2, "1200.00"),
    )

    assert str(cotizacion.version) == "v.1"
    assert cotizacion.tipo is TipoCotizacion.INICIAL
    assert cotizacion.generada_en == INICIO
    assert cotizacion.total == _pesos("2900.00")
    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert [linea.numero for linea in cotizacion.lineas] == [1, 2]


def test_ca_005_total_igual_al_umbral_va_directo_al_cliente() -> None:
    cotizacion = _inicial(_linea(monto="15000.00"))

    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE


def test_ca_005_emite_cotizacion_generada_con_sus_datos() -> None:
    evento = _inicial(_linea(monto="3065.00")).extraer_eventos()[0]

    assert evento == ev.CotizacionGenerada(INICIO, "COT-1", "OS-1", "v.1", "3065.00")


def test_generar_acepta_otra_politica() -> None:
    cotizacion = Cotizacion.generar(
        "COT-1",
        NUMERO,
        TipoCotizacion.INICIAL,
        VersionCotizacion(1),
        [_linea()],
        INICIO,
        politica=EsCotizacionInicial(),
    )

    assert cotizacion.estado is _E.PENDIENTE_DE_APROBACION_GERENCIAL


def test_rn_23_cotizacion_sin_trabajos_se_rechaza() -> None:
    with pytest.raises(CotizacionSinTrabajos):
        Cotizacion.generar(
            "COT-1", NUMERO, TipoCotizacion.INICIAL, VersionCotizacion(1), [], INICIO
        )


def test_rn_23_lineas_repetidas_se_rechazan() -> None:
    with pytest.raises(ValorInvalido, match="repetido"):
        _inicial(_linea(1), _linea(1))


@pytest.mark.parametrize("cantidad", [0, -1])
def test_rn_23_refaccion_con_cantidad_invalida(cantidad: int) -> None:
    with pytest.raises(ValorInvalido, match="mayor a cero"):
        RefaccionCotizada("Balatas", cantidad, _pesos("100.00"))


def test_rn_23_refaccion_sin_descripcion() -> None:
    with pytest.raises(ValorInvalido, match="descripción"):
        RefaccionCotizada("  ", 1, _pesos("100.00"))


def test_rn_23_refaccion_calcula_su_importe() -> None:
    assert RefaccionCotizada(" Balatas ", 3, _pesos("100.50")).importe == _pesos("301.50")


def test_rn_23_linea_exige_numero_y_descripcion() -> None:
    with pytest.raises(ValorInvalido, match="línea"):
        LineaDeCotizacion(0, "Frenos", _pesos("1.00"))
    with pytest.raises(ValorInvalido, match="descripción"):
        LineaDeCotizacion(1, " ", _pesos("1.00"))


def test_rn_24_inicial_siempre_es_v1() -> None:
    with pytest.raises(ValorInvalido, match="versión 1"):
        Cotizacion.generar(
            "COT-1", NUMERO, TipoCotizacion.INICIAL, VersionCotizacion(2), [_linea()], INICIO
        )


def test_rn_24_adicional_es_v2_en_adelante() -> None:
    with pytest.raises(ValorInvalido, match="versión 2"):
        Cotizacion.generar(
            "COT-2", NUMERO, TipoCotizacion.ADICIONAL, VersionCotizacion(1), [_linea()], INICIO
        )
    assert str(_adicional().version) == "v.2"


def test_rn_24_version_empieza_en_uno() -> None:
    with pytest.raises(ValorInvalido, match="empieza en 1"):
        VersionCotizacion(0)


def test_ca_016_adicional_no_pasa_por_gerente() -> None:
    cotizacion = _adicional("90000.00")

    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert _eventos_nuevos(cotizacion) == [ev.CotizacionGenerada]


# ------------------------------------------------------------------ presentar


def test_ca_006_registra_fecha_de_presentacion() -> None:
    cotizacion = _sin_eventos(_inicial())

    cotizacion.marcar_presentada(DESPUES)

    assert cotizacion.fecha_presentacion == DESPUES
    assert cotizacion.ultimo_contacto == DESPUES
    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert cotizacion.extraer_eventos() == [ev.CotizacionPresentada(DESPUES, "COT-1", "OS-1")]


def test_ca_006_no_se_presenta_dos_veces() -> None:
    cotizacion = _inicial()
    cotizacion.marcar_presentada(INICIO)

    with pytest.raises(OperacionDeCotizacionNoPermitida, match="recontacto"):
        cotizacion.marcar_presentada(DESPUES)

    assert cotizacion.fecha_presentacion == INICIO


def test_ca_007_queda_pendiente_de_gerente_y_emite_alerta() -> None:
    cotizacion = _con_gerente()

    assert cotizacion.estado is _E.PENDIENTE_DE_APROBACION_GERENCIAL
    assert cotizacion.extraer_eventos() == [
        ev.CotizacionGenerada(INICIO, "COT-1", "OS-1", "v.1", "20000.00"),
        ev.AprobacionGerencialRequerida(INICIO, "COT-1", "OS-1", "20000.00"),
    ]


def test_rn_06_no_se_presenta_sin_aprobacion() -> None:
    cotizacion = _con_gerente()

    with pytest.raises(OperacionDeCotizacionNoPermitida, match="Pendiente de Aprobación"):
        cotizacion.marcar_presentada(DESPUES)

    assert cotizacion.fecha_presentacion is None


# ------------------------------------------------------------------ Gerente


def test_ca_008_aprueba_y_guarda_fecha() -> None:
    cotizacion = _sin_eventos(_con_gerente())

    cotizacion.aprobar_por_gerente(DESPUES)

    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert cotizacion.fecha_aprobacion_gerencial == DESPUES
    assert cotizacion.extraer_eventos() == [
        ev.CotizacionAprobadaPorGerente(DESPUES, "COT-1", "OS-1")
    ]


def test_rn_04_aprobar_dos_veces_se_rechaza() -> None:
    cotizacion = _con_gerente()
    cotizacion.aprobar_por_gerente(DESPUES)

    with pytest.raises(OperacionDeCotizacionNoPermitida):
        cotizacion.aprobar_por_gerente(DESPUES)


def test_rn_04_no_se_aprueba_lo_que_requiere_ajuste() -> None:
    cotizacion = _con_gerente()
    cotizacion.rechazar_por_gerente("Revisar", DESPUES)

    with pytest.raises(OperacionDeCotizacionNoPermitida, match="Requiere Ajuste"):
        cotizacion.aprobar_por_gerente(DESPUES)

    assert cotizacion.estado is _E.REQUIERE_AJUSTE
    assert cotizacion.fecha_aprobacion_gerencial is None


def test_rn_05_no_se_ajusta_lo_que_espera_al_gerente() -> None:
    with pytest.raises(OperacionDeCotizacionNoPermitida, match="Requiere Ajuste"):
        _con_gerente().ajustar([_linea()], DESPUES)


def test_ca_009_rechazo_guarda_observaciones() -> None:
    cotizacion = _sin_eventos(_con_gerente())

    cotizacion.rechazar_por_gerente(" Bajar la mano de obra ", DESPUES)

    assert cotizacion.estado is _E.REQUIERE_AJUSTE
    assert cotizacion.observaciones_del_gerente == "Bajar la mano de obra"
    assert cotizacion.extraer_eventos() == [
        ev.CotizacionRechazadaPorGerente(DESPUES, "COT-1", "OS-1", "Bajar la mano de obra")
    ]


@pytest.mark.parametrize("observaciones", ["", "   "])
def test_ca_009_rechazo_exige_observaciones(observaciones: str) -> None:
    cotizacion = _con_gerente()

    with pytest.raises(ValorInvalido, match="observaciones"):
        cotizacion.rechazar_por_gerente(observaciones, DESPUES)

    assert cotizacion.estado is _E.PENDIENTE_DE_APROBACION_GERENCIAL


def test_rn_05_gerente_solo_rechaza_lo_que_espera_revision() -> None:
    with pytest.raises(OperacionDeCotizacionNoPermitida):
        _inicial().rechazar_por_gerente("No procede", DESPUES)


def test_rn_05_ajustada_no_regresa_a_revision() -> None:
    cotizacion = _con_gerente()
    cotizacion.rechazar_por_gerente("Revisar", DESPUES)
    _sin_eventos(cotizacion)

    cotizacion.ajustar([_linea(monto="18000.00")], DESPUES)

    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert cotizacion.total == _pesos("18000.00")
    assert cotizacion.extraer_eventos() == [
        ev.CotizacionAjustada(DESPUES, "COT-1", "OS-1", "18000.00")
    ]


def test_rn_05_ajustar_exige_al_menos_un_trabajo_sin_cambiar_nada() -> None:
    cotizacion = _con_gerente()
    cotizacion.rechazar_por_gerente("Revisar", DESPUES)

    with pytest.raises(CotizacionSinTrabajos):
        cotizacion.ajustar([], DESPUES)

    assert cotizacion.estado is _E.REQUIERE_AJUSTE
    assert cotizacion.total == _pesos("20000.00")


def test_rn_05_solo_se_ajusta_lo_que_requiere_ajuste() -> None:
    with pytest.raises(OperacionDeCotizacionNoPermitida, match="Requiere Ajuste"):
        _inicial().ajustar([_linea()], DESPUES)


# ------------------------------------------------------------------ decisión


def test_ca_010_autorizacion_total() -> None:
    cotizacion = _sin_eventos(_inicial(_linea(1), _linea(2)))

    decision = cotizacion.registrar_decision({1, 2}, CLIENTE, DESPUES)

    assert cotizacion.estado is _E.AUTORIZADA
    assert cotizacion.decision == decision
    assert decision.id_cotizacion == "COT-1"
    assert decision.autorizante == CLIENTE
    assert decision.registrada_en == DESPUES
    assert decision.tipo_cotizacion is TipoCotizacion.INICIAL
    assert decision.no_autorizados == ()
    assert not decision.es_rechazo_total
    assert cotizacion.extraer_eventos() == [
        ev.CotizacionAutorizada(DESPUES, "COT-1", "OS-1", False, False, "Luis Peña")
    ]


def test_ca_010_autorizacion_parcial() -> None:
    cotizacion = _sin_eventos(_inicial(_linea(1, "100.00"), _linea(2, "200.00")))

    decision = cotizacion.registrar_decision({2}, CLIENTE, DESPUES)

    assert cotizacion.estado is _E.AUTORIZADA_PARCIALMENTE
    assert decision.autorizados == (TrabajoDecidido(2, "Trabajo 2", _pesos("200.00")),)
    assert decision.no_autorizados == (TrabajoDecidido(1, "Trabajo 1", _pesos("100.00")),)
    assert cotizacion.lineas[0].decision is DecisionDeLinea.NO_AUTORIZADO
    assert cotizacion.lineas[1].decision is DecisionDeLinea.AUTORIZADA
    assert cotizacion.extraer_eventos() == [
        ev.CotizacionAutorizada(DESPUES, "COT-1", "OS-1", True, False, "Luis Peña")
    ]


def test_ca_012_rechazo_total() -> None:
    cotizacion = _sin_eventos(_inicial(_linea(1), _linea(2)))

    decision = cotizacion.registrar_decision(set(), CLIENTE, DESPUES)

    assert cotizacion.estado is _E.RECHAZADA
    assert decision.es_rechazo_total
    assert cotizacion.extraer_eventos() == [
        ev.CotizacionRechazadaPorCliente(DESPUES, "COT-1", "OS-1", False, "Luis Peña")
    ]


def test_ca_017_autorizar_adicional_lo_indica_en_el_evento() -> None:
    cotizacion = _sin_eventos(_adicional())

    cotizacion.registrar_decision({1}, CLIENTE, DESPUES)

    assert cotizacion.extraer_eventos() == [
        ev.CotizacionAutorizada(DESPUES, "COT-2", "OS-1", False, True, "Luis Peña")
    ]


def test_ca_018_rechazar_adicional_lo_indica_en_el_evento() -> None:
    cotizacion = _sin_eventos(_adicional())

    decision = cotizacion.registrar_decision(set(), CLIENTE, DESPUES)

    assert decision.tipo_cotizacion is TipoCotizacion.ADICIONAL
    assert cotizacion.extraer_eventos() == [
        ev.CotizacionRechazadaPorCliente(DESPUES, "COT-2", "OS-1", True, "Luis Peña")
    ]


def test_rn_22_segunda_decision_se_rechaza() -> None:
    cotizacion = _inicial()
    primera = cotizacion.registrar_decision({1}, CLIENTE, DESPUES)

    with pytest.raises(OperacionDeCotizacionNoPermitida):
        cotizacion.registrar_decision(set(), CLIENTE, DESPUES)

    assert cotizacion.decision == primera
    assert cotizacion.estado is _E.AUTORIZADA


def test_rn_22_decision_con_gerente_pendiente_se_rechaza() -> None:
    with pytest.raises(OperacionDeCotizacionNoPermitida):
        _con_gerente().registrar_decision({1}, CLIENTE, DESPUES)


def test_rn_08_linea_inexistente_se_rechaza() -> None:
    cotizacion = _inicial()

    with pytest.raises(ValorInvalido, match=r"\[9\]"):
        cotizacion.registrar_decision({1, 9}, CLIENTE, DESPUES)

    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert cotizacion.lineas[0].decision is None


def test_ca_010_autorizante_exige_nombre() -> None:
    with pytest.raises(ValorInvalido, match="nombre"):
        Autorizante(" ", RolDeAutorizante.CLIENTE)


# ------------------------------------------------------------------ recontacto


def test_ca_040_recontacto_no_cambia_estado() -> None:
    cotizacion = _inicial()
    cotizacion.marcar_presentada(INICIO)
    _sin_eventos(cotizacion)

    cotizacion.registrar_recontacto(" EMP-001 ", DESPUES)

    assert cotizacion.estado is _E.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
    assert cotizacion.recontactos == (Recontacto("EMP-001", DESPUES),)
    assert cotizacion.ultimo_contacto == DESPUES
    assert cotizacion.extraer_eventos() == [
        ev.RecontactoRegistrado(DESPUES, "COT-1", "OS-1", "EMP-001")
    ]


def test_ca_040_no_se_recontacta_sin_haber_presentado() -> None:
    with pytest.raises(OperacionDeCotizacionNoPermitida, match="presenta"):
        _inicial().registrar_recontacto("EMP-001", DESPUES)


def test_ca_040_no_se_recontacta_despues_de_la_decision() -> None:
    cotizacion = _inicial()
    cotizacion.marcar_presentada(INICIO)
    cotizacion.registrar_decision({1}, CLIENTE, DESPUES)

    with pytest.raises(OperacionDeCotizacionNoPermitida):
        cotizacion.registrar_recontacto("EMP-001", DESPUES)


def test_ca_040_recontacto_exige_asesor() -> None:
    cotizacion = _inicial()
    cotizacion.marcar_presentada(INICIO)

    with pytest.raises(ValorInvalido, match="asesor"):
        cotizacion.registrar_recontacto(" ", DESPUES)


# ------------------------------------------------------------------ valores de la base


def test_tipo_rol_y_decision_coinciden_con_la_base() -> None:
    assert {tipo.value for tipo in TipoCotizacion} == valores_del_check("cotizaciones", "tipo")
    assert {rol.value for rol in RolDeAutorizante} == valores_del_check(
        "cotizaciones", "decision_rol"
    )
    assert {decision.value for decision in DecisionDeLinea} == valores_del_check(
        "lineas_de_cotizacion", "decision"
    )
