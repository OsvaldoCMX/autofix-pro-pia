# Modelo de dominio — AutoFix Pro (PIA v3.0)

Este documento es la referencia del dominio para la implementación del PIA: Aggregates, Value Objects, Specifications, máquinas de estados, Domain Events y errores. Continúa el mapa de dominio de la Unidad 3 (ADR-001 y ADR-002) y agrega lo que pide el PIA (Specification, máquinas de estados de todos los objetos con estado y Domain Events con reacciones). Las reglas de negocio `RN-xx` están en la [matriz de trazabilidad](../trazabilidad/matriz-trazabilidad.md#2-reglas-de-negocio).

Diagramas: [mapa de dominio](diagramas/mapa-dominio.png) · [clases por capa](diagramas/clases-dominio.png) · [estados de la orden](diagramas/estados-orden.png) · [estados de cotización, trabajo y solicitud](diagramas/estados-cotizacion-trabajo-solicitud.png).

## 1. Contexto y módulos

Un solo *Bounded Context*, **Gestión del Taller**, dividido en módulos del paquete `src/domain`:

| Módulo | Contenido |
|---|---|
| `compartido` | Value Objects comunes (`Dinero`, `NumeroOrden`, `Placas`, `VIN`), `Especificacion`, `MaquinaDeEstados`, `EventoDeDominio`, `RaizDeAgregado`, `CalendarioHabil`, errores del dominio. |
| `ordenes` | Aggregate Orden de Servicio, sus entidades internas, estados, eventos y especificaciones. |
| `cotizaciones` | Aggregate Cotización, líneas, estados, eventos y la especificación de aprobación gerencial. |
| `clientes` | Aggregate Cliente y la especificación del autorizante válido. |
| `vehiculos` | Aggregate Vehículo (búsqueda por placas). |
| `empleados` | Aggregate Empleado y `RolDeEmpleado`. |
| `servicios` | Domain Service `VerificadorDeAutorizante`. |

Los Aggregates se relacionan **solo por identidad** (`numero_orden`, `id_cliente`, `placas`, `id_empleado`). Cuando un caso de uso modifica dos Aggregates (generar cotización + marcar la orden; registrar decisión + crear trabajos) los dos cambios se confirman en la misma Unidad de Trabajo (ADR-002).

## 2. Fichas de Aggregate

### 2.1 Orden de Servicio — raíz `OrdenDeServicio`

| Campo | Contenido |
|---|---|
| Identidad | `NumeroOrden` (folio único). En los datos del profesor, el folio es el `operacion_id` (p. ej. `AUT-O001`). |
| Referencias | `id_cliente`, `placas`, `asesor` (empleado que la registró), `tecnico_de_diagnostico`. |
| Entidades internas | `Trabajo`, `SolicitudDeCompra`, `FallaAdicional`, `ReciboInterno` (se construye en la Fase 10 junto con su PDF, P2; hasta entonces la orden solo guarda el `Pago`). |
| Value Objects | `EstadoDeRecepcion` (kilometraje, nivel de combustible, fotos), `Diagnostico`, `Pago`, `CargoACredito`, `NotaDeResponsabilidad`, `Cancelacion`. |
| Responsabilidades | Ciclo de vida completo del servicio: recepción, diagnóstico, cotizada, decisión, asignación y avance de trabajos, fallas adicionales, refacciones, retiro anticipado, pago o crédito, entrega y cancelación. |
| Invariantes | Solo cambia de estado por la tabla de su máquina de estados (RN-22) · sin diagnóstico no hay cotización y después el diagnóstico no cambia (RN-02, RN-03) · solo se asignan e inician trabajos autorizados (RN-08) · refacciones solo de trabajos autorizados (RN-09) · «En Espera de Refacción» mientras exista una solicitud «Solicitada» (RN-10) · nadie trabaja la orden con el vehículo fuera del taller y cada trabajo lo inicia su técnico (RN-14) · «Lista para Entrega» cuando todos los trabajos autorizados están completados y no hay cotización adicional sin decisión (RN-15) · el pago cubre el total autorizado y las flotillas no pagan de contado; después ya no cambian los costos (RN-16) · el vencimiento del crédito es la entrega + 15 días naturales (RN-17) · se entrega solo con pago, crédito o rechazo total (RN-18) · se cancela solo sin cotización, con motivo (RN-19). |
| Eventos | `OrdenRecibida`, `TecnicoAsignadoParaDiagnostico`, `DiagnosticoRegistrado`, `OrdenAutorizada`, `TrabajosAsignados`, `TrabajoIniciado`, `FallaAdicionalReportada`, `SolicitudDeCompraCreada`, `RefaccionDisponible`, `ClienteAvisadoDelRetraso`, `VehiculoRetirado`, `OrdenReactivada`, `OrdenListaParaEntrega`, `PagoRegistrado`, `CargoACreditoRegistrado`, `VehiculoEntregado`, `OrdenCancelada`. |
| Repositorio | `RepositorioDeOrdenes`: `obtener(numero)`, `agregar(orden)`, `guardar(orden)`, `siguiente_numero()`. |

### 2.2 Cotización — raíz `Cotizacion`

| Campo | Contenido |
|---|---|
| Identidad | `id` de la cotización; pertenece a una orden por `numero_orden`. |
| Entidades internas | `LineaDeCotizacion` (número, descripción, mano de obra, refacciones, decisión). |
| Value Objects | `TipoCotizacion` (Inicial/Adicional), `VersionCotizacion` (v.1, v.2…), `RefaccionCotizada`, `DecisionDelCliente`, `TrabajoDecidido`, `Autorizante`, `Recontacto`. |
| Responsabilidades | Calcular el total, decidir si requiere aprobación gerencial (por medio de la Specification), controlar revisión, ajuste, presentación y recontactos, y registrar la decisión del cliente. |
| Invariantes | Al menos un trabajo; total = suma de las líneas (RN-23) · la inicial es v.1 y las adicionales v.2 en adelante y no modifican la original (RN-24) · si requiere aprobación no se presenta (RN-04, RN-06) · el rechazo del Gerente exige observaciones y la ajustada no regresa a revisión (RN-05) · la decisión se registra una sola vez y sobre líneas existentes (RN-22). Guarda `fecha_aprobacion_gerencial` (CA-008, H-PIA-08). |
| Eventos | `CotizacionGenerada`, `AprobacionGerencialRequerida`, `CotizacionAprobadaPorGerente`, `CotizacionRechazadaPorGerente`, `CotizacionAjustada`, `CotizacionPresentada`, `RecontactoRegistrado`, `CotizacionAutorizada`, `CotizacionRechazadaPorCliente`. |
| Repositorio | `RepositorioDeCotizaciones`: `obtener(id)`, `agregar`, `guardar`, `de_la_orden(numero)`, `siguiente_version(numero)`, `siguiente_id()` (folio COT-0001). |

### 2.3 Cliente — raíz `Cliente`

Identidad `id_cliente`; `TipoCliente` (Particular/Flotilla); nombre, teléfono, correo; si es flotilla, `empresa` y `ResponsableDeFlotilla` (VO: nombre, teléfono, correo). **Invariante:** un cliente de flotilla siempre tiene empresa y Responsable de Flotilla (CA-028). `actualizar_contacto` cambia nombre, teléfono y correo de un cliente recurrente (CA-003). Repositorio: `RepositorioDeClientes` (`obtener`, `agregar`, `guardar`, `buscar_flotilla(empresa)`, `siguiente_id()`, folio CLI-0001). Sin eventos.

### 2.4 Vehículo — raíz `Vehiculo`

Identidad `Placas` (VO normalizado: sin espacios ni guiones, en mayúsculas) y `VIN`; marca, modelo, año e `id_cliente`. **Invariante:** placas y VIN obligatorios; el año está entre 1900 y 2100 (como el `CHECK` de la base). `actualizar_datos` cambia VIN, marca, modelo y año de un vehículo que regresa (CA-003). Repositorio: `RepositorioDeVehiculos` (`por_placas`, `agregar`, `guardar`). Sin eventos. En los datos del profesor no hay vehículos: se crea uno por operación con las placas derivadas de `referencia` (ADR-013).

### 2.5 Empleado — raíz `Empleado`

Identidad `id_empleado`; nombre; `RolDeEmpleado` (Asesor, Técnico, Gerente, Compras, Caja). **Invariante:** exactamente un rol. Se usa para asignar técnicos (CA-035, CA-036), dirigir las alertas y autorizar las rutas por rol (ADR-012). Repositorio: `RepositorioDeEmpleados` (`obtener`, `por_token` en la infraestructura de seguridad).

## 3. Value Objects principales

| Value Object | Regla que valida |
|---|---|
| `Dinero` | MXN con `Decimal`, redondeo a 2 decimales (`ROUND_HALF_UP`), nunca negativo; máximo 9,999,999,999.99 (`NUMERIC(12,2)` de la base). |
| `NumeroOrden` | No vacío; se guarda en mayúsculas. |
| `Placas` | No vacías; se comparan sin mayúsculas, espacios ni guiones. Ya normalizadas, solo admiten `A-Z` y `0-9` y máximo 15 caracteres (como el `CHECK` y el `VARCHAR(15)` de la base). |
| `VIN` | 17 caracteres alfanuméricos (sin I, O, Q). Antes de validar se quitan los espacios de los extremos y se pasa a mayúsculas. |
| `VersionCotizacion` | Empieza en 1; se muestra como `v.1`. |
| `RefaccionCotizada` | Descripción no vacía, cantidad > 0, importe = precio × cantidad. |
| `EstadoDeRecepcion` | Kilometraje ≥ 0, nivel de combustible de la lista (Reserva, 1/4, 1/2, 3/4, Lleno), fotos opcionales. Obligatorios al registrar una orden por la API; vacíos solo en las 60 órdenes importadas del profesor (no vienen en los datos). |
| `Diagnostico` | Fallas encontradas (no vacío), trabajos y refacciones recomendados, técnico y fecha/hora (CA-032, H-PIA-05). |
| `Autorizante` | Nombre no vacío y rol (Cliente o Responsable de Flotilla). |
| `DecisionDelCliente` | Trabajos autorizados y no autorizados, autorizante, fecha/hora y tipo de cotización. |
| `Pago` | Monto, `FormaDePago` (Efectivo, Tarjeta, Transferencia) y fecha/hora. |
| `CargoACredito` | Monto y fecha de registro; `fecha_vencimiento` = fecha de entrega + 15 días naturales, se fija al entregar (H-PIA-02). |
| `NotaDeResponsabilidad` | Fecha de salida, si ya se firmó y fecha de firma. |
| `Cancelacion` | Motivo (no vacío), fecha/hora y asesor (H-PIA-01). |

## 4. Specifications

Base: `Especificacion[T]` con `es_satisfecha_por(candidato) -> bool` y los combinadores `y()`, `o()`, `no()` (también como operadores `&`, `|`, `~`). Las especificaciones compuestas se arman con piezas pequeñas y reutilizables; cuando no se satisfacen, el Aggregate lanza el error del negocio correspondiente con un mensaje para el usuario (ADR-006).

| # | Specification | Composición | Candidato | Dónde se usa | RN / CA |
|---|---|---|---|---|---|
| E1 | `RequiereAprobacionGerencial` | `EsCotizacionInicial() & TotalMayorAlUmbral($15,000)` | `Cotizacion` | `Cotizacion.generar` decide el estado inicial | RN-04 · CA-005, CA-007, CA-016 |
| E2 | `AutorizanteValido` | `(EsClienteParticular() & AutorizaElCliente()) \| (EsClienteDeFlotilla() & AutorizaSuResponsableDeFlotilla())` | `(Cliente, Autorizante)` | `VerificadorDeAutorizante` antes de registrar la decisión | RN-07 · CA-010, CA-029 |
| E3 | `PuedeEntregarse` | `EstaPagada() \| EstaPorCobrarACredito() \| (EstaCotizada() & TieneRechazoTotal())` | `OrdenDeServicio` | `entregar` y `entregar_sin_reparacion` | RN-18 · CA-041, CA-042, CA-043 |
| E4 | `PuedeCancelarse` | `EstaRecibida() \| EstaEnDiagnostico()` | `OrdenDeServicio` | `cancelar` | RN-19 · CA-044, CA-045 |
| E5 | `PuedeIniciarTrabajo` | `TrabajoPendiente() & AsignadoAlTecnico(id) & ~OrdenPausadaPorRetiro()` | `(OrdenDeServicio, Trabajo)` | `iniciar_trabajo` | RN-14 · CA-014, CA-046 |
| E6 | `PuedeSolicitarRefaccion` | `TrabajoAutorizado() & (OrdenAutorizada() \| OrdenEnReparacion() \| OrdenEnEsperaDeRefaccion())` | `(OrdenDeServicio, Trabajo)` | `crear_solicitud_de_compra` | RN-09 · CA-019, CA-020 |
| E7 | `RequiereAlertaDeRefaccion` | `SolicitudPendiente() & MasDeDiasHabiles(3) & ~ClienteYaAvisado()` | `SolicitudDeCompra` + fecha de revisión | `ServicioDeRevisionDePlazos` | RN-11 · CA-023 |
| E8 | `RequiereRecontacto` | `PendienteDeAutorizacion() & FuePresentada() & MasDeHorasDesdeElUltimoContacto(48)` | `Cotizacion` + fecha de revisión | `ServicioDeRevisionDePlazos` | RN-12 · CA-040 |

En E2, `AutorizaElCliente` y `AutorizaSuResponsableDeFlotilla` comprueban el rol y el nombre del autorizante, sin distinguir mayúsculas, contra el cliente o su Responsable de Flotilla.

En E6, la pieza `TrabajoAutorizado` solo acepta trabajos abiertos («Pendiente» o «En Progreso»): un trabajo «Completado» ya no necesita piezas y la solicitud se rechaza con `SolicitudNoPermitida`. Así, mientras haya una solicitud pendiente siempre queda un trabajo abierto y la orden no se atasca después de que llega la refacción.

Combinan **AND, OR y NOT**: E2 y E6 (AND + OR), E3 (OR + AND), E5 y E7 (AND + NOT). E1 sustituye la lógica de `PoliticaPorMontoDeCotizacionInicial` de la Unidad 3 sin cambiar su intención (ADR-005 sigue vigente).

**Specifications de referencia del profesor.** Las reglas `puede_procesarse` y `beneficio_referencia` del paquete de datos **no** se agregan al dominio porque no son requisitos de AutoFix Pro (no hay clientes inactivos, preferentes ni promociones en el BRD). Para anotar los 120 casos de prueba, el arnés de `tests/datos_profesor/` las arma con la misma clase `Especificacion` y compara su resultado con la regla propia equivalente (ADR-013, [datos-profesor](../datos-profesor/README.md)).

## 5. Máquinas de estados

Una clase genérica `MaquinaDeEstados[E]` guarda la tabla `{estado: {estados destino}}`, los estados finales y el método `validar(actual, nuevo)`, que lanza `TransicionDeEstadoNoPermitida` («La orden no puede pasar de «X» a «Y»»). Cada Aggregate tiene su tabla (ADR-007). Las *guardas* son las Specifications de la sección 4.

### 5.1 Orden de Servicio (13 estados)

| Desde | Hacia | Disparador (método) | Guarda | Evento | CA |
|---|---|---|---|---|---|
| (inicio) | Recibida | `OrdenDeServicio.registrar` | datos válidos | `OrdenRecibida` | CA-001 |
| Recibida | En Diagnóstico | `asignar_tecnico_para_diagnostico` | empleado con rol Técnico | `TecnicoAsignadoParaDiagnostico` | CA-035 |
| Recibida | Cancelada | `cancelar` | E4 `PuedeCancelarse` + motivo | `OrdenCancelada` | CA-044 |
| En Diagnóstico | Cotizada | `marcar_cotizada` | diagnóstico registrado (RN-02) | (`CotizacionGenerada` en la cotización) | CA-005 |
| En Diagnóstico | Cancelada | `cancelar` | E4 + motivo | `OrdenCancelada` | CA-044 |
| Cotizada | Autorizada | `aplicar_decision` (total o parcial) | E2 `AutorizanteValido` | `OrdenAutorizada` | CA-010 |
| Cotizada | Cerrada sin Reparación | `entregar_sin_reparacion` | E3 (rechazo total) | `VehiculoEntregado(sin_reparacion=True)` | CA-043 |
| Autorizada | En Reparación | `iniciar_trabajo` | E5 `PuedeIniciarTrabajo` | `TrabajoIniciado` | CA-014 |
| Autorizada | En Espera de Refacción | `crear_solicitud_de_compra` | E6 `PuedeSolicitarRefaccion` | `SolicitudDeCompraCreada` | CA-019 |
| En Reparación | En Espera de Refacción | `crear_solicitud_de_compra` | E6 | `SolicitudDeCompraCreada` | CA-019 |
| En Reparación | Lista para Entrega | `completar_trabajo` / `aplicar_decision` (adicional rechazada) | todos los autorizados completados y sin adicional pendiente | `OrdenListaParaEntrega` | CA-015, CA-018 |
| En Espera de Refacción | Autorizada | `registrar_llegada_de_refaccion` | última pendiente y ningún trabajo iniciado | `RefaccionDisponible` | CA-022 |
| En Espera de Refacción | En Reparación | `registrar_llegada_de_refaccion` | última pendiente y algún trabajo iniciado | `RefaccionDisponible` | CA-022 |
| En Espera de Refacción | Pausada por Retiro de Vehículo | `confirmar_firma_de_nota` | nota generada | `VehiculoRetirado` | CA-024 |
| Pausada por Retiro de Vehículo | En Espera de Refacción | `reactivar` | aún hay solicitudes pendientes | `OrdenReactivada` | CA-025 |
| Pausada por Retiro de Vehículo | Autorizada | `reactivar` | sin pendientes y ningún trabajo iniciado | `OrdenReactivada` | CA-025 |
| Pausada por Retiro de Vehículo | En Reparación | `reactivar` | sin pendientes y algún trabajo iniciado | `OrdenReactivada` | CA-025 |
| Lista para Entrega | Pagada | `registrar_pago` | cliente particular, monto = total autorizado | `PagoRegistrado` | CA-026 |
| Lista para Entrega | Por Cobrar (Crédito) | `registrar_cargo_a_credito` | cliente de flotilla | `CargoACreditoRegistrado` | CA-039 |
| Pagada | Cerrada | `entregar` | E3 | `VehiculoEntregado` | CA-041 |
| Por Cobrar (Crédito) | Cerrada | `entregar` (fija el vencimiento) | E3 | `VehiculoEntregado(vence=…)` | CA-041 |

Estados finales: **Cerrada**, **Cerrada sin Reparación** y **Cancelada**. Cualquier otra combinación (por ejemplo, Recibida → Autorizada, «saltar estado») se rechaza con `TransicionDeEstadoNoPermitida` (HTTP 409).

Notas de comportamiento (precisiones v3.0):

- La orden entra a la fila de trabajo al registrarse: `fecha_ingreso_a_fila` es la fecha de ingreso. Sale de la fila al cancelarse o al firmarse la Nota de Responsabilidad (la fecha queda vacía) y `reactivar` le asigna una nueva, de modo que queda al final (CA-025, CA-044).
- Iniciar un trabajo mientras la orden está «En Espera de Refacción» se permite (otros trabajos pueden avanzar) y la orden sigue en espera; lo que cambia es el estado al que regresará: «En Reparación» (H-PIA-07).
- Completar el último trabajo mientras hay una solicitud «Solicitada» se rechaza con 409: la orden no puede quedar lista con refacciones pendientes. La validación se hace **antes** de modificar el trabajo, para no dejar el Aggregate a medias.
- La llegada de una refacción con la orden «Pausada por Retiro de Vehículo» marca la solicitud como «Disponible» pero no cambia el estado de la orden; al reactivarla se decide el estado (CA-025).
- El rechazo total no cierra la orden: queda «Cotizada» con la marca de rechazo total hasta «Entregar sin reparación» (decisión de la Unidad 3).
- El estado al que regresa una orden en espera o pausada se calcula con sus trabajos: «En Reparación» si alguno se inició y «Autorizada» si ninguno; `estado_antes_de_espera` expone ese resultado para guardarlo.
- Solo el técnico asignado registra el diagnóstico (RN-02) y, antes de generar la cotización, puede corregirlo. Las fallas adicionales y las cotizaciones adicionales solo se registran con la orden «En Reparación» (CA-016, CA-034).
- `asignar_trabajos` acepta trabajos «Pendiente», también para reasignarlos; una orden pausada o un trabajo ya iniciado se rechazan con `TrabajoNoPermitido`. Con el vehículo fuera del taller tampoco se completan trabajos (RN-14).
- El aviso al cliente se registra solo con la solicitud «Solicitada» y una sola vez; si no, `SolicitudNoPermitida`.
- La salida se registra solo con la orden «En Espera de Refacción». Una nota sin firmar se reemplaza si se registra otra salida y se descarta si la orden sale de la espera.

### 5.2 Cotización (6 estados)

| Desde | Hacia | Disparador | Guarda | Evento | CA |
|---|---|---|---|---|---|
| (inicio) | Pendiente de Aprobación Gerencial | `generar` | E1 se cumple | `CotizacionGenerada`, `AprobacionGerencialRequerida` | CA-007 |
| (inicio) | Pendiente de Autorización del Cliente | `generar` | E1 no se cumple (incluye todas las adicionales) | `CotizacionGenerada` | CA-005, CA-016 |
| Pendiente de Aprobación Gerencial | Pendiente de Autorización del Cliente | `aprobar_por_gerente` | — | `CotizacionAprobadaPorGerente` | CA-008 |
| Pendiente de Aprobación Gerencial | Requiere Ajuste | `rechazar_por_gerente` | observaciones no vacías | `CotizacionRechazadaPorGerente` | CA-009 |
| Requiere Ajuste | Pendiente de Autorización del Cliente | `ajustar` | al menos un trabajo | `CotizacionAjustada` | CA-009 |
| Pendiente de Autorización del Cliente | (mismo estado) | `marcar_presentada`, `registrar_recontacto` | — | `CotizacionPresentada`, `RecontactoRegistrado` | CA-006, CA-040 |
| Pendiente de Autorización del Cliente | Autorizada | `registrar_decision` (todas las líneas) | E2 | `CotizacionAutorizada` | CA-010 |
| Pendiente de Autorización del Cliente | Autorizada Parcialmente | `registrar_decision` (algunas líneas) | E2 | `CotizacionAutorizada(parcial)` | CA-010 |
| Pendiente de Autorización del Cliente | Rechazada | `registrar_decision` (ninguna línea) | E2 | `CotizacionRechazadaPorCliente` | CA-012, CA-018 |

Estados finales: Autorizada, Autorizada Parcialmente y Rechazada. Aprobar dos veces, presentar una cotización que espera al Gerente o registrar una segunda decisión lanza `OperacionDeCotizacionNoPermitida` (409). Lo mismo ocurre al presentar dos veces (reiniciaría las 48 horas; para eso está el recontacto) o al registrar un recontacto de una cotización que no se ha presentado.

### 5.3 Trabajo (4 estados) y Solicitud de Compra (2 estados)

| Objeto | Desde | Hacia | Disparador | Guarda | CA |
|---|---|---|---|---|---|
| Trabajo | (inicio) | Pendiente | `aplicar_decision` (línea autorizada) | — | CA-010, CA-017 |
| Trabajo | (inicio) | No Autorizado | `aplicar_decision` (línea no autorizada) | — | CA-010, CA-018 |
| Trabajo | Pendiente | En Progreso | `iniciar_trabajo` | E5 | CA-014 |
| Trabajo | En Progreso | Completado | `completar_trabajo` | técnico asignado | CA-015 |
| Solicitud | (inicio) | Solicitada | `crear_solicitud_de_compra` | E6 | CA-019 |
| Solicitud | Solicitada | Disponible | `registrar_llegada_de_refaccion` | — | CA-022 |

La asignación de un técnico no cambia el estado del trabajo (solo guarda `tecnico`). El aviso al cliente por retraso no cambia el estado de la solicitud (solo guarda `fecha_aviso_al_cliente`).

## 6. Domain Events y reacciones

Los eventos se registran dentro del Aggregate, la Unidad de Trabajo los recolecta y se publican **solo después de confirmar** la transacción (ADR-016). Los manejadores de la capa de aplicación crean las alertas internas; ningún manejador modifica otro Aggregate.

| Evento | Lo emite | Reacción (manejador) | CA |
|---|---|---|---|
| `OrdenRecibida` | Orden | — (bitácora) | CA-001 |
| `TecnicoAsignadoParaDiagnostico` | Orden | aparece en el panel del técnico (modelo de lectura) | CA-035 |
| `DiagnosticoRegistrado` | Orden | alerta al asesor: «lista para cotizar» | CA-032 |
| `AprobacionGerencialRequerida` | Cotización | alerta al Gerente | CA-007 |
| `CotizacionAprobadaPorGerente` | Cotización | alerta al asesor: «ya puede presentarse» | CA-008 |
| `CotizacionRechazadaPorGerente` | Cotización | alerta al asesor con las observaciones | CA-009 |
| `CotizacionAutorizada` (adicional) | Cotización | alerta a cada técnico con trabajos asignados en la orden | CA-017 |
| `FallaAdicionalReportada` | Orden | alerta al asesor: «generar cotización adicional» | CA-034 |
| `RefaccionDisponible` | Orden | alertas al técnico y al asesor | CA-022 |
| `OrdenListaParaEntrega` | Orden | alerta al asesor | CA-015 |
| `OrdenCancelada` | Orden | se quita del panel del técnico | CA-044 |
| `CotizacionGenerada`, `CotizacionPresentada`, `RecontactoRegistrado`, `OrdenAutorizada`, `TrabajosAsignados`, `TrabajoIniciado`, `SolicitudDeCompraCreada`, `ClienteAvisadoDelRetraso`, `VehiculoRetirado`, `OrdenReactivada`, `PagoRegistrado`, `CargoACreditoRegistrado`, `VehiculoEntregado`, `CotizacionAjustada`, `CotizacionRechazadaPorCliente` | Orden / Cotización | bitácora de eventos (evidencia de la trazabilidad y de las pruebas de transición) | varios |

Las alertas por tiempo (CA-023 y CA-040) no vienen de un evento sino de la revisión periódica de plazos (E7 y E8, ADR-015).

## 7. Errores del dominio

| Error | Cuándo | HTTP (ADR-008) |
|---|---|---|
| `ValorInvalido`, `CotizacionSinTrabajos` | Un dato en sí es inválido (vacío, negativo, cantidad ≤ 0, servicio inhabilitado en los datos de entrada). | 422 |
| `TransicionDeEstadoNoPermitida` | La máquina de estados no permite el cambio. | 409 |
| `OperacionDeCotizacionNoPermitida` | La cotización no está en el estado que exige la acción. | 409 |
| `DiagnosticoRequerido`, `DiagnosticoNoModificable` | RN-02 y RN-03. | 409 |
| `AutorizanteNoValido` | E2 no se cumple. | 409 |
| `TrabajoNoAutorizado`, `SolicitudNoPermitida` | E6 no se cumple, o se intenta asignar trabajos de una orden sin trabajos autorizados (rechazo total, CA-012). | 409 |
| `TrabajoNoPermitido` | E5 no se cumple porque el vehículo está fuera del taller o el trabajo no está pendiente; también al asignar con el vehículo fuera o un trabajo ya iniciado, o al completar con el vehículo fuera. | 409 |
| `TrabajoDeOtroTecnico` | E5 no se cumple porque el trabajo está asignado a otro técnico o a ninguno; también al completar un trabajo ajeno o al registrar un diagnóstico asignado a otro técnico. | 403 |
| `PagoNoPermitido` | Monto distinto del total autorizado o pago de contado de una flotilla. | 409 |
| `EntregaNoPermitida` | E3 no se cumple. | 409 |
| `CancelacionNoPermitida` | E4 no se cumple. | 409 |
| `OrdenNoEncontrada`, `CotizacionNoEncontrada`, `ClienteNoEncontrado`, `VehiculoNoEncontrado`, `EmpleadoNoEncontrado`, `TrabajoNoEncontrado`, `SolicitudNoEncontrada` | El identificador no existe. | 404 |

Todos heredan de `ErrorDeDominio` y su mensaje está escrito para el usuario del taller (se devuelve tal cual en el campo `detalle` de la respuesta).
