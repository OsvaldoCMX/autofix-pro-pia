# ADR-009 — PostgreSQL 16: Docker en local y Supabase en producción

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 04/11/2026 (PIA) |
| Trazabilidad | N-01 a N-03, N-11 · CE-01, CE-06 · PIA: persistencia, Docker Compose, despliegue · actualiza ADR-004 |

## Contexto

El «Data Center» es un paquete de CSV y el gestor lo elige el equipo. El PIA pide persistencia en base de datos, Docker Compose con un servicio de base y despliegue en la nube. La U5 ya tiene adaptadores SQLAlchemy 2 (tablas y traducción explícita fila ↔ objeto, sin que el dominio conozca el ORM) y pruebas de contrato. El equipo ya trabajó con Supabase (que es PostgreSQL) y con MySQL.

## Alternativas consideradas

- **SQLite en archivo:** simple, pero el disco de Render es efímero (se pierde al reiniciar) y no hay un servicio de base en Docker Compose.
- **MySQL:** el equipo lo conoce, pero Render no lo ofrece y habría que buscar otro proveedor gratuito.
- **PostgreSQL de Render:** cómodo, pero la base gratuita expira a los 30 días de crearse.
- **PostgreSQL en Supabase** (elegida): el equipo ya conoce su panel, el plan gratuito no expira y permite ver las tablas durante la demostración.

## Decisión

PostgreSQL 16 en todos los ambientes: `postgres:16-alpine` en Docker Compose y en el CI, y un proyecto gratuito de **Supabase** en producción. Acceso con SQLAlchemy 2 (tablas de SQLAlchemy Core y Data Mapper explícito en `mapeo.py`, como en la U5) y psycopg 3. El esquema oficial es `database/01_esquema.sql` (generado por `scripts/db/esquema.py`, documentado en `architecture/modelo-de-datos.md`): 18 tablas, importes `NUMERIC(12,2)`, fechas `TIMESTAMPTZ` en UTC, estados validados con `CHECK` y RLS activado para proteger la Data API de Supabase. Se ejecuta en el SQL Editor de Supabase y, en Docker, automáticamente al crear el volumen (`docker-entrypoint-initdb.d`); la aplicación **no** crea tablas en producción. `src/infrastructure/base_de_datos/tablas.py` refleja el esquema y una prueba de integración lo compara contra PostgreSQL; las pruebas sin Docker usan SQLite en memoria con `metadata.create_all()`. Render se conecta con la cadena **Session pooler** de Supabase (IPv4, puerto 5432) en `DATABASE_URL`; la configuración normaliza el prefijo a `postgresql+psycopg://`.

## Consecuencias

- (+) El mismo gestor en local, CI y producción, y un panel que el equipo ya conoce.
- (+) Se reutilizan los adaptadores y las pruebas de contrato de la U5.
- (+) Las restricciones `CHECK` y las llaves foráneas protegen la integridad aunque alguien edite datos a mano en Supabase.
- (−) El plan gratuito de Supabase pausa el proyecto tras 7 días sin actividad; la revisión de plazos cada 6 horas (ADR-015) lo mantiene activo. Límite de 500 MB, suficiente para la demostración.
- (−) Sin migraciones automáticas: un cambio de esquema se hace en `esquema.py`, se regenera el SQL y se vuelve a ejecutar (los datos son ficticios y se recargan con `02_datos_iniciales.sql`).
