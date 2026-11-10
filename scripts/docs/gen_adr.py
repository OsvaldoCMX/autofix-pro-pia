"""Genera docs/architecture/adr/ADR-0XX-*.md y su índice."""
import sys
from pathlib import Path

DIR = Path(sys.argv[1]) / "architecture" / "adr"
DIR.mkdir(parents=True, exist_ok=True)

ADRS = []


def adr(num, slug, titulo, estado, fecha, contexto, alternativas, decision, consecuencias, trazabilidad,
        nota=None, resumen=None, necesidades=""):
    ADRS.append(dict(num=num, slug=slug, titulo=titulo, estado=estado, fecha=fecha, contexto=contexto,
                     alternativas=alternativas, decision=decision, consecuencias=consecuencias,
                     trazabilidad=trazabilidad, nota=nota, resumen=resumen or titulo, necesidades=necesidades))


U3, PIA = "10/2026 (Unidad 3)", "04/11/2026 (PIA)"

adr(1, "domain-model", "Domain Model como patrón de lógica de negocio",
    "Aceptada", U3 + "; actualizada en el PIA",
    "El proceso cotización → autorización → refacciones → entrega tiene 13 estados de orden, 6 de cotización, 4 de trabajo y 2 de solicitud (Glosario, «Estados del sistema»), diez restricciones de proceso (BRD) y criterios de rechazo explícitos (CA-007, CA-009, CA-012, CA-020, CA-029, CA-042, CA-045, CA-046). Varias reglas dependen del estado y cruzan conceptos (cotización, orden, cliente). Es un proyecto universitario con alcance acotado.",
    ["**Transaction Script:** el más rápido, pero repetiría las validaciones de estado en cada caso de uso y no impediría que una función se salte una regla.",
     "**Table Module:** agrupa por tabla, pero las reglas que cruzan orden, cotización y cliente no tienen un lugar natural.",
     "**Domain Model** (elegida): cada regla vive en el objeto que protege sus datos; requiere más clases."],
    "Domain Model para los Aggregates Orden de Servicio, Cotización, Cliente, Vehículo y Empleado. Las consultas de lectura (CQRS Queries) se resuelven con un lector simple, al estilo Transaction Script, porque solo arman vistas.",
    ["(+) Las reglas se escriben una sola vez y se prueban sin base de datos.",
     "(+) Los nombres del código son los del Glosario.",
     "(−) Más clases y mapeo entre los datos de entrada (API) y el dominio.",
     "(−) Algunos casos de uso modifican dos Aggregates y necesitan Unidad de Trabajo (ADR-002)."],
    "N-02, N-03, N-04, N-07, N-10, N-11, N-15 · US-004, US-005, US-006, US-010, US-016, US-024, US-025 · CA-005, CA-007, CA-010, CA-020, CA-029, CA-042, CA-045 · BPMN Fases 2 a 6",
    nota="**Actualización PIA.** Se completó el «trabajo posterior» de la U3: el modelo se extiende a recepción, diagnóstico, retiro anticipado, caja y cancelación, y las reglas compuestas se expresan como Specifications (ADR-006).",
    necesidades="N-02 a N-04, N-07, N-10, N-11, N-15")

adr(2, "aggregates-y-unidad-de-trabajo", "Límites de los Aggregates y Unidad de Trabajo",
    "Aceptada", U3 + "; actualizada en el PIA",
    "Una orden puede tener varias cotizaciones (inicial v.1 y adicionales v.2+; US-009). El Gerente revisa cotizaciones sin tocar la orden (US-005). La decisión del cliente cambia la cotización y crea los trabajos de la orden (CA-010). La orden debe estar «En Espera de Refacción» mientras exista una solicitud «Solicitada» (CA-019, CA-022). Vehículo y Empleado existen fuera de una orden (un vehículo regresa varias veces; un técnico atiende muchas órdenes).",
    ["**A)** Un solo Aggregate Orden con sus cotizaciones dentro: consistencia total, pero un objeto enorme y el Gerente tendría que cargar toda la orden.",
     "**B)** Cotización separada y Solicitud de Compra como Aggregate propio: Compras independiente, pero el invariante de «En Espera de Refacción» quedaría entre dos Aggregates.",
     "**C)** Cotización separada y Solicitud dentro de la Orden (elegida)."],
    "Opción C. Aggregates: Orden de Servicio (con Trabajos, Solicitudes de Compra, Fallas Adicionales, Recibo), Cotización (con sus Líneas y la Decisión), Cliente, Vehículo y Empleado. La relación entre Aggregates es solo por identidad (`numero_orden`, `id_cliente`, `placas`, `id_empleado`). Cuando un caso de uso modifica dos Aggregates (generar cotización + marcar la orden «Cotizada»; registrar decisión + crear trabajos) ambos cambios se confirman en la misma Unidad de Trabajo.",
    ["(+) Cada Aggregate es pequeño y protege sus invariantes.",
     "(+) La regla de la espera de refacciones se cumple en una sola transacción.",
     "(−) Dos casos de uso rompen la recomendación de «un Aggregate por transacción»; lo aceptamos porque el BRD exige evidencia consistente de la autorización (CE-01) y la Unidad de Trabajo lo garantiza.",
     "(−) Compras consulta las solicitudes a través del lector, no de un repositorio propio."],
    "N-03, N-06, N-10 · US-006, US-009, US-010, US-011 · CA-010, CA-019, CA-022 · BPMN Fases 3 y 4",
    necesidades="N-03, N-06, N-10")

adr(3, "service-layer-y-cqrs", "Service Layer por caso de uso y CQRS básico",
    "Aceptada", U3 + "; actualizada en el PIA",
    "Los casos de uso tienen actores distintos (Asesor, Técnico, Gerente, Compras, Caja). Los paneles de Compras, del técnico, del Gerente y la consulta del cliente (US-007, US-011, US-017, US-018, US-021) solo leen y cruzan varias órdenes. La Service Layer debe coordinar sin absorber reglas.",
    ["**Un único ServicioDeOrdenes:** menos archivos, pero mezcla actores y crece sin control.",
     "**Reglas en los servicios** (Transaction Script disfrazado): contradice ADR-001.",
     "**CQRS completo con base de lectura separada:** excesivo para el volumen de un taller."],
    "Un Application Service por grupo de casos de uso de un mismo actor: `ServicioDeRecepcion`, `ServicioDeCancelacion`, `ServicioDeDiagnostico`, `ServicioDeCotizacion`, `ServicioDeAprobacionGerencial`, `ServicioDeAutorizacion`, `ServicioDeReparacion`, `ServicioDeRefacciones`, `ServicioDeRetiro`, `ServicioDeCaja`, `ServicioDeEntrega` y `ServicioDeRevisionDePlazos` (12). Cada método recibe un Command y devuelve un resultado (DTO). Las consultas usan Queries con su manejador y la interfaz `LectorDeOrdenes`, y devuelven vistas propias: `ConsultarEstadoDeOrden`, `BuscarVehiculoPorPlacas`, `BuscarClientes`, `ConsultarPanelDelTecnico`, `ListarSolicitudesPendientes`, `ListarCotizacionesPendientesDeAprobacion`, `ConsultarCotizacion`, `ConsultarExpedienteDeOrden`, `ListarOrdenes`, `ConsultarIngresosDelDia` y `ListarAlertas`. Mismo almacenamiento para lectura y escritura.",
    ["(+) Cada servicio tiene una sola razón para cambiar (SOLID-S).",
     "(+) Las vistas no exponen los Aggregates; la consulta del cliente no revela datos si el folio y las placas no coinciden (CA-038).",
     "(+) Las rutas de la API solo traducen HTTP ↔ Command/Query (ADR-008).",
     "(−) Más clases pequeñas."],
    "N-02 a N-05, N-08 a N-11, N-13 a N-15 · US-005, US-007, US-011, US-017, US-018, US-021 · CA-007, CA-013, CA-021, CA-030, CA-031, CA-037, CA-038",
    nota="**Actualización PIA.** Se agregaron los servicios y consultas que la U3 dejó como trabajo posterior (recepción, diagnóstico, reparación, retiro, caja, cancelación, consultas del Gerente y revisión de plazos).",
    necesidades="N-02 a N-05, N-08 a N-11, N-13 a N-15")

adr(4, "repository", "Repository en términos del dominio",
    "Aceptada (el gestor de base de datos se define en ADR-009)", U3 + "; actualizada en U5 y en el PIA",
    "El BRD exige guardar digitalmente las autorizaciones (CE-01) y los documentos generados. En la U3 el gestor no estaba definido y se esperaba un «Data Center» del profesor. En el PIA se aclaró que el Data Center es el **paquete de datos ficticios** `06_AutoFix_Pro` (CSV) y que el gestor lo elige el equipo.",
    ["**Elegir un gestor y acceder a él desde los servicios:** amarra el diseño a una tecnología.",
     "**Usar el ORM dentro del dominio:** mezcla las reglas del negocio con detalles del framework.",
     "**Repository + Unidad de Trabajo como interfaces** (elegida), con implementación en memoria y en base de datos."],
    "Los repositorios (`RepositorioDeOrdenes`, `RepositorioDeCotizaciones`, `RepositorioDeClientes`, `RepositorioDeVehiculos`, `RepositorioDeEmpleados`) son interfaces del dominio con métodos de negocio (`obtener`, `agregar`, `guardar`, `siguiente_numero`…). Hay dos implementaciones que cumplen el mismo contrato: en memoria (pruebas unitarias) y SQLAlchemy (U5 y PIA). `obtener()` siempre responde con el error del negocio (p. ej. `OrdenNoEncontrada`) si no existe.",
    ["(+) El dominio y la aplicación no cambiaron al pasar de memoria a base de datos (comprobado en la U5 con pruebas de contrato).",
     "(+) Las pruebas unitarias no necesitan base de datos.",
     "(−) Hay que mantener el mapeo entre tablas y objetos del dominio."],
    "N-01 a N-03 · CE-01, CE-06 · BRD, Restricciones técnicas (almacenar digitalmente documentos)",
    nota="**Actualización U5/PIA.** En la U5 se implementaron los adaptadores SQLAlchemy con SQLite en memoria y pruebas de contrato memoria vs. base de datos. En el PIA el gestor de producción es PostgreSQL (ADR-009).",
    necesidades="N-01 a N-03")

adr(5, "politica-de-aprobacion-gerencial", "La regla de $15,000 MXN como política del dominio",
    "Aceptada (implementada como Specification en el PIA, ADR-006)", U3 + "; actualizada en el PIA",
    "El BRD establece que la cotización inicial mayor a $15,000 MXN requiere aprobación del Gerente antes de presentarse, y en la Unidad 2 se decidió que no aplica a las cotizaciones adicionales. Es la regla con más probabilidad de cambiar (monto o alcance).",
    ["**Condicional en ServicioDeCotizacion:** la aplicación decidiría el negocio.",
     "**Constante dentro de Cotizacion:** funciona, pero cada política nueva edita la clase.",
     "**Política inyectada en `Cotizacion.generar`** (elegida)."],
    "La política se inyecta en `Cotizacion.generar` y decide el estado inicial. En el PIA la política es la Specification `RequiereAprobacionGerencial = EsCotizacionInicial() & TotalMayorAlUmbral($15,000)`; el umbral es un parámetro.",
    ["(+) Cumple Open/Closed: otra política es otra Specification, sin editar `Cotizacion`.",
     "(+) La regla se prueba de forma aislada, con su tabla de verdad.",
     "(−) Una abstracción más que explicar."],
    "N-04 · US-005 · CA-005, CA-007, CA-016 · RN-04 · BPMN compuerta «¿Monto mayor a $15,000 MXN?»",
    necesidades="N-04")

adr(6, "specification", "Reglas compuestas con el patrón Specification",
    "Aceptada", PIA,
    "El PIA exige al menos tres Specifications que combinen AND, OR y NOT. En el código de la U3/U5 varias reglas compuestas estaban escritas como `if` dentro de métodos (`VerificadorDeAutorizante`, `registrar_entrega`, `crear_solicitud_de_compra`, la política de $15,000) y las reglas nuevas del PIA (cancelación, vehículo retirado, alertas por plazo) también son condiciones compuestas.",
    ["**Seguir con `if` en los métodos:** menos clases, pero las condiciones no se pueden reutilizar ni probar por separado.",
     "**Motor de reglas o tablas de decisión externas:** flexible, pero excesivo y saca las reglas del modelo.",
     "**Specification con combinadores** (Evans y Fowler) (elegida)."],
    "Clase base `Especificacion[T]` en `domain/compartido/especificacion.py` con `es_satisfecha_por(candidato)` y los combinadores `y()`, `o()`, `no()` (operadores `&`, `|`, `~`). Las piezas pequeñas llevan nombres del Glosario y viven en el `especificaciones.py` de cada módulo. Ocho Specifications de negocio: E1 `RequiereAprobacionGerencial`, E2 `AutorizanteValido`, E3 `PuedeEntregarse`, E4 `PuedeCancelarse`, E5 `PuedeIniciarTrabajo`, E6 `PuedeSolicitarRefaccion`, E7 `RequiereAlertaDeRefaccion`, E8 `RequiereRecontacto` (composición en `modelo-de-dominio.md` §4). Son **puras** (sin efectos secundarios); el Aggregate las consulta y, si no se cumplen, lanza el error del negocio con un mensaje para el usuario.",
    ["(+) Cada regla se lee como en el BRD y se prueba con su tabla de verdad.",
     "(+) Las mismas piezas sirven al dominio y a las consultas (p. ej. E7 en la revisión de plazos).",
     "(+) Las reglas de referencia del profesor se pueden armar con la misma clase en el arnés de pruebas sin tocar el dominio (ADR-013).",
     "(−) Más clases pequeñas; se mitiga agrupándolas por módulo."],
    "RN-04, RN-07, RN-09, RN-11, RN-12, RN-14, RN-18, RN-19 · CA-007, CA-014, CA-019, CA-020, CA-023, CA-029, CA-040 a CA-046",
    necesidades="N-03, N-04, N-05, N-07, N-09 a N-12, N-14, N-15")

adr(7, "maquinas-de-estados", "Máquinas de estados declarativas por tabla",
    "Aceptada", PIA,
    "Hay cuatro objetos con estado: Orden (13 estados), Cotización (6), Trabajo (4) y Solicitud de Compra (2). En la U3 solo la orden tenía tabla de transiciones; la cotización y el trabajo validaban con `if`. El PIA exige una máquina de estados y el profesor entrega pruebas de transición (`completar`, `cancelar`, `repetir_aprobacion`, `saltar_estado`, `aprobar`).",
    ["**Patrón State** (una clase por estado): 25 clases para reglas que casi siempre son «desde X solo se puede ir a Y».",
     "**Librería externa** (p. ej. `transitions`): agrega una dependencia y saca las reglas del dominio.",
     "**Tabla declarativa + clase genérica** (elegida)."],
    "`MaquinaDeEstados[E]` genérica en `domain/compartido/maquina_de_estados.py` con la tabla `{estado: {destinos}}`, los estados finales y `validar(actual, nuevo)`, que lanza `TransicionDeEstadoNoPermitida`. Cada objeto tiene su tabla (`estados.py`). Los métodos del Aggregate validan **antes** de modificar nada y usan las Specifications como guardas. Los diagramas de estados se dibujan a partir de las mismas tablas.",
    ["(+) Una sola fuente de verdad para código, diagramas y pruebas.",
     "(+) Una prueba parametrizada recorre **todas** las parejas (estado, destino) y confirma cuáles se permiten y cuáles no.",
     "(−) Las guardas complejas siguen en los métodos del Aggregate (con Specifications)."],
    "RN-22 · Glosario §2 · todos los CA que cambian un estado · `transiciones_prueba.csv`",
    necesidades="N-01 a N-15")

adr(8, "api-rest-fastapi", "API REST con FastAPI, OpenAPI y mapeo de errores",
    "Aceptada", PIA,
    "El PIA exige una API REST documentada con OpenAPI/Swagger y disponible en producción, y contrastar respuestas con 200/201, 400/409/422 y 404. En la U4 (TechStore) el equipo ya trabajó con FastAPI.",
    ["**Flask + extensión OpenAPI:** más configuración para documentar y validar.",
     "**Django REST Framework:** robusto, pero trae ORM y estructura propios que chocan con el Domain Model.",
     "**FastAPI** (elegida): OpenAPI automático, validación con Pydantic, `TestClient` para pruebas."],
    "FastAPI con un router por área (`api/rutas/`), esquemas Pydantic separados del dominio (`api/esquemas/`) y un manejador de errores que traduce cada `ErrorDeDominio` a su código: 404 (`*NoEncontrada/o`), 409 (regla o transición violada), 422 (dato inválido), 403 (`TrabajoDeOtroTecnico`). El JSON mal formado responde 400 (se distingue del 422 de validación). Formato único de error `{error, detalle, codigo}`. Swagger UI en `/docs` también en producción, con el botón *Authorize* para el token (ADR-012). El contrato planeado está en `docs/api/README.md`.",
    ["(+) La documentación de la API siempre coincide con el código.",
     "(+) Los tipos se validan antes de llegar al dominio; el dominio sigue siendo la autoridad de las reglas.",
     "(−) Algunas validaciones de formato quedan en dos lugares (Pydantic y Value Objects)."],
    "Todos los CA (cada criterio tiene su ruta) · PIA: API REST, OpenAPI, códigos HTTP",
    necesidades="N-01 a N-15")

adr(9, "postgresql-supabase", "PostgreSQL 16: Docker en local y Supabase en producción",
    "Aceptada", PIA,
    "El «Data Center» es un paquete de CSV y el gestor lo elige el equipo. El PIA pide persistencia en base de datos, Docker Compose con un servicio de base y despliegue en la nube. La U5 ya tiene adaptadores SQLAlchemy 2 (tablas y traducción explícita fila ↔ objeto, sin que el dominio conozca el ORM) y pruebas de contrato. El equipo ya trabajó con Supabase (que es PostgreSQL) y con MySQL.",
    ["**SQLite en archivo:** simple, pero el disco de Render es efímero (se pierde al reiniciar) y no hay un servicio de base en Docker Compose.",
     "**MySQL:** el equipo lo conoce, pero Render no lo ofrece y habría que buscar otro proveedor gratuito.",
     "**PostgreSQL de Render:** cómodo, pero la base gratuita expira a los 30 días de crearse.",
     "**PostgreSQL en Supabase** (elegida): el equipo ya conoce su panel, el plan gratuito no expira y permite ver las tablas durante la demostración."],
    "PostgreSQL 16 en todos los ambientes: `postgres:16-alpine` en Docker Compose y en el CI, y un proyecto gratuito de **Supabase** en producción. Acceso con SQLAlchemy 2 (tablas de SQLAlchemy Core y Data Mapper explícito en `mapeo.py`, como en la U5) y psycopg 3. El esquema oficial es `database/01_esquema.sql` (generado por `scripts/db/esquema.py`, documentado en `architecture/modelo-de-datos.md`): 18 tablas, importes `NUMERIC(12,2)`, fechas `TIMESTAMPTZ` en UTC, estados validados con `CHECK` y RLS activado para proteger la Data API de Supabase. Se ejecuta en el SQL Editor de Supabase y, en Docker, automáticamente al crear el volumen (`docker-entrypoint-initdb.d`); la aplicación **no** crea tablas en producción. `src/infrastructure/base_de_datos/tablas.py` refleja el esquema y una prueba de integración lo compara contra PostgreSQL; las pruebas sin Docker usan SQLite en memoria con `metadata.create_all()`. Render se conecta con la cadena **Session pooler** de Supabase (IPv4, puerto 5432) en `DATABASE_URL`; la configuración normaliza el prefijo a `postgresql+psycopg://`.",
    ["(+) El mismo gestor en local, CI y producción, y un panel que el equipo ya conoce.",
     "(+) Se reutilizan los adaptadores y las pruebas de contrato de la U5.",
     "(+) Las restricciones `CHECK` y las llaves foráneas protegen la integridad aunque alguien edite datos a mano en Supabase.",
     "(−) El plan gratuito de Supabase pausa el proyecto tras 7 días sin actividad; la revisión de plazos cada 6 horas (ADR-015) lo mantiene activo. Límite de 500 MB, suficiente para la demostración.",
     "(−) Sin migraciones automáticas: un cambio de esquema se hace en `esquema.py`, se regenera el SQL y se vuelve a ejecutar (los datos son ficticios y se recargan con `02_datos_iniciales.sql`)."],
    "N-01 a N-03, N-11 · CE-01, CE-06 · PIA: persistencia, Docker Compose, despliegue · actualiza ADR-004",
    necesidades="N-01 a N-03, N-11")

adr(10, "docker-compose-y-configuracion", "Docker Compose (db, app, tests) y configuración por variables de entorno",
     "Aceptada", PIA,
     "El PIA exige Docker Compose con base de datos, aplicación y pruebas, configuración por variables de entorno (12-Factor) y un `.env.example` sin secretos.",
     ["**Instalar todo a mano en cada computadora:** frágil y distinto en cada integrante.",
      "**Solo un Dockerfile:** no levanta la base ni corre las pruebas contra ella.",
      "**Docker Compose con tres servicios** (elegida)."],
     "`Dockerfile` basado en `python:3.12-slim`, usuario sin privilegios, `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`. `docker-compose.yml` con: **db** (`postgres:16-alpine`, volumen, *healthcheck* `pg_isready` y la carpeta `database/` montada en `/docker-entrypoint-initdb.d` para crear el esquema y cargar los datos iniciales), **app** (depende de `db` sano, `env_file: .env`, puerto 8000, *healthcheck* `/health`) y **tests** (misma imagen, perfil `tests`, ejecuta `pytest --cov=src --cov-branch --cov-fail-under=80` contra `db`). Toda la configuración se lee del entorno en `infrastructure/config.py`; `.env.example` tiene valores de ejemplo y `.env` está en `.gitignore`.",
     ["(+) Cualquiera levanta el sistema con `docker compose up` y corre las pruebas con `docker compose run --rm tests`.",
      "(+) La aplicación corre igual en local, en el CI y en Render.",
      "(−) En Windows se necesita Docker Desktop."],
     "PIA: Docker Compose, variables de entorno · Restricciones técnicas del BRD",
     necesidades="Restricciones técnicas")

adr(11, "despliegue-render-y-ci-cd", "Despliegue en Render y CI/CD con GitHub Actions",
     "Aceptada", PIA,
     "El PIA exige una URL pública (Render, Railway o Fly.io) con Swagger disponible, y un pipeline de CI/CD. El repositorio está en GitHub y el CI de la U5 ya corre en GitHub Actions.",
     ["**Railway:** sencillo, pero el uso gratuito es por créditos de prueba.",
      "**Fly.io:** flexible, pero pide tarjeta y su capa gratuita cambió.",
      "**Render** (elegida): Web Service con Docker gratuito y despliegue desde GitHub; la base vive en Supabase (ADR-009)."],
     "**CI** (`.github/workflows/ci.yml`): en cada *push* y *pull request* instala dependencias, corre Ruff y `pytest` con cobertura ≥ 80 % usando PostgreSQL como servicio, y publica `htmlcov/`, `coverage.xml` y `reportes/` como artefactos. **CD:** Render Web Service (tipo Docker) conectado a `main` con *Auto-Deploy* = «After CI Checks Pass», *health check* en `/health` y las variables de entorno en el panel de Render; `DATABASE_URL` es la cadena *Session pooler* de Supabase. Conviene elegir regiones cercanas: Supabase «East US (North Virginia)» y Render «Virginia (US East)».",
     ["(+) Solo se despliega lo que pasó las pruebas.",
      "(−) El servicio gratuito se duerme tras 15 minutos sin tráfico y tarda alrededor de un minuto en despertar: abrir `/health` antes de la presentación.",
      "(−) 750 horas gratuitas al mes y disco efímero (por eso los archivos van a la base, ADR-014).",
      "(−) Si Supabase pausa el proyecto por inactividad, la API responde con error de base de datos hasta reanudarlo desde el panel (ADR-009, ADR-015)."],
     "PIA: despliegue, CI/CD, URL pública",
     necesidades="Restricciones técnicas")

adr(12, "seguridad-por-token", "Seguridad con token sencillo por empleado y rol",
     "Aceptada", PIA,
     "Cada actor del taller tiene acciones distintas (Asesor, Técnico, Gerente, Compras, Caja) y el BRD excluye cuentas para clientes y responsables de flotilla. La consulta de estado del cliente es pública (US-021). Es un proyecto académico con datos ficticios.",
     ["**Sin seguridad:** no demuestra los roles y cualquiera cambiaría estados en producción.",
      "**OAuth2/JWT con usuarios y contraseñas:** más completo, pero agrega registro, hashes y expiración que el BRD no pide.",
      "**Token Bearer fijo por empleado de demostración** (elegida)."],
     "Los seis empleados de demostración (EMP-001 Asesor, EMP-002 y EMP-003 Técnicos, EMP-004 Gerente, EMP-005 Compras, EMP-006 Caja) vienen en `database/02_datos_iniciales.sql`; además existe un usuario técnico «Sistema» que no es empleado. Sus tokens vienen de variables de entorno (`TOKEN_ASESOR`, …, `TOKEN_SISTEMA`). La dependencia `requiere_rol(*roles)` lee `Authorization: Bearer <token>`, lo compara con `secrets.compare_digest` y entrega el `Empleado`: 401 si falta o es inválido, 403 si su rol no puede usar la ruta. Rutas públicas: `/health`, `/docs`, `/openapi.json` y `/api/consulta-de-estado`.",
     ["(+) Se demuestra la regla «cada ruta exige un rol» (RN-01, RN-14) con pruebas de 401/403.",
      "(+) Swagger permite probar con el botón *Authorize*.",
      "(−) Los tokens no expiran; se cambian modificando la variable. Es una limitación documentada para un entorno de demostración.",
      "(−) Nunca se suben tokens reales: `.env.example` solo tiene marcadores."],
     "RN-01, RN-14 · BRD §2 Roles y permisos, §5 Fuera del alcance (sin cuentas de clientes) · CA-013, CA-021, CA-030, CA-037",
     necesidades="N-08, N-09, N-13")

adr(13, "adaptacion-datos-del-profesor", "Adaptación de los datos ficticios del profesor",
     "Aceptada", PIA,
     "El paquete `06_AutoFix_Pro` trae 40 propietarios, 20 servicios, 60 operaciones (todas «RECIBIDA»), 117 líneas de detalle, 120 casos de prueba y 20 pruebas de transición, con un flujo de referencia de 5 estados y dos reglas ilustrativas. El propio paquete aclara que es un **modelo de pruebas propuesto** y que, si difiere de los requerimientos del equipo, se deben documentar las diferencias y adaptar fixtures y oráculos, sin reemplazar los requerimientos propios.",
     ["**Cambiar el BRD para que coincida con los datos:** contradice la instrucción del profesor y el trabajo de U2/U3.",
      "**Ignorar los datos:** no cumple el PIA.",
      "**Cargar los datos con un adaptador y escribir oráculos propios** (elegida)."],
     "El estado inicial se carga con `database/02_datos_iniciales.sql`, generado desde los CSV por `scripts/db/generar_datos_iniciales.py` (UTF-8 con BOM, importes con `Decimal`): propietarios → `Cliente` Particular; operaciones → `OrdenDeServicio` «Recibida» con folio = `operacion_id`, placas derivadas de `referencia` y un `Vehiculo` ficticio por orden; catálogo y detalle → tablas de referencia `catalogo_servicios` y `servicios_solicitados`, que se usan para armar la cotización (precio × cantidad); las columnas sin equivalente quedan en `referencia_operaciones_profesor`. Los cambios de estado se hacen con la API, como pide el paquete. Un servicio inhabilitado se rechaza como dato inválido (422) y la cotización no se genera: `ServicioDeCotizacion.generar_inicial` lo comprueba con el puerto `CatalogoDeServicios` (H-PIA-19). `activo`, `es_preferente`, `promocion_activa` y `capacidad_o_stock` no tienen equivalente en el BRD y no cambian el dominio. Los 120 casos y las 20 transiciones se ejecutan en `tests/datos_profesor/` con **oráculos propios** y, como referencia, las reglas del profesor armadas con `Especificacion` dentro del arnés de pruebas. Resultados en `reportes/resultados_casos.csv` y `reportes/resultados_transiciones.csv`. Diferencias y oráculos: `docs/datos-profesor/README.md`.",
     ["(+) Se usan todos los datos del profesor sin perder los requerimientos propios.",
      "(+) Cada diferencia queda explicada y es verificable con una prueba.",
      "(−) Algunos resultados difieren de la regla de referencia del profesor por decisión documentada (p. ej. clientes inactivos)."],
     "H-PIA-03 · BRD §8 Supuestos · RN-23 · `casos_prueba.csv`, `transiciones_prueba.csv`",
     necesidades="N-01 a N-04, N-11, N-15")

adr(14, "documentos-y-archivos", "PDF generados al vuelo y fotos guardadas en la base de datos",
     "Aceptada", PIA,
     "El BRD pide almacenar digitalmente fotos y documentos (cotización, Nota de Responsabilidad, recibo interno; CA-002, CA-005, CA-024, CA-027). En Render el disco es efímero y un servicio de almacenamiento externo requiere credenciales.",
     ["**Guardar archivos en el disco del servidor:** se pierden en cada reinicio de Render.",
      "**Almacenamiento en la nube (S3 o similar):** correcto para producción real, pero agrega cuentas y secretos.",
      "**PDF generados al pedirlos y fotos en la base** (elegida)."],
     "Los PDF se generan al momento a partir de los datos guardados (fpdf2, detrás del puerto `GeneradorDeDocumentos`); como los datos ya no cambian después de la acción correspondiente (cotización guardada, nota firmada, pago registrado), el PDF siempre es el mismo. Las fotos se guardan en la tabla `fotos_de_danos` (`BYTEA`, JPEG o PNG, máximo 5 MB). Es alcance **P2**: si no se termina, las rutas responden 501 y la matriz lo indica.",
     ["(+) Nada se pierde al reiniciar el servicio y no hay secretos extra.",
      "(−) La base crece con las fotos; aceptable para el volumen de una demostración."],
     "N-01, N-02, N-11, N-12 · CA-002, CA-005, CA-024, CA-027 · BRD Restricciones técnicas",
     necesidades="N-01, N-02, N-11, N-12")

adr(15, "revision-periodica-de-plazos", "Revisión periódica de plazos con un endpoint y un workflow programado",
     "Aceptada", PIA,
     "CA-023 pide una revisión diaria de las refacciones con más de 3 días hábiles y CA-040 una revisión de las cotizaciones con más de 48 horas sin respuesta. El servicio gratuito de Render se duerme sin tráfico, así que un temporizador dentro de la aplicación no correría.",
     ["**Planificador dentro de la app (APScheduler):** no corre mientras el servicio está dormido.",
      "**Cron Job de Render:** es de pago.",
      "**Endpoint idempotente + workflow programado de GitHub Actions** (elegida)."],
     "`POST /api/revisiones/plazos` (solo `TOKEN_SISTEMA`) ejecuta `ServicioDeRevisionDePlazos`, que evalúa E7 `RequiereAlertaDeRefaccion` y E8 `RequiereRecontacto` con el reloj actual y crea alertas solo si no existe ya una alerta abierta para la misma solicitud o el mismo periodo de la cotización (idempotente). `.github/workflows/revision-de-plazos.yml` lo llama cada 6 horas (`cron: '0 */6 * * *'`) y también se puede lanzar a mano (`workflow_dispatch`). En las pruebas se usa un reloj falso.",
     ["(+) Cumple «revisión diaria» aunque el servicio duerma (la llamada lo despierta).",
      "(+) Se puede demostrar en vivo desde Swagger.",
      "(+) Como la revisión consulta la base, también evita que Supabase pause el proyecto por inactividad.",
      "(−) GitHub puede retrasar los workflows programados y los desactiva tras 60 días sin actividad en el repositorio."],
     "N-05, N-14 · US-012, US-023 · CA-023, CA-040 · RN-11, RN-12 · BPMN temporizadores no interruptores",
     necesidades="N-05, N-14")

adr(16, "domain-events", "Domain Events publicados después de confirmar y alertas internas",
     "Aceptada", PIA + " (amplía la decisión de la U3)",
     "El PIA exige Domain Events. En la U3 los Aggregates ya registraban eventos y la Unidad de Trabajo los entregaba al `PublicadorDeEventos` después de confirmar. Varias historias piden «notificar» a un empleado (CA-007, CA-008, CA-009, CA-015, CA-017, CA-022, CA-032, CA-034) y el BRD aclara que las alertas son internas (sin correo ni SMS).",
     ["**Llamar a las alertas desde los servicios:** acopla cada caso de uso a quién debe enterarse.",
      "**Publicar antes de confirmar:** podría avisar de un cambio que después se deshace.",
      "**Broker de mensajes (RabbitMQ, etc.):** excesivo para un taller.",
      "**Eventos registrados en el Aggregate, bitácora en la misma transacción y manejadores en proceso después de confirmar** (elegida)."],
     "Los eventos son `dataclass` inmutables con `ocurrido_en`. La Unidad de Trabajo los recolecta, guarda la **bitácora de eventos** (tabla `eventos`: tipo, datos JSON, fecha) en la misma transacción y, después de confirmar, `PublicadorEnProceso` los entrega a los manejadores registrados en el Composition Root. Los manejadores de `application/manejadores/alertas.py` crean `AlertaInterna` para el empleado correcto (asesor de la orden, técnico asignado, gerentes). Ningún manejador modifica otro Aggregate.",
     ["(+) Los casos de uso no saben quién recibe alertas; agregar una reacción es agregar un manejador (Open/Closed).",
      "(+) La bitácora es la evidencia de «registrar evento o excepción» que piden las pruebas de transición.",
      "(−) Si un manejador falla después de confirmar, la alerta se pierde (el cambio de negocio sí queda); se registra en la bitácora de la aplicación."],
     "N-04, N-05, N-06, N-09 a N-11, N-14 · CA-007, CA-008, CA-009, CA-015, CA-017, CA-022, CA-032, CA-034 · `modelo-de-dominio.md` §6",
     necesidades="N-04 a N-06, N-09 a N-11, N-14")


def md(a):
    out = [f"# ADR-{a['num']:03d} — {a['titulo']}\n",
           "| Campo | Contenido |", "|---|---|",
           f"| Estado | {a['estado']} |", f"| Fecha | {a['fecha']} |",
           f"| Trazabilidad | {a['trazabilidad']} |", "",
           "## Contexto\n", a["contexto"], "", "## Alternativas consideradas\n"]
    out += [f"- {x}" for x in a["alternativas"]]
    out += ["", "## Decisión\n", a["decision"], "", "## Consecuencias\n"]
    out += [f"- {x}" for x in a["consecuencias"]]
    if a["nota"]:
        out += ["", a["nota"]]
    return "\n".join(out) + "\n"


for a in ADRS:
    (DIR / f"ADR-{a['num']:03d}-{a['slug']}.md").write_text(md(a), encoding="utf-8")

idx = ["# Registro de decisiones de arquitectura (ADR)\n",
       "Cada ADR sigue los campos de la guía de la Unidad 3: estado, fecha, contexto, alternativas, decisión, consecuencias y trazabilidad. ADR-001 a ADR-005 vienen de la U3 (actualizados); ADR-006 a ADR-016 son del PIA. Todas están aceptadas por el equipo (las propuestas ADR-009, 011, 014 y 015 se confirmaron el 04/11/2026).\n",
       "| ADR | Decisión | Estado | Necesidades |", "|---|---|---|---|"]
for a in ADRS:
    idx.append(f"| [ADR-{a['num']:03d}](ADR-{a['num']:03d}-{a['slug']}.md) | {a['titulo']} | {a['estado']} | {a['necesidades']} |")
(DIR / "README.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
print(len(ADRS))
