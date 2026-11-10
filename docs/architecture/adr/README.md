# Registro de decisiones de arquitectura (ADR)

Cada ADR sigue los campos de la guía de la Unidad 3: estado, fecha, contexto, alternativas, decisión, consecuencias y trazabilidad. ADR-001 a ADR-005 vienen de la U3 (actualizados); ADR-006 a ADR-016 son del PIA; desde ADR-017 salen de la revisión del 09/11/2026 (Fases 12 a 20). Todas están aceptadas por el equipo (las propuestas ADR-009, 011, 014 y 015 se confirmaron el 04/11/2026).

| ADR | Decisión | Estado | Necesidades |
|---|---|---|---|
| [ADR-001](ADR-001-domain-model.md) | Domain Model como patrón de lógica de negocio | Aceptada | N-02 a N-04, N-07, N-10, N-11, N-15 |
| [ADR-002](ADR-002-aggregates-y-unidad-de-trabajo.md) | Límites de los Aggregates y Unidad de Trabajo | Aceptada | N-03, N-06, N-10 |
| [ADR-003](ADR-003-service-layer-y-cqrs.md) | Service Layer por caso de uso y CQRS básico | Aceptada | N-02 a N-05, N-08 a N-11, N-13 a N-15 |
| [ADR-004](ADR-004-repository.md) | Repository en términos del dominio | Aceptada (el gestor de base de datos se define en ADR-009) | N-01 a N-03 |
| [ADR-005](ADR-005-politica-de-aprobacion-gerencial.md) | La regla de $15,000 MXN como política del dominio | Aceptada (implementada como Specification en el PIA, ADR-006) | N-04 |
| [ADR-006](ADR-006-specification.md) | Reglas compuestas con el patrón Specification | Aceptada | N-03, N-04, N-05, N-07, N-09 a N-12, N-14, N-15 |
| [ADR-007](ADR-007-maquinas-de-estados.md) | Máquinas de estados declarativas por tabla | Aceptada | N-01 a N-15 |
| [ADR-008](ADR-008-api-rest-fastapi.md) | API REST con FastAPI, OpenAPI y mapeo de errores | Aceptada | N-01 a N-15 |
| [ADR-009](ADR-009-postgresql-supabase.md) | PostgreSQL 16: Docker en local y Supabase en producción | Aceptada | N-01 a N-03, N-11 |
| [ADR-010](ADR-010-docker-compose-y-configuracion.md) | Docker Compose (db, app, tests) y configuración por variables de entorno | Aceptada | Restricciones técnicas |
| [ADR-011](ADR-011-despliegue-render-y-ci-cd.md) | Despliegue en Render y CI/CD con GitHub Actions | Aceptada | Restricciones técnicas |
| [ADR-012](ADR-012-seguridad-por-token.md) | Seguridad con token sencillo por empleado y rol | Aceptada | N-08, N-09, N-13 |
| [ADR-013](ADR-013-adaptacion-datos-del-profesor.md) | Adaptación de los datos ficticios del profesor | Aceptada | N-01 a N-04, N-11, N-15 |
| [ADR-014](ADR-014-documentos-y-archivos.md) | PDF generados al vuelo y fotos guardadas en la base de datos | Aceptada | N-01, N-02, N-11, N-12 |
| [ADR-015](ADR-015-revision-periodica-de-plazos.md) | Revisión periódica de plazos con un endpoint y un workflow programado | Aceptada | N-05, N-14 |
| [ADR-016](ADR-016-domain-events.md) | Domain Events publicados después de confirmar y alertas internas | Aceptada | N-04 a N-06, N-09 a N-11, N-14 |
| [ADR-018](ADR-018-correccion-de-cotizaciones.md) | Corrección de una cotización antes de la decisión del cliente | Aceptada | N-02, N-04, N-16 |
