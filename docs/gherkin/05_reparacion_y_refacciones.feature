# language: es
@reparacion-y-refacciones
Característica: Reparación, refacciones y retiro anticipado
  Ejecutar los trabajos autorizados, gestionar refacciones con Compras y manejar el retiro anticipado.

  User Stories de esta característica:
    US-008: Como Técnico, quiero poder actualizar el estado de los trabajos de una orden a «En Progreso» o «Completado», para que el sistema refleje el estado actual de la reparación y el Asesor pueda informar al cliente.
    US-010: Como Técnico, quiero poder marcar una refacción de un trabajo autorizado como «No disponible» y generar una solicitud de compra desde la orden de servicio, para que el área de Compras sepa qué pieza se necesita y pueda gestionar su adquisición.
    US-011: Como Personal de Compras, quiero ver una lista de todas las solicitudes de refacciones pendientes, para gestionar su compra con proveedores y registrar en el sistema su llegada al taller.
    US-012: Como Asesor de Servicio, quiero recibir una alerta automática en el sistema si una refacción solicitada tarda más de 3 días hábiles en llegar, para poder contactar proactivamente al cliente y comunicarle el retraso, mejorando la comunicación y la confianza.
    US-013: Como Asesor de Servicio, quiero registrar la salida de un vehículo cuya orden está en espera de refacciones, generando la Nota de Responsabilidad, para permitir que el cliente use su vehículo y dejar constancia formal de que lo retiró sin que la reparación estuviera terminada.

  # ---------------------------------------------------------------- US-008 (Técnico)

  @US-008 @CA-014
  Escenario: CA-014 Iniciar un trabajo
    Dado que un técnico tiene un trabajo asignado en estado «Pendiente»
    Cuando lo actualiza a «En Progreso»
    Entonces el sistema debe registrar el cambio
    Y si la orden estaba en «Autorizada», debe cambiarla a «En Reparación»

  @US-008 @CA-015 @v3
  Escenario: CA-015 Completar el último trabajo autorizado
    Dado que un técnico está trabajando en una orden asignada
    Cuando actualiza un trabajo a «Completado»
    Y todos los trabajos autorizados de la orden quedan completados
    Y no hay una cotización adicional esperando la decisión del cliente
    Entonces el sistema debe cambiar el estado de la orden a «Lista para Entrega»
    Y debe notificar al asesor

  @US-008 @CA-046 @v3
  Escenario: CA-046 No se trabaja un vehículo retirado del taller
    Dado que una orden está en «Pausada por Retiro de Vehículo»
    Cuando el técnico intenta iniciar uno de sus trabajos
    Entonces el sistema no debe permitirlo
    Y debe indicar que el vehículo no está en el taller

  # ---------------------------------------------------------------- US-010 (Técnico)

  @US-010 @CA-019
  Escenario: CA-019 Solicitar una refacción no disponible
    Dado que el técnico verificó en el almacén que una refacción de un trabajo autorizado no está disponible
    Cuando la marca como «No disponible» y captura la descripción y la cantidad
    Entonces el sistema debe crear una «Solicitud de Compra» en estado «Solicitada» con su fecha
    Y debe mostrarla en la lista de Compras
    Y debe cambiar la orden a «En Espera de Refacción»

  @US-010 @CA-020
  Escenario: CA-020 No se piden refacciones de trabajos no autorizados
    Dado que un trabajo no ha sido autorizado por el cliente
    Cuando el técnico intenta crear una solicitud de compra para ese trabajo
    Entonces el sistema no debe permitirlo

  # ---------------------------------------------------------------- US-011 (Personal de Compras)

  @US-011 @CA-021
  Escenario: CA-021 Lista de solicitudes pendientes
    Dado que el Personal de Compras inicia sesión
    Cuando accede a «Solicitudes pendientes»
    Entonces debe visualizar todas las solicitudes en estado «Solicitada» con número de orden, refacción, cantidad, fecha de solicitud y días hábiles transcurridos

  @US-011 @CA-022 @v3
  Escenario: CA-022 Registrar la llegada de la refacción
    Dado que una refacción solicitada llegó al taller
    Cuando Compras registra su llegada
    Entonces el sistema debe cambiar la solicitud a «Disponible»
    Y debe notificar al técnico y al asesor
    Y si la orden ya no tiene solicitudes pendientes, debe regresarla al estado que tenía antes de la espera («Autorizada» o «En Reparación»; si durante la espera se inició algún trabajo, a «En Reparación»)

  # ---------------------------------------------------------------- US-012 (Asesor de Servicio)

  @US-012 @CA-023 @v3
  Escenario: CA-023 Alerta por refacción con más de 3 días hábiles
    Dado que una solicitud de compra lleva más de 3 días hábiles en estado «Solicitada»
    Cuando el sistema ejecuta su revisión diaria
    Entonces debe generar una alerta en el panel del asesor responsable de la orden
    Cuando el asesor avisa al cliente y lo registra
    Entonces el sistema guarda la fecha y hora de la notificación
    Y no vuelve a generar la alerta para esa solicitud

  # ---------------------------------------------------------------- US-013 (Asesor de Servicio)

  @US-013 @CA-024
  Escenario: CA-024 Retiro anticipado con Nota de Responsabilidad
    Dado que una orden está en «En Espera de Refacción» y el cliente desea retirar su vehículo
    Cuando el asesor registra la salida
    Entonces el sistema debe generar el PDF de la «Nota de Responsabilidad» para imprimirla
    Cuando el asesor marca que el cliente la firmó
    Entonces la orden pasa a «Pausada por Retiro de Vehículo»
    Y sale de la fila de trabajo

  @US-013 @CA-025 @v3
  Escenario: CA-025 Reactivar la orden al final de la fila
    Dado que una orden está en «Pausada por Retiro de Vehículo»
    Cuando el cliente regresa con el vehículo y el asesor reactiva la orden
    Entonces el sistema debe regresarla a «En Espera de Refacción» si aún falta alguna refacción o, si ya están todas, a «Autorizada» (ningún trabajo iniciado) o a «En Reparación» (algún trabajo ya iniciado)
    Y debe asignarle una nueva fecha de ingreso a la fila, de modo que quede al final
