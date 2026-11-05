# Plan de implementación por fases — AutoFix Pro (PIA)

Orden en que se construye el sistema a partir de esta documentación. Cada fase termina con pruebas en verde, uno o varios commits y un `git push` (así el historial muestra el avance y, desde la Fase 8, cada push corre el CI). La fase siguiente empieza solo cuando la anterior está terminada. En este archivo, las rutas de documentos son relativas a `docs/` y las de código, a la raíz del repositorio.

**Reglas para todas las fases**

- Antes de escribir código: `git pull`, leer los documentos que indica la fase y proponer un plan (archivos, clases y pruebas) para aprobarlo.
- Los nombres de clases, métodos, estados, eventos, errores y rutas son **exactamente** los de `glosario.md`, `architecture/modelo-de-dominio.md` y `api/README.md`.
- Cada criterio tiene al menos una prueba `test_ca_0XX_…` y cada regla de negocio al menos una `test_rn_XX_…`.
- Antes de cada commit: `ruff check .` sin errores y `pytest` en verde.
- Commits pequeños en español con el formato `tipo(área): descripción` (`feat`, `test`, `fix`, `refactor`, `docs`, `build`, `ci`, `chore`).
- Si la documentación tiene un hueco o una contradicción, se detiene la fase y se decide con el equipo; si cambia algo, el documento se actualiza en el mismo commit.

## Estado de avance

| Fase | Contenido | Estado | Fecha | Último commit |
|---|---|---|---|---|
| 0 | Preparación del repositorio | Terminada | 05/11/2026 | `chore: configurar el proyecto y la estructura de carpetas` |
| 1 | Núcleo compartido del dominio | Terminada | 05/11/2026 | `feat(dominio): eventos de dominio y calendario hábil` |
| 2 | Aggregates, Specifications y máquinas de estados | Pendiente | | |
| 3 | Capa de aplicación y adaptadores en memoria | Pendiente | | |
| 4 | Persistencia con SQLAlchemy y PostgreSQL | Pendiente | | |
| 5 | API REST con FastAPI | Pendiente | | |
| 6 | Pruebas con los datos del profesor y trazabilidad | Pendiente | | |
| 7 | Docker Compose | Pendiente | | |
| 8 | CI/CD con GitHub Actions | Pendiente | | |
| 9 | Despliegue en Render con Supabase | Pendiente | | |
| 10 | P2: documentos PDF y fotos de daños | Pendiente | | |
| 11 | README técnico, evidencias y cierre | Pendiente | | |

---

## Fase 0 — Preparación del repositorio

**Lee:** `architecture/decisiones-tecnicas.md` (§1 a §3 y §7).

**Construye:**
- `pyproject.toml`: proyecto `autofix-pro`, `requires-python >=3.11`; dependencias `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `sqlalchemy>=2`, `psycopg[binary]>=3`, `fpdf2`, `python-multipart`, `tzdata` (Windows no trae las zonas horarias que usa `zoneinfo`); extras `dev` con `pytest`, `pytest-cov`, `httpx` y `ruff` (rangos con límite de versión mayor, como en la U5). Configuración de pytest (`testpaths = ["tests"]`, `pythonpath = ["src"]`), de coverage (`source = ["src"]`, ramas) y de Ruff (`E4, E7, E9, F, W, I, B, UP`, línea de 100, `extend-exclude = ["_referencia"]`). La carpeta local `_referencia/` (código de la U5 y PDF del PIA) está en `.gitignore` y no se sube.
- La estructura de carpetas de `architecture/decisiones-tecnicas.md` §2 con sus `__init__.py`: paquetes raíz `domain`, `application`, `infrastructure` y `api` dentro de `src/` (se importan sin el prefijo `src.`), y `tests/unit/domain`, `tests/unit/application`, `tests/integration`, `tests/api`, `tests/datos_profesor`.
- `.env.example` con todas las variables de `architecture/decisiones-tecnicas.md` §3 y valores de ejemplo (sin secretos reales).
- `tests/test_arquitectura.py`: la regla de dependencias de la U5 adaptada (el dominio no importa `application`, `infrastructure`, `api`, `fastapi`, `pydantic` ni `sqlalchemy`; la aplicación no importa `infrastructure`, `api`, `fastapi` ni `sqlalchemy`; la infraestructura no importa `api`; dentro de `api`, solo `dependencias.py` importa `infrastructure`).
- `README.md` corto en la raíz: nombre del proyecto, equipo y enlace a `docs/` (el completo se hace en la Fase 11).

**Listo cuando:** `pip install -e ".[dev]"` funciona, `ruff check .` sin errores y `pytest` pasa (prueba de arquitectura).

**Commits:** `chore: agregar CLAUDE.md, esquema SQL, scripts y datos del profesor` · `chore: configurar el proyecto y la estructura de carpetas`.

## Fase 1 — Núcleo compartido del dominio (`src/domain/compartido`)

**Lee:** `architecture/modelo-de-dominio.md` §1, §3, §4 (base), §5 (clase genérica) y §7; ADR-006, ADR-007, ADR-016.

**Construye:** `valores.py` (`Dinero` con `Decimal` y `ROUND_HALF_UP`, `NumeroOrden`, `Placas`, `VIN`), `errores.py` (`ErrorDeDominio` y todos los errores de §7 con mensajes para el usuario), `eventos.py` (`EventoDeDominio` inmutable con `ocurrido_en`, `RaizDeAgregado` que registra eventos), `especificacion.py` (`Especificacion[T]` con `es_satisfecha_por`, `y`/`o`/`no` y los operadores `&`, `|`, `~`), `maquina_de_estados.py` (`MaquinaDeEstados[E]` por tabla, estados finales y `validar` que lanza `TransicionDeEstadoNoPermitida`), `calendario.py` (`CalendarioHabil`: lunes a viernes, sin feriados).

**Pruebas:** unitarias de cada Value Object (valores válidos e inválidos), de cada combinador de la Specification (AND, OR, NOT y combinaciones) y de la máquina de estados (transición válida, inválida y desde estado final).

**Commits:** `feat(dominio): value objects y errores compartidos` · `feat(dominio): Specification y máquina de estados genéricas`.

## Fase 2 — Aggregates, Specifications y máquinas de estados

**Lee:** `architecture/modelo-de-dominio.md` completo, `glosario.md` §2 y §3, `gherkin/*.feature` y la sección 2 de `trazabilidad/matriz-trazabilidad.md` (RN-01 a RN-24).

**Construye** en este orden, cada uno con sus pruebas antes de pasar al siguiente:
1. `clientes`, `vehiculos` y `empleados` (Aggregates, Value Objects e interfaces de repositorio).
2. `cotizaciones`: `Cotizacion`, `LineaDeCotizacion`, Value Objects, `EstadoCotizacion` (6 estados) con su tabla de transiciones, eventos y E1 `RequiereAprobacionGerencial`.
3. `ordenes`: `OrdenDeServicio`, `Trabajo`, `SolicitudDeCompra`, `FallaAdicional`, Value Objects (`EstadoDeRecepcion`, `Diagnostico`, `Pago`, `CargoACredito`, `NotaDeResponsabilidad`, `Cancelacion`), `EstadoOrden` (13), `EstadoTrabajo` (4), `EstadoSolicitud` (2), eventos y E3 a E8.
4. `servicios`: `VerificadorDeAutorizante` con E2 `AutorizanteValido`.

Los valores de los enums son los textos del Glosario (por ejemplo `EstadoOrden.EN_DIAGNOSTICO = "En Diagnóstico"`), porque la base los valida con `CHECK`.

**Pruebas (`tests/unit/domain`):** todas las transiciones válidas de las 4 tablas de `architecture/modelo-de-dominio.md` §5 y ejemplos inválidos (incluido «saltar estado»); cada Specification E1–E8 con casos verdaderos y falsos; las notas de comportamiento de §5.1; los eventos que emite cada operación.

**Commits:** uno por Aggregate, por ejemplo `feat(dominio): aggregate Cotización con E1 y su máquina de estados`.

## Fase 3 — Capa de aplicación y adaptadores en memoria

**Lee:** `architecture/patrones.md`, `architecture/diagramas/secuencia-*.png`, ADR-002, ADR-003, ADR-015, ADR-016 y la columna «Caso de uso» de `api/README.md`.

**Construye:**
- `src/application`: `puertos.py` (repositorios, `UnidadDeTrabajo`, `Reloj`, `PublicadorDeEventos`, `GeneradorDeDocumentos`, lector de consultas), `comandos.py`, `resultados.py`, los **12 servicios** de `api/README.md` (de `ServicioDeRecepcion` a `ServicioDeRevisionDePlazos`), las **11 consultas** (CQRS) y `manejadores/alertas.py` (reacciones de `architecture/modelo-de-dominio.md` §6).
- `src/infrastructure/memoria` (repositorios, Unidad de Trabajo y lector en memoria), `infrastructure/reloj.py` y `infrastructure/eventos/publicador_en_proceso.py`.
- La Unidad de Trabajo recolecta los eventos y los publica **solo después de confirmar**; la revisión de plazos es idempotente (ADR-015).

**Pruebas (`tests/unit/application`):** cada servicio con repositorios en memoria y `Mock(spec=…)` para reloj, publicador y PDF; el flujo completo de una orden particular y de una de flotilla; alertas generadas por cada evento; revisión de plazos con reloj falso (E7, E8).

**Commits:** `feat(aplicacion): puertos, comandos y unidad de trabajo` · `feat(aplicacion): servicios de recepción a entrega` · `feat(aplicacion): consultas y manejadores de alertas` · `feat(infraestructura): adaptadores en memoria`.

## Fase 4 — Persistencia con SQLAlchemy y PostgreSQL

**Lee:** `architecture/modelo-de-datos.md`, `database/01_esquema.sql`, ADR-004, ADR-009.

**Construye** (`src/infrastructure`): `config.py` (lee el entorno; convierte `postgresql://` en `postgresql+psycopg://`), `base_de_datos/motor.py`, `tablas.py` (las 18 tablas con SQLAlchemy Core, mismas columnas, tipos, nulos, PK y FK que el SQL), `mapeo.py` (traducción explícita fila ↔ objeto, como en la U5), `repositorios.py`, `unidad_de_trabajo.py` (guarda la bitácora en `eventos` en la misma transacción) y `lector.py` (consultas), con los folios de `secuencias` (OS-0001, COT-0001, REC-0001).

Las restricciones `CHECK` propias de PostgreSQL (por ejemplo, expresiones regulares con `~`) no se ponen en `tablas.py` o se limitan al dialecto PostgreSQL, para que las pruebas con SQLite funcionen. La aplicación **no** crea tablas en producción.

**Pruebas (`tests/integration`):** contrato memoria vs. base de datos para cada repositorio (mismas pruebas con las dos implementaciones); Unidad de Trabajo (confirmar, revertir, eventos publicados solo al confirmar); `tablas.py` coincide con `database/01_esquema.sql`. Corren con SQLite en memoria si no hay `DATABASE_URL` y con PostgreSQL si la hay (Docker o el CI). **Nunca** contra Supabase.

**Commits:** `feat(infraestructura): tablas y mapeo con SQLAlchemy` · `feat(infraestructura): repositorios, unidad de trabajo y lector` · `test(integracion): contrato memoria vs base de datos y esquema`.

## Fase 5 — API REST con FastAPI

**Lee:** `api/README.md` (43 rutas), `architecture/decisiones-tecnicas.md` §4 y §5, ADR-008, ADR-012.

**Construye** (`src/api`): `main.py` (app, routers, `/health`, Swagger con botón *Authorize*), `dependencias.py` (Composition Root), `seguridad.py` (`requiere_rol(*roles)` con `secrets.compare_digest`), `errores.py` (cada `ErrorDeDominio` a su código y el formato `{"error", "detalle", "codigo"}`; JSON mal formado → 400), `esquemas/` (Pydantic; importes como texto con dos decimales) y los 14 archivos de `rutas/`. Las rutas P2 (PDF y fotos) responden `501` por ahora. `api/exportar_openapi.py` escribe `docs/api/openapi.json`.

**Pruebas (`tests/api`, `TestClient`):** cada criterio de aceptación de punta a punta y los códigos 200/201/400/401/403/404/409/422 de cada área; rutas públicas sin token.

**Listo cuando:** `uvicorn api.main:app --reload` (con `src` en el `PYTHONPATH`) muestra las 43 rutas en `/docs`.

**Commits:** uno por grupo de rutas, más `docs(api): exportar openapi.json`.

## Fase 6 — Pruebas con los datos del profesor y trazabilidad

**Lee:** `datos-profesor/README.md`, `datos-profesor/oraculos_casos.csv` y `oraculos_transiciones.csv`, ADR-013, `trazabilidad/matriz-trazabilidad.md`.

**Construye:**
- `tests/datos_profesor/test_casos_prueba.py`: los 120 casos de `datos/profesor/casos_prueba.csv` contra `oraculos_casos.csv`; escribe `reportes/resultados_casos.csv`.
- `tests/datos_profesor/test_transiciones.py`: los 20 casos de `transiciones_prueba.csv` ejecutados con los casos de uso, contra `oraculos_transiciones.csv`; escribe `reportes/resultados_transiciones.csv`.
- `tests/test_trazabilidad.py`: cada `CA-001`…`CA-046` de los `.feature` tiene al menos una prueba `test_ca_0XX_` y cada `RN-01`…`RN-24` una `test_rn_XX_`.

**Listo cuando:** todo en verde y `pytest --cov=src --cov-branch --cov-fail-under=80` pasa (objetivo del equipo: ≥ 90 %).

**Commits:** `test(datos): casos y transiciones del profesor con reportes` · `test: verificación de trazabilidad de criterios y reglas`.

## Fase 7 — Docker Compose

**Lee:** ADR-010.

**Construye:** `Dockerfile` (`python:3.12-slim`, usuario sin privilegios, `PYTHONPATH=/app/src`, `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`), `.dockerignore`, `docker-compose.yml` con **db** (`postgres:16-alpine`, volumen, *healthcheck* y `database/` en `/docker-entrypoint-initdb.d`), **app** (depende de `db` sano, `env_file: .env`, puerto 8000, *healthcheck* `/health`) y **tests** (perfil `tests`, misma imagen con las dependencias de pruebas, corre la suite con cobertura contra `db`).

**Listo cuando:** `docker compose up --build` deja Swagger en `http://localhost:8000/docs` con las 60 órdenes del profesor, y `docker compose --profile tests run --rm tests` pasa.

**Commit:** `build: Dockerfile y docker-compose con db, app y tests`.

## Fase 8 — CI/CD con GitHub Actions

**Lee:** ADR-011, ADR-015.

**Construye:**
- `.github/workflows/ci.yml`: en cada push y pull request instala, corre Ruff y `pytest` con cobertura ≥ 80 % usando un servicio `postgres:16` y publica `htmlcov/`, `coverage.xml` y `reportes/` como artefactos.
- `.github/workflows/revision-de-plazos.yml`: `cron: '0 */6 * * *'` y `workflow_dispatch`; llama `POST $AUTOFIX_API_URL/api/revisiones/plazos` con `TOKEN_SISTEMA` (secretos del repositorio) con reintentos, porque Render gratis tarda en despertar. Si los secretos aún no existen, termina sin error con un aviso.

**Listo cuando:** el push muestra el check verde en GitHub (pestaña Actions).

**Commit:** `ci: pipeline de pruebas y revisión de plazos programada`.

## Fase 9 — Despliegue en Render con Supabase

**Lee:** ADR-009, ADR-011. Los pasos en las páginas de Render y Supabase los hace el equipo; el código solo se ajusta si algo falla.

**Antes de empezar:** `database/02_datos_iniciales.sql` cambió en la Fase 2 (las órdenes importadas ahora traen `fecha_ingreso_a_fila`). Si los scripts ya se habían ejecutado en Supabase, el equipo debe **volver a ejecutar `01_esquema.sql`, `02_datos_iniciales.sql` y `03_verificacion.sql`, en ese orden, en el SQL Editor**. `01` borra y vuelve a crear las tablas, así que se ejecuta a mano y nunca desde pruebas o scripts automáticos.

**Pasos:** Supabase con los tres scripts de `database/` ya ejecutados → Render: *New* → *Web Service* → este repositorio → *Docker* → región *Virginia (US East)* → plan *Free* → variables de entorno (`APP_ENV=produccion`, `DATABASE_URL` = cadena *Session pooler* de Supabase, los 7 tokens, `ZONA_HORARIA`, `LOG_LEVEL`) → *Health Check Path* `/health` → *Auto-Deploy* «After CI Checks Pass». Luego, en GitHub, los secretos `AUTOFIX_API_URL` y `TOKEN_SISTEMA` para la revisión de plazos.

**Listo cuando:** `https://<servicio>.onrender.com/docs` funciona con los datos de Supabase y una ejecución manual de «revisión de plazos» termina en verde.

**Commit:** `docs: agregar la URL de producción`.

## Fase 10 — P2: documentos PDF y fotos de daños

**Lee:** ADR-014, CA-002, CA-005, CA-024, CA-027.

**Construye:** `infrastructure/documentos/generador_pdf.py` (fpdf2) para la cotización, la Nota de Responsabilidad y el recibo interno, y las fotos de daños en `fotos_de_danos` (JPEG o PNG, máximo 5 MB). Las 4 rutas P2 dejan de responder 501.

**Pruebas:** el PDF se genera y contiene los datos clave; foto válida, tipo inválido y tamaño excedido.

**Commit:** `feat: PDF de cotización, nota y recibo, y fotos de daños`. Si no hay tiempo, esta fase se omite y la matriz lo indica (las rutas siguen en 501).

## Fase 11 — README técnico, evidencias y cierre

**Construye:**
- `README.md`: descripción, equipo, arquitectura en breve, requisitos, instalación, ejecución (local y Docker), pruebas y cobertura, variables de entorno, despliegue, URL del repositorio y de producción, insignia del CI, tokens de demostración (solo los de `.env.example`) y un **guion de demostración** paso a paso en Swagger (orden particular completa, rechazo de transición inválida, aprobación gerencial, flotilla con crédito, cancelación y consulta pública).
- `docs/trazabilidad/evidencia-pruebas.md`: cada criterio y regla con el nombre real de sus pruebas y el resultado, generado por un script en `scripts/docs/` a partir de pytest; `docs/api/openapi.json` actualizado; este plan con todas las fases marcadas.

**Listo cuando:** alguien que clona el repositorio puede correrlo siguiendo solo el README.

**Commit:** `docs: README técnico, guion de demostración y evidencia de pruebas`.
