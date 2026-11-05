# language: es
@recepcion
Característica: Recepción y registro del vehículo
  Registrar digitalmente al cliente, al vehículo y su estado de ingreso para abrir la Orden de Servicio.

  User Stories de esta característica:
    US-001: Como Asesor de Servicio, quiero poder registrar un vehículo nuevo en el sistema, para tener un expediente digital completo del cliente y su vehículo, evitando errores de captura y pérdida de papeles.
    US-002: Como Asesor de Servicio, quiero poder capturar el kilometraje, nivel de combustible y tomar fotos de los daños visibles del vehículo al momento de la recepción, para tener evidencia del estado en el que ingresó el vehículo y evitar futuras disputas con el cliente.
    US-003: Como Asesor de Servicio, quiero buscar un vehículo por su número de placas al inicio del registro, para recuperar automáticamente la información del cliente y vehículo si ya es un cliente recurrente, y así agilizar el proceso de recepción.
    US-016: Como Asesor de Servicio, quiero registrar a un cliente como tipo «Flotilla», vinculado a su empresa y a su Responsable de Flotilla, para que las decisiones sobre las cotizaciones se registren a nombre del responsable y no del conductor.

  # ---------------------------------------------------------------- US-001 (Asesor de Servicio)

  @US-001 @CA-001
  Escenario: CA-001 Registrar un vehículo nuevo y abrir su orden
    Dado que un vehículo llega al taller y el asesor abre la pantalla «Nueva Orden»
    Cuando el asesor ingresa los datos del cliente (nombre, teléfono y correo), los del vehículo (marca, modelo, año, placas y VIN) y el motivo de ingreso
    Entonces el sistema debe guardar la información
    Y debe generar un número de orden de servicio único
    Y debe asignarle el estado «Recibida»
    Y debe mostrar un mensaje de éxito

  # ---------------------------------------------------------------- US-002 (Asesor de Servicio)

  @US-002 @CA-002
  Escenario: CA-002 Capturar el estado de ingreso y las fotos de daños
    Dado que el asesor está en la pantalla de registro de un vehículo
    Cuando ingresa el kilometraje, selecciona el nivel de combustible y adjunta las fotos de los daños
    Entonces el sistema debe almacenar estos datos y fotos como parte del expediente de la orden de servicio

  # ---------------------------------------------------------------- US-003 (Asesor de Servicio)

  @US-003 @CA-003
  Escenario: CA-003 Encontrar un cliente recurrente por sus placas
    Dado que el asesor está en la pantalla de inicio de una nueva orden
    Cuando escribe el número de placas
    Y el sistema encuentra un registro previo
    Entonces el sistema debe mostrar los datos precargados del cliente y el vehículo
    Y el asesor solo debe confirmarlos o actualizarlos

  @US-003 @CA-004
  Escenario: CA-004 Placas no registradas
    Dado que el asesor ingresa un número de placas que no existe en el sistema
    Cuando el sistema no encuentra el vehículo
    Entonces debe habilitar la opción para crear un nuevo registro desde cero

  # ---------------------------------------------------------------- US-016 (Asesor de Servicio)

  @US-016 @CA-028
  Escenario: CA-028 Registrar un cliente de flotilla
    Dado que el asesor registra una orden para un vehículo de empresa
    Cuando selecciona el tipo de cliente «Flotilla»
    Entonces el sistema debe pedir la empresa
    Y debe mostrar los datos de su Responsable de Flotilla (nombre, teléfono y correo)
    Y debe permitir registrarlos si la empresa es nueva

  @US-016 @CA-029
  Escenario: CA-029 En flotillas solo autoriza el Responsable de Flotilla
    Dado que la orden es de un cliente de flotilla
    Cuando el asesor registra la decisión sobre una cotización (inicial o adicional)
    Entonces el sistema debe registrarla a nombre del Responsable de Flotilla
    Y no debe permitir registrar al conductor como autorizante
