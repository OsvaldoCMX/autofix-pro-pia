# language: es
@consultas
Característica: Consultas del gerente y del cliente
  Dar visibilidad del estado del taller al Gerente y del estado del vehículo al cliente.

  User Stories de esta característica:
    US-017: Como Gerente de Taller, quiero ver un listado de todas las órdenes abiertas y cerradas, para tener visibilidad del estado general del taller.
    US-018: Como Gerente de Taller, quiero ver el total de ingresos del día, para conocer el desempeño financiero diario del taller.
    US-021: Como Cliente, quiero consultar el estado de mi vehículo ingresando mi número de orden y mis placas, para saber cómo va el servicio sin tener que llamar al taller.

  # ---------------------------------------------------------------- US-017 (Gerente de Taller)

  @US-017 @CA-030
  Escenario: CA-030 Listado de órdenes abiertas y cerradas
    Dado que el Gerente inicia sesión en el sistema
    Cuando accede a la sección «Órdenes»
    Entonces debe visualizar un listado con todas las órdenes abiertas y cerradas, mostrando su estado actual

  # ---------------------------------------------------------------- US-018 (Gerente de Taller)

  @US-018 @CA-031
  Escenario: CA-031 Total de ingresos del día
    Dado que el Gerente inicia sesión en el sistema
    Cuando accede a la sección «Ingresos del día»
    Entonces debe visualizar el monto total de los pagos registrados en la fecha actual (sin incluir los cargos a crédito)

  # ---------------------------------------------------------------- US-021 (Cliente)

  @US-021 @CA-037
  Escenario: CA-037 Consulta de estado con datos correctos
    Dado que un cliente entra a la pantalla «Consulta tu vehículo»
    Cuando escribe su número de orden y sus placas y ambos coinciden
    Entonces el sistema debe mostrar el estado actual de la orden, la fecha de ingreso y la fecha de su última actualización
    Y no debe permitir modificar nada

  @US-021 @CA-038
  Escenario: CA-038 Consulta de estado con datos que no coinciden
    Dado que un cliente está en la pantalla «Consulta tu vehículo»
    Cuando el número de orden y las placas no coinciden con ninguna orden
    Entonces el sistema debe mostrar el mensaje «No se encontró una orden con esos datos» sin revelar ninguna información
