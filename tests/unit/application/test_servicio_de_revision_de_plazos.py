"""ServicioDeRevisionDePlazos con reloj falso: E7, E8 e idempotencia (ADR-015)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from application.comandos import (
    PresentarCotizacion,
    RegistrarAvisoAlCliente,
    RegistrarLlegadaDeRefaccion,
    RegistrarRecontacto,
)
from tests.unit.application.escenarios import (
    AHORA,
    ASESOR,
    Taller,
    cotizada,
    decidir,
    en_espera,
    pausada,
    poner_hora,
)

# Mediodía en Monterrey (UTC-6) de cada día de octubre de 2026; el 5 es lunes.
LUNES_5 = datetime(2026, 10, 5, 18, 0, tzinfo=UTC)
JUEVES_8 = LUNES_5 + timedelta(days=3)
VIERNES_9 = LUNES_5 + timedelta(days=4)
MARTES_13 = LUNES_5 + timedelta(days=8)
MIERCOLES_14 = LUNES_5 + timedelta(days=9)


def _alertas(taller: Taller, tipo: str) -> list:
    return [alerta for alerta in taller.datos.alertas if alerta.tipo == tipo]


def _presentada(taller: Taller) -> tuple[str, str]:
    numero, id_cotizacion = cotizada(taller)
    poner_hora(taller.reloj, AHORA)
    taller.cotizacion.presentar(PresentarCotizacion(id_cotizacion))
    return numero, id_cotizacion


def _revisar_en(taller: Taller, fecha: datetime) -> tuple[int, int]:
    poner_hora(taller.reloj, fecha)
    resultado = taller.revision.revisar()
    return resultado.alertas_de_refaccion, resultado.alertas_de_recontacto


# ------------------------------------------------------------------ E7: refacciones
def test_ca_023_alerta_al_asesor_tras_3_dias_habiles(taller: Taller) -> None:
    poner_hora(taller.reloj, LUNES_5)
    numero = en_espera(taller)

    assert _revisar_en(taller, VIERNES_9) == (1, 0)

    alerta = _alertas(taller, "RefaccionRetrasada")[0]
    assert alerta.destinatario == ASESOR
    assert alerta.numero_orden == numero
    assert alerta.clave == f"refaccion:{numero}:1"
    assert "Balatas" in alerta.mensaje


def test_rn_11_con_3_dias_exactos_no_alerta(taller: Taller) -> None:
    poner_hora(taller.reloj, LUNES_5)
    en_espera(taller)

    assert _revisar_en(taller, JUEVES_8) == (0, 0)
    assert taller.datos.alertas == []


def test_rn_11_fin_de_semana_no_cuenta(taller: Taller) -> None:
    poner_hora(taller.reloj, JUEVES_8)
    en_espera(taller)

    assert _revisar_en(taller, MARTES_13) == (0, 0)
    assert _revisar_en(taller, MIERCOLES_14) == (1, 0)


def test_rn_11_cuenta_los_dias_en_la_zona_del_taller(taller: Taller) -> None:
    # 20:00 del lunes en Monterrey: en UTC ya es martes, pero el plazo cuenta desde el lunes.
    poner_hora(taller.reloj, datetime(2026, 10, 6, 2, 0, tzinfo=UTC))
    en_espera(taller)

    assert _revisar_en(taller, VIERNES_9) == (1, 0)


def test_ca_023_revision_repetida_no_duplica(taller: Taller) -> None:
    poner_hora(taller.reloj, LUNES_5)
    en_espera(taller)

    assert _revisar_en(taller, VIERNES_9) == (1, 0)
    assert _revisar_en(taller, VIERNES_9) == (0, 0)
    assert _revisar_en(taller, MARTES_13) == (0, 0)
    assert len(_alertas(taller, "RefaccionRetrasada")) == 1


def test_ca_023_no_alerta_tras_el_aviso(taller: Taller) -> None:
    poner_hora(taller.reloj, LUNES_5)
    numero = en_espera(taller)
    taller.refacciones.registrar_aviso_al_cliente(RegistrarAvisoAlCliente(numero, 1))

    assert _revisar_en(taller, VIERNES_9) == (0, 0)


def test_rn_11_refaccion_que_ya_llego_no_alerta(taller: Taller) -> None:
    poner_hora(taller.reloj, LUNES_5)
    numero = en_espera(taller)
    taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))

    assert _revisar_en(taller, VIERNES_9) == (0, 0)


def test_rn_11_cada_solicitud_retrasada_tiene_su_alerta(taller: Taller) -> None:
    poner_hora(taller.reloj, LUNES_5)
    en_espera(taller)
    pausada(taller)

    assert _revisar_en(taller, VIERNES_9) == (2, 0)


# ------------------------------------------------------------------ E8: cotizaciones
def test_ca_040_alerta_tras_48_horas(taller: Taller) -> None:
    numero, id_cotizacion = _presentada(taller)

    assert _revisar_en(taller, AHORA + timedelta(hours=48, minutes=1)) == (0, 1)

    alerta = _alertas(taller, "CotizacionSinRespuesta")[0]
    assert alerta.destinatario == ASESOR
    assert (alerta.numero_orden, alerta.id_cotizacion) == (numero, id_cotizacion)
    assert "48 horas" in alerta.mensaje


def test_rn_12_con_48_horas_exactas_no_alerta(taller: Taller) -> None:
    _presentada(taller)

    assert _revisar_en(taller, AHORA + timedelta(hours=48)) == (0, 0)


def test_rn_12_cotizacion_sin_presentar_no_alerta(taller: Taller) -> None:
    cotizada(taller)

    assert _revisar_en(taller, AHORA + timedelta(days=30)) == (0, 0)


def test_rn_12_cotizacion_decidida_no_alerta(taller: Taller) -> None:
    _, id_cotizacion = _presentada(taller)
    decidir(taller, id_cotizacion, (1, 2))

    assert _revisar_en(taller, AHORA + timedelta(days=30)) == (0, 0)


def test_ca_040_revision_repetida_no_duplica(taller: Taller) -> None:
    _presentada(taller)
    despues = AHORA + timedelta(hours=49)

    assert _revisar_en(taller, despues) == (0, 1)
    assert _revisar_en(taller, despues) == (0, 0)
    assert _revisar_en(taller, despues + timedelta(hours=72)) == (0, 0)


def test_ca_040_recontacto_abre_un_nuevo_periodo(taller: Taller) -> None:
    _, id_cotizacion = _presentada(taller)
    recontacto = AHORA + timedelta(hours=49)
    assert _revisar_en(taller, recontacto) == (0, 1)
    taller.cotizacion.registrar_recontacto(RegistrarRecontacto(id_cotizacion, ASESOR))

    assert _revisar_en(taller, recontacto + timedelta(hours=48)) == (0, 0)
    assert _revisar_en(taller, recontacto + timedelta(hours=49)) == (0, 1)
    assert len(_alertas(taller, "CotizacionSinRespuesta")) == 2


def test_revision_no_cambia_estados_ni_escribe_bitacora(taller: Taller) -> None:
    poner_hora(taller.reloj, LUNES_5)
    numero = en_espera(taller)
    registros = len(taller.datos.bitacora)

    _revisar_en(taller, VIERNES_9)

    assert taller.datos.ordenes[numero].estado.value == "En Espera de Refacción"
    assert len(taller.datos.bitacora) == registros
