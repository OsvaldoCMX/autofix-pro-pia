# language: es
@recepcion
Característica: Recepción y registro del vehículo
  Registrar digitalmente al cliente, al vehículo y su estado de ingreso para abrir la Orden de Servicio.

  User Stories de esta característica:
    US-001: Como Asesor de Servicio, quiero poder registrar un vehículo nuevo en el sistema, para tener un expediente digital completo del cliente y su vehículo, evitando errores de captura y pérdida de papeles.
    US-002: Como Asesor de Servicio, quiero poder capturar el kilometraje, nivel de combustible y tomar fotos de los daños visibles del vehículo al momento de la recepción, para tener evidencia del estado en el que ingresó el vehículo y evitar futuras disputas con el cliente.
    US-003: Como Asesor de Servicio, quiero buscar un vehículo por su número de placas al inicio del registro, para recuperar automáticamente la información del cliente y vehículo si ya es un cliente recurrente, y así agilizar el proceso de recepción.
    US-016: Como Asesor de Servicio, quiero registrar a un cliente como tipo «Flotilla», vinculado a su empresa y a su Responsable de Flotilla, para que las decisiones sobre las cotizaciones se registren a nombre del responsable y no del conductor.
    US-027: Como Asesor de Servicio, quiero corregir los datos del cliente, del vehículo y del estado de recepción que capturé mal, para que el expediente quede correcto sin tener que abrir otra orden.

  # ---------------------------------------------------------------- US-001 (Asesor de Servicio)

  @US-001 @CA-001
  Escenario: CA-001 Registrar un vehículo nuevo y abrir su orden
    Dado que un vehículo llega al taller y el asesor abre la pantalla «Nueva Orden»
    Cuando el asesor ingresa los datos del cliente (nombre, teléfono y correo), los del vehículo (marca, modelo, año, placas y VIN) y el motivo de ingreso
    Entonces el sistema debe guardar la información
    Y debe generar un número de orden de servicio único
    Y debe asignarle el estado «Recibida»
    Y debe mostrar un mensaje de éxito

  @US-001 @CA-052 @v3.1
  Escenario: CA-052 No se abre una segunda orden del mismo vehículo
    Dado que el vehículo con placas XYZ998 ya tiene una orden abierta (en un estado distinto de «Cerrada», «Cerrada sin Reparación» y «Cancelada»)
    Cuando el asesor intenta registrar otra orden para ese vehículo, por ejemplo con un doble clic en «Registrar»
    Entonces el sistema no debe abrir una segunda orden
    Y debe mostrar el mensaje «El vehículo con placas XYZ998 ya tiene abierta la orden OS-0001 (estado «Recibida»). Ábrala en lugar de registrar otra.»
    Y aunque las dos solicitudes lleguen al mismo tiempo, solo una orden debe quedar registrada y la otra debe recibir el mismo mensaje

  @US-001 @CA-059 @v3.1
  Escenario: CA-059 Datos de captura con forma y rango razonables
    Dado que el asesor captura los datos del cliente, del Responsable de Flotilla, del vehículo y del estado de recepción
    Cuando escribe un teléfono que no tiene 10 dígitos, un correo sin la forma nombre@dominio.algo, un año mayor al año actual + 1, un kilometraje mayor a 2,000,000 o un texto de más de 1,000 caracteres
    Entonces el sistema no debe guardar el registro
    Y debe indicar qué dato está mal y cómo debe capturarse, por ejemplo «El teléfono debe tener 10 dígitos, por ejemplo 81 1234 5678.»
    Y un teléfono o un correo con solo espacios debe tratarse como no capturado

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

  @US-016 @CA-064 @v3.1
  Escenario: CA-064 Flotilla: el mensaje dice a nombre de quién y con qué rol
    Dado que la orden es de un cliente de flotilla de la empresa «Transportes Norte», cuyo Responsable de Flotilla es «Ana Torres»
    Cuando el asesor registra la decisión con el rol «Cliente» o a nombre de otra persona
    Entonces el sistema no debe registrarla
    Y debe indicar la empresa, el nombre del Responsable de Flotilla y el rol con el que se registra: «Para la flotilla de Transportes Norte, registre la decisión a nombre de su Responsable de Flotilla, Ana Torres, con el rol «Responsable de Flotilla».»

  @US-016 @CA-065 @v3.1
  Escenario: CA-065 La empresa de flotilla ya está registrada
    Dado que la empresa «Transportes Norte» ya está registrada con su Responsable de Flotilla «Ana Torres»
    Cuando el asesor registra la misma empresa con datos distintos del responsable
    Entonces el sistema no debe crear otra empresa ni cambiar en silencio al responsable registrado
    Y debe indicar que la empresa ya está registrada, con el nombre y el teléfono de su Responsable de Flotilla, para que use ese registro
    Y si los datos del responsable son los mismos, debe devolver la empresa registrada, como hasta ahora

  # ---------------------------------------------------------------- US-027 (Asesor de Servicio)

  @US-027 @CA-055 @v3.1
  Escenario: CA-055 Corregir los datos del cliente
    Dado que el nombre, el teléfono o el correo de un cliente se capturaron mal
    Cuando el asesor los corrige
    Entonces el sistema debe guardar los datos corregidos sin cambiar las órdenes ni las cotizaciones del cliente
    Y las decisiones que se registren después deben compararse con el nombre corregido

  @US-027 @CA-056 @v3.1
  Escenario: CA-056 Corregir los datos del vehículo
    Dado que el VIN, la marca, el modelo o el año de un vehículo se capturaron mal
    Cuando el asesor los corrige
    Entonces el sistema debe guardar los datos corregidos sin cambiar las placas
    Y si el VIN corregido ya pertenece a otro vehículo, no debe permitirlo e indicar que revise el dato

  @US-027 @CA-057 @v3.1
  Escenario: CA-057 Corregir el estado de recepción
    Dado que una orden está en «Recibida» o «En Diagnóstico»
    Cuando el asesor corrige el kilometraje, el nivel de combustible o el motivo de ingreso
    Entonces el sistema debe guardar los datos corregidos sin cambiar el estado de la orden
    Y si la orden ya tiene cotización, no debe permitirlo e indicar que esos datos solo se corrigen antes de la cotización
