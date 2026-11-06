"""Configuración: toda viene del entorno (decisiones-tecnicas.md §3, ADR-010).

La URL de la base y los tokens son secretos: no aparecen en `repr`, así no llegan a una bitácora.
"""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

AMBIENTES = ("desarrollo", "pruebas", "produccion")
VARIABLES_DE_TOKEN = (
    "TOKEN_ASESOR",
    "TOKEN_TECNICO",
    "TOKEN_TECNICO_2",
    "TOKEN_GERENTE",
    "TOKEN_COMPRAS",
    "TOKEN_CAJA",
    "TOKEN_SISTEMA",
)
_PREFIJO_POSTGRESQL = "postgresql://"
_PREFIJO_CON_DRIVER = "postgresql+psycopg://"


def normalizar_url_de_base(url: str) -> str:
    """Supabase entrega `postgresql://`; SQLAlchemy necesita saber que el driver es psycopg 3."""
    if url.startswith(_PREFIJO_POSTGRESQL):
        return _PREFIJO_CON_DRIVER + url.removeprefix(_PREFIJO_POSTGRESQL)
    return url


@dataclass(frozen=True)
class Configuracion:
    app_env: str = "desarrollo"
    zona_horaria: str = "America/Monterrey"
    port: int = 8000
    log_level: str = "info"
    database_url: str | None = field(default=None, repr=False)
    tokens: Mapping[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if self.app_env not in AMBIENTES:
            raise ValueError(f"APP_ENV debe ser uno de {AMBIENTES}, no «{self.app_env}».")

    @classmethod
    def desde_entorno(cls, entorno: Mapping[str, str] | None = None) -> Configuracion:
        valores = os.environ if entorno is None else entorno
        url = valores.get("DATABASE_URL")
        return cls(
            app_env=valores.get("APP_ENV") or cls.app_env,
            zona_horaria=valores.get("ZONA_HORARIA") or cls.zona_horaria,
            port=int(valores.get("PORT") or cls.port),
            log_level=valores.get("LOG_LEVEL") or cls.log_level,
            database_url=normalizar_url_de_base(url) if url else None,
            tokens={
                variable: valores[variable]
                for variable in VARIABLES_DE_TOKEN
                if valores.get(variable)
            },
        )
