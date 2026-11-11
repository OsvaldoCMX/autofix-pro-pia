"""Las 19 tablas de `database/01_esquema.sql` con SQLAlchemy Core (ADR-009, modelo-de-datos.md).

El dominio no conoce este módulo: `mapeo.py` traduce filas y objetos. La aplicación no crea tablas
en producción; `metadata.create_all()` solo se usa en las pruebas con SQLite. Cada cambio se hace
primero en `scripts/db/esquema.py`, y una prueba de integración compara este archivo con el SQL.
Los dos CHECK con expresiones regulares (`~`) solo existen en PostgreSQL.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    CHAR,
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Dialect,
    ForeignKeyConstraint,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    Numeric,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Table,
    Text,
    TypeDecorator,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

SECUENCIAS = ("orden", "cotizacion", "recibo", "cliente")

_ESTADOS_ORDEN = (
    "'Recibida', 'En Diagnóstico', 'Cotizada', 'Autorizada', 'En Reparación', 'En Espera de "
    "Refacción', 'Pausada por Retiro de Vehículo', 'Lista para Entrega', 'Pagada', 'Por "
    "Cobrar (Crédito)', 'Cerrada', 'Cerrada sin Reparación', 'Cancelada'"
)
_ESTADOS_COTIZACION = (
    "'Pendiente de Aprobación Gerencial', 'Requiere Ajuste', 'Pendiente de Autorización del "
    "Cliente', 'Autorizada', 'Autorizada Parcialmente', 'Rechazada'"
)
_ESTADOS_TRABAJO = "'Pendiente', 'En Progreso', 'Completado', 'No Autorizado'"
_ESTADOS_SOLICITUD = "'Solicitada', 'Disponible'"
_ROLES = "'Asesor', 'Técnico', 'Gerente', 'Compras', 'Caja'"
_COMBUSTIBLE = "'Reserva', '1/4', '1/2', '3/4', 'Lleno'"
_FORMAS_DE_PAGO = "'Efectivo', 'Tarjeta', 'Transferencia'"

_IMPORTE = Numeric(12, 2)
_ID_AUTOMATICO = BigInteger().with_variant(Integer(), "sqlite")  # BIGSERIAL
_JSON = JSON().with_variant(JSONB(), "postgresql")


class FechaUTC(TypeDecorator[datetime]):
    """TIMESTAMPTZ: se guarda en UTC y se lee siempre con zona, también en SQLite, que no la tiene.

    Rechaza las fechas sin zona porque no se sabría a qué instante corresponden.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> Any:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Las fechas deben indicar su zona horaria.")
        utc = value.astimezone(UTC)
        return utc.replace(tzinfo=None) if dialect.name == "sqlite" else utc

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


empleados = Table(
    "empleados",
    metadata,
    Column("id", String(20), nullable=False),
    Column("nombre", String(120), nullable=False),
    Column("rol", String(20), nullable=False),
    PrimaryKeyConstraint("id", name="pk_empleados"),
    CheckConstraint(f"rol IN ({_ROLES})", name="ck_empleados_1"),
)

clientes = Table(
    "clientes",
    metadata,
    Column("id", String(20), nullable=False),
    Column("nombre", String(120), nullable=False),
    Column("telefono", String(20), nullable=True),
    Column("correo", String(120), nullable=True),
    Column("tipo", String(20), nullable=False, server_default=text("'Particular'")),
    Column("empresa", String(120), nullable=True),
    Column("responsable_nombre", String(120), nullable=True),
    Column("responsable_telefono", String(20), nullable=True),
    Column("responsable_correo", String(120), nullable=True),
    PrimaryKeyConstraint("id", name="pk_clientes"),
    CheckConstraint("tipo IN ('Particular', 'Flotilla')", name="ck_clientes_1"),
    CheckConstraint(
        ("tipo = 'Particular' OR (empresa IS NOT NULL AND responsable_nombre IS NOT NULL)"),
        name="ck_clientes_2",
    ),
    Index("ix_clientes_empresa", "empresa"),
)

vehiculos = Table(
    "vehiculos",
    metadata,
    Column("placas", String(15), nullable=False),
    Column("vin", CHAR(17), nullable=False),
    Column("marca", String(60), nullable=False),
    Column("modelo", String(60), nullable=False),
    Column("anio", SmallInteger(), nullable=False),
    Column("id_cliente", String(20), nullable=False),
    PrimaryKeyConstraint("placas", name="pk_vehiculos"),
    UniqueConstraint("vin", name="uq_vehiculos_vin"),
    ForeignKeyConstraint(
        ["id_cliente"], ["clientes.id"], name="fk_vehiculos_id_cliente", ondelete="RESTRICT"
    ),
    CheckConstraint("placas ~ '^[A-Z0-9]+$'", name="ck_vehiculos_1").ddl_if(dialect="postgresql"),
    CheckConstraint("vin ~ '^[A-HJ-NPR-Z0-9]{17}$'", name="ck_vehiculos_2").ddl_if(
        dialect="postgresql"
    ),
    CheckConstraint("anio BETWEEN 1900 AND 2100", name="ck_vehiculos_3"),
    Index("ix_vehiculos_cliente", "id_cliente"),
)

# RN-27: la misma lista de estados cerrados que el dominio (`ESTADOS_DE_ORDEN_CERRADA`).
INDICE_DE_ORDEN_ABIERTA = "uq_ordenes_una_abierta_por_vehiculo"
CONDICION_DE_ORDEN_ABIERTA = "estado NOT IN ('Cerrada', 'Cerrada sin Reparación', 'Cancelada')"

ordenes = Table(
    "ordenes",
    metadata,
    Column("numero", String(20), nullable=False),
    Column("id_cliente", String(20), nullable=False),
    Column("es_cliente_de_flotilla", Boolean(), nullable=False, server_default=false()),
    Column("placas", String(15), nullable=False),
    Column("asesor", String(20), nullable=False),
    Column("motivo_de_ingreso", Text(), nullable=False),
    Column("kilometraje", Integer(), nullable=True),
    Column("nivel_combustible", String(10), nullable=True),
    Column("estado", String(40), nullable=False, server_default=text("'Recibida'")),
    Column("fecha_ingreso", FechaUTC(), nullable=False),
    Column("ultima_actualizacion", FechaUTC(), nullable=False),
    Column("tecnico_de_diagnostico", String(20), nullable=True),
    Column("diagnostico_fallas", Text(), nullable=True),
    Column("diagnostico_recomendaciones", Text(), nullable=True),
    Column("diagnostico_registrado_en", FechaUTC(), nullable=True),
    Column("cotizada", Boolean(), nullable=False, server_default=false()),
    Column("rechazo_total", Boolean(), nullable=False, server_default=false()),
    Column("adicionales_pendientes", SmallInteger(), nullable=False, server_default=text("0")),
    Column("fecha_ingreso_a_fila", FechaUTC(), nullable=True),
    Column("estado_antes_de_espera", String(40), nullable=True),
    Column("nota_fecha_salida", FechaUTC(), nullable=True),
    Column("nota_firmada", Boolean(), nullable=False, server_default=false()),
    Column("nota_fecha_firma", FechaUTC(), nullable=True),
    Column("pago_monto", _IMPORTE, nullable=True),
    Column("pago_forma", String(20), nullable=True),
    Column("pago_registrado_en", FechaUTC(), nullable=True),
    Column("recibo_numero", String(20), nullable=True),
    Column("credito_monto", _IMPORTE, nullable=True),
    Column("credito_registrado_en", FechaUTC(), nullable=True),
    Column("credito_fecha_vencimiento", Date(), nullable=True),
    Column("fecha_entrega", FechaUTC(), nullable=True),
    Column("cancelacion_motivo", Text(), nullable=True),
    Column("cancelacion_registrada_en", FechaUTC(), nullable=True),
    Column("cancelacion_asesor", String(20), nullable=True),
    PrimaryKeyConstraint("numero", name="pk_ordenes"),
    UniqueConstraint("recibo_numero", name="uq_ordenes_recibo_numero"),
    ForeignKeyConstraint(
        ["id_cliente"], ["clientes.id"], name="fk_ordenes_id_cliente", ondelete="RESTRICT"
    ),
    ForeignKeyConstraint(
        ["placas"],
        ["vehiculos.placas"],
        name="fk_ordenes_placas",
        ondelete="RESTRICT",
        onupdate="CASCADE",
    ),
    ForeignKeyConstraint(
        ["asesor"], ["empleados.id"], name="fk_ordenes_asesor", ondelete="RESTRICT"
    ),
    ForeignKeyConstraint(
        ["tecnico_de_diagnostico"],
        ["empleados.id"],
        name="fk_ordenes_tecnico_de_diagnostico",
        ondelete="RESTRICT",
    ),
    ForeignKeyConstraint(
        ["cancelacion_asesor"],
        ["empleados.id"],
        name="fk_ordenes_cancelacion_asesor",
        ondelete="RESTRICT",
    ),
    CheckConstraint(f"estado IN ({_ESTADOS_ORDEN})", name="ck_ordenes_1"),
    CheckConstraint(
        (
            "estado_antes_de_espera IS NULL OR estado_antes_de_espera IN ('Autorizada', "
            "'En Reparación')"
        ),
        name="ck_ordenes_2",
    ),
    CheckConstraint("kilometraje IS NULL OR kilometraje >= 0", name="ck_ordenes_3"),
    CheckConstraint(
        (f"nivel_combustible IS NULL OR nivel_combustible IN ({_COMBUSTIBLE})"), name="ck_ordenes_4"
    ),
    CheckConstraint("adicionales_pendientes >= 0", name="ck_ordenes_5"),
    CheckConstraint(
        f"pago_forma IS NULL OR pago_forma IN ({_FORMAS_DE_PAGO})", name="ck_ordenes_6"
    ),
    CheckConstraint("pago_monto IS NULL OR pago_monto >= 0", name="ck_ordenes_7"),
    CheckConstraint("credito_monto IS NULL OR credito_monto >= 0", name="ck_ordenes_8"),
    CheckConstraint(
        "NOT (pago_monto IS NOT NULL AND credito_monto IS NOT NULL)", name="ck_ordenes_9"
    ),
    CheckConstraint(
        "estado <> 'Cancelada' OR cancelacion_motivo IS NOT NULL", name="ck_ordenes_10"
    ),
    Index("ix_ordenes_estado", "estado"),
    Index("ix_ordenes_cliente", "id_cliente"),
    Index("ix_ordenes_placas", "placas"),
    Index("ix_ordenes_pago_fecha", "pago_registrado_en"),
    Index(
        INDICE_DE_ORDEN_ABIERTA,
        "placas",
        unique=True,
        postgresql_where=text(CONDICION_DE_ORDEN_ABIERTA),
        sqlite_where=text(CONDICION_DE_ORDEN_ABIERTA),
    ),
)

trabajos = Table(
    "trabajos",
    metadata,
    Column("numero_orden", String(20), nullable=False),
    Column("id", Integer(), nullable=False, autoincrement=False),
    Column("descripcion", Text(), nullable=False),
    Column("importe", _IMPORTE, nullable=False),
    Column("estado", String(20), nullable=False, server_default=text("'Pendiente'")),
    Column("tecnico", String(20), nullable=True),
    Column("id_cotizacion", String(20), nullable=True),
    Column("numero_linea", Integer(), nullable=True),
    PrimaryKeyConstraint("numero_orden", "id", name="pk_trabajos"),
    ForeignKeyConstraint(
        ["numero_orden"], ["ordenes.numero"], name="fk_trabajos_numero_orden", ondelete="CASCADE"
    ),
    ForeignKeyConstraint(
        ["tecnico"], ["empleados.id"], name="fk_trabajos_tecnico", ondelete="RESTRICT"
    ),
    CheckConstraint(f"estado IN ({_ESTADOS_TRABAJO})", name="ck_trabajos_1"),
    CheckConstraint("importe >= 0", name="ck_trabajos_2"),
    CheckConstraint("id >= 1", name="ck_trabajos_3"),
    Index("ix_trabajos_tecnico", "tecnico"),
)

solicitudes_de_compra = Table(
    "solicitudes_de_compra",
    metadata,
    Column("numero_orden", String(20), nullable=False),
    Column("id", Integer(), nullable=False, autoincrement=False),
    Column("id_trabajo", Integer(), nullable=False),
    Column("refaccion", String(200), nullable=False),
    Column("cantidad", Integer(), nullable=False),
    Column("fecha_solicitud", FechaUTC(), nullable=False),
    Column("estado", String(20), nullable=False, server_default=text("'Solicitada'")),
    Column("fecha_llegada", FechaUTC(), nullable=True),
    Column("fecha_aviso_al_cliente", FechaUTC(), nullable=True),
    PrimaryKeyConstraint("numero_orden", "id", name="pk_solicitudes_de_compra"),
    ForeignKeyConstraint(
        ["numero_orden"],
        ["ordenes.numero"],
        name="fk_solicitudes_de_compra_numero_orden",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["numero_orden", "id_trabajo"],
        ["trabajos.numero_orden", "trabajos.id"],
        name="fk_solicitudes_de_compra_numero_orden_id_trabajo",
        ondelete="RESTRICT",
    ),
    CheckConstraint(f"estado IN ({_ESTADOS_SOLICITUD})", name="ck_solicitudes_de_compra_1"),
    CheckConstraint("cantidad > 0", name="ck_solicitudes_de_compra_2"),
    Index("ix_solicitudes_estado", "estado"),
)

fallas_adicionales = Table(
    "fallas_adicionales",
    metadata,
    Column("numero_orden", String(20), nullable=False),
    Column("id", Integer(), nullable=False, autoincrement=False),
    Column("descripcion", Text(), nullable=False),
    Column("tecnico", String(20), nullable=False),
    Column("reportada_en", FechaUTC(), nullable=False),
    PrimaryKeyConstraint("numero_orden", "id", name="pk_fallas_adicionales"),
    ForeignKeyConstraint(
        ["numero_orden"],
        ["ordenes.numero"],
        name="fk_fallas_adicionales_numero_orden",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["tecnico"], ["empleados.id"], name="fk_fallas_adicionales_tecnico", ondelete="RESTRICT"
    ),
)

fotos_de_danos = Table(
    "fotos_de_danos",
    metadata,
    Column("id", _ID_AUTOMATICO, nullable=False),
    Column("numero_orden", String(20), nullable=False),
    Column("nombre_archivo", String(200), nullable=False),
    Column("tipo_mime", String(20), nullable=False),
    Column("tamano_bytes", Integer(), nullable=False),
    Column("contenido", LargeBinary(), nullable=False),
    Column("subida_en", FechaUTC(), nullable=False, server_default=func.now()),
    PrimaryKeyConstraint("id", name="pk_fotos_de_danos"),
    ForeignKeyConstraint(
        ["numero_orden"],
        ["ordenes.numero"],
        name="fk_fotos_de_danos_numero_orden",
        ondelete="CASCADE",
    ),
    CheckConstraint("tipo_mime IN ('image/jpeg', 'image/png')", name="ck_fotos_de_danos_1"),
    CheckConstraint("tamano_bytes BETWEEN 1 AND 5242880", name="ck_fotos_de_danos_2"),
    Index("ix_fotos_orden", "numero_orden"),
)

cotizaciones = Table(
    "cotizaciones",
    metadata,
    Column("id", String(20), nullable=False),
    Column("numero_orden", String(20), nullable=False),
    Column("tipo", String(20), nullable=False),
    Column("version", SmallInteger(), nullable=False),
    Column("estado", String(50), nullable=False),
    Column("total", _IMPORTE, nullable=False),
    Column("generada_en", FechaUTC(), nullable=False),
    Column("fecha_aprobacion_gerencial", FechaUTC(), nullable=True),
    Column("observaciones_del_gerente", Text(), nullable=True),
    Column("fecha_presentacion", FechaUTC(), nullable=True),
    Column("decision_autorizante", String(120), nullable=True),
    Column("decision_rol", String(30), nullable=True),
    Column("decision_registrada_en", FechaUTC(), nullable=True),
    PrimaryKeyConstraint("id", name="pk_cotizaciones"),
    UniqueConstraint("numero_orden", "version", name="uq_cotizaciones_numero_orden_version"),
    ForeignKeyConstraint(
        ["numero_orden"],
        ["ordenes.numero"],
        name="fk_cotizaciones_numero_orden",
        ondelete="CASCADE",
    ),
    CheckConstraint("tipo IN ('Inicial', 'Adicional')", name="ck_cotizaciones_1"),
    CheckConstraint(
        ("(tipo = 'Inicial' AND version = 1) OR (tipo = 'Adicional' AND version >= 2)"),
        name="ck_cotizaciones_2",
    ),
    CheckConstraint(f"estado IN ({_ESTADOS_COTIZACION})", name="ck_cotizaciones_3"),
    CheckConstraint("total >= 0", name="ck_cotizaciones_4"),
    CheckConstraint(
        ("decision_rol IS NULL OR decision_rol IN ('Cliente', 'Responsable de Flotilla')"),
        name="ck_cotizaciones_5",
    ),
    Index("ix_cotizaciones_estado", "estado"),
)

lineas_de_cotizacion = Table(
    "lineas_de_cotizacion",
    metadata,
    Column("id_cotizacion", String(20), nullable=False),
    Column("numero", Integer(), nullable=False, autoincrement=False),
    Column("descripcion", Text(), nullable=False),
    Column("mano_de_obra", _IMPORTE, nullable=False),
    Column("decision", String(20), nullable=True),
    PrimaryKeyConstraint("id_cotizacion", "numero", name="pk_lineas_de_cotizacion"),
    ForeignKeyConstraint(
        ["id_cotizacion"],
        ["cotizaciones.id"],
        name="fk_lineas_de_cotizacion_id_cotizacion",
        ondelete="CASCADE",
    ),
    CheckConstraint("numero >= 1", name="ck_lineas_de_cotizacion_1"),
    CheckConstraint("mano_de_obra >= 0", name="ck_lineas_de_cotizacion_2"),
    CheckConstraint(
        ("decision IS NULL OR decision IN ('Autorizada', 'No Autorizado')"),
        name="ck_lineas_de_cotizacion_3",
    ),
)

refacciones_cotizadas = Table(
    "refacciones_cotizadas",
    metadata,
    Column("id", _ID_AUTOMATICO, nullable=False),
    Column("id_cotizacion", String(20), nullable=False),
    Column("numero_linea", Integer(), nullable=False),
    Column("posicion", Integer(), nullable=False),
    Column("descripcion", String(200), nullable=False),
    Column("cantidad", Integer(), nullable=False),
    Column("precio_unitario", _IMPORTE, nullable=False),
    PrimaryKeyConstraint("id", name="pk_refacciones_cotizadas"),
    ForeignKeyConstraint(
        ["id_cotizacion", "numero_linea"],
        ["lineas_de_cotizacion.id_cotizacion", "lineas_de_cotizacion.numero"],
        name="fk_refacciones_cotizadas_id_cotizacion_numero_linea",
        ondelete="CASCADE",
    ),
    CheckConstraint("cantidad > 0", name="ck_refacciones_cotizadas_1"),
    CheckConstraint("precio_unitario >= 0", name="ck_refacciones_cotizadas_2"),
)

recontactos = Table(
    "recontactos",
    metadata,
    Column("id", _ID_AUTOMATICO, nullable=False),
    Column("id_cotizacion", String(20), nullable=False),
    Column("asesor", String(20), nullable=False),
    Column("registrado_en", FechaUTC(), nullable=False),
    PrimaryKeyConstraint("id", name="pk_recontactos"),
    ForeignKeyConstraint(
        ["id_cotizacion"],
        ["cotizaciones.id"],
        name="fk_recontactos_id_cotizacion",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["asesor"], ["empleados.id"], name="fk_recontactos_asesor", ondelete="RESTRICT"
    ),
)

_ESTADOS_CORREGIBLES = "'Pendiente de Aprobación Gerencial', 'Pendiente de Autorización del Cliente'"

correcciones_de_cotizacion = Table(
    "correcciones_de_cotizacion",
    metadata,
    Column("id", _ID_AUTOMATICO, nullable=False),
    Column("id_cotizacion", String(20), nullable=False),
    Column("asesor", String(20), nullable=False),
    Column("registrada_en", FechaUTC(), nullable=False),
    Column("motivo", Text(), nullable=False),
    Column("total_anterior", _IMPORTE, nullable=False),
    Column("total_nuevo", _IMPORTE, nullable=False),
    Column("estado_anterior", String(50), nullable=False),
    Column("estado_nuevo", String(50), nullable=False),
    Column("fecha_presentacion_anterior", FechaUTC(), nullable=True),
    Column("fecha_aprobacion_gerencial_anterior", FechaUTC(), nullable=True),
    PrimaryKeyConstraint("id", name="pk_correcciones_de_cotizacion"),
    ForeignKeyConstraint(
        ["id_cotizacion"],
        ["cotizaciones.id"],
        name="fk_correcciones_de_cotizacion_id_cotizacion",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["asesor"],
        ["empleados.id"],
        name="fk_correcciones_de_cotizacion_asesor",
        ondelete="RESTRICT",
    ),
    CheckConstraint("total_anterior >= 0", name="ck_correcciones_de_cotizacion_1"),
    CheckConstraint("total_nuevo >= 0", name="ck_correcciones_de_cotizacion_2"),
    CheckConstraint(
        f"estado_anterior IN ({_ESTADOS_CORREGIBLES})", name="ck_correcciones_de_cotizacion_3"
    ),
    CheckConstraint(
        f"estado_nuevo IN ({_ESTADOS_CORREGIBLES})", name="ck_correcciones_de_cotizacion_4"
    ),
)

alertas_internas = Table(
    "alertas_internas",
    metadata,
    Column("id", _ID_AUTOMATICO, nullable=False),
    Column("destinatario", String(20), nullable=True),
    Column("destinatario_rol", String(20), nullable=True),
    Column("tipo", String(50), nullable=False),
    Column("mensaje", Text(), nullable=False),
    Column("numero_orden", String(20), nullable=True),
    Column("id_cotizacion", String(20), nullable=True),
    Column("clave", String(120), nullable=True),
    Column("creada_en", FechaUTC(), nullable=False, server_default=func.now()),
    Column("leida", Boolean(), nullable=False, server_default=false()),
    PrimaryKeyConstraint("id", name="pk_alertas_internas"),
    UniqueConstraint("clave", name="uq_alertas_internas_clave"),
    ForeignKeyConstraint(
        ["destinatario"],
        ["empleados.id"],
        name="fk_alertas_internas_destinatario",
        ondelete="SET NULL",
    ),
    ForeignKeyConstraint(
        ["numero_orden"],
        ["ordenes.numero"],
        name="fk_alertas_internas_numero_orden",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["id_cotizacion"],
        ["cotizaciones.id"],
        name="fk_alertas_internas_id_cotizacion",
        ondelete="CASCADE",
    ),
    CheckConstraint(
        "destinatario IS NOT NULL OR destinatario_rol IS NOT NULL", name="ck_alertas_internas_1"
    ),
    CheckConstraint(
        f"destinatario_rol IS NULL OR destinatario_rol IN ({_ROLES})", name="ck_alertas_internas_2"
    ),
    Index("ix_alertas_destinatario", "destinatario", "leida"),
    Index("ix_alertas_rol", "destinatario_rol", "leida"),
)

eventos = Table(
    "eventos",
    metadata,
    Column("id", _ID_AUTOMATICO, nullable=False),
    Column("tipo", String(60), nullable=False),
    Column("agregado", String(30), nullable=False),
    Column("id_agregado", String(20), nullable=False),
    Column("datos", _JSON, nullable=False, server_default=text("'{}'")),
    Column("ocurrido_en", FechaUTC(), nullable=False),
    Column("registrado_en", FechaUTC(), nullable=False, server_default=func.now()),
    PrimaryKeyConstraint("id", name="pk_eventos"),
    Index("ix_eventos_agregado", "id_agregado"),
    Index("ix_eventos_tipo", "tipo"),
)

secuencias = Table(
    "secuencias",
    metadata,
    Column("nombre", String(30), nullable=False),
    Column("ultimo_valor", Integer(), nullable=False, server_default=text("0")),
    PrimaryKeyConstraint("nombre", name="pk_secuencias"),
    CheckConstraint("ultimo_valor >= 0", name="ck_secuencias_1"),
)

catalogo_servicios = Table(
    "catalogo_servicios",
    metadata,
    Column("recurso_id", String(20), nullable=False),
    Column("descripcion", String(120), nullable=False),
    Column("precio_mxn", _IMPORTE, nullable=False),
    Column("capacidad_o_stock", Integer(), nullable=False),
    Column("habilitado", Boolean(), nullable=False),
    PrimaryKeyConstraint("recurso_id", name="pk_catalogo_servicios"),
    CheckConstraint("precio_mxn >= 0", name="ck_catalogo_servicios_1"),
    CheckConstraint("capacidad_o_stock >= 0", name="ck_catalogo_servicios_2"),
)

servicios_solicitados = Table(
    "servicios_solicitados",
    metadata,
    Column("numero_orden", String(20), nullable=False),
    Column("recurso_id", String(20), nullable=False),
    Column("cantidad", Integer(), nullable=False),
    PrimaryKeyConstraint("numero_orden", "recurso_id", name="pk_servicios_solicitados"),
    ForeignKeyConstraint(
        ["numero_orden"],
        ["ordenes.numero"],
        name="fk_servicios_solicitados_numero_orden",
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["recurso_id"],
        ["catalogo_servicios.recurso_id"],
        name="fk_servicios_solicitados_recurso_id",
        ondelete="RESTRICT",
    ),
    CheckConstraint("cantidad > 0", name="ck_servicios_solicitados_1"),
)

referencia_operaciones_profesor = Table(
    "referencia_operaciones_profesor",
    metadata,
    Column("numero_orden", String(20), nullable=False),
    Column("actor_activo", Boolean(), nullable=False),
    Column("actor_preferente", Boolean(), nullable=False),
    Column("promocion_activa", Boolean(), nullable=False),
    Column("autorizado", Boolean(), nullable=False),
    Column("referencia", String(30), nullable=False),
    PrimaryKeyConstraint("numero_orden", name="pk_referencia_operaciones_profesor"),
    ForeignKeyConstraint(
        ["numero_orden"],
        ["ordenes.numero"],
        name="fk_referencia_operaciones_profesor_numero_orden",
        ondelete="CASCADE",
    ),
)
