"""Value Objects compartidos de modelo-de-dominio.md §3."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from domain.compartido.errores import ValorInvalido
from domain.compartido.valores import VIN, Dinero, NumeroOrden, Placas


def test_rn_23_dinero_rechaza_importe_negativo() -> None:
    with pytest.raises(ValorInvalido, match="negativo"):
        Dinero(Decimal("-1.00"))


def test_rn_23_dinero_rechaza_negativo_que_redondea_a_cero() -> None:
    with pytest.raises(ValorInvalido, match="negativo"):
        Dinero(Decimal("-0.001"))


@pytest.mark.parametrize(
    ("capturado", "esperado"),
    [
        ("10.005", "10.01"),
        ("10.004", "10.00"),
        ("2.675", "2.68"),
        ("1500", "1500.00"),
        ("1E+3", "1000.00"),
    ],
)
def test_rn_23_dinero_redondea_a_dos_decimales_half_up(capturado: str, esperado: str) -> None:
    assert str(Dinero(capturado).monto) == esperado


def test_rn_23_dinero_suma_con_decimal_sin_perder_centavos() -> None:
    assert Dinero("0.10") + Dinero("0.20") == Dinero("0.30")


def test_rn_23_dinero_multiplica_por_cantidad() -> None:
    assert Dinero("359.00").por(3) == Dinero("1077.00")


@pytest.mark.parametrize("monto", [10.5, True])
def test_rn_23_dinero_rechaza_float_y_bool(monto: float | bool) -> None:
    with pytest.raises(ValorInvalido):
        Dinero(monto)


@pytest.mark.parametrize("monto", ["abc", "", "NaN", "Infinity", "1e100", None])
def test_dinero_rechaza_texto_nan_infinito_y_valores_enormes(monto: str | None) -> None:
    with pytest.raises(ValorInvalido):
        Dinero(monto)


def test_dinero_acepta_el_maximo_y_rechaza_lo_que_lo_supera() -> None:
    assert Dinero("9999999999.99").monto == Decimal("9999999999.99")

    with pytest.raises(ValorInvalido, match="máximo"):
        Dinero("9999999999.995")


def test_dinero_cero_y_comparacion() -> None:
    assert Dinero.cero() == Dinero(0)
    assert Dinero("15000.01") > Dinero("15000.00")


def test_dinero_se_muestra_en_mxn() -> None:
    assert str(Dinero("1500")) == "$1,500.00 MXN"


def test_dinero_es_inmutable() -> None:
    with pytest.raises(FrozenInstanceError):
        Dinero("1.00").monto = Decimal("2.00")


def test_ca_037_numero_orden_coincide_sin_importar_mayusculas_ni_espacios() -> None:
    assert NumeroOrden(" aut-o007 ") == NumeroOrden("AUT-O007")
    assert str(NumeroOrden(" aut-o007 ")) == "AUT-O007"


@pytest.mark.parametrize("valor", ["", "   "])
def test_numero_orden_rechaza_vacio(valor: str) -> None:
    with pytest.raises(ValorInvalido):
        NumeroOrden(valor)


def test_ca_003_placas_con_otro_formato_identifican_al_mismo_vehiculo() -> None:
    assert Placas("abc-123") == Placas("ABC123")


def test_ca_037_placas_coinciden_sin_importar_el_formato() -> None:
    assert Placas(" abc 12-3 ") == Placas("ABC123")


@pytest.mark.parametrize("valor", ["", "   ", " - "])
def test_placas_rechaza_vacias(valor: str) -> None:
    with pytest.raises(ValorInvalido, match="vacías"):
        Placas(valor)


@pytest.mark.parametrize("valor", ["ABC*123", "ABC_123", "ABCÑ123"])
def test_placas_rechaza_simbolos(valor: str) -> None:
    with pytest.raises(ValorInvalido, match="letras"):
        Placas(valor)


def test_placas_acepta_15_caracteres_y_rechaza_16() -> None:
    assert str(Placas("A" * 15)) == "A" * 15

    with pytest.raises(ValorInvalido, match="15"):
        Placas("A" * 16)


def test_placas_del_profesor_se_normalizan() -> None:
    assert str(Placas("PIA-AUT-001")) == "PIAAUT001"


def test_vin_acepta_valor_valido_del_profesor() -> None:
    assert str(VIN("AUT00000000000001")) == "AUT00000000000001"


def test_vin_normaliza_minusculas_y_espacios() -> None:
    assert VIN(" aut00000000000001 ") == VIN("AUT00000000000001")


@pytest.mark.parametrize("valor", ["", "AUT0000000000000", "AUT000000000000001"])
def test_vin_rechaza_longitud_distinta_de_17(valor: str) -> None:
    with pytest.raises(ValorInvalido):
        VIN(valor)


@pytest.mark.parametrize("letra", ["I", "O", "Q"])
def test_vin_rechaza_i_o_q(letra: str) -> None:
    with pytest.raises(ValorInvalido):
        VIN(f"{letra}UT00000000000001")


@pytest.mark.parametrize("valor", ["AUT-0000000000001", "AUT 0000000000001", "AUT0000000000000\n1"])
def test_vin_rechaza_simbolos(valor: str) -> None:
    with pytest.raises(ValorInvalido):
        VIN(valor)
