# ADR-008 — API REST con FastAPI, OpenAPI y mapeo de errores

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 04/11/2026 (PIA) |
| Trazabilidad | Todos los CA (cada criterio tiene su ruta) · PIA: API REST, OpenAPI, códigos HTTP |

## Contexto

El PIA exige una API REST documentada con OpenAPI/Swagger y disponible en producción, y contrastar respuestas con 200/201, 400/409/422 y 404. En la U4 (TechStore) el equipo ya trabajó con FastAPI.

## Alternativas consideradas

- **Flask + extensión OpenAPI:** más configuración para documentar y validar.
- **Django REST Framework:** robusto, pero trae ORM y estructura propios que chocan con el Domain Model.
- **FastAPI** (elegida): OpenAPI automático, validación con Pydantic, `TestClient` para pruebas.

## Decisión

FastAPI con un router por área (`api/rutas/`), esquemas Pydantic separados del dominio (`api/esquemas/`) y un manejador de errores que traduce cada `ErrorDeDominio` a su código: 404 (`*NoEncontrada/o`), 409 (regla o transición violada), 422 (dato inválido), 403 (`TrabajoDeOtroTecnico`). El JSON mal formado responde 400 (se distingue del 422 de validación). Formato único de error `{error, detalle, codigo}`. Swagger UI en `/docs` también en producción, con el botón *Authorize* para el token (ADR-012). El contrato planeado está en `docs/api/README.md`.

## Consecuencias

- (+) La documentación de la API siempre coincide con el código.
- (+) Los tipos se validan antes de llegar al dominio; el dominio sigue siendo la autoridad de las reglas.
- (−) Algunas validaciones de formato quedan en dos lugares (Pydantic y Value Objects).
