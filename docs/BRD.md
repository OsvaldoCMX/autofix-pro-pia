# Business Requirements Document — AutoFix Pro

**Materia:** Componentes de Lógica de Negocio · FIME UANL
**Profesor:** Miguel Ángel Gómez Marroquín
**Equipo 6:** Jesus Eduardo Moreno Osoria (2136063) · Osvaldo Salvador Cárdenas Mejorado (2141553)

## Historial de versiones

| Versión | Fecha | Origen | Cambios |
|---|---|---|---|
| 1.0 | 03/09/2026 | Unidad 2 | Primera versión del BRD (levantamiento con el stakeholder). |
| 2.0 | 10/2026 | Unidad 3 | Hallazgos H-U2-01 a H-U2-03: se corrigieron inconsistencias entre BRD, User Stories, Glosario y BPMN (US-019 a US-024, sección «Estados del sistema»; 14 necesidades y 43 criterios) y se agregaron al Glosario los términos del modelo. |
| 3.0 | 04/11/2026 | PIA | H-PIA-01: cancelación de la orden antes de cotizar (N-15, US-025). H-PIA-02: el crédito de flotilla se cuenta desde la entrega. H-PIA-03: los datos ficticios del profesor se usan como datos de prueba y demostración. Detalle en `registro-de-cambios.md`. |

## 1. Contexto y descripción del negocio

AutoFix Pro es un taller automotriz que ofrece servicios de diagnóstico, mantenimiento y reparación a clientes particulares y a empresas con flotillas de vehículos.

El proceso central del negocio abarca la recepción del vehículo, el diagnóstico técnico, la autorización del cliente y la ejecución de la reparación. Al ingresar el vehículo, el asesor de servicio registra los datos del cliente, del vehículo, kilometraje, nivel de combustible, daños visibles (con evidencia fotográfica) y el motivo de ingreso. Actualmente esta información se guarda en un sistema interno básico que no controla versiones, estados ni autorizaciones, y algunas áreas, como Compras, trabajan de forma paralela en Excel. Después, el asesor asigna un técnico, quien realiza y registra el diagnóstico.

Con el diagnóstico, el asesor genera la cotización correspondiente, que se presenta directamente al cliente sin aprobación interna previa, salvo cuando la cotización inicial supera los $15,000 MXN: en ese caso requiere primero la aprobación del gerente de taller. El cliente decide si autoriza la reparación total o parcialmente, o si la rechaza; en los clientes de flotilla esta decisión la toma el responsable de flotilla de la empresa. Con la autorización, se asignan los trabajos y se verifican las refacciones necesarias; si una pieza no está disponible, el técnico genera una solicitud de compra, el área de Compras la gestiona y el vehículo permanece en espera, debiendo notificarse al cliente si el retraso supera los 3 días hábiles.

Durante la reparación pueden surgir fallas adicionales, lo que genera una cotización adicional (no una modificación de la original) sujeta a nueva autorización del cliente. Al finalizar los trabajos autorizados, se revisan y se prepara la entrega, que se formaliza cuando el cliente cubre el pago en caja (o, si es cliente de flotilla, cuando se registra el cargo a crédito) y retira el vehículo; en los pagos se emite un recibo interno como comprobante.

## 2. Levantamiento

### Información de la sesión

| Campo | Detalle |
|---|---|
| Stakeholder | Jesús Eduardo (rol: Asesor de Servicio / representante del negocio) |
| Analista | Osvaldo Salvador Cárdenas Mejorado |
| Fecha | 02/09/2026 |

### Guía de preguntas

| ID | Categoría | Pregunta |
|---|---|---|
| 1 | Inicio y fin del proceso | ¿Qué evento exactamente da inicio al proceso? ¿Basta con que el cliente llegue, o hay que agendar una cita? |
| 2 | Inicio y fin del proceso | ¿Cuándo se considera que el proceso terminó oficialmente? ¿Cuándo el cliente paga, cuando sale del taller, o hay algún seguimiento posterior? |
| 3 | Roles y permisos | ¿Quién puede registrar un vehículo nuevo? ¿Solo el asesor, o también el técnico? |
| 4 | Roles y permisos | ¿Quién tiene autoridad para aprobar una cotización antes de mostrársela al cliente? |
| 5 | Roles y permisos | ¿Puede un técnico modificar el diagnóstico después de que ya se generó la cotización? |
| 6 | Roles y permisos | ¿Quién autoriza la compra de refacciones? ¿El asesor, o se necesita aprobación del cliente primero? |
| 7 | Tiempos y límites | ¿Hay un tiempo máximo para entregar el diagnóstico al cliente desde que entra el vehículo? |
| 8 | Tiempos y límites | ¿Cuánto tiempo tiene el cliente para responder si acepta o rechaza la cotización? |
| 9 | Tiempos y límites | ¿Existe un límite de tiempo que el vehículo puede estar en espera por refacciones antes de notificar al cliente? |
| 10 | Excepciones y flujos alternos | Si durante la reparación aparecen fallas adicionales, ¿se genera una nueva cotización o se amplía la original? ¿Quién decide? |
| 11 | Excepciones y flujos alternos | Si el cliente rechaza parcialmente la cotización, ¿qué pasa con las partes que sí autorizó? ¿Se procede igual? |
| 12 | Excepciones y flujos alternos | Si una refacción no llega a tiempo, ¿el cliente puede retirar el vehículo y regresar después? |
| 13 | Datos que se capturan | ¿Qué información exacta se registra al recibir el vehículo? ¿Solo datos del cliente y vehículo, o también fotos de daños visibles? |
| 14 | Datos que se capturan | ¿Dónde se registra todo esto actualmente? |
| 15 | Datos que se capturan | ¿La cotización queda guardada en algún lado o solo se le muestra al cliente en papel? |
| 16 | Reglas de negocio implícitas | ¿Hay algún monto mínimo o máximo de cotización que requiera aprobación especial? |
| 17 | Reglas de negocio implícitas | ¿Las flotillas empresariales tienen algún trato diferente? ¿Crédito, descuentos, proceso distinto? |
| 18 | Reportes y métricas | ¿Qué información necesita el dueño del taller para saber cómo va el negocio? |
| 19 | Reportes y métricas | ¿Hay algún indicador con el que hoy midan si el servicio fue exitoso o no? |

### Hallazgos clave del levantamiento

**Inicio y fin del proceso.** El proceso inicia cuando el vehículo llega físicamente al taller y el asesor de servicio registra los datos de recepción. No es obligatorio agendar cita previa, aunque se recomienda para clientes de flotilla. El proceso concluye cuando el cliente realiza el pago en caja (o se registra el cargo a crédito, en el caso de las flotillas) y el vehículo sale del taller. Actualmente no existe un proceso formal de seguimiento posventa.

**Roles y permisos.** Solo el asesor de servicio tiene permitido registrar vehículos nuevos en el sistema; el técnico no cuenta con esa función. El asesor asigna a un técnico, quien realiza y registra el diagnóstico. Una vez generada la cotización, el técnico no puede modificar el diagnóstico: cualquier hallazgo posterior se reporta como falla adicional y requiere una cotización adicional formalmente autorizada. En cuanto a las refacciones, el técnico genera la solicitud de compra cuando una pieza no está disponible, y el área de Compras solo puede proceder con ella si el cliente ya autorizó esa parte de la reparación.

**Tiempos y límites.** El taller maneja los siguientes tiempos de respuesta como estándar de operación:

- Diagnóstico: el diagnóstico y su cotización deben entregarse al cliente en un máximo de 24 horas desde el ingreso del vehículo.
- Respuesta del cliente a la cotización: el cliente tiene 48 horas, contadas desde que se le presenta, para aceptar o rechazar; si no contesta, el asesor debe volver a contactarlo.
- Refacciones: si una pieza tarda más de 3 días hábiles en llegar, se debe notificar proactivamente al cliente.

**Excepciones y flujos alternos.** Si durante la reparación se detectan fallas adicionales, el asesor genera una cotización adicional (ampliación) sin modificar la original; esta requiere nueva autorización del cliente antes de proceder y, si el cliente la rechaza, se continúa únicamente con los trabajos autorizados originalmente. Si el cliente rechaza parte de la cotización, se continúa con los trabajos autorizados y los rechazados quedan registrados como no autorizados. Si rechaza la cotización completa, se le entrega el vehículo sin reparación y la orden se cierra sin cobro. En caso de que una refacción no llegue a tiempo, el cliente puede retirar su vehículo firmando una nota de responsabilidad, aunque pierde su lugar en la fila de trabajo: cuando regresa, su orden se coloca al final de la fila.

*(Agregado en v3.0, H-PIA-01)* Si el cliente desiste del servicio **antes de que se genere la cotización** (la orden está «Recibida» o «En Diagnóstico»), el asesor cancela la orden registrando el motivo; la orden se cierra sin cobro y sale de la fila de trabajo. Una vez generada la cotización ya no se cancela: si el cliente no quiere la reparación, se registra el rechazo total y el vehículo se entrega sin reparación.

**Datos que se capturan.** Al recibir un vehículo se registran: datos del cliente, datos del vehículo (marca, modelo, año, placas y número de serie VIN), kilometraje, nivel de combustible, daños visibles con fotografías y motivo de ingreso. El sistema interno actual guarda las cotizaciones, pero sin control de versiones, estados ni evidencia de la autorización del cliente, y el área de Compras aún opera en paralelo con Excel para el control de refacciones.

**Reglas de negocio implícitas.** Se identificaron dos reglas de negocio relevantes no documentadas previamente:

- La cotización inicial que supere $15,000 MXN requiere aprobación del gerente de taller antes de presentarse al cliente; si el gerente no la aprueba, el asesor la ajusta según sus indicaciones. Las cotizaciones adicionales no requieren esta aprobación.
- Los clientes de flotilla empresarial tienen crédito a 15 días naturales **contados desde la entrega del vehículo** y un proceso de autorización distinto: la aprobación la da el responsable de flotilla de la empresa, no el conductor del vehículo. El responsable recibe la cotización por correo electrónico o teléfono y comunica su decisión al asesor. Las flotillas no tienen descuentos.

**Reportes y métricas.** El dueño del taller necesita información sobre: tiempo promedio de entrega de vehículos, número de órdenes abiertas y cerradas por semana, ingresos desglosados por diagnóstico, mano de obra y refacciones, y porcentaje de cotizaciones rechazadas. Actualmente no existe un indicador formal de éxito del servicio; el desempeño se evalúa de forma informal a través de quejas de clientes o retrasos evidentes, lo cual representa uno de los principales problemas a resolver con el sistema propuesto. Para esta fase, el sistema solo incluirá dos consultas operativas para el gerente (el listado de órdenes abiertas y cerradas y el total de ingresos del día); el resto de los indicadores queda fuera del alcance.

## 3. Problema / Oportunidad

### Situación actual

AutoFix Pro opera actualmente con procesos parcialmente digitalizados que presentan deficiencias importantes. El problema más crítico es que las autorizaciones de reparación se gestionan de manera verbal o por teléfono, sin dejar evidencia formal registrada en ningún sistema. Esto genera disputas frecuentes cuando los clientes desconocen o niegan haber aprobado ciertos trabajos, representando un riesgo legal y operativo considerable para el taller.

Adicionalmente, el cliente no tiene ninguna forma de consultar por su cuenta el estado de su vehículo; depende de llamar al taller para obtener información, lo que genera inconformidades. Los retrasos ocasionados por la espera de refacciones tampoco se comunican de forma proactiva, lo que afecta la confianza del cliente en el servicio.

### Oportunidad

La implementación de un sistema de gestión integrado para AutoFix Pro representa una oportunidad significativa para digitalizar y formalizar todos los procesos del taller. Con el sistema propuesto, cada autorización del cliente quedará registrada digitalmente, generando un expediente trazable por orden de servicio que elimina las disputas. El cliente podrá consultar el estado de su vehículo ingresando su número de orden y sus placas, sin necesidad de llamar al taller, y el sistema alertará automáticamente al asesor cuando una refacción se retrase o una cotización no tenga respuesta, para que contacte al cliente de forma proactiva.

Asimismo, el sistema registrará los pagos de contado y los cargos a crédito de flotilla, y emitirá recibos internos de pago, agilizando el cierre administrativo.

## 4. Stakeholders

| Rol | Nombre/Área | Tipo | Interés en el sistema |
|---|---|---|---|
| Cliente | Clientes particulares y empresas de flotilla | Externo | Recibir un diagnóstico claro, autorizar reparaciones (clientes particulares) y consultar el estado de su vehículo con su número de orden y placas |
| Responsable de Flotilla | Contacto designado por empresa cliente | Externo | Autorizar o rechazar las cotizaciones de los vehículos de su empresa (comunica su decisión al asesor; no usa el sistema) y recibir el aviso de cargo a crédito |
| Asesor de Servicio | Personal del taller | Interno | Registrar vehículos, asignar técnicos, generar y presentar cotizaciones, registrar autorizaciones, coordinar con Compras, registrar la entrega del vehículo y cancelar órdenes cuando el cliente desiste antes de la cotización |
| Técnico | Personal del taller | Interno | Recibir asignación de trabajos, registrar diagnósticos, reportar fallas adicionales, solicitar refacciones y actualizar el avance de los trabajos |
| Personal de Compras | Área de Compras | Interno | Gestionar las solicitudes de refacciones y registrar la llegada de las piezas al taller |
| Personal de Caja | Área administrativa | Interno | Registrar pagos de contado y cargos a crédito de flotilla, y emitir recibos internos |
| Gerente de Taller | Dirección del taller (dueño) | Interno | Aprobar o rechazar las cotizaciones iniciales mayores a $15,000 MXN y consultar el listado de órdenes y el total de ingresos del día |

## 5. Alcance del sistema

### Dentro del alcance

El sistema cubrirá el flujo completo de atención de vehículos en el taller, desde la recepción hasta el cierre de la orden. En la etapa de recepción, el sistema permitirá registrar digitalmente todos los datos del cliente y del vehículo, incluyendo marca, modelo, año, placas y número de serie VIN, el kilometraje, el nivel de combustible, fotografías de los daños visibles y el motivo de ingreso. También contemplará la búsqueda de historial por número de placas para agilizar la atención a clientes recurrentes, la asignación de técnicos y el registro del diagnóstico. Si el cliente desiste antes de la cotización, el asesor podrá cancelar la orden registrando el motivo.

En cuanto a la gestión de cotizaciones, el sistema generará y almacenará documentos formales con número, versión, fecha, estado y desglose de mano de obra y refacciones, incluyendo un flujo de aprobación gerencial para la cotización inicial que supere los $15,000 MXN. Registrará la fecha en que cada cotización se presenta al cliente y alertará al asesor si pasan 48 horas sin respuesta. Se registrará digitalmente la decisión del cliente, ya sea autorización total, parcial o rechazo, antes de iniciar cualquier trabajo, con un proceso diferenciado para clientes de flotilla en el que la decisión se registra a nombre del responsable de flotilla. Cuando durante la reparación se descubran fallas adicionales, el sistema permitirá generar cotizaciones adicionales sin afectar la cotización original.

La ejecución de reparaciones incluirá la asignación de trabajos a técnicos y el seguimiento de su estado. La gestión de refacciones registrará las solicitudes de compra y la llegada de las piezas, controlará los tiempos de espera y alertará al asesor si una pieza tarda más de tres días hábiles en llegar, para que notifique al cliente. Se contempla también el registro de retiros anticipados de vehículos con generación de la Nota de Responsabilidad. Finalmente, el sistema registrará los pagos de contado y los cargos a crédito de flotilla, emitirá recibos internos de pago y registrará la entrega del vehículo para cerrar la orden. Además, el cliente podrá consultar el estado de su vehículo con su número de orden y placas, y el gerente podrá consultar el listado de órdenes y el total de ingresos del día.

### Fuera del alcance

El sistema no contempla la contabilidad general del taller, la gestión de nómina ni ningún módulo de recursos humanos. Tampoco incluye integración directa con proveedores externos de refacciones (el sistema gestiona solicitudes internas, no órdenes de compra hacia proveedores), el control de inventario o existencias de refacciones, ni un módulo de seguimiento posventa o gestión de garantías. Las ventas al mostrador de refacciones sin una orden de servicio asociada también quedan fuera del alcance. El módulo de agendamiento de citas en línea para clientes podría considerarse en una segunda fase, pero no forma parte de los requerimientos actuales. La emisión de facturas electrónicas (CFDI) y el cumplimiento fiscal ante el SAT quedan explícitamente fuera del alcance, al igual que la cobranza de los créditos de flotilla después de la entrega. El sistema no enviará correos, SMS ni mensajes al cliente: las alertas son internas y es el asesor quien contacta al cliente. Tampoco habrá cuentas de usuario para clientes ni para responsables de flotilla, ni firma electrónica (la Nota de Responsabilidad se imprime y se firma en papel). No se manejan descuentos, promociones ni clientes preferentes. Finalmente, la generación de reportes gerenciales, KPIs y dashboards queda fuera del alcance, salvo el listado de órdenes y el total de ingresos del día.

## 6. Necesidades del negocio

| ID | Necesidad del negocio | Prioridad | US vinculadas |
|---|---|---|---|
| N-01 | Registrar digitalmente la recepción del vehículo incluyendo fotografías de daños visibles | Alta | US-001, US-002, US-003 |
| N-02 | Generar cotizaciones formales almacenadas con número, fecha, versión y estado | Alta | US-004 |
| N-03 | Registrar la decisión del cliente (autorización total, parcial o rechazo) antes de iniciar trabajos | Alta | US-006 |
| N-04 | Aplicar flujo de aprobación del Gerente para cotizaciones iniciales mayores a $15,000 MXN | Alta | US-005 |
| N-05 | Alertar automáticamente al asesor cuando una refacción tarde más de 3 días hábiles, para que notifique al cliente | Media | US-012 |
| N-06 | Generar cotizaciones adicionales para fallas descubiertas sin modificar la cotización original | Alta | US-009, US-019 |
| N-07 | Gestionar el proceso diferenciado para clientes de flotilla empresarial (autorización del responsable y crédito a 15 días desde la entrega) | Media | US-016, US-022 |
| N-08 | Permitir al Gerente visualizar un listado de órdenes abiertas/cerradas y el total de ingresos del día | Media | US-017, US-018 |
| N-09 | (Implícita) Asignar técnicos y permitirles registrar el diagnóstico, ver sus trabajos y actualizar su estado | Alta | US-007, US-008, US-019, US-020 |
| N-10 | (Implícita) Controlar la solicitud y la llegada de refacciones con el área de Compras | Alta | US-010, US-011 |
| N-11 | (Implícita) Registrar el pago, emitir el recibo interno y registrar la entrega del vehículo | Alta | US-014, US-015, US-024 |
| N-12 | (Implícita) Permitir el retiro de vehículo en espera con generación de Nota de Responsabilidad | Media | US-013 |
| N-13 | Permitir al cliente consultar el estado de su vehículo sin llamar al taller | Media | US-021 |
| N-14 | (Implícita) Dar seguimiento a las cotizaciones que lleven más de 48 horas sin respuesta | Media | US-023 |
| N-15 | (Implícita, v3.0) Cancelar la orden cuando el cliente desiste antes de que se genere la cotización | Media | US-025 |

## 7. Restricciones

### Restricciones de proceso

1. El diagnóstico y su cotización deben entregarse al cliente en un máximo de 24 horas desde el ingreso del vehículo.
2. El cliente tiene 48 horas, contadas desde que se le presenta la cotización, para aceptarla o rechazarla; si no responde, el sistema alerta al asesor para que lo contacte nuevamente.
3. Si una refacción tarda más de 3 días hábiles en llegar, se debe notificar proactivamente al cliente (el sistema alerta al asesor para que lo haga).
4. La cotización inicial mayor a $15,000 MXN requiere aprobación del gerente de taller antes de presentarse al cliente; las cotizaciones adicionales no requieren esta aprobación.
5. Los clientes de flotilla empresarial tienen crédito a 15 días naturales contados desde la entrega del vehículo, y su autorización la otorga el responsable de flotilla, no el conductor.
6. El retiro anticipado del vehículo por espera de refacciones implica la firma de una Nota de Responsabilidad y la pérdida del lugar en la fila de trabajo.
7. Una vez generada la cotización, el técnico no puede modificar el diagnóstico; los hallazgos posteriores se tratan como fallas adicionales.
8. Compras solo gestiona refacciones de trabajos que el cliente ya autorizó.
9. El vehículo solo se entrega después de registrar el pago (cliente particular) o el cargo a crédito (cliente de flotilla). Si el cliente rechaza toda la cotización, el vehículo se entrega sin reparación y sin cobro.
10. *(v3.0)* Una orden solo puede cancelarse mientras no tenga cotización («Recibida» o «En Diagnóstico»); la cancelación no genera cobro.

### Restricciones técnicas

- El sistema debe ser una aplicación con acceso a internet.
- El área de recepción debe contar con al menos un dispositivo con acceso a internet.
- Los técnicos dispondrán de una computadora para consultar y actualizar el estado de sus órdenes.
- El sistema debe almacenar digitalmente fotografías y documentos generados (cotizaciones, notas, recibos).
- No se integrará directamente con sistemas de proveedores externos en esta fase.

## 8. Supuestos

Para la elaboración de este documento se asumieron como válidos los siguientes supuestos. Si alguno de ellos resultara falso durante la implementación, los requerimientos documentados podrían requerir revisión o ajuste.

Se asume que el taller cuenta con al menos un dispositivo con acceso a internet en el área de recepción, y que los técnicos dispondrán de una computadora para consultar y actualizar el estado de sus órdenes asignadas desde la bahía de trabajo. También se asume que todos los actores del proceso, Asesores, Técnicos, personal de Compras, Caja y Gerencia, adoptarán el uso del nuevo sistema y recibirán la capacitación necesaria para operarlo.

En cuanto a los clientes de flotilla, se asume que existe un contrato previo firmado con AutoFix Pro antes de la prestación de cualquier servicio, y que el Responsable de Flotilla designado por cada empresa puede recibir las cotizaciones por correo electrónico o teléfono y comunicar su decisión al asesor, sin necesidad de acceder al sistema. También se asume que el asesor entrega al cliente su número de orden al recibir el vehículo, para que pueda consultar su estado. Finalmente, se asume que el taller no requiere emitir facturas electrónicas (CFDI) en esta fase, y que el recibo interno de pago es suficiente para el cierre administrativo.

*(v3.0, H-PIA-03)* Para las pruebas y la demostración se usan los datos ficticios proporcionados por el profesor (paquete «Data Center» 06_AutoFix_Pro: propietarios, servicios, órdenes y casos de prueba). Esos datos no cambian los requisitos de este documento; las diferencias se documentan en `datos-profesor/README.md`.

## 9. Criterios de éxito

| ID | Criterio de éxito | Métrica de verificación |
|---|---|---|
| CE-01 | Eliminar autorizaciones de reparación sin evidencia formal | 0% de órdenes de trabajo iniciadas sin autorización registrada en el sistema |
| CE-02 | Reducir disputas con clientes sobre trabajos realizados | Disminución medible en reclamaciones postservicio respecto al período anterior a la implementación |
| CE-03 | Mejorar visibilidad del estado del vehículo para el cliente | 100% de órdenes activas con estado actualizado y consultable por el cliente mediante su número de orden y placas |
| CE-04 | Comunicar retrasos por refacciones de forma oportuna | 100% de las refacciones con más de 3 días hábiles de espera generan alerta al asesor y tienen registrada la notificación al cliente |
| CE-05 | Garantizar aprobación gerencial en cotizaciones de alto monto | 0% de cotizaciones iniciales mayores a $15,000 MXN presentadas al cliente sin aprobación del Gerente |
| CE-06 | Centralizar la gestión de refacciones en el sistema | 100% de solicitudes de compra gestionadas desde el sistema en los primeros 3 meses tras la implementación |
| CE-07 | Permitir a la gerencia consultar el listado de órdenes e ingresos diarios | 100% de las órdenes visibles en el listado del Gerente y total de ingresos del día igual a la suma de los pagos registrados |
| CE-08 | Reducir el tiempo promedio del proceso de recepción | Reducción del tiempo de registro en al menos 30% respecto al proceso actual |

## 10. Bibliografía

- Evans, E. (2003). *Domain-driven design: Tackling complexity in the heart of software*. Addison-Wesley Professional.
- Fowler, M. (2003). *Patterns of enterprise application architecture*. Addison-Wesley Professional.
- International Institute of Business Analysis (IIBA). (2015). *A guide to the business analysis body of knowledge (BABOK® Guide)* (3rd ed.).
- Robertson, S., & Robertson, J. (2023). *Mastering the requirements process: Getting requirements right* (4th ed.). Addison-Wesley.
- Vernon, V. (2013). *Implementing domain-driven design*. Addison-Wesley Professional.
- Wiegers, K. E., & Beatty, J. (2013). *Software requirements* (3rd ed.). Microsoft Press.
