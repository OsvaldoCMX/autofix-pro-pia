# ADR-005 — La regla de $15,000 MXN como política del dominio

| Campo | Contenido |
|---|---|
| Estado | Aceptada (implementada como Specification en el PIA, ADR-006) |
| Fecha | 10/2026 (Unidad 3); actualizada en el PIA |
| Trazabilidad | N-04 · US-005 · CA-005, CA-007, CA-016 · RN-04 · BPMN compuerta «¿Monto mayor a $15,000 MXN?» |

## Contexto

El BRD establece que la cotización inicial mayor a $15,000 MXN requiere aprobación del Gerente antes de presentarse, y en la Unidad 2 se decidió que no aplica a las cotizaciones adicionales. Es la regla con más probabilidad de cambiar (monto o alcance).

## Alternativas consideradas

- **Condicional en ServicioDeCotizacion:** la aplicación decidiría el negocio.
- **Constante dentro de Cotizacion:** funciona, pero cada política nueva edita la clase.
- **Política inyectada en `Cotizacion.generar`** (elegida).

## Decisión

La política se inyecta en `Cotizacion.generar` y decide el estado inicial. En el PIA la política es la Specification `RequiereAprobacionGerencial = EsCotizacionInicial() & TotalMayorAlUmbral($15,000)`; el umbral es un parámetro.

## Consecuencias

- (+) Cumple Open/Closed: otra política es otra Specification, sin editar `Cotizacion`.
- (+) La regla se prueba de forma aislada, con su tabla de verdad.
- (−) Una abstracción más que explicar.
