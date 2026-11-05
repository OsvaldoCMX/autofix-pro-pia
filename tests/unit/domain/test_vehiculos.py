"""Aggregate Vehículo (modelo-de-dominio.md §2.4)."""
from __future__ import annotations

import pytest

from domain.compartido.errores import ValorInvalido
from domain.compartido.valores import VIN, Placas
from domain.vehiculos.vehiculo import Vehiculo

VIN_VALIDO = "1HGCM82633A004352"


def _vehiculo(anio: int = 2020, marca: str = "Nissan", modelo: str = "Versa") -> Vehiculo:
    return Vehiculo(Placas("ABC-123"), VIN(VIN_VALIDO), marca, modelo, anio, "CLI-1")


def test_ca_001_vehiculo_guarda_sus_datos() -> None:
    vehiculo = _vehiculo()

    assert vehiculo.placas == Placas("ABC123")
    assert vehiculo.vin == VIN(VIN_VALIDO)
    assert (vehiculo.marca, vehiculo.modelo, vehiculo.anio) == ("Nissan", "Versa", 2020)
    assert vehiculo.id_cliente == "CLI-1"


@pytest.mark.parametrize(
    ("placas", "vin"), [("", VIN_VALIDO), ("ABC123", ""), ("ABC123", "CORTO")]
)
def test_ca_001_vehiculo_exige_placas_y_vin(placas: str, vin: str) -> None:
    with pytest.raises(ValorInvalido):
        Vehiculo(Placas(placas), VIN(vin), "Nissan", "Versa", 2020, "CLI-1")


@pytest.mark.parametrize(("marca", "modelo"), [(" ", "Versa"), ("Nissan", " ")])
def test_ca_001_vehiculo_exige_marca_y_modelo(marca: str, modelo: str) -> None:
    with pytest.raises(ValorInvalido):
        _vehiculo(marca=marca, modelo=modelo)


def test_ca_003_placas_se_normalizan_para_buscar() -> None:
    assert _vehiculo().placas == Placas(" abc 123 ")


def test_ca_003_vehiculo_actualiza_datos() -> None:
    vehiculo = _vehiculo()
    nuevo_vin = VIN("2HGCM82633A004353")

    vehiculo.actualizar_datos(nuevo_vin, "Toyota", "Yaris", 2021)

    assert vehiculo.vin == nuevo_vin
    assert (vehiculo.marca, vehiculo.modelo, vehiculo.anio) == ("Toyota", "Yaris", 2021)
    assert vehiculo.placas == Placas("ABC123")


def test_ca_003_actualizacion_invalida_no_cambia_nada() -> None:
    vehiculo = _vehiculo()

    with pytest.raises(ValorInvalido, match="año"):
        vehiculo.actualizar_datos(VIN(VIN_VALIDO), "Toyota", "Yaris", 1800)

    assert (vehiculo.marca, vehiculo.anio) == ("Nissan", 2020)


@pytest.mark.parametrize("anio", [1900, 2100])
def test_anio_acepta_los_limites_de_la_base(anio: int) -> None:
    assert _vehiculo(anio=anio).anio == anio


@pytest.mark.parametrize("anio", [1899, 2101, 999, 20200])
def test_anio_rechaza_valores_fuera_del_rango(anio: int) -> None:
    with pytest.raises(ValorInvalido, match="año"):
        _vehiculo(anio=anio)
