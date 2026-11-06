"""`tablas.py` debe coincidir con `database/01_esquema.sql`, que es el esquema oficial (ADR-009)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

import pytest
from sqlalchemy import (
    CheckConstraint,
    Engine,
    ForeignKeyConstraint,
    Table,
    UniqueConstraint,
    inspect,
    text,
)
from sqlalchemy.dialects import postgresql

from application.comandos import (
    AsignarTecnicoParaDiagnostico,
    RegistrarDiagnostico,
    RegistrarOrden,
)
from domain.compartido.valores import NumeroOrden
from domain.ordenes.estados import EstadoOrden
from domain.ordenes.valores import NivelDeCombustible
from infrastructure.base_de_datos.tablas import metadata
from tests.integration.apoyo_base import (
    DATABASE,
    TallerEnBase,
)
from tests.unit.application.escenarios import ASESOR, TECNICO

_TIPOS_EQUIVALENTES = {
    "TIMESTAMPTZ": "TIMESTAMP WITH TIME ZONE",
    "BIGSERIAL": "BIGINT",
    "NUMERIC(12,2)": "NUMERIC(12, 2)",
}
_NOMBRES_DE_LAS_18_TABLAS = {
    "empleados",
    "clientes",
    "vehiculos",
    "ordenes",
    "trabajos",
    "solicitudes_de_compra",
    "fallas_adicionales",
    "fotos_de_danos",
    "cotizaciones",
    "lineas_de_cotizacion",
    "refacciones_cotizadas",
    "recontactos",
    "alertas_internas",
    "eventos",
    "secuencias",
    "catalogo_servicios",
    "servicios_solicitados",
    "referencia_operaciones_profesor",
}


@dataclass
class DefinicionDeTabla:
    """Lo que se compara de cada tabla, venga del SQL o de `tablas.py`."""

    columnas: dict[str, tuple[str, bool]] = field(default_factory=dict)
    llave_primaria: tuple[str, ...] = ()
    llaves_foraneas: set[tuple[str, tuple[str, ...], str, tuple[str, ...], str]] = field(
        default_factory=set
    )
    unicas: set[tuple[str, tuple[str, ...]]] = field(default_factory=set)
    checks: dict[str, str] = field(default_factory=dict)
    indices: dict[str, tuple[str, ...]] = field(default_factory=dict)


def _lista(texto: str) -> tuple[str, ...]:
    return tuple(parte.strip() for parte in texto.split(","))


def _sql_del_esquema() -> str:
    return (DATABASE / "01_esquema.sql").read_text(encoding="utf-8")


def _definicion_desde_el_sql(sql: str, tabla: str) -> DefinicionDeTabla:
    cuerpo = re.search(rf"CREATE TABLE {tabla} \((.*?)\n\);", sql, re.DOTALL)
    assert cuerpo, f"El SQL no tiene la tabla {tabla}"
    definicion = DefinicionDeTabla()
    for linea in cuerpo[1].strip().split("\n"):
        _leer_linea(linea.strip().rstrip(","), definicion)
    for nombre, columnas in re.findall(rf"CREATE INDEX (\w+) ON {tabla} \((.*?)\);", sql):
        definicion.indices[nombre] = _lista(columnas)
    return definicion


def _leer_linea(linea: str, definicion: DefinicionDeTabla) -> None:
    if pk := re.fullmatch(r"CONSTRAINT \w+ PRIMARY KEY \((.*)\)", linea):
        definicion.llave_primaria = _lista(pk[1])
    elif uq := re.fullmatch(r"CONSTRAINT (\w+) UNIQUE \((.*)\)", linea):
        definicion.unicas.add((uq[1], _lista(uq[2])))
    elif fk := re.fullmatch(
        r"CONSTRAINT (\w+) FOREIGN KEY \((.*?)\) REFERENCES (\w+) \((.*?)\) ON DELETE ([A-Z ]+)",
        linea,
    ):
        definicion.llaves_foraneas.add((fk[1], _lista(fk[2]), fk[3], _lista(fk[4]), fk[5]))
    elif ck := re.fullmatch(r"CONSTRAINT (\w+) CHECK \((.*)\)", linea):
        definicion.checks[ck[1]] = ck[2]
    else:
        columna = re.fullmatch(r"(\w+)\s+([A-Z]+(?:\(\d+(?:,\d+)?\))?)(.*)", linea)
        assert columna, f"Línea que no se entiende: {linea}"
        tipo = _TIPOS_EQUIVALENTES.get(columna[2], columna[2])
        definicion.columnas[columna[1]] = (tipo, "NOT NULL" not in columna[3])


def _definicion_desde_tablas(tabla: Table) -> DefinicionDeTabla:
    dialecto = postgresql.dialect()
    definicion = DefinicionDeTabla(
        columnas={
            columna.name: (columna.type.compile(dialect=dialecto), columna.nullable)
            for columna in tabla.columns
        },
        llave_primaria=tuple(columna.name for columna in tabla.primary_key.columns),
        indices={
            indice.name: tuple(columna.name for columna in indice.columns)
            for indice in tabla.indexes
        },
    )
    for restriccion in tabla.constraints:
        if isinstance(restriccion, ForeignKeyConstraint):
            definicion.llaves_foraneas.add(
                (
                    restriccion.name,
                    tuple(restriccion.column_keys),
                    restriccion.referred_table.name,
                    tuple(elemento.column.name for elemento in restriccion.elements),
                    restriccion.ondelete,
                )
            )
        elif isinstance(restriccion, UniqueConstraint):
            nombres = tuple(columna.name for columna in restriccion.columns)
            definicion.unicas.add((restriccion.name, nombres))
        elif isinstance(restriccion, CheckConstraint):
            definicion.checks[restriccion.name] = str(restriccion.sqltext)
    return definicion


def test_tablas_tiene_las_18_tablas_del_modelo_de_datos() -> None:
    assert set(metadata.tables) == _NOMBRES_DE_LAS_18_TABLAS
    creadas = set(re.findall(r"^CREATE TABLE (\w+) \(", _sql_del_esquema(), re.MULTILINE))
    assert creadas == _NOMBRES_DE_LAS_18_TABLAS


@pytest.mark.parametrize("nombre", sorted(_NOMBRES_DE_LAS_18_TABLAS))
def test_tablas_coincide_con_el_sql(nombre: str) -> None:
    del_sql = _definicion_desde_el_sql(_sql_del_esquema(), nombre)
    de_tablas = _definicion_desde_tablas(metadata.tables[nombre])

    assert de_tablas.columnas == del_sql.columnas
    assert de_tablas.llave_primaria == del_sql.llave_primaria
    assert de_tablas.llaves_foraneas == del_sql.llaves_foraneas
    assert de_tablas.unicas == del_sql.unicas
    assert de_tablas.checks == del_sql.checks
    assert de_tablas.indices == del_sql.indices


def test_los_check_con_expresion_regular_solo_existen_en_postgresql(motor: Engine) -> None:
    nombres = {
        check["name"] for check in inspect(motor).get_check_constraints("vehiculos")
    }

    assert ("ck_vehiculos_1" in nombres) == (motor.dialect.name == "postgresql")
    assert "ck_vehiculos_3" in nombres


@pytest.fixture
def base_real(motor_postgresql: Engine | None) -> Engine:
    if motor_postgresql is None:
        pytest.skip("Requiere PostgreSQL: se ejecuta con DATABASE_URL (Docker o el CI).")
    return motor_postgresql


@pytest.mark.parametrize("nombre", sorted(_NOMBRES_DE_LAS_18_TABLAS))
def test_tablas_coincide_con_postgresql_real(base_real: Engine, nombre: str) -> None:
    inspector = inspect(base_real)
    tabla = metadata.tables[nombre]
    dialecto = postgresql.dialect()

    reales = {
        columna["name"]: (columna["type"].compile(dialect=dialecto), columna["nullable"])
        for columna in inspector.get_columns(nombre)
    }
    esperadas = {
        columna.name: (columna.type.compile(dialect=dialecto), columna.nullable)
        for columna in tabla.columns
    }
    assert reales == esperadas
    assert tuple(inspector.get_pk_constraint(nombre)["constrained_columns"]) == tuple(
        columna.name for columna in tabla.primary_key.columns
    )
    foraneas_reales = {
        (fk["name"], tuple(fk["constrained_columns"]), fk["referred_table"])
        for fk in inspector.get_foreign_keys(nombre)
    }
    foraneas_esperadas = {
        (fk.name, tuple(fk.column_keys), fk.referred_table.name)
        for fk in tabla.foreign_key_constraints
    }
    assert foraneas_reales == foraneas_esperadas


# ------------------------------------------------------------------ datos iniciales del profesor
def _consultas_de_verificacion() -> list[str]:
    script = (DATABASE / "03_verificacion.sql").read_text(encoding="utf-8")
    return [parte.strip() for parte in script.split(";") if "SELECT" in parte]


def test_datos_iniciales_cargan_y_verifican(base_con_datos_iniciales: Engine) -> None:
    conteos, total, mayor = _consultas_de_verificacion()

    with base_con_datos_iniciales.connect() as conexion:
        filas = conexion.execute(text(conteos)).all()
        referencia = conexion.execute(text(total)).scalar_one()
        operacion_mayor = conexion.execute(text(mayor)).one()

    assert len(filas) == 10
    assert [fila.tabla for fila in filas if fila.obtenido != fila.esperado] == []
    assert referencia == Decimal("305758.00")
    assert (operacion_mayor.numero_orden, operacion_mayor.total) == ("AUT-O008", Decimal("12887.00"))


def test_las_60_ordenes_iniciales_se_reconstruyen_en_el_dominio(
    base_con_datos_iniciales: Engine,
) -> None:
    taller = TallerEnBase(base_con_datos_iniciales)
    resumenes = taller.lector().ordenes(EstadoOrden.RECIBIDA)
    assert len(resumenes) == 60

    with taller.uow() as uow:
        for resumen in resumenes:
            orden = uow.ordenes.obtener(NumeroOrden(resumen.numero_orden))
            assert orden.estado is EstadoOrden.RECIBIDA
            assert orden.estado_de_recepcion is None
            assert orden.fecha_ingreso_a_fila == orden.fecha_ingreso
            assert uow.clientes.obtener(orden.id_cliente).id_cliente == orden.id_cliente
            assert uow.vehiculos.por_placas(orden.placas).id_cliente == orden.id_cliente

    assert len(taller.lector().clientes(None, None)) == 40


def test_orden_del_profesor_avanza_con_los_casos_de_uso(base_con_datos_iniciales: Engine) -> None:
    taller = TallerEnBase(base_con_datos_iniciales)

    taller.diagnostico.asignar_tecnico(AsignarTecnicoParaDiagnostico("AUT-O001", TECNICO))
    taller.diagnostico.registrar_diagnostico(
        RegistrarDiagnostico("AUT-O001", TECNICO, "Balatas gastadas", "Cambiar balatas")
    )

    expediente = taller.lector().expediente(NumeroOrden("AUT-O001"))
    assert expediente.estado == "En Diagnóstico"
    assert expediente.diagnostico_fallas == "Balatas gastadas"


def test_el_primer_folio_nuevo_es_os_0001(base_con_datos_iniciales: Engine) -> None:
    """Un vehículo del profesor que regresa reutiliza sus registros (CA-003)."""
    taller = TallerEnBase(base_con_datos_iniciales)

    resultado = taller.recepcion.registrar_orden(
        RegistrarOrden(ASESOR, "PIA-AUT-001", "Revisión", 1000, NivelDeCombustible.LLENO)
    )

    assert resultado.numero_orden == "OS-0001"
    assert resultado.id_cliente == "AUT-C014"
