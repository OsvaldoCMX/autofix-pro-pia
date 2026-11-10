# Arquitectura — AutoFix Pro (PIA v3.0)

Arquitectura en capas con **Domain-Driven Design**: un Domain Model rico (Aggregates, Value Objects, Specifications, máquinas de estados y Domain Events) protegido por una Service Layer, con persistencia detrás de Repository + Unit of Work y una API REST como entrada. Continúa el diseño de la Unidad 3 y la implementación de la Unidad 5.

## Documentos

| Documento | Contenido |
|---|---|
| [modelo-de-datos.md](modelo-de-datos.md) | Las 18 tablas de PostgreSQL / Supabase con sus columnas, llaves y restricciones, y los scripts de `database/`. |
| [modelo-de-dominio.md](modelo-de-dominio.md) | Fichas de Aggregate, Value Objects, las 8 Specifications, las 4 máquinas de estados (tablas de transiciones), Domain Events con sus reacciones y errores del dominio. |
| [decisiones-tecnicas.md](decisiones-tecnicas.md) | Stack, estructura del repositorio (`src/domain`, `src/application`, `src/infrastructure`, `src/api`), variables de entorno, convenciones de la API, roles, datos de demostración, estrategia de pruebas y alcance P1/P2. |
| [patrones.md](patrones.md) | Patrones aplicados, dónde y por qué; patrones descartados. |
| [solid.md](solid.md) | Revisión SOLID de la U3 (S-01 a S-07) y hallazgos nuevos del PIA (S-08 a S-12). |
| [adr/](adr/README.md) | 18 decisiones de arquitectura (ADR-001 a ADR-005 de la U3, actualizados; ADR-006 a ADR-016 del PIA; ADR-017 y ADR-018 de la revisión del 09/11/2026). |

## Diagramas (`diagramas/`: fuente PlantUML `.puml` + `.png` + `.svg`)

| Diagrama | Qué muestra |
|---|---|
| `mapa-dominio` | Los 5 Aggregates, sus entidades y Value Objects, referencias por identidad, Specifications E1–E8, reglas y Domain Events. |
| `clases-dominio` | Clases de `src/domain`: Aggregates con sus métodos, `Especificacion<T>`, `MaquinaDeEstados<E>`, eventos y repositorios. |
| `arquitectura-capas` | Dependencias entre `api`, `application`, `domain` e `infrastructure` (regla de dependencias y Composition Root). |
| `secuencia-generar-cotizacion` | CA-005/CA-007: de la ruta HTTP a la Specification E1 y la alerta al Gerente. |
| `secuencia-registrar-decision` | CA-010/CA-012/CA-029: Specification E2 y la Unidad de Trabajo con dos Aggregates. |
| `secuencia-entrega` | CA-041/CA-042: Specification E3 y el vencimiento del crédito desde la entrega. |
| `estados-orden` | Máquina de estados de la Orden de Servicio (13 estados) con guardas y criterios. |
| `estados-cotizacion-trabajo-solicitud` | Máquinas de estados de Cotización (6), Trabajo (4) y Solicitud de Compra (2). |
| `modelo-de-datos` | Diagrama entidad-relación de la base (18 tablas). |
| `despliegue` | Docker Compose (db, app, tests), GitHub Actions (CI y revisión de plazos) y Render (Web Service) y Supabase (PostgreSQL). |

Para regenerar las imágenes: `java -jar plantuml.jar -tpng -tsvg docs/architecture/diagramas/*.puml` (con `-DPLANTUML_LIMIT_SIZE=16384` para los diagramas grandes).

## Resumen de la arquitectura

```
HTTP ──► src/api (FastAPI: rutas, esquemas, seguridad, errores, dependencias)
            │ Command / Query
            ▼
         src/application (12 servicios, 11 consultas, manejadores de eventos, puertos)
            │ obtiene Aggregates por la Unidad de Trabajo y les pide la operación
            ▼
         src/domain (Aggregates · Value Objects · Specifications · Máquinas de estados · Domain Events)
            ▲ implementan las interfaces
            │
         src/infrastructure (SQLAlchemy/PostgreSQL, memoria, PDF, reloj, publicador, configuración)
```

**Regla de dependencias:** el dominio no conoce FastAPI, Pydantic ni SQLAlchemy; la aplicación solo conoce interfaces; únicamente `api/dependencias.py` decide qué implementación se usa.
