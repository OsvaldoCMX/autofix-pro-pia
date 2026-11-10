# language: es
@autorizacion
Característica: Autorización del cliente y cotizaciones adicionales
  Registrar con evidencia la decisión del cliente o del Responsable de Flotilla.

  User Stories de esta característica:
    US-006: Como Asesor de Servicio, quiero registrar la decisión del cliente cuando autoriza total o parcialmente, o rechaza una cotización, para tener evidencia formal de lo que se acordó y poder iniciar solo los trabajos autorizados, evitando disputas posteriores.
    US-009: Como Asesor de Servicio, quiero poder crear una cotización adicional si durante la reparación se descubren nuevas fallas, para obtener la autorización del cliente para los trabajos extra sin modificar la cotización original, manteniendo un historial claro.

  # ---------------------------------------------------------------- US-006 (Asesor de Servicio)

  @US-006 @CA-010
  Escenario: CA-010 Registrar la autorización total o parcial
    Dado que el cliente (o el Responsable de Flotilla) revisó la cotización
    Cuando el asesor selecciona los trabajos autorizados y guarda la decisión
    Entonces el sistema debe cambiar la cotización a «Autorizada» o «Autorizada Parcialmente»
    Y debe cambiar la orden a «Autorizada»
    Y debe registrar la fecha, la hora y el nombre de quien autorizó
    Y debe marcar los trabajos no aceptados como «No Autorizado»

  @US-006 @CA-011
  Escenario: CA-011 Solo se asignan los trabajos autorizados
    Dado que el cliente autorizó parcialmente la cotización
    Cuando el asesor asigna los trabajos a un técnico
    Entonces el sistema solo debe permitir seleccionar los trabajos autorizados

  @US-006 @CA-012
  Escenario: CA-012 Registrar el rechazo total
    Dado que el cliente no acepta ningún trabajo de la cotización
    Cuando el asesor registra el rechazo total
    Entonces el sistema debe cambiar la cotización a «Rechazada»
    Y debe impedir la asignación de trabajos
    Y debe habilitar la opción «Entregar sin reparación»

  # ---------------------------------------------------------------- US-009 (Asesor de Servicio)

  @US-009 @CA-016
  Escenario: CA-016 Crear una cotización adicional
    Dado que el técnico reportó una falla adicional en una orden «En Reparación»
    Cuando el asesor crea una nueva cotización vinculada a esa orden
    Entonces el sistema debe etiquetarla como «Cotización Adicional»
    Y debe asignarle la siguiente versión (v.2, v.3…)
    Y debe dejarla en «Pendiente de Autorización del Cliente» sin importar su monto
    Y debe mantener sin cambios la cotización original

  @US-009 @CA-017
  Escenario: CA-017 El cliente autoriza la cotización adicional
    Dado que el cliente autoriza la cotización adicional
    Cuando el asesor registra la decisión
    Entonces los trabajos adicionales se agregan a la orden en estado «Pendiente»
    Y el sistema debe notificar al técnico

  @US-009 @CA-018 @v3
  Escenario: CA-018 El cliente rechaza la cotización adicional
    Dado que el cliente rechaza la cotización adicional
    Cuando el asesor registra la decisión
    Entonces el sistema debe marcar los trabajos adicionales como «No Autorizado»
    Y la orden continúa solo con los trabajos autorizados originalmente
    Y si esos trabajos ya estaban completados, la orden pasa a «Lista para Entrega»

  @US-009 @CA-061 @v3.1
  Escenario: CA-061 Una sola cotización adicional sin decisión a la vez
    Dado que una orden tiene una cotización adicional en «Pendiente de Autorización del Cliente»
    Cuando el asesor intenta generar otra cotización adicional, por ejemplo con un doble clic
    Entonces el sistema no debe generarla
    Y debe indicar que primero se registre la decisión del cliente sobre la cotización adicional pendiente, con su versión
