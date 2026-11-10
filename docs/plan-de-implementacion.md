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
| 2 | Aggregates, Specifications y máquinas de estados | Terminada | 05/11/2026 | `docs: cerrar la Fase 2` |
| 3 | Capa de aplicación y adaptadores en memoria | Terminada | 05/11/2026 | `docs: cerrar la Fase 3` |
| 4 | Persistencia con SQLAlchemy y PostgreSQL | Terminada | 05/11/2026 | `docs: cerrar la Fase 4` |
| 5 | API REST con FastAPI | Terminada | 05/11/2026 | `docs: cerrar la Fase 5` |
| 6 | Pruebas con los datos del profesor y trazabilidad | Terminada | 05/11/2026 | `docs: cerrar la Fase 6` |
| 7 | Docker Compose | Terminada | 05/11/2026 | `docs: cerrar la Fase 7` |
| 8 | CI/CD con GitHub Actions | Terminada | 05/11/2026 | `docs: cerrar la Fase 8` |
| 9 | Despliegue en Render con Supabase | Terminada | 06/11/2026 | `docs: agregar la URL de producción` |
| 10 | P2: documentos PDF y fotos de daños | Omitida | 06/11/2026 | `docs: registrar la omisión de la Fase 10` |
| 11 | README técnico, evidencias y cierre | Terminada | 06/11/2026 | `docs: README técnico, guion de demostración y evidencia de pruebas` |
| 12 | Auditoría «¿y si me equivoco?» | Terminada | 09/11/2026 | `docs: decisiones del equipo en la auditoría` |
| 13 | Documentar la interfaz web y las correcciones aprobadas | Terminada | 09/11/2026 | `docs: cerrar la Fase 13` |
| 14 | Correcciones en el dominio y la API | Terminada | 10/11/2026 | `docs: cerrar la Fase 14` |
| 15 | Base de la interfaz web | Terminada | 10/11/2026 | `docs: cerrar la Fase 15` |
| 16 | Pantallas del Asesor | Pendiente | — | — |
| 17 | Pantallas de Técnico, Gerente, Compras y Caja | Pendiente | — | — |
| 18 | Revisión como usuario del taller | Pendiente | — | — |
| 19 | Despliegue de la interfaz en Render y datos limpios en Supabase | Pendiente | — | — |
| 20 | README, guion de demostración y reporte | Pendiente | — | — |

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
2. `cotizaciones`: `Cotizacion`, `LineaDeCotizacion`, Value Objects, `EstadoCotizacion` (6 estados) con su tabla de transiciones, eventos, E1 `RequiereAprobacionGerencial` y E8 `RequiereRecontacto` (su candidato es la cotización).
3. `ordenes`: `OrdenDeServicio`, `Trabajo`, `SolicitudDeCompra`, `FallaAdicional`, Value Objects (`EstadoDeRecepcion`, `Diagnostico`, `Pago`, `CargoACredito`, `NotaDeResponsabilidad`, `Cancelacion`), `EstadoOrden` (13), `EstadoTrabajo` (4), `EstadoSolicitud` (2), eventos y E3 a E7.
4. `servicios`: `VerificadorDeAutorizante` con E2 `AutorizanteValido`.

Los valores de los enums son los textos del Glosario (por ejemplo `EstadoOrden.EN_DIAGNOSTICO = "En Diagnóstico"`), porque la base los valida con `CHECK`.

**Pruebas (`tests/unit/domain`):** todas las transiciones válidas de las 4 tablas de `architecture/modelo-de-dominio.md` §5 y ejemplos inválidos (incluido «saltar estado»); cada Specification E1–E8 con casos verdaderos y falsos; las notas de comportamiento de §5.1; los eventos que emite cada operación.

**Commits:** uno por Aggregate, por ejemplo `feat(dominio): aggregate Cotización con E1 y su máquina de estados`.

## Fase 3 — Capa de aplicación y adaptadores en memoria

**Lee:** `architecture/patrones.md`, `architecture/diagramas/secuencia-*.png`, ADR-002, ADR-003, ADR-015, ADR-016 y la columna «Caso de uso» de `api/README.md`.

**Construye:**
- `src/application`: `puertos.py` (`Reloj`, `PublicadorDeEventos`, `GeneradorDeDocumentos`, `AlertaInterna`, `RepositorioDeAlertas`), `unidad_de_trabajo.py`, `comandos.py`, `resultados.py`, los **12 servicios** de `api/README.md` (de `ServicioDeRecepcion` a `ServicioDeRevisionDePlazos`, sin sus métodos P2, que se construyen en la Fase 10), las **11 consultas** (CQRS, con `LectorDeOrdenes` en `consultas/lector.py`) y `manejadores/alertas.py` (reacciones de `architecture/modelo-de-dominio.md` §6).
- `src/infrastructure/memoria` (repositorios, Unidad de Trabajo y lector en memoria), `infrastructure/reloj.py` y `infrastructure/eventos/publicador_en_proceso.py`.
- La Unidad de Trabajo recolecta los eventos y guarda la bitácora; el servicio los publica **solo después de confirmar**, como en los diagramas de secuencia; la revisión de plazos es idempotente (ADR-015).

**Pruebas (`tests/unit/application`):** cada servicio con repositorios en memoria y `Mock(spec=…)` para reloj y publicador; el flujo completo de una orden particular y de una de flotilla; alertas generadas por cada evento; revisión de plazos con reloj falso (E7, E8).

**Commits:** `feat(aplicacion): puertos, comandos y unidad de trabajo` · `feat(infraestructura): adaptadores en memoria` (antes que los servicios, porque sus pruebas los usan) · `feat(aplicacion): servicios de recepción a entrega` · `feat(aplicacion): consultas y manejadores de alertas`.

## Fase 4 — Persistencia con SQLAlchemy y PostgreSQL

**Lee:** `architecture/modelo-de-datos.md`, `database/01_esquema.sql`, ADR-004, ADR-009.

**Construye** (`src/infrastructure`): `config.py` (lee el entorno; convierte `postgresql://` en `postgresql+psycopg://`), `base_de_datos/motor.py`, `tablas.py` (las 18 tablas con SQLAlchemy Core, mismas columnas, tipos, nulos, PK y FK que el SQL), `mapeo.py` (traducción explícita fila ↔ objeto, como en la U5), `repositorios.py`, `unidad_de_trabajo.py` (guarda la bitácora en `eventos` en la misma transacción) y `lector.py` (consultas), con los folios de `secuencias` (OS-0001, COT-0001, REC-0001, CLI-0001).

Las restricciones `CHECK` propias de PostgreSQL (por ejemplo, expresiones regulares con `~`) no se ponen en `tablas.py` o se limitan al dialecto PostgreSQL, para que las pruebas con SQLite funcionen. La aplicación **no** crea tablas en producción.

**Pruebas (`tests/integration`):** contrato memoria vs. base de datos para cada repositorio (mismas pruebas con las dos implementaciones); Unidad de Trabajo (confirmar, revertir, eventos publicados solo al confirmar); `tablas.py` coincide con `database/01_esquema.sql`. Corren con SQLite en memoria si no hay `DATABASE_URL` y con PostgreSQL si la hay (Docker o el CI). **Nunca** contra Supabase.

**Commits:** `feat(infraestructura): tablas y mapeo con SQLAlchemy` · `feat(infraestructura): repositorios, unidad de trabajo y lector` · `test(integracion): contrato memoria vs base de datos y esquema`.

## Fase 5 — API REST con FastAPI

**Lee:** `api/README.md` (43 rutas), `architecture/decisiones-tecnicas.md` §4 y §5, ADR-008, ADR-012.

**Construye** (`src/api`): `main.py` (app, routers, `/health`, Swagger con botón *Authorize*), `dependencias.py` (Composition Root), `seguridad.py` (`requiere_rol(*roles)` con `secrets.compare_digest`), `errores.py` (cada `ErrorDeDominio` a su código y el formato `{"error", "detalle", "codigo"}`; JSON mal formado → 400), `esquemas/` (Pydantic; importes como texto con dos decimales) y los 14 archivos de `rutas/`. Las rutas P2 (PDF y fotos) responden `501` por ahora. `api/exportar_openapi.py` escribe `docs/api/openapi.json`.

**Pruebas (`tests/api`, `TestClient`):** cada criterio de aceptación de punta a punta y los códigos 200/201/400/401/403/404/409/422 de cada área; rutas públicas sin token. `test_ca_027_` comprueba que la ruta del recibo responde 501 hasta que se haga la Fase 10.

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

**Antes de empezar:** `database/02_datos_iniciales.sql` cambió en la Fase 2 (las órdenes importadas ahora traen `fecha_ingreso_a_fila`) y `01_esquema.sql` y `03_verificacion.sql` en la Fase 3 (secuencia `cliente`). Si los scripts ya se habían ejecutado en Supabase, el equipo debe **volver a ejecutar `01_esquema.sql`, `02_datos_iniciales.sql` y `03_verificacion.sql`, en ese orden, en el SQL Editor**. `01` borra y vuelve a crear las tablas, así que se ejecuta a mano y nunca desde pruebas o scripts automáticos.

**Pasos:** Supabase con los tres scripts de `database/` ya ejecutados → Render: *New* → *Web Service* → este repositorio → *Docker* → región *Virginia (US East)* → plan *Free* → variables de entorno (`APP_ENV=produccion`, `DATABASE_URL` = cadena *Session pooler* de Supabase, los 7 tokens, `ZONA_HORARIA`, `LOG_LEVEL`) → *Health Check Path* `/health` → *Auto-Deploy* «After CI Checks Pass». Luego, en GitHub, los secretos `AUTOFIX_API_URL` y `TOKEN_SISTEMA` para la revisión de plazos.

**Listo cuando:** `https://<servicio>.onrender.com/docs` funciona con los datos de Supabase y una ejecución manual de «revisión de plazos» termina en verde.

**Commit:** `docs: agregar la URL de producción`.

## Fase 10 — P2: documentos PDF y fotos de daños

**Lee:** ADR-014, CA-002, CA-005, CA-024, CA-027.

**Construye:** `infrastructure/documentos/generador_pdf.py` (fpdf2) para la cotización, la Nota de Responsabilidad y el recibo interno, y las fotos de daños en `fotos_de_danos` (JPEG o PNG, máximo 5 MB). Los métodos de servicio `ServicioDeCotizacion.generar_pdf`, `ServicioDeRetiro.generar_pdf_de_nota`, `ServicioDeCaja.generar_recibo` (con `ReciboInterno` y su folio REC-0001) y `ServicioDeRecepcion.adjuntar_foto`. Las 4 rutas P2 dejan de responder 501.

**Pruebas:** el PDF se genera y contiene los datos clave; foto válida, tipo inválido y tamaño excedido.

**Commit:** `feat: PDF de cotización, nota y recibo, y fotos de daños`. Si no hay tiempo, esta fase se omite y la matriz lo indica (las rutas siguen en 501).

## Fase 11 — README técnico, evidencias y cierre

**Construye:**
- `README.md`: descripción, equipo, arquitectura en breve, requisitos, instalación, ejecución (local y Docker), pruebas y cobertura, variables de entorno, despliegue, URL del repositorio y de producción, insignia del CI, tokens de demostración (solo los de `.env.example`) y un **guion de demostración** paso a paso en Swagger (orden particular completa, rechazo de transición inválida, aprobación gerencial, flotilla con crédito, cancelación y consulta pública).
- `docs/trazabilidad/evidencia-pruebas.md`: cada criterio y regla con el nombre real de sus pruebas y el resultado, generado por un script en `scripts/docs/` a partir de pytest; `docs/api/openapi.json` actualizado; este plan con todas las fases marcadas.

**Listo cuando:** alguien que clona el repositorio puede correrlo siguiendo solo el README.

**Commit:** `docs: README técnico, guion de demostración y evidencia de pruebas`.

---

# Fases 12 a 20 — Interfaz web y correcciones después de la revisión del 09/11/2026

La versión entregada el 06/11/2026 quedó en la etiqueta `entrega-2026-11-06` y no se toca. En la revisión del 09/11/2026 vimos que el profesor evalúa usando el sistema como un usuario del taller: busca errores de captura que no se pueden corregir y mensajes que no entiende alguien que no sabe de computadoras. Estas fases agregan una página web para el personal del taller y para el cliente, encima de la API, y corrigen esos huecos. Se trabajan en la rama `interfaz-web`; se juntan con `main` en la Fase 19.

**Reglas adicionales para estas fases**

- La página vive en `src/api/web/` y la sirve el mismo FastAPI (HTML, CSS y JavaScript con módulos ES; sin Node, sin npm y sin compilación). Solo habla con la API.
- Todo texto que ve un usuario va en español sencillo, sin códigos HTTP, JSON, nombres de clases ni inglés. La página muestra el `detalle` de los errores tal cual; si un mensaje no se entiende, se corrige en el dominio o en `src/api/errores.py`.
- Las validaciones de la página solo ayudan al usuario; las reglas viven en el dominio.
- `user-stories.md`, `gherkin/*.feature`, `trazabilidad/matriz-trazabilidad.md`, `api/README.md` y los ADR **se generan** con los scripts de `scripts/docs/` (`datos.py`, `rutas.py`, `gen_adr.py`): se edita el script y se regenera, nunca el Markdown a mano. Lo mismo con el esquema (`scripts/db/esquema.py`).
- **Docker local con datos:** Docker Desktop no monta `database/` desde la USB (`I:`); para verificar la página con las 60 órdenes se usa una copia del repositorio en un disco fijo (`C:`), como advierte el README. El perfil `tests` sí funciona desde la USB.

## Fase 12 — Auditoría «¿y si me equivoco?»

**Objetivo:** encontrar, antes que el profesor, los pasos donde un usuario se equivoca y el sistema no lo deja corregir, o donde el mensaje no se entiende. **Esta fase no escribe código.**

**Lee:** `user-stories.md`, `gherkin/*.feature`, `glosario.md`, `api/README.md`, `architecture/modelo-de-dominio.md` y el código de `src/domain`, `src/api/esquemas` y `src/api/errores.py`.

**Construye** `docs/auditoria-errores-de-usuario.md` con una tabla por actor (Asesor, Técnico, Gerente, Compras, Caja, Cliente). Por cada paso del proceso:

| Paso | Error posible del usuario | Qué hace hoy el sistema (con archivo y línea) | ¿Se puede corregir? | ¿El mensaje se entiende? | Propuesta | Prioridad |
|---|---|---|---|---|---|---|

Revisa como mínimo:
- **Datos mal capturados:** nombre, teléfono o correo del cliente; placas, VIN, año, kilometraje, nivel de combustible; técnico equivocado al asignar el diagnóstico o los trabajos; diagnóstico con un error; cotización con un importe o una descripción mal; trabajos marcados por error en la decisión del cliente; refacción solicitada por error; forma de pago equivocada; llegada de refacción registrada por error.
- **Datos absurdos:** negativos, ceros, textos vacíos o solo espacios, textos larguísimos, años imposibles, importes con más de 2 decimales, letras donde van números, placas con caracteres raros.
- **Acciones repetidas o fuera de orden:** doble clic en guardar, registrar dos veces lo mismo, saltarse pasos, usar la función de otro puesto.
- **Cada mensaje de error que puede salir:** ¿lo entiende alguien que no sabe de computadoras? ¿dice qué pasó y qué hacer?

La prioridad es **Alta** si el profesor lo puede encontrar en una demo de 10 minutos, **Media** si es raro y **Baja** si es cosmético. La corrección de cotizaciones ya está decidida por el equipo (09/11/2026); se anota como **H-PIA-21** (el último hallazgo de `registro-de-cambios.md` es H-PIA-20).

**Listo cuando:** el equipo revisó la tabla y marcó qué propuestas se hacen. **Se detiene la fase y se espera la decisión del equipo** antes de la Fase 13.

**Commit:** `docs: auditoría de errores de usuario`.

## Fase 13 — Documentar la interfaz web y las correcciones aprobadas

**Objetivo:** que `docs/` diga exactamente qué se va a construir, antes de programar. **Esta fase no escribe código de la aplicación** (sí edita los generadores de `scripts/docs/`).

**Lee:** `auditoria-errores-de-usuario.md` con las decisiones del equipo, `scripts/docs/README.md`, `architecture/modelo-de-dominio.md` §5.2 (máquina de la cotización), RN-04 y RN-05, CA-005 a CA-009, ADR-005, ADR-007 y ADR-012.

**Construye:**
- `docs/interfaz-web.md`:
  - Principios: usuario no técnico, botones con verbos claros («Registrar llegada del vehículo»), estados con los nombres del Glosario, montos como `$1,500.00`, fechas `dd/mm/aaaa hh:mm` en America/Monterrey, confirmación antes de acciones que no se deshacen (cancelar, registrar decisión del cliente, pago, cargo a crédito, entrega), botón de guardar deshabilitado mientras se envía (evita el doble clic).
  - Mensajes: de éxito (el `mensaje` de la API o uno corto), de error (el `detalle` tal cual), sin conexión o con Render despertando («El sistema está iniciando, espere unos segundos e intente de nuevo») y sesión vencida (regresa al inicio de sesión con un aviso).
  - Pantallas por puesto. Por cada una: qué ve el usuario, qué botones tiene, en qué estados aparece cada botón, qué ruta de la API llama y qué criterios cubre. Mínimo:
    - **Inicio:** «Consulta tu vehículo» (cliente, sin clave) y «Entrar como personal del taller».
    - **Inicio de sesión:** solo pide la clave de acceso y saluda con nombre y puesto.
    - **Asesor:** buscar por placas, registrar cliente y orden, expediente de la orden, asignar técnico, generar, corregir y presentar cotización, registrar recontacto, decisión del cliente, asignar trabajos, cotización adicional, aviso de retraso de refacción, retiro anticipado (salida, firma y reactivación), entrega, entrega sin reparación, cancelación, alertas.
    - **Técnico:** su fila de trabajo, registrar diagnóstico, iniciar y terminar trabajos, solicitar refacción, reportar falla adicional, alertas.
    - **Gerente:** cotizaciones por aprobar (aprobar, o rechazar con observaciones), listado de órdenes con filtro por estado, ingresos del día, alertas.
    - **Compras:** solicitudes pendientes con días hábiles y registrar llegada.
    - **Caja:** buscar la orden, registrar pago de contado o cargo a crédito según el tipo de cliente.
    - El token de Sistema (revisión de plazos) no tiene pantalla. Las funciones P2 (PDF y fotos, Fase 10 omitida) no aparecen en la página.
- Ruta nueva `GET /api/sesion` (en `scripts/docs/rutas.py`, que regenera `api/README.md`): con una clave válida devuelve nombre y puesto del empleado; sin clave o con una clave inválida responde 401 con mensaje claro.
- La corrección de cotizaciones y los cambios aprobados en la Fase 12, con la numeración que sigue a la existente: User Stories desde **US-026**, criterios desde **CA-047**, reglas desde **RN-25**, hallazgos desde **H-PIA-21**, **ADR-017** (interfaz web) y **ADR-018** (corrección de cotizaciones). Se editan:
  - Generadores: `scripts/docs/datos.py` (US, CA, RN, Gherkin y matriz), `scripts/docs/rutas.py` (rutas nuevas) y `scripts/docs/gen_adr.py` (ADR-017, ADR-018 y el índice `architecture/adr/README.md`); después se corren `gen_historias.py`, `gen_trazabilidad.py` y `gen_adr.py`.
  - A mano: `BRD.md`, `glosario.md`, `architecture/modelo-de-dominio.md` (estados, transiciones, eventos y errores), `architecture/decisiones-tecnicas.md` (§2, carpeta `src/api/web/`) y `registro-de-cambios.md`.
  - `CLAUDE.md`: los rangos de la tabla «Dónde está cada cosa» (número de rutas, CA, RN y ADR).
  - Si el BPMN cambia, solo se anota en `bpmn/README.md` qué cambiaría; no se edita el PDF de Lucidchart.
- **Decisiones del equipo sobre la corrección de cotizaciones (09/11/2026)**, que estos documentos deben recoger:
  - La hace solo el Asesor, con motivo obligatorio, y aplica solo en «Pendiente de Aprobación Gerencial» y «Pendiente de Autorización del Cliente». En «Requiere Ajuste» se sigue usando `ajustar` (CA-009) y **RN-05 no cambia**. En «Autorizada», «Autorizada Parcialmente» y «Rechazada» no se corrige: para trabajo nuevo existe la cotización adicional (N-06).
  - Se guardan asesor, fecha y hora, motivo, total anterior y total nuevo; la cotización conserva su número y su versión.
  - Después de corregir se vuelve a evaluar E1. Transición nueva: «Pendiente de Autorización del Cliente» → «Pendiente de Aprobación Gerencial». Corregir una cotización en «Pendiente de Aprobación Gerencial» que sigue arriba de $15,000 no es una transición: se queda en ese estado y solo cambian sus líneas.
  - Al corregir, `fecha_presentacion` vuelve a vacío y el asesor la puede presentar otra vez. Los recontactos anteriores se conservan como historial, pero el plazo de 48 horas (E8) solo cuenta desde la nueva presentación y los recontactos posteriores a ella. El detalle se define en esta fase.
  - Por decidir en esta fase: qué pasa con `fecha_aprobacion_gerencial` (CA-008) cuando la cotización regresa a revisión (propuesta: se borra y el historial de la corrección guarda el dato anterior).

**Listo cuando:** los scripts de `scripts/docs/` corren sin errores de conteo y el equipo aprueba `docs/interfaz-web.md` y los criterios nuevos.

**Commits:** `docs: interfaz web y ADR-017` · `docs: corrección de cotizaciones (H-PIA-21, ADR-018)` · uno por cada otra corrección aprobada.

**Resultado (09/11/2026).** Hallazgos H-PIA-21 a H-PIA-29 (`registro-de-cambios.md` §6), necesidad N-16, US-026 y US-027, CA-047 a CA-066, RN-25 a RN-35, ADR-017 y ADR-018, 8 rutas nuevas (51 en total) y `interfaz-web.md`. Todo lo nuevo lleva la marca **«Planeado»** (matriz, contrato de la API y tabla de errores del modelo de dominio) para que el CI siga en verde: las pruebas no le exigen prueba, ruta ni error, pero fallan si ya existe. Se hicieron los commits de los hallazgos antes que el de la interfaz para que `interfaz-web.md` pudiera citar todas las rutas.

## Fase 14 — Correcciones en el dominio y la API

**Lee:** lo que se aprobó en la Fase 13.

**Orden de prioridad (09/11/2026).** Si se acaba el tiempo, se recorta **desde abajo**; lo que se recorte se queda documentado como «Planeado».

| # | Corrección | Criterios y reglas | Rutas |
|---|---|---|---|
| 1 | H-PIA-21: corrección de cotizaciones (AU-17) | CA-047 a CA-051 · RN-25, RN-26 | `POST /api/cotizaciones/{id}/correcciones` (y el historial en `GET /api/cotizaciones/{id}`) |
| 2 | H-PIA-22: una sola orden abierta por vehículo (AU-06), con índice único parcial y prueba de integración: si la base rechaza un segundo registro simultáneo, la API responde el **mismo 409** `VehiculoConOrdenAbierta`, nunca un 500 | CA-052 · RN-27 | 409 en `POST /api/ordenes` |
| 3 | H-PIA-23: lista de técnicos (AU-13) | CA-053 · RN-28 | `GET /api/tecnicos` |
| 4 | H-PIA-23: cambio del técnico de diagnóstico (AU-12) | CA-054 · RN-28 | la misma `asignacion-diagnostico` |
| 5 | Expediente completo (`interfaz-web.md` §7): `GET /api/ordenes/{numero}` agrega el nombre y el tipo del cliente (y su Responsable de Flotilla), la marca, el modelo y el año del vehículo y el nombre del técnico asignado; lo necesita la página en las Fases 16 y 17. Se documenta en el contrato de la API y lleva su prueba | — | la misma `GET /api/ordenes/{numero}` |
| 6 | H-PIA-24: correcciones de datos: cliente (AU-02), vehículo (AU-03), recepción (AU-05) y forma de pago (AU-34) | CA-055 a CA-058 · RN-29, RN-30 | 4 rutas `PUT` |
| 7 | Cambios chicos, en este orden: H-PIA-25 (AU-08 a AU-11, AU-18), H-PIA-26 (AU-20, AU-28 a), H-PIA-27 (AU-15, AU-16), H-PIA-28 (AU-04 a, AU-19, AU-27, AU-38, AU-39) | CA-059 a CA-065 · RN-31 a RN-34 | 409 en `POST /api/clientes` |
| 8 | H-PIA-29: corrección de placas, **P2**, solo si sobra tiempo (AU-01) | CA-066 · RN-35 | `PUT /api/ordenes/{numero}/placas` |

`GET /api/sesion` también está planeada, pero se construye en la Fase 15.

**Al construir cada corrección, quitar su marca «Planeado»:** `planeado=True` del criterio y la regla en `REGLAS_PLANEADAS` (`scripts/docs/datos.py`); `P1_PLANEADA` → `"P1"` en `scripts/docs/rutas.py`, y en las rutas que ya existían, pasar el 409 de la nota «*Planeado (H-PIA-xx):*» a la columna de errores; «409 · Planeado» → «409» en la tabla de errores de `architecture/modelo-de-dominio.md` §7. Después se regeneran los documentos. Las pruebas de trazabilidad, de contrato y de errores fallan mientras quede una marca sobre algo ya construido. Además:
- Si la corrección de placas no se construye, su ruta se agrega como las demás P2 (responde 501), su prioridad pasa de `P2_PLANEADA` a `"P2"` y no aparece en la página.
- CA-064 cambia el mensaje de flotilla que hoy revisa la prueba de CA-029: hay que actualizar esa prueba y explicarlo en el commit (no se debilita, cambia el texto esperado).
- Las pruebas que registran dos órdenes del mismo vehículo sin cerrar la primera chocarán con RN-27; se ajusta su preparación (cerrar o cancelar la primera) y se explica en el commit.

**Construye** la corrección de cotizaciones y las demás correcciones aprobadas, por capas como siempre:
- Dominio: método en `src/domain/cotizaciones/cotizacion.py`, transiciones nuevas en `MAQUINA_DE_COTIZACION` (`src/domain/cotizaciones/estados.py`), evento `CotizacionCorregida` en `eventos.py` y el error que corresponda.
- Aplicación: método en `ServicioDeCotizacion` y su comando en `src/application/comandos.py`; manejador de alertas si la Fase 13 lo pide.
- Infraestructura: tabla nueva del historial de correcciones en `scripts/db/esquema.py`, SQL y `architecture/modelo-de-datos.md` regenerados (`python scripts/db/esquema.py .` y `python scripts/db/generar_datos_iniciales.py datos/profesor database`), `tablas.py`, `mapeo.py`, repositorios en memoria y en base de datos.
- API: ruta en `src/api/rutas/cotizaciones.py`, esquema en `src/api/esquemas/cotizaciones.py` y mensajes; `docs/api/openapi.json` con `api/exportar_openapi.py`.

**Pruebas:** `test_ca_0XX_` y `test_rn_XX_` de cada criterio y regla nuevos en dominio, aplicación, integración y API (los rangos de `tests/test_trazabilidad.py` ya llegan a CA-066 y RN-35 desde la Fase 13; lo que cambia es que se quitan las marcas «Planeado»). Integración también contra PostgreSQL 16 local en Docker (`docker compose --profile tests run --rm tests`). **Nunca contra Supabase.** Al final, `scripts/docs/gen_evidencia.py` regenera `trazabilidad/evidencia-pruebas.md`.

**Listo cuando:** todo en verde, cobertura ≥ 90 % y los criterios nuevos aparecen en la evidencia.

**Commits:** uno por corrección (`feat(cotizacion): corregir una cotización antes de la decisión del cliente`, …).

**Resultado (10/11/2026).** Se construyeron los 8 puntos del orden de prioridad, con `push` al terminar cada uno; no hubo que recortar nada, así que la corrección de placas (P2) también quedó construida y ya no responde 501. Solo `GET /api/sesion` sigue marcada «Planeado» porque es de la Fase 15. Decisiones durante la fase:
- RN-27 con los datos del profesor: los 60 vehículos ya tienen una orden «Recibida», así que para abrirles otra primero se cierra o se cancela la suya. Las pruebas de cliente recurrente (CA-003) cancelan primero la visita anterior; los 120 casos y las 20 transiciones siguen con «coincide = SI» y sin cambiar los oráculos (decisión del equipo).
- Las reglas de captura nuevas (teléfono, correo, año, kilometraje, largo de textos, trabajos de más de $0.00) solo se aplican al capturar o corregir; lo guardado se lee tal cual, y una prueba abre el expediente de las 60 órdenes de los datos iniciales (condición del equipo). Los datos del profesor cumplen todas las reglas nuevas.
- El VIN de otro vehículo al corregir responde 422, como al registrar (el contrato decía 409).
- El teléfono se guarda como se capturó (sin espacios en los extremos); los textos de 1,000 caracteres se revisan en los esquemas de la API, igual que los demás largos de columna.
- Pruebas que cambiaron sin debilitarse: la máquina de la cotización (transición nueva), `test_esquema` (19 tablas, índices únicos con su condición y `ON UPDATE`), las de CA-003 y la de la numeración de adicionales (RN-27 y RN-33), la de CA-029 (mensaje nuevo de CA-064) y los teléfonos de los datos de prueba (10 dígitos).
- Verificado con SQLite y con PostgreSQL 16 en Docker, cargando `01`, `02` y `03` por la entrada estándar; nunca contra Supabase.

## Fase 15 — Base de la interfaz web

**Construye:**
- En `src/api/main.py`: servir la página de `src/api/web/` en `/` sin romper `/docs`, `/openapi.json`, `/health` ni `/api/*`. Navegación con `#` en la URL (por ejemplo `#/asesor/orden/OS-0001`) para que recargar la página no dé 404.
- `GET /api/sesion` (de la Fase 13) en `src/api/rutas/sesion.py` y `src/api/esquemas/sesion.py`, usando `src/api/seguridad.py`.
- `src/api/web/`: `index.html`, `estilos.css` y módulos JS: `api.js` (todas las llamadas, el token y el manejo de errores en un solo lugar), `sesion.js`, `formato.js` (dinero y fechas; el dinero se maneja como texto o centavos, nunca con sumas de `float`), `ui.js` (mensajes, confirmaciones, botones ocupados) y un archivo por puesto (`asesor.js`, `tecnico.js`, `gerente.js`, `compras.js`, `caja.js`, `cliente.js`).
- Pantalla de inicio, consulta pública del cliente (CA-037, CA-038), inicio de sesión, menú según el puesto y cerrar sesión.
- Diseño limpio y legible en laptop y tablet: letras grandes, botones grandes, colores por estado de la orden y nada de texto técnico.

**Pruebas (`tests/api`):** `/` responde HTML; los archivos estáticos se sirven; `/docs`, `/openapi.json` y `/health` siguen respondiendo; `GET /api/sesion` con cada rol, sin clave y con clave inválida; `tests/test_arquitectura.py` sigue pasando.

**Listo cuando:** en Docker local se puede consultar una orden como cliente y entrar con la clave de cada puesto.

**Commits:** `feat(web): servir la interfaz y la consulta pública` · `feat(api): ruta de sesión` · `feat(web): inicio de sesión y menú por puesto`.

**Resultado (10/11/2026).** Se construyeron P-01 (inicio), P-02 (consulta pública), P-03 (inicio de sesión), el menú de cada puesto con «Cerrar sesión» siempre visible y `GET /api/sesion`; ya no queda ninguna ruta «Planeado». Las pantallas de cada puesto dicen «Esta pantalla estará disponible pronto.» hasta las Fases 16 y 17. Decisiones del equipo durante la fase:
- `GET /api/sesion` responde `id_empleado`, `nombre`, `rol` (el valor del código) y `puesto` (el nombre del Glosario §1). Con la clave de Sistema responde 403 del mismo tipo `RolNoPermitido`, con un mensaje propio («Esta clave es del sistema automático, no de un empleado del taller…»); las demás rutas conservan el suyo. En el contrato, el caso de uso pasa de `ConsultarSesion` a `seguridad.requiere_empleado`, que es quien identifica al empleado (no hace falta una consulta en la capa de aplicación).
- Dirección nueva `#/gerente/ingresos` (G-03) y archivo nuevo `principal.js` (lee la dirección y muestra la pantalla), anotados en `interfaz-web.md` §3 y §8 y en `decisiones-tecnicas.md` §2.
- Los archivos de la página se sirven en `/web/…` (no en `/`) para que una dirección que no existe siga respondiendo el 404 de siempre, con `Cache-Control: no-cache`; ni `/` ni `/web/…` aparecen en Swagger.
- Si un puesto abre la dirección de otro, regresa a su menú con el aviso «Esa pantalla es de otro puesto del taller. Le mostramos su menú.» (`interfaz-web.md` §3). Al recargar, la página vuelve a revisar la clave con la API.
- Verificado: 2275 pruebas con SQLite y 2306 con PostgreSQL 16 en Docker (perfil `tests`), cobertura 99.80 %; recorrido del inicio de sesión, la consulta, el cambio de puesto, recargar, cerrar sesión y sin conexión en Chrome sin ventana, sin errores de JavaScript. La prueba con la aplicación de Docker Compose y los datos del profesor la hace el equipo desde una copia en `C:` (desde la USB `I:` Docker monta `database/` vacía).

## Fase 16 — Pantallas del Asesor

**Construye** las pantallas del Asesor de `docs/interfaz-web.md`, con sus confirmaciones y mensajes. En la cotización, la página puede mostrar un total preliminar mientras se captura, pero el total oficial y la regla de $15,000 (E1) los decide la API.

**Pruebas:** si una pantalla necesita algo que la API no da (por ejemplo, un dato en el expediente), se agrega a la API con su prueba y se documenta en `scripts/docs/rutas.py`; no se resuelve con trucos en la página. La revisión visual va en la lista de la Fase 18.

**Listo cuando:** en Docker local se completan, solo desde la página, los escenarios 1, 3, 4 y 5 del guion de demostración del `README.md` en la parte del Asesor.

**Commits:** uno por grupo de pantallas (`feat(web): recepción y expediente`, `feat(web): cotizaciones y decisión del cliente`, …).

## Fase 17 — Pantallas de Técnico, Gerente, Compras y Caja

**Construye** las pantallas de esos cuatro puestos de `docs/interfaz-web.md` y la campana de alertas para todos.

**Listo cuando:** los 6 escenarios del guion del `README.md` se completan de punta a punta solo desde la página, cambiando de puesto con cerrar sesión.

**Commits:** `feat(web): pantallas del técnico` · `feat(web): pantallas del gerente` · `feat(web): compras y caja` · `feat(web): alertas`.

## Fase 18 — Revisión como usuario del taller

**Construye** `docs/evidencias/revision-interfaz.md`, una lista de verificación que el equipo ejecuta a mano en Docker local:
- Los 6 escenarios del guion desde la página.
- Cada fila de prioridad Alta de `auditoria-errores-de-usuario.md`: intentar el error y anotar qué mensaje sale.
- Datos absurdos en cada formulario (negativos, vacíos, espacios, textos largos, doble clic).
- Cerrar sesión, clave inválida, recargar la página, apagar la API (mensaje de «sistema iniciando»).

Lo que falle se corrige en esta fase: la página, o el mensaje en el dominio o en `src/api/errores.py`. Después se vuelven a correr todas las pruebas.

**Commits:** `fix(web): …` por cada corrección · `docs: lista de revisión de la interfaz`.

## Fase 19 — Despliegue de la interfaz en Render y datos limpios en Supabase

*(Se detalla con el equipo cuando termine la Fase 18.)* Juntar `interfaz-web` con `main` cuando el CI esté en verde, revisar el Auto-Deploy de Render, volver a ejecutar `01_esquema.sql`, `02_datos_iniciales.sql` y `03_verificacion.sql` de `database/`, en ese orden, en el SQL Editor de Supabase (la Fase 14 cambia el esquema; `01` borra las tablas, así que se ejecuta a mano) y probar la página en producción.

## Fase 20 — README, guion de demostración y reporte

*(Se detalla con el equipo.)* README con la página como forma principal de uso y Swagger para la parte técnica, guion de demostración desde la página, evidencias nuevas en `docs/evidencias/` y anexo del reporte con lo que cambió después de la revisión del 09/11/2026.
