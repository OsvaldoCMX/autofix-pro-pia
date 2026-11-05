# ADR-016 — Domain Events publicados después de confirmar y alertas internas

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 04/11/2026 (PIA) (amplía la decisión de la U3) |
| Trazabilidad | N-04, N-05, N-06, N-09 a N-11, N-14 · CA-007, CA-008, CA-009, CA-015, CA-017, CA-022, CA-032, CA-034 · `modelo-de-dominio.md` §6 |

## Contexto

El PIA exige Domain Events. En la U3 los Aggregates ya registraban eventos y la Unidad de Trabajo los entregaba al `PublicadorDeEventos` después de confirmar. Varias historias piden «notificar» a un empleado (CA-007, CA-008, CA-009, CA-015, CA-017, CA-022, CA-032, CA-034) y el BRD aclara que las alertas son internas (sin correo ni SMS).

## Alternativas consideradas

- **Llamar a las alertas desde los servicios:** acopla cada caso de uso a quién debe enterarse.
- **Publicar antes de confirmar:** podría avisar de un cambio que después se deshace.
- **Broker de mensajes (RabbitMQ, etc.):** excesivo para un taller.
- **Eventos registrados en el Aggregate, bitácora en la misma transacción y manejadores en proceso después de confirmar** (elegida).

## Decisión

Los eventos son `dataclass` inmutables con `ocurrido_en`. La Unidad de Trabajo los recolecta, guarda la **bitácora de eventos** (tabla `eventos`: tipo, datos JSON, fecha) en la misma transacción y, después de confirmar, `PublicadorEnProceso` los entrega a los manejadores registrados en el Composition Root. Los manejadores de `application/manejadores/alertas.py` crean `AlertaInterna` para el empleado correcto (asesor de la orden, técnico asignado, gerentes). Ningún manejador modifica otro Aggregate.

## Consecuencias

- (+) Los casos de uso no saben quién recibe alertas; agregar una reacción es agregar un manejador (Open/Closed).
- (+) La bitácora es la evidencia de «registrar evento o excepción» que piden las pruebas de transición.
- (−) Si un manejador falla después de confirmar, la alerta se pierde (el cambio de negocio sí queda); se registra en la bitácora de la aplicación.
