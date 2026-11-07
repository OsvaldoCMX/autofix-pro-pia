# Evidencias del PIA — AutoFix Pro

Capturas de la ejecución del sistema. Los tokens de producción no aparecen: en las capturas de Swagger local se usan los tokens de ejemplo de `.env.example`, y en producción el token está oculto.

| # | Archivo | Qué demuestra |
|---|---|---|
| 1 | `01-docker-listado-gerente.png` | Docker Compose local: `GET /api/gerencia/ordenes` devuelve las 60 órdenes del profesor (200). |
| 2 | `02-docker-consulta-publica.png` | Consulta pública sin token (CA-037): solo estado y fechas. |
| 3 | `03-mensaje-sin-token.png` | Mensaje claro al usuario: acceso sin token (401). |
| 4 | `04-mensaje-consulta-publica.png` | Mensaje claro al usuario: consulta con datos que no coinciden (404, CA-038, RN-20). |
| 5 | `05-mensaje-entrega-cancelada.png` | Mensaje claro al usuario: entregar una orden cancelada (409). |
| 6 | `06-ci-lista-de-ejecuciones.png` | GitHub Actions: ejecuciones del CI en verde. |
| 7 | `07-ci-detalle.png` | Detalle del CI: duración y artefacto `cobertura-y-reportes`. |
| 8 | `08-ci-pruebas-y-cobertura.png` | Paso de pruebas del CI con PostgreSQL: pruebas aprobadas y cobertura. |
| 9 | `09-supabase-verificacion.png` | Supabase: `03_verificacion.sql`, obtenido = esperado. |
| 10 | `10-supabase-ordenes.png` | Supabase: tabla `ordenes` con las 60 órdenes. |
| 11 | `11-render-logs-live.png` | Render: arranque de la aplicación y servicio en vivo. |
| 12 | `12-render-listado-gerente.png` | Producción (Render + Supabase): listado del gerente con las 60 órdenes. |
| 13 | `13-revision-de-plazos.png` | GitHub Actions «Revisión de plazos» llamando a producción: HTTP 200 (ADR-015). |
| 14 | `14-render-auto-deploy.png` | Render: despliegue automático después del CI (Auto-Deploy). |
| 15 | `15-render-version-final.png` | Render: versión final desplegada en vivo. |
