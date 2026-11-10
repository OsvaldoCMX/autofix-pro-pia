# User Stories y Criterios de Aceptación — AutoFix Pro

**Materia:** Componentes de Lógica de Negocio · FIME UANL · **Equipo 6**  
**Versión:** 3.1 (revisión del 09/11/2026)

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 03/09/2026 | Unidad 2: 18 User Stories y sus criterios. |
| 2.0 | 10/2026 | Unidad 3: hallazgos H-U2-01 a H-U2-03 (se agregaron US-019 a US-024); 24 User Stories y 43 criterios. |
| 3.0 | 04/11/2026 | PIA: US-025 (cancelación), CA-044 a CA-046, crédito desde la entrega y precisiones en CA-015, CA-018, CA-022, CA-023, CA-025, CA-027, CA-039, CA-040 y CA-041. Los criterios ahora también están en Gherkin formal (`gherkin/*.feature`). Detalle en `registro-de-cambios.md`. |
| 3.1 | 09/11/2026 | Revisión del profesor como usuario del taller: correcciones de datos mal capturados y prevención de registros repetidos (H-PIA-21 en adelante, necesidad N-16, desde US-026 y CA-047). Los criterios marcados **(v3.1)** son nuevos; los que tienen la marca «Planeado» en la matriz de trazabilidad todavía no se construyen. |

Este documento contiene las User Stories derivadas del levantamiento de requerimientos del sistema de gestión de taller AutoFix Pro. Cada historia representa una funcionalidad que el sistema debe proporcionar a un rol específico para resolver los problemas de la operación actual (AS-IS), como la falta de evidencia en las autorizaciones o la falta de visibilidad del estado de las reparaciones.

Las historias siguen el formato *Como… quiero… para…* y cada criterio de aceptación está escrito en Gherkin (*Dado / Cuando / Entonces / Y*). Los mismos criterios, palabra por palabra, están en los archivos `docs/gherkin/*.feature` con las etiquetas `@US-xxx` y `@CA-xxx`, para que cada escenario se pueda relacionar con su prueba automatizada (convención `test_ca_0XX_…`). Los nombres de estados, roles y términos son los del [Glosario del Dominio](glosario.md).

**Resumen:** 16 necesidades · 27 User Stories · 60 criterios de aceptación · 8 archivos `.feature`.

## 1. Trazabilidad con el BRD

| ID Necesidad | Descripción de la necesidad | User Stories vinculadas |
|---|---|---|
| N-01 | Registrar digitalmente la recepción del vehículo incluyendo fotografías de daños visibles. | US-001, US-002, US-003 |
| N-02 | Generar cotizaciones formales almacenadas con número, fecha, versión y estado. | US-004 |
| N-03 | Registrar la decisión del cliente (autorización total, parcial o rechazo) antes de iniciar trabajos. | US-006 |
| N-04 | Aplicar flujo de aprobación del Gerente para cotizaciones iniciales mayores a $15,000 MXN. | US-005 |
| N-05 | Alertar automáticamente al asesor cuando una refacción tarde más de 3 días hábiles, para que notifique al cliente. | US-012 |
| N-06 | Generar cotizaciones adicionales para fallas descubiertas sin modificar la cotización original. | US-009, US-019 |
| N-07 | Gestionar el proceso diferenciado para clientes de flotilla empresarial (autorización del responsable y crédito a 15 días desde la entrega). | US-016, US-022 |
| N-08 | Permitir al Gerente visualizar un listado de órdenes abiertas/cerradas y el total de ingresos del día. | US-017, US-018 |
| N-09 | (Implícita) Asignar técnicos y permitirles registrar el diagnóstico, ver sus trabajos y actualizar su estado. | US-007, US-008, US-019, US-020 |
| N-10 | (Implícita) Controlar la solicitud y la llegada de refacciones con el área de Compras. | US-010, US-011 |
| N-11 | (Implícita) Registrar el pago, emitir el recibo interno y registrar la entrega del vehículo. | US-014, US-015, US-024 |
| N-12 | (Implícita) Permitir el retiro de vehículo en espera con generación de Nota de Responsabilidad. | US-013 |
| N-13 | Permitir al cliente consultar el estado de su vehículo sin llamar al taller. | US-021 |
| N-14 | (Implícita) Dar seguimiento a las cotizaciones que lleven más de 48 horas sin respuesta. | US-023 |
| N-15 | (Implícita, v3.0) Cancelar la orden cuando el cliente desiste antes de que se genere la cotización. | US-025 |
| N-16 | (Implícita, v3.1) Corregir los datos mal capturados dejando constancia y evitar registros repetidos (revisión del 09/11/2026). | US-026, US-020, US-027, US-014 |

## 2. Listado de User Stories

| ID | Rol | User Story | Archivo Gherkin |
|---|---|---|---|
| US-001 | Asesor de Servicio | Como Asesor de Servicio, quiero poder registrar un vehículo nuevo en el sistema, para tener un expediente digital completo del cliente y su vehículo, evitando errores de captura y pérdida de papeles. | `01_recepcion.feature` |
| US-002 | Asesor de Servicio | Como Asesor de Servicio, quiero poder capturar el kilometraje, nivel de combustible y tomar fotos de los daños visibles del vehículo al momento de la recepción, para tener evidencia del estado en el que ingresó el vehículo y evitar futuras disputas con el cliente. | `01_recepcion.feature` |
| US-003 | Asesor de Servicio | Como Asesor de Servicio, quiero buscar un vehículo por su número de placas al inicio del registro, para recuperar automáticamente la información del cliente y vehículo si ya es un cliente recurrente, y así agilizar el proceso de recepción. | `01_recepcion.feature` |
| US-004 | Asesor de Servicio | Como Asesor de Servicio, quiero poder generar una cotización detallada a partir del diagnóstico del técnico y registrar cuándo se la presento al cliente, para entregarle un documento formal con el desglose de mano de obra, refacciones y costos. | `03_cotizacion.feature` |
| US-005 | Gerente de Taller | Como Gerente de Taller, quiero recibir una alerta y poder aprobar o rechazar con observaciones las cotizaciones iniciales cuyo total supere los $15,000 MXN, para asegurarme de que los trabajos costosos tengan una revisión especial antes de ser presentados al cliente. | `03_cotizacion.feature` |
| US-006 | Asesor de Servicio | Como Asesor de Servicio, quiero registrar la decisión del cliente cuando autoriza total o parcialmente, o rechaza una cotización, para tener evidencia formal de lo que se acordó y poder iniciar solo los trabajos autorizados, evitando disputas posteriores. | `04_autorizacion.feature` |
| US-007 | Técnico | Como Técnico, quiero ver en mi panel las órdenes de servicio y trabajos que me han sido asignados, ordenados según la fila de trabajo, para organizar mi jornada y saber exactamente en qué vehículo debo trabajar primero. | `02_diagnostico.feature` |
| US-008 | Técnico | Como Técnico, quiero poder actualizar el estado de los trabajos de una orden a «En Progreso» o «Completado», para que el sistema refleje el estado actual de la reparación y el Asesor pueda informar al cliente. | `05_reparacion_y_refacciones.feature` |
| US-009 | Asesor de Servicio | Como Asesor de Servicio, quiero poder crear una cotización adicional si durante la reparación se descubren nuevas fallas, para obtener la autorización del cliente para los trabajos extra sin modificar la cotización original, manteniendo un historial claro. | `04_autorizacion.feature` |
| US-010 | Técnico | Como Técnico, quiero poder marcar una refacción de un trabajo autorizado como «No disponible» y generar una solicitud de compra desde la orden de servicio, para que el área de Compras sepa qué pieza se necesita y pueda gestionar su adquisición. | `05_reparacion_y_refacciones.feature` |
| US-011 | Personal de Compras | Como Personal de Compras, quiero ver una lista de todas las solicitudes de refacciones pendientes, para gestionar su compra con proveedores y registrar en el sistema su llegada al taller. | `05_reparacion_y_refacciones.feature` |
| US-012 | Asesor de Servicio | Como Asesor de Servicio, quiero recibir una alerta automática en el sistema si una refacción solicitada tarda más de 3 días hábiles en llegar, para poder contactar proactivamente al cliente y comunicarle el retraso, mejorando la comunicación y la confianza. | `05_reparacion_y_refacciones.feature` |
| US-013 | Asesor de Servicio | Como Asesor de Servicio, quiero registrar la salida de un vehículo cuya orden está en espera de refacciones, generando la Nota de Responsabilidad, para permitir que el cliente use su vehículo y dejar constancia formal de que lo retiró sin que la reparación estuviera terminada. | `05_reparacion_y_refacciones.feature` |
| US-014 | Personal de Caja | Como Personal de Caja, quiero registrar el pago de una orden de cliente particular cuando está lista para entrega, para cerrar la parte administrativa del servicio. | `06_caja_y_entrega.feature` |
| US-015 | Personal de Caja | Como Personal de Caja, quiero generar un recibo interno de una orden pagada, para entregar al cliente un comprobante de pago sin necesidad de emitir facturas fiscales. | `06_caja_y_entrega.feature` |
| US-016 | Asesor de Servicio | Como Asesor de Servicio, quiero registrar a un cliente como tipo «Flotilla», vinculado a su empresa y a su Responsable de Flotilla, para que las decisiones sobre las cotizaciones se registren a nombre del responsable y no del conductor. | `01_recepcion.feature` |
| US-017 | Gerente de Taller | Como Gerente de Taller, quiero ver un listado de todas las órdenes abiertas y cerradas, para tener visibilidad del estado general del taller. | `07_consultas.feature` |
| US-018 | Gerente de Taller | Como Gerente de Taller, quiero ver el total de ingresos del día, para conocer el desempeño financiero diario del taller. | `07_consultas.feature` |
| US-019 | Técnico | Como Técnico, quiero registrar el diagnóstico de la orden que me fue asignada y reportar las fallas adicionales que encuentre durante la reparación, para que el asesor pueda generar las cotizaciones con información técnica completa. | `02_diagnostico.feature` |
| US-020 | Asesor de Servicio | Como Asesor de Servicio, quiero asignar un técnico a cada orden, tanto para el diagnóstico como para los trabajos autorizados, para que cada técnico sepa qué vehículos debe atender. | `02_diagnostico.feature` |
| US-021 | Cliente | Como Cliente, quiero consultar el estado de mi vehículo ingresando mi número de orden y mis placas, para saber cómo va el servicio sin tener que llamar al taller. | `07_consultas.feature` |
| US-022 | Personal de Caja | Como Personal de Caja, quiero registrar un cargo a crédito de 15 días (contados desde la entrega del vehículo) para las órdenes de clientes de flotilla, para cerrar la parte administrativa del servicio sin cobrarle al conductor y dejar registrada la fecha en que la empresa debe pagar. | `06_caja_y_entrega.feature` |
| US-023 | Asesor de Servicio | Como Asesor de Servicio, quiero recibir una alerta cuando una cotización presentada lleve más de 48 horas sin respuesta, para volver a contactar al cliente o al Responsable de Flotilla. | `03_cotizacion.feature` |
| US-024 | Asesor de Servicio | Como Asesor de Servicio, quiero registrar la entrega del vehículo al cliente, para cerrar la orden de servicio y dejar constancia de cuándo salió el vehículo del taller. | `06_caja_y_entrega.feature` |
| US-025 | Asesor de Servicio | Como Asesor de Servicio, quiero cancelar una orden cuando el cliente desiste del servicio antes de que se genere la cotización, para cerrar el expediente sin cobro y dejar registrado el motivo. | `08_cancelacion.feature` |
| US-026 | Asesor de Servicio | Como Asesor de Servicio, quiero corregir una cotización con un importe o una descripción mal capturados mientras espera la revisión del Gerente o la decisión del cliente, indicando el motivo, para presentar un documento correcto sin perder el historial de lo que cambió. | `03_cotizacion.feature` |
| US-027 | Asesor de Servicio | Como Asesor de Servicio, quiero corregir los datos del cliente, del vehículo y del estado de recepción que capturé mal, para que el expediente quede correcto sin tener que abrir otra orden. | `01_recepcion.feature` |

## 3. Criterios de aceptación en Gherkin

Los criterios marcados con **(v3.0)** se agregaron o se precisaron en el PIA y los marcados con **(v3.1)** salen de la revisión del 09/11/2026; el hallazgo que lo justifica se indica entre paréntesis.

### US-001

> Como Asesor de Servicio, quiero poder registrar un vehículo nuevo en el sistema, para tener un expediente digital completo del cliente y su vehículo, evitando errores de captura y pérdida de papeles.

| ID | Criterio de aceptación |
|---|---|
| **CA-001**<br>Registrar un vehículo nuevo y abrir su orden | **Dado** que un vehículo llega al taller y el asesor abre la pantalla «Nueva Orden»<br>**Cuando** el asesor ingresa los datos del cliente (nombre, teléfono y correo), los del vehículo (marca, modelo, año, placas y VIN) y el motivo de ingreso<br>**Entonces** el sistema debe guardar la información<br>**Y** debe generar un número de orden de servicio único<br>**Y** debe asignarle el estado «Recibida»<br>**Y** debe mostrar un mensaje de éxito |
| **CA-052**<br>No se abre una segunda orden del mismo vehículo **(v3.1, H-PIA-22)** | **Dado** que el vehículo con placas XYZ998 ya tiene una orden abierta (en un estado distinto de «Cerrada», «Cerrada sin Reparación» y «Cancelada»)<br>**Cuando** el asesor intenta registrar otra orden para ese vehículo, por ejemplo con un doble clic en «Registrar»<br>**Entonces** el sistema no debe abrir una segunda orden<br>**Y** debe mostrar el mensaje «El vehículo con placas XYZ998 ya tiene abierta la orden OS-0001 (estado «Recibida»). Ábrala en lugar de registrar otra.»<br>**Y** aunque las dos solicitudes lleguen al mismo tiempo, solo una orden debe quedar registrada y la otra debe recibir el mismo mensaje |
| **CA-059**<br>Datos de captura con forma y rango razonables **(v3.1, H-PIA-25)** | **Dado** que el asesor captura los datos del cliente, del Responsable de Flotilla, del vehículo y del estado de recepción<br>**Cuando** escribe un teléfono que no tiene 10 dígitos, un correo sin la forma nombre@dominio.algo, un año mayor al año actual + 1, un kilometraje mayor a 2,000,000 o un texto de más de 1,000 caracteres<br>**Entonces** el sistema no debe guardar el registro<br>**Y** debe indicar qué dato está mal y cómo debe capturarse, por ejemplo «El teléfono debe tener 10 dígitos, por ejemplo 81 1234 5678.»<br>**Y** un teléfono o un correo con solo espacios debe tratarse como no capturado |

### US-002

> Como Asesor de Servicio, quiero poder capturar el kilometraje, nivel de combustible y tomar fotos de los daños visibles del vehículo al momento de la recepción, para tener evidencia del estado en el que ingresó el vehículo y evitar futuras disputas con el cliente.

| ID | Criterio de aceptación |
|---|---|
| **CA-002**<br>Capturar el estado de ingreso y las fotos de daños | **Dado** que el asesor está en la pantalla de registro de un vehículo<br>**Cuando** ingresa el kilometraje, selecciona el nivel de combustible y adjunta las fotos de los daños<br>**Entonces** el sistema debe almacenar estos datos y fotos como parte del expediente de la orden de servicio |

### US-003

> Como Asesor de Servicio, quiero buscar un vehículo por su número de placas al inicio del registro, para recuperar automáticamente la información del cliente y vehículo si ya es un cliente recurrente, y así agilizar el proceso de recepción.

| ID | Criterio de aceptación |
|---|---|
| **CA-003**<br>Encontrar un cliente recurrente por sus placas | **Dado** que el asesor está en la pantalla de inicio de una nueva orden<br>**Cuando** escribe el número de placas<br>**Y** el sistema encuentra un registro previo<br>**Entonces** el sistema debe mostrar los datos precargados del cliente y el vehículo<br>**Y** el asesor solo debe confirmarlos o actualizarlos |
| **CA-004**<br>Placas no registradas | **Dado** que el asesor ingresa un número de placas que no existe en el sistema<br>**Cuando** el sistema no encuentra el vehículo<br>**Entonces** debe habilitar la opción para crear un nuevo registro desde cero |

### US-004

> Como Asesor de Servicio, quiero poder generar una cotización detallada a partir del diagnóstico del técnico y registrar cuándo se la presento al cliente, para entregarle un documento formal con el desglose de mano de obra, refacciones y costos.

| ID | Criterio de aceptación |
|---|---|
| **CA-005**<br>Generar la cotización inicial | **Dado** que la orden tiene un diagnóstico registrado por el técnico<br>**Cuando** el asesor agrega los trabajos (mano de obra) y las refacciones con sus costos y guarda la cotización<br>**Entonces** el sistema debe generarla con número único, versión 1, fecha, desglose y costo total<br>**Y** debe generar su PDF<br>**Y** debe cambiar la orden a «Cotizada»<br>**Y** si el total es menor o igual a $15,000 MXN, debe asignar a la cotización el estado «Pendiente de Autorización del Cliente» |
| **CA-006**<br>Marcar la cotización como presentada | **Dado** que una cotización está en «Pendiente de Autorización del Cliente»<br>**Cuando** el asesor la marca como presentada (al cliente o, si es flotilla, al Responsable de Flotilla)<br>**Entonces** el sistema debe registrar la fecha y hora de presentación, a partir de la cual corre el plazo de 48 horas |
| **CA-060**<br>Cada trabajo de la cotización vale más de $0.00 **(v3.1, H-PIA-25)** | **Dado** que el asesor captura los trabajos de una cotización<br>**Cuando** un trabajo suma $0.00 entre su mano de obra y sus refacciones<br>**Entonces** el sistema no debe guardar la cotización<br>**Y** debe indicar qué trabajo vale $0.00 y pedir que capture su importe |

### US-005

> Como Gerente de Taller, quiero recibir una alerta y poder aprobar o rechazar con observaciones las cotizaciones iniciales cuyo total supere los $15,000 MXN, para asegurarme de que los trabajos costosos tengan una revisión especial antes de ser presentados al cliente.

| ID | Criterio de aceptación |
|---|---|
| **CA-007**<br>Cotización inicial mayor a $15,000 MXN | **Dado** que el asesor guarda una cotización inicial con un total mayor a $15,000 MXN<br>**Cuando** el sistema la genera<br>**Entonces** debe asignarle el estado «Pendiente de Aprobación Gerencial»<br>**Y** debe impedir que se marque como presentada<br>**Y** debe enviar una alerta al panel del Gerente |
| **CA-008**<br>El Gerente aprueba la cotización | **Dado** que la cotización está en «Pendiente de Aprobación Gerencial»<br>**Cuando** el Gerente la revisa y la aprueba<br>**Entonces** el sistema debe cambiar su estado a «Pendiente de Autorización del Cliente»<br>**Y** debe registrar la fecha de aprobación<br>**Y** debe notificar al asesor para que pueda presentarla |
| **CA-009**<br>El Gerente rechaza la cotización con observaciones | **Dado** que la cotización está en «Pendiente de Aprobación Gerencial»<br>**Cuando** el Gerente la rechaza capturando sus observaciones<br>**Entonces** el sistema debe cambiar su estado a «Requiere Ajuste»<br>**Y** debe notificar al asesor<br>**Cuando** el asesor guarda la cotización ajustada<br>**Entonces** su estado pasa a «Pendiente de Autorización del Cliente» sin volver a revisión gerencial |

### US-006

> Como Asesor de Servicio, quiero registrar la decisión del cliente cuando autoriza total o parcialmente, o rechaza una cotización, para tener evidencia formal de lo que se acordó y poder iniciar solo los trabajos autorizados, evitando disputas posteriores.

| ID | Criterio de aceptación |
|---|---|
| **CA-010**<br>Registrar la autorización total o parcial | **Dado** que el cliente (o el Responsable de Flotilla) revisó la cotización<br>**Cuando** el asesor selecciona los trabajos autorizados y guarda la decisión<br>**Entonces** el sistema debe cambiar la cotización a «Autorizada» o «Autorizada Parcialmente»<br>**Y** debe cambiar la orden a «Autorizada»<br>**Y** debe registrar la fecha, la hora y el nombre de quien autorizó<br>**Y** debe marcar los trabajos no aceptados como «No Autorizado» |
| **CA-011**<br>Solo se asignan los trabajos autorizados | **Dado** que el cliente autorizó parcialmente la cotización<br>**Cuando** el asesor asigna los trabajos a un técnico<br>**Entonces** el sistema solo debe permitir seleccionar los trabajos autorizados |
| **CA-012**<br>Registrar el rechazo total | **Dado** que el cliente no acepta ningún trabajo de la cotización<br>**Cuando** el asesor registra el rechazo total<br>**Entonces** el sistema debe cambiar la cotización a «Rechazada»<br>**Y** debe impedir la asignación de trabajos<br>**Y** debe habilitar la opción «Entregar sin reparación» |

### US-007

> Como Técnico, quiero ver en mi panel las órdenes de servicio y trabajos que me han sido asignados, ordenados según la fila de trabajo, para organizar mi jornada y saber exactamente en qué vehículo debo trabajar primero.

| ID | Criterio de aceptación |
|---|---|
| **CA-013**<br>Panel del técnico ordenado por la fila de trabajo | **Dado** que un técnico inicia sesión en el sistema<br>**Cuando** accede a su panel de trabajo<br>**Entonces** debe visualizar la lista de órdenes y trabajos que le han sido asignados, ordenada según la fila de trabajo (de la fecha de ingreso a la fila más antigua a la más reciente) |

### US-008

> Como Técnico, quiero poder actualizar el estado de los trabajos de una orden a «En Progreso» o «Completado», para que el sistema refleje el estado actual de la reparación y el Asesor pueda informar al cliente.

| ID | Criterio de aceptación |
|---|---|
| **CA-014**<br>Iniciar un trabajo | **Dado** que un técnico tiene un trabajo asignado en estado «Pendiente»<br>**Cuando** lo actualiza a «En Progreso»<br>**Entonces** el sistema debe registrar el cambio<br>**Y** si la orden estaba en «Autorizada», debe cambiarla a «En Reparación» |
| **CA-015**<br>Completar el último trabajo autorizado **(v3.0, H-PIA-12)** | **Dado** que un técnico está trabajando en una orden asignada<br>**Cuando** actualiza un trabajo a «Completado»<br>**Y** todos los trabajos autorizados de la orden quedan completados<br>**Y** no hay una cotización adicional esperando la decisión del cliente<br>**Entonces** el sistema debe cambiar el estado de la orden a «Lista para Entrega»<br>**Y** debe notificar al asesor |
| **CA-046**<br>No se trabaja un vehículo retirado del taller **(v3.0, H-PIA-06)** | **Dado** que una orden está en «Pausada por Retiro de Vehículo»<br>**Cuando** el técnico intenta iniciar uno de sus trabajos<br>**Entonces** el sistema no debe permitirlo<br>**Y** debe indicar que el vehículo no está en el taller |

### US-009

> Como Asesor de Servicio, quiero poder crear una cotización adicional si durante la reparación se descubren nuevas fallas, para obtener la autorización del cliente para los trabajos extra sin modificar la cotización original, manteniendo un historial claro.

| ID | Criterio de aceptación |
|---|---|
| **CA-016**<br>Crear una cotización adicional | **Dado** que el técnico reportó una falla adicional en una orden «En Reparación»<br>**Cuando** el asesor crea una nueva cotización vinculada a esa orden<br>**Entonces** el sistema debe etiquetarla como «Cotización Adicional»<br>**Y** debe asignarle la siguiente versión (v.2, v.3…)<br>**Y** debe dejarla en «Pendiente de Autorización del Cliente» sin importar su monto<br>**Y** debe mantener sin cambios la cotización original |
| **CA-017**<br>El cliente autoriza la cotización adicional | **Dado** que el cliente autoriza la cotización adicional<br>**Cuando** el asesor registra la decisión<br>**Entonces** los trabajos adicionales se agregan a la orden en estado «Pendiente»<br>**Y** el sistema debe notificar al técnico |
| **CA-018**<br>El cliente rechaza la cotización adicional **(v3.0, H-PIA-12)** | **Dado** que el cliente rechaza la cotización adicional<br>**Cuando** el asesor registra la decisión<br>**Entonces** el sistema debe marcar los trabajos adicionales como «No Autorizado»<br>**Y** la orden continúa solo con los trabajos autorizados originalmente<br>**Y** si esos trabajos ya estaban completados, la orden pasa a «Lista para Entrega» |

### US-010

> Como Técnico, quiero poder marcar una refacción de un trabajo autorizado como «No disponible» y generar una solicitud de compra desde la orden de servicio, para que el área de Compras sepa qué pieza se necesita y pueda gestionar su adquisición.

| ID | Criterio de aceptación |
|---|---|
| **CA-019**<br>Solicitar una refacción no disponible | **Dado** que el técnico verificó en el almacén que una refacción de un trabajo autorizado no está disponible<br>**Cuando** la marca como «No disponible» y captura la descripción y la cantidad<br>**Entonces** el sistema debe crear una «Solicitud de Compra» en estado «Solicitada» con su fecha<br>**Y** debe mostrarla en la lista de Compras<br>**Y** debe cambiar la orden a «En Espera de Refacción» |
| **CA-020**<br>No se piden refacciones de trabajos no autorizados | **Dado** que un trabajo no ha sido autorizado por el cliente<br>**Cuando** el técnico intenta crear una solicitud de compra para ese trabajo<br>**Entonces** el sistema no debe permitirlo |

### US-011

> Como Personal de Compras, quiero ver una lista de todas las solicitudes de refacciones pendientes, para gestionar su compra con proveedores y registrar en el sistema su llegada al taller.

| ID | Criterio de aceptación |
|---|---|
| **CA-021**<br>Lista de solicitudes pendientes | **Dado** que el Personal de Compras inicia sesión<br>**Cuando** accede a «Solicitudes pendientes»<br>**Entonces** debe visualizar todas las solicitudes en estado «Solicitada» con número de orden, refacción, cantidad, fecha de solicitud y días hábiles transcurridos |
| **CA-022**<br>Registrar la llegada de la refacción **(v3.0, H-PIA-07)** | **Dado** que una refacción solicitada llegó al taller<br>**Cuando** Compras registra su llegada<br>**Entonces** el sistema debe cambiar la solicitud a «Disponible»<br>**Y** debe notificar al técnico y al asesor<br>**Y** si la orden ya no tiene solicitudes pendientes, debe regresarla al estado que tenía antes de la espera («Autorizada» o «En Reparación»; si durante la espera se inició algún trabajo, a «En Reparación») |

### US-012

> Como Asesor de Servicio, quiero recibir una alerta automática en el sistema si una refacción solicitada tarda más de 3 días hábiles en llegar, para poder contactar proactivamente al cliente y comunicarle el retraso, mejorando la comunicación y la confianza.

| ID | Criterio de aceptación |
|---|---|
| **CA-023**<br>Alerta por refacción con más de 3 días hábiles **(v3.0, H-PIA-10)** | **Dado** que una solicitud de compra lleva más de 3 días hábiles en estado «Solicitada»<br>**Cuando** el sistema ejecuta su revisión diaria<br>**Entonces** debe generar una alerta en el panel del asesor responsable de la orden<br>**Cuando** el asesor avisa al cliente y lo registra<br>**Entonces** el sistema guarda la fecha y hora de la notificación<br>**Y** no vuelve a generar la alerta para esa solicitud |

### US-013

> Como Asesor de Servicio, quiero registrar la salida de un vehículo cuya orden está en espera de refacciones, generando la Nota de Responsabilidad, para permitir que el cliente use su vehículo y dejar constancia formal de que lo retiró sin que la reparación estuviera terminada.

| ID | Criterio de aceptación |
|---|---|
| **CA-024**<br>Retiro anticipado con Nota de Responsabilidad | **Dado** que una orden está en «En Espera de Refacción» y el cliente desea retirar su vehículo<br>**Cuando** el asesor registra la salida<br>**Entonces** el sistema debe generar el PDF de la «Nota de Responsabilidad» para imprimirla<br>**Cuando** el asesor marca que el cliente la firmó<br>**Entonces** la orden pasa a «Pausada por Retiro de Vehículo»<br>**Y** sale de la fila de trabajo |
| **CA-025**<br>Reactivar la orden al final de la fila **(v3.0, H-PIA-07)** | **Dado** que una orden está en «Pausada por Retiro de Vehículo»<br>**Cuando** el cliente regresa con el vehículo y el asesor reactiva la orden<br>**Entonces** el sistema debe regresarla a «En Espera de Refacción» si aún falta alguna refacción o, si ya están todas, a «Autorizada» (ningún trabajo iniciado) o a «En Reparación» (algún trabajo ya iniciado)<br>**Y** debe asignarle una nueva fecha de ingreso a la fila, de modo que quede al final |

### US-014

> Como Personal de Caja, quiero registrar el pago de una orden de cliente particular cuando está lista para entrega, para cerrar la parte administrativa del servicio.

| ID | Criterio de aceptación |
|---|---|
| **CA-026**<br>Registrar el pago de contado | **Dado** que una orden de cliente particular está en estado «Lista para Entrega»<br>**Cuando** Caja registra el pago del total y la forma de pago (efectivo, tarjeta o transferencia)<br>**Entonces** el sistema debe cambiar el estado de la orden a «Pagada»<br>**Y** debe impedir que se modifiquen los costos |
| **CA-058**<br>Corregir la forma de pago antes de la entrega **(v3.1, H-PIA-24)** | **Dado** que Caja registró el pago de una orden con la forma de pago equivocada y la orden sigue «Pagada»<br>**Cuando** Caja corrige la forma de pago<br>**Entonces** el sistema debe guardar la forma de pago correcta sin cambiar el monto, la fecha del pago ni el estado de la orden<br>**Y** debe dejar constancia de la forma de pago anterior y de la nueva<br>**Y** si el vehículo ya se entregó, no debe permitir el cambio |

### US-015

> Como Personal de Caja, quiero generar un recibo interno de una orden pagada, para entregar al cliente un comprobante de pago sin necesidad de emitir facturas fiscales.

| ID | Criterio de aceptación |
|---|---|
| **CA-027**<br>Generar el recibo interno **(v3.0, H-PIA-11)** | **Dado** que la orden de servicio tiene un pago registrado (estado «Pagada», o «Cerrada» si ya se entregó el vehículo)<br>**Cuando** Caja selecciona la opción «Generar recibo»<br>**Entonces** el sistema debe generar un archivo PDF del recibo interno con su número, los datos de la orden y del cliente, el monto y la forma de pago |

### US-016

> Como Asesor de Servicio, quiero registrar a un cliente como tipo «Flotilla», vinculado a su empresa y a su Responsable de Flotilla, para que las decisiones sobre las cotizaciones se registren a nombre del responsable y no del conductor.

| ID | Criterio de aceptación |
|---|---|
| **CA-028**<br>Registrar un cliente de flotilla | **Dado** que el asesor registra una orden para un vehículo de empresa<br>**Cuando** selecciona el tipo de cliente «Flotilla»<br>**Entonces** el sistema debe pedir la empresa<br>**Y** debe mostrar los datos de su Responsable de Flotilla (nombre, teléfono y correo)<br>**Y** debe permitir registrarlos si la empresa es nueva |
| **CA-029**<br>En flotillas solo autoriza el Responsable de Flotilla | **Dado** que la orden es de un cliente de flotilla<br>**Cuando** el asesor registra la decisión sobre una cotización (inicial o adicional)<br>**Entonces** el sistema debe registrarla a nombre del Responsable de Flotilla<br>**Y** no debe permitir registrar al conductor como autorizante |

### US-017

> Como Gerente de Taller, quiero ver un listado de todas las órdenes abiertas y cerradas, para tener visibilidad del estado general del taller.

| ID | Criterio de aceptación |
|---|---|
| **CA-030**<br>Listado de órdenes abiertas y cerradas | **Dado** que el Gerente inicia sesión en el sistema<br>**Cuando** accede a la sección «Órdenes»<br>**Entonces** debe visualizar un listado con todas las órdenes abiertas y cerradas, mostrando su estado actual |

### US-018

> Como Gerente de Taller, quiero ver el total de ingresos del día, para conocer el desempeño financiero diario del taller.

| ID | Criterio de aceptación |
|---|---|
| **CA-031**<br>Total de ingresos del día | **Dado** que el Gerente inicia sesión en el sistema<br>**Cuando** accede a la sección «Ingresos del día»<br>**Entonces** debe visualizar el monto total de los pagos registrados en la fecha actual (sin incluir los cargos a crédito) |

### US-019

> Como Técnico, quiero registrar el diagnóstico de la orden que me fue asignada y reportar las fallas adicionales que encuentre durante la reparación, para que el asesor pueda generar las cotizaciones con información técnica completa.

| ID | Criterio de aceptación |
|---|---|
| **CA-032**<br>Registrar el diagnóstico | **Dado** que una orden está en «En Diagnóstico» y asignada a un técnico<br>**Cuando** el técnico registra las fallas encontradas y los trabajos y refacciones recomendados<br>**Entonces** el sistema debe guardar el diagnóstico con fecha y hora<br>**Y** debe notificar al asesor que la orden está lista para cotizar |
| **CA-033**<br>El diagnóstico no cambia después de cotizar | **Dado** que la orden ya tiene una cotización generada<br>**Cuando** el técnico intenta modificar el diagnóstico<br>**Entonces** el sistema no debe permitirlo<br>**Y** debe indicar que cualquier hallazgo nuevo se registra como falla adicional |
| **CA-034**<br>Reportar una falla adicional | **Dado** que una orden está en «En Reparación»<br>**Cuando** el técnico reporta una falla adicional con su descripción<br>**Entonces** el sistema debe vincularla a la orden<br>**Y** debe notificar al asesor para que genere la cotización adicional |

### US-020

> Como Asesor de Servicio, quiero asignar un técnico a cada orden, tanto para el diagnóstico como para los trabajos autorizados, para que cada técnico sepa qué vehículos debe atender.

| ID | Criterio de aceptación |
|---|---|
| **CA-035**<br>Asignar técnico para el diagnóstico | **Dado** que una orden está en estado «Recibida»<br>**Cuando** el asesor le asigna un técnico<br>**Entonces** el sistema debe cambiar la orden a «En Diagnóstico»<br>**Y** debe mostrarla en el panel de ese técnico |
| **CA-036**<br>Asignar los trabajos autorizados | **Dado** que una orden tiene trabajos autorizados sin asignar<br>**Cuando** el asesor los asigna a un técnico<br>**Entonces** el sistema debe mostrarlos en el panel de ese técnico en estado «Pendiente» |
| **CA-053**<br>Lista de técnicos para asignar **(v3.1, H-PIA-23)** | **Dado** que el asesor va a asignar un técnico para el diagnóstico o para los trabajos autorizados<br>**Cuando** consulta la lista de técnicos<br>**Entonces** el sistema debe mostrar la clave y el nombre de cada empleado con rol Técnico<br>**Y** no debe mostrar empleados de otros puestos |
| **CA-054**<br>Cambiar el técnico de diagnóstico **(v3.1, H-PIA-23)** | **Dado** que una orden está en «En Diagnóstico» y el técnico asignado todavía no registra el diagnóstico<br>**Cuando** el asesor asigna a otro técnico<br>**Entonces** el sistema debe cambiar el técnico de la orden sin cambiar su estado<br>**Y** la orden debe salir del panel del técnico anterior y aparecer en el del nuevo<br>**Y** si el diagnóstico ya está registrado, no debe permitir el cambio e indicar que el diagnóstico ya está registrado |

### US-021

> Como Cliente, quiero consultar el estado de mi vehículo ingresando mi número de orden y mis placas, para saber cómo va el servicio sin tener que llamar al taller.

| ID | Criterio de aceptación |
|---|---|
| **CA-037**<br>Consulta de estado con datos correctos | **Dado** que un cliente entra a la pantalla «Consulta tu vehículo»<br>**Cuando** escribe su número de orden y sus placas y ambos coinciden<br>**Entonces** el sistema debe mostrar el estado actual de la orden, la fecha de ingreso y la fecha de su última actualización<br>**Y** no debe permitir modificar nada |
| **CA-038**<br>Consulta de estado con datos que no coinciden | **Dado** que un cliente está en la pantalla «Consulta tu vehículo»<br>**Cuando** el número de orden y las placas no coinciden con ninguna orden<br>**Entonces** el sistema debe mostrar el mensaje «No se encontró una orden con esos datos. Revise el número de orden y las placas e intente de nuevo.» sin revelar ninguna información |

### US-022

> Como Personal de Caja, quiero registrar un cargo a crédito de 15 días (contados desde la entrega del vehículo) para las órdenes de clientes de flotilla, para cerrar la parte administrativa del servicio sin cobrarle al conductor y dejar registrada la fecha en que la empresa debe pagar.

| ID | Criterio de aceptación |
|---|---|
| **CA-039**<br>Registrar el cargo a crédito de una flotilla **(v3.0, H-PIA-02)** | **Dado** que una orden de cliente de flotilla está en «Lista para Entrega»<br>**Cuando** Caja registra el cargo a crédito<br>**Entonces** el sistema debe cambiar la orden a «Por Cobrar (Crédito)»<br>**Y** debe registrar el monto del cargo<br>**Y** debe impedir que se modifiquen los costos<br>**Y** la fecha de vencimiento queda pendiente hasta que se entregue el vehículo |

### US-023

> Como Asesor de Servicio, quiero recibir una alerta cuando una cotización presentada lleve más de 48 horas sin respuesta, para volver a contactar al cliente o al Responsable de Flotilla.

| ID | Criterio de aceptación |
|---|---|
| **CA-040**<br>Alerta por cotización sin respuesta en 48 horas **(v3.0, H-PIA-10)** | **Dado** que una cotización lleva más de 48 horas en «Pendiente de Autorización del Cliente» desde que se marcó como presentada (o desde el último recontacto)<br>**Cuando** el sistema ejecuta su revisión<br>**Entonces** debe generar una alerta en el panel del asesor<br>**Cuando** el asesor registra el recontacto<br>**Entonces** el sistema guarda la fecha y hora sin cambiar el estado de la cotización<br>**Y** el plazo de 48 horas vuelve a contar desde ese recontacto |

### US-024

> Como Asesor de Servicio, quiero registrar la entrega del vehículo al cliente, para cerrar la orden de servicio y dejar constancia de cuándo salió el vehículo del taller.

| ID | Criterio de aceptación |
|---|---|
| **CA-041**<br>Entregar el vehículo y cerrar la orden **(v3.0, H-PIA-02)** | **Dado** que una orden está en «Pagada» o en «Por Cobrar (Crédito)»<br>**Cuando** el asesor registra la entrega del vehículo<br>**Entonces** el sistema debe cambiar la orden a «Cerrada»<br>**Y** debe guardar la fecha y hora de entrega<br>**Y** si la orden tiene cargo a crédito, debe registrar su fecha de vencimiento: 15 días naturales después de la entrega |
| **CA-042**<br>No se entrega sin pago ni cargo a crédito | **Dado** que una orden no está en «Pagada» ni en «Por Cobrar (Crédito)»<br>**Cuando** el asesor intenta registrar la entrega<br>**Entonces** el sistema no debe permitirlo<br>**Y** si la orden todavía puede cobrarse, debe indicar que primero debe registrarse el pago o el cargo a crédito<br>**Y** si la orden está «Cancelada», «Cerrada» o «Cerrada sin Reparación», debe indicar esa situación sin pedir el pago |
| **CA-043**<br>Entregar el vehículo sin reparación | **Dado** que el cliente rechazó toda la cotización<br>**Cuando** el asesor selecciona «Entregar sin reparación»<br>**Entonces** el sistema debe cambiar la orden a «Cerrada sin Reparación»<br>**Y** debe guardar la fecha y hora de entrega<br>**Y** no debe generar ningún cobro |

### US-025

> Como Asesor de Servicio, quiero cancelar una orden cuando el cliente desiste del servicio antes de que se genere la cotización, para cerrar el expediente sin cobro y dejar registrado el motivo.

| ID | Criterio de aceptación |
|---|---|
| **CA-044**<br>Cancelar la orden antes de la cotización **(v3.0, H-PIA-01)** | **Dado** que una orden está en «Recibida» o «En Diagnóstico»<br>**Y** el cliente decide no continuar con el servicio<br>**Cuando** el asesor registra la cancelación indicando el motivo<br>**Entonces** el sistema debe cambiar la orden a «Cancelada»<br>**Y** debe guardar la fecha, la hora y el motivo<br>**Y** debe quitarla del panel del técnico asignado, si tenía uno<br>**Y** no debe generar ningún cobro |
| **CA-045**<br>No se cancela una orden que ya tiene cotización **(v3.0, H-PIA-01)** | **Dado** que una orden ya tiene una cotización generada («Cotizada» o un estado posterior)<br>**Cuando** el asesor intenta cancelarla<br>**Entonces** el sistema no debe permitirlo<br>**Y** debe indicar que la orden no se puede cancelar<br>**Y** si la orden está «Cotizada» y el cliente aún no decide, debe indicar que, si no desea la reparación, se registra el rechazo total de la cotización |

### US-026

> Como Asesor de Servicio, quiero corregir una cotización con un importe o una descripción mal capturados mientras espera la revisión del Gerente o la decisión del cliente, indicando el motivo, para presentar un documento correcto sin perder el historial de lo que cambió.

| ID | Criterio de aceptación |
|---|---|
| **CA-047**<br>Corregir una cotización que espera la decisión del cliente **(v3.1, H-PIA-21)** | **Dado** que una cotización está en «Pendiente de Autorización del Cliente» con un importe o una descripción mal capturados<br>**Cuando** el asesor la corrige capturando los trabajos correctos y el motivo de la corrección<br>**Entonces** el sistema debe guardar los trabajos corregidos conservando el número y la versión de la cotización<br>**Y** debe guardar en el historial de correcciones al asesor, la fecha y hora, el motivo, el total anterior y el total nuevo<br>**Y** si la cotización no requiere aprobación gerencial, debe dejarla en «Pendiente de Autorización del Cliente» como no presentada, para que el asesor la presente otra vez |
| **CA-048**<br>La corrección sube la cotización inicial arriba de $15,000 MXN **(v3.1, H-PIA-21)** | **Dado** que una cotización inicial está en «Pendiente de Autorización del Cliente», aunque el Gerente ya la haya aprobado o se haya ajustado según sus observaciones<br>**Cuando** el asesor la corrige y el total nuevo es mayor a $15,000 MXN<br>**Entonces** el sistema debe cambiarla a «Pendiente de Aprobación Gerencial»<br>**Y** debe borrar la fecha de aprobación gerencial, que queda guardada en el historial de la corrección<br>**Y** debe enviar una alerta al panel del Gerente<br>**Y** debe impedir que se presente al cliente hasta que el Gerente la apruebe |
| **CA-049**<br>Corregir una cotización que espera al Gerente **(v3.1, H-PIA-21)** | **Dado** que una cotización está en «Pendiente de Aprobación Gerencial»<br>**Cuando** el asesor la corrige capturando el motivo<br>**Entonces** si el total nuevo sigue siendo mayor a $15,000 MXN, la cotización debe quedarse en «Pendiente de Aprobación Gerencial» con los trabajos corregidos<br>**Y** si el total nuevo es menor o igual a $15,000 MXN, debe cambiarla a «Pendiente de Autorización del Cliente» como no presentada<br>**Y** en los dos casos debe guardar la corrección en el historial |
| **CA-050**<br>No se corrige sin motivo ni una cotización por ajustar o ya decidida **(v3.1, H-PIA-21)** | **Dado** que el asesor intenta corregir una cotización<br>**Cuando** la cotización está en «Requiere Ajuste», «Autorizada», «Autorizada Parcialmente» o «Rechazada», o el asesor no captura el motivo<br>**Entonces** el sistema no debe permitirlo<br>**Y** si falta el motivo, debe pedir que lo capture<br>**Y** si está en «Requiere Ajuste», debe indicar que se guarde la cotización ajustada según las observaciones del Gerente<br>**Y** si ya tiene la decisión del cliente, debe indicar que ya no se corrige y que los trabajos nuevos se cotizan con una cotización adicional |
| **CA-051**<br>El plazo de 48 horas después de una corrección **(v3.1, H-PIA-21)** | **Dado** que una cotización presentada, con recontactos registrados, se corrigió y quedó en «Pendiente de Autorización del Cliente»<br>**Cuando** el sistema ejecuta su revisión de plazos antes de que el asesor la presente otra vez<br>**Entonces** no debe generar la alerta de 48 horas<br>**Y** debe conservar los recontactos anteriores como historial<br>**Cuando** el asesor la presenta otra vez<br>**Entonces** el plazo de 48 horas debe contar solo desde la nueva presentación y los recontactos posteriores a ella |

### US-027

> Como Asesor de Servicio, quiero corregir los datos del cliente, del vehículo y del estado de recepción que capturé mal, para que el expediente quede correcto sin tener que abrir otra orden.

| ID | Criterio de aceptación |
|---|---|
| **CA-055**<br>Corregir los datos del cliente **(v3.1, H-PIA-24)** | **Dado** que el nombre, el teléfono o el correo de un cliente se capturaron mal<br>**Cuando** el asesor los corrige<br>**Entonces** el sistema debe guardar los datos corregidos sin cambiar las órdenes ni las cotizaciones del cliente<br>**Y** las decisiones que se registren después deben compararse con el nombre corregido |
| **CA-056**<br>Corregir los datos del vehículo **(v3.1, H-PIA-24)** | **Dado** que el VIN, la marca, el modelo o el año de un vehículo se capturaron mal<br>**Cuando** el asesor los corrige<br>**Entonces** el sistema debe guardar los datos corregidos sin cambiar las placas<br>**Y** si el VIN corregido ya pertenece a otro vehículo, no debe permitirlo e indicar que revise el dato |
| **CA-057**<br>Corregir el estado de recepción **(v3.1, H-PIA-24)** | **Dado** que una orden está en «Recibida» o «En Diagnóstico»<br>**Cuando** el asesor corrige el kilometraje, el nivel de combustible o el motivo de ingreso<br>**Entonces** el sistema debe guardar los datos corregidos sin cambiar el estado de la orden<br>**Y** si la orden ya tiene cotización, no debe permitirlo e indicar que esos datos solo se corrigen antes de la cotización |

## 4. Validación y trazabilidad

| ID Necesidad | User Stories relacionadas | Criterios de aceptación | Proceso modelado en BPMN |
|---|---|---|---|
| N-01 | US-001, US-002, US-003 | CA-001, CA-002, CA-003, CA-004, CA-052, CA-059 | Fase 1: Recepción y registro |
| N-02 | US-004 | CA-005, CA-006, CA-060 | Fase 2: Diagnóstico y cotización; Fase 3: Autorización |
| N-03 | US-006 | CA-010, CA-011, CA-012 | Fase 3: Autorización |
| N-04 | US-005 | CA-007, CA-008, CA-009 | Fase 2: Diagnóstico y cotización |
| N-05 | US-012 | CA-023 | Fase 4: Gestión de refacciones |
| N-06 | US-009, US-019 | CA-016, CA-017, CA-018, CA-034 | Fase 5: Reparación y ampliación |
| N-07 | US-016, US-022 | CA-028, CA-029, CA-039, CA-041 | Fase 1, Fase 3 y Fase 6: Cierre, pago y entrega |
| N-08 | US-017, US-018 | CA-030, CA-031 | Consulta transversal (no es una tarea del flujo) |
| N-09 | US-007, US-008, US-019, US-020 | CA-013, CA-014, CA-015, CA-032, CA-033, CA-035, CA-036, CA-046, CA-053, CA-054 | Fase 1, Fase 2 y Fase 5 |
| N-10 | US-010, US-011 | CA-019, CA-020, CA-021, CA-022 | Fase 4: Gestión de refacciones |
| N-11 | US-014, US-015, US-024 | CA-026, CA-027, CA-041, CA-042, CA-043, CA-058 | Fase 6: Cierre, pago y entrega (y Fase 3 para la entrega sin reparación) |
| N-12 | US-013 | CA-024, CA-025 | Diagrama 2 (Casos especiales): Retiro anticipado |
| N-13 | US-021 | CA-037, CA-038 | Consulta transversal (no es una tarea del flujo) |
| N-14 | US-023 | CA-040 | Fase 3: Autorización (temporizador de 48 h) |
| N-15 | US-025 | CA-044, CA-045 | Diagrama 2 (Casos especiales): Cliente desiste antes de la cotización |
| N-16 | US-026, US-020, US-027, US-014 | CA-047, CA-048, CA-049, CA-050, CA-051, CA-054, CA-055, CA-056, CA-057, CA-058 | Fase 2 y Fase 3: corrección de la cotización (v3.1) |

La trazabilidad completa de cada criterio hasta la regla de negocio, el componente, la ruta de la API y la prueba está en [trazabilidad/matriz-trazabilidad.md](trazabilidad/matriz-trazabilidad.md).

## 5. Bibliografía

- Cohn, M. (2004). *User stories applied: For agile software development*. Addison-Wesley.
- Evans, E. (2003). *Domain-driven design: Tackling complexity in the heart of software*. Addison-Wesley Professional.
- Lee, C. (2023). *The art of crafting user stories* (1st ed.). Packt Publishing.
- SmartBear. (s. f.). *Gherkin reference*. Cucumber. https://cucumber.io/docs/gherkin/reference/
- Vernon, V. (2013). *Implementing domain-driven design*. Addison-Wesley Professional.
