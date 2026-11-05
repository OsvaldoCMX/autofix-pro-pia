"""Clase genérica MaquinaDeEstados (ADR-007). Las 4 tablas reales se prueban en la Fase 2."""
from __future__ import annotations

from enum import Enum
from itertools import product

import pytest

from domain.compartido.errores import TransicionDeEstadoNoPermitida
from domain.compartido.maquina_de_estados import MaquinaDeEstados


class _Estado(Enum):
    RECIBIDA = "Recibida"
    EN_DIAGNOSTICO = "En Diagnóstico"
    AUTORIZADA = "Autorizada"
    CANCELADA = "Cancelada"


TRANSICIONES = {
    _Estado.RECIBIDA: {_Estado.EN_DIAGNOSTICO, _Estado.CANCELADA},
    _Estado.EN_DIAGNOSTICO: {_Estado.AUTORIZADA, _Estado.CANCELADA},
}
PERMITIDAS = {(desde, hacia) for desde, destinos in TRANSICIONES.items() for hacia in destinos}


@pytest.fixture
def maquina() -> MaquinaDeEstados[_Estado]:
    return MaquinaDeEstados("La orden", TRANSICIONES, finales={_Estado.CANCELADA})


def test_rn_22_permite_transicion_de_la_tabla(maquina: MaquinaDeEstados[_Estado]) -> None:
    maquina.validar(_Estado.RECIBIDA, _Estado.EN_DIAGNOSTICO)


def test_rn_22_rechaza_saltar_estado(maquina: MaquinaDeEstados[_Estado]) -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida):
        maquina.validar(_Estado.RECIBIDA, _Estado.AUTORIZADA)


def test_rn_22_rechaza_salir_de_estado_final(maquina: MaquinaDeEstados[_Estado]) -> None:
    assert maquina.es_final(_Estado.CANCELADA)
    assert not maquina.es_final(_Estado.RECIBIDA)

    with pytest.raises(TransicionDeEstadoNoPermitida):
        maquina.validar(_Estado.CANCELADA, _Estado.RECIBIDA)


def test_rn_22_rechaza_quedarse_en_el_mismo_estado(maquina: MaquinaDeEstados[_Estado]) -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida):
        maquina.validar(_Estado.RECIBIDA, _Estado.RECIBIDA)


@pytest.mark.parametrize(("actual", "nuevo"), list(product(_Estado, repeat=2)))
def test_rn_22_recorre_todas_las_parejas_de_estados(
    maquina: MaquinaDeEstados[_Estado], actual: _Estado, nuevo: _Estado
) -> None:
    assert maquina.permite(actual, nuevo) is ((actual, nuevo) in PERMITIDAS)


def test_rn_22_mensaje_nombra_el_objeto_y_los_estados(
    maquina: MaquinaDeEstados[_Estado],
) -> None:
    with pytest.raises(TransicionDeEstadoNoPermitida) as error:
        maquina.validar(_Estado.RECIBIDA, _Estado.AUTORIZADA)

    assert str(error.value) == "La orden no puede pasar de «Recibida» a «Autorizada»"


def test_estado_final_con_destinos_es_error_de_configuracion() -> None:
    with pytest.raises(ValueError, match="Recibida"):
        MaquinaDeEstados("La orden", TRANSICIONES, finales={_Estado.RECIBIDA})


def test_la_tabla_no_cambia_si_se_modifica_la_original() -> None:
    destinos = {_Estado.EN_DIAGNOSTICO}
    tabla = {_Estado.RECIBIDA: destinos}
    maquina = MaquinaDeEstados("La orden", tabla, finales=set())

    destinos.add(_Estado.AUTORIZADA)
    tabla[_Estado.AUTORIZADA] = {_Estado.CANCELADA}

    assert not maquina.permite(_Estado.RECIBIDA, _Estado.AUTORIZADA)
    assert not maquina.permite(_Estado.AUTORIZADA, _Estado.CANCELADA)
