"""Aggregate Cliente (modelo-de-dominio.md §2.3)."""
from __future__ import annotations

import pytest

from domain.clientes.cliente import Cliente, ResponsableDeFlotilla, TipoCliente
from domain.compartido.errores import ValorInvalido
from tests.unit.domain.apoyo_esquema import valores_del_check

RESPONSABLE = ResponsableDeFlotilla("Ana Torres", "81-1111-2222", "ana@empresa.test")


def test_ca_028_registra_flotilla_con_responsable() -> None:
    cliente = Cliente(
        "CLI-1", "Transportes Norte", TipoCliente.FLOTILLA, empresa="Norte", responsable=RESPONSABLE
    )

    assert cliente.es_de_flotilla
    assert cliente.empresa == "Norte"
    assert cliente.responsable == RESPONSABLE


@pytest.mark.parametrize(
    ("empresa", "responsable"),
    [(None, RESPONSABLE), ("", RESPONSABLE), ("   ", RESPONSABLE), ("Norte", None)],
)
def test_ca_028_flotilla_exige_empresa_y_responsable(
    empresa: str | None, responsable: ResponsableDeFlotilla | None
) -> None:
    with pytest.raises(ValorInvalido, match="Responsable de Flotilla"):
        Cliente(
            "CLI-1", "Transportes", TipoCliente.FLOTILLA, empresa=empresa, responsable=responsable
        )


@pytest.mark.parametrize(
    ("nombre", "telefono", "correo", "falta"),
    [
        (" ", "81-1", "a@b.test", "nombre"),
        ("Ana", " ", "a@b.test", "teléfono"),
        ("Ana", "81-1", " ", "correo"),
    ],
)
def test_ca_028_responsable_exige_nombre_telefono_y_correo(
    nombre: str, telefono: str, correo: str, falta: str
) -> None:
    with pytest.raises(ValorInvalido, match=falta):
        ResponsableDeFlotilla(nombre, telefono, correo)


def test_rn_07_particular_no_tiene_responsable() -> None:
    cliente = Cliente("CLI-2", "Luis Peña", TipoCliente.PARTICULAR, "81-2", "luis@correo.test")

    assert not cliente.es_de_flotilla
    assert cliente.responsable is None
    assert cliente.empresa is None


def test_ca_001_cliente_exige_nombre() -> None:
    with pytest.raises(ValorInvalido, match="nombre"):
        Cliente("CLI-3", "  ", TipoCliente.PARTICULAR)


def test_ca_003_cliente_actualiza_contacto() -> None:
    cliente = Cliente("CLI-4", "Luis Peña", TipoCliente.PARTICULAR, "81-2", "luis@correo.test")

    cliente.actualizar_contacto("Luis Peña Ruiz", "81-9", "nuevo@correo.test")

    assert (cliente.nombre, cliente.telefono, cliente.correo) == (
        "Luis Peña Ruiz",
        "81-9",
        "nuevo@correo.test",
    )


def test_ca_003_actualizacion_invalida_no_cambia_nada() -> None:
    cliente = Cliente("CLI-5", "Luis Peña", TipoCliente.PARTICULAR, "81-2", "luis@correo.test")

    with pytest.raises(ValorInvalido, match="nombre"):
        cliente.actualizar_contacto("  ", "81-9", "nuevo@correo.test")

    assert (cliente.nombre, cliente.telefono) == ("Luis Peña", "81-2")


def test_tipo_de_cliente_coincide_con_la_base() -> None:
    assert {tipo.value for tipo in TipoCliente} == valores_del_check("clientes", "tipo")
