# language: es
@cancelacion
Característica: Cancelación de la orden
  Cerrar sin cobro la orden de un cliente que desiste antes de la cotización.

  User Stories de esta característica:
    US-025: Como Asesor de Servicio, quiero cancelar una orden cuando el cliente desiste del servicio antes de que se genere la cotización, para cerrar el expediente sin cobro y dejar registrado el motivo.

  # ---------------------------------------------------------------- US-025 (Asesor de Servicio)

  @US-025 @CA-044 @v3
  Escenario: CA-044 Cancelar la orden antes de la cotización
    Dado que una orden está en «Recibida» o «En Diagnóstico»
    Y el cliente decide no continuar con el servicio
    Cuando el asesor registra la cancelación indicando el motivo
    Entonces el sistema debe cambiar la orden a «Cancelada»
    Y debe guardar la fecha, la hora y el motivo
    Y debe quitarla del panel del técnico asignado, si tenía uno
    Y no debe generar ningún cobro

  @US-025 @CA-045 @v3
  Escenario: CA-045 No se cancela una orden que ya tiene cotización
    Dado que una orden ya tiene una cotización generada («Cotizada» o un estado posterior)
    Cuando el asesor intenta cancelarla
    Entonces el sistema no debe permitirlo
    Y debe indicar que una orden con cotización no se cancela: si el cliente no desea la reparación, se registra el rechazo total de la cotización
