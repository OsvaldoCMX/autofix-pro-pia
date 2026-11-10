"""Fuente única de verdad para User Stories, criterios, Gherkin y matriz de trazabilidad (PIA v3.0).

Todo lo que se genera (user-stories.md, gherkin/*.feature, matriz-trazabilidad.md/.xlsx)
sale de estas estructuras, para que los conteos y los textos coincidan siempre.
"""

# ----------------------------------------------------------------------------- necesidades
NECESIDADES = [
    ("N-01", "Registrar digitalmente la recepción del vehículo incluyendo fotografías de daños visibles.", "Alta"),
    ("N-02", "Generar cotizaciones formales almacenadas con número, fecha, versión y estado.", "Alta"),
    ("N-03", "Registrar la decisión del cliente (autorización total, parcial o rechazo) antes de iniciar trabajos.", "Alta"),
    ("N-04", "Aplicar flujo de aprobación del Gerente para cotizaciones iniciales mayores a $15,000 MXN.", "Alta"),
    ("N-05", "Alertar automáticamente al asesor cuando una refacción tarde más de 3 días hábiles, para que notifique al cliente.", "Media"),
    ("N-06", "Generar cotizaciones adicionales para fallas descubiertas sin modificar la cotización original.", "Alta"),
    ("N-07", "Gestionar el proceso diferenciado para clientes de flotilla empresarial (autorización del responsable y crédito a 15 días desde la entrega).", "Media"),
    ("N-08", "Permitir al Gerente visualizar un listado de órdenes abiertas/cerradas y el total de ingresos del día.", "Media"),
    ("N-09", "(Implícita) Asignar técnicos y permitirles registrar el diagnóstico, ver sus trabajos y actualizar su estado.", "Alta"),
    ("N-10", "(Implícita) Controlar la solicitud y la llegada de refacciones con el área de Compras.", "Alta"),
    ("N-11", "(Implícita) Registrar el pago, emitir el recibo interno y registrar la entrega del vehículo.", "Alta"),
    ("N-12", "(Implícita) Permitir el retiro de vehículo en espera con generación de Nota de Responsabilidad.", "Media"),
    ("N-13", "Permitir al cliente consultar el estado de su vehículo sin llamar al taller.", "Media"),
    ("N-14", "(Implícita) Dar seguimiento a las cotizaciones que lleven más de 48 horas sin respuesta.", "Media"),
    ("N-15", "(Implícita, v3.0) Cancelar la orden cuando el cliente desiste antes de que se genere la cotización.", "Media"),
    ("N-16", "(Implícita, v3.1) Corregir los datos mal capturados dejando constancia y evitar registros repetidos (revisión del 09/11/2026).", "Alta"),
]

# necesidad -> (US, CA, proceso BPMN)
TRAZA_NECESIDAD = {
    "N-01": (["US-001", "US-002", "US-003"], ["CA-001", "CA-002", "CA-003", "CA-004", "CA-052", "CA-059"], "Fase 1: Recepción y registro"),
    "N-02": (["US-004"], ["CA-005", "CA-006", "CA-060"], "Fase 2: Diagnóstico y cotización; Fase 3: Autorización"),
    "N-03": (["US-006"], ["CA-010", "CA-011", "CA-012", "CA-063"], "Fase 3: Autorización"),
    "N-04": (["US-005"], ["CA-007", "CA-008", "CA-009"], "Fase 2: Diagnóstico y cotización"),
    "N-05": (["US-012"], ["CA-023"], "Fase 4: Gestión de refacciones"),
    "N-06": (["US-009", "US-019"], ["CA-016", "CA-017", "CA-018", "CA-034", "CA-061"], "Fase 5: Reparación y ampliación"),
    "N-07": (["US-016", "US-022"], ["CA-028", "CA-029", "CA-039", "CA-041", "CA-064", "CA-065"], "Fase 1, Fase 3 y Fase 6: Cierre, pago y entrega"),
    "N-08": (["US-017", "US-018"], ["CA-030", "CA-031"], "Consulta transversal (no es una tarea del flujo)"),
    "N-09": (["US-007", "US-008", "US-019", "US-020"], ["CA-013", "CA-014", "CA-015", "CA-032", "CA-033", "CA-035", "CA-036", "CA-046", "CA-053", "CA-054"], "Fase 1, Fase 2 y Fase 5"),
    "N-10": (["US-010", "US-011"], ["CA-019", "CA-020", "CA-021", "CA-022", "CA-062"], "Fase 4: Gestión de refacciones"),
    "N-11": (["US-014", "US-015", "US-024"], ["CA-026", "CA-027", "CA-041", "CA-042", "CA-043", "CA-058"],
             "Fase 6: Cierre, pago y entrega (y Fase 3 para la entrega sin reparación)"),
    "N-12": (["US-013"], ["CA-024", "CA-025"], "Diagrama 2 (Casos especiales): Retiro anticipado"),
    "N-13": (["US-021"], ["CA-037", "CA-038"], "Consulta transversal (no es una tarea del flujo)"),
    "N-14": (["US-023"], ["CA-040"], "Fase 3: Autorización (temporizador de 48 h)"),
    "N-15": (["US-025"], ["CA-044", "CA-045"], "Diagrama 2 (Casos especiales): Cliente desiste antes de la cotización"),
    "N-16": (["US-026", "US-020", "US-027", "US-014"], ["CA-047", "CA-048", "CA-049", "CA-050", "CA-051", "CA-054", "CA-055", "CA-056", "CA-057", "CA-058", "CA-066"],
             "Fase 2 y Fase 3: corrección de la cotización (v3.1)"),
}

# ----------------------------------------------------------------------------- user stories
US = {
    "US-001": ("Asesor de Servicio", "Como Asesor de Servicio, quiero poder registrar un vehículo nuevo en el sistema, para tener un expediente digital completo del cliente y su vehículo, evitando errores de captura y pérdida de papeles."),
    "US-002": ("Asesor de Servicio", "Como Asesor de Servicio, quiero poder capturar el kilometraje, nivel de combustible y tomar fotos de los daños visibles del vehículo al momento de la recepción, para tener evidencia del estado en el que ingresó el vehículo y evitar futuras disputas con el cliente."),
    "US-003": ("Asesor de Servicio", "Como Asesor de Servicio, quiero buscar un vehículo por su número de placas al inicio del registro, para recuperar automáticamente la información del cliente y vehículo si ya es un cliente recurrente, y así agilizar el proceso de recepción."),
    "US-004": ("Asesor de Servicio", "Como Asesor de Servicio, quiero poder generar una cotización detallada a partir del diagnóstico del técnico y registrar cuándo se la presento al cliente, para entregarle un documento formal con el desglose de mano de obra, refacciones y costos."),
    "US-005": ("Gerente de Taller", "Como Gerente de Taller, quiero recibir una alerta y poder aprobar o rechazar con observaciones las cotizaciones iniciales cuyo total supere los $15,000 MXN, para asegurarme de que los trabajos costosos tengan una revisión especial antes de ser presentados al cliente."),
    "US-006": ("Asesor de Servicio", "Como Asesor de Servicio, quiero registrar la decisión del cliente cuando autoriza total o parcialmente, o rechaza una cotización, para tener evidencia formal de lo que se acordó y poder iniciar solo los trabajos autorizados, evitando disputas posteriores."),
    "US-007": ("Técnico", "Como Técnico, quiero ver en mi panel las órdenes de servicio y trabajos que me han sido asignados, ordenados según la fila de trabajo, para organizar mi jornada y saber exactamente en qué vehículo debo trabajar primero."),
    "US-008": ("Técnico", "Como Técnico, quiero poder actualizar el estado de los trabajos de una orden a «En Progreso» o «Completado», para que el sistema refleje el estado actual de la reparación y el Asesor pueda informar al cliente."),
    "US-009": ("Asesor de Servicio", "Como Asesor de Servicio, quiero poder crear una cotización adicional si durante la reparación se descubren nuevas fallas, para obtener la autorización del cliente para los trabajos extra sin modificar la cotización original, manteniendo un historial claro."),
    "US-010": ("Técnico", "Como Técnico, quiero poder marcar una refacción de un trabajo autorizado como «No disponible» y generar una solicitud de compra desde la orden de servicio, para que el área de Compras sepa qué pieza se necesita y pueda gestionar su adquisición."),
    "US-011": ("Personal de Compras", "Como Personal de Compras, quiero ver una lista de todas las solicitudes de refacciones pendientes, para gestionar su compra con proveedores y registrar en el sistema su llegada al taller."),
    "US-012": ("Asesor de Servicio", "Como Asesor de Servicio, quiero recibir una alerta automática en el sistema si una refacción solicitada tarda más de 3 días hábiles en llegar, para poder contactar proactivamente al cliente y comunicarle el retraso, mejorando la comunicación y la confianza."),
    "US-013": ("Asesor de Servicio", "Como Asesor de Servicio, quiero registrar la salida de un vehículo cuya orden está en espera de refacciones, generando la Nota de Responsabilidad, para permitir que el cliente use su vehículo y dejar constancia formal de que lo retiró sin que la reparación estuviera terminada."),
    "US-014": ("Personal de Caja", "Como Personal de Caja, quiero registrar el pago de una orden de cliente particular cuando está lista para entrega, para cerrar la parte administrativa del servicio."),
    "US-015": ("Personal de Caja", "Como Personal de Caja, quiero generar un recibo interno de una orden pagada, para entregar al cliente un comprobante de pago sin necesidad de emitir facturas fiscales."),
    "US-016": ("Asesor de Servicio", "Como Asesor de Servicio, quiero registrar a un cliente como tipo «Flotilla», vinculado a su empresa y a su Responsable de Flotilla, para que las decisiones sobre las cotizaciones se registren a nombre del responsable y no del conductor."),
    "US-017": ("Gerente de Taller", "Como Gerente de Taller, quiero ver un listado de todas las órdenes abiertas y cerradas, para tener visibilidad del estado general del taller."),
    "US-018": ("Gerente de Taller", "Como Gerente de Taller, quiero ver el total de ingresos del día, para conocer el desempeño financiero diario del taller."),
    "US-019": ("Técnico", "Como Técnico, quiero registrar el diagnóstico de la orden que me fue asignada y reportar las fallas adicionales que encuentre durante la reparación, para que el asesor pueda generar las cotizaciones con información técnica completa."),
    "US-020": ("Asesor de Servicio", "Como Asesor de Servicio, quiero asignar un técnico a cada orden, tanto para el diagnóstico como para los trabajos autorizados, para que cada técnico sepa qué vehículos debe atender."),
    "US-021": ("Cliente", "Como Cliente, quiero consultar el estado de mi vehículo ingresando mi número de orden y mis placas, para saber cómo va el servicio sin tener que llamar al taller."),
    "US-022": ("Personal de Caja", "Como Personal de Caja, quiero registrar un cargo a crédito de 15 días (contados desde la entrega del vehículo) para las órdenes de clientes de flotilla, para cerrar la parte administrativa del servicio sin cobrarle al conductor y dejar registrada la fecha en que la empresa debe pagar."),
    "US-023": ("Asesor de Servicio", "Como Asesor de Servicio, quiero recibir una alerta cuando una cotización presentada lleve más de 48 horas sin respuesta, para volver a contactar al cliente o al Responsable de Flotilla."),
    "US-024": ("Asesor de Servicio", "Como Asesor de Servicio, quiero registrar la entrega del vehículo al cliente, para cerrar la orden de servicio y dejar constancia de cuándo salió el vehículo del taller."),
    "US-025": ("Asesor de Servicio", "Como Asesor de Servicio, quiero cancelar una orden cuando el cliente desiste del servicio antes de que se genere la cotización, para cerrar el expediente sin cobro y dejar registrado el motivo."),
    "US-026": ("Asesor de Servicio", "Como Asesor de Servicio, quiero corregir una cotización con un importe o una descripción mal capturados mientras espera la revisión del Gerente o la decisión del cliente, indicando el motivo, para presentar un documento correcto sin perder el historial de lo que cambió."),
    "US-027": ("Asesor de Servicio", "Como Asesor de Servicio, quiero corregir los datos del cliente, del vehículo y del estado de recepción que capturé mal, para que el expediente quede correcto sin tener que abrir otra orden."),
}

# ----------------------------------------------------------------------------- criterios
# Cada criterio: pasos Gherkin (palabra clave, texto) + datos de trazabilidad.
#   bpmn: fase del BPMN · reglas: RN-xx · dominio: componentes del dominio (aggregate, spec,
#   máquina de estados, evento) · servicio: caso de uso · ruta: endpoint · rol · prioridad:
#   P1 = se implementa en el PIA; P2 = se implementa si el tiempo lo permite (PDF/fotos)
#   cambio: hallazgo que modificó el criterio en v3.0 (None = sin cambios desde U2/U3)
#   planeado: aprobado en la Fase 13 y todavía sin construir; la Fase 14 quita la marca al
#   construirlo (tests/test_trazabilidad.py exige que un criterio planeado aún no tenga prueba)
D, C, E, Y = "Dado", "Cuando", "Entonces", "Y"
PLANEADO = "Planeado"

CA = {}


def ca(id_, us, pasos, bpmn, reglas, dominio, servicio, ruta, rol, prioridad="P1", cambio=None, nombre=None,
       planeado=False):
    CA[id_] = dict(id=id_, us=us, pasos=pasos, bpmn=bpmn, reglas=reglas, dominio=dominio,
                   servicio=servicio, ruta=ruta, rol=rol, prioridad=prioridad, cambio=cambio,
                   nombre=nombre, planeado=planeado)


def prioridad_de(c):
    return f"{c['prioridad']} · {PLANEADO}" if c["planeado"] else c["prioridad"]


F1, F2, F3, F4, F5, F6 = ("Fase 1: Recepción y registro", "Fase 2: Diagnóstico y cotización",
                          "Fase 3: Autorización", "Fase 4: Gestión de refacciones",
                          "Fase 5: Reparación y ampliación", "Fase 6: Cierre, pago y entrega")
DG2R = "Diagrama 2: Retiro anticipado"
DG2C = "Diagrama 2: Cliente desiste antes de la cotización"
TRANS = "Consulta transversal"
ASE, TEC, GER, COM, CAJ, PUB, SIS = ("Asesor", "Técnico", "Gerente", "Compras", "Caja",
                                     "Público (sin token)", "Sistema (token de sistema)")

ca("CA-001", "US-001", [
    (D, "que un vehículo llega al taller y el asesor abre la pantalla «Nueva Orden»"),
    (C, "el asesor ingresa los datos del cliente (nombre, teléfono y correo), los del vehículo (marca, modelo, año, placas y VIN) y el motivo de ingreso"),
    (E, "el sistema debe guardar la información"),
    (Y, "debe generar un número de orden de servicio único"),
    (Y, "debe asignarle el estado «Recibida»"),
    (Y, "debe mostrar un mensaje de éxito"),
], F1, ["RN-01", "RN-22"], "Cliente, Vehiculo, OrdenDeServicio (MAQUINA_DE_ORDEN), evento OrdenRecibida",
   "ServicioDeRecepcion.registrar_orden", "POST /api/ordenes", ASE,
   nombre="Registrar un vehículo nuevo y abrir su orden")

ca("CA-002", "US-002", [
    (D, "que el asesor está en la pantalla de registro de un vehículo"),
    (C, "ingresa el kilometraje, selecciona el nivel de combustible y adjunta las fotos de los daños"),
    (E, "el sistema debe almacenar estos datos y fotos como parte del expediente de la orden de servicio"),
], F1, ["RN-23"], "OrdenDeServicio, EstadoDeRecepcion (kilometraje, nivel de combustible, fotos)",
   "ServicioDeRecepcion.registrar_orden / adjuntar_foto", "POST /api/ordenes · POST /api/ordenes/{numero}/fotos",
   ASE, prioridad="P1 (datos) · P2 (fotos)", nombre="Capturar el estado de ingreso y las fotos de daños")

ca("CA-003", "US-003", [
    (D, "que el asesor está en la pantalla de inicio de una nueva orden"),
    (C, "escribe el número de placas"),
    (Y, "el sistema encuentra un registro previo"),
    (E, "el sistema debe mostrar los datos precargados del cliente y el vehículo"),
    (Y, "el asesor solo debe confirmarlos o actualizarlos"),
], F1, ["RN-01"], "Vehiculo, Cliente, Placas (VO)", "Consulta BuscarVehiculoPorPlacas",
   "GET /api/vehiculos/{placas}", ASE, nombre="Encontrar un cliente recurrente por sus placas")

ca("CA-004", "US-003", [
    (D, "que el asesor ingresa un número de placas que no existe en el sistema"),
    (C, "el sistema no encuentra el vehículo"),
    (E, "debe habilitar la opción para crear un nuevo registro desde cero"),
], F1, ["RN-01"], "Vehiculo, Placas (VO)", "Consulta BuscarVehiculoPorPlacas",
   "GET /api/vehiculos/{placas} (404) → POST /api/ordenes", ASE, nombre="Placas no registradas")

ca("CA-005", "US-004", [
    (D, "que la orden tiene un diagnóstico registrado por el técnico"),
    (C, "el asesor agrega los trabajos (mano de obra) y las refacciones con sus costos y guarda la cotización"),
    (E, "el sistema debe generarla con número único, versión 1, fecha, desglose y costo total"),
    (Y, "debe generar su PDF"),
    (Y, "debe cambiar la orden a «Cotizada»"),
    (Y, "si el total es menor o igual a $15,000 MXN, debe asignar a la cotización el estado «Pendiente de Autorización del Cliente»"),
], F2, ["RN-02", "RN-04", "RN-23", "RN-22"],
   "Cotizacion, LineaDeCotizacion, Dinero, VersionCotizacion, spec RequiereAprobacionGerencial, MAQUINA_DE_COTIZACION, OrdenDeServicio, evento CotizacionGenerada",
   "ServicioDeCotizacion.generar_inicial", "POST /api/ordenes/{numero}/cotizaciones · GET /api/cotizaciones/{id}/pdf",
   ASE, prioridad="P1 (cotización) · P2 (PDF)", nombre="Generar la cotización inicial")

ca("CA-006", "US-004", [
    (D, "que una cotización está en «Pendiente de Autorización del Cliente»"),
    (C, "el asesor la marca como presentada (al cliente o, si es flotilla, al Responsable de Flotilla)"),
    (E, "el sistema debe registrar la fecha y hora de presentación, a partir de la cual corre el plazo de 48 horas"),
], F3, ["RN-06", "RN-12"], "Cotizacion (MAQUINA_DE_COTIZACION), evento CotizacionPresentada",
   "ServicioDeCotizacion.presentar", "POST /api/cotizaciones/{id}/presentacion", ASE,
   nombre="Marcar la cotización como presentada")

ca("CA-007", "US-005", [
    (D, "que el asesor guarda una cotización inicial con un total mayor a $15,000 MXN"),
    (C, "el sistema la genera"),
    (E, "debe asignarle el estado «Pendiente de Aprobación Gerencial»"),
    (Y, "debe impedir que se marque como presentada"),
    (Y, "debe enviar una alerta al panel del Gerente"),
], F2, ["RN-04", "RN-06"],
   "spec RequiereAprobacionGerencial (EsCotizacionInicial AND TotalMayorAlUmbral), Cotizacion, evento AprobacionGerencialRequerida → AlertaInterna",
   "ServicioDeCotizacion.generar_inicial · Consulta ListarCotizacionesPendientesDeAprobacion",
   "POST /api/ordenes/{numero}/cotizaciones · GET /api/gerencia/cotizaciones-por-aprobar · GET /api/alertas",
   f"{ASE} / {GER}", nombre="Cotización inicial mayor a $15,000 MXN")

ca("CA-008", "US-005", [
    (D, "que la cotización está en «Pendiente de Aprobación Gerencial»"),
    (C, "el Gerente la revisa y la aprueba"),
    (E, "el sistema debe cambiar su estado a «Pendiente de Autorización del Cliente»"),
    (Y, "debe registrar la fecha de aprobación"),
    (Y, "debe notificar al asesor para que pueda presentarla"),
], F2, ["RN-04", "RN-22"], "Cotizacion (fecha_aprobacion_gerencial), evento CotizacionAprobadaPorGerente → AlertaInterna",
   "ServicioDeAprobacionGerencial.revisar", "POST /api/cotizaciones/{id}/revision-gerencial", GER,
   cambio="H-PIA-08", nombre="El Gerente aprueba la cotización")

ca("CA-009", "US-005", [
    (D, "que la cotización está en «Pendiente de Aprobación Gerencial»"),
    (C, "el Gerente la rechaza capturando sus observaciones"),
    (E, "el sistema debe cambiar su estado a «Requiere Ajuste»"),
    (Y, "debe notificar al asesor"),
    (C, "el asesor guarda la cotización ajustada"),
    (E, "su estado pasa a «Pendiente de Autorización del Cliente» sin volver a revisión gerencial"),
], F2, ["RN-05", "RN-22"], "Cotizacion (ajustar), evento CotizacionRechazadaPorGerente → AlertaInterna",
   "ServicioDeAprobacionGerencial.revisar · ServicioDeCotizacion.ajustar",
   "POST /api/cotizaciones/{id}/revision-gerencial · PUT /api/cotizaciones/{id}/lineas", f"{GER} / {ASE}",
   nombre="El Gerente rechaza la cotización con observaciones")

ca("CA-010", "US-006", [
    (D, "que el cliente (o el Responsable de Flotilla) revisó la cotización"),
    (C, "el asesor selecciona los trabajos autorizados y guarda la decisión"),
    (E, "el sistema debe cambiar la cotización a «Autorizada» o «Autorizada Parcialmente»"),
    (Y, "debe cambiar la orden a «Autorizada»"),
    (Y, "debe registrar la fecha, la hora y el nombre de quien autorizó"),
    (Y, "debe marcar los trabajos no aceptados como «No Autorizado»"),
], F3, ["RN-07", "RN-08", "RN-22"],
   "Cotizacion, DecisionDelCliente, Autorizante, spec AutorizanteValido, OrdenDeServicio, eventos CotizacionAutorizada y OrdenAutorizada",
   "ServicioDeAutorizacion.registrar_decision", "POST /api/cotizaciones/{id}/decision", ASE,
   nombre="Registrar la autorización total o parcial")

ca("CA-011", "US-006", [
    (D, "que el cliente autorizó parcialmente la cotización"),
    (C, "el asesor asigna los trabajos a un técnico"),
    (E, "el sistema solo debe permitir seleccionar los trabajos autorizados"),
], F5, ["RN-08"], "OrdenDeServicio, Trabajo (MAQUINA_DE_TRABAJO), evento TrabajosAsignados",
   "ServicioDeReparacion.asignar_trabajos", "POST /api/ordenes/{numero}/asignacion-trabajos", ASE,
   nombre="Solo se asignan los trabajos autorizados")

ca("CA-012", "US-006", [
    (D, "que el cliente no acepta ningún trabajo de la cotización"),
    (C, "el asesor registra el rechazo total"),
    (E, "el sistema debe cambiar la cotización a «Rechazada»"),
    (Y, "debe impedir la asignación de trabajos"),
    (Y, "debe habilitar la opción «Entregar sin reparación»"),
], F3, ["RN-08", "RN-18"], "Cotizacion, OrdenDeServicio (rechazo_total), evento CotizacionRechazadaPorCliente",
   "ServicioDeAutorizacion.registrar_decision", "POST /api/cotizaciones/{id}/decision", ASE,
   nombre="Registrar el rechazo total")

ca("CA-013", "US-007", [
    (D, "que un técnico inicia sesión en el sistema"),
    (C, "accede a su panel de trabajo"),
    (E, "debe visualizar la lista de órdenes y trabajos que le han sido asignados, ordenada según la fila de trabajo (de la fecha de ingreso a la fila más antigua a la más reciente)"),
], F5, ["RN-14"], "Modelo de lectura PanelDelTecnico (fecha_ingreso_a_fila)", "Consulta ConsultarPanelDelTecnico",
   "GET /api/tecnicos/me/panel", TEC, nombre="Panel del técnico ordenado por la fila de trabajo")

ca("CA-014", "US-008", [
    (D, "que un técnico tiene un trabajo asignado en estado «Pendiente»"),
    (C, "lo actualiza a «En Progreso»"),
    (E, "el sistema debe registrar el cambio"),
    (Y, "si la orden estaba en «Autorizada», debe cambiarla a «En Reparación»"),
], F5, ["RN-14", "RN-22"], "spec PuedeIniciarTrabajo, Trabajo y OrdenDeServicio (máquinas de estados), evento TrabajoIniciado",
   "ServicioDeReparacion.iniciar_trabajo", "POST /api/ordenes/{numero}/trabajos/{id}/inicio", TEC,
   nombre="Iniciar un trabajo")

ca("CA-015", "US-008", [
    (D, "que un técnico está trabajando en una orden asignada"),
    (C, "actualiza un trabajo a «Completado»"),
    (Y, "todos los trabajos autorizados de la orden quedan completados"),
    (Y, "no hay una cotización adicional esperando la decisión del cliente"),
    (E, "el sistema debe cambiar el estado de la orden a «Lista para Entrega»"),
    (Y, "debe notificar al asesor"),
], F5, ["RN-15", "RN-22"], "Trabajo, OrdenDeServicio, evento OrdenListaParaEntrega → AlertaInterna",
   "ServicioDeReparacion.completar_trabajo", "POST /api/ordenes/{numero}/trabajos/{id}/completado", TEC,
   cambio="H-PIA-12", nombre="Completar el último trabajo autorizado")

ca("CA-016", "US-009", [
    (D, "que el técnico reportó una falla adicional en una orden «En Reparación»"),
    (C, "el asesor crea una nueva cotización vinculada a esa orden"),
    (E, "el sistema debe etiquetarla como «Cotización Adicional»"),
    (Y, "debe asignarle la siguiente versión (v.2, v.3…)"),
    (Y, "debe dejarla en «Pendiente de Autorización del Cliente» sin importar su monto"),
    (Y, "debe mantener sin cambios la cotización original"),
], F5, ["RN-24", "RN-04"], "Cotizacion (TipoCotizacion.ADICIONAL), VersionCotizacion, spec RequiereAprobacionGerencial (no aplica)",
   "ServicioDeCotizacion.generar_adicional", "POST /api/ordenes/{numero}/cotizaciones-adicionales", ASE,
   nombre="Crear una cotización adicional")

ca("CA-017", "US-009", [
    (D, "que el cliente autoriza la cotización adicional"),
    (C, "el asesor registra la decisión"),
    (E, "los trabajos adicionales se agregan a la orden en estado «Pendiente»"),
    (Y, "el sistema debe notificar al técnico"),
], F5, ["RN-07", "RN-08"], "Cotizacion, OrdenDeServicio (aplicar_decision), evento CotizacionAutorizada → AlertaInterna",
   "ServicioDeAutorizacion.registrar_decision", "POST /api/cotizaciones/{id}/decision", ASE,
   nombre="El cliente autoriza la cotización adicional")

ca("CA-018", "US-009", [
    (D, "que el cliente rechaza la cotización adicional"),
    (C, "el asesor registra la decisión"),
    (E, "el sistema debe marcar los trabajos adicionales como «No Autorizado»"),
    (Y, "la orden continúa solo con los trabajos autorizados originalmente"),
    (Y, "si esos trabajos ya estaban completados, la orden pasa a «Lista para Entrega»"),
], F5, ["RN-08", "RN-15"], "Cotizacion, OrdenDeServicio, Trabajo (No Autorizado), evento OrdenListaParaEntrega",
   "ServicioDeAutorizacion.registrar_decision", "POST /api/cotizaciones/{id}/decision", ASE,
   cambio="H-PIA-12", nombre="El cliente rechaza la cotización adicional")

ca("CA-019", "US-010", [
    (D, "que el técnico verificó en el almacén que una refacción de un trabajo autorizado no está disponible"),
    (C, "la marca como «No disponible» y captura la descripción y la cantidad"),
    (E, "el sistema debe crear una «Solicitud de Compra» en estado «Solicitada» con su fecha"),
    (Y, "debe mostrarla en la lista de Compras"),
    (Y, "debe cambiar la orden a «En Espera de Refacción»"),
], F4, ["RN-09", "RN-10", "RN-23", "RN-22"],
   "spec PuedeSolicitarRefaccion, SolicitudDeCompra (MAQUINA_DE_SOLICITUD), OrdenDeServicio, evento SolicitudDeCompraCreada",
   "ServicioDeRefacciones.solicitar", "POST /api/ordenes/{numero}/solicitudes-de-compra", TEC,
   nombre="Solicitar una refacción no disponible")

ca("CA-020", "US-010", [
    (D, "que un trabajo no ha sido autorizado por el cliente"),
    (C, "el técnico intenta crear una solicitud de compra para ese trabajo"),
    (E, "el sistema no debe permitirlo"),
], F4, ["RN-09"], "spec PuedeSolicitarRefaccion (TrabajoAutorizado), error TrabajoNoAutorizado",
   "ServicioDeRefacciones.solicitar", "POST /api/ordenes/{numero}/solicitudes-de-compra (409)", TEC,
   nombre="No se piden refacciones de trabajos no autorizados")

ca("CA-021", "US-011", [
    (D, "que el Personal de Compras inicia sesión"),
    (C, "accede a «Solicitudes pendientes»"),
    (E, "debe visualizar todas las solicitudes en estado «Solicitada» con número de orden, refacción, cantidad, fecha de solicitud y días hábiles transcurridos"),
], F4, ["RN-11"], "Modelo de lectura SolicitudPendienteVista, CalendarioHabil", "Consulta ListarSolicitudesPendientes",
   "GET /api/compras/solicitudes-pendientes", COM, nombre="Lista de solicitudes pendientes")

ca("CA-022", "US-011", [
    (D, "que una refacción solicitada llegó al taller"),
    (C, "Compras registra su llegada"),
    (E, "el sistema debe cambiar la solicitud a «Disponible»"),
    (Y, "debe notificar al técnico y al asesor"),
    (Y, "si la orden ya no tiene solicitudes pendientes, debe regresarla al estado que tenía antes de la espera («Autorizada» o «En Reparación»; si durante la espera se inició algún trabajo, a «En Reparación»)"),
], F4, ["RN-10", "RN-22"], "SolicitudDeCompra, OrdenDeServicio (MAQUINA_DE_ORDEN), evento RefaccionDisponible → AlertaInterna",
   "ServicioDeRefacciones.registrar_llegada", "POST /api/ordenes/{numero}/solicitudes-de-compra/{id}/llegada", COM,
   cambio="H-PIA-07", nombre="Registrar la llegada de la refacción")

ca("CA-023", "US-012", [
    (D, "que una solicitud de compra lleva más de 3 días hábiles en estado «Solicitada»"),
    (C, "el sistema ejecuta su revisión diaria"),
    (E, "debe generar una alerta en el panel del asesor responsable de la orden"),
    (C, "el asesor avisa al cliente y lo registra"),
    (E, "el sistema guarda la fecha y hora de la notificación"),
    (Y, "no vuelve a generar la alerta para esa solicitud"),
], F4, ["RN-11"], "spec RequiereAlertaDeRefaccion (SolicitudPendiente AND MasDeDiasHabiles(3) AND NOT ClienteYaAvisado), CalendarioHabil, AlertaInterna",
   "ServicioDeRevisionDePlazos.revisar · ServicioDeRefacciones.registrar_aviso_al_cliente",
   "POST /api/revisiones/plazos · POST /api/ordenes/{numero}/solicitudes-de-compra/{id}/aviso-al-cliente",
   f"{SIS} / {ASE}", cambio="H-PIA-10", nombre="Alerta por refacción con más de 3 días hábiles")

ca("CA-024", "US-013", [
    (D, "que una orden está en «En Espera de Refacción» y el cliente desea retirar su vehículo"),
    (C, "el asesor registra la salida"),
    (E, "el sistema debe generar el PDF de la «Nota de Responsabilidad» para imprimirla"),
    (C, "el asesor marca que el cliente la firmó"),
    (E, "la orden pasa a «Pausada por Retiro de Vehículo»"),
    (Y, "sale de la fila de trabajo"),
], DG2R, ["RN-13", "RN-22"], "OrdenDeServicio (registrar_salida, confirmar_firma_de_nota), NotaDeResponsabilidad, evento VehiculoRetirado",
   "ServicioDeRetiro.registrar_salida / confirmar_firma",
   "POST /api/ordenes/{numero}/retiro · GET /api/ordenes/{numero}/nota-de-responsabilidad/pdf · POST /api/ordenes/{numero}/retiro/firma",
   ASE, prioridad="P1 (estados) · P2 (PDF)", nombre="Retiro anticipado con Nota de Responsabilidad")

ca("CA-025", "US-013", [
    (D, "que una orden está en «Pausada por Retiro de Vehículo»"),
    (C, "el cliente regresa con el vehículo y el asesor reactiva la orden"),
    (E, "el sistema debe regresarla a «En Espera de Refacción» si aún falta alguna refacción o, si ya están todas, a «Autorizada» (ningún trabajo iniciado) o a «En Reparación» (algún trabajo ya iniciado)"),
    (Y, "debe asignarle una nueva fecha de ingreso a la fila, de modo que quede al final"),
], DG2R, ["RN-13", "RN-22"], "OrdenDeServicio (reactivar, fecha_ingreso_a_fila), evento OrdenReactivada",
   "ServicioDeRetiro.reactivar", "POST /api/ordenes/{numero}/reactivacion", ASE,
   cambio="H-PIA-07", nombre="Reactivar la orden al final de la fila")

ca("CA-026", "US-014", [
    (D, "que una orden de cliente particular está en estado «Lista para Entrega»"),
    (C, "Caja registra el pago del total y la forma de pago (efectivo, tarjeta o transferencia)"),
    (E, "el sistema debe cambiar el estado de la orden a «Pagada»"),
    (Y, "debe impedir que se modifiquen los costos"),
], F6, ["RN-16", "RN-22"], "OrdenDeServicio, Pago, FormaDePago, Dinero, evento PagoRegistrado",
   "ServicioDeCaja.registrar_pago", "POST /api/ordenes/{numero}/pago", CAJ, nombre="Registrar el pago de contado")

ca("CA-027", "US-015", [
    (D, "que la orden de servicio tiene un pago registrado (estado «Pagada», o «Cerrada» si ya se entregó el vehículo)"),
    (C, "Caja selecciona la opción «Generar recibo»"),
    (E, "el sistema debe generar un archivo PDF del recibo interno con su número, los datos de la orden y del cliente, el monto y la forma de pago"),
], F6, ["RN-16"], "OrdenDeServicio (pago), ReciboInterno", "ServicioDeCaja.generar_recibo",
   "GET /api/ordenes/{numero}/recibo/pdf", CAJ, prioridad="P2", cambio="H-PIA-11",
   nombre="Generar el recibo interno")

ca("CA-028", "US-016", [
    (D, "que el asesor registra una orden para un vehículo de empresa"),
    (C, "selecciona el tipo de cliente «Flotilla»"),
    (E, "el sistema debe pedir la empresa"),
    (Y, "debe mostrar los datos de su Responsable de Flotilla (nombre, teléfono y correo)"),
    (Y, "debe permitir registrarlos si la empresa es nueva"),
], F1, ["RN-07"], "Cliente (TipoCliente.FLOTILLA), ResponsableDeFlotilla", "ServicioDeRecepcion.registrar_cliente · Consulta BuscarClientes",
   "GET /api/clientes?tipo=Flotilla&empresa= · POST /api/clientes", ASE, nombre="Registrar un cliente de flotilla")

ca("CA-029", "US-016", [
    (D, "que la orden es de un cliente de flotilla"),
    (C, "el asesor registra la decisión sobre una cotización (inicial o adicional)"),
    (E, "el sistema debe registrarla a nombre del Responsable de Flotilla"),
    (Y, "no debe permitir registrar al conductor como autorizante"),
], F3, ["RN-07"], "spec AutorizanteValido ((EsParticular AND AutorizaElCliente) OR (EsFlotilla AND AutorizaSuResponsable)), VerificadorDeAutorizante",
   "ServicioDeAutorizacion.registrar_decision", "POST /api/cotizaciones/{id}/decision (409)", ASE,
   nombre="En flotillas solo autoriza el Responsable de Flotilla")

ca("CA-030", "US-017", [
    (D, "que el Gerente inicia sesión en el sistema"),
    (C, "accede a la sección «Órdenes»"),
    (E, "debe visualizar un listado con todas las órdenes abiertas y cerradas, mostrando su estado actual"),
], TRANS, ["RN-22"], "Modelo de lectura OrdenResumenVista", "Consulta ListarOrdenes", "GET /api/gerencia/ordenes", GER,
   nombre="Listado de órdenes abiertas y cerradas")

ca("CA-031", "US-018", [
    (D, "que el Gerente inicia sesión en el sistema"),
    (C, "accede a la sección «Ingresos del día»"),
    (E, "debe visualizar el monto total de los pagos registrados en la fecha actual (sin incluir los cargos a crédito)"),
], TRANS, ["RN-21"], "Pago, Dinero (suma con Decimal)", "Consulta ConsultarIngresosDelDia", "GET /api/gerencia/ingresos-del-dia", GER,
   nombre="Total de ingresos del día")

ca("CA-032", "US-019", [
    (D, "que una orden está en «En Diagnóstico» y asignada a un técnico"),
    (C, "el técnico registra las fallas encontradas y los trabajos y refacciones recomendados"),
    (E, "el sistema debe guardar el diagnóstico con fecha y hora"),
    (Y, "debe notificar al asesor que la orden está lista para cotizar"),
], F2, ["RN-02"], "OrdenDeServicio, Diagnostico (VO), evento DiagnosticoRegistrado → AlertaInterna",
   "ServicioDeDiagnostico.registrar_diagnostico", "POST /api/ordenes/{numero}/diagnostico", TEC,
   cambio="H-PIA-05", nombre="Registrar el diagnóstico")

ca("CA-033", "US-019", [
    (D, "que la orden ya tiene una cotización generada"),
    (C, "el técnico intenta modificar el diagnóstico"),
    (E, "el sistema no debe permitirlo"),
    (Y, "debe indicar que cualquier hallazgo nuevo se registra como falla adicional"),
], F2, ["RN-03"], "OrdenDeServicio, error DiagnosticoNoModificable", "ServicioDeDiagnostico.registrar_diagnostico",
   "POST /api/ordenes/{numero}/diagnostico (409)", TEC, nombre="El diagnóstico no cambia después de cotizar")

ca("CA-034", "US-019", [
    (D, "que una orden está en «En Reparación»"),
    (C, "el técnico reporta una falla adicional con su descripción"),
    (E, "el sistema debe vincularla a la orden"),
    (Y, "debe notificar al asesor para que genere la cotización adicional"),
], F5, ["RN-24"], "OrdenDeServicio, FallaAdicional, evento FallaAdicionalReportada → AlertaInterna",
   "ServicioDeDiagnostico.reportar_falla_adicional", "POST /api/ordenes/{numero}/fallas-adicionales", TEC,
   nombre="Reportar una falla adicional")

ca("CA-035", "US-020", [
    (D, "que una orden está en estado «Recibida»"),
    (C, "el asesor le asigna un técnico"),
    (E, "el sistema debe cambiar la orden a «En Diagnóstico»"),
    (Y, "debe mostrarla en el panel de ese técnico"),
], F2, ["RN-22"], "OrdenDeServicio (MAQUINA_DE_ORDEN), Empleado (RolDeEmpleado.TECNICO), evento TecnicoAsignadoParaDiagnostico",
   "ServicioDeDiagnostico.asignar_tecnico", "POST /api/ordenes/{numero}/asignacion-diagnostico", ASE,
   nombre="Asignar técnico para el diagnóstico")

ca("CA-036", "US-020", [
    (D, "que una orden tiene trabajos autorizados sin asignar"),
    (C, "el asesor los asigna a un técnico"),
    (E, "el sistema debe mostrarlos en el panel de ese técnico en estado «Pendiente»"),
], F5, ["RN-08"], "OrdenDeServicio, Trabajo, Empleado (RolDeEmpleado.TECNICO), evento TrabajosAsignados",
   "ServicioDeReparacion.asignar_trabajos", "POST /api/ordenes/{numero}/asignacion-trabajos", ASE,
   nombre="Asignar los trabajos autorizados")

ca("CA-037", "US-021", [
    (D, "que un cliente entra a la pantalla «Consulta tu vehículo»"),
    (C, "escribe su número de orden y sus placas y ambos coinciden"),
    (E, "el sistema debe mostrar el estado actual de la orden, la fecha de ingreso y la fecha de su última actualización"),
    (Y, "no debe permitir modificar nada"),
], TRANS, ["RN-20"], "Modelo de lectura EstadoDeOrdenVista, NumeroOrden y Placas (VO)", "Consulta ConsultarEstadoDeOrden",
   "GET /api/consulta-de-estado?orden=&placas=", PUB, nombre="Consulta de estado con datos correctos")

ca("CA-038", "US-021", [
    (D, "que un cliente está en la pantalla «Consulta tu vehículo»"),
    (C, "el número de orden y las placas no coinciden con ninguna orden"),
    (E, "el sistema debe mostrar el mensaje «No se encontró una orden con esos datos. Revise el número de orden y las placas e intente de nuevo.» sin revelar ninguna información"),
], TRANS, ["RN-20"], "Modelo de lectura EstadoDeOrdenVista", "Consulta ConsultarEstadoDeOrden",
   "GET /api/consulta-de-estado?orden=&placas= (404)", PUB, nombre="Consulta de estado con datos que no coinciden")

ca("CA-039", "US-022", [
    (D, "que una orden de cliente de flotilla está en «Lista para Entrega»"),
    (C, "Caja registra el cargo a crédito"),
    (E, "el sistema debe cambiar la orden a «Por Cobrar (Crédito)»"),
    (Y, "debe registrar el monto del cargo"),
    (Y, "debe impedir que se modifiquen los costos"),
    (Y, "la fecha de vencimiento queda pendiente hasta que se entregue el vehículo"),
], F6, ["RN-16", "RN-17", "RN-22"], "OrdenDeServicio, CargoACredito, evento CargoACreditoRegistrado",
   "ServicioDeCaja.registrar_cargo_a_credito", "POST /api/ordenes/{numero}/cargo-a-credito", CAJ,
   cambio="H-PIA-02", nombre="Registrar el cargo a crédito de una flotilla")

ca("CA-040", "US-023", [
    (D, "que una cotización lleva más de 48 horas en «Pendiente de Autorización del Cliente» desde que se marcó como presentada (o desde el último recontacto)"),
    (C, "el sistema ejecuta su revisión"),
    (E, "debe generar una alerta en el panel del asesor"),
    (C, "el asesor registra el recontacto"),
    (E, "el sistema guarda la fecha y hora sin cambiar el estado de la cotización"),
    (Y, "el plazo de 48 horas vuelve a contar desde ese recontacto"),
], F3, ["RN-12"], "spec RequiereRecontacto (PendienteDeAutorizacion AND FuePresentada AND MasDeHorasDesdeElUltimoContacto(48)), Cotizacion (recontactos), AlertaInterna",
   "ServicioDeRevisionDePlazos.revisar · ServicioDeCotizacion.registrar_recontacto",
   "POST /api/revisiones/plazos · POST /api/cotizaciones/{id}/recontactos", f"{SIS} / {ASE}",
   cambio="H-PIA-10", nombre="Alerta por cotización sin respuesta en 48 horas")

ca("CA-041", "US-024", [
    (D, "que una orden está en «Pagada» o en «Por Cobrar (Crédito)»"),
    (C, "el asesor registra la entrega del vehículo"),
    (E, "el sistema debe cambiar la orden a «Cerrada»"),
    (Y, "debe guardar la fecha y hora de entrega"),
    (Y, "si la orden tiene cargo a crédito, debe registrar su fecha de vencimiento: 15 días naturales después de la entrega"),
], F6, ["RN-17", "RN-18", "RN-22"], "spec PuedeEntregarse, OrdenDeServicio, CargoACredito (fecha_vencimiento), evento VehiculoEntregado",
   "ServicioDeEntrega.entregar", "POST /api/ordenes/{numero}/entrega", ASE,
   cambio="H-PIA-02", nombre="Entregar el vehículo y cerrar la orden")

ca("CA-042", "US-024", [
    (D, "que una orden no está en «Pagada» ni en «Por Cobrar (Crédito)»"),
    (C, "el asesor intenta registrar la entrega"),
    (E, "el sistema no debe permitirlo"),
    (Y, "si la orden todavía puede cobrarse, debe indicar que primero debe registrarse el pago o el cargo a crédito"),
    (Y, "si la orden está «Cancelada», «Cerrada» o «Cerrada sin Reparación», debe indicar esa situación sin pedir el pago"),
], F6, ["RN-18"], "spec PuedeEntregarse, error EntregaNoPermitida", "ServicioDeEntrega.entregar",
   "POST /api/ordenes/{numero}/entrega (409)", ASE, nombre="No se entrega sin pago ni cargo a crédito")

ca("CA-043", "US-024", [
    (D, "que el cliente rechazó toda la cotización"),
    (C, "el asesor selecciona «Entregar sin reparación»"),
    (E, "el sistema debe cambiar la orden a «Cerrada sin Reparación»"),
    (Y, "debe guardar la fecha y hora de entrega"),
    (Y, "no debe generar ningún cobro"),
], F3, ["RN-18", "RN-22"], "spec PuedeEntregarse (EstaCotizada AND TieneRechazoTotal), OrdenDeServicio, evento VehiculoEntregado",
   "ServicioDeEntrega.entregar_sin_reparacion", "POST /api/ordenes/{numero}/entrega-sin-reparacion", ASE,
   nombre="Entregar el vehículo sin reparación")

ca("CA-044", "US-025", [
    (D, "que una orden está en «Recibida» o «En Diagnóstico»"),
    (Y, "el cliente decide no continuar con el servicio"),
    (C, "el asesor registra la cancelación indicando el motivo"),
    (E, "el sistema debe cambiar la orden a «Cancelada»"),
    (Y, "debe guardar la fecha, la hora y el motivo"),
    (Y, "debe quitarla del panel del técnico asignado, si tenía uno"),
    (Y, "no debe generar ningún cobro"),
], DG2C, ["RN-19", "RN-22"], "spec PuedeCancelarse (EstaRecibida OR EstaEnDiagnostico), OrdenDeServicio, Cancelacion (VO), evento OrdenCancelada",
   "ServicioDeCancelacion.cancelar", "POST /api/ordenes/{numero}/cancelacion", ASE,
   cambio="H-PIA-01", nombre="Cancelar la orden antes de la cotización")

ca("CA-045", "US-025", [
    (D, "que una orden ya tiene una cotización generada («Cotizada» o un estado posterior)"),
    (C, "el asesor intenta cancelarla"),
    (E, "el sistema no debe permitirlo"),
    (Y, "debe indicar que la orden no se puede cancelar"),
    (Y, "si la orden está «Cotizada» y el cliente aún no decide, debe indicar que, si no desea la reparación, se registra el rechazo total de la cotización"),
], DG2C, ["RN-19"], "spec PuedeCancelarse, error CancelacionNoPermitida", "ServicioDeCancelacion.cancelar",
   "POST /api/ordenes/{numero}/cancelacion (409)", ASE, cambio="H-PIA-01",
   nombre="No se cancela una orden que ya tiene cotización")

ca("CA-046", "US-008", [
    (D, "que una orden está en «Pausada por Retiro de Vehículo»"),
    (C, "el técnico intenta iniciar uno de sus trabajos"),
    (E, "el sistema no debe permitirlo"),
    (Y, "debe indicar que el vehículo no está en el taller"),
], DG2R, ["RN-13", "RN-14"], "spec PuedeIniciarTrabajo (TrabajoPendiente AND AsignadoAlTecnico AND NOT OrdenPausadaPorRetiro), error TrabajoNoPermitido",
   "ServicioDeReparacion.iniciar_trabajo", "POST /api/ordenes/{numero}/trabajos/{id}/inicio (409)", TEC,
   cambio="H-PIA-06", nombre="No se trabaja un vehículo retirado del taller")

# ----------------------------------------------------------------------------- v3.1 (revisión del 09/11/2026)
# Criterios aprobados en la Fase 13 a partir de docs/auditoria-errores-de-usuario.md.
F23 = "Fase 2 y Fase 3: corrección de la cotización"

ca("CA-047", "US-026", [
    (D, "que una cotización está en «Pendiente de Autorización del Cliente» con un importe o una descripción mal capturados"),
    (C, "el asesor la corrige capturando los trabajos correctos y el motivo de la corrección"),
    (E, "el sistema debe guardar los trabajos corregidos conservando el número y la versión de la cotización"),
    (Y, "debe guardar en el historial de correcciones al asesor, la fecha y hora, el motivo, el total anterior y el total nuevo"),
    (Y, "si la cotización no requiere aprobación gerencial, debe dejarla en «Pendiente de Autorización del Cliente» como no presentada, para que el asesor la presente otra vez"),
], F23, ["RN-25", "RN-26", "RN-23"],
   "Cotizacion (corregir), CorreccionDeCotizacion, spec RequiereAprobacionGerencial, evento CotizacionCorregida",
   "ServicioDeCotizacion.corregir", "POST /api/cotizaciones/{id}/correcciones", ASE,
   cambio="H-PIA-21", nombre="Corregir una cotización que espera la decisión del cliente")

ca("CA-048", "US-026", [
    (D, "que una cotización inicial está en «Pendiente de Autorización del Cliente», aunque el Gerente ya la haya aprobado o se haya ajustado según sus observaciones"),
    (C, "el asesor la corrige y el total nuevo es mayor a $15,000 MXN"),
    (E, "el sistema debe cambiarla a «Pendiente de Aprobación Gerencial»"),
    (Y, "debe borrar la fecha de aprobación gerencial, que queda guardada en el historial de la corrección"),
    (Y, "debe enviar una alerta al panel del Gerente"),
    (Y, "debe impedir que se presente al cliente hasta que el Gerente la apruebe"),
], F23, ["RN-26", "RN-04", "RN-06", "RN-22"],
   "Cotizacion (corregir), spec RequiereAprobacionGerencial, MAQUINA_DE_COTIZACION, eventos CotizacionCorregida y AprobacionGerencialRequerida → AlertaInterna",
   "ServicioDeCotizacion.corregir", "POST /api/cotizaciones/{id}/correcciones · GET /api/alertas", f"{ASE} / {GER}",
   cambio="H-PIA-21", nombre="La corrección sube la cotización inicial arriba de $15,000 MXN")

ca("CA-049", "US-026", [
    (D, "que una cotización está en «Pendiente de Aprobación Gerencial»"),
    (C, "el asesor la corrige capturando el motivo"),
    (E, "si el total nuevo sigue siendo mayor a $15,000 MXN, la cotización debe quedarse en «Pendiente de Aprobación Gerencial» con los trabajos corregidos"),
    (Y, "si el total nuevo es menor o igual a $15,000 MXN, debe cambiarla a «Pendiente de Autorización del Cliente» como no presentada"),
    (Y, "en los dos casos debe guardar la corrección en el historial"),
], F23, ["RN-25", "RN-26", "RN-04"],
   "Cotizacion (corregir), spec RequiereAprobacionGerencial, MAQUINA_DE_COTIZACION, evento CotizacionCorregida",
   "ServicioDeCotizacion.corregir", "POST /api/cotizaciones/{id}/correcciones", ASE,
   cambio="H-PIA-21", nombre="Corregir una cotización que espera al Gerente")

ca("CA-050", "US-026", [
    (D, "que el asesor intenta corregir una cotización"),
    (C, "la cotización está en «Requiere Ajuste», «Autorizada», «Autorizada Parcialmente» o «Rechazada», o el asesor no captura el motivo"),
    (E, "el sistema no debe permitirlo"),
    (Y, "si falta el motivo, debe pedir que lo capture"),
    (Y, "si está en «Requiere Ajuste», debe indicar que se guarde la cotización ajustada según las observaciones del Gerente"),
    (Y, "si ya tiene la decisión del cliente, debe indicar que ya no se corrige y que los trabajos nuevos se cotizan con una cotización adicional"),
], F23, ["RN-25", "RN-05"],
   "Cotizacion (corregir), error OperacionDeCotizacionNoPermitida, ValorInvalido (motivo)",
   "ServicioDeCotizacion.corregir", "POST /api/cotizaciones/{id}/correcciones (409, 422)", ASE,
   cambio="H-PIA-21", nombre="No se corrige sin motivo ni una cotización por ajustar o ya decidida")

ca("CA-051", "US-026", [
    (D, "que una cotización presentada, con recontactos registrados, se corrigió y quedó en «Pendiente de Autorización del Cliente»"),
    (C, "el sistema ejecuta su revisión de plazos antes de que el asesor la presente otra vez"),
    (E, "no debe generar la alerta de 48 horas"),
    (Y, "debe conservar los recontactos anteriores como historial"),
    (C, "el asesor la presenta otra vez"),
    (E, "el plazo de 48 horas debe contar solo desde la nueva presentación y los recontactos posteriores a ella"),
], F23, ["RN-26", "RN-12"],
   "Cotizacion (fecha_presentacion, ultimo_contacto), spec RequiereRecontacto, ServicioDeRevisionDePlazos",
   "ServicioDeRevisionDePlazos.revisar · ServicioDeCotizacion.presentar",
   "POST /api/revisiones/plazos · POST /api/cotizaciones/{id}/presentacion", f"{SIS} / {ASE}",
   cambio="H-PIA-21", nombre="El plazo de 48 horas después de una corrección")

ca("CA-052", "US-001", [
    (D, "que el vehículo con placas XYZ998 ya tiene una orden abierta (en un estado distinto de «Cerrada», «Cerrada sin Reparación» y «Cancelada»)"),
    (C, "el asesor intenta registrar otra orden para ese vehículo, por ejemplo con un doble clic en «Registrar»"),
    (E, "el sistema no debe abrir una segunda orden"),
    (Y, "debe mostrar el mensaje «El vehículo con placas XYZ998 ya tiene abierta la orden OS-0001 (estado «Recibida»). Ábrala en lugar de registrar otra.»"),
    (Y, "aunque las dos solicitudes lleguen al mismo tiempo, solo una orden debe quedar registrada y la otra debe recibir el mismo mensaje"),
], F1, ["RN-27"], "VerificadorDeOrdenUnica, RepositorioDeOrdenes.abierta_del_vehiculo, índice único parcial de ordenes(placas), error VehiculoConOrdenAbierta",
   "ServicioDeRecepcion.registrar_orden", "POST /api/ordenes (409)", ASE,
   cambio="H-PIA-22", nombre="No se abre una segunda orden del mismo vehículo")

ca("CA-053", "US-020", [
    (D, "que el asesor va a asignar un técnico para el diagnóstico o para los trabajos autorizados"),
    (C, "consulta la lista de técnicos"),
    (E, "el sistema debe mostrar la clave y el nombre de cada empleado con rol Técnico"),
    (Y, "no debe mostrar empleados de otros puestos"),
], F2, ["RN-28"], "Empleado (RolDeEmpleado.TECNICO), modelo de lectura TecnicoVista", "Consulta ListarTecnicos",
   "GET /api/tecnicos", ASE, cambio="H-PIA-23", nombre="Lista de técnicos para asignar")

ca("CA-054", "US-020", [
    (D, "que una orden está en «En Diagnóstico» y el técnico asignado todavía no registra el diagnóstico"),
    (C, "el asesor asigna a otro técnico"),
    (E, "el sistema debe cambiar el técnico de la orden sin cambiar su estado"),
    (Y, "la orden debe salir del panel del técnico anterior y aparecer en el del nuevo"),
    (Y, "si el diagnóstico ya está registrado, no debe permitir el cambio e indicar que el diagnóstico ya está registrado"),
], F2, ["RN-28", "RN-22"], "OrdenDeServicio (asignar_tecnico_para_diagnostico), evento TecnicoDeDiagnosticoReasignado, error CorreccionNoPermitida",
   "ServicioDeDiagnostico.asignar_tecnico", "POST /api/ordenes/{numero}/asignacion-diagnostico · GET /api/tecnicos/me/panel", ASE,
   cambio="H-PIA-23", nombre="Cambiar el técnico de diagnóstico")

ca("CA-055", "US-027", [
    (D, "que el nombre, el teléfono o el correo de un cliente se capturaron mal"),
    (C, "el asesor los corrige"),
    (E, "el sistema debe guardar los datos corregidos sin cambiar las órdenes ni las cotizaciones del cliente"),
    (Y, "las decisiones que se registren después deben compararse con el nombre corregido"),
], F1, ["RN-29", "RN-07"], "Cliente (actualizar_contacto)", "ServicioDeRecepcion.corregir_cliente",
   "PUT /api/clientes/{id}", ASE, cambio="H-PIA-24", nombre="Corregir los datos del cliente")

ca("CA-056", "US-027", [
    (D, "que el VIN, la marca, el modelo o el año de un vehículo se capturaron mal"),
    (C, "el asesor los corrige"),
    (E, "el sistema debe guardar los datos corregidos sin cambiar las placas"),
    (Y, "si el VIN corregido ya pertenece a otro vehículo, no debe permitirlo e indicar que revise el dato"),
], F1, ["RN-29"], "Vehiculo (actualizar_datos), VIN (VO)", "ServicioDeRecepcion.corregir_vehiculo",
   "PUT /api/vehiculos/{placas}", ASE, cambio="H-PIA-24", nombre="Corregir los datos del vehículo")

ca("CA-057", "US-027", [
    (D, "que una orden está en «Recibida» o «En Diagnóstico»"),
    (C, "el asesor corrige el kilometraje, el nivel de combustible o el motivo de ingreso"),
    (E, "el sistema debe guardar los datos corregidos sin cambiar el estado de la orden"),
    (Y, "si la orden ya tiene cotización, no debe permitirlo e indicar que esos datos solo se corrigen antes de la cotización"),
], F1, ["RN-29"], "OrdenDeServicio (corregir_datos_de_recepcion), EstadoDeRecepcion, evento DatosDeRecepcionCorregidos, error CorreccionNoPermitida",
   "ServicioDeRecepcion.corregir_recepcion", "PUT /api/ordenes/{numero}/recepcion", ASE,
   cambio="H-PIA-24", nombre="Corregir el estado de recepción")

ca("CA-058", "US-014", [
    (D, "que Caja registró el pago de una orden con la forma de pago equivocada y la orden sigue «Pagada»"),
    (C, "Caja corrige la forma de pago"),
    (E, "el sistema debe guardar la forma de pago correcta sin cambiar el monto, la fecha del pago ni el estado de la orden"),
    (Y, "debe dejar constancia de la forma de pago anterior y de la nueva"),
    (Y, "si el vehículo ya se entregó, no debe permitir el cambio"),
], F6, ["RN-30", "RN-16"], "OrdenDeServicio (corregir_forma_de_pago), Pago, FormaDePago, evento FormaDePagoCorregida, error CorreccionNoPermitida",
   "ServicioDeCaja.corregir_forma_de_pago", "PUT /api/ordenes/{numero}/pago", CAJ,
   cambio="H-PIA-24", nombre="Corregir la forma de pago antes de la entrega")

ca("CA-059", "US-001", [
    (D, "que el asesor captura los datos del cliente, del Responsable de Flotilla, del vehículo y del estado de recepción"),
    (C, "escribe un teléfono que no tiene 10 dígitos, un correo sin la forma nombre@dominio.algo, un año mayor al año actual + 1, un kilometraje mayor a 2,000,000 o un texto de más de 1,000 caracteres"),
    (E, "el sistema no debe guardar el registro"),
    (Y, "debe indicar qué dato está mal y cómo debe capturarse, por ejemplo «El teléfono debe tener 10 dígitos, por ejemplo 81 1234 5678.»"),
    (Y, "un teléfono o un correo con solo espacios debe tratarse como no capturado"),
], F1, ["RN-31"], "Telefono y Correo (VO), Vehiculo (año), EstadoDeRecepcion (kilometraje), textos libres con largo máximo",
   "ServicioDeRecepcion.registrar_orden / registrar_cliente", "POST /api/ordenes (422) · POST /api/clientes (422)", ASE,
   cambio="H-PIA-25", nombre="Datos de captura con forma y rango razonables")

ca("CA-060", "US-004", [
    (D, "que el asesor captura los trabajos de una cotización"),
    (C, "un trabajo suma $0.00 entre su mano de obra y sus refacciones"),
    (E, "el sistema no debe guardar la cotización"),
    (Y, "debe indicar qué trabajo vale $0.00 y pedir que capture su importe"),
], F2, ["RN-32", "RN-23"], "LineaDeCotizacion (subtotal), Dinero",
   "ServicioDeCotizacion.generar_inicial / generar_adicional / ajustar / corregir",
   "POST /api/ordenes/{numero}/cotizaciones (422) · POST /api/ordenes/{numero}/cotizaciones-adicionales (422)", ASE,
   cambio="H-PIA-25", nombre="Cada trabajo de la cotización vale más de $0.00")

ca("CA-061", "US-009", [
    (D, "que una orden tiene una cotización adicional en «Pendiente de Autorización del Cliente»"),
    (C, "el asesor intenta generar otra cotización adicional, por ejemplo con un doble clic"),
    (E, "el sistema no debe generarla"),
    (Y, "debe indicar que primero se registre la decisión del cliente sobre la cotización adicional pendiente, con su versión"),
], F5, ["RN-33", "RN-24"], "OrdenDeServicio (adicionales_pendientes), error OperacionDeCotizacionNoPermitida",
   "ServicioDeCotizacion.generar_adicional", "POST /api/ordenes/{numero}/cotizaciones-adicionales (409)", ASE,
   cambio="H-PIA-26", nombre="Una sola cotización adicional sin decisión a la vez")

ca("CA-062", "US-010", [
    (D, "que un trabajo ya tiene una solicitud de compra «Solicitada» de una refacción"),
    (C, "el técnico vuelve a solicitar la misma refacción para el mismo trabajo, por ejemplo con un doble clic"),
    (E, "el sistema no debe crear otra solicitud"),
    (Y, "debe indicar que esa refacción ya está solicitada y que Compras la está gestionando"),
    (Y, "la refacción debe compararse sin distinguir mayúsculas ni espacios repetidos"),
], F4, ["RN-34", "RN-09"], "OrdenDeServicio (crear_solicitud_de_compra), SolicitudDeCompra, error SolicitudNoPermitida",
   "ServicioDeRefacciones.solicitar", "POST /api/ordenes/{numero}/solicitudes-de-compra (409)", TEC,
   cambio="H-PIA-26", nombre="No se repite la solicitud de una refacción pendiente")

ca("CA-063", "US-006", [
    (D, "que el cliente particular se llama «Luis Peña»"),
    (C, "el asesor registra la decisión a nombre de «Luis  Peña» (con dos espacios), « luis peña » o «LUIS PEÑA»"),
    (E, "el sistema debe aceptar el nombre como el mismo"),
    (Y, "si el nombre se escribe sin acento («Luis Pena»), debe rechazarlo e indicar a nombre de quién se registra la decisión"),
], F3, ["RN-07"], "spec AutorizanteValido (AutorizaElCliente, AutorizaSuResponsableDeFlotilla)",
   "ServicioDeAutorizacion.registrar_decision", "POST /api/cotizaciones/{id}/decision", ASE,
   cambio="H-PIA-27", nombre="El nombre del autorizante con espacios de más")

ca("CA-064", "US-016", [
    (D, "que la orden es de un cliente de flotilla de la empresa «Transportes Norte», cuyo Responsable de Flotilla es «Ana Torres»"),
    (C, "el asesor registra la decisión con el rol «Cliente» o a nombre de otra persona"),
    (E, "el sistema no debe registrarla"),
    (Y, "debe indicar la empresa, el nombre del Responsable de Flotilla y el rol con el que se registra: «Para la flotilla de Transportes Norte, registre la decisión a nombre de su Responsable de Flotilla, Ana Torres, con el rol «Responsable de Flotilla».»"),
], F3, ["RN-07"], "VerificadorDeAutorizante, error AutorizanteNoValido",
   "ServicioDeAutorizacion.registrar_decision", "POST /api/cotizaciones/{id}/decision (409)", ASE,
   cambio="H-PIA-27", nombre="Flotilla: el mensaje dice a nombre de quién y con qué rol")

ca("CA-065", "US-016", [
    (D, "que la empresa «Transportes Norte» ya está registrada con su Responsable de Flotilla «Ana Torres»"),
    (C, "el asesor registra la misma empresa con datos distintos del responsable"),
    (E, "el sistema no debe crear otra empresa ni cambiar en silencio al responsable registrado"),
    (Y, "debe indicar que la empresa ya está registrada, con el nombre y el teléfono de su Responsable de Flotilla, para que use ese registro"),
    (Y, "si los datos del responsable son los mismos, debe devolver la empresa registrada, como hasta ahora"),
], F1, ["RN-07"], "Cliente (TipoCliente.FLOTILLA), ResponsableDeFlotilla, error EmpresaYaRegistrada",
   "ServicioDeRecepcion.registrar_cliente", "POST /api/clientes (409)", ASE,
   cambio="H-PIA-28", nombre="La empresa de flotilla ya está registrada")

ca("CA-066", "US-027", [
    (D, "que una orden está en «Recibida» o «En Diagnóstico» y las placas de su vehículo se capturaron mal"),
    (C, "el asesor corrige las placas"),
    (E, "el sistema debe cambiar las placas del vehículo y de sus órdenes"),
    (Y, "el cliente debe poder consultar el estado de su orden con las placas correctas"),
    (Y, "si las placas nuevas ya pertenecen a otro vehículo, o la orden está en otro estado, no debe permitirlo e indicar el motivo"),
], F1, ["RN-35"], "Vehiculo y OrdenDeServicio (corregir placas), Placas (VO), evento PlacasCorregidas, error CorreccionNoPermitida",
   "ServicioDeRecepcion.corregir_placas", "PUT /api/ordenes/{numero}/placas · GET /api/consulta-de-estado?orden=&placas=", ASE,
   cambio="H-PIA-29", nombre="Corregir las placas mal capturadas")

# ----------------------------------------------------------------------------- áreas (archivos .feature)
AREAS = [
    ("01_recepcion", "Recepción y registro del vehículo",
     "Registrar digitalmente al cliente, al vehículo y su estado de ingreso para abrir la Orden de Servicio.",
     ["US-001", "US-002", "US-003", "US-016", "US-027"]),
    ("02_diagnostico", "Asignación y diagnóstico",
     "Asignar técnicos, registrar el diagnóstico y reportar fallas adicionales.",
     ["US-020", "US-019", "US-007"]),
    ("03_cotizacion", "Cotización y aprobación gerencial",
     "Generar cotizaciones formales, aprobar las de alto monto y dar seguimiento a las que no tienen respuesta.",
     ["US-004", "US-005", "US-023", "US-026"]),
    ("04_autorizacion", "Autorización del cliente y cotizaciones adicionales",
     "Registrar con evidencia la decisión del cliente o del Responsable de Flotilla.",
     ["US-006", "US-009"]),
    ("05_reparacion_y_refacciones", "Reparación, refacciones y retiro anticipado",
     "Ejecutar los trabajos autorizados, gestionar refacciones con Compras y manejar el retiro anticipado.",
     ["US-008", "US-010", "US-011", "US-012", "US-013"]),
    ("06_caja_y_entrega", "Caja y entrega del vehículo",
     "Registrar el pago o el cargo a crédito, emitir el recibo y entregar el vehículo.",
     ["US-014", "US-015", "US-022", "US-024"]),
    ("07_consultas", "Consultas del gerente y del cliente",
     "Dar visibilidad del estado del taller al Gerente y del estado del vehículo al cliente.",
     ["US-017", "US-018", "US-021"]),
    ("08_cancelacion", "Cancelación de la orden",
     "Cerrar sin cobro la orden de un cliente que desiste antes de la cotización.",
     ["US-025"]),
]

# ----------------------------------------------------------------------------- reglas de negocio
REGLAS = {
    "RN-01": ("Solo el Asesor de Servicio registra clientes, vehículos y órdenes.", "BRD §2 Roles y permisos"),
    "RN-02": ("La cotización solo se genera a partir de un diagnóstico registrado por el técnico asignado.", "BRD §1; CA-005, CA-032"),
    "RN-03": ("Después de generar la cotización el diagnóstico no se modifica; los hallazgos nuevos son fallas adicionales.", "BRD Restricción 7"),
    "RN-04": ("La cotización inicial mayor a $15,000 MXN requiere aprobación del Gerente; las adicionales nunca.", "BRD Restricción 4"),
    "RN-05": ("El rechazo del Gerente exige observaciones; la versión ajustada no regresa a revisión.", "BRD §2 Reglas implícitas"),
    "RN-06": ("Una cotización que espera aprobación gerencial no puede presentarse al cliente.", "BRD Restricción 4; CE-05"),
    "RN-07": ("La decisión se registra a nombre del autorizante válido: el cliente particular o el Responsable de Flotilla, nunca el conductor.", "BRD Restricción 5"),
    "RN-08": ("Solo los trabajos autorizados se asignan y se ejecutan; los demás quedan «No Autorizado».", "BRD §2 Excepciones; CE-01"),
    "RN-09": ("Compras solo gestiona refacciones de trabajos que el cliente ya autorizó.", "BRD Restricción 8"),
    "RN-10": ("La orden está «En Espera de Refacción» mientras exista una solicitud «Solicitada» y regresa a su estado al llegar todas.", "BRD §1; CA-019, CA-022"),
    "RN-11": ("Una solicitud con más de 3 días hábiles sin llegar genera una alerta al asesor hasta que registre el aviso al cliente.", "BRD Restricción 3"),
    "RN-12": ("Una cotización presentada con más de 48 horas sin respuesta genera una alerta al asesor.", "BRD Restricción 2"),
    "RN-13": ("El retiro anticipado requiere la Nota de Responsabilidad firmada y la orden pierde su lugar en la fila.", "BRD Restricción 6"),
    "RN-14": ("Un trabajo solo lo inicia el técnico asignado y nunca mientras el vehículo está fuera del taller.", "BRD §4 Técnico; CA-046"),
    "RN-15": ("La orden pasa a «Lista para Entrega» cuando todos sus trabajos autorizados están completados.", "BRD §1"),
    "RN-16": ("El pago de contado cubre el total autorizado y solo aplica a particulares; las flotillas usan cargo a crédito; después del pago o cargo no cambian los costos.", "BRD Restricción 9; CA-026, CA-039"),
    "RN-17": ("El crédito de flotilla vence 15 días naturales después de la entrega del vehículo.", "BRD Restricción 5"),
    "RN-18": ("El vehículo solo se entrega con pago o cargo a crédito registrado; con rechazo total se entrega sin reparación y sin cobro.", "BRD Restricción 9"),
    "RN-19": ("Una orden solo se cancela antes de tener cotización («Recibida» o «En Diagnóstico»), con motivo y sin cobro.", "BRD Restricción 10"),
    "RN-20": ("La consulta pública muestra el estado solo si el número de orden y las placas coinciden, sin revelar otros datos.", "BRD §3 Oportunidad; CE-03"),
    "RN-21": ("El total de ingresos del día suma solo los pagos de contado de la fecha actual (sin cargos a crédito).", "BRD §2 Reportes; CE-07"),
    "RN-22": ("Los estados solo cambian por las transiciones permitidas de su máquina de estados; un cambio inválido se rechaza.", "Glosario §2; ADR-007"),
    "RN-23": ("Importes en MXN nunca negativos y calculados con Decimal; cantidades mayores a cero; una cotización tiene al menos un trabajo.", "BRD §5; datos del profesor"),
    "RN-24": ("La cotización adicional es la versión siguiente (v.2, v.3…) y no modifica la cotización original.", "BRD §2 Excepciones"),
    # v3.1 (revisión del 09/11/2026)
    "RN-25": ("Solo el Asesor corrige una cotización, con motivo, y solo en «Pendiente de Aprobación Gerencial» o «Pendiente de Autorización del Cliente»; conserva su número y versión, y cada corrección queda en su historial (asesor, fecha y hora, motivo, total anterior y total nuevo). En «Requiere Ajuste» se usa el ajuste (RN-05); después de la decisión del cliente, la cotización adicional.", "Revisión del 09/11/2026 (H-PIA-21); BRD Restricción 11"),
    "RN-26": ("Al corregir se vuelve a evaluar E1 y la cotización se presenta otra vez: si es inicial y supera $15,000 MXN regresa al Gerente aunque ya la hubiera aprobado o ajustado, porque RN-05 solo protege el ajuste que pidió el Gerente y una corrección cambia el monto que él revisó; el plazo de 48 horas cuenta desde la nueva presentación.", "H-PIA-21; BRD Restricciones 2, 4 y 11; ADR-018"),
    "RN-27": ("Un vehículo tiene a lo más una orden abierta (en un estado que no sea «Cerrada», «Cerrada sin Reparación» ni «Cancelada»); un segundo registro se rechaza con el mismo mensaje aunque llegue al mismo tiempo.", "Revisión del 09/11/2026 (H-PIA-22); BRD Restricción 12"),
    "RN-28": ("El técnico de diagnóstico se elige entre los empleados con rol Técnico y se puede cambiar mientras la orden está «En Diagnóstico» sin diagnóstico registrado; el cambio no modifica el estado de la orden.", "Revisión del 09/11/2026 (H-PIA-23); US-020"),
    "RN-29": ("El Asesor corrige los datos del cliente (nombre, teléfono, correo) y del vehículo (VIN, marca, modelo, año) con las mismas validaciones del registro y sin repetir un VIN; el kilometraje, el nivel de combustible y el motivo de ingreso solo se corrigen con la orden «Recibida» o «En Diagnóstico».", "Revisión del 09/11/2026 (H-PIA-24); CA-003"),
    "RN-30": ("Caja corrige la forma de pago solo mientras la orden está «Pagada» (antes de la entrega); el monto y la fecha del pago no cambian y queda constancia de la forma anterior.", "Revisión del 09/11/2026 (H-PIA-24); BRD Restricción 9"),
    "RN-31": ("Los datos de captura tienen forma y rango razonables: teléfono con 10 dígitos (se aceptan espacios, guiones y paréntesis), correo con la forma nombre@dominio.algo, año del vehículo hasta el año actual + 1 (America/Monterrey), kilometraje hasta 2,000,000 y textos libres de hasta 1,000 caracteres; un teléfono o un correo con solo espacios cuenta como no capturado.", "Revisión del 09/11/2026 (H-PIA-25); BRD §5"),
    "RN-32": ("Cada trabajo de una cotización vale más de $0.00 (mano de obra más refacciones); el taller no maneja trabajos sin costo.", "Revisión del 09/11/2026 (H-PIA-25); BRD §5 (sin garantías ni promociones)"),
    "RN-33": ("Una orden tiene a lo más una cotización adicional sin decisión del cliente; la siguiente se genera después de registrar esa decisión.", "Revisión del 09/11/2026 (H-PIA-26); BRD §2 Excepciones"),
    "RN-34": ("Un trabajo no tiene dos solicitudes «Solicitada» de la misma refacción (misma descripción, sin distinguir mayúsculas ni espacios repetidos); cuando la pieza llega se puede volver a solicitar.", "Revisión del 09/11/2026 (H-PIA-26); BRD Restricción 8"),
    "RN-35": ("Las placas de un vehículo se corrigen solo mientras su orden está «Recibida» o «En Diagnóstico» y si no pertenecen a otro vehículo; cambian en el vehículo y en sus órdenes a la vez (P2).", "Revisión del 09/11/2026 (H-PIA-29); AU-01, AU-36"),
}

# Reglas aprobadas en la Fase 13 que todavía no se construyen (misma idea que `planeado` en los CA).
REGLAS_PLANEADAS = set()

# ----------------------------------------------------------------------------- pruebas previstas
# Convención: toda prueba de aceptación se llama test_ca_0XX_<descripcion> para poder
# localizarla desde la matriz (ver docs/architecture/decisiones-tecnicas.md §7).
AREA_DE_PRUEBA = {
    "01_recepcion": "tests/api/test_recepcion.py",
    "02_diagnostico": "tests/api/test_diagnostico.py",
    "03_cotizacion": "tests/api/test_cotizacion.py",
    "04_autorizacion": "tests/api/test_autorizacion.py",
    "05_reparacion_y_refacciones": "tests/api/test_reparacion_y_refacciones.py",
    "06_caja_y_entrega": "tests/api/test_caja_y_entrega.py",
    "07_consultas": "tests/api/test_consultas.py",
    "08_cancelacion": "tests/api/test_cancelacion.py",
}


def area_de(us_id):
    for clave, _titulo, _desc, lista in AREAS:
        if us_id in lista:
            return clave
    raise KeyError(us_id)


def validar():
    usados = {c["us"] for c in CA.values()}
    assert usados == set(US), set(US) ^ usados
    en_areas = [u for *_x, lista in AREAS for u in lista]
    assert sorted(en_areas) == sorted(US), "cada US en exactamente un área"
    en_necesidades = [c for _us, cas, _b in TRAZA_NECESIDAD.values() for c in cas]
    assert set(en_necesidades) == set(CA), set(CA) ^ set(en_necesidades)
    for c in CA.values():
        for r in c["reglas"]:
            assert r in REGLAS, (c["id"], r)
    reglas_usadas = {r for c in CA.values() for r in c["reglas"]}
    assert reglas_usadas == set(REGLAS), set(REGLAS) - reglas_usadas
    assert REGLAS_PLANEADAS <= set(REGLAS), REGLAS_PLANEADAS - set(REGLAS)
    return len(NECESIDADES), len(US), len(CA), len(REGLAS)


if __name__ == "__main__":
    print(validar())
