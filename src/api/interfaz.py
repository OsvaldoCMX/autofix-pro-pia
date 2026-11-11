"""La página del taller (ADR-017): `/` entrega `index.html` y `/web/…` sus archivos.

Los archivos van en `/web/` y no en `/` para que una dirección que no existe, como
`/api/no-existe`, siga respondiendo el error de siempre y no la página.
"""
from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

CARPETA_WEB = Path(__file__).resolve().parent / "web"
# El navegador revisa con el servidor si cambió algo: después de actualizar no usa una versión vieja.
SIN_CACHE = {"Cache-Control": "no-cache"}

# En algunos Windows el registro dice que `.js` es texto y el navegador no carga los módulos.
mimetypes.add_type("text/javascript", ".js")


class ArchivosDeLaPagina(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        respuesta = await super().get_response(path, scope)
        respuesta.headers.update(SIN_CACHE)
        return respuesta


def pagina() -> FileResponse:
    return FileResponse(CARPETA_WEB / "index.html", headers=SIN_CACHE)


def montar_interfaz(app: FastAPI) -> None:
    app.add_api_route("/", pagina, methods=["GET"], include_in_schema=False)
    app.mount("/web", ArchivosDeLaPagina(directory=CARPETA_WEB), name="web")
