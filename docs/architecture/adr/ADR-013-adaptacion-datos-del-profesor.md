# ADR-013 — Adaptación de los datos ficticios del profesor

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 04/11/2026 (PIA) |
| Trazabilidad | H-PIA-03 · BRD §8 Supuestos · RN-23 · `casos_prueba.csv`, `transiciones_prueba.csv` |

## Contexto

El paquete `06_AutoFix_Pro` trae 40 propietarios, 20 servicios, 60 operaciones (todas «RECIBIDA»), 117 líneas de detalle, 120 casos de prueba y 20 pruebas de transición, con un flujo de referencia de 5 estados y dos reglas ilustrativas. El propio paquete aclara que es un **modelo de pruebas propuesto** y que, si difiere de los requerimientos del equipo, se deben documentar las diferencias y adaptar fixtures y oráculos, sin reemplazar los requerimientos propios.

## Alternativas consideradas

- **Cambiar el BRD para que coincida con los datos:** contradice la instrucción del profesor y el trabajo de U2/U3.
- **Ignorar los datos:** no cumple el PIA.
- **Cargar los datos con un adaptador y escribir oráculos propios** (elegida).

## Decisión

El estado inicial se carga con `database/02_datos_iniciales.sql`, generado desde los CSV por `scripts/db/generar_datos_iniciales.py` (UTF-8 con BOM, importes con `Decimal`): propietarios → `Cliente` Particular; operaciones → `OrdenDeServicio` «Recibida» con folio = `operacion_id`, placas derivadas de `referencia` y un `Vehiculo` ficticio por orden; catálogo y detalle → tablas de referencia `catalogo_servicios` y `servicios_solicitados`, que se usan para armar la cotización (precio × cantidad); las columnas sin equivalente quedan en `referencia_operaciones_profesor`. Los cambios de estado se hacen con la API, como pide el paquete. Un servicio inhabilitado se rechaza como dato inválido (422) y la cotización no se genera. `activo`, `es_preferente`, `promocion_activa` y `capacidad_o_stock` no tienen equivalente en el BRD y no cambian el dominio. Los 120 casos y las 20 transiciones se ejecutan en `tests/datos_profesor/` con **oráculos propios** y, como referencia, las reglas del profesor armadas con `Especificacion` dentro del arnés de pruebas. Resultados en `reportes/resultados_casos.csv` y `reportes/resultados_transiciones.csv`. Diferencias y oráculos: `docs/datos-profesor/README.md`.

## Consecuencias

- (+) Se usan todos los datos del profesor sin perder los requerimientos propios.
- (+) Cada diferencia queda explicada y es verificable con una prueba.
- (−) Algunos resultados difieren de la regla de referencia del profesor por decisión documentada (p. ej. clientes inactivos).
