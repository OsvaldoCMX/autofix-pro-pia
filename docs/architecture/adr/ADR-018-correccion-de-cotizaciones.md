# ADR-018 — Corrección de una cotización antes de la decisión del cliente

| Campo | Contenido |
|---|---|
| Estado | Aceptada |
| Fecha | 09/11/2026 (revisión del PIA, Fase 13) |
| Trazabilidad | H-PIA-21 · AU-17 · N-16 · US-026 · CA-047 a CA-051 · RN-25, RN-26 (y RN-04, RN-05, RN-12) · CE-05 · `modelo-de-dominio.md` §5.2 |

## Contexto

En la revisión del 09/11/2026 el profesor usó el sistema como un usuario del taller y buscó datos mal capturados que no se pudieran corregir. Una cotización con un importe o una descripción equivocados no tenía salida: `Cotizacion.ajustar` solo funciona en «Requiere Ajuste», un estado al que solo la lleva el Gerente cuando la rechaza (AU-17 de `auditoria-errores-de-usuario.md`, H-PIA-21). Además, la orden ya está «Cotizada» (no se puede generar otra cotización inicial), la inicial es siempre la v.1 y las versiones siguientes son las adicionales (RN-24), y la regla de $15,000 MXN (RN-04, CE-05) no debe poder saltarse con un cambio posterior.

## Alternativas consideradas

- **Ampliar `ajustar` a más estados:** un solo método, pero mezcla el ajuste que pidió el Gerente (RN-05: no regresa a revisión) con un error de captura del asesor, y permitiría subir el monto después de la aprobación sin que el Gerente lo viera (rompe CE-05).
- **Generar una cotización nueva con la versión siguiente:** conserva la anterior, pero las versiones v.2 en adelante son las cotizaciones adicionales (RN-24) y la orden ya está «Cotizada».
- **Regresar la cotización a «Requiere Ajuste»:** reutiliza `ajustar`, pero esa transición solo la dispara el Gerente con sus observaciones; el asesor dependería de él para arreglar un error de captura y la cotización ajustada ya no volvería a revisión.
- **Método `Cotizacion.corregir` con historial** (elegida).

## Decisión

`Cotizacion.corregir(lineas, motivo, asesor, fecha)` lo usa solo el Asesor (`POST /api/cotizaciones/{id}/correcciones`), con motivo obligatorio, y solo en «Pendiente de Aprobación Gerencial» o «Pendiente de Autorización del Cliente». En «Requiere Ajuste» se sigue usando `ajustar` (CA-009, RN-05 no cambia) y en «Autorizada», «Autorizada Parcialmente» o «Rechazada» no se corrige: el trabajo nuevo se cotiza con una cotización adicional (N-06). La cotización conserva su número y su versión; cada corrección guarda en la tabla `correcciones_de_cotizacion` el asesor, la fecha y hora, el motivo, el total anterior y el nuevo, el estado anterior y el nuevo, y las fechas de presentación y de aprobación gerencial que tenía. Después se vuelve a evaluar E1 `RequiereAprobacionGerencial`: (1) en «Pendiente de Autorización del Cliente», si E1 se cumple pasa a «Pendiente de Aprobación Gerencial» (**única transición nueva** de la máquina de la cotización), se borra `fecha_aprobacion_gerencial` y se emite `AprobacionGerencialRequerida` (alerta al Gerente); si no se cumple, se queda y conserva esa fecha; (2) en «Pendiente de Aprobación Gerencial», si E1 se sigue cumpliendo no hay transición (solo cambian las líneas) y, si ya no, pasa a «Pendiente de Autorización del Cliente» por la transición que ya existía. **Una cotización ajustada que después se corrige y sigue arriba de $15,000 regresa al Gerente:** RN-05 solo protege el ajuste que el propio Gerente pidió; una corrección cambia el monto que él revisó, así que debe verlo otra vez (RN-26). Al corregir, `fecha_presentacion` vuelve a quedar vacía y el asesor presenta la cotización otra vez; los recontactos anteriores se conservan como historial, pero `ultimo_contacto` (la base de E8) solo toma la nueva presentación y los recontactos posteriores a ella. Las observaciones del Gerente se conservan. Siempre se emite `CotizacionCorregida` (bitácora).

## Consecuencias

- (+) Un error de captura se corrige sin perder la evidencia: el historial dice quién, cuándo, por qué y cuánto cambió.
- (+) CE-05 se sigue cumpliendo: ningún monto inicial queda arriba de $15,000 MXN frente al cliente sin que el Gerente lo haya visto.
- (+) RN-05, RN-24 y la orden no cambian; la máquina de la cotización solo gana la transición «Pendiente de Autorización del Cliente» → «Pendiente de Aprobación Gerencial».
- (−) Una tabla más (`correcciones_de_cotizacion`) que hay que mapear en memoria y en la base.
- (−) Una corrección pequeña de una cotización mayor a $15,000 la regresa al Gerente; es una decisión consciente del equipo.
