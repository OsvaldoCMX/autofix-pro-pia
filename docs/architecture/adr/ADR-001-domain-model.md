# ADR-001 — Domain Model como patrón de lógica de negocio

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 10/2026 (Unidad 3); actualizada en el PIA |
| Trazabilidad | N-02, N-03, N-04, N-07, N-10, N-11, N-15 · US-004, US-005, US-006, US-010, US-016, US-024, US-025 · CA-005, CA-007, CA-010, CA-020, CA-029, CA-042, CA-045 · BPMN Fases 2 a 6 |

## Contexto

El proceso cotización → autorización → refacciones → entrega tiene 13 estados de orden, 6 de cotización, 4 de trabajo y 2 de solicitud (Glosario, «Estados del sistema»), diez restricciones de proceso (BRD) y criterios de rechazo explícitos (CA-007, CA-009, CA-012, CA-020, CA-029, CA-042, CA-045, CA-046). Varias reglas dependen del estado y cruzan conceptos (cotización, orden, cliente). Es un proyecto universitario con alcance acotado.

## Alternativas consideradas

- **Transaction Script:** el más rápido, pero repetiría las validaciones de estado en cada caso de uso y no impediría que una función se salte una regla.
- **Table Module:** agrupa por tabla, pero las reglas que cruzan orden, cotización y cliente no tienen un lugar natural.
- **Domain Model** (elegida): cada regla vive en el objeto que protege sus datos; requiere más clases.

## Decisión

Domain Model para los Aggregates Orden de Servicio, Cotización, Cliente, Vehículo y Empleado. Las consultas de lectura (CQRS Queries) se resuelven con un lector simple, al estilo Transaction Script, porque solo arman vistas.

## Consecuencias

- (+) Las reglas se escriben una sola vez y se prueban sin base de datos.
- (+) Los nombres del código son los del Glosario.
- (−) Más clases y mapeo entre los datos de entrada (API) y el dominio.
- (−) Algunos casos de uso modifican dos Aggregates y necesitan Unidad de Trabajo (ADR-002).

**Actualización PIA.** Se completó el «trabajo posterior» de la U3: el modelo se extiende a recepción, diagnóstico, retiro anticipado, caja y cancelación, y las reglas compuestas se expresan como Specifications (ADR-006).
