# Datos del profesor (paquete «06_AutoFix_Pro») — adaptación y oráculos

El paquete `06_AutoFix_Pro/01_Alumno` es el «Data Center» del PIA: datos **ficticios** para cargar, probar y demostrar el sistema. El propio paquete aclara que su flujo y sus reglas son un **modelo de pruebas propuesto** y que, si difieren de los requerimientos del equipo, se deben **documentar las diferencias y adaptar fixtures y oráculos, sin reemplazar los requerimientos propios**. Este documento hace exactamente eso (ADR-013, hallazgo H-PIA-03).

> La carpeta `02_Docente` no se usa ni se incluye en el repositorio (indicación del paquete).

## 1. Contenido

| Archivo | Registros | Uso en AutoFix Pro |
|---|---|---|
| `actores.csv` | 40 propietarios (`AUT-C001`…) | Clientes **Particulares** |
| `catalogo.csv` | 20 servicios (`AUT-P001`…) | Catálogo de referencia para armar las líneas de la cotización |
| `operaciones.csv` | 60 operaciones, todas `RECIBIDA` (2026-10-01 a 2026-10-24) | Órdenes de Servicio «Recibida» |
| `detalle_operaciones.csv` | 117 líneas | Líneas de la cotización inicial (precio × cantidad) |
| `casos_prueba.csv` | 120 casos (60 `validar_operacion` + 60 `evaluar_beneficio`) | Pruebas de reglas con oráculos propios (sección 5) |
| `transiciones_prueba.csv` | 20 casos (`completar`, `cancelar`, `repetir_aprobacion`, `saltar_estado`, `aprobar` × 4) | Pruebas de la máquina de estados (sección 6) |

Formato: CSV UTF-8 **con BOM** (leer con `encoding="utf-8-sig"`), importes en MXN con dos decimales (convertir con `Decimal`, nunca `float`), fechas ISO 8601.

## 2. Cómo se cargan (`database/02_datos_iniciales.sql`)

| Dato del profesor | Se convierte en | Regla de conversión |
|---|---|---|
| `actor_id`, `nombre` | `clientes` (Particular): id y nombre | Teléfono y correo no vienen: se generan valores ficticios reconocibles (`81-0000-0001`, `aut-c001@ejemplo.test`). |
| `ciudad` | — | Informativo; no forma parte del modelo. |
| `operacion_id` | `NumeroOrden` (folio) | El folio es el mismo id (`AUT-O001`), para que los casos se puedan cruzar. |
| `fecha_solicitud` | `fecha_ingreso` | A las 09:00 de Monterrey, guardada en UTC. |
| `referencia` (`PIA_AUT_001`) | `Placas` del vehículo y motivo de ingreso | Placas = `PIA-AUT-001` (el Value Object las normaliza a `PIAAUT001`); motivo = «Servicio de referencia PIA_AUT_001». |
| — | `Vehiculo` | Uno por operación: marca «Ficticia», modelo «Referencia», año 2020, VIN `AUT` + 14 dígitos del número de operación. |
| `estado_inicial` = `RECIBIDA` | `EstadoOrden.RECIBIDA` | Sin cambios; los cambios de estado se hacen **con el código** (casos de uso), como pide el paquete. |
| `detalle` (`recurso_id`, `cantidad`) | `LineaDeCotizacion` | Descripción = descripción del catálogo + id; mano de obra = `precio_mxn × cantidad` con `Decimal`. Cantidad > 0. |
| `habilitado` = 0 | Error de dato (422) | Un servicio inhabilitado no se puede cotizar: la cotización de esa orden no se genera. |
| `autorizado` | Decisión del cliente | 1 = autoriza todos los trabajos; 0 = **no autoriza ninguno** (rechazo total, CA-012). |
| `activo`, `es_preferente`, `promocion_activa`, `capacidad_o_stock` | — | Sin equivalente en el BRD (ver diferencias D-01 a D-03). |

El script lo genera `scripts/db/generar_datos_iniciales.py` y además registra los 6 empleados de demostración (ADR-012). Solo carga el **estado inicial**: las 60 órdenes quedan «Recibida» y los cambios de estado se hacen con la API, así que todas las reglas del dominio aplican también a los datos del profesor. El catálogo y el detalle quedan en `catalogo_servicios` y `servicios_solicitados`, y las columnas sin equivalente (`activo`, `es_preferente`, `promocion_activa`, `autorizado`) en `referencia_operaciones_profesor`, solo como referencia. Kilometraje y combustible quedan vacíos (no vienen en los datos).

## 3. Diferencias entre el modelo propuesto y AutoFix Pro

| ID | Modelo del profesor | AutoFix Pro (BRD propio) | Decisión |
|---|---|---|---|
| D-01 | `puede_procesarse` exige **actor activo**. | El BRD no maneja clientes inactivos: un cliente recurrente siempre se atiende (US-003). | Se ignora `activo`. Las 9 operaciones de actores inactivos se procesan si cumplen lo demás. |
| D-02 | `beneficio_referencia`: preferente AND total ≥ 1500 AND NOT promoción. | Fuera de alcance: «No se manejan descuentos, promociones ni clientes preferentes» (BRD §5). | No se agrega al dominio. La regla propia comparable (composición AND sobre el total) es `RequiereAprobacionGerencial`. La regla del profesor se evalúa solo como **referencia** en el arnés de pruebas con la clase `Especificacion`. |
| D-03 | `capacidad_o_stock` por servicio. | «El sistema no controla existencias de inventario» (Glosario, Verificación de Disponibilidad). | Se ignora. Ninguna línea excede la capacidad (0 casos), así que no cambia ningún resultado. |
| D-04 | 5 estados: RECIBIDA → DIAGNOSTICADA → EN_REPARACION → ENTREGADA; CANCELADA desde RECIBIDA. | 13 estados de orden (Glosario §2). | Equivalencias: RECIBIDA = «Recibida»; DIAGNOSTICADA ≈ «En Diagnóstico» con diagnóstico registrado; EN_REPARACION = «En Reparación»; ENTREGADA = «Cerrada»; CANCELADA = «Cancelada» (agregada en v3.0 por H-PIA-01, también desde «En Diagnóstico»). |
| D-05 | La regla de ejemplo no menciona `habilitado`, pero el paquete pide «validar disponibilidad». | Un servicio inhabilitado es un dato inválido. | `validar_operacion` de AutoFix = TieneDetalle AND ServiciosHabilitados AND Autorizado. |
| D-06 | Precondición «técnico disponible». | El asesor asigna un técnico (CA-035); no hay agenda de técnicos en el BRD. | En las pruebas se asigna siempre el Técnico 1 de demostración. |
| D-07 | Un actor = «propietario». | Clientes particulares o de flotilla. | Todos los propietarios se cargan como particulares; las flotillas se prueban con fixtures propios (CA-028, CA-029, CA-039). |

## 4. Anomalías detectadas en los datos (y cómo se prueban)

| Anomalía | Operaciones | Resultado esperado en AutoFix |
|---|---|---|
| Actores inactivos (AUT-C007, AUT-C014, AUT-C021, AUT-C028, AUT-C035) | 9: AUT-O001, AUT-O002, AUT-O003, AUT-O004, AUT-O040, AUT-O041, AUT-O042, AUT-O043, AUT-O044 | Se procesan (D-01). |
| No autorizadas (`autorizado` = 0) | 7: AUT-O008, AUT-O016, AUT-O024, AUT-O032, AUT-O040, AUT-O048, AUT-O056 | Rechazo total: cotización «Rechazada», orden «Cotizada»; no se pueden asignar trabajos (409); se entregan sin reparación. |
| Servicio inhabilitado (AUT-P011) | 6: AUT-O005, AUT-O015, AUT-O020, AUT-O035, AUT-O040, AUT-O055 | La cotización no se genera (422); la orden queda «En Diagnóstico». |
| Sin líneas de detalle | 2: AUT-O013, AUT-O039 | La cotización no se genera (422 `CotizacionSinTrabajos`). |
| Promoción activa | 6: AUT-O009, AUT-O018, AUT-O027, AUT-O036, AUT-O045, AUT-O054 | Sin efecto en AutoFix (D-02). |
| Ninguna supera $15,000 MXN | máximo AUT-O008 = $12,887.00; 52 de 60 son ≥ $1,500 | La aprobación gerencial (CA-007 a CA-009) se prueba con fixtures propios (p. ej. una cotización de $16,500.00) y con la matriz PIA de la U5. |
| Clientes preferentes (AUT-C005, AUT-C010, AUT-C015, AUT-C020, AUT-C025, AUT-C030, AUT-C035, AUT-C040) | — | Sin efecto en AutoFix (D-02). |

`AUT-O040` combina tres anomalías (actor inactivo, no autorizada y servicio inhabilitado): en AutoFix gana la validación del dato (422 por el servicio inhabilitado), porque la cotización ni siquiera se puede generar.

## 5. Oráculos de `casos_prueba.csv`

Archivo completo: [`oraculos_casos.csv`](oraculos_casos.csv) (120 filas: referencia del profesor, resultado esperado en AutoFix, regla, diferencia y explicación). Resumen:

| Tipo de prueba | Regla del profesor (referencia) | Regla de AutoFix | Verdaderos (profesor) | Verdaderos (AutoFix) | Coinciden |
|---|---|---|---|---|---|
| `validar_operacion` | activo AND detalle AND autorización | TieneDetalle AND ServiciosHabilitados AND Autorizado | 43 | 46 | 47 de 60 (las 13 diferencias son D-01 o D-05) |
| `evaluar_beneficio` | preferente AND total ≥ 1500 AND NOT promoción | No aplica (D-02); se registra `RequiereAprobacionGerencial` | 9 | 0 | Diferencia documentada (D-02) |

La prueba `tests/datos_profesor/test_casos_prueba.py` recorre los 120 casos, compara el resultado con este oráculo y escribe `reportes/resultados_casos.csv` con las columnas del profesor (`resultado_alumno` = resultado obtenido) más la evidencia (nombre de la prueba y mensaje del dominio).

## 6. Oráculos de `transiciones_prueba.csv`

Interpretación de las acciones sugeridas con los casos de uso de AutoFix:

- **completar**: flujo completo hasta entregar el vehículo (asignar técnico → diagnóstico → cotización → presentar → decisión → asignar y completar trabajos → pago → entrega).
- **cancelar**: cancelación con motivo desde «Recibida» (US-025).
- **repetir_aprobacion**: registrar dos veces la decisión del cliente sobre la misma cotización.
- **saltar_estado**: intentar entregar una orden que sigue «Recibida».
- **aprobar**: flujo hasta registrar la decisión del cliente.

| Caso | Operación | Acción | Flujo en AutoFix | Estado final esperado | Evento o excepción | HTTP |
|---|---|---|---|---|---|---|
| AUT-S001 | AUT-O001 | completar | Asignar técnico → diagnóstico → generar cotización → presentar → registrar decisión → asignar y completar trabajos → pago → entrega | Cerrada | VehiculoEntregado (cadena completa de eventos) | 200 |
| AUT-S002 | AUT-O002 | cancelar | Cancelar con motivo desde «Recibida» (E4) | Cancelada | OrdenCancelada | 200 |
| AUT-S003 | AUT-O003 | repetir_aprobacion | Asignar técnico → diagnóstico → generar cotización → presentar → registrar decisión dos veces | Autorizada | OperacionDeCotizacionNoPermitida (la decisión ya está registrada) | 409 |
| AUT-S004 | AUT-O004 | saltar_estado | Intentar entregar una orden «Recibida» (saltar a «Cerrada») | Recibida | EntregaNoPermitida (E3 no se cumple) | 409 |
| AUT-S005 | AUT-O005 | aprobar | Asignar técnico → diagnóstico → generar cotización | En Diagnóstico | ValorInvalido (servicio AUT-P011 inhabilitado) | 422 |
| AUT-S006 | AUT-O006 | completar | Asignar técnico → diagnóstico → generar cotización → presentar → registrar decisión → asignar y completar trabajos → pago → entrega | Cerrada | VehiculoEntregado (cadena completa de eventos) | 200 |
| AUT-S007 | AUT-O007 | cancelar | Cancelar con motivo desde «Recibida» (E4) | Cancelada | OrdenCancelada | 200 |
| AUT-S008 | AUT-O008 | repetir_aprobacion | Asignar técnico → diagnóstico → generar cotización → presentar → registrar decisión dos veces | Cotizada | OperacionDeCotizacionNoPermitida (la decisión ya está registrada) | 409 |
| AUT-S009 | AUT-O009 | saltar_estado | Intentar entregar una orden «Recibida» (saltar a «Cerrada») | Recibida | EntregaNoPermitida (E3 no se cumple) | 409 |
| AUT-S010 | AUT-O010 | aprobar | Asignar técnico → diagnóstico → generar cotización → presentar → registrar decisión (autoriza todo) | Autorizada | CotizacionAutorizada + OrdenAutorizada | 200 |
| AUT-S011 | AUT-O011 | completar | Asignar técnico → diagnóstico → generar cotización → presentar → registrar decisión → asignar y completar trabajos → pago → entrega | Cerrada | VehiculoEntregado (cadena completa de eventos) | 200 |
| AUT-S012 | AUT-O012 | cancelar | Cancelar con motivo desde «Recibida» (E4) | Cancelada | OrdenCancelada | 200 |
| AUT-S013 | AUT-O013 | repetir_aprobacion | Asignar técnico → diagnóstico → generar cotización | En Diagnóstico | CotizacionSinTrabajos (sin detalle) | 422 |
| AUT-S014 | AUT-O014 | saltar_estado | Intentar entregar una orden «Recibida» (saltar a «Cerrada») | Recibida | EntregaNoPermitida (E3 no se cumple) | 409 |
| AUT-S015 | AUT-O015 | aprobar | Asignar técnico → diagnóstico → generar cotización | En Diagnóstico | ValorInvalido (servicio AUT-P011 inhabilitado) | 422 |
| AUT-S016 | AUT-O016 | completar | Asignar técnico → diagnóstico → generar cotización → presentar → registrar decisión (rechazo total) → asignar trabajos | Cotizada | TrabajoNoAutorizado (no hay trabajos autorizados) | 409 |
| AUT-S017 | AUT-O017 | cancelar | Cancelar con motivo desde «Recibida» (E4) | Cancelada | OrdenCancelada | 200 |
| AUT-S018 | AUT-O018 | repetir_aprobacion | Asignar técnico → diagnóstico → generar cotización → presentar → registrar decisión dos veces | Autorizada | OperacionDeCotizacionNoPermitida (la decisión ya está registrada) | 409 |
| AUT-S019 | AUT-O019 | saltar_estado | Intentar entregar una orden «Recibida» (saltar a «Cerrada») | Recibida | EntregaNoPermitida (E3 no se cumple) | 409 |
| AUT-S020 | AUT-O020 | aprobar | Asignar técnico → diagnóstico → generar cotización | En Diagnóstico | ValorInvalido (servicio AUT-P011 inhabilitado) | 422 |

Archivo: [`oraculos_transiciones.csv`](oraculos_transiciones.csv). La prueba `tests/datos_profesor/test_transiciones.py` ejecuta cada caso, compara con el oráculo y escribe `reportes/resultados_transiciones.csv` con el estado final, los eventos de la bitácora o la excepción y su código HTTP.

## 7. Totales calculados (muestra)

| Operación | Detalle | Total (Decimal) |
|---|---|---|
| AUT-O001 | AUT-P009 × 3 + AUT-P014 × 4 | $7,909.00 |
| AUT-O005 | AUT-P001 × 3 + AUT-P006 × 4 + AUT-P011 × 1 | $5,002.00 |
| AUT-O007 | AUT-P007 × 1 + AUT-P012 × 2 | $3,065.00 |
| AUT-O008 | AUT-P010 × 2 + AUT-P015 × 3 + AUT-P020 × 4 | $12,887.00 |
| AUT-O013 |  | $0.00 |

Los totales de las 60 operaciones están en `oraculos_casos.csv` (columna «explicacion» de `evaluar_beneficio`).
