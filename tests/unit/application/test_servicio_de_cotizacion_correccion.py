"""ServicioDeCotizacion.corregir (US-026, H-PIA-21)."""
from __future__ import annotations

from datetime import timedelta

import pytest

from application.comandos import (
    CorregirCotizacion,
    PresentarCotizacion,
    RegistrarRecontacto,
    RevisarCotizacion,
)
from domain.compartido.errores import (
    CotizacionNoEncontrada,
    OperacionDeCotizacionNoPermitida,
    ValorInvalido,
)
from domain.cotizaciones.eventos import AprobacionGerencialRequerida, CotizacionCorregida
from tests.unit.application.escenarios import (
    AHORA,
    ASESOR,
    Taller,
    autorizada,
    cotizada,
    poner_hora,
    trabajos,
)


def _corregir(taller: Taller, id_cotizacion: str, *importes: str, motivo: str = "Importe mal"):
    return taller.cotizacion.corregir(
        CorregirCotizacion(id_cotizacion, trabajos(*importes), motivo, ASESOR)
    )


def _eventos_publicados(taller: Taller) -> list[type]:
    return [type(evento) for evento in taller.publicador.publicar.call_args.args[0]]


def test_ca_047_corregir_guarda_y_publica_cotizacion_corregida(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller)
    taller.cotizacion.presentar(PresentarCotizacion(id_cotizacion))
    poner_hora(taller.reloj, AHORA + timedelta(hours=2))

    resultado = _corregir(taller, id_cotizacion, "800.00", "2000.00")

    cotizacion = taller.datos.cotizaciones[id_cotizacion]
    assert (resultado.id, resultado.version, resultado.total) == (id_cotizacion, "v.1", "2800.00")
    assert resultado.estado == "Pendiente de Autorización del Cliente"
    assert resultado.fecha_presentacion is None
    assert cotizacion.correcciones[0].registrada_en == AHORA + timedelta(hours=2)
    assert taller.datos.ordenes[numero].estado.value == "Cotizada"
    assert _eventos_publicados(taller) == [CotizacionCorregida]


def test_ca_048_correccion_arriba_de_15000_avisa_al_gerente(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller)

    resultado = _corregir(taller, id_cotizacion, "16000.00")

    assert resultado.estado == "Pendiente de Aprobación Gerencial"
    assert _eventos_publicados(taller) == [CotizacionCorregida, AprobacionGerencialRequerida]


def test_ca_048_aprobada_que_se_corrige_vuelve_a_revision(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller, importes=("20000.00",))
    taller.aprobacion.revisar(RevisarCotizacion(id_cotizacion, aprobada=True))

    resultado = _corregir(taller, id_cotizacion, "20500.00")

    assert resultado.estado == "Pendiente de Aprobación Gerencial"
    assert resultado.fecha_aprobacion_gerencial is None


def test_ca_050_ya_decidida_no_se_corrige_ni_publica(taller: Taller) -> None:
    _, id_cotizacion = autorizada(taller)
    taller.publicador.reset_mock()

    with pytest.raises(OperacionDeCotizacionNoPermitida):
        _corregir(taller, id_cotizacion, "100.00")

    taller.publicador.publicar.assert_not_called()


def test_ca_050_sin_motivo_no_cambia_nada(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller)

    with pytest.raises(ValorInvalido):
        _corregir(taller, id_cotizacion, "100.00", motivo=" ")

    assert str(taller.datos.cotizaciones[id_cotizacion].total.monto) == "3000.00"


def test_cotizacion_inexistente_no_se_corrige(taller: Taller) -> None:
    with pytest.raises(CotizacionNoEncontrada):
        _corregir(taller, "COT-9999", "100.00")


def test_ca_051_sin_alerta_hasta_volver_a_presentar(taller: Taller) -> None:
    _, id_cotizacion = cotizada(taller)
    taller.cotizacion.presentar(PresentarCotizacion(id_cotizacion))
    poner_hora(taller.reloj, AHORA + timedelta(hours=49))
    taller.cotizacion.registrar_recontacto(RegistrarRecontacto(id_cotizacion, ASESOR))
    _corregir(taller, id_cotizacion, "2500.00")

    poner_hora(taller.reloj, AHORA + timedelta(hours=200))
    sin_presentar = taller.revision.revisar()

    poner_hora(taller.reloj, AHORA + timedelta(hours=201))
    taller.cotizacion.presentar(PresentarCotizacion(id_cotizacion))
    poner_hora(taller.reloj, AHORA + timedelta(hours=250))
    presentada = taller.revision.revisar()

    assert sin_presentar.alertas_de_recontacto == 0
    assert presentada.alertas_de_recontacto == 1
    assert len(taller.datos.cotizaciones[id_cotizacion].recontactos) == 1
