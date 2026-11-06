# ADR-011 — Despliegue en Render y CI/CD con GitHub Actions

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 04/11/2026 (PIA) |
| Trazabilidad | PIA: despliegue, CI/CD, URL pública |

## Contexto

El PIA exige una URL pública (Render, Railway o Fly.io) con Swagger disponible, y un pipeline de CI/CD. El repositorio está en GitHub y el CI de la U5 ya corre en GitHub Actions.

## Alternativas consideradas

- **Railway:** sencillo, pero el uso gratuito es por créditos de prueba.
- **Fly.io:** flexible, pero pide tarjeta y su capa gratuita cambió.
- **Render** (elegida): Web Service con Docker gratuito y despliegue desde GitHub; la base vive en Supabase (ADR-009).

## Decisión

**CI** (`.github/workflows/ci.yml`): en cada *push* y *pull request* instala dependencias, corre Ruff y `pytest` con cobertura ≥ 80 % usando PostgreSQL como servicio, y publica `htmlcov/`, `coverage.xml` y `reportes/` como artefactos. **CD:** Render Web Service (tipo Docker) conectado a `main` con *Auto-Deploy* = «After CI Checks Pass», *health check* en `/health` y las variables de entorno en el panel de Render; `DATABASE_URL` es la cadena *Session pooler* de Supabase. Conviene elegir regiones cercanas: Supabase «East US (North Virginia)» y Render «Virginia (US East)».

## Consecuencias

- (+) Solo se despliega lo que pasó las pruebas.
- (−) El servicio gratuito se duerme tras 15 minutos sin tráfico y tarda alrededor de un minuto en despertar: abrir `/health` antes de la presentación.
- (−) 750 horas gratuitas al mes y disco efímero (por eso los archivos van a la base, ADR-014).
- (−) Si Supabase pausa el proyecto por inactividad, la API responde con error de base de datos hasta reanudarlo desde el panel (ADR-009, ADR-015).
