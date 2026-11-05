# ADR-004 — Repository en términos del dominio

| Campo | Contenido |
|---|---|
| Estado | Aceptada (el gestor de base de datos se define en ADR-009) |
| Fecha | 10/2026 (Unidad 3); actualizada en U5 y en el PIA |
| Trazabilidad | N-01 a N-03 · CE-01, CE-06 · BRD, Restricciones técnicas (almacenar digitalmente documentos) |

## Contexto

El BRD exige guardar digitalmente las autorizaciones (CE-01) y los documentos generados. En la U3 el gestor no estaba definido y se esperaba un «Data Center» del profesor. En el PIA se aclaró que el Data Center es el **paquete de datos ficticios** `06_AutoFix_Pro` (CSV) y que el gestor lo elige el equipo.

## Alternativas consideradas

- **Elegir un gestor y acceder a él desde los servicios:** amarra el diseño a una tecnología.
- **Usar el ORM dentro del dominio:** mezcla las reglas del negocio con detalles del framework.
- **Repository + Unidad de Trabajo como interfaces** (elegida), con implementación en memoria y en base de datos.

## Decisión

Los repositorios (`RepositorioDeOrdenes`, `RepositorioDeCotizaciones`, `RepositorioDeClientes`, `RepositorioDeVehiculos`, `RepositorioDeEmpleados`) son interfaces del dominio con métodos de negocio (`obtener`, `agregar`, `guardar`, `siguiente_numero`…). Hay dos implementaciones que cumplen el mismo contrato: en memoria (pruebas unitarias) y SQLAlchemy (U5 y PIA). `obtener()` siempre responde con el error del negocio (p. ej. `OrdenNoEncontrada`) si no existe.

## Consecuencias

- (+) El dominio y la aplicación no cambiaron al pasar de memoria a base de datos (comprobado en la U5 con pruebas de contrato).
- (+) Las pruebas unitarias no necesitan base de datos.
- (−) Hay que mantener el mapeo entre tablas y objetos del dominio.

**Actualización U5/PIA.** En la U5 se implementaron los adaptadores SQLAlchemy con SQLite en memoria y pruebas de contrato memoria vs. base de datos. En el PIA el gestor de producción es PostgreSQL (ADR-009).
