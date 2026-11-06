"""Apoyo de las pruebas de integración: elige la base y protege los datos reales.

Sin `DATABASE_URL` se usa SQLite en memoria. Con ella se usa PostgreSQL, pero las pruebas trabajan
en un esquema privado y temporal: su `search_path` solo ve ese esquema, así que ningún `DROP` o
`TRUNCATE` alcanza las tablas de `public`. Nunca corren contra Supabase ni otro servidor remoto.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, insert, make_url, text

from domain.empleados.empleado import Empleado
from infrastructure.base_de_datos import mapeo
from infrastructure.base_de_datos.motor import crear_motor
from infrastructure.base_de_datos.tablas import SECUENCIAS, empleados, metadata, secuencias
from infrastructure.config import Configuracion

DATABASE = Path(__file__).resolve().parents[2] / "database"
SERVIDORES_LOCALES = frozenset({"localhost", "127.0.0.1", "::1", "db", "postgres"})


class ServidorNoPermitido(Exception):
    """La URL no apunta a una base local: las pruebas no se ejecutan."""


def url_de_postgresql_para_pruebas() -> str | None:
    """Devuelve la URL de PostgreSQL de `DATABASE_URL`, o `None` si toca usar SQLite."""
    url = Configuracion.desde_entorno().database_url
    if url is None or not url.startswith("postgresql"):
        return None
    exigir_servidor_local(url)
    return url


def exigir_servidor_local(url: str) -> None:
    """El mensaje solo incluye el servidor: nunca muestra la contraseña."""
    servidor = make_url(url).host
    if servidor not in SERVIDORES_LOCALES:
        raise ServidorNoPermitido(
            f"Las pruebas de integración solo corren en una base local; DATABASE_URL apunta a "
            f"«{servidor}». Quite esa variable o use PostgreSQL de Docker."
        )


def url_con_esquema(url: str, esquema: str) -> str:
    conectada = make_url(url).update_query_dict({"options": f"-csearch_path={esquema}"})
    return conectada.render_as_string(hide_password=False)


def crear_esquema(url: str, esquema: str) -> None:
    motor = crear_motor(url)
    with motor.connect().execution_options(isolation_level="AUTOCOMMIT") as conexion:
        conexion.execute(text(f'CREATE SCHEMA "{esquema}"'))
    motor.dispose()


def eliminar_esquema(url: str, esquema: str) -> None:
    motor = crear_motor(url)
    with motor.connect().execution_options(isolation_level="AUTOCOMMIT") as conexion:
        conexion.execute(text(f'DROP SCHEMA "{esquema}" CASCADE'))
    motor.dispose()


def ejecutar_script(motor: Engine, nombre: str) -> None:
    """Ejecuta un archivo de `database/` completo, como `psql` (trae su propio BEGIN y COMMIT)."""
    sql = (DATABASE / nombre).read_text(encoding="utf-8")
    conexion = motor.raw_connection()
    try:
        original = conexion.driver_connection
        original.autocommit = True
        original.execute(sql)
        original.autocommit = False
    finally:
        conexion.close()


def preparar_base(motor: Engine, personal: tuple[Empleado, ...]) -> None:
    """Deja la base como la dejaría `01_esquema.sql`, más los empleados indicados."""
    with motor.begin() as conexion:
        if motor.dialect.name == "postgresql":
            nombres = ", ".join(tabla.name for tabla in metadata.sorted_tables)
            conexion.execute(text(f"TRUNCATE {nombres} RESTART IDENTITY CASCADE"))
        else:
            metadata.create_all(conexion)
        conexion.execute(
            insert(secuencias), [{"nombre": nombre, "ultimo_valor": 0} for nombre in SECUENCIAS]
        )
        if personal:
            conexion.execute(
                insert(empleados), [mapeo.fila_de_empleado(empleado) for empleado in personal]
            )
