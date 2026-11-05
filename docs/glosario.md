# Glosario del Dominio — AutoFix Pro

**Materia:** Componentes de Lógica de Negocio · FIME UANL · **Equipo 6**
**Versión:** 3.0 (PIA, 04/11/2026). Cambios respecto a la v2.0: se agregaron *Cancelación de la Orden*, *Motivo de Cancelación* y el estado *Orden · Cancelada* (H-PIA-01); se alineó la fecha de vencimiento del crédito con la entrega (H-PIA-02); se precisó *Rechazo Parcial* y *Diagnóstico* (H-PIA-04, H-PIA-05).

Este glosario establece el **lenguaje ubicuo** del proyecto: los mismos términos se usan en el BRD, las User Stories, los escenarios Gherkin, el BPMN, los diagramas UML y el código. Los términos se identificaron a partir del caso AutoFix Pro, la entrevista con el stakeholder y las necesidades del BRD.

## 1. Definición de términos

| Término | Definición |
|---|---|
| AutoFix Pro | Nombre comercial del taller automotriz, objeto del proyecto. Es la organización que ofrece servicios de diagnóstico, mantenimiento y reparación de vehículos. |
| Cliente | Persona física (particular) o jurídica (empresa) que contrata los servicios del taller. En los clientes particulares es quien autoriza y paga; en los clientes de flotilla, la autorización corresponde al Responsable de Flotilla y el pago se maneja como cargo a crédito. |
| Cliente Particular | Persona física que lleva su vehículo al taller de forma individual. Autoriza directamente las cotizaciones y paga al recoger su vehículo (efectivo, tarjeta o transferencia). |
| Cliente de Flotilla | Persona jurídica (empresa) que posee múltiples vehículos y ha firmado un contrato con AutoFix Pro. Tiene condiciones especiales: crédito a 15 días naturales contados desde la entrega del vehículo y proceso de autorización a través de un Responsable de Flotilla. |
| Responsable de Flotilla | Contacto autorizado por la empresa cliente de flotilla. Es la única persona que puede aprobar cotizaciones y servicios para los vehículos de la empresa. No usa el sistema: recibe la cotización por correo electrónico o teléfono y comunica su decisión al asesor, quien la registra a su nombre. |
| Conductor | Persona que lleva y recoge un vehículo de flotilla en el taller. No puede autorizar cotizaciones ni realizar pagos; solo entrega y recibe el vehículo. |
| Asesor de Servicio | Empleado del taller con funciones de atención al cliente: recibe vehículos, asigna técnicos, genera y presenta cotizaciones, registra autorizaciones, entregas y cancelaciones. Es el principal interlocutor entre el taller y el cliente. |
| Técnico | Mecánico automotriz que realiza y registra el diagnóstico, ejecuta los trabajos autorizados, reporta fallas adicionales, solicita las refacciones no disponibles y actualiza el avance de sus trabajos. |
| Gerente de Taller | Figura de autoridad dentro del taller, generalmente el dueño o administrador. Aprueba o rechaza las cotizaciones iniciales de alto monto (> $15,000 MXN) y consulta el listado de órdenes y el total de ingresos del día. |
| Personal de Compras | Área o empleado responsable de la adquisición de refacciones. Gestiona las solicitudes de compra creadas por los técnicos y registra la llegada de las piezas al taller. |
| Personal de Caja | Área o empleado encargado de registrar los pagos de los clientes particulares, registrar los cargos a crédito de las flotillas y emitir recibos internos. |
| Orden de Servicio (OS) | Documento digital que se genera al recibir un vehículo. Es el "expediente" principal que integra toda la información del servicio: datos del cliente, datos del vehículo, diagnóstico, cotizaciones, trabajos autorizados, refacciones y estado de la reparación. Se identifica con un número de orden único (folio), que el cliente usa para consultar su estado. |
| Vehículo | Bien mueble (automóvil, camioneta, etc.) que ingresa al taller para ser diagnosticado o reparado. Se identifica por atributos únicos como el número de placas, número de serie (VIN), marca, modelo y año. |
| Fila de Trabajo | Orden en que los técnicos atienden las órdenes de servicio, según su fecha de ingreso a la fila (de la más antigua a la más reciente). |
| Diagnóstico | Informe técnico que registra el técnico asignado, con fecha y hora, después de inspeccionar el vehículo: las fallas encontradas y los trabajos y refacciones recomendados. Es la base para la elaboración de la cotización. Una vez generada la cotización ya no puede modificarse; los hallazgos posteriores se registran como fallas adicionales. |
| Cotización | Documento formal que presenta al cliente el desglose detallado de los trabajos propuestos (mano de obra), las refacciones necesarias y el costo total. Tiene número único, versión, fecha y estado, y se genera en PDF. La cotización inicial corresponde a la versión 1 (v.1). |
| Presentación de la Cotización | Momento en que el asesor entrega la cotización al cliente o al Responsable de Flotilla y lo marca en el sistema. A partir de ese momento corre el plazo de 48 horas para responder. |
| Cotización Adicional | Nueva cotización generada durante la reparación cuando se detectan fallas no contempladas originalmente. No modifica la cotización inicial: se guarda como la versión siguiente (v.2, v.3…), requiere autorización del cliente y no requiere aprobación gerencial, sin importar su monto. |
| Trabajo | Cada servicio de mano de obra incluido en una cotización (por ejemplo, cambio de balatas). Es la unidad que se autoriza, se asigna a un técnico y se marca como completada. |
| Refacción | Pieza, componente o repuesto necesario para reparar o reemplazar una parte del vehículo. Puede ser original (OEM) o alternativa. |
| Verificación de Disponibilidad | Revisión física que hace el técnico en el almacén del taller para confirmar si una refacción está disponible. El sistema no controla existencias de inventario. |
| Solicitud de Compra | Petición formal que el técnico genera en el sistema cuando una refacción de un trabajo autorizado no está disponible. El Personal de Compras la gestiona con el proveedor y registra la llegada de la pieza. |
| Registro de Llegada de Refacción | Acción con la que el Personal de Compras marca una solicitud de compra como «Disponible» cuando la pieza llega al taller. El sistema notifica al técnico y al asesor. |
| Nota de Responsabilidad | Documento que el sistema genera en PDF y que el cliente firma en papel al retirar su vehículo sin que la reparación haya concluido (por espera de refacciones). Con su firma, el cliente exonera al taller de responsabilidades futuras por el estado del vehículo y acepta que pierde su lugar en la fila de trabajo. |
| Recibo Interno | Comprobante de pago que el sistema genera en PDF cuando Caja registra el pago de una orden. Acredita el pago recibido y sirve como comprobante para el cliente y para el cierre administrativo del taller. No es una factura fiscal (CFDI). |
| Cargo a Crédito | Registro que hace Caja para una orden de flotilla en lugar del pago de contado. Guarda el monto del cargo; la fecha de vencimiento se registra al entregar el vehículo y es de 15 días naturales después de la entrega. La cobranza posterior está fuera del alcance del sistema. |
| Alerta Interna | Aviso que el sistema muestra en el panel de un usuario (asesor, gerente, técnico o Compras). No es un correo ni un SMS: el contacto con el cliente lo hace el asesor. |
| Consulta de Estado | Pantalla en la que el cliente, sin crear una cuenta, escribe su número de orden y sus placas para ver el estado actual de su vehículo. |
| Listado de órdenes | Vista del sistema que muestra todas las órdenes de servicio, tanto abiertas como cerradas, con su estado actual. Está disponible para el Gerente de Taller. Se consideran cerradas las órdenes en un estado final («Cerrada», «Cerrada sin Reparación» o «Cancelada»); todas las demás están abiertas. |
| Total de Ingresos del Día | Monto total de los pagos registrados en la fecha actual (no incluye los cargos a crédito). El Gerente de Taller puede consultarlo para conocer el desempeño financiero diario del taller. |
| Proceso de Recepción | Actividad inicial donde el asesor registra los datos del cliente y del vehículo, captura el estado inicial (kilometraje, combustible, daños visibles con fotos) y el motivo de ingreso. Marca el inicio de la orden de servicio. |
| Proceso de Diagnóstico | Fase en la que el técnico asignado inspecciona el vehículo, identifica las fallas y registra el diagnóstico. Junto con la cotización, debe entregarse al cliente en un máximo de 24 horas desde la recepción. |
| Proceso de Cotización | Fase donde, a partir del diagnóstico, el asesor elabora el documento formal con los trabajos y costos. Si la cotización inicial supera $15,000 MXN, pasa primero por la aprobación del Gerente antes de presentarse al cliente. |
| Proceso de Autorización | Etapa en la que el cliente (o el Responsable de Flotilla) revisa la cotización y aprueba, rechaza o aprueba parcialmente los trabajos. Sin esta autorización, no se puede iniciar la reparación. Si no responde en 48 horas, el asesor vuelve a contactarlo. |
| Proceso de Reparación | Fase en la que el técnico ejecuta los trabajos autorizados. Incluye la asignación de trabajos, la gestión de refacciones, la atención de fallas adicionales y la actualización del estado de la orden. |
| Proceso de Entrega | Etapa final: revisión final del trabajo, pago en caja (o cargo a crédito para flotillas), emisión del recibo interno y entrega del vehículo, con la que se cierra la orden. |
| Estado de la Orden de Servicio | Situación actual en la que se encuentra una orden de servicio. Permite dar seguimiento al avance del vehículo. La lista completa de estados, y cuándo se asigna cada uno, está en la sección «Estados del sistema». |
| Asignación de Técnico | Acción mediante la cual el Asesor de Servicio designa a un técnico específico para realizar el diagnóstico o para ejecutar los trabajos autorizados de una orden de servicio. |
| Tiempo máximo de diagnóstico | Plazo máximo de 24 horas desde la recepción del vehículo para que el técnico realice el diagnóstico y el asesor presente la cotización al cliente. |
| Tiempo de Respuesta del Cliente | Plazo de 48 horas, contado desde la presentación de la cotización, para que el cliente la acepte o la rechace. Si no responde, el sistema alerta al asesor para que lo contacte nuevamente. |
| Plazo de Espera de Refacción | Período máximo de 3 días hábiles, contado desde la fecha de la solicitud de compra, antes de que el sistema alerte al asesor para que notifique al cliente sobre el retraso. |
| Monto Máximo sin Aprobación Gerencial | Límite de $15,000 MXN. La cotización inicial que supere este monto requiere aprobación del Gerente de Taller antes de presentarse al cliente. No aplica a las cotizaciones adicionales. |
| Crédito a 15 días (Flotillas) | Condición comercial exclusiva para clientes de flotilla empresarial, que les permite pagar los servicios 15 días naturales después de la entrega del vehículo. Se registra como cargo a crédito. |
| Pérdida de Lugar en la Fila | Consecuencia de que el cliente retire su vehículo antes de que la reparación concluya (por espera de refacciones). Al reactivarse la orden, recibe una nueva fecha de ingreso a la fila y queda al final. |
| Falla Adicional | Avería o problema no contemplado en el diagnóstico original, que el técnico descubre y reporta durante la reparación. Genera una cotización adicional sujeta a nueva autorización del cliente. |
| Rechazo Parcial de Cotización | Situación en la que el cliente acepta solo algunos de los trabajos propuestos en la cotización (cada trabajo se autoriza junto con sus refacciones). La orden procede únicamente con los trabajos autorizados; los demás quedan como «No Autorizado». |
| Rechazo Total de Cotización | Situación en la que el cliente no acepta ningún trabajo de la cotización. El vehículo se entrega sin reparación y la orden pasa a «Cerrada sin Reparación», sin cobro. |
| Retiro de Vehículo en Espera | Caso especial en el que el cliente decide llevarse el vehículo del taller mientras se espera la llegada de una refacción. Esto activa la generación de la Nota de Responsabilidad. |
| Ampliación de Trabajos | Proceso formal que se activa cuando, durante la reparación, se requiere realizar trabajos adicionales a los autorizados inicialmente. Se materializa a través de una cotización adicional. |
| Línea de Cotización | Cada trabajo propuesto dentro de una cotización, con su mano de obra y sus refacciones. Se identifica por su número dentro de la cotización y es la unidad que el cliente autoriza o no. |
| Decisión del Cliente | Registro de la autorización total, parcial o del rechazo de una cotización, con la fecha, la hora y el nombre de quien autorizó. A partir de ella se crean los trabajos de la orden. |
| Autorizante | Persona a cuyo nombre se registra la decisión: el Cliente Particular o, en flotillas, el Responsable de Flotilla. El conductor nunca es autorizante. |
| Política de Aprobación Gerencial | Regla que determina si una cotización debe pasar por el Gerente de Taller antes de presentarse. Actualmente aplica a la cotización inicial mayor a $15,000 MXN. |
| Cancelación de la Orden | *(v3.0)* Acción con la que el asesor cierra una orden porque el cliente desiste del servicio **antes de que se genere la cotización** (orden «Recibida» o «En Diagnóstico»). Requiere un motivo, no genera cobro y saca la orden de la fila de trabajo. Si la orden ya tiene cotización, no se cancela: se registra el rechazo total y el vehículo se entrega sin reparación. |
| Motivo de Cancelación | *(v3.0)* Texto obligatorio que el asesor captura al cancelar una orden para explicar por qué el cliente desistió. |

## 2. Estados del sistema

Para que todos los documentos usen exactamente los mismos nombres, esta tabla lista los **25 estados** que maneja el sistema, agrupados por objeto: Orden de Servicio (13), Cotización (6), Trabajo (4) y Solicitud de Compra (2). Son los mismos estados que aparecen en los criterios de aceptación, en los objetos de datos del BPMN, en los diagramas de estados y en el código.

| Estado | Significado y cuándo se asigna | En el código |
|---|---|---|
| Orden · Recibida | La orden se creó al recibir el vehículo. | `EstadoOrden.RECIBIDA` |
| Orden · En Diagnóstico | El asesor asignó un técnico para el diagnóstico. | `EstadoOrden.EN_DIAGNOSTICO` |
| Orden · Cotizada | Se generó la cotización inicial; se espera la aprobación del Gerente (si aplica) o la decisión del cliente. Si el cliente rechaza toda la cotización, la orden permanece «Cotizada» hasta que se entrega sin reparación. | `EstadoOrden.COTIZADA` |
| Orden · Autorizada | El cliente (o el Responsable de Flotilla) autorizó total o parcialmente la cotización; los trabajos ya pueden asignarse. | `EstadoOrden.AUTORIZADA` |
| Orden · En Reparación | El técnico inició al menos un trabajo autorizado. | `EstadoOrden.EN_REPARACION` |
| Orden · En Espera de Refacción | La orden tiene al menos una solicitud de compra en estado «Solicitada». Cuando llegan todas las piezas, regresa al estado que tenía antes. | `EstadoOrden.EN_ESPERA_DE_REFACCION` |
| Orden · Pausada por Retiro de Vehículo | El cliente retiró el vehículo firmando la Nota de Responsabilidad; la orden sale de la fila de trabajo hasta que el vehículo regresa. | `EstadoOrden.PAUSADA_POR_RETIRO_DE_VEHICULO` |
| Orden · Lista para Entrega | Todos los trabajos autorizados están completados. | `EstadoOrden.LISTA_PARA_ENTREGA` |
| Orden · Pagada | Caja registró el pago de un cliente particular. | `EstadoOrden.PAGADA` |
| Orden · Por Cobrar (Crédito) | Caja registró el cargo a crédito de un cliente de flotilla (la fecha de vencimiento se fija al entregar el vehículo). | `EstadoOrden.POR_COBRAR_CREDITO` |
| Orden · Cerrada | El asesor registró la entrega del vehículo (solo es posible desde «Pagada» o «Por Cobrar (Crédito)»). | `EstadoOrden.CERRADA` |
| Orden · Cerrada sin Reparación | El cliente rechazó toda la cotización y el vehículo se entregó sin reparación y sin cobro. | `EstadoOrden.CERRADA_SIN_REPARACION` |
| Orden · Cancelada | *(v3.0)* El cliente desistió antes de que se generara la cotización; el asesor registró el motivo, la orden se cerró sin cobro y salió de la fila de trabajo. | `EstadoOrden.CANCELADA` |
| Cotización · Pendiente de Aprobación Gerencial | Cotización inicial mayor a $15,000 MXN en espera de la revisión del Gerente. Todavía no puede presentarse al cliente. | `EstadoCotizacion.PENDIENTE_DE_APROBACION_GERENCIAL` |
| Cotización · Requiere Ajuste | El Gerente la rechazó con observaciones; el asesor debe ajustarla. Una vez ajustada, pasa a «Pendiente de Autorización del Cliente». | `EstadoCotizacion.REQUIERE_AJUSTE` |
| Cotización · Pendiente de Autorización del Cliente | Lista para presentarse, o ya presentada, en espera de la decisión del cliente (plazo de 48 horas desde su presentación). | `EstadoCotizacion.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE` |
| Cotización · Autorizada | El cliente aceptó todos los trabajos. | `EstadoCotizacion.AUTORIZADA` |
| Cotización · Autorizada Parcialmente | El cliente aceptó solo algunos trabajos. | `EstadoCotizacion.AUTORIZADA_PARCIALMENTE` |
| Cotización · Rechazada | El cliente no aceptó ningún trabajo. | `EstadoCotizacion.RECHAZADA` |
| Trabajo · Pendiente | Autorizado, en espera de iniciarse. | `EstadoTrabajo.PENDIENTE` |
| Trabajo · En Progreso | El técnico lo está ejecutando. | `EstadoTrabajo.EN_PROGRESO` |
| Trabajo · Completado | El técnico lo terminó. | `EstadoTrabajo.COMPLETADO` |
| Trabajo · No Autorizado | El cliente no lo aceptó; no se ejecuta. | `EstadoTrabajo.NO_AUTORIZADO` |
| Solicitud de Compra · Solicitada | Creada por el técnico; Compras la está gestionando. Desde aquí corre el plazo de 3 días hábiles. | `EstadoSolicitud.SOLICITADA` |
| Solicitud de Compra · Disponible | Compras registró la llegada de la pieza al taller. | `EstadoSolicitud.DISPONIBLE` |

**Estados finales de la orden:** «Cerrada», «Cerrada sin Reparación» y «Cancelada». Desde ellos no hay ninguna transición.

## 3. Del lenguaje del negocio al código

Los nombres de clases, métodos y eventos se escriben en español y con los mismos términos de este glosario; las carpetas del proyecto siguen la estructura que pide el PIA (`src/domain`, `src/application`, `src/infrastructure`, `src/api`).

| Término del negocio | Elemento del modelo | Tipo DDD |
|---|---|---|
| Orden de Servicio | `OrdenDeServicio` | Aggregate Root |
| Cotización / Cotización Adicional | `Cotizacion` (con `TipoCotizacion.INICIAL` / `ADICIONAL`) | Aggregate Root |
| Línea de Cotización | `LineaDeCotizacion` | Entidad interna |
| Cliente / Cliente Particular / Cliente de Flotilla | `Cliente` (con `TipoCliente`) | Aggregate Root |
| Responsable de Flotilla | `ResponsableDeFlotilla` | Value Object |
| Vehículo | `Vehiculo` | Aggregate Root |
| Asesor, Técnico, Gerente, Compras, Caja | `Empleado` (con `RolDeEmpleado`) | Aggregate Root |
| Trabajo | `Trabajo` | Entidad interna de la orden |
| Solicitud de Compra | `SolicitudDeCompra` | Entidad interna de la orden |
| Diagnóstico | `Diagnostico` | Value Object |
| Número de orden (folio), Placas, VIN | `NumeroOrden`, `Placas`, `VIN` | Value Objects |
| Importe en MXN | `Dinero` | Value Object |
| Versión de la cotización (v.1, v.2…) | `VersionCotizacion` | Value Object |
| Decisión del Cliente / Autorizante | `DecisionDelCliente` / `Autorizante` | Value Objects |
| Pago / Cargo a Crédito | `Pago` / `CargoACredito` | Value Objects |
| Cancelación de la Orden / Motivo | `Cancelacion` | Value Object |
| Política de Aprobación Gerencial | `RequiereAprobacionGerencial` | Specification |
| Autorizante válido (particular o responsable de flotilla) | `AutorizanteValido` | Specification |
| Plazo de días hábiles | `CalendarioHabil` | Domain Service |
| Kilometraje, nivel de combustible y fotos de daños | `EstadoDeRecepcion` | Value Object |
| Falla Adicional | `FallaAdicional` | Entidad interna de la orden |
| Nota de Responsabilidad / Recibo Interno | `NotaDeResponsabilidad` / `ReciboInterno` | Value Object / Entidad interna |
| Alerta Interna | `AlertaInterna` (la crea un manejador de Domain Events o la revisión de plazos) | Modelo de lectura |
