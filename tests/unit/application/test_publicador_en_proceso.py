"""Publicador en proceso (ADR-016)."""
from __future__ import annotations

import logging
from unittest.mock import Mock

import pytest

from domain.ordenes.eventos import OrdenListaParaEntrega, VehiculoRetirado
from infrastructure.eventos.publicador_en_proceso import PublicadorEnProceso
from tests.unit.application.escenarios import AHORA, ASESOR

LISTA = OrdenListaParaEntrega(AHORA, "OS-0001", ASESOR)


def test_entrega_a_los_suscritos() -> None:
    publicador = PublicadorEnProceso()
    manejador, otro = Mock(), Mock()
    publicador.suscribir(OrdenListaParaEntrega, manejador)
    publicador.suscribir(VehiculoRetirado, otro)

    publicador.publicar([LISTA])

    manejador.assert_called_once_with(LISTA)
    otro.assert_not_called()


def test_manejador_que_falla_no_detiene_a_los_demas(caplog: pytest.LogCaptureFixture) -> None:
    publicador = PublicadorEnProceso()
    siguiente = Mock()
    publicador.suscribir(OrdenListaParaEntrega, Mock(side_effect=RuntimeError("falla")))
    publicador.suscribir(OrdenListaParaEntrega, siguiente)

    with caplog.at_level(logging.ERROR):
        publicador.publicar([LISTA])

    siguiente.assert_called_once_with(LISTA)
    assert "OrdenListaParaEntrega" in caplog.text


def test_evento_sin_suscritos_no_hace_nada() -> None:
    PublicadorEnProceso().publicar([LISTA])
