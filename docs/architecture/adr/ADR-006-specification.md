# ADR-006 — Reglas compuestas con el patrón Specification

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 04/11/2026 (PIA) |
| Trazabilidad | RN-04, RN-07, RN-09, RN-11, RN-12, RN-14, RN-18, RN-19 · CA-007, CA-014, CA-019, CA-020, CA-023, CA-029, CA-040 a CA-046 |

## Contexto

El PIA exige al menos tres Specifications que combinen AND, OR y NOT. En el código de la U3/U5 varias reglas compuestas estaban escritas como `if` dentro de métodos (`VerificadorDeAutorizante`, `registrar_entrega`, `crear_solicitud_de_compra`, la política de $15,000) y las reglas nuevas del PIA (cancelación, vehículo retirado, alertas por plazo) también son condiciones compuestas.

## Alternativas consideradas

- **Seguir con `if` en los métodos:** menos clases, pero las condiciones no se pueden reutilizar ni probar por separado.
- **Motor de reglas o tablas de decisión externas:** flexible, pero excesivo y saca las reglas del modelo.
- **Specification con combinadores** (Evans y Fowler) (elegida).

## Decisión

Clase base `Especificacion[T]` en `domain/compartido/especificacion.py` con `es_satisfecha_por(candidato)` y los combinadores `y()`, `o()`, `no()` (operadores `&`, `|`, `~`). Las piezas pequeñas llevan nombres del Glosario y viven en el `especificaciones.py` de cada módulo. Ocho Specifications de negocio: E1 `RequiereAprobacionGerencial`, E2 `AutorizanteValido`, E3 `PuedeEntregarse`, E4 `PuedeCancelarse`, E5 `PuedeIniciarTrabajo`, E6 `PuedeSolicitarRefaccion`, E7 `RequiereAlertaDeRefaccion`, E8 `RequiereRecontacto` (composición en `modelo-de-dominio.md` §4). Son **puras** (sin efectos secundarios); el Aggregate las consulta y, si no se cumplen, lanza el error del negocio con un mensaje para el usuario.

## Consecuencias

- (+) Cada regla se lee como en el BRD y se prueba con su tabla de verdad.
- (+) Las mismas piezas sirven al dominio y a las consultas (p. ej. E7 en la revisión de plazos).
- (+) Las reglas de referencia del profesor se pueden armar con la misma clase en el arnés de pruebas sin tocar el dominio (ADR-013).
- (−) Más clases pequeñas; se mitiga agrupándolas por módulo.
