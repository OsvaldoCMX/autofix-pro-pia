# AutoFix Pro — PIA de Componentes de Lógica de Negocio

Sistema de gestión de órdenes de servicio para el taller automotriz ficticio **AutoFix Pro**. Es el proyecto final (PIA) de la materia Componentes de Lógica de Negocio (FIME UANL), profesor Miguel Ángel Gómez Marroquín. **Equipo 6:** Jesus Eduardo Moreno Osoria (2136063) y Osvaldo Salvador Cárdenas Mejorado (2141553). Entrega del repositorio: **06/11/2026**.

El PIA exige: DDD, Specification, State Machine, API REST con Swagger, pruebas unitarias y de integración con cobertura ≥ 80 %, Docker Compose (DB + App + Tests), variables de entorno, CI/CD en GitHub Actions, despliegue funcional y trazabilidad análisis → arquitectura → código → pruebas.

**Después de la entrega (Fases 12 a 20).** El repositorio se entregó el 06/11/2026; esa versión quedó marcada con la etiqueta `entrega-2026-11-06` y no se toca. En la revisión del 09/11/2026 vimos que el profesor evalúa usando el sistema **como un usuario del taller**, no en Swagger: busca errores de captura (datos negativos, datos mal capturados que no se pueden corregir) y exige mensajes que entienda alguien que no sabe de computadoras. Nuestro sistema tiene un hueco así: `Cotizacion.ajustar` solo funciona en «Requiere Ajuste», así que una cotización con un dato mal capturado no se puede corregir. Las Fases 12 a 20 agregan una página web para el personal del taller y para el cliente, encima de la API que ya existe, y corrigen esos huecos. Se trabajan en la rama `interfaz-web` y se juntan con `main` solo cuando el equipo lo apruebe.

## Reglas de oro

1. **`docs/` es la fuente de verdad.** El código hace exactamente lo que dicen el BRD, las User Stories y los `.feature`, el Glosario, el BPMN, el modelo de dominio, los ADR y el contrato de la API. No inventes reglas, estados, campos, rutas ni pantallas. Las pantallas se definen en `docs/interfaz-web.md` (se crea en la Fase 13); hasta que el equipo apruebe ese documento, no se programa ninguna pantalla.
2. **Si algo falta o se contradice en `docs/`, detente y pregúntame** antes de decidir. Si acordamos un cambio, actualiza el documento afectado en el mismo commit (y su generador en `scripts/` si lo tiene).
3. **Trabaja por fases** según `docs/plan-de-implementacion.md`. Al empezar una fase, lee su sección y los documentos que indica, propón un plan y espera mi aprobación. No adelantes trabajo de fases posteriores.
4. **Explícame en español sencillo** lo que hiciste al terminar cada tarea: qué archivos creaste, qué reglas cubren, cómo lo probaste y qué sigue. Soy estudiante; no des por hecho que conozco cada herramienta.
5. **Nunca** escribas secretos reales (contraseña de Supabase, tokens reales) en archivos del repositorio, en commits ni en la salida. `.env` es local y está en `.gitignore`; `.env.example` solo lleva valores de ejemplo.
6. **Usuario no técnico.** Todo texto que vea un usuario va en español sencillo, sin códigos HTTP, sin JSON, sin nombres de clases y sin inglés. La página muestra el `detalle` de los errores **tal cual** lo manda la API. Si un mensaje no se entiende, se corrige en el dominio o en `api/errores.py`, no se «traduce» en la página.
7. **La regla vive en el dominio.** Las validaciones de la página (campos obligatorios, números ≥ 0) solo ayudan al usuario; **nunca** sustituyen a las del dominio. La página no calcula reglas del negocio (por ejemplo, no decide si una cotización requiere aprobación gerencial).

## Dónde está cada cosa (lee solo lo que la tarea necesite)

| Para… | Lee |
|---|---|
| Qué construir y en qué orden | `docs/plan-de-implementacion.md` |
| Aggregates, Value Objects, Specifications E1–E8, máquinas de estados, eventos y errores | `docs/architecture/modelo-de-dominio.md` |
| Stack, estructura, variables de entorno, convenciones de la API, roles y pruebas | `docs/architecture/decisiones-tecnicas.md` |
| Tablas y columnas | `docs/architecture/modelo-de-datos.md` y `database/01_esquema.sql` |
| Las 51 rutas (rol, códigos, caso de uso, criterios; las nuevas llevan «Planeado» hasta construirse) | `docs/api/README.md` |
| Criterios CA-001 a CA-066 | `docs/gherkin/*.feature` y `docs/user-stories.md` |
| Reglas RN-01 a RN-35 y la matriz de trazabilidad | `docs/trazabilidad/matriz-trazabilidad.md` |
| Nombres exactos del negocio y de los estados | `docs/glosario.md` (§2 y §3) |
| Datos del profesor, diferencias y oráculos | `docs/datos-profesor/` y `datos/profesor/` |
| Por qué de cada decisión | `docs/architecture/adr/` (ADR-001 a ADR-018) |
| Pantallas de la página web | `docs/interfaz-web.md` |
| Errores de usuario y decisiones del equipo (AU-01 a AU-39) | `docs/auditoria-errores-de-usuario.md` |
| Patrones y SOLID | `docs/architecture/patrones.md` y `docs/architecture/solid.md` |

`_referencia/` (no se sube a GitHub) tiene el código de la Unidad 5 (`_referencia/u5/`) y el PDF de requisitos del PIA. Úsalo como **ejemplo de estilo y de soluciones ya probadas** (Value Objects, Unidad de Trabajo, mapeo, prueba de arquitectura, pruebas de contrato). Cuando la U5 y `docs/` no coincidan, **gana `docs/`** (la v3.0 corrigió varias reglas: H-PIA-01 a H-PIA-20 en `docs/registro-de-cambios.md`).

## Stack

Python 3.12 (compatible con 3.11) · FastAPI + Pydantic v2 + Uvicorn · SQLAlchemy 2 (Core: `tablas.py` + Data Mapper explícito en `mapeo.py`) · psycopg 3 · PostgreSQL 16 (Docker en local y en el CI, **Supabase** en producción; SQLite en memoria para pruebas sin Docker) · fpdf2 · pytest + pytest-cov + httpx · Ruff · Docker Compose · GitHub Actions · Render.

Interfaz web (desde la Fase 15): HTML, CSS y JavaScript sin framework (módulos ES), servida por el mismo FastAPI. Sin Node, sin npm, sin paso de compilación.

## Estructura

Detalle completo en `docs/architecture/decisiones-tecnicas.md` §2. Puntos clave:

- `src/domain`, `src/application`, `src/infrastructure`, `src/api`: los paquetes raíz son `domain`, `application`, `infrastructure` y `api` y se importan **sin** el prefijo `src.` (`from domain.ordenes.orden_de_servicio import OrdenDeServicio`). pytest usa `pythonpath = ["src"]`; el Dockerfile define `PYTHONPATH=/app/src`.
- Regla de dependencias: `api → application → domain`; `infrastructure → application/domain`. El dominio no importa FastAPI, Pydantic ni SQLAlchemy. Solo `api/dependencias.py` (Composition Root) decide qué implementación se usa. `tests/test_arquitectura.py` lo verifica.
- Carpetas en inglés (las pide el PIA); **módulos, clases, métodos y variables en español**, con el lenguaje ubicuo del Glosario.
- La interfaz web vive en `src/api/web/`: es parte de la capa de presentación, así `src/` sigue con sus 4 paquetes y el Dockerfile no cambia. `/docs`, `/openapi.json`, `/health` y `/api/*` deben seguir funcionando igual. La página solo habla con la API; nunca se conecta a Supabase.

## Seguridad de la página

- El inicio de sesión usa la misma clave (token) de cada empleado que ya acepta la API. La clave se guarda en `sessionStorage` (se borra al cerrar la pestaña).
- Nunca se escriben tokens reales en el código de la página (regla 5).

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
- Los criterios nuevos (desde la Fase 13) se prueban con pytest por la API, como siempre. Lo que solo se puede ver en el navegador va en la lista de verificación manual de la Fase 18 (`docs/evidencias/revision-interfaz.md`), no como criterio de aceptación.

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

- Desde la Fase 12 se trabaja en la rama `interfaz-web` (no en `main`); se junta con `main` solo cuando el equipo lo apruebe (Fase 19). Antes de empezar una fase y antes de cada push: `git pull` (mi compañero sube cambios desde GitHub).
- Nunca muevas ni borres la etiqueta `entrega-2026-11-06` (la versión entregada).
- Commits pequeños, en español, formato `tipo(área): descripción` (`feat`, `test`, `fix`, `refactor`, `docs`, `build`, `ci`, `chore`). Cada fase deja varios commits; los mensajes sugeridos están en el plan.
- Antes de cada commit: `ruff check .` sin errores y pruebas en verde. Revisa con `git status` que no se suban `.env`, `.venv/`, `htmlcov/`, `_referencia/` ni archivos temporales.
- Haz commit cuando termines un paso del plan y yo lo apruebe; haz `push` cuando te lo pida o al cerrar la fase.
- Nunca uses `git push --force`, `git reset --hard` ni reescribas el historial.
- Al cerrar una fase, marca su fila en «Estado de avance» de `docs/plan-de-implementacion.md` (estado «Terminada», fecha y mensaje del último commit) e inclúyelo en ese commit.
