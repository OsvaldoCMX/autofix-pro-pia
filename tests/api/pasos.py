"""Tokens de prueba y pasos HTTP para llegar a cada estado, como lo haría el taller."""
from __future__ import annotations

from itertools import count
from typing import Any

from fastapi.testclient import TestClient

TOKENS = {
    "TOKEN_ASESOR": "token-asesor",
    "TOKEN_TECNICO": "token-tecnico",
    "TOKEN_TECNICO_2": "token-tecnico-2",
    "TOKEN_GERENTE": "token-gerente",
    "TOKEN_COMPRAS": "token-compras",
    "TOKEN_CAJA": "token-caja",
    "TOKEN_SISTEMA": "token-sistema",
}


def con_token(variable: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKENS[variable]}"}


ASESOR = con_token("TOKEN_ASESOR")
TECNICO = con_token("TOKEN_TECNICO")
OTRO_TECNICO = con_token("TOKEN_TECNICO_2")
GERENTE = con_token("TOKEN_GERENTE")
COMPRAS = con_token("TOKEN_COMPRAS")
CAJA = con_token("TOKEN_CAJA")
SISTEMA = con_token("TOKEN_SISTEMA")

ID_ASESOR = "EMP-001"
ID_TECNICO = "EMP-002"
ID_OTRO_TECNICO = "EMP-003"

CLIENTE_PARTICULAR = {
    "nombre": "Luis Peña",
    "telefono": "81-2222",
    "correo": "luis@correo.test",
}
CLIENTE_DE_FLOTILLA = {
    "nombre": "Transportes Norte SA",
    "tipo": "Flotilla",
    "telefono": "81-3333",
    "correo": "contacto@norte.test",
    "empresa": "Transportes Norte",
    "responsable_nombre": "Ana Torres",
    "responsable_telefono": "81-1111",
    "responsable_correo": "ana@norte.test",
}

_consecutivo = count(1)


def datos_de_orden(flotilla: bool = False, **cambios: Any) -> dict[str, Any]:
    """Cuerpo válido de `POST /api/ordenes`, con placas y VIN que no se repiten."""
    numero = next(_consecutivo)
    return {
        "placas": f"ABC{numero:03d}",
        "motivo_de_ingreso": "Ruido al frenar",
        "kilometraje": 45000,
        "nivel_de_combustible": "1/2",
        "vehiculo": {
            "vin": f"1HGCM82633A{numero:06d}",
            "marca": "Nissan",
            "modelo": "Versa",
            "anio": 2020,
        },
        "cliente": CLIENTE_DE_FLOTILLA if flotilla else CLIENTE_PARTICULAR,
        **cambios,
    }


def exigir(respuesta: Any, codigo: int) -> dict[str, Any]:
    """Un paso previo que falla debe detener la prueba con un mensaje claro."""
    assert respuesta.status_code == codigo, respuesta.text
    return respuesta.json()


def recibida(cliente: TestClient, flotilla: bool = False) -> str:
    cuerpo = datos_de_orden(flotilla)
    return exigir(cliente.post("/api/ordenes", json=cuerpo, headers=ASESOR), 201)["numero_orden"]
