"""Errores del dominio de modelo-de-dominio.md §7."""
from __future__ import annotations

import pytest

from domain.compartido import errores
from domain.compartido.errores import ErrorDeDominio, ValorInvalido

ERRORES_DEL_MODELO = [
    "ValorInvalido",
    "CotizacionSinTrabajos",
    "TransicionDeEstadoNoPermitida",
    "OperacionDeCotizacionNoPermitida",
    "DiagnosticoRequerido",
    "DiagnosticoNoModificable",
    "AutorizanteNoValido",
    "TrabajoNoAutorizado",
    "SolicitudNoPermitida",
    "TrabajoNoPermitido",
    "TrabajoDeOtroTecnico",
    "PagoNoPermitido",
    "EntregaNoPermitida",
    "CancelacionNoPermitida",
    "OrdenNoEncontrada",
    "CotizacionNoEncontrada",
    "ClienteNoEncontrado",
    "VehiculoNoEncontrado",
    "EmpleadoNoEncontrado",
    "TrabajoNoEncontrado",
    "SolicitudNoEncontrada",
]


@pytest.mark.parametrize("nombre", ERRORES_DEL_MODELO)
def test_todos_los_errores_heredan_de_error_de_dominio(nombre: str) -> None:
    assert issubclass(getattr(errores, nombre), ErrorDeDominio)


@pytest.mark.parametrize("nombre", ERRORES_DEL_MODELO)
def test_cada_error_tiene_mensaje_por_defecto(nombre: str) -> None:
    clase = getattr(errores, nombre)

    assert clase.mensaje_por_defecto != ErrorDeDominio.mensaje_por_defecto
    assert str(clase()) == clase.mensaje_por_defecto


def test_el_mensaje_especifico_reemplaza_al_de_por_defecto() -> None:
    assert str(ValorInvalido("El kilometraje no puede ser negativo.")) == (
        "El kilometraje no puede ser negativo."
    )
