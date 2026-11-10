"""RN-27: un vehículo tiene a lo más una orden abierta (H-PIA-22)."""
from __future__ import annotations

import pytest

from domain.compartido.errores import VehiculoConOrdenAbierta
from domain.compartido.valores import Placas
from domain.ordenes.estados import ESTADOS_DE_ORDEN_CERRADA, EstadoOrden, esta_abierta
from domain.servicios.verificador_de_orden_unica import VerificadorDeOrdenUnica
from tests.unit.domain.constructores import autorizada, recibida

PLACAS = Placas("ABC-123")


def test_rn_27_sin_orden_abierta_se_puede_registrar() -> None:
    VerificadorDeOrdenUnica().verificar(PLACAS, None)


def test_rn_27_con_orden_abierta_dice_el_folio_y_el_estado() -> None:
    orden = autorizada()

    with pytest.raises(VehiculoConOrdenAbierta) as error:
        VerificadorDeOrdenUnica().verificar(PLACAS, orden)

    assert str(error.value) == (
        f"El vehículo con placas ABC123 ya tiene abierta la orden {orden.numero} "
        "(estado «Autorizada»). Ábrala en lugar de registrar otra."
    )


@pytest.mark.parametrize("estado", list(EstadoOrden))
def test_rn_27_orden_abierta_es_cualquier_estado_que_no_este_cerrado(estado: EstadoOrden) -> None:
    cerrados = {EstadoOrden.CERRADA, EstadoOrden.CERRADA_SIN_REPARACION, EstadoOrden.CANCELADA}

    assert esta_abierta(estado) is (estado not in cerrados)
    assert ESTADOS_DE_ORDEN_CERRADA == cerrados


def test_rn_27_la_orden_recibida_esta_abierta() -> None:
    assert esta_abierta(recibida().estado)
