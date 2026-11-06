# AutoFix Pro

[![CI](https://github.com/OsvaldoCMX/autofix-pro-pia/actions/workflows/ci.yml/badge.svg)](https://github.com/OsvaldoCMX/autofix-pro-pia/actions/workflows/ci.yml)

Sistema de gestión de órdenes de servicio para el taller automotriz ficticio AutoFix Pro: desde la recepción del vehículo hasta la cotización, la reparación, el cobro y la entrega. Es una API REST que se usa desde Swagger.

Proyecto final (PIA) de la materia Componentes de Lógica de Negocio, FIME UANL.

## Equipo 6

- Jesus Eduardo Moreno Osoria (2136063)
- Osvaldo Salvador Cárdenas Mejorado (2141553)

## Enlaces

- Repositorio: <https://github.com/OsvaldoCMX/autofix-pro-pia>
- API en producción: <https://autofix-pro-pia.onrender.com>
- Swagger en producción: <https://autofix-pro-pia.onrender.com/docs>
- Documentación: [docs/](docs/)
- Evidencia de pruebas: [docs/trazabilidad/evidencia-pruebas.md](docs/trazabilidad/evidencia-pruebas.md)
- Matriz de trazabilidad: [docs/trazabilidad/matriz-trazabilidad.md](docs/trazabilidad/matriz-trazabilidad.md)

El servicio gratuito de Render se duerme tras 15 minutos sin tráfico: la primera visita puede tardar cerca de un minuto.

**Los tokens de producción se entregan por separado.**

## Alcance

Está implementado todo el flujo obligatorio (P1). Las funciones opcionales de PDF y fotos de daños (P2) se omitieron por decisión del equipo, y sus 4 rutas responden `501`:

| Criterio | Qué falta |
|---|---|
| CA-002 | Fotos de daños |
| CA-005 | PDF de la cotización |
| CA-024 | PDF de la Nota de Responsabilidad |
| CA-027 | Recibo interno en PDF (no implementado) |

## Arquitectura en breve

Diseño guiado por el dominio (DDD), con dependencias que apuntan hacia adentro: `api → application → domain` e `infrastructure → application/domain`. `tests/test_arquitectura.py` lo verifica.

| Carpeta | Contenido |
|---|---|
| `src/domain` | Aggregates, Value Objects, Specifications E1–E8, máquinas de estados y eventos. No conoce FastAPI, Pydantic ni SQLAlchemy. |
| `src/application` | Casos de uso, consultas, Unidad de Trabajo y manejadores de alertas. |
| `src/infrastructure` | PostgreSQL con SQLAlchemy Core y Data Mapper, adaptadores en memoria y reloj. |
| `src/api` | Rutas FastAPI, esquemas, seguridad por rol y traducción de errores. |

**Stack:** Python 3.12, FastAPI, SQLAlchemy 2, psycopg 3, PostgreSQL 16, pytest, Ruff, Docker Compose, GitHub Actions, Render y Supabase. Las decisiones están en [docs/architecture/adr/](docs/architecture/adr/).

## Requisitos

- Git.
- Docker Desktop, para la ejecución recomendada.
- Python 3.12, solo para trabajar sin Docker (también es compatible con 3.11).

**Clona el repositorio en un disco fijo (`C:`, `D:`).** Docker Desktop no ve las unidades USB: monta `database/` vacía y la base queda sin tablas, aunque `/health` responda bien. Si ya pasó, mueve el proyecto y borra el volumen con `docker compose down -v`.

## Ejecución con Docker (recomendada)

```bash
git clone https://github.com/OsvaldoCMX/autofix-pro-pia.git
cd autofix-pro-pia
cp .env.example .env
docker compose up --build
```

En PowerShell, usa `Copy-Item .env.example .env` en lugar de `cp`.

Abre <http://localhost:8000/docs>. La base arranca con el estado inicial del paquete del profesor: 60 órdenes «Recibida», 40 clientes y 60 vehículos. Para volver a ese estado:

```bash
docker compose down -v
docker compose up --build
```

### Tokens locales

Son los de `.env.example`. Solo sirven en local, no en producción.

| Rol | Empleado | Token local |
|---|---|---|
| Asesor | EMP-001 Laura Méndez | `cambia-este-token-asesor` |
| Técnico | EMP-002 Carlos Ruiz | `cambia-este-token-tecnico` |
| Técnico | EMP-003 Diego Salinas | `cambia-este-token-tecnico-2` |
| Gerente | EMP-004 Patricia Garza | `cambia-este-token-gerente` |
| Compras | EMP-005 Jorge Treviño | `cambia-este-token-compras` |
| Caja | EMP-006 Sofía Leal | `cambia-este-token-caja` |
| Sistema | Solo la revisión de plazos | `cambia-este-token-sistema` |

## Ejecución sin Docker

Usa adaptadores en memoria: arranca sin órdenes y los datos se pierden al cerrar. La aplicación lee el entorno, no el archivo `.env`, así que cada token debe definirse en la terminal. En PowerShell:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
$env:PYTHONPATH = "src"
$env:TOKEN_ASESOR = "cambia-este-token-asesor"
.venv/Scripts/python -m uvicorn api.main:app --reload
```

## Pruebas y cobertura

Con el entorno virtual de la sección anterior y sin `DATABASE_URL`, las pruebas usan SQLite en memoria y omiten las que requieren PostgreSQL:

```bash
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=80
```

Para correr todas contra PostgreSQL dentro de Docker:

```bash
docker compose --profile tests run --rm tests
```

Las pruebas usan un esquema temporal y no tocan los datos de demostración. **Nunca se ejecutan contra Supabase.**

La evidencia se regenera con una base local desechable en `DATABASE_URL`:

```bash
python scripts/docs/gen_evidencia.py
```

## Variables de entorno

| Variable | Uso |
|---|---|
| `APP_ENV` | `desarrollo`, `pruebas` o `produccion`. En `produccion`, la aplicación no arranca sin `DATABASE_URL`. |
| `DATABASE_URL` | Conexión a la base. En Render es la cadena *Session pooler* de Supabase. |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Solo para el servicio `db` de Docker Compose. |
| `TOKEN_ASESOR`, `TOKEN_TECNICO`, `TOKEN_TECNICO_2`, `TOKEN_GERENTE`, `TOKEN_COMPRAS`, `TOKEN_CAJA` | Token de cada empleado de demostración. |
| `TOKEN_SISTEMA` | Solo para `POST /api/revisiones/plazos`. |
| `ZONA_HORARIA` | `America/Monterrey`: «hoy» y los días hábiles. Las fechas se guardan en UTC. |
| `PORT` | Puerto de Uvicorn. Render lo define. |
| `LOG_LEVEL` | Nivel de bitácora. |

`.env` es local y no se sube al repositorio.

## Despliegue

- **Base de datos:** proyecto de Supabase. Los scripts `database/01_esquema.sql`, `02_datos_iniciales.sql` y `03_verificacion.sql` se ejecutan en ese orden en el SQL Editor; la aplicación no crea tablas en producción. **`01` borra y vuelve a crear las tablas.**
- **Aplicación:** Render Web Service con Docker, región Virginia y plan Free, conectado a `main`. Tiene *Health Check Path* `/health` y *Auto-Deploy* «After CI Checks Pass».
- **CI:** cada push corre Ruff y `pytest` con cobertura mínima de 80 % contra PostgreSQL ([ci.yml](.github/workflows/ci.yml)).
- **Revisión de plazos:** un workflow la llama cada 6 horas y también se puede lanzar a mano ([revision-de-plazos.yml](.github/workflows/revision-de-plazos.yml)). Usa los secretos `AUTOFIX_API_URL` y `TOKEN_SISTEMA`.

`/health` no consulta la base. Para comprobar la conexión con Supabase, usa una ruta con datos como `GET /api/gerencia/ordenes`.

## Guion de demostración en Swagger

**Preparación:**
1. Abre `/health` un par de minutos antes para despertar el servicio.
2. Abre `/docs`. Para cambiar de rol, usa **Authorize**, luego **Logout**, y pega el token del siguiente rol.

**Estos pasos cambian los datos.** Cada orden avanza una sola vez, así que ensaya en local. Para repetir la demostración en producción, vuelve a ejecutar los tres scripts de `database/` en el SQL Editor de Supabase; esto borra todo lo registrado.

### 1. Orden particular completa (`AUT-O001`)

| # | Rol | Ruta | Cuerpo | Resultado |
|---|---|---|---|---|
| 1 | Público | `GET /api/consulta-de-estado?orden=AUT-O001&placas=PIAAUT001` | | 200, «Recibida» |
| 2 | Asesor | `POST /api/ordenes/AUT-O001/asignacion-diagnostico` | `{"tecnico": "EMP-002"}` | 200, «En Diagnóstico» |
| 3 | Técnico | `POST /api/ordenes/AUT-O001/diagnostico` | `{"fallas": "Balatas gastadas", "recomendaciones": "Cambiar balatas"}` | 201 |
| 4 | Asesor | `POST /api/ordenes/AUT-O001/cotizaciones` | `{"trabajos": [{"numero": 1, "descripcion": "Cambio de balatas", "mano_de_obra": "3000.00"}]}` | 201; anota el `id` de la cotización |
| 5 | Asesor | `POST /api/cotizaciones/{id}/presentacion` | | 200 |
| 6 | Asesor | `POST /api/cotizaciones/{id}/decision` | `{"lineas_autorizadas": [1], "nombre_del_autorizante": "Propietario 14", "rol_del_autorizante": "Cliente"}` | 200, «Autorizada» |
| 7 | Asesor | `POST /api/ordenes/AUT-O001/asignacion-trabajos` | `{"ids_trabajos": [1], "tecnico": "EMP-002"}` | 200 |
| 8 | Técnico | `POST /api/ordenes/AUT-O001/trabajos/1/inicio` | | 200, «En Reparación» |
| 9 | Técnico | `POST /api/ordenes/AUT-O001/trabajos/1/completado` | | 200, «Lista para Entrega» |
| 10 | Caja | `POST /api/ordenes/AUT-O001/pago` | `{"monto": "3000.00", "forma": "Tarjeta"}` | 201, «Pagada» |
| 11 | Asesor | `POST /api/ordenes/AUT-O001/entrega` | | 200, «Cerrada» |
| 12 | Gerente | `GET /api/gerencia/ingresos-del-dia` | | 200, incluye los $3,000.00 |

### 2. Rechazo de una transición inválida (`AUT-O002`)

| # | Rol | Ruta | Cuerpo | Resultado |
|---|---|---|---|---|
| 1 | Asesor | `POST /api/ordenes/AUT-O002/entrega` | | 409 `EntregaNoPermitida` |
| 2 | Asesor | `POST /api/ordenes/AUT-O002/cotizaciones` | `{"trabajos": [{"numero": 1, "descripcion": "Prueba", "mano_de_obra": "100.00"}]}` | 409 `DiagnosticoRequerido` |
| 3 | Caja | `POST /api/ordenes/AUT-O002/entrega` | | 403 `RolNoPermitido` |
| 4 | Sin token (**Logout**) | `POST /api/ordenes/AUT-O002/entrega` | | 401 `TokenInvalido` |

### 3. Aprobación gerencial (`AUT-O003`, más de $15,000)

| # | Rol | Ruta | Cuerpo | Resultado |
|---|---|---|---|---|
| 1 | Asesor | `POST /api/ordenes/AUT-O003/asignacion-diagnostico` | `{"tecnico": "EMP-002"}` | 200 |
| 2 | Técnico | `POST /api/ordenes/AUT-O003/diagnostico` | `{"fallas": "Motor dañado", "recomendaciones": "Reparar motor"}` | 201 |
| 3 | Asesor | `POST /api/ordenes/AUT-O003/cotizaciones` | `{"trabajos": [{"numero": 1, "descripcion": "Reparación de motor", "mano_de_obra": "20000.00"}]}` | 201, «Pendiente de Aprobación Gerencial»; anota el `id` |
| 4 | Asesor | `POST /api/cotizaciones/{id}/presentacion` | | 409: falta la aprobación |
| 5 | Gerente | `GET /api/gerencia/cotizaciones-por-aprobar` | | 200, aparece la cotización |
| 6 | Gerente | `GET /api/alertas` | | 200, alerta `AprobacionGerencialRequerida` |
| 7 | Gerente | `POST /api/cotizaciones/{id}/revision-gerencial` | `{"aprobada": true, "observaciones": "Aprobada"}` | 200, «Pendiente de Autorización del Cliente» |
| 8 | Asesor | `POST /api/cotizaciones/{id}/presentacion` | | 200 |

### 4. Flotilla con crédito (orden nueva)

Registra la orden con el rol Asesor en `POST /api/ordenes` y anota su `numero_orden`:

```json
{
  "placas": "FLT0001",
  "motivo_de_ingreso": "Servicio de frenos",
  "kilometraje": 80000,
  "nivel_de_combustible": "3/4",
  "vehiculo": {"vin": "1HGCM82633A000001", "marca": "Nissan", "modelo": "NP300", "anio": 2022},
  "cliente": {
    "nombre": "Transportes Norte SA",
    "tipo": "Flotilla",
    "telefono": "81-3333",
    "correo": "contacto@norte.test",
    "empresa": "Transportes Norte",
    "responsable_nombre": "Ana Torres",
    "responsable_telefono": "81-1111",
    "responsable_correo": "ana@norte.test"
  }
}
```

Repite los pasos 2 a 5 del escenario 1 con ese número y una cotización de `"3000.00"`. Después:

| # | Rol | Ruta | Cuerpo | Resultado |
|---|---|---|---|---|
| 1 | Asesor | `POST /api/cotizaciones/{id}/decision` | `{"lineas_autorizadas": [1], "nombre_del_autorizante": "Pedro Pérez", "rol_del_autorizante": "Cliente"}` | 409 `AutorizanteNoValido` |
| 2 | Asesor | `POST /api/cotizaciones/{id}/decision` | `{"lineas_autorizadas": [1], "nombre_del_autorizante": "Ana Torres", "rol_del_autorizante": "Responsable de Flotilla"}` | 200, «Autorizada» |
| 3 | Asesor | `POST /api/ordenes/{numero}/asignacion-trabajos` | `{"ids_trabajos": [1], "tecnico": "EMP-002"}` | 200 |
| 4 | Técnico | `POST /api/ordenes/{numero}/trabajos/1/inicio` | | 200 |
| 5 | Técnico | `POST /api/ordenes/{numero}/trabajos/1/completado` | | 200, «Lista para Entrega» |
| 6 | Caja | `POST /api/ordenes/{numero}/pago` | `{"monto": "3000.00", "forma": "Tarjeta"}` | 409 `PagoNoPermitido` |
| 7 | Caja | `POST /api/ordenes/{numero}/cargo-a-credito` | | 201, «Por Cobrar (Crédito)» |
| 8 | Asesor | `POST /api/ordenes/{numero}/entrega` | | 200, «Cerrada», con vencimiento a 15 días |

### 5. Cancelación

| # | Rol | Ruta | Cuerpo | Resultado |
|---|---|---|---|---|
| 1 | Asesor | `POST /api/ordenes/AUT-O004/cancelacion` | `{"motivo": "El cliente desiste"}` | 200, «Cancelada» |
| 2 | Asesor | `POST /api/ordenes/AUT-O003/cancelacion` | `{"motivo": "El cliente desiste"}` | 409 `CancelacionNoPermitida`: ya tiene cotización |
| 3 | Gerente | `GET /api/gerencia/ordenes?estado=Cancelada` | | 200, aparece `AUT-O004` |

### 6. Consulta pública

Sin token (**Logout**):

| # | Ruta | Resultado |
|---|---|---|
| 1 | `GET /api/consulta-de-estado?orden=AUT-O001&placas=PIAAUT001` | 200, «Cerrada» |
| 2 | `GET /api/consulta-de-estado?orden=AUT-O001&placas=XXX000` | 404 `OrdenNoEncontrada` |
