-- =============================================================================
-- AutoFix Pro · Esquema de la base de datos (PostgreSQL 16 / Supabase) · PIA v3.1
-- Generado por scripts/db/esquema.py — no editar a mano: cambie esquema.py y regenere.
--
-- Cómo usarlo:
--   · Supabase: SQL Editor → New query → pegar TODO el archivo → Run.
--   · Docker Compose: se ejecuta solo al crear el volumen de la base (docker-entrypoint-initdb.d).
-- ATENCIÓN: borra y vuelve a crear las tablas de AutoFix Pro (los datos son ficticios).
-- Después ejecute 02_datos_iniciales.sql.
-- =============================================================================

BEGIN;

DROP TABLE IF EXISTS referencia_operaciones_profesor CASCADE;
DROP TABLE IF EXISTS servicios_solicitados CASCADE;
DROP TABLE IF EXISTS catalogo_servicios CASCADE;
DROP TABLE IF EXISTS secuencias CASCADE;
DROP TABLE IF EXISTS eventos CASCADE;
DROP TABLE IF EXISTS alertas_internas CASCADE;
DROP TABLE IF EXISTS correcciones_de_cotizacion CASCADE;
DROP TABLE IF EXISTS recontactos CASCADE;
DROP TABLE IF EXISTS refacciones_cotizadas CASCADE;
DROP TABLE IF EXISTS lineas_de_cotizacion CASCADE;
DROP TABLE IF EXISTS cotizaciones CASCADE;
DROP TABLE IF EXISTS fotos_de_danos CASCADE;
DROP TABLE IF EXISTS fallas_adicionales CASCADE;
DROP TABLE IF EXISTS solicitudes_de_compra CASCADE;
DROP TABLE IF EXISTS trabajos CASCADE;
DROP TABLE IF EXISTS ordenes CASCADE;
DROP TABLE IF EXISTS vehiculos CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;
DROP TABLE IF EXISTS empleados CASCADE;

-- Empleados del taller (Aggregate Empleado). Los tokens de acceso NO se guardan aquí: vienen de variables de entorno (ADR-012).
CREATE TABLE empleados (
    id                           VARCHAR(20) NOT NULL,
    nombre                       VARCHAR(120) NOT NULL,
    rol                          VARCHAR(20) NOT NULL,
    CONSTRAINT pk_empleados PRIMARY KEY (id),
    CONSTRAINT ck_empleados_1 CHECK (rol IN ('Asesor', 'Técnico', 'Gerente', 'Compras', 'Caja'))
);
COMMENT ON TABLE empleados IS 'Empleados del taller (Aggregate Empleado). Los tokens de acceso NO se guardan aquí: vienen de variables de entorno (ADR-012).';
COMMENT ON COLUMN empleados.id IS 'Identificador del empleado (EMP-001…)';
COMMENT ON COLUMN empleados.nombre IS 'Nombre completo';
COMMENT ON COLUMN empleados.rol IS 'RolDeEmpleado';

-- Clientes particulares o de flotilla (Aggregate Cliente).
CREATE TABLE clientes (
    id                           VARCHAR(20) NOT NULL,
    nombre                       VARCHAR(120) NOT NULL,
    telefono                     VARCHAR(20),
    correo                       VARCHAR(120),
    tipo                         VARCHAR(20) NOT NULL DEFAULT 'Particular',
    empresa                      VARCHAR(120),
    responsable_nombre           VARCHAR(120),
    responsable_telefono         VARCHAR(20),
    responsable_correo           VARCHAR(120),
    CONSTRAINT pk_clientes PRIMARY KEY (id),
    CONSTRAINT ck_clientes_1 CHECK (tipo IN ('Particular', 'Flotilla')),
    CONSTRAINT ck_clientes_2 CHECK (tipo = 'Particular' OR (empresa IS NOT NULL AND responsable_nombre IS NOT NULL))
);
CREATE INDEX ix_clientes_empresa ON clientes (empresa);
COMMENT ON TABLE clientes IS 'Clientes particulares o de flotilla (Aggregate Cliente).';
COMMENT ON COLUMN clientes.id IS 'Identificador (AUT-C001 en los datos del profesor)';
COMMENT ON COLUMN clientes.nombre IS 'Nombre del cliente o razón social';
COMMENT ON COLUMN clientes.telefono IS 'Teléfono de contacto';
COMMENT ON COLUMN clientes.correo IS 'Correo de contacto';
COMMENT ON COLUMN clientes.tipo IS 'TipoCliente: Particular o Flotilla';
COMMENT ON COLUMN clientes.empresa IS 'Empresa (solo flotilla)';
COMMENT ON COLUMN clientes.responsable_nombre IS 'Responsable de Flotilla (solo flotilla)';
COMMENT ON COLUMN clientes.responsable_telefono IS 'Teléfono del Responsable de Flotilla';
COMMENT ON COLUMN clientes.responsable_correo IS 'Correo del Responsable de Flotilla';

-- Vehículos (Aggregate Vehículo). Las placas se guardan normalizadas: mayúsculas, sin espacios ni guiones.
CREATE TABLE vehiculos (
    placas                       VARCHAR(15) NOT NULL,
    vin                          CHAR(17) NOT NULL,
    marca                        VARCHAR(60) NOT NULL,
    modelo                       VARCHAR(60) NOT NULL,
    anio                         SMALLINT NOT NULL,
    id_cliente                   VARCHAR(20) NOT NULL,
    CONSTRAINT pk_vehiculos PRIMARY KEY (placas),
    CONSTRAINT uq_vehiculos_vin UNIQUE (vin),
    CONSTRAINT fk_vehiculos_id_cliente FOREIGN KEY (id_cliente) REFERENCES clientes (id) ON DELETE RESTRICT,
    CONSTRAINT ck_vehiculos_1 CHECK (placas ~ '^[A-Z0-9]+$'),
    CONSTRAINT ck_vehiculos_2 CHECK (vin ~ '^[A-HJ-NPR-Z0-9]{17}$'),
    CONSTRAINT ck_vehiculos_3 CHECK (anio BETWEEN 1900 AND 2100)
);
CREATE INDEX ix_vehiculos_cliente ON vehiculos (id_cliente);
COMMENT ON TABLE vehiculos IS 'Vehículos (Aggregate Vehículo). Las placas se guardan normalizadas: mayúsculas, sin espacios ni guiones.';
COMMENT ON COLUMN vehiculos.placas IS 'Placas normalizadas (Value Object Placas)';
COMMENT ON COLUMN vehiculos.vin IS 'Número de serie VIN (17 caracteres, sin I, O ni Q)';
COMMENT ON COLUMN vehiculos.marca IS 'Marca';
COMMENT ON COLUMN vehiculos.modelo IS 'Modelo';
COMMENT ON COLUMN vehiculos.anio IS 'Año del modelo';
COMMENT ON COLUMN vehiculos.id_cliente IS 'Propietario';

-- Órdenes de Servicio (Aggregate Orden de Servicio). Los Value Objects (recepción, diagnóstico, nota, pago, crédito, cancelación) se guardan como columnas.
CREATE TABLE ordenes (
    numero                       VARCHAR(20) NOT NULL,
    id_cliente                   VARCHAR(20) NOT NULL,
    es_cliente_de_flotilla       BOOLEAN NOT NULL DEFAULT FALSE,
    placas                       VARCHAR(15) NOT NULL,
    asesor                       VARCHAR(20) NOT NULL,
    motivo_de_ingreso            TEXT NOT NULL,
    kilometraje                  INTEGER,
    nivel_combustible            VARCHAR(10),
    estado                       VARCHAR(40) NOT NULL DEFAULT 'Recibida',
    fecha_ingreso                TIMESTAMPTZ NOT NULL,
    ultima_actualizacion         TIMESTAMPTZ NOT NULL,
    tecnico_de_diagnostico       VARCHAR(20),
    diagnostico_fallas           TEXT,
    diagnostico_recomendaciones  TEXT,
    diagnostico_registrado_en    TIMESTAMPTZ,
    cotizada                     BOOLEAN NOT NULL DEFAULT FALSE,
    rechazo_total                BOOLEAN NOT NULL DEFAULT FALSE,
    adicionales_pendientes       SMALLINT NOT NULL DEFAULT 0,
    fecha_ingreso_a_fila         TIMESTAMPTZ,
    estado_antes_de_espera       VARCHAR(40),
    nota_fecha_salida            TIMESTAMPTZ,
    nota_firmada                 BOOLEAN NOT NULL DEFAULT FALSE,
    nota_fecha_firma             TIMESTAMPTZ,
    pago_monto                   NUMERIC(12,2),
    pago_forma                   VARCHAR(20),
    pago_registrado_en           TIMESTAMPTZ,
    recibo_numero                VARCHAR(20),
    credito_monto                NUMERIC(12,2),
    credito_registrado_en        TIMESTAMPTZ,
    credito_fecha_vencimiento    DATE,
    fecha_entrega                TIMESTAMPTZ,
    cancelacion_motivo           TEXT,
    cancelacion_registrada_en    TIMESTAMPTZ,
    cancelacion_asesor           VARCHAR(20),
    CONSTRAINT pk_ordenes PRIMARY KEY (numero),
    CONSTRAINT uq_ordenes_recibo_numero UNIQUE (recibo_numero),
    CONSTRAINT fk_ordenes_id_cliente FOREIGN KEY (id_cliente) REFERENCES clientes (id) ON DELETE RESTRICT,
    CONSTRAINT fk_ordenes_placas FOREIGN KEY (placas) REFERENCES vehiculos (placas) ON DELETE RESTRICT,
    CONSTRAINT fk_ordenes_asesor FOREIGN KEY (asesor) REFERENCES empleados (id) ON DELETE RESTRICT,
    CONSTRAINT fk_ordenes_tecnico_de_diagnostico FOREIGN KEY (tecnico_de_diagnostico) REFERENCES empleados (id) ON DELETE RESTRICT,
    CONSTRAINT fk_ordenes_cancelacion_asesor FOREIGN KEY (cancelacion_asesor) REFERENCES empleados (id) ON DELETE RESTRICT,
    CONSTRAINT ck_ordenes_1 CHECK (estado IN ('Recibida', 'En Diagnóstico', 'Cotizada', 'Autorizada', 'En Reparación', 'En Espera de Refacción', 'Pausada por Retiro de Vehículo', 'Lista para Entrega', 'Pagada', 'Por Cobrar (Crédito)', 'Cerrada', 'Cerrada sin Reparación', 'Cancelada')),
    CONSTRAINT ck_ordenes_2 CHECK (estado_antes_de_espera IS NULL OR estado_antes_de_espera IN ('Autorizada', 'En Reparación')),
    CONSTRAINT ck_ordenes_3 CHECK (kilometraje IS NULL OR kilometraje >= 0),
    CONSTRAINT ck_ordenes_4 CHECK (nivel_combustible IS NULL OR nivel_combustible IN ('Reserva', '1/4', '1/2', '3/4', 'Lleno')),
    CONSTRAINT ck_ordenes_5 CHECK (adicionales_pendientes >= 0),
    CONSTRAINT ck_ordenes_6 CHECK (pago_forma IS NULL OR pago_forma IN ('Efectivo', 'Tarjeta', 'Transferencia')),
    CONSTRAINT ck_ordenes_7 CHECK (pago_monto IS NULL OR pago_monto >= 0),
    CONSTRAINT ck_ordenes_8 CHECK (credito_monto IS NULL OR credito_monto >= 0),
    CONSTRAINT ck_ordenes_9 CHECK (NOT (pago_monto IS NOT NULL AND credito_monto IS NOT NULL)),
    CONSTRAINT ck_ordenes_10 CHECK (estado <> 'Cancelada' OR cancelacion_motivo IS NOT NULL)
);
CREATE INDEX ix_ordenes_estado ON ordenes (estado);
CREATE INDEX ix_ordenes_cliente ON ordenes (id_cliente);
CREATE INDEX ix_ordenes_placas ON ordenes (placas);
CREATE INDEX ix_ordenes_pago_fecha ON ordenes (pago_registrado_en);
CREATE UNIQUE INDEX uq_ordenes_una_abierta_por_vehiculo ON ordenes (placas) WHERE estado NOT IN ('Cerrada', 'Cerrada sin Reparación', 'Cancelada');
COMMENT ON TABLE ordenes IS 'Órdenes de Servicio (Aggregate Orden de Servicio). Los Value Objects (recepción, diagnóstico, nota, pago, crédito, cancelación) se guardan como columnas.';
COMMENT ON COLUMN ordenes.numero IS 'Folio (NumeroOrden): OS-0001… o AUT-O001 en los datos del profesor';
COMMENT ON COLUMN ordenes.id_cliente IS 'Cliente';
COMMENT ON COLUMN ordenes.es_cliente_de_flotilla IS 'Copia del tipo de cliente al registrar la orden';
COMMENT ON COLUMN ordenes.placas IS 'Vehículo';
COMMENT ON COLUMN ordenes.asesor IS 'Asesor que registró la orden (recibe sus alertas)';
COMMENT ON COLUMN ordenes.motivo_de_ingreso IS 'Motivo de ingreso';
COMMENT ON COLUMN ordenes.kilometraje IS 'Estado de recepción: kilometraje (sin dato en las órdenes importadas)';
COMMENT ON COLUMN ordenes.nivel_combustible IS 'Estado de recepción: nivel de combustible';
COMMENT ON COLUMN ordenes.estado IS 'EstadoOrden (13 estados del Glosario)';
COMMENT ON COLUMN ordenes.fecha_ingreso IS 'Fecha y hora de ingreso';
COMMENT ON COLUMN ordenes.ultima_actualizacion IS 'Última actualización (consulta del cliente, CA-037)';
COMMENT ON COLUMN ordenes.tecnico_de_diagnostico IS 'Técnico asignado al diagnóstico (CA-035)';
COMMENT ON COLUMN ordenes.diagnostico_fallas IS 'Diagnóstico: fallas encontradas (CA-032)';
COMMENT ON COLUMN ordenes.diagnostico_recomendaciones IS 'Diagnóstico: trabajos y refacciones recomendados';
COMMENT ON COLUMN ordenes.diagnostico_registrado_en IS 'Diagnóstico: fecha y hora';
COMMENT ON COLUMN ordenes.cotizada IS 'Ya tiene cotización (el diagnóstico ya no cambia, CA-033)';
COMMENT ON COLUMN ordenes.rechazo_total IS 'El cliente rechazó toda la cotización (CA-012)';
COMMENT ON COLUMN ordenes.adicionales_pendientes IS 'Cotizaciones adicionales sin decisión (CA-015, CA-018)';
COMMENT ON COLUMN ordenes.fecha_ingreso_a_fila IS 'Lugar en la fila de trabajo (CA-013, CA-025)';
COMMENT ON COLUMN ordenes.estado_antes_de_espera IS 'Estado al que regresa al llegar las refacciones (CA-022)';
COMMENT ON COLUMN ordenes.nota_fecha_salida IS 'Nota de Responsabilidad: salida del vehículo (CA-024)';
COMMENT ON COLUMN ordenes.nota_firmada IS 'Nota de Responsabilidad firmada';
COMMENT ON COLUMN ordenes.nota_fecha_firma IS 'Fecha de la firma';
COMMENT ON COLUMN ordenes.pago_monto IS 'Pago de contado (CA-026)';
COMMENT ON COLUMN ordenes.pago_forma IS 'Forma de pago';
COMMENT ON COLUMN ordenes.pago_registrado_en IS 'Fecha del pago (ingresos del día, CA-031)';
COMMENT ON COLUMN ordenes.recibo_numero IS 'Número del recibo interno (CA-027)';
COMMENT ON COLUMN ordenes.credito_monto IS 'Cargo a crédito de flotilla (CA-039)';
COMMENT ON COLUMN ordenes.credito_registrado_en IS 'Fecha del cargo';
COMMENT ON COLUMN ordenes.credito_fecha_vencimiento IS 'Vencimiento = entrega + 15 días naturales (CA-041)';
COMMENT ON COLUMN ordenes.fecha_entrega IS 'Entrega del vehículo (CA-041, CA-043)';
COMMENT ON COLUMN ordenes.cancelacion_motivo IS 'Motivo de la cancelación (CA-044)';
COMMENT ON COLUMN ordenes.cancelacion_registrada_en IS 'Fecha de la cancelación';
COMMENT ON COLUMN ordenes.cancelacion_asesor IS 'Asesor que canceló';

-- Trabajos de la orden (entidad interna). Se crean al registrar la decisión del cliente.
CREATE TABLE trabajos (
    numero_orden                 VARCHAR(20) NOT NULL,
    id                           INTEGER NOT NULL,
    descripcion                  TEXT NOT NULL,
    importe                      NUMERIC(12,2) NOT NULL,
    estado                       VARCHAR(20) NOT NULL DEFAULT 'Pendiente',
    tecnico                      VARCHAR(20),
    id_cotizacion                VARCHAR(20),
    numero_linea                 INTEGER,
    CONSTRAINT pk_trabajos PRIMARY KEY (numero_orden, id),
    CONSTRAINT fk_trabajos_numero_orden FOREIGN KEY (numero_orden) REFERENCES ordenes (numero) ON DELETE CASCADE,
    CONSTRAINT fk_trabajos_tecnico FOREIGN KEY (tecnico) REFERENCES empleados (id) ON DELETE RESTRICT,
    CONSTRAINT ck_trabajos_1 CHECK (estado IN ('Pendiente', 'En Progreso', 'Completado', 'No Autorizado')),
    CONSTRAINT ck_trabajos_2 CHECK (importe >= 0),
    CONSTRAINT ck_trabajos_3 CHECK (id >= 1)
);
CREATE INDEX ix_trabajos_tecnico ON trabajos (tecnico);
COMMENT ON TABLE trabajos IS 'Trabajos de la orden (entidad interna). Se crean al registrar la decisión del cliente.';
COMMENT ON COLUMN trabajos.numero_orden IS 'Orden';
COMMENT ON COLUMN trabajos.id IS 'Número del trabajo dentro de la orden (1, 2, …)';
COMMENT ON COLUMN trabajos.descripcion IS 'Descripción';
COMMENT ON COLUMN trabajos.importe IS 'Importe (mano de obra + refacciones de la línea)';
COMMENT ON COLUMN trabajos.estado IS 'EstadoTrabajo';
COMMENT ON COLUMN trabajos.tecnico IS 'Técnico asignado (CA-036)';
COMMENT ON COLUMN trabajos.id_cotizacion IS 'Cotización de donde salió';
COMMENT ON COLUMN trabajos.numero_linea IS 'Línea de la cotización de donde salió';

-- Solicitudes de compra de refacciones (entidad interna de la orden).
CREATE TABLE solicitudes_de_compra (
    numero_orden                 VARCHAR(20) NOT NULL,
    id                           INTEGER NOT NULL,
    id_trabajo                   INTEGER NOT NULL,
    refaccion                    VARCHAR(200) NOT NULL,
    cantidad                     INTEGER NOT NULL,
    fecha_solicitud              TIMESTAMPTZ NOT NULL,
    estado                       VARCHAR(20) NOT NULL DEFAULT 'Solicitada',
    fecha_llegada                TIMESTAMPTZ,
    fecha_aviso_al_cliente       TIMESTAMPTZ,
    CONSTRAINT pk_solicitudes_de_compra PRIMARY KEY (numero_orden, id),
    CONSTRAINT fk_solicitudes_de_compra_numero_orden FOREIGN KEY (numero_orden) REFERENCES ordenes (numero) ON DELETE CASCADE,
    CONSTRAINT fk_solicitudes_de_compra_numero_orden_id_trabajo FOREIGN KEY (numero_orden, id_trabajo) REFERENCES trabajos (numero_orden, id) ON DELETE RESTRICT,
    CONSTRAINT ck_solicitudes_de_compra_1 CHECK (estado IN ('Solicitada', 'Disponible')),
    CONSTRAINT ck_solicitudes_de_compra_2 CHECK (cantidad > 0)
);
CREATE INDEX ix_solicitudes_estado ON solicitudes_de_compra (estado);
COMMENT ON TABLE solicitudes_de_compra IS 'Solicitudes de compra de refacciones (entidad interna de la orden).';
COMMENT ON COLUMN solicitudes_de_compra.numero_orden IS 'Orden';
COMMENT ON COLUMN solicitudes_de_compra.id IS 'Número de la solicitud dentro de la orden';
COMMENT ON COLUMN solicitudes_de_compra.id_trabajo IS 'Trabajo autorizado al que pertenece (CA-020)';
COMMENT ON COLUMN solicitudes_de_compra.refaccion IS 'Descripción de la refacción';
COMMENT ON COLUMN solicitudes_de_compra.cantidad IS 'Cantidad';
COMMENT ON COLUMN solicitudes_de_compra.fecha_solicitud IS 'Desde aquí corren los 3 días hábiles (CA-023)';
COMMENT ON COLUMN solicitudes_de_compra.estado IS 'EstadoSolicitud';
COMMENT ON COLUMN solicitudes_de_compra.fecha_llegada IS 'Llegada de la refacción (CA-022)';
COMMENT ON COLUMN solicitudes_de_compra.fecha_aviso_al_cliente IS 'Aviso de retraso al cliente (CA-023)';

-- Fallas adicionales reportadas durante la reparación (CA-034).
CREATE TABLE fallas_adicionales (
    numero_orden                 VARCHAR(20) NOT NULL,
    id                           INTEGER NOT NULL,
    descripcion                  TEXT NOT NULL,
    tecnico                      VARCHAR(20) NOT NULL,
    reportada_en                 TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_fallas_adicionales PRIMARY KEY (numero_orden, id),
    CONSTRAINT fk_fallas_adicionales_numero_orden FOREIGN KEY (numero_orden) REFERENCES ordenes (numero) ON DELETE CASCADE,
    CONSTRAINT fk_fallas_adicionales_tecnico FOREIGN KEY (tecnico) REFERENCES empleados (id) ON DELETE RESTRICT
);
COMMENT ON TABLE fallas_adicionales IS 'Fallas adicionales reportadas durante la reparación (CA-034).';
COMMENT ON COLUMN fallas_adicionales.numero_orden IS 'Orden';
COMMENT ON COLUMN fallas_adicionales.id IS 'Número de la falla dentro de la orden';
COMMENT ON COLUMN fallas_adicionales.descripcion IS 'Descripción de la falla';
COMMENT ON COLUMN fallas_adicionales.tecnico IS 'Técnico que la reportó';
COMMENT ON COLUMN fallas_adicionales.reportada_en IS 'Fecha y hora';

-- Fotos de daños visibles al recibir el vehículo (CA-002, ADR-014). Máximo 5 MB, JPEG o PNG.
CREATE TABLE fotos_de_danos (
    id                           BIGSERIAL NOT NULL,
    numero_orden                 VARCHAR(20) NOT NULL,
    nombre_archivo               VARCHAR(200) NOT NULL,
    tipo_mime                    VARCHAR(20) NOT NULL,
    tamano_bytes                 INTEGER NOT NULL,
    contenido                    BYTEA NOT NULL,
    subida_en                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_fotos_de_danos PRIMARY KEY (id),
    CONSTRAINT fk_fotos_de_danos_numero_orden FOREIGN KEY (numero_orden) REFERENCES ordenes (numero) ON DELETE CASCADE,
    CONSTRAINT ck_fotos_de_danos_1 CHECK (tipo_mime IN ('image/jpeg', 'image/png')),
    CONSTRAINT ck_fotos_de_danos_2 CHECK (tamano_bytes BETWEEN 1 AND 5242880)
);
CREATE INDEX ix_fotos_orden ON fotos_de_danos (numero_orden);
COMMENT ON TABLE fotos_de_danos IS 'Fotos de daños visibles al recibir el vehículo (CA-002, ADR-014). Máximo 5 MB, JPEG o PNG.';
COMMENT ON COLUMN fotos_de_danos.id IS 'Identificador';
COMMENT ON COLUMN fotos_de_danos.numero_orden IS 'Orden';
COMMENT ON COLUMN fotos_de_danos.nombre_archivo IS 'Nombre original';
COMMENT ON COLUMN fotos_de_danos.tipo_mime IS 'image/jpeg o image/png';
COMMENT ON COLUMN fotos_de_danos.tamano_bytes IS 'Tamaño';
COMMENT ON COLUMN fotos_de_danos.contenido IS 'Bytes de la imagen';
COMMENT ON COLUMN fotos_de_danos.subida_en IS 'Fecha';

-- Cotizaciones (Aggregate Cotización). La inicial es v.1; las adicionales v.2 en adelante.
CREATE TABLE cotizaciones (
    id                           VARCHAR(20) NOT NULL,
    numero_orden                 VARCHAR(20) NOT NULL,
    tipo                         VARCHAR(20) NOT NULL,
    version                      SMALLINT NOT NULL,
    estado                       VARCHAR(50) NOT NULL,
    total                        NUMERIC(12,2) NOT NULL,
    generada_en                  TIMESTAMPTZ NOT NULL,
    fecha_aprobacion_gerencial   TIMESTAMPTZ,
    observaciones_del_gerente    TEXT,
    fecha_presentacion           TIMESTAMPTZ,
    decision_autorizante         VARCHAR(120),
    decision_rol                 VARCHAR(30),
    decision_registrada_en       TIMESTAMPTZ,
    CONSTRAINT pk_cotizaciones PRIMARY KEY (id),
    CONSTRAINT uq_cotizaciones_numero_orden_version UNIQUE (numero_orden, version),
    CONSTRAINT fk_cotizaciones_numero_orden FOREIGN KEY (numero_orden) REFERENCES ordenes (numero) ON DELETE CASCADE,
    CONSTRAINT ck_cotizaciones_1 CHECK (tipo IN ('Inicial', 'Adicional')),
    CONSTRAINT ck_cotizaciones_2 CHECK ((tipo = 'Inicial' AND version = 1) OR (tipo = 'Adicional' AND version >= 2)),
    CONSTRAINT ck_cotizaciones_3 CHECK (estado IN ('Pendiente de Aprobación Gerencial', 'Requiere Ajuste', 'Pendiente de Autorización del Cliente', 'Autorizada', 'Autorizada Parcialmente', 'Rechazada')),
    CONSTRAINT ck_cotizaciones_4 CHECK (total >= 0),
    CONSTRAINT ck_cotizaciones_5 CHECK (decision_rol IS NULL OR decision_rol IN ('Cliente', 'Responsable de Flotilla'))
);
CREATE INDEX ix_cotizaciones_estado ON cotizaciones (estado);
COMMENT ON TABLE cotizaciones IS 'Cotizaciones (Aggregate Cotización). La inicial es v.1; las adicionales v.2 en adelante.';
COMMENT ON COLUMN cotizaciones.id IS 'Identificador (COT-0001…)';
COMMENT ON COLUMN cotizaciones.numero_orden IS 'Orden';
COMMENT ON COLUMN cotizaciones.tipo IS 'TipoCotizacion: Inicial o Adicional';
COMMENT ON COLUMN cotizaciones.version IS 'VersionCotizacion';
COMMENT ON COLUMN cotizaciones.estado IS 'EstadoCotizacion (6 estados)';
COMMENT ON COLUMN cotizaciones.total IS 'Suma de las líneas (dato derivado para las consultas)';
COMMENT ON COLUMN cotizaciones.generada_en IS 'Fecha de generación';
COMMENT ON COLUMN cotizaciones.fecha_aprobacion_gerencial IS 'Aprobación del Gerente (CA-008)';
COMMENT ON COLUMN cotizaciones.observaciones_del_gerente IS 'Observaciones del rechazo gerencial (CA-009)';
COMMENT ON COLUMN cotizaciones.fecha_presentacion IS 'Presentación al cliente (inicia las 48 h, CA-006)';
COMMENT ON COLUMN cotizaciones.decision_autorizante IS 'Nombre de quien decidió (CA-010)';
COMMENT ON COLUMN cotizaciones.decision_rol IS 'Cliente o Responsable de Flotilla (CA-029)';
COMMENT ON COLUMN cotizaciones.decision_registrada_en IS 'Fecha y hora de la decisión';

-- Líneas de la cotización (entidad interna): cada trabajo propuesto con su mano de obra.
CREATE TABLE lineas_de_cotizacion (
    id_cotizacion                VARCHAR(20) NOT NULL,
    numero                       INTEGER NOT NULL,
    descripcion                  TEXT NOT NULL,
    mano_de_obra                 NUMERIC(12,2) NOT NULL,
    decision                     VARCHAR(20),
    CONSTRAINT pk_lineas_de_cotizacion PRIMARY KEY (id_cotizacion, numero),
    CONSTRAINT fk_lineas_de_cotizacion_id_cotizacion FOREIGN KEY (id_cotizacion) REFERENCES cotizaciones (id) ON DELETE CASCADE,
    CONSTRAINT ck_lineas_de_cotizacion_1 CHECK (numero >= 1),
    CONSTRAINT ck_lineas_de_cotizacion_2 CHECK (mano_de_obra >= 0),
    CONSTRAINT ck_lineas_de_cotizacion_3 CHECK (decision IS NULL OR decision IN ('Autorizada', 'No Autorizado'))
);
COMMENT ON TABLE lineas_de_cotizacion IS 'Líneas de la cotización (entidad interna): cada trabajo propuesto con su mano de obra.';
COMMENT ON COLUMN lineas_de_cotizacion.id_cotizacion IS 'Cotización';
COMMENT ON COLUMN lineas_de_cotizacion.numero IS 'Número de la línea (1, 2, …)';
COMMENT ON COLUMN lineas_de_cotizacion.descripcion IS 'Trabajo propuesto';
COMMENT ON COLUMN lineas_de_cotizacion.mano_de_obra IS 'Importe de mano de obra';
COMMENT ON COLUMN lineas_de_cotizacion.decision IS 'Autorizada o No Autorizado (CA-010)';

-- Refacciones de cada línea de cotización (Value Object RefaccionCotizada).
CREATE TABLE refacciones_cotizadas (
    id                           BIGSERIAL NOT NULL,
    id_cotizacion                VARCHAR(20) NOT NULL,
    numero_linea                 INTEGER NOT NULL,
    posicion                     INTEGER NOT NULL,
    descripcion                  VARCHAR(200) NOT NULL,
    cantidad                     INTEGER NOT NULL,
    precio_unitario              NUMERIC(12,2) NOT NULL,
    CONSTRAINT pk_refacciones_cotizadas PRIMARY KEY (id),
    CONSTRAINT fk_refacciones_cotizadas_id_cotizacion_numero_linea FOREIGN KEY (id_cotizacion, numero_linea) REFERENCES lineas_de_cotizacion (id_cotizacion, numero) ON DELETE CASCADE,
    CONSTRAINT ck_refacciones_cotizadas_1 CHECK (cantidad > 0),
    CONSTRAINT ck_refacciones_cotizadas_2 CHECK (precio_unitario >= 0)
);
COMMENT ON TABLE refacciones_cotizadas IS 'Refacciones de cada línea de cotización (Value Object RefaccionCotizada).';
COMMENT ON COLUMN refacciones_cotizadas.id IS 'Identificador';
COMMENT ON COLUMN refacciones_cotizadas.id_cotizacion IS 'Cotización';
COMMENT ON COLUMN refacciones_cotizadas.numero_linea IS 'Línea';
COMMENT ON COLUMN refacciones_cotizadas.posicion IS 'Orden dentro de la línea';
COMMENT ON COLUMN refacciones_cotizadas.descripcion IS 'Refacción';
COMMENT ON COLUMN refacciones_cotizadas.cantidad IS 'Cantidad';
COMMENT ON COLUMN refacciones_cotizadas.precio_unitario IS 'Precio unitario';

-- Recontactos al cliente por cotizaciones sin respuesta (CA-040).
CREATE TABLE recontactos (
    id                           BIGSERIAL NOT NULL,
    id_cotizacion                VARCHAR(20) NOT NULL,
    asesor                       VARCHAR(20) NOT NULL,
    registrado_en                TIMESTAMPTZ NOT NULL,
    CONSTRAINT pk_recontactos PRIMARY KEY (id),
    CONSTRAINT fk_recontactos_id_cotizacion FOREIGN KEY (id_cotizacion) REFERENCES cotizaciones (id) ON DELETE CASCADE,
    CONSTRAINT fk_recontactos_asesor FOREIGN KEY (asesor) REFERENCES empleados (id) ON DELETE RESTRICT
);
COMMENT ON TABLE recontactos IS 'Recontactos al cliente por cotizaciones sin respuesta (CA-040).';
COMMENT ON COLUMN recontactos.id IS 'Identificador';
COMMENT ON COLUMN recontactos.id_cotizacion IS 'Cotización';
COMMENT ON COLUMN recontactos.asesor IS 'Asesor que recontactó';
COMMENT ON COLUMN recontactos.registrado_en IS 'Fecha y hora (el plazo de 48 h vuelve a contar)';

-- Historial de correcciones de una cotización antes de la decisión del cliente (CA-047 a CA-050, H-PIA-21, ADR-018).
CREATE TABLE correcciones_de_cotizacion (
    id                           BIGSERIAL NOT NULL,
    id_cotizacion                VARCHAR(20) NOT NULL,
    asesor                       VARCHAR(20) NOT NULL,
    registrada_en                TIMESTAMPTZ NOT NULL,
    motivo                       TEXT NOT NULL,
    total_anterior               NUMERIC(12,2) NOT NULL,
    total_nuevo                  NUMERIC(12,2) NOT NULL,
    estado_anterior              VARCHAR(50) NOT NULL,
    estado_nuevo                 VARCHAR(50) NOT NULL,
    fecha_presentacion_anterior  TIMESTAMPTZ,
    fecha_aprobacion_gerencial_anterior TIMESTAMPTZ,
    CONSTRAINT pk_correcciones_de_cotizacion PRIMARY KEY (id),
    CONSTRAINT fk_correcciones_de_cotizacion_id_cotizacion FOREIGN KEY (id_cotizacion) REFERENCES cotizaciones (id) ON DELETE CASCADE,
    CONSTRAINT fk_correcciones_de_cotizacion_asesor FOREIGN KEY (asesor) REFERENCES empleados (id) ON DELETE RESTRICT,
    CONSTRAINT ck_correcciones_de_cotizacion_1 CHECK (total_anterior >= 0),
    CONSTRAINT ck_correcciones_de_cotizacion_2 CHECK (total_nuevo >= 0),
    CONSTRAINT ck_correcciones_de_cotizacion_3 CHECK (estado_anterior IN ('Pendiente de Aprobación Gerencial', 'Pendiente de Autorización del Cliente')),
    CONSTRAINT ck_correcciones_de_cotizacion_4 CHECK (estado_nuevo IN ('Pendiente de Aprobación Gerencial', 'Pendiente de Autorización del Cliente'))
);
COMMENT ON TABLE correcciones_de_cotizacion IS 'Historial de correcciones de una cotización antes de la decisión del cliente (CA-047 a CA-050, H-PIA-21, ADR-018).';
COMMENT ON COLUMN correcciones_de_cotizacion.id IS 'Identificador';
COMMENT ON COLUMN correcciones_de_cotizacion.id_cotizacion IS 'Cotización';
COMMENT ON COLUMN correcciones_de_cotizacion.asesor IS 'Asesor que corrigió';
COMMENT ON COLUMN correcciones_de_cotizacion.registrada_en IS 'Fecha y hora de la corrección';
COMMENT ON COLUMN correcciones_de_cotizacion.motivo IS 'Motivo de la corrección (obligatorio)';
COMMENT ON COLUMN correcciones_de_cotizacion.total_anterior IS 'Total antes de corregir';
COMMENT ON COLUMN correcciones_de_cotizacion.total_nuevo IS 'Total después de corregir';
COMMENT ON COLUMN correcciones_de_cotizacion.estado_anterior IS 'Estado antes de corregir';
COMMENT ON COLUMN correcciones_de_cotizacion.estado_nuevo IS 'Estado después de corregir (se vuelve a evaluar E1)';
COMMENT ON COLUMN correcciones_de_cotizacion.fecha_presentacion_anterior IS 'Presentación al cliente que se anuló al corregir';
COMMENT ON COLUMN correcciones_de_cotizacion.fecha_aprobacion_gerencial_anterior IS 'Aprobación del Gerente que tenía (se borra si regresa a revisión)';

-- Alertas internas del panel de cada empleado (no son correos ni SMS).
CREATE TABLE alertas_internas (
    id                           BIGSERIAL NOT NULL,
    destinatario                 VARCHAR(20),
    destinatario_rol             VARCHAR(20),
    tipo                         VARCHAR(50) NOT NULL,
    mensaje                      TEXT NOT NULL,
    numero_orden                 VARCHAR(20),
    id_cotizacion                VARCHAR(20),
    clave                        VARCHAR(120),
    creada_en                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    leida                        BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_alertas_internas PRIMARY KEY (id),
    CONSTRAINT uq_alertas_internas_clave UNIQUE (clave),
    CONSTRAINT fk_alertas_internas_destinatario FOREIGN KEY (destinatario) REFERENCES empleados (id) ON DELETE SET NULL,
    CONSTRAINT fk_alertas_internas_numero_orden FOREIGN KEY (numero_orden) REFERENCES ordenes (numero) ON DELETE CASCADE,
    CONSTRAINT fk_alertas_internas_id_cotizacion FOREIGN KEY (id_cotizacion) REFERENCES cotizaciones (id) ON DELETE CASCADE,
    CONSTRAINT ck_alertas_internas_1 CHECK (destinatario IS NOT NULL OR destinatario_rol IS NOT NULL),
    CONSTRAINT ck_alertas_internas_2 CHECK (destinatario_rol IS NULL OR destinatario_rol IN ('Asesor', 'Técnico', 'Gerente', 'Compras', 'Caja'))
);
CREATE INDEX ix_alertas_destinatario ON alertas_internas (destinatario, leida);
CREATE INDEX ix_alertas_rol ON alertas_internas (destinatario_rol, leida);
COMMENT ON TABLE alertas_internas IS 'Alertas internas del panel de cada empleado (no son correos ni SMS).';
COMMENT ON COLUMN alertas_internas.id IS 'Identificador';
COMMENT ON COLUMN alertas_internas.destinatario IS 'Empleado destinatario (o NULL si va a todo un rol)';
COMMENT ON COLUMN alertas_internas.destinatario_rol IS 'Rol destinatario (p. ej. todos los Gerentes)';
COMMENT ON COLUMN alertas_internas.tipo IS 'Tipo de alerta (AprobacionGerencialRequerida, RefaccionRetrasada, …)';
COMMENT ON COLUMN alertas_internas.mensaje IS 'Texto para el usuario';
COMMENT ON COLUMN alertas_internas.numero_orden IS 'Orden relacionada';
COMMENT ON COLUMN alertas_internas.id_cotizacion IS 'Cotización relacionada';
COMMENT ON COLUMN alertas_internas.clave IS 'Evita alertas duplicadas en la revisión de plazos (ADR-015)';
COMMENT ON COLUMN alertas_internas.creada_en IS 'Fecha';
COMMENT ON COLUMN alertas_internas.leida IS 'Si ya se leyó';

-- Bitácora de Domain Events (ADR-016): evidencia de transiciones y pruebas.
CREATE TABLE eventos (
    id                           BIGSERIAL NOT NULL,
    tipo                         VARCHAR(60) NOT NULL,
    agregado                     VARCHAR(30) NOT NULL,
    id_agregado                  VARCHAR(20) NOT NULL,
    datos                        JSONB NOT NULL DEFAULT '{}'::jsonb,
    ocurrido_en                  TIMESTAMPTZ NOT NULL,
    registrado_en                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_eventos PRIMARY KEY (id)
);
CREATE INDEX ix_eventos_agregado ON eventos (id_agregado);
CREATE INDEX ix_eventos_tipo ON eventos (tipo);
COMMENT ON TABLE eventos IS 'Bitácora de Domain Events (ADR-016): evidencia de transiciones y pruebas.';
COMMENT ON COLUMN eventos.id IS 'Identificador';
COMMENT ON COLUMN eventos.tipo IS 'Nombre del evento (OrdenCancelada, CotizacionAutorizada, …)';
COMMENT ON COLUMN eventos.agregado IS 'Orden o Cotizacion';
COMMENT ON COLUMN eventos.id_agregado IS 'Folio o id de la cotización';
COMMENT ON COLUMN eventos.datos IS 'Datos del evento';
COMMENT ON COLUMN eventos.ocurrido_en IS 'Cuándo ocurrió';
COMMENT ON COLUMN eventos.registrado_en IS 'Cuándo se guardó';

-- Folios consecutivos (OS-0001, COT-0001, REC-0001, CLI-0001); se revierten con la transacción.
CREATE TABLE secuencias (
    nombre                       VARCHAR(30) NOT NULL,
    ultimo_valor                 INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT pk_secuencias PRIMARY KEY (nombre),
    CONSTRAINT ck_secuencias_1 CHECK (ultimo_valor >= 0)
);
COMMENT ON TABLE secuencias IS 'Folios consecutivos (OS-0001, COT-0001, REC-0001, CLI-0001); se revierten con la transacción.';
COMMENT ON COLUMN secuencias.nombre IS 'orden, cotizacion, recibo, cliente';
COMMENT ON COLUMN secuencias.ultimo_valor IS 'Último número usado';

-- Catálogo de referencia del profesor (catalogo.csv). No es parte del dominio: sirve para armar cotizaciones de demostración y para rechazar las órdenes con servicios inhabilitados con el puerto `CatalogoDeServicios` (ADR-013, H-PIA-19).
CREATE TABLE catalogo_servicios (
    recurso_id                   VARCHAR(20) NOT NULL,
    descripcion                  VARCHAR(120) NOT NULL,
    precio_mxn                   NUMERIC(12,2) NOT NULL,
    capacidad_o_stock            INTEGER NOT NULL,
    habilitado                   BOOLEAN NOT NULL,
    CONSTRAINT pk_catalogo_servicios PRIMARY KEY (recurso_id),
    CONSTRAINT ck_catalogo_servicios_1 CHECK (precio_mxn >= 0),
    CONSTRAINT ck_catalogo_servicios_2 CHECK (capacidad_o_stock >= 0)
);
COMMENT ON TABLE catalogo_servicios IS 'Catálogo de referencia del profesor (catalogo.csv). No es parte del dominio: sirve para armar cotizaciones de demostración y para rechazar las órdenes con servicios inhabilitados con el puerto `CatalogoDeServicios` (ADR-013, H-PIA-19).';
COMMENT ON COLUMN catalogo_servicios.recurso_id IS 'AUT-P001…';
COMMENT ON COLUMN catalogo_servicios.descripcion IS 'Servicio';
COMMENT ON COLUMN catalogo_servicios.precio_mxn IS 'Precio unitario';
COMMENT ON COLUMN catalogo_servicios.capacidad_o_stock IS 'Dato del profesor sin uso en AutoFix (D-03)';
COMMENT ON COLUMN catalogo_servicios.habilitado IS 'Un servicio inhabilitado no se puede cotizar (D-05)';

-- Detalle de referencia de cada operación del profesor (detalle_operaciones.csv).
CREATE TABLE servicios_solicitados (
    numero_orden                 VARCHAR(20) NOT NULL,
    recurso_id                   VARCHAR(20) NOT NULL,
    cantidad                     INTEGER NOT NULL,
    CONSTRAINT pk_servicios_solicitados PRIMARY KEY (numero_orden, recurso_id),
    CONSTRAINT fk_servicios_solicitados_numero_orden FOREIGN KEY (numero_orden) REFERENCES ordenes (numero) ON DELETE CASCADE,
    CONSTRAINT fk_servicios_solicitados_recurso_id FOREIGN KEY (recurso_id) REFERENCES catalogo_servicios (recurso_id) ON DELETE RESTRICT,
    CONSTRAINT ck_servicios_solicitados_1 CHECK (cantidad > 0)
);
COMMENT ON TABLE servicios_solicitados IS 'Detalle de referencia de cada operación del profesor (detalle_operaciones.csv).';
COMMENT ON COLUMN servicios_solicitados.numero_orden IS 'Orden (operacion_id)';
COMMENT ON COLUMN servicios_solicitados.recurso_id IS 'Servicio del catálogo';
COMMENT ON COLUMN servicios_solicitados.cantidad IS 'Cantidad';

-- Columnas del profesor sin equivalente en el BRD, guardadas solo como referencia para los oráculos (D-01, D-02).
CREATE TABLE referencia_operaciones_profesor (
    numero_orden                 VARCHAR(20) NOT NULL,
    actor_activo                 BOOLEAN NOT NULL,
    actor_preferente             BOOLEAN NOT NULL,
    promocion_activa             BOOLEAN NOT NULL,
    autorizado                   BOOLEAN NOT NULL,
    referencia                   VARCHAR(30) NOT NULL,
    CONSTRAINT pk_referencia_operaciones_profesor PRIMARY KEY (numero_orden),
    CONSTRAINT fk_referencia_operaciones_profesor_numero_orden FOREIGN KEY (numero_orden) REFERENCES ordenes (numero) ON DELETE CASCADE
);
COMMENT ON TABLE referencia_operaciones_profesor IS 'Columnas del profesor sin equivalente en el BRD, guardadas solo como referencia para los oráculos (D-01, D-02).';
COMMENT ON COLUMN referencia_operaciones_profesor.numero_orden IS 'Orden (operacion_id)';
COMMENT ON COLUMN referencia_operaciones_profesor.actor_activo IS 'actores.activo (D-01: AutoFix no lo usa)';
COMMENT ON COLUMN referencia_operaciones_profesor.actor_preferente IS 'actores.es_preferente (D-02)';
COMMENT ON COLUMN referencia_operaciones_profesor.promocion_activa IS 'operaciones.promocion_activa (D-02)';
COMMENT ON COLUMN referencia_operaciones_profesor.autorizado IS 'operaciones.autorizado: 1 = autoriza todo; 0 = rechazo total';
COMMENT ON COLUMN referencia_operaciones_profesor.referencia IS 'operaciones.referencia';

-- Folios iniciales
INSERT INTO secuencias (nombre, ultimo_valor) VALUES ('orden', 0), ('cotizacion', 0), ('recibo', 0), ('cliente', 0);

-- Seguridad para Supabase: la aplicación se conecta con el usuario dueño de las tablas (que no
-- está sujeto a RLS). Activar RLS sin políticas impide leer o escribir estas tablas desde la
-- Data API pública de Supabase con las llaves anon/authenticated. En PostgreSQL local no estorba.
ALTER TABLE empleados ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehiculos ENABLE ROW LEVEL SECURITY;
ALTER TABLE ordenes ENABLE ROW LEVEL SECURITY;
ALTER TABLE trabajos ENABLE ROW LEVEL SECURITY;
ALTER TABLE solicitudes_de_compra ENABLE ROW LEVEL SECURITY;
ALTER TABLE fallas_adicionales ENABLE ROW LEVEL SECURITY;
ALTER TABLE fotos_de_danos ENABLE ROW LEVEL SECURITY;
ALTER TABLE cotizaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE lineas_de_cotizacion ENABLE ROW LEVEL SECURITY;
ALTER TABLE refacciones_cotizadas ENABLE ROW LEVEL SECURITY;
ALTER TABLE recontactos ENABLE ROW LEVEL SECURITY;
ALTER TABLE correcciones_de_cotizacion ENABLE ROW LEVEL SECURITY;
ALTER TABLE alertas_internas ENABLE ROW LEVEL SECURITY;
ALTER TABLE eventos ENABLE ROW LEVEL SECURITY;
ALTER TABLE secuencias ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalogo_servicios ENABLE ROW LEVEL SECURITY;
ALTER TABLE servicios_solicitados ENABLE ROW LEVEL SECURITY;
ALTER TABLE referencia_operaciones_profesor ENABLE ROW LEVEL SECURITY;

COMMIT;
