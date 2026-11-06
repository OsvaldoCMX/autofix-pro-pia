"""Creación del motor de base de datos (ADR-009). La aplicación nunca crea tablas aquí."""
from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.pool import StaticPool

URL_DE_SQLITE_EN_MEMORIA = "sqlite+pysqlite:///:memory:"


def crear_motor(url: str) -> Engine:
    if url.startswith("sqlite"):
        return _motor_de_sqlite(url)
    # Una conexión puede caducar si Render o Supabase están inactivos: se revisa antes de usarla.
    return create_engine(url, pool_pre_ping=True)


def _motor_de_sqlite(url: str) -> Engine:
    if ":memory:" in url:
        # La base en memoria solo existe dentro de su conexión: todos deben compartir la misma.
        motor = create_engine(url, poolclass=StaticPool, connect_args={"check_same_thread": False})
    else:
        motor = create_engine(url)
    event.listen(motor, "connect", _activar_llaves_foraneas)
    return motor


def _activar_llaves_foraneas(conexion: Any, _registro: Any) -> None:
    """SQLite no revisa las llaves foráneas si no se le pide."""
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
