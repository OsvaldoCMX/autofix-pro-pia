"""Interfaces de repositorio del dominio (modelo-de-dominio.md §2)."""
from __future__ import annotations

from abc import ABC

import pytest

from domain.clientes.repositorio import RepositorioDeClientes
from domain.cotizaciones.repositorio import RepositorioDeCotizaciones
from domain.empleados.repositorio import RepositorioDeEmpleados
from domain.ordenes.repositorio import RepositorioDeOrdenes
from domain.vehiculos.repositorio import RepositorioDeVehiculos


@pytest.mark.parametrize(
    ("interfaz", "metodos"),
    [
        (
            RepositorioDeOrdenes,
            {"obtener", "agregar", "guardar", "siguiente_numero", "abierta_del_vehiculo"},
        ),
        (
            RepositorioDeCotizaciones,
            {"obtener", "agregar", "guardar", "de_la_orden", "siguiente_version", "siguiente_id"},
        ),
        (RepositorioDeClientes, {"obtener", "agregar", "guardar", "buscar_flotilla", "siguiente_id"}),
        (RepositorioDeVehiculos, {"por_placas", "agregar", "guardar"}),
        (RepositorioDeEmpleados, {"obtener"}),
    ],
)
def test_interfaz_declara_los_metodos_del_modelo(interfaz: type[ABC], metodos: set[str]) -> None:
    assert interfaz.__abstractmethods__ == metodos
    with pytest.raises(TypeError):
        interfaz()
