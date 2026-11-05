# Registro de cambios y hallazgos del PIA (v3.0)

Antes de empezar la implementación del PIA se revisaron juntos el BRD, las User Stories, el Glosario y el BPMN (U2), la arquitectura (U3), el código y las pruebas (U5), los requisitos del PIA y el paquete de datos del profesor. Esta tabla registra cada hallazgo, la decisión del equipo y los archivos que cambiaron. Ningún hallazgo cambia el objetivo del sistema ni el flujo principal del BPMN.

## 1. Hallazgos

| ID | Hallazgo | Origen | Decisión del equipo | Archivos afectados |
|---|---|---|---|---|
| H-PIA-01 | No existía forma de cerrar una orden cuando el cliente desiste **antes** de la cotización; el paquete del profesor incluye la acción «cancelar» y el estado CANCELADA. | Datos del profesor (`transiciones_prueba.csv`, flujo de referencia) | Nueva necesidad N-15, US-025, CA-044 y CA-045, estado «Orden · Cancelada» (13 estados de orden, 25 en total), Specification E4 `PuedeCancelarse`, evento `OrdenCancelada`. Solo antes de la cotización; después se usa el rechazo total. Las órdenes canceladas cuentan como cerradas en el listado del Gerente. | BRD (§2, §4, §5, §6, restricción 10), `user-stories.md`, `08_cancelacion.feature`, `glosario.md`, BPMN (caso especial 2), modelo de dominio, diagramas de estados |
| H-PIA-02 | El vencimiento del crédito de flotilla era inconsistente: el Glosario decía «después de la entrega», el código de la U3 lo calculaba desde el registro del cargo y CA-039 no lo aclaraba. | Revisión cruzada Glosario ↔ código | Se cuenta **desde la entrega**: CA-039 registra el monto y CA-041 fija el vencimiento (entrega + 15 días naturales). | BRD (§2, N-07, restricción 5), US-022, CA-039, CA-041, Glosario, `CargoACredito`, BPMN (cambios 4 y 5), secuencia de entrega |
| H-PIA-03 | El «Data Center» del profesor es un paquete de CSV ficticios con un flujo de referencia distinto al del equipo. | Paquete `06_AutoFix_Pro` | Se usa como datos de prueba y demostración sin reemplazar los requisitos; las diferencias y los oráculos están documentados. | BRD §8, ADR-013, `datos-profesor/` |
| H-PIA-04 | El Glosario definía el rechazo parcial como aceptar «trabajos o refacciones», pero la unidad que se autoriza es el trabajo (línea de cotización con sus refacciones). | Glosario ↔ CA-010 ↔ código | «Acepta solo algunos de los trabajos (cada trabajo se autoriza junto con sus refacciones)». | `glosario.md` |
| H-PIA-05 | El diagnóstico se guardaba como un solo texto, pero CA-032 pide fallas, trabajos y refacciones recomendados, con fecha y hora. | CA-032 ↔ código U3/U5 | `Diagnostico` como Value Object con fallas, recomendaciones, técnico y fecha/hora. | Glosario, modelo de dominio, mapa de dominio |
| H-PIA-06 | El código permitía iniciar un trabajo con la orden «Pausada por Retiro de Vehículo» (el vehículo no está en el taller) y no verificaba que fuera el técnico asignado. | Revisión de la máquina de estados | Nuevo CA-046 y Specification E5 `PuedeIniciarTrabajo` (Pendiente AND AsignadoAlTecnico AND NOT OrdenPausadaPorRetiro). | `user-stories.md`, `05_reparacion_y_refacciones.feature`, modelo de dominio |
| H-PIA-07 | Al llegar la última refacción (CA-022) o al reactivar la orden (CA-025) se regresaba a «Autorizada» aunque ya hubiera trabajos iniciados, y desde «Autorizada» no se puede pasar a «Lista para Entrega». | Revisión de la máquina de estados | Si ya hay trabajos iniciados se regresa a «En Reparación» (nueva transición «Pausada por Retiro de Vehículo» → «En Reparación»). Completar el último trabajo con una refacción pendiente se rechaza (409). | CA-022, CA-025, modelo de dominio, diagrama de estados, BPMN (cambio 7) |
| H-PIA-08 | CA-008 pide «registrar la fecha de aprobación» del Gerente, pero el código no la guardaba. | CA-008 ↔ código | `Cotizacion.fecha_aprobacion_gerencial`. | Modelo de dominio, mapa de dominio |
| H-PIA-09 | ADR-004 dejaba el gestor de base de datos sin definir («Data Center»). | ADR-004 | ADR-009: PostgreSQL 16 (Docker en local, **Supabase** en producción) con esquema oficial `database/01_esquema.sql` y datos iniciales `02_datos_iniciales.sql`. | ADR-004, ADR-009, `modelo-de-datos.md`, `database/` |
| H-PIA-10 | Las alertas por tiempo no decían qué pasa después del aviso o del recontacto. | CA-023, CA-040 | CA-023: después de registrar el aviso al cliente ya no se repite la alerta (NOT en E7). CA-040: el plazo de 48 h vuelve a contar desde el último recontacto (E8). | CA-023, CA-040, modelo de dominio |
| H-PIA-11 | CA-027 solo permitía el recibo con la orden «Pagada»; después de entregar el vehículo (orden «Cerrada») ya no se podría reimprimir. | CA-027 ↔ máquina de estados | El recibo se genera con cualquier orden que tenga pago registrado («Pagada» o «Cerrada»). | CA-027 |
| H-PIA-12 | Si el cliente no ha decidido una cotización adicional y el técnico termina los trabajos originales, la orden pasaría a «Lista para Entrega» antes de la decisión; el BPMN (Fase 5) espera la decisión. | BPMN Fase 5 ↔ CA-015 | La orden no queda lista mientras haya una cotización adicional sin decisión (CA-015); si la adicional se rechaza y los originales ya estaban completos, pasa a «Lista para Entrega» (CA-018). | CA-015, CA-018, modelo de dominio |
| H-PIA-13 | El reporte de pruebas de la U3 (caso 14) usaba el estado «Entregada», que no existe en el Glosario. | Reporte de pruebas U3 | El estado correcto es «Cerrada». En el PIA los resultados salen de las pruebas automatizadas (`reportes/`). | Solo documentado (entregable histórico) |
| H-PIA-14 | El informe de la U3 decía «Glosario: 43 criterios» (los criterios están en las User Stories) y citaba archivos que no existían (`informe-arquitectura.pdf`, `adr-autofix-pro.pdf`, `reporte-pruebas.pdf`, `resumen-unidad3.pdf`). | Informe U3 | En el PIA toda la documentación vive en `docs/` en Markdown con los nombres reales; el índice está en `docs/README.md`. | `docs/README.md` |
| H-PIA-15 | Requisitos del PIA que la U3/U5 no cubrían: Specification, máquinas de estados para cotización/trabajo/solicitud, Gherkin formal, estructura `src/domain…`, API REST con OpenAPI, Docker Compose, variables de entorno, despliegue y CI/CD, seguridad por rol y reacciones a eventos. | PIA (requisitos) | ADR-006 a ADR-016, Gherkin en `gherkin/*.feature`, estructura en `decisiones-tecnicas.md`, contrato de la API en `api/README.md`. El mapa de dominio ya no tiene elementos punteados: todo es alcance del PIA. | `architecture/`, `gherkin/`, `api/` |
| H-PIA-16 | Los clientes creados por la API no tenían folio y `RepositorioDeCotizaciones` no tenía un método para generar `COT-0001`. | Fase 3 ↔ `secuencias` y modelo de dominio | Nueva secuencia `cliente` (`CLI-0001`) y método `siguiente_id()` en los repositorios de clientes y de cotizaciones. | `scripts/db/`, `database/`, `modelo-de-datos.md`, modelo de dominio |
| H-PIA-17 | CA-003 dice que el asesor confirma o actualiza los datos de un cliente recurrente, pero ninguna de las 43 rutas actualiza clientes o vehículos. | Fase 3 ↔ CA-003 | `POST /api/ordenes` lleva los datos: si las placas ya existen, reutiliza el registro y actualiza lo enviado (`Cliente.actualizar_contacto`, `Vehiculo.actualizar_datos`). | `api/README.md`, `scripts/docs/rutas.py`, modelo de dominio |
| H-PIA-18 | CA-017 pide avisar «al técnico», pero una orden puede tener varios técnicos. | Fase 3 ↔ CA-017 | La alerta llega a cada técnico distinto con trabajos asignados en la orden. | Modelo de dominio §6 |

## 2. Lo que no cambió

- El objetivo, el alcance y el flujo principal del BPMN (6 fases y retiro anticipado).
- Las 14 necesidades originales y las 24 User Stories originales (solo US-022 aclara «contados desde la entrega»).
- Los 43 criterios originales: 34 sin cambios y 9 con una precisión marcada como **(v3.0)** (CA-015, CA-018, CA-022, CA-023, CA-025, CA-027, CA-039, CA-040, CA-041).
- Los 24 estados originales y sus nombres exactos; se agregó «Cancelada».
- Las decisiones ADR-001 a ADR-005 (se actualizaron sus conteos y su estado).

## 3. Conteos finales

| Elemento | U3 | PIA v3.0 |
|---|---|---|
| Necesidades | 14 | 15 |
| User Stories | 24 | 25 |
| Criterios de aceptación | 43 | 46 |
| Estados (orden / cotización / trabajo / solicitud) | 24 (12/6/4/2) | 25 (13/6/4/2) |
| Reglas de negocio trazadas | — | 24 (RN-01 a RN-24) |
| Specifications | 0 (1 política) | 8 (E1–E8) |
| ADR | 5 | 16 |
| Domain Events | 15 | 26 |
| Rutas de la API | — | 43 |

## 4. Decisiones confirmadas por el equipo (04/11/2026)

1. Base de datos: PostgreSQL con **Supabase** en producción (ADR-009) y despliegue en **Render** (ADR-011).
2. PDF generados al pedirlos y fotos en la base (ADR-014); revisión de plazos con un endpoint y GitHub Actions cada 6 horas (ADR-015).
3. BPMN v3 aplicado directamente sobre el PDF exportado de Lucidchart (`bpmn/BPMN_AutoFix_Pro_v3.pdf`).
4. El equipo del PIA queda integrado por Jesus Eduardo Moreno Osoria y Osvaldo Salvador Cárdenas Mejorado.
