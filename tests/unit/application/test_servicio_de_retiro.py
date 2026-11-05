"""ServicioDeRetiro (US-013)."""
from __future__ import annotations

from datetime import timedelta

import pytest

from application.comandos import (
    ConfirmarFirmaDeNota,
    ReactivarOrden,
    RegistrarLlegadaDeRefaccion,
    RegistrarSalida,
)
from domain.compartido.errores import TransicionDeEstadoNoPermitida
from domain.ordenes.eventos import OrdenReactivada, VehiculoRetirado
from tests.unit.application.escenarios import (
    AHORA,
    Taller,
    asignada,
    en_espera,
    pausada,
    poner_hora,
)


def test_ca_024_salida_genera_nota(taller: Taller) -> None:
    numero = en_espera(taller)

    resultado = taller.retiro.registrar_salida(RegistrarSalida(numero))

    assert resultado.fecha_salida == AHORA
    assert resultado.firmada is False
    assert resultado.estado == "En Espera de Refacción"
    assert taller.datos.ordenes[numero].nota_de_responsabilidad.firmada is False


def test_ca_024_firma_pausa_y_saca_de_la_fila(taller: Taller) -> None:
    numero = en_espera(taller)
    taller.retiro.registrar_salida(RegistrarSalida(numero))

    resultado = taller.retiro.confirmar_firma(ConfirmarFirmaDeNota(numero))

    orden = taller.datos.ordenes[numero]
    assert resultado.estado == "Pausada por Retiro de Vehículo"
    assert orden.fecha_ingreso_a_fila is None
    assert orden.nota_de_responsabilidad.firmada is True
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [VehiculoRetirado]


def test_ca_024_salida_solo_en_espera_de_refaccion(taller: Taller) -> None:
    numero = asignada(taller)

    with pytest.raises(TransicionDeEstadoNoPermitida, match="En Espera de Refacción"):
        taller.retiro.registrar_salida(RegistrarSalida(numero))


def test_rn_13_firma_sin_salida_se_rechaza(taller: Taller) -> None:
    numero = en_espera(taller)

    with pytest.raises(TransicionDeEstadoNoPermitida, match="registrarse la salida"):
        taller.retiro.confirmar_firma(ConfirmarFirmaDeNota(numero))

    assert taller.datos.ordenes[numero].estado.value == "En Espera de Refacción"


def test_ca_025_reactiva_al_final_de_la_fila(taller: Taller) -> None:
    numero = pausada(taller)
    taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))
    regreso = AHORA + timedelta(days=5)
    poner_hora(taller.reloj, regreso)

    resultado = taller.retiro.reactivar(ReactivarOrden(numero))

    assert resultado.estado == "Autorizada"
    assert taller.datos.ordenes[numero].fecha_ingreso_a_fila == regreso
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [OrdenReactivada]


def test_ca_025_reactiva_en_espera_si_faltan_piezas(taller: Taller) -> None:
    numero = pausada(taller)

    resultado = taller.retiro.reactivar(ReactivarOrden(numero))

    assert resultado.estado == "En Espera de Refacción"


def test_ca_025_reactiva_en_reparacion_con_trabajo_iniciado(taller: Taller) -> None:
    numero = pausada(taller, iniciada=True)
    taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))

    resultado = taller.retiro.reactivar(ReactivarOrden(numero))

    assert resultado.estado == "En Reparación"


def test_ca_025_solo_se_reactiva_una_orden_pausada(taller: Taller) -> None:
    numero = en_espera(taller)

    with pytest.raises(TransicionDeEstadoNoPermitida, match="Pausada por Retiro"):
        taller.retiro.reactivar(ReactivarOrden(numero))
