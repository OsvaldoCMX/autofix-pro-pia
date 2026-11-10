# language: es
@cotizacion
Característica: Cotización y aprobación gerencial
  Generar cotizaciones formales, aprobar las de alto monto y dar seguimiento a las que no tienen respuesta.

  User Stories de esta característica:
    US-004: Como Asesor de Servicio, quiero poder generar una cotización detallada a partir del diagnóstico del técnico y registrar cuándo se la presento al cliente, para entregarle un documento formal con el desglose de mano de obra, refacciones y costos.
    US-005: Como Gerente de Taller, quiero recibir una alerta y poder aprobar o rechazar con observaciones las cotizaciones iniciales cuyo total supere los $15,000 MXN, para asegurarme de que los trabajos costosos tengan una revisión especial antes de ser presentados al cliente.
    US-023: Como Asesor de Servicio, quiero recibir una alerta cuando una cotización presentada lleve más de 48 horas sin respuesta, para volver a contactar al cliente o al Responsable de Flotilla.
    US-026: Como Asesor de Servicio, quiero corregir una cotización con un importe o una descripción mal capturados mientras espera la revisión del Gerente o la decisión del cliente, indicando el motivo, para presentar un documento correcto sin perder el historial de lo que cambió.

  # ---------------------------------------------------------------- US-004 (Asesor de Servicio)

  @US-004 @CA-005
  Escenario: CA-005 Generar la cotización inicial
    Dado que la orden tiene un diagnóstico registrado por el técnico
    Cuando el asesor agrega los trabajos (mano de obra) y las refacciones con sus costos y guarda la cotización
    Entonces el sistema debe generarla con número único, versión 1, fecha, desglose y costo total
    Y debe generar su PDF
    Y debe cambiar la orden a «Cotizada»
    Y si el total es menor o igual a $15,000 MXN, debe asignar a la cotización el estado «Pendiente de Autorización del Cliente»

  @US-004 @CA-006
  Escenario: CA-006 Marcar la cotización como presentada
    Dado que una cotización está en «Pendiente de Autorización del Cliente»
    Cuando el asesor la marca como presentada (al cliente o, si es flotilla, al Responsable de Flotilla)
    Entonces el sistema debe registrar la fecha y hora de presentación, a partir de la cual corre el plazo de 48 horas

  # ---------------------------------------------------------------- US-005 (Gerente de Taller)

  @US-005 @CA-007
  Escenario: CA-007 Cotización inicial mayor a $15,000 MXN
    Dado que el asesor guarda una cotización inicial con un total mayor a $15,000 MXN
    Cuando el sistema la genera
    Entonces debe asignarle el estado «Pendiente de Aprobación Gerencial»
    Y debe impedir que se marque como presentada
    Y debe enviar una alerta al panel del Gerente

  @US-005 @CA-008
  Escenario: CA-008 El Gerente aprueba la cotización
    Dado que la cotización está en «Pendiente de Aprobación Gerencial»
    Cuando el Gerente la revisa y la aprueba
    Entonces el sistema debe cambiar su estado a «Pendiente de Autorización del Cliente»
    Y debe registrar la fecha de aprobación
    Y debe notificar al asesor para que pueda presentarla

  @US-005 @CA-009
  Escenario: CA-009 El Gerente rechaza la cotización con observaciones
    Dado que la cotización está en «Pendiente de Aprobación Gerencial»
    Cuando el Gerente la rechaza capturando sus observaciones
    Entonces el sistema debe cambiar su estado a «Requiere Ajuste»
    Y debe notificar al asesor
    Cuando el asesor guarda la cotización ajustada
    Entonces su estado pasa a «Pendiente de Autorización del Cliente» sin volver a revisión gerencial

  # ---------------------------------------------------------------- US-023 (Asesor de Servicio)

  @US-023 @CA-040 @v3
  Escenario: CA-040 Alerta por cotización sin respuesta en 48 horas
    Dado que una cotización lleva más de 48 horas en «Pendiente de Autorización del Cliente» desde que se marcó como presentada (o desde el último recontacto)
    Cuando el sistema ejecuta su revisión
    Entonces debe generar una alerta en el panel del asesor
    Cuando el asesor registra el recontacto
    Entonces el sistema guarda la fecha y hora sin cambiar el estado de la cotización
    Y el plazo de 48 horas vuelve a contar desde ese recontacto

  # ---------------------------------------------------------------- US-026 (Asesor de Servicio)

  @US-026 @CA-047 @v3.1
  Escenario: CA-047 Corregir una cotización que espera la decisión del cliente
    Dado que una cotización está en «Pendiente de Autorización del Cliente» con un importe o una descripción mal capturados
    Cuando el asesor la corrige capturando los trabajos correctos y el motivo de la corrección
    Entonces el sistema debe guardar los trabajos corregidos conservando el número y la versión de la cotización
    Y debe guardar en el historial de correcciones al asesor, la fecha y hora, el motivo, el total anterior y el total nuevo
    Y si la cotización no requiere aprobación gerencial, debe dejarla en «Pendiente de Autorización del Cliente» como no presentada, para que el asesor la presente otra vez

  @US-026 @CA-048 @v3.1
  Escenario: CA-048 La corrección sube la cotización inicial arriba de $15,000 MXN
    Dado que una cotización inicial está en «Pendiente de Autorización del Cliente», aunque el Gerente ya la haya aprobado o se haya ajustado según sus observaciones
    Cuando el asesor la corrige y el total nuevo es mayor a $15,000 MXN
    Entonces el sistema debe cambiarla a «Pendiente de Aprobación Gerencial»
    Y debe borrar la fecha de aprobación gerencial, que queda guardada en el historial de la corrección
    Y debe enviar una alerta al panel del Gerente
    Y debe impedir que se presente al cliente hasta que el Gerente la apruebe

  @US-026 @CA-049 @v3.1
  Escenario: CA-049 Corregir una cotización que espera al Gerente
    Dado que una cotización está en «Pendiente de Aprobación Gerencial»
    Cuando el asesor la corrige capturando el motivo
    Entonces si el total nuevo sigue siendo mayor a $15,000 MXN, la cotización debe quedarse en «Pendiente de Aprobación Gerencial» con los trabajos corregidos
    Y si el total nuevo es menor o igual a $15,000 MXN, debe cambiarla a «Pendiente de Autorización del Cliente» como no presentada
    Y en los dos casos debe guardar la corrección en el historial

  @US-026 @CA-050 @v3.1
  Escenario: CA-050 No se corrige sin motivo ni una cotización por ajustar o ya decidida
    Dado que el asesor intenta corregir una cotización
    Cuando la cotización está en «Requiere Ajuste», «Autorizada», «Autorizada Parcialmente» o «Rechazada», o el asesor no captura el motivo
    Entonces el sistema no debe permitirlo
    Y si falta el motivo, debe pedir que lo capture
    Y si está en «Requiere Ajuste», debe indicar que se guarde la cotización ajustada según las observaciones del Gerente
    Y si ya tiene la decisión del cliente, debe indicar que ya no se corrige y que los trabajos nuevos se cotizan con una cotización adicional

  @US-026 @CA-051 @v3.1
  Escenario: CA-051 El plazo de 48 horas después de una corrección
    Dado que una cotización presentada, con recontactos registrados, se corrigió y quedó en «Pendiente de Autorización del Cliente»
    Cuando el sistema ejecuta su revisión de plazos antes de que el asesor la presente otra vez
    Entonces no debe generar la alerta de 48 horas
    Y debe conservar los recontactos anteriores como historial
    Cuando el asesor la presenta otra vez
    Entonces el plazo de 48 horas debe contar solo desde la nueva presentación y los recontactos posteriores a ella
