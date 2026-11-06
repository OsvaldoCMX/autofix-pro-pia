# Decisiones técnicas — AutoFix Pro (PIA)

Resumen operativo de **cómo** se construye el sistema. El **porqué** de cada decisión está en su ADR (`adr/`). Todas las decisiones están aceptadas por el equipo (04/11/2026); si alguna cambia, se actualiza su ADR.

## 1. Stack

| Elemento | Elección | ADR |
|---|---|---|
| Lenguaje | Python 3.12 (compatible con 3.11) | — |
| API REST | FastAPI + Pydantic v2, servidor Uvicorn; OpenAPI/Swagger automático en `/docs` y `/openapi.json` | ADR-008 |
| Persistencia | SQLAlchemy 2: tablas con SQLAlchemy Core (`tablas.py`) y Data Mapper explícito fila ↔ objeto (`mapeo.py`, como en la U5); el dominio no conoce el ORM | ADR-004, ADR-009 |
| Base de datos | **PostgreSQL 16**: Docker Compose en local y en el CI, **Supabase** en producción; SQLite en memoria solo para pruebas rápidas sin Docker. Esquema oficial en `database/01_esquema.sql` ([modelo de datos](modelo-de-datos.md)) | ADR-009 |
| Driver | psycopg 3 (`postgresql+psycopg://…`) | ADR-009 |
| PDF | fpdf2 (cotización, Nota de Responsabilidad, recibo interno), generados al pedirlos; fotos en la base | ADR-014 |
| Pruebas | pytest, pytest-cov (líneas y ramas), httpx/`TestClient` de FastAPI | ADR-010 |
| Calidad | Ruff (mismas reglas de la U5: `E4, E7, E9, F, W, I, B, UP`, línea de 100) | — |
| Contenedores | Docker + Docker Compose: servicios `db`, `app` y `tests` | ADR-010 |
| CI/CD | GitHub Actions (lint + pruebas + cobertura ≥ 80 % con PostgreSQL como servicio) y despliegue automático en Render desde `main` | ADR-011 |
| Despliegue | Render: Web Service (Docker) conectado a Supabase | ADR-011 |
| Seguridad | Token Bearer sencillo por empleado; cada ruta exige un rol | ADR-012 |

## 2. Estructura del repositorio

Las carpetas siguen la estructura que pide el PIA (en inglés); los **nombres de clases, métodos y archivos internos siguen en español** porque son el lenguaje ubicuo del Glosario.

```
autofix-pro/
├── docs/                      ← este paquete (BRD, US, Gherkin, BPMN, arquitectura, API, trazabilidad)
├── src/
│   ├── domain/                ← modelo de dominio puro (sin FastAPI ni SQLAlchemy)
│   │   ├── compartido/        valores, errores, eventos, especificacion, maquina_de_estados, calendario
│   │   ├── ordenes/           orden_de_servicio, trabajo, solicitud_de_compra, falla_adicional, valores, estados, eventos, especificaciones, repositorio
│   │   ├── cotizaciones/      cotizacion, linea_de_cotizacion, valores, estados, eventos, especificaciones, repositorio
│   │   ├── clientes/          cliente, especificaciones, repositorio
│   │   ├── vehiculos/         vehiculo, repositorio
│   │   ├── empleados/         empleado, repositorio
│   │   └── servicios/         verificador_de_autorizante
│   ├── application/           ← casos de uso (Service Layer), comandos, consultas, puertos, manejadores de eventos
│   │   ├── servicios/         servicio_de_recepcion … servicio_de_revision_de_plazos (12)
│   │   ├── consultas/         consultas, vistas, lector
│   │   ├── manejadores/       alertas (reaccionan a Domain Events)
│   │   ├── comandos.py · resultados.py · puertos.py · unidad_de_trabajo.py
│   ├── infrastructure/        ← adaptadores
│   │   ├── base_de_datos/     tablas, mapeo, repositorios, unidad_de_trabajo, lector, motor
│   │   ├── memoria/           repositorios y UoW en memoria (pruebas unitarias)
│   │   ├── documentos/        generador_pdf
│   │   ├── eventos/           publicador_en_proceso
│   │   ├── config.py · reloj.py
│   └── api/                   ← FastAPI
│       ├── main.py · dependencias.py (composition root) · seguridad.py · errores.py
│       ├── esquemas/          modelos Pydantic de entrada y salida
│       └── rutas/             recepcion, diagnostico, cotizaciones, autorizacion, reparacion, refacciones,
│                              retiro, caja, entrega, cancelacion, consultas, alertas, revisiones, salud
├── tests/
│   ├── unit/domain/ · unit/application/ · integration/ · api/ · datos_profesor/
│   └── conftest.py
├── database/                  ← 01_esquema.sql · 02_datos_iniciales.sql · 03_verificacion.sql
├── datos/profesor/            ← CSV del paquete 01_Alumno (sin cambios; UTF-8 con BOM)
├── reportes/                  ← resultados generados por las pruebas (CSV de casos y transiciones)
├── scripts/                   ← docs/ (generan US, Gherkin, matriz, ADR) · db/ (generan el esquema y los datos iniciales)
├── .github/workflows/         ci.yml · revision-de-plazos.yml
├── Dockerfile · docker-compose.yml · .env.example · pyproject.toml · README.md
```

**Regla de dependencias:** `api → application → domain` e `infrastructure → application/domain`. El dominio no importa nada de las otras capas; la composición (qué implementación se usa) vive solo en `api/dependencias.py` (Composition Root). Una prueba de arquitectura (como la de la U5) verifica estas dependencias.

## 3. Variables de entorno (12-Factor)

Toda la configuración viene del entorno; `.env.example` se sube al repositorio **sin secretos reales** y `.env` está en `.gitignore`.

**Arranque sin `DATABASE_URL`:** en `desarrollo` y `pruebas` la aplicación usa los adaptadores en memoria con los 6 empleados de §6 (los datos se pierden al reiniciar), para poder probarla en Swagger sin base de datos. En `produccion` no arranca y muestra un mensaje claro.

| Variable | Ejemplo en `.env.example` | Uso |
|---|---|---|
| `APP_ENV` | `desarrollo` | `desarrollo`, `pruebas` o `produccion`. |
| `DATABASE_URL` | `postgresql+psycopg://autofix:cambia-esta-clave@db:5432/autofix` | Conexión a la base. En Render se pone la cadena **Session pooler** de Supabase (`postgresql://postgres.<ref>:<clave>@<servidor>.pooler.supabase.com:5432/postgres`); la configuración cambia el prefijo a `postgresql+psycopg://`. |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `autofix` / `cambia-esta-clave` / `autofix` | Solo para el servicio `db` de Docker Compose. |
| `TOKEN_ASESOR`, `TOKEN_TECNICO`, `TOKEN_TECNICO_2`, `TOKEN_GERENTE`, `TOKEN_COMPRAS`, `TOKEN_CAJA` | `cambia-este-token-asesor`, … | Token de cada empleado de demostración (ADR-012). |
| `TOKEN_SISTEMA` | `cambia-este-token-sistema` | Solo para `POST /api/revisiones/plazos` (ADR-015). |
| `ZONA_HORARIA` | `America/Monterrey` | Para «ingresos del día» y los días hábiles. Las fechas se guardan en UTC. |
| `PORT` | `8000` | Puerto de Uvicorn (Render lo define). |
| `LOG_LEVEL` | `info` | Nivel de bitácora. |

## 4. Convenciones de la API

- Prefijo `/api`; recursos en español, en plural y con guiones: `/api/ordenes/{numero}/solicitudes-de-compra`.
- Las **acciones** del negocio se exponen como sub-recursos con `POST` (p. ej. `/cotizaciones/{id}/presentacion`, `/ordenes/{numero}/entrega`), porque cada una es un caso de uso con reglas propias y no un simple cambio de campo.
- Códigos: **201** crea algo (orden, cotización, solicitud, pago…), **200** acción o consulta, **400** JSON mal formado, **401** falta el token o no es válido, **403** el rol no puede usar la ruta (o el trabajo es de otro técnico), **404** no existe, **409** viola una regla o transición del negocio, **422** un dato es inválido (ADR-008).
- Formato de error único: `{"error": "EntregaNoPermitida", "detalle": "No se puede entregar el vehículo de la orden AUT-O006 (estado «Autorizada»): primero debe registrarse el pago o el cargo a crédito.", "codigo": 409}`.
- Importes como texto decimal con dos decimales (`"12887.00"`), nunca `float`. Fechas en ISO 8601 con zona.
- Las «pantallas» de los criterios de aceptación (p. ej. «Nueva Orden», «Consulta tu vehículo») se representan con sus endpoints; para la demostración se usa Swagger UI.
- El contrato completo planeado está en [`../api/README.md`](../api/README.md); el `openapi.json` real se exporta a `docs/api/openapi.json` cuando la API esté implementada.

## 5. Roles y permisos

| Rol | Puede |
|---|---|
| Asesor | Recepción, clientes, cancelación, asignaciones, cotizaciones (generar, presentar, ajustar, recontactar), decisión del cliente, avisos al cliente, retiro y reactivación, entrega. |
| Técnico | Su panel, diagnóstico, fallas adicionales, iniciar/completar **sus** trabajos, solicitudes de compra. |
| Gerente | Revisión gerencial, cotizaciones por aprobar, listado de órdenes, ingresos del día, expediente. |
| Compras | Solicitudes pendientes y registro de llegada. |
| Caja | Pago, cargo a crédito, recibo interno. |
| Sistema | Solo la revisión de plazos. |
| Público | Consulta de estado (sin token) y `/health`. |

## 6. Datos de demostración

La base se prepara con tres scripts de `database/` (en Supabase: SQL Editor; en Docker: automáticamente al crear el volumen):

1. `01_esquema.sql` — crea las 18 tablas (borra las anteriores; los datos son ficticios).
2. `02_datos_iniciales.sql` — 6 empleados de demostración y el **estado inicial** de los datos del profesor: 40 clientes, 60 vehículos, 60 órdenes «Recibida», 20 servicios de catálogo y 117 líneas de detalle. Los cambios de estado se hacen después con la API, como pide el paquete del profesor.
3. `03_verificacion.sql` — muestra los conteos obtenidos contra los esperados.

| Empleado | Nombre (ficticio) | Rol | Token (variable) |
|---|---|---|---|
| EMP-001 | Laura Méndez | Asesor | `TOKEN_ASESOR` |
| EMP-002 | Carlos Ruiz | Técnico | `TOKEN_TECNICO` |
| EMP-003 | Diego Salinas | Técnico | `TOKEN_TECNICO_2` |
| EMP-004 | Patricia Garza | Gerente | `TOKEN_GERENTE` |
| EMP-005 | Jorge Treviño | Compras | `TOKEN_COMPRAS` |
| EMP-006 | Sofía Leal | Caja | `TOKEN_CAJA` |
| — | Sistema | (revisión de plazos) | `TOKEN_SISTEMA` |

Las reglas de conversión y las diferencias con el modelo del profesor están en ADR-013 y [`../datos-profesor/README.md`](../datos-profesor/README.md). Las pruebas no dependen de esta carga: crean sus propios datos y leen los CSV de `datos/profesor/` para los 120 casos y las 20 transiciones.

## 7. Estrategia de pruebas

| Nivel | Carpeta | Qué prueba | Implementación |
|---|---|---|---|
| Unitarias de dominio | `tests/unit/domain` | Value Objects, Specifications (cada pieza y cada combinación), máquinas de estados (todas las transiciones válidas y ejemplos inválidos), Aggregates y eventos. | Sin base de datos. |
| Unitarias de aplicación | `tests/unit/application` | Cada servicio con repositorios en memoria; mocks (`Mock(spec=…)`) para reloj, publicador y PDF. | Memoria. |
| Integración | `tests/integration` | Repositorios y Unidad de Trabajo con SQLAlchemy; pruebas de contrato memoria vs. base de datos (Liskov, como en la U5); `tablas.py` coincide con `database/01_esquema.sql`. | PostgreSQL en Docker/CI; SQLite si no hay `DATABASE_URL`. |
| API | `tests/api` | Cada criterio de aceptación de punta a punta con `TestClient`, incluidos los códigos 200/201/400/401/403/404/409/422. | Base de pruebas. |
| Datos del profesor | `tests/datos_profesor` | Los 120 casos de `casos_prueba.csv` y las 20 transiciones de `transiciones_prueba.csv`; escribe `reportes/resultados_casos.csv` y `reportes/resultados_transiciones.csv`. | Base de pruebas. |

**Convención de nombres:** cada criterio tiene al menos una prueba cuyo nombre empieza con `test_ca_0XX_` (p. ej. `test_ca_044_cancela_orden_recibida_con_motivo`), y cada regla de negocio al menos una con `test_rn_XX_`. Así la [matriz de trazabilidad](../trazabilidad/matriz-trazabilidad.md) se puede comprobar con una búsqueda (`pytest --collect-only -q | grep test_ca_044`).

**Cobertura:** `pytest --cov=src --cov-branch --cov-fail-under=80`; el objetivo del equipo es ≥ 90 % (en la U5 se logró 99.5 % de líneas). El reporte HTML (`htmlcov/`) y el XML se publican como artefacto del CI.

## 8. Alcance de implementación

- **P1 (obligatorio en el PIA):** todo el flujo de la orden, las 8 Specifications, las 4 máquinas de estados, los Domain Events con sus alertas, la revisión de plazos, las consultas, la seguridad por roles, la carga de los datos del profesor y sus pruebas.
- **P2 (si el tiempo lo permite):** generación de PDF (cotización, Nota de Responsabilidad, recibo) y fotos de daños. Mientras no estén, las rutas P2 responden `501 Not Implemented` con un mensaje claro y la matriz de trazabilidad lo indica en la columna «Prioridad».
