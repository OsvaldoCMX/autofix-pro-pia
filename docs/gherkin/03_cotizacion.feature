# language: es
@cotizacion
Característica: Cotización y aprobación gerencial
  Generar cotizaciones formales, aprobar las de alto monto y dar seguimiento a las que no tienen respuesta.

  User Stories de esta característica:
    US-004: Como Asesor de Servicio, quiero poder generar una cotización detallada a partir del diagnóstico del técnico y registrar cuándo se la presento al cliente, para entregarle un documento formal con el desglose de mano de obra, refacciones y costos.
    US-005: Como Gerente de Taller, quiero recibir una alerta y poder aprobar o rechazar con observaciones las cotizaciones iniciales cuyo total supere los $15,000 MXN, para asegurarme de que los trabajos costosos tengan una revisión especial antes de ser presentados al cliente.
    US-023: Como Asesor de Servicio, quiero recibir una alerta cuando una cotización presentada lleve más de 48 horas sin respuesta, para volver a contactar al cliente o al Responsable de Flotilla.

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
