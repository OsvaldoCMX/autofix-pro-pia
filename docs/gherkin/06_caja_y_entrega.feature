# language: es
@caja-y-entrega
Característica: Caja y entrega del vehículo
  Registrar el pago o el cargo a crédito, emitir el recibo y entregar el vehículo.

  User Stories de esta característica:
    US-014: Como Personal de Caja, quiero registrar el pago de una orden de cliente particular cuando está lista para entrega, para cerrar la parte administrativa del servicio.
    US-015: Como Personal de Caja, quiero generar un recibo interno de una orden pagada, para entregar al cliente un comprobante de pago sin necesidad de emitir facturas fiscales.
    US-022: Como Personal de Caja, quiero registrar un cargo a crédito de 15 días (contados desde la entrega del vehículo) para las órdenes de clientes de flotilla, para cerrar la parte administrativa del servicio sin cobrarle al conductor y dejar registrada la fecha en que la empresa debe pagar.
    US-024: Como Asesor de Servicio, quiero registrar la entrega del vehículo al cliente, para cerrar la orden de servicio y dejar constancia de cuándo salió el vehículo del taller.

  # ---------------------------------------------------------------- US-014 (Personal de Caja)

  @US-014 @CA-026
  Escenario: CA-026 Registrar el pago de contado
    Dado que una orden de cliente particular está en estado «Lista para Entrega»
    Cuando Caja registra el pago del total y la forma de pago (efectivo, tarjeta o transferencia)
    Entonces el sistema debe cambiar el estado de la orden a «Pagada»
    Y debe impedir que se modifiquen los costos

  @US-014 @CA-058 @v3.1
  Escenario: CA-058 Corregir la forma de pago antes de la entrega
    Dado que Caja registró el pago de una orden con la forma de pago equivocada y la orden sigue «Pagada»
    Cuando Caja corrige la forma de pago
    Entonces el sistema debe guardar la forma de pago correcta sin cambiar el monto, la fecha del pago ni el estado de la orden
    Y debe dejar constancia de la forma de pago anterior y de la nueva
    Y si el vehículo ya se entregó, no debe permitir el cambio

  # ---------------------------------------------------------------- US-015 (Personal de Caja)

  @US-015 @CA-027 @v3
  Escenario: CA-027 Generar el recibo interno
    Dado que la orden de servicio tiene un pago registrado (estado «Pagada», o «Cerrada» si ya se entregó el vehículo)
    Cuando Caja selecciona la opción «Generar recibo»
    Entonces el sistema debe generar un archivo PDF del recibo interno con su número, los datos de la orden y del cliente, el monto y la forma de pago

  # ---------------------------------------------------------------- US-022 (Personal de Caja)

  @US-022 @CA-039 @v3
  Escenario: CA-039 Registrar el cargo a crédito de una flotilla
    Dado que una orden de cliente de flotilla está en «Lista para Entrega»
    Cuando Caja registra el cargo a crédito
    Entonces el sistema debe cambiar la orden a «Por Cobrar (Crédito)»
    Y debe registrar el monto del cargo
    Y debe impedir que se modifiquen los costos
    Y la fecha de vencimiento queda pendiente hasta que se entregue el vehículo

  # ---------------------------------------------------------------- US-024 (Asesor de Servicio)

  @US-024 @CA-041 @v3
  Escenario: CA-041 Entregar el vehículo y cerrar la orden
    Dado que una orden está en «Pagada» o en «Por Cobrar (Crédito)»
    Cuando el asesor registra la entrega del vehículo
    Entonces el sistema debe cambiar la orden a «Cerrada»
    Y debe guardar la fecha y hora de entrega
    Y si la orden tiene cargo a crédito, debe registrar su fecha de vencimiento: 15 días naturales después de la entrega

  @US-024 @CA-042
  Escenario: CA-042 No se entrega sin pago ni cargo a crédito
    Dado que una orden no está en «Pagada» ni en «Por Cobrar (Crédito)»
    Cuando el asesor intenta registrar la entrega
    Entonces el sistema no debe permitirlo
    Y si la orden todavía puede cobrarse, debe indicar que primero debe registrarse el pago o el cargo a crédito
    Y si la orden está «Cancelada», «Cerrada» o «Cerrada sin Reparación», debe indicar esa situación sin pedir el pago

  @US-024 @CA-043
  Escenario: CA-043 Entregar el vehículo sin reparación
    Dado que el cliente rechazó toda la cotización
    Cuando el asesor selecciona «Entregar sin reparación»
    Entonces el sistema debe cambiar la orden a «Cerrada sin Reparación»
    Y debe guardar la fecha y hora de entrega
    Y no debe generar ningún cobro
