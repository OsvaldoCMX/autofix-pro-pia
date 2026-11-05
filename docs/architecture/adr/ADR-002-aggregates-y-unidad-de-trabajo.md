# ADR-002 — Límites de los Aggregates y Unidad de Trabajo

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 10/2026 (Unidad 3); actualizada en el PIA |
| Trazabilidad | N-03, N-06, N-10 · US-006, US-009, US-010, US-011 · CA-010, CA-019, CA-022 · BPMN Fases 3 y 4 |

## Contexto

Una orden puede tener varias cotizaciones (inicial v.1 y adicionales v.2+; US-009). El Gerente revisa cotizaciones sin tocar la orden (US-005). La decisión del cliente cambia la cotización y crea los trabajos de la orden (CA-010). La orden debe estar «En Espera de Refacción» mientras exista una solicitud «Solicitada» (CA-019, CA-022). Vehículo y Empleado existen fuera de una orden (un vehículo regresa varias veces; un técnico atiende muchas órdenes).

## Alternativas consideradas

- **A)** Un solo Aggregate Orden con sus cotizaciones dentro: consistencia total, pero un objeto enorme y el Gerente tendría que cargar toda la orden.
- **B)** Cotización separada y Solicitud de Compra como Aggregate propio: Compras independiente, pero el invariante de «En Espera de Refacción» quedaría entre dos Aggregates.
- **C)** Cotización separada y Solicitud dentro de la Orden (elegida).

## Decisión

Opción C. Aggregates: Orden de Servicio (con Trabajos, Solicitudes de Compra, Fallas Adicionales, Recibo), Cotización (con sus Líneas y la Decisión), Cliente, Vehículo y Empleado. La relación entre Aggregates es solo por identidad (`numero_orden`, `id_cliente`, `placas`, `id_empleado`). Cuando un caso de uso modifica dos Aggregates (generar cotización + marcar la orden «Cotizada»; registrar decisión + crear trabajos) ambos cambios se confirman en la misma Unidad de Trabajo.

## Consecuencias

- (+) Cada Aggregate es pequeño y protege sus invariantes.
- (+) La regla de la espera de refacciones se cumple en una sola transacción.
- (−) Dos casos de uso rompen la recomendación de «un Aggregate por transacción»; lo aceptamos porque el BRD exige evidencia consistente de la autorización (CE-01) y la Unidad de Trabajo lo garantiza.
- (−) Compras consulta las solicitudes a través del lector, no de un repositorio propio.
