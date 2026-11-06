"""Aplicación FastAPI: `uvicorn api.main:app` (con `src` en el PYTHONPATH)."""
from __future__ import annotations

import logging

from fastapi import Depends, FastAPI

from api.dependencias import Contenedor, crear_contenedor
from api.errores import registrar_manejadores
from api.esquemas.comunes import rechazar_caracteres_no_validos
from api.rutas import salud

ROUTERS = (salud.router,)


def crear_app(contenedor: Contenedor | None = None) -> FastAPI:
    contenedor = contenedor or crear_contenedor()
    logging.basicConfig(level=contenedor.configuracion.log_level.upper())
    app = FastAPI(
        title="AutoFix Pro API",
        version="0.1.0",
        description=(
            "Gestión de órdenes de servicio del taller AutoFix Pro. Use el botón **Authorize** "
            "con el token del empleado."
        ),
        dependencies=[Depends(rechazar_caracteres_no_validos)],
    )
    app.state.contenedor = contenedor
    registrar_manejadores(app)
    for router in ROUTERS:
        app.include_router(router)
    return app


app = crear_app()
