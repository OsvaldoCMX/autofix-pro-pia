"""ServicioDeCotizacion (US-004, US-005, US-023)."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from application.comandos import (
    AjustarCotizacion,
    AsignarTrabajos,
    GenerarCotizacion,
    IniciarTrabajo,
    PresentarCotizacion,
    RefaccionPropuesta,
    RegistrarRecontacto,
    TrabajoPropuesto,
)
from domain.compartido.errores import (
    CotizacionNoEncontrada,
    CotizacionSinTrabajos,
    DiagnosticoRequerido,
    OperacionDeCotizacionNoPermitida,
    OrdenNoEncontrada,
    TransicionDeEstadoNoPermitida,
    ValorInvalido,
)
from domain.cotizaciones.eventos import AprobacionGerencialRequerida, CotizacionGenerada
from tests.unit.application.escenarios import (
    AHORA,
    ASESOR,
    TECNICO,
    Taller,
    autorizada,
    cotizada,
    diagnosticada,
    en_diagnostico,
    en_reparacion,
    poner_hora,
    trabajos,
)

MAYOR_AL_UMBRAL = ("15000.01",)


def test_ca_005_genera_v1_y_marca_cotizada(taller: Taller) -> None:
    numero = diagnosticada(taller)

    resultado = taller.cotizacion.generar_inicial(GenerarCotizacion(numero, trabajos("1000.00")))

    assert resultado.version == "v.1"
    assert resultado.tipo == "Inicial"
    assert resultado.estado == "Pendiente de Autorización del Cliente"
    assert taller.datos.ordenes[numero].estado.value == "Cotizada"
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [CotizacionGenerada]


def test_ca_005_folio_y_total(taller: Taller) -> None:
    numero = diagnosticada(taller)
    con_refaccion = TrabajoPropuesto(
        1,
        "Cambio de balatas",
        Decimal("785.00"),
        (RefaccionPropuesta("Balatas", 2, Decimal("1140.00")),),
    )

    resultado = taller.cotizacion.generar_inicial(GenerarCotizacion(numero, (con_refaccion,)))

    assert resultado.id == "COT-0001"
    assert resultado.numero_orden == numero
    assert resultado.total == "3065.00"


def test_ca_005_orden_y_cotizacion_se_guardan_juntas(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller)

    orden = taller.datos.ordenes[numero]
    assert taller.datos.cotizaciones[id_cotizacion].numero_orden == orden.numero
    assert orden.cotizada is True


def test_rn_02_sin_diagnostico_no_cotiza_ni_consume_folio(taller: Taller) -> None:
    numero = en_diagnostico(taller)

    with pytest.raises(DiagnosticoRequerido):
        taller.cotizacion.generar_inicial(GenerarCotizacion(numero, trabajos("100.00")))

    assert taller.datos.cotizaciones == {}
    assert taller.datos.ultimo_folio_de_cotizacion == 0
    assert taller.datos.ordenes[numero].estado.value == "En Diagnóstico"


def test_orden_inexistente_no_se_cotiza(taller: Taller) -> None:
    with pytest.raises(OrdenNoEncontrada):
        taller.cotizacion.generar_inicial(GenerarCotizacion("OS-9999", trabajos("100.00")))


def test_ca_007_mayor_al_umbral_espera_al_gerente(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=MAYOR_AL_UMBRAL)

    assert taller.datos.cotizaciones[id_cotizacion].estado.value == (
        "Pendiente de Aprobación Gerencial"
    )
    eventos = taller.publicador.publicar.call_args.args[0]
    assert AprobacionGerencialRequerida in [type(evento) for evento in eventos]


def test_rn_04_exactamente_15000_no_requiere_gerente(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=("15000.00",))

    assert taller.datos.cotizaciones[id_cotizacion].estado.value == (
        "Pendiente de Autorización del Cliente"
    )


def test_rn_06_no_se_presenta_si_espera_al_gerente(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=MAYOR_AL_UMBRAL)

    with pytest.raises(OperacionDeCotizacionNoPermitida):
        taller.cotizacion.presentar(PresentarCotizacion(id_cotizacion))

    assert taller.datos.cotizaciones[id_cotizacion].fecha_presentacion is None


def test_ca_006_presentar_guarda_la_fecha(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller)

    resultado = taller.cotizacion.presentar(PresentarCotizacion(id_cotizacion))

    assert resultado.fecha_presentacion == AHORA
    assert resultado.estado == "Pendiente de Autorización del Cliente"


def test_cotizacion_inexistente_no_se_presenta(taller: Taller) -> None:
    with pytest.raises(CotizacionNoEncontrada):
        taller.cotizacion.presentar(PresentarCotizacion("COT-9999"))


def test_ca_016_adicional_v2_sin_gerente(taller: Taller) -> None:
    numero = en_reparacion(taller)

    resultado = taller.cotizacion.generar_adicional(GenerarCotizacion(numero, trabajos("90000.00")))

    assert resultado.version == "v.2"
    assert resultado.tipo == "Adicional"
    assert resultado.estado == "Pendiente de Autorización del Cliente"
    assert taller.datos.ordenes[numero].adicionales_pendientes == 1


def test_ca_016_cada_adicional_toma_la_siguiente_version(taller: Taller) -> None:
    numero = en_reparacion(taller)
    taller.cotizacion.generar_adicional(GenerarCotizacion(numero, trabajos("100.00")))

    resultado = taller.cotizacion.generar_adicional(GenerarCotizacion(numero, trabajos("100.00")))

    assert resultado.version == "v.3"


def test_ca_016_adicional_fuera_de_reparacion_se_rechaza(taller: Taller) -> None:
    numero, _ = cotizada(taller)

    with pytest.raises(TransicionDeEstadoNoPermitida, match="En Reparación"):
        taller.cotizacion.generar_adicional(GenerarCotizacion(numero, trabajos("100.00")))


def test_rn_24_adicional_no_modifica_la_original(taller: Taller) -> None:
    numero, id_original = autorizada(taller)
    original = taller.datos.cotizaciones[id_original]
    total, estado = original.total, original.estado
    taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1, 2), TECNICO))
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 1, TECNICO))

    taller.cotizacion.generar_adicional(GenerarCotizacion(numero, trabajos("100.00")))

    original = taller.datos.cotizaciones[id_original]
    assert (original.total, original.estado) == (total, estado)


def test_rn_23_sin_trabajos_no_cambia_la_orden(taller: Taller) -> None:
    numero = diagnosticada(taller)

    with pytest.raises(CotizacionSinTrabajos):
        taller.cotizacion.generar_inicial(GenerarCotizacion(numero, ()))

    orden = taller.datos.ordenes[numero]
    assert orden.estado.value == "En Diagnóstico"
    assert orden.cotizada is False


def test_ca_040_registra_recontacto_sin_cambiar_estado(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller)
    taller.cotizacion.presentar(PresentarCotizacion(id_cotizacion))
    despues = AHORA + timedelta(hours=49)
    poner_hora(taller.reloj, despues)

    resultado = taller.cotizacion.registrar_recontacto(RegistrarRecontacto(id_cotizacion, ASESOR))

    cotizacion = taller.datos.cotizaciones[id_cotizacion]
    assert resultado.estado == "Pendiente de Autorización del Cliente"
    assert resultado.registrado_en == despues
    assert cotizacion.ultimo_contacto == despues


def test_ca_040_recontacto_sin_presentar_se_rechaza(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller)

    with pytest.raises(OperacionDeCotizacionNoPermitida):
        taller.cotizacion.registrar_recontacto(RegistrarRecontacto(id_cotizacion, ASESOR))


def test_ca_009_ajustar_una_cotizacion_que_no_lo_requiere_se_rechaza(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller)

    with pytest.raises(OperacionDeCotizacionNoPermitida):
        taller.cotizacion.ajustar(AjustarCotizacion(id_cotizacion, trabajos("100.00")))



def test_no_genera_cotizacion_con_servicio_inhabilitado(taller: Taller) -> None:
    """D-05: el dato es inválido, la orden sigue «En Diagnóstico» y no se consume un folio."""
    numero = diagnosticada(taller)
    taller.registrar_servicios_de_orden(numero, ("AUT-P001",), ("AUT-P011",))
    taller.publicador.reset_mock()

    with pytest.raises(ValorInvalido, match="AUT-P011"):
        taller.cotizacion.generar_inicial(GenerarCotizacion(numero, trabajos("1000.00")))

    assert taller.datos.ordenes[numero].estado.value == "En Diagnóstico"
    assert taller.datos.cotizaciones == {}
    assert taller.datos.ultimo_folio_de_cotizacion == 0
    taller.publicador.publicar.assert_not_called()


def test_el_error_de_estado_tiene_prioridad_sobre_el_servicio_inhabilitado(taller: Taller) -> None:
    numero = en_diagnostico(taller)
    taller.registrar_servicios_de_orden(numero, (), ("AUT-P011",))

    with pytest.raises(DiagnosticoRequerido):
        taller.cotizacion.generar_inicial(GenerarCotizacion(numero, trabajos("1000.00")))


def test_orden_con_servicios_habilitados_si_se_cotiza(taller: Taller) -> None:
    numero = diagnosticada(taller)
    taller.registrar_servicios_de_orden(numero, ("AUT-P001",), ())

    resultado = taller.cotizacion.generar_inicial(GenerarCotizacion(numero, trabajos("1000.00")))

    assert resultado.version == "v.1"
