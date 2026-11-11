"""`GET /api/sesion`: la página pregunta quién es el empleado de la clave (ADR-017, Fase 15)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.api.pasos import ASESOR, CAJA, COMPRAS, GERENTE, OTRO_TECNICO, SISTEMA, TECNICO

CLAVE_NO_VALIDA = {
    "error": "TokenInvalido",
    "detalle": (
        "No pudimos identificarlo: falta su clave de acceso o no es válida. "
        "Revísela e intente de nuevo."
    ),
    "codigo": 401,
}


@pytest.mark.parametrize(
    ("encabezados", "esperado"),
    [
        (ASESOR, ("EMP-001", "Laura Méndez", "Asesor", "Asesor de Servicio")),
        (TECNICO, ("EMP-002", "Carlos Ruiz", "Técnico", "Técnico")),
        (OTRO_TECNICO, ("EMP-003", "Diego Salinas", "Técnico", "Técnico")),
        (GERENTE, ("EMP-004", "Patricia Garza", "Gerente", "Gerente de Taller")),
        (COMPRAS, ("EMP-005", "Jorge Treviño", "Compras", "Personal de Compras")),
        (CAJA, ("EMP-006", "Sofía Leal", "Caja", "Personal de Caja")),
    ],
    ids=["asesor", "tecnico", "otro_tecnico", "gerente", "compras", "caja"],
)
def test_cada_empleado_recibe_su_nombre_y_su_puesto(
    cliente: TestClient, encabezados: dict[str, str], esperado: tuple[str, str, str, str]
) -> None:
    respuesta = cliente.get("/api/sesion", headers=encabezados)

    assert respuesta.status_code == 200
    id_empleado, nombre, rol, puesto = esperado
    assert respuesta.json() == {
        "id_empleado": id_empleado,
        "nombre": nombre,
        "rol": rol,
        "puesto": puesto,
    }


def test_sin_clave_responde_401_con_mensaje_claro(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/sesion")

    assert respuesta.status_code == 401
    assert respuesta.json() == CLAVE_NO_VALIDA
    assert respuesta.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "clave",
    ["clave-equivocada", "TOKEN-ASESOR", "token-asesor-2", "contraseña"],
    ids=["otra", "mayusculas", "casi_igual", "con_enie"],
)
def test_una_clave_no_valida_responde_401_con_mensaje_claro(
    cliente: TestClient, clave: str
) -> None:
    respuesta = cliente.get(
        "/api/sesion", headers={"Authorization": f"Bearer {clave}".encode()}
    )

    assert respuesta.status_code == 401
    assert respuesta.json() == CLAVE_NO_VALIDA


def test_la_clave_de_sistema_no_es_de_un_empleado(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/sesion", headers=SISTEMA)

    assert respuesta.status_code == 403
    assert respuesta.json() == {
        "error": "RolNoPermitido",
        "detalle": (
            "Esta clave es del sistema automático, no de un empleado del taller. "
            "Escriba su clave de acceso personal."
        ),
        "codigo": 403,
    }


def test_las_demas_rutas_conservan_su_mensaje_para_la_clave_de_sistema(
    cliente: TestClient,
) -> None:
    respuesta = cliente.get("/api/alertas", headers=SISTEMA)

    assert respuesta.status_code == 403
    assert respuesta.json()["detalle"] == (
        "Esta función es de otro puesto del taller. Pida a la persona encargada que la realice."
    )
