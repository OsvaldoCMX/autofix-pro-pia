"""Aggregate Empleado (modelo-de-dominio.md §2.5)."""
from __future__ import annotations

import pytest

from domain.compartido.errores import ValorInvalido
from domain.empleados.empleado import Empleado, RolDeEmpleado
from tests.unit.domain.apoyo_esquema import valores_del_check


def test_rn_01_empleado_asesor_tiene_su_rol() -> None:
    asesor = Empleado("EMP-001", "Laura Méndez", RolDeEmpleado.ASESOR)

    assert asesor.tiene_rol(RolDeEmpleado.ASESOR)
    assert not asesor.tiene_rol(RolDeEmpleado.TECNICO)


def test_ca_035_empleado_tecnico_tiene_su_rol() -> None:
    tecnico = Empleado("EMP-002", "Carlos Ruiz", RolDeEmpleado.TECNICO)

    assert tecnico.tiene_rol(RolDeEmpleado.TECNICO)


@pytest.mark.parametrize("rol", [None, "Asesor", ("Asesor", "Caja")])
def test_empleado_exige_exactamente_un_rol(rol: object) -> None:
    with pytest.raises(ValorInvalido, match="rol"):
        Empleado("EMP-009", "Sin Rol", rol)  # type: ignore[arg-type]


def test_empleado_exige_nombre() -> None:
    with pytest.raises(ValorInvalido, match="nombre"):
        Empleado("EMP-009", "  ", RolDeEmpleado.CAJA)


def test_roles_coinciden_con_la_base() -> None:
    assert {rol.value for rol in RolDeEmpleado} == valores_del_check("empleados", "rol")
