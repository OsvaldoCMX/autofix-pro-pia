# AutoFix Pro — PIA de Componentes de Lógica de Negocio

Sistema de gestión de órdenes de servicio para el taller automotriz ficticio **AutoFix Pro**. Es el proyecto final (PIA) de la materia Componentes de Lógica de Negocio (FIME UANL), profesor Miguel Ángel Gómez Marroquín. **Equipo 6:** Jesus Eduardo Moreno Osoria (2136063) y Osvaldo Salvador Cárdenas Mejorado (2141553). Entrega del repositorio: **06/11/2026**.

El PIA exige: DDD, Specification, State Machine, API REST con Swagger, pruebas unitarias y de integración con cobertura ≥ 80 %, Docker Compose (DB + App + Tests), variables de entorno, CI/CD en GitHub Actions, despliegue funcional y trazabilidad análisis → arquitectura → código → pruebas.

## Reglas de oro

1. **`docs/` es la fuente de verdad.** El código hace exactamente lo que dicen el BRD, las User Stories y los `.feature`, el Glosario, el BPMN, el modelo de dominio, los ADR y el contrato de la API. No inventes reglas, estados, campos, rutas ni pantallas.
2. **Si algo falta o se contradice en `docs/`, detente y pregúntame** antes de decidir. Si acordamos un cambio, actualiza el documento afectado en el mismo commit (y su generador en `scripts/` si lo tiene).
3. **Trabaja por fases** según `docs/plan-de-implementacion.md`. Al empezar una fase, lee su sección y los documentos que indica, propón un plan y espera mi aprobación. No adelantes trabajo de fases posteriores.
4. **Explícame en español sencillo** lo que hiciste al terminar cada tarea: qué archivos creaste, qué reglas cubren, cómo lo probaste y qué sigue. Soy estudiante; no des por hecho que conozco cada herramienta.
5. **Nunca** escribas secretos reales (contraseña de Supabase, tokens reales) en archivos del repositorio, en commits ni en la salida. `.env` es local y está en `.gitignore`; `.env.example` solo lleva valores de ejemplo.

## Dónde está cada cosa (lee solo lo que la tarea necesite)

| Para… | Lee |
|---|---|
| Qué construir y en qué orden | `docs/plan-de-implementacion.md` |
| Aggregates, Value Objects, Specifications E1–E8, máquinas de estados, eventos y errores | `docs/architecture/modelo-de-dominio.md` |
| Stack, estructura, variables de entorno, convenciones de la API, roles y pruebas | `docs/architecture/decisiones-tecnicas.md` |
| Tablas y columnas | `docs/architecture/modelo-de-datos.md` y `database/01_esquema.sql` |
| Las 43 rutas (rol, códigos, caso de uso, criterios) | `docs/api/README.md` |
| Criterios CA-001 a CA-046 | `docs/gherkin/*.feature` y `docs/user-stories.md` |
| Reglas RN-01 a RN-24 y la matriz de trazabilidad | `docs/trazabilidad/matriz-trazabilidad.md` |
| Nombres exactos del negocio y de los estados | `docs/glosario.md` (§2 y §3) |
| Datos del profesor, diferencias y oráculos | `docs/datos-profesor/` y `datos/profesor/` |
| Por qué de cada decisión | `docs/architecture/adr/` (ADR-001 a ADR-016) |
| Patrones y SOLID | `docs/architecture/patrones.md` y `docs/architecture/solid.md` |

`_referencia/` (no se sube a GitHub) tiene el código de la Unidad 5 (`_referencia/u5/`) y el PDF de requisitos del PIA. Úsalo como **ejemplo de estilo y de soluciones ya probadas** (Value Objects, Unidad de Trabajo, mapeo, prueba de arquitectura, pruebas de contrato). Cuando la U5 y `docs/` no coincidan, **gana `docs/`** (la v3.0 corrigió varias reglas: H-PIA-01 a H-PIA-15 en `docs/registro-de-cambios.md`).

## Stack

Python 3.12 (compatible con 3.11) · FastAPI + Pydantic v2 + Uvicorn · SQLAlchemy 2 (Core: `tablas.py` + Data Mapper explícito en `mapeo.py`) · psycopg 3 · PostgreSQL 16 (Docker en local y en el CI, **Supabase** en producción; SQLite en memoria para pruebas sin Docker) · fpdf2 · pytest + pytest-cov + httpx · Ruff · Docker Compose · GitHub Actions · Render.

## Estructura

Detalle completo en `docs/architecture/decisiones-tecnicas.md` §2. Puntos clave:

- `src/domain`, `src/application`, `src/infrastructure`, `src/api`: los paquetes raíz son `domain`, `application`, `infrastructure` y `api` y se importan **sin** el prefijo `src.` (`from domain.ordenes.orden_de_servicio import OrdenDeServicio`). pytest usa `pythonpath = ["src"]`; el Dockerfile define `PYTHONPATH=/app/src`.
- Regla de dependencias: `api → application → domain`; `infrastructure → application/domain`. El dominio no importa FastAPI, Pydantic ni SQLAlchemy. Solo `api/dependencias.py` (Composition Root) decide qué implementación se usa. `tests/test_arquitectura.py` lo verifica.
- Carpetas en inglés (las pide el PIA); **módulos, clases, métodos y variables en español**, con el lenguaje ubicuo del Glosario.

## Convenciones de código

- Estados como `Enum` cuyos valores son los textos del Glosario (`EstadoOrden.POR_COBRAR_CREDITO = "Por Cobrar (Crédito)"`); la base los valida con `CHECK`, así que deben coincidir letra por letra, acentos incluidos.
- Las transiciones de estado solo pasan por la tabla de `MaquinaDeEstados` de cada Aggregate (RN-22). Las guardas son las Specifications E1–E8 combinadas con `&`, `|`, `~`.
- Dinero siempre con `Decimal` (Value Object `Dinero`, 2 decimales, `ROUND_HALF_UP`), nunca `float`. En la API los importes viajan como texto `"1500.00"`.
- Fechas con zona horaria, guardadas en UTC; «hoy» y los días hábiles se calculan en `America/Monterrey`. Días hábiles = lunes a viernes.
- Los errores heredan de `ErrorDeDominio`, con mensajes en español para el usuario del taller; `api/errores.py` los traduce a 404/409/422/403 con el formato `{"error", "detalle", "codigo"}`.
- Domain Events: `dataclass` inmutables; se publican **solo después** de confirmar la Unidad de Trabajo; los manejadores crean alertas y no modifican otros Aggregates.
- Type hints en todo, funciones cortas, sin código muerto ni comentarios obvios. Ruff: `E4, E7, E9, F, W, I, B, UP`, línea de 100.

## Pruebas

- Carpetas: `tests/unit/domain`, `tests/unit/application`, `tests/integration`, `tests/api`, `tests/datos_profesor`.
- Nombres: cada criterio tiene al menos una prueba `test_ca_0XX_…` (por ejemplo `test_ca_044_cancela_orden_recibida_con_motivo`) y cada regla una `test_rn_XX_…`. No cambies el número del criterio o de la regla en el nombre.
- Unitarias sin base de datos (memoria y `Mock(spec=…)`). Integración con SQLite si no hay `DATABASE_URL` y con PostgreSQL de Docker o del CI si la hay. **Nunca ejecutes pruebas ni scripts que borran tablas contra Supabase.**
- Cobertura: `pytest --cov=src --cov-branch --cov-fail-under=80` (objetivo ≥ 90 %).
- No borres ni debilites una prueba para que pase; si una prueba está mal, explícame por qué antes de cambiarla.

## Comandos

El equipo trabaja en **Windows** (VS Code); el CI y Docker son Linux. Usa el Python del entorno virtual por su ruta.

```bash
py -3.12 -m venv .venv                               # una sola vez
.venv/Scripts/python -m pip install -e ".[dev]"      # instalar (repetir si cambia pyproject.toml)
.venv/Scripts/python -m ruff check .                 # estilo y errores
.venv/Scripts/python -m pytest -q                    # pruebas
.venv/Scripts/python -m pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=80
docker compose up --build                            # app + base local (desde la Fase 7)
docker compose --profile tests run --rm tests        # pruebas dentro de Docker
```

## Base de datos y datos del profesor

- El esquema se genera con `scripts/db/esquema.py`: **no edites `database/*.sql` a mano**; edita el script, regenera (`python scripts/db/esquema.py .` y `python scripts/db/generar_datos_iniciales.py datos/profesor database`) y actualiza `src/infrastructure/base_de_datos/tablas.py`. La prueba de integración compara `tablas.py` con el SQL.
- La aplicación no crea tablas en producción; en Supabase el equipo ejecuta los scripts en el SQL Editor.
- `datos/profesor/*.csv` no se modifican (UTF-8 con BOM: lee con `encoding="utf-8-sig"`). Solo se carga el estado inicial (60 órdenes «Recibida»); los cambios de estado se hacen con los casos de uso.
- La carpeta `02_Docente` del paquete del profesor no se usa ni se sube.

## Git

- Rama `main`. Antes de empezar una fase y antes de cada push: `git pull` (mi compañero sube cambios desde GitHub).
- Commits pequeños, en español, formato `tipo(área): descripción` (`feat`, `test`, `fix`, `refactor`, `docs`, `build`, `ci`, `chore`). Cada fase deja varios commits; los mensajes sugeridos están en el plan.
- Antes de cada commit: `ruff check .` sin errores y pruebas en verde. Revisa con `git status` que no se suban `.env`, `.venv/`, `htmlcov/`, `_referencia/` ni archivos temporales.
- Haz commit cuando termines un paso del plan y yo lo apruebe; haz `push` cuando te lo pida o al cerrar la fase.
- Nunca uses `git push --force`, `git reset --hard` ni reescribas el historial.
- Al cerrar una fase, marca su fila en «Estado de avance» de `docs/plan-de-implementacion.md` (estado «Terminada», fecha y mensaje del último commit) e inclúyelo en ese commit.
