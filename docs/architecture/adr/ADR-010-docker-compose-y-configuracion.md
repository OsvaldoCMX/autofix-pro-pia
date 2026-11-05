# ADR-010 — Docker Compose (db, app, tests) y configuración por variables de entorno

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 04/11/2026 (PIA) |
| Trazabilidad | PIA: Docker Compose, variables de entorno · Restricciones técnicas del BRD |

## Contexto

El PIA exige Docker Compose con base de datos, aplicación y pruebas, configuración por variables de entorno (12-Factor) y un `.env.example` sin secretos.

## Alternativas consideradas

- **Instalar todo a mano en cada computadora:** frágil y distinto en cada integrante.
- **Solo un Dockerfile:** no levanta la base ni corre las pruebas contra ella.
- **Docker Compose con tres servicios** (elegida).

## Decisión

`Dockerfile` basado en `python:3.12-slim`, usuario sin privilegios, `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`. `docker-compose.yml` con: **db** (`postgres:16-alpine`, volumen, *healthcheck* `pg_isready` y la carpeta `database/` montada en `/docker-entrypoint-initdb.d` para crear el esquema y cargar los datos iniciales), **app** (depende de `db` sano, `env_file: .env`, puerto 8000, *healthcheck* `/health`) y **tests** (misma imagen, perfil `tests`, ejecuta `pytest --cov=src --cov-branch --cov-fail-under=80` contra `db`). Toda la configuración se lee del entorno en `infrastructure/config.py`; `.env.example` tiene valores de ejemplo y `.env` está en `.gitignore`.

## Consecuencias

- (+) Cualquiera levanta el sistema con `docker compose up` y corre las pruebas con `docker compose run --rm tests`.
- (+) La aplicación corre igual en local, en el CI y en Render.
- (−) En Windows se necesita Docker Desktop.
