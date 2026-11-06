"""Escribe el contrato real de la API en `docs/api/openapi.json`.

Uso: `python -m api.exportar_openapi` (con `src` en el PYTHONPATH). No se conecta a la base.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI

from api.main import app

DESTINO = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json"


def contenido_de_openapi(aplicacion: FastAPI) -> str:
    return json.dumps(aplicacion.openapi(), ensure_ascii=False, indent=2) + "\n"


def exportar(destino: Path = DESTINO) -> None:
    destino.write_text(contenido_de_openapi(app), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    exportar()
