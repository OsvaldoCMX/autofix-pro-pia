"""Apoyo de las pruebas de integración: elige la base y protege los datos reales.

Sin `DATABASE_URL` se usa SQLite en memoria. Con ella se usa PostgreSQL, pero las pruebas trabajan
en un esquema privado y temporal: su `search_path` solo ve ese esquema, así que ningún `DROP` o
`DELETE` alcanza las tablas de `public`. Nunca corren contra Supabase ni otro servidor remoto.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import Connection, Engine, func, insert, make_url, select, text

from application.puertos import PublicadorDeEventos
from domain.empleados.empleado import Empleado
from infrastructure.base_de_datos import mapeo
from infrastructure.base_de_datos.lector import LectorDeOrdenesSqlAlchemy
from infrastructure.base_de_datos.motor import crear_motor
from infrastructure.base_de_datos.tablas import (
    SECUENCIAS,
    catalogo_servicios,
    empleados,
    metadata,
    ordenes,
    secuencias,
    servicios_solicitados,
)
from infrastructure.base_de_datos.unidad_de_trabajo import UnidadDeTrabajoSqlAlchemy
from infrastructure.config import Configuracion
from tests.unit.application.escenarios import Taller

DATABASE = Path(__file__).resolve().parents[2] / "database"
SERVIDORES_LOCALES = frozenset({"localhost", "127.0.0.1", "::1", "db", "postgres"})
_REINICIAR_SECUENCIAS = """
    SELECT setval(clase.oid::regclass, 1, false)
    FROM pg_class AS clase
    WHERE clase.relkind = 'S' AND clase.relnamespace = current_schema()::regnamespace
"""


class TallerEnBase(Taller):
    """El mismo taller de las pruebas de aplicación, pero guardando en la base de datos."""

    def __init__(self, motor: Engine, publicador: PublicadorDeEventos | None = None) -> None:
        super().__init__(publicador)
        self.motor = motor

    def uow(self) -> UnidadDeTrabajoSqlAlchemy:
        return UnidadDeTrabajoSqlAlchemy(self.motor)

    def lector(self) -> LectorDeOrdenesSqlAlchemy:
        return LectorDeOrdenesSqlAlchemy(self.motor)

    def ordenes_registradas(self) -> int:
        with self.motor.connect() as conexion:
            return conexion.execute(select(func.count()).select_from(ordenes)).scalar_one()

    def registrar_servicios_de_orden(
        self, numero: str, habilitados: tuple[str, ...], inhabilitados: tuple[str, ...]
    ) -> None:
        registrar_servicios_de_orden(self.motor, numero, habilitados, inhabilitados)


def registrar_servicios_de_orden(
    motor: Engine, numero: str, habilitados: tuple[str, ...], inhabilitados: tuple[str, ...]
) -> None:
    """Agrega al catálogo los servicios indicados y los liga a la orden, como los datos iniciales."""
    servicios = [(recurso, True) for recurso in habilitados]
    servicios += [(recurso, False) for recurso in inhabilitados]
    with motor.begin() as conexion:
        conexion.execute(
            insert(catalogo_servicios),
            [
                {
                    "recurso_id": recurso,
                    "descripcion": f"Servicio {recurso}",
                    "precio_mxn": Decimal("100.00"),
                    "capacidad_o_stock": 1,
                    "habilitado": habilitado,
                }
                for recurso, habilitado in servicios
            ],
        )
        conexion.execute(
            insert(servicios_solicitados),
            [{"numero_orden": numero, "recurso_id": r, "cantidad": 1} for r, _ in servicios],
        )


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


def nombre_de_esquema(prefijo: str) -> str:
    """Aleatorio: en un contenedor el pid se repite y una ejecución interrumpida deja su esquema."""
    return f"{prefijo}_{uuid4().hex[:12]}"


def url_con_esquema(url: str, esquema: str) -> str:
    """`synchronous_commit=off` no cambia lo que se lee, y solo aplica a estas conexiones."""
    opciones = f"-csearch_path={esquema} -csynchronous_commit=off"
    conectada = make_url(url).update_query_dict({"options": opciones})
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
            _vaciar_postgresql(conexion)
        else:
            metadata.create_all(conexion)
        conexion.execute(
            insert(secuencias), [{"nombre": nombre, "ultimo_valor": 0} for nombre in SECUENCIAS]
        )
        if personal:
            conexion.execute(
                insert(empleados), [mapeo.fila_de_empleado(empleado) for empleado in personal]
            )


def _vaciar_postgresql(conexion: Connection) -> None:
    """Mismo resultado que `TRUNCATE ... RESTART IDENTITY`, pero mucho más rápido con pocas filas.

    `TRUNCATE` crea archivos nuevos para cada tabla e índice. Todo va en una sola sentencia al
    servidor para ahorrar una ida y vuelta por tabla.
    """
    borrados = "; ".join(f"DELETE FROM {tabla.name}" for tabla in reversed(metadata.sorted_tables))
    conexion.exec_driver_sql(borrados)
    conexion.execute(text(_REINICIAR_SECUENCIAS))
