"""Configuración desde el entorno, creación del motor y protección contra bases remotas."""
from __future__ import annotations

import pytest
from sqlalchemy import inspect, text

from infrastructure.base_de_datos.motor import URL_DE_SQLITE_EN_MEMORIA, crear_motor
from infrastructure.config import Configuracion, normalizar_url_de_base
from tests.integration.apoyo_base import ServidorNoPermitido, exigir_servidor_local

URL_CON_SECRETO = "postgresql://usuario:clave-secreta@localhost:5432/autofix"
URL_REMOTA = "postgresql://postgres.ref:clave-secreta@aws-0-us-east-1.pooler.supabase.com:5432/db"


def test_normaliza_el_prefijo_postgresql() -> None:
    assert (
        normalizar_url_de_base("postgresql://u:c@servidor:5432/base")
        == "postgresql+psycopg://u:c@servidor:5432/base"
    )
    configuracion = Configuracion.desde_entorno({"DATABASE_URL": URL_CON_SECRETO})
    assert configuracion.database_url.startswith("postgresql+psycopg://")


@pytest.mark.parametrize(
    "url", ["postgresql+psycopg://u:c@db:5432/base", "sqlite+pysqlite:///:memory:"]
)
def test_respeta_urls_ya_normalizadas(url: str) -> None:
    assert normalizar_url_de_base(url) == url


def test_valores_por_defecto() -> None:
    configuracion = Configuracion.desde_entorno({})

    assert configuracion.app_env == "desarrollo"
    assert configuracion.zona_horaria == "America/Monterrey"
    assert configuracion.port == 8000
    assert configuracion.log_level == "info"
    assert configuracion.database_url is None
    assert configuracion.tokens == {}


def test_lee_las_variables_del_entorno() -> None:
    configuracion = Configuracion.desde_entorno(
        {
            "APP_ENV": "produccion",
            "ZONA_HORARIA": "UTC",
            "PORT": "9000",
            "LOG_LEVEL": "debug",
            "TOKEN_CAJA": "token-de-caja",
            "OTRA_VARIABLE": "se ignora",
        }
    )

    assert (configuracion.app_env, configuracion.zona_horaria) == ("produccion", "UTC")
    assert (configuracion.port, configuracion.log_level) == (9000, "debug")
    assert configuracion.tokens == {"TOKEN_CAJA": "token-de-caja"}


def test_app_env_invalido_se_rechaza() -> None:
    with pytest.raises(ValueError, match="APP_ENV"):
        Configuracion.desde_entorno({"APP_ENV": "staging"})


def test_repr_no_expone_secretos() -> None:
    configuracion = Configuracion.desde_entorno(
        {"DATABASE_URL": URL_CON_SECRETO, "TOKEN_ASESOR": "token-secreto"}
    )

    assert "clave-secreta" not in repr(configuracion)
    assert "token-secreto" not in repr(configuracion)


def test_sqlite_activa_llaves_foraneas() -> None:
    motor = crear_motor(URL_DE_SQLITE_EN_MEMORIA)
    with motor.connect() as conexion:
        assert conexion.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    motor.dispose()


def test_sqlite_en_archivo_activa_llaves_foraneas(tmp_path) -> None:
    motor = crear_motor(f"sqlite+pysqlite:///{tmp_path / 'prueba.db'}")
    with motor.connect() as conexion:
        assert conexion.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    motor.dispose()


def test_crear_motor_no_crea_tablas() -> None:
    motor = crear_motor(URL_DE_SQLITE_EN_MEMORIA)

    assert inspect(motor).get_table_names() == []
    motor.dispose()


def test_crear_motor_de_postgresql_no_se_conecta_al_crearse() -> None:
    motor = crear_motor("postgresql+psycopg://u:c@servidor-inexistente:5432/base")

    assert motor.dialect.name == "postgresql"
    assert motor.pool.checkedout() == 0
    motor.dispose()


def test_la_proteccion_rechaza_supabase() -> None:
    with pytest.raises(ServidorNoPermitido) as error:
        exigir_servidor_local(URL_REMOTA)

    assert "supabase" in str(error.value)
    assert "clave-secreta" not in str(error.value)


@pytest.mark.parametrize("servidor", ["localhost", "127.0.0.1", "db", "postgres"])
def test_la_proteccion_acepta_servidores_locales(servidor: str) -> None:
    exigir_servidor_local(f"postgresql+psycopg://u:c@{servidor}:5432/base")
