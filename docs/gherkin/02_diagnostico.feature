# language: es
@diagnostico
Característica: Asignación y diagnóstico
  Asignar técnicos, registrar el diagnóstico y reportar fallas adicionales.

  User Stories de esta característica:
    US-020: Como Asesor de Servicio, quiero asignar un técnico a cada orden, tanto para el diagnóstico como para los trabajos autorizados, para que cada técnico sepa qué vehículos debe atender.
    US-019: Como Técnico, quiero registrar el diagnóstico de la orden que me fue asignada y reportar las fallas adicionales que encuentre durante la reparación, para que el asesor pueda generar las cotizaciones con información técnica completa.
    US-007: Como Técnico, quiero ver en mi panel las órdenes de servicio y trabajos que me han sido asignados, ordenados según la fila de trabajo, para organizar mi jornada y saber exactamente en qué vehículo debo trabajar primero.

  # ---------------------------------------------------------------- US-020 (Asesor de Servicio)

  @US-020 @CA-035
  Escenario: CA-035 Asignar técnico para el diagnóstico
    Dado que una orden está en estado «Recibida»
    Cuando el asesor le asigna un técnico
    Entonces el sistema debe cambiar la orden a «En Diagnóstico»
    Y debe mostrarla en el panel de ese técnico

  @US-020 @CA-036
  Escenario: CA-036 Asignar los trabajos autorizados
    Dado que una orden tiene trabajos autorizados sin asignar
    Cuando el asesor los asigna a un técnico
    Entonces el sistema debe mostrarlos en el panel de ese técnico en estado «Pendiente»

  @US-020 @CA-053 @v3.1
  Escenario: CA-053 Lista de técnicos para asignar
    Dado que el asesor va a asignar un técnico para el diagnóstico o para los trabajos autorizados
    Cuando consulta la lista de técnicos
    Entonces el sistema debe mostrar la clave y el nombre de cada empleado con rol Técnico
    Y no debe mostrar empleados de otros puestos

  @US-020 @CA-054 @v3.1
  Escenario: CA-054 Cambiar el técnico de diagnóstico
    Dado que una orden está en «En Diagnóstico» y el técnico asignado todavía no registra el diagnóstico
    Cuando el asesor asigna a otro técnico
    Entonces el sistema debe cambiar el técnico de la orden sin cambiar su estado
    Y la orden debe salir del panel del técnico anterior y aparecer en el del nuevo
    Y si el diagnóstico ya está registrado, no debe permitir el cambio e indicar que el diagnóstico ya está registrado

  # ---------------------------------------------------------------- US-019 (Técnico)

  @US-019 @CA-032
  Escenario: CA-032 Registrar el diagnóstico
    Dado que una orden está en «En Diagnóstico» y asignada a un técnico
    Cuando el técnico registra las fallas encontradas y los trabajos y refacciones recomendados
    Entonces el sistema debe guardar el diagnóstico con fecha y hora
    Y debe notificar al asesor que la orden está lista para cotizar

  @US-019 @CA-033
  Escenario: CA-033 El diagnóstico no cambia después de cotizar
    Dado que la orden ya tiene una cotización generada
    Cuando el técnico intenta modificar el diagnóstico
    Entonces el sistema no debe permitirlo
    Y debe indicar que cualquier hallazgo nuevo se registra como falla adicional

  @US-019 @CA-034
  Escenario: CA-034 Reportar una falla adicional
    Dado que una orden está en «En Reparación»
    Cuando el técnico reporta una falla adicional con su descripción
    Entonces el sistema debe vincularla a la orden
    Y debe notificar al asesor para que genere la cotización adicional

  # ---------------------------------------------------------------- US-007 (Técnico)

  @US-007 @CA-013
  Escenario: CA-013 Panel del técnico ordenado por la fila de trabajo
    Dado que un técnico inicia sesión en el sistema
    Cuando accede a su panel de trabajo
    Entonces debe visualizar la lista de órdenes y trabajos que le han sido asignados, ordenada según la fila de trabajo (de la fecha de ingreso a la fila más antigua a la más reciente)
