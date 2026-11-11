"""E2 `AutorizanteValido` y `VerificadorDeAutorizante` (modelo-de-dominio.md §4)."""
from __future__ import annotations

import pytest

from domain.clientes.cliente import Cliente, ResponsableDeFlotilla, TipoCliente
from domain.clientes.especificaciones import (
    AutorizaElCliente,
    AutorizanteValido,
    AutorizaSuResponsableDeFlotilla,
    EsClienteDeFlotilla,
    EsClienteParticular,
)
from domain.compartido.errores import AutorizanteNoValido
from domain.cotizaciones.valores import Autorizante, RolDeAutorizante
from domain.servicios.verificador_de_autorizante import VerificadorDeAutorizante

_CLIENTE = RolDeAutorizante.CLIENTE
_RESPONSABLE = RolDeAutorizante.RESPONSABLE_DE_FLOTILLA

PARTICULAR = Cliente("CLI-1", "Luis Peña", TipoCliente.PARTICULAR)
FLOTILLA = Cliente(
    "CLI-2",
    "Transportes Norte",
    TipoCliente.FLOTILLA,
    empresa="Norte",
    responsable=ResponsableDeFlotilla("Ana Torres", "81-1", "ana@norte.test"),
)


def test_ca_010_particular_autoriza_a_su_nombre() -> None:
    VerificadorDeAutorizante().verificar(PARTICULAR, Autorizante("Luis Peña", _CLIENTE))


def test_ca_010_el_nombre_no_distingue_mayusculas() -> None:
    VerificadorDeAutorizante().verificar(PARTICULAR, Autorizante(" LUIS PEÑA ", _CLIENTE))


def test_rn_07_particular_con_otro_nombre_se_rechaza() -> None:
    with pytest.raises(AutorizanteNoValido, match="Luis Peña"):
        VerificadorDeAutorizante().verificar(PARTICULAR, Autorizante("Juan Ruiz", _CLIENTE))


def test_rn_07_particular_no_autoriza_como_responsable() -> None:
    with pytest.raises(AutorizanteNoValido):
        VerificadorDeAutorizante().verificar(PARTICULAR, Autorizante("Luis Peña", _RESPONSABLE))


def test_ca_029_responsable_de_flotilla_autoriza() -> None:
    VerificadorDeAutorizante().verificar(FLOTILLA, Autorizante("ana torres", _RESPONSABLE))


def test_ca_029_conductor_no_autoriza() -> None:
    # CA-064 cambió el texto: ahora dice a nombre de quién y con qué rol (H-PIA-27).
    with pytest.raises(AutorizanteNoValido, match="a nombre de su Responsable de Flotilla, Ana"):
        VerificadorDeAutorizante().verificar(FLOTILLA, Autorizante("Pedro Conductor", _RESPONSABLE))


def test_ca_029_flotilla_no_autoriza_con_rol_de_cliente() -> None:
    with pytest.raises(AutorizanteNoValido, match="Norte"):
        VerificadorDeAutorizante().verificar(FLOTILLA, Autorizante("Ana Torres", _CLIENTE))


def test_ca_017_adicional_exige_el_mismo_autorizante() -> None:
    """La regla no depende del tipo de cotización: la adicional se verifica igual (RN-07)."""
    verificador = VerificadorDeAutorizante()

    verificador.verificar(FLOTILLA, Autorizante("Ana Torres", _RESPONSABLE))
    with pytest.raises(AutorizanteNoValido):
        verificador.verificar(FLOTILLA, Autorizante("Otra Persona", _RESPONSABLE))


@pytest.mark.parametrize(
    ("cliente", "nombre", "rol", "esperado"),
    [
        (PARTICULAR, "Luis Peña", _CLIENTE, True),
        (PARTICULAR, "Otra Persona", _CLIENTE, False),
        (PARTICULAR, "Luis Peña", _RESPONSABLE, False),
        (FLOTILLA, "Ana Torres", _RESPONSABLE, True),
        (FLOTILLA, "Otra Persona", _RESPONSABLE, False),
        (FLOTILLA, "Ana Torres", _CLIENTE, False),
        (FLOTILLA, "Transportes Norte", _CLIENTE, False),
    ],
)
def test_rn_07_e2_tabla_de_verdad(
    cliente: Cliente, nombre: str, rol: RolDeAutorizante, esperado: bool
) -> None:
    assert AutorizanteValido().es_satisfecha_por((cliente, Autorizante(nombre, rol))) is esperado


def test_rn_07_e2_cada_pieza_se_evalua_por_separado() -> None:
    del_cliente = (PARTICULAR, Autorizante("Luis Peña", _CLIENTE))
    del_responsable = (FLOTILLA, Autorizante("Ana Torres", _RESPONSABLE))

    assert EsClienteParticular().es_satisfecha_por(del_cliente)
    assert not EsClienteParticular().es_satisfecha_por(del_responsable)
    assert EsClienteDeFlotilla().es_satisfecha_por(del_responsable)
    assert not EsClienteDeFlotilla().es_satisfecha_por(del_cliente)
    assert AutorizaElCliente().es_satisfecha_por(del_cliente)
    assert not AutorizaElCliente().es_satisfecha_por(del_responsable)
    assert AutorizaSuResponsableDeFlotilla().es_satisfecha_por(del_responsable)
    assert not AutorizaSuResponsableDeFlotilla().es_satisfecha_por(del_cliente)


# ------------------------------------------------------------------ H-PIA-27
@pytest.mark.parametrize("nombre", ["Luis  Peña", " luis peña ", "LUIS PEÑA", "Luis\tPeña"])
def test_ca_063_espacios_de_mas_y_mayusculas_no_cuentan(nombre: str) -> None:
    VerificadorDeAutorizante().verificar(
        PARTICULAR, Autorizante(nombre, RolDeAutorizante.CLIENTE)
    )


def test_ca_063_sin_acento_se_rechaza_y_dice_a_nombre_de_quien() -> None:
    with pytest.raises(AutorizanteNoValido, match="a nombre del cliente Luis Peña"):
        VerificadorDeAutorizante().verificar(
            PARTICULAR, Autorizante("Luis Pena", RolDeAutorizante.CLIENTE)
        )


@pytest.mark.parametrize(
    ("nombre", "rol"),
    [("Ana Torres", RolDeAutorizante.CLIENTE), ("Pedro Conductor", RolDeAutorizante.CLIENTE)],
)
def test_ca_064_flotilla_dice_el_responsable_y_el_rol(nombre: str, rol: RolDeAutorizante) -> None:
    with pytest.raises(AutorizanteNoValido) as error:
        VerificadorDeAutorizante().verificar(FLOTILLA, Autorizante(nombre, rol))

    assert str(error.value) == (
        "Para la flotilla de Norte, registre la decisión a nombre de su Responsable "
        "de Flotilla, Ana Torres, con el rol «Responsable de Flotilla»."
    )
