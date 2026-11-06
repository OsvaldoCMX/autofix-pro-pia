"""Tokens de prueba y pasos HTTP para llegar a cada estado, como lo haría el taller."""
from __future__ import annotations

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
