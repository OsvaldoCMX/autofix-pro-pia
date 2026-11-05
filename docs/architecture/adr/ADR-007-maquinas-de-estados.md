# ADR-007 — Máquinas de estados declarativas por tabla

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 04/11/2026 (PIA) |
| Trazabilidad | RN-22 · Glosario §2 · todos los CA que cambian un estado · `transiciones_prueba.csv` |

## Contexto

Hay cuatro objetos con estado: Orden (13 estados), Cotización (6), Trabajo (4) y Solicitud de Compra (2). En la U3 solo la orden tenía tabla de transiciones; la cotización y el trabajo validaban con `if`. El PIA exige una máquina de estados y el profesor entrega pruebas de transición (`completar`, `cancelar`, `repetir_aprobacion`, `saltar_estado`, `aprobar`).

## Alternativas consideradas

- **Patrón State** (una clase por estado): 25 clases para reglas que casi siempre son «desde X solo se puede ir a Y».
- **Librería externa** (p. ej. `transitions`): agrega una dependencia y saca las reglas del dominio.
- **Tabla declarativa + clase genérica** (elegida).

## Decisión

`MaquinaDeEstados[E]` genérica en `domain/compartido/maquina_de_estados.py` con la tabla `{estado: {destinos}}`, los estados finales y `validar(actual, nuevo)`, que lanza `TransicionDeEstadoNoPermitida`. Cada objeto tiene su tabla (`estados.py`). Los métodos del Aggregate validan **antes** de modificar nada y usan las Specifications como guardas. Los diagramas de estados se dibujan a partir de las mismas tablas.

## Consecuencias

- (+) Una sola fuente de verdad para código, diagramas y pruebas.
- (+) Una prueba parametrizada recorre **todas** las parejas (estado, destino) y confirma cuáles se permiten y cuáles no.
- (−) Las guardas complejas siguen en los métodos del Aggregate (con Specifications).
