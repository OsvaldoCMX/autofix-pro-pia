# Modelo de dominio — AutoFix Pro (PIA v3.1)

Este documento es la referencia del dominio para la implementación del PIA: Aggregates, Value Objects, Specifications, máquinas de estados, Domain Events y errores. Continúa el mapa de dominio de la Unidad 3 (ADR-001 y ADR-002) y agrega lo que pide el PIA (Specification, máquinas de estados de todos los objetos con estado y Domain Events con reacciones). La v3.1 agrega las correcciones aprobadas después de la revisión del 09/11/2026 (H-PIA-21 en adelante, `auditoria-errores-de-usuario.md`); mientras la Fase 14 no las construya, la matriz de trazabilidad las marca como «Planeado». Las reglas de negocio `RN-xx` están en la [matriz de trazabilidad](../trazabilidad/matriz-trazabilidad.md#2-reglas-de-negocio).

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
| `servicios` | Domain Services `VerificadorDeAutorizante` y, en la v3.1, `VerificadorDeOrdenUnica` (RN-27). |

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
| Invariantes | Solo cambia de estado por la tabla de su máquina de estados (RN-22) · sin diagnóstico no hay cotización y después el diagnóstico no cambia (RN-02, RN-03) · solo se asignan e inician trabajos autorizados (RN-08) · refacciones solo de trabajos autorizados (RN-09) · «En Espera de Refacción» mientras exista una solicitud «Solicitada» (RN-10) · nadie trabaja la orden con el vehículo fuera del taller y cada trabajo lo inicia su técnico (RN-14) · «Lista para Entrega» cuando todos los trabajos autorizados están completados y no hay cotización adicional sin decisión (RN-15) · el pago cubre el total autorizado y las flotillas no pagan de contado; después ya no cambian los costos (RN-16) · el vencimiento del crédito es la entrega + 15 días naturales (RN-17) · se entrega solo con pago, crédito o rechazo total (RN-18) · se cancela solo sin cotización, con motivo (RN-19) · *(v3.1)* a lo más una cotización adicional sin decisión (RN-33) y ninguna refacción solicitada dos veces para el mismo trabajo mientras está «Solicitada» (RN-34). |
| Eventos | `OrdenRecibida`, `TecnicoAsignadoParaDiagnostico`, `DiagnosticoRegistrado`, `OrdenAutorizada`, `TrabajosAsignados`, `TrabajoIniciado`, `FallaAdicionalReportada`, `SolicitudDeCompraCreada`, `RefaccionDisponible`, `ClienteAvisadoDelRetraso`, `VehiculoRetirado`, `OrdenReactivada`, `OrdenListaParaEntrega`, `PagoRegistrado`, `CargoACreditoRegistrado`, `VehiculoEntregado`, `OrdenCancelada`, `TecnicoDeDiagnosticoReasignado`, `DatosDeRecepcionCorregidos`, `FormaDePagoCorregida` y `PlacasCorregidas` (P2) (v3.1). |
| Repositorio | `RepositorioDeOrdenes`: `obtener(numero)`, `agregar(orden)`, `guardar(orden)`, `siguiente_numero()` y, en la v3.1, `abierta_del_vehiculo(placas)`. |

### 2.2 Cotización — raíz `Cotizacion`

| Campo | Contenido |
|---|---|
| Identidad | `id` de la cotización; pertenece a una orden por `numero_orden`. |
| Entidades internas | `LineaDeCotizacion` (número, descripción, mano de obra, refacciones, decisión) y `CorreccionDeCotizacion` (v3.1: asesor, fecha y hora, motivo, total anterior y nuevo, estado anterior y nuevo, fechas de presentación y de aprobación gerencial que tenía; tabla `correcciones_de_cotizacion`). |
| Value Objects | `TipoCotizacion` (Inicial/Adicional), `VersionCotizacion` (v.1, v.2…), `RefaccionCotizada`, `DecisionDelCliente`, `TrabajoDecidido`, `Autorizante`, `Recontacto`. |
| Responsabilidades | Calcular el total, decidir si requiere aprobación gerencial (por medio de la Specification), controlar revisión, ajuste, corrección, presentación y recontactos, y registrar la decisión del cliente. |
| Invariantes | Al menos un trabajo; total = suma de las líneas (RN-23) · la inicial es v.1 y las adicionales v.2 en adelante y no modifican la original (RN-24) · si requiere aprobación no se presenta (RN-04, RN-06) · el rechazo del Gerente exige observaciones y la ajustada no regresa a revisión (RN-05) · la decisión se registra una sola vez y sobre líneas existentes (RN-22) · la corrige solo el Asesor, con motivo, antes de la decisión y fuera de «Requiere Ajuste»; conserva número y versión y deja historial (RN-25) · después de corregir se vuelve a evaluar E1 y se presenta otra vez (RN-26). Guarda `fecha_aprobacion_gerencial` (CA-008, H-PIA-08). |
| Eventos | `CotizacionGenerada`, `AprobacionGerencialRequerida`, `CotizacionAprobadaPorGerente`, `CotizacionRechazadaPorGerente`, `CotizacionAjustada`, `CotizacionCorregida` (v3.1), `CotizacionPresentada`, `RecontactoRegistrado`, `CotizacionAutorizada`, `CotizacionRechazadaPorCliente`. |
| Repositorio | `RepositorioDeCotizaciones`: `obtener(id)`, `agregar`, `guardar`, `de_la_orden(numero)`, `siguiente_version(numero)`, `siguiente_id()` (folio COT-0001). |

### 2.3 Cliente — raíz `Cliente`

Identidad `id_cliente`; `TipoCliente` (Particular/Flotilla); nombre, teléfono, correo; si es flotilla, `empresa` y `ResponsableDeFlotilla` (VO: nombre, teléfono, correo). **Invariante:** un cliente de flotilla siempre tiene empresa y Responsable de Flotilla (CA-028). *(v3.1, CA-065)* Si se registra otra vez la misma empresa con los mismos datos del responsable, se devuelve la registrada; con datos distintos, `EmpresaYaRegistrada` (409), sin cambiar al responsable en silencio. `actualizar_contacto` cambia nombre, teléfono y correo de un cliente recurrente (CA-003) y, en la v3.1, también corrige los datos mal capturados (`PUT /api/clientes/{id}`, CA-055, RN-29). Repositorio: `RepositorioDeClientes` (`obtener`, `agregar`, `guardar`, `buscar_flotilla(empresa)`, `siguiente_id()`, folio CLI-0001). Sin eventos.

### 2.4 Vehículo — raíz `Vehiculo`

Identidad `Placas` (VO normalizado: sin espacios ni guiones, en mayúsculas) y `VIN`; marca, modelo, año e `id_cliente`. **Invariante:** placas y VIN obligatorios; el año está entre 1900 y el año actual + 1 en America/Monterrey (v3.1, RN-31; el «año actual» lo da el reloj del caso de uso y el `CHECK` de la base sigue en 1900–2100). `actualizar_datos` cambia VIN, marca, modelo y año de un vehículo que regresa (CA-003) y, en la v3.1, también corrige los datos mal capturados sin repetir un VIN (`PUT /api/vehiculos/{placas}`, CA-056, RN-29). Repositorio: `RepositorioDeVehiculos` (`por_placas`, `agregar`, `guardar`). Sin eventos. En los datos del profesor no hay vehículos: se crea uno por operación con las placas derivadas de `referencia` (ADR-013).

**Una sola orden abierta por vehículo (v3.1, RN-27, H-PIA-22).** Antes de registrar una orden, `VerificadorDeOrdenUnica` consulta `RepositorioDeOrdenes.abierta_del_vehiculo(placas)` (una orden que no está en «Cerrada», «Cerrada sin Reparación» ni «Cancelada») y, si existe, lanza `VehiculoConOrdenAbierta` con el folio y el estado de esa orden. Como respaldo ante dos registros simultáneos (doble clic), la base tiene un índice único parcial en `ordenes(placas)` para las órdenes abiertas; si la base rechaza el segundo registro, la API responde el **mismo 409 con el mismo mensaje**, nunca un error 500 (lo comprueba una prueba de integración de la Fase 14). Las 60 órdenes del profesor tienen un vehículo cada una, así que el índice no las afecta.

**Corrección de placas (v3.1, P2, RN-35, H-PIA-29).** Las placas son la identidad del vehículo. Si sobra tiempo en la Fase 14, `ServicioDeRecepcion.corregir_placas` cambia las placas del vehículo y de sus órdenes en la misma Unidad de Trabajo, solo con la orden «Recibida» o «En Diagnóstico» y si las placas nuevas no pertenecen a otro vehículo (`CorreccionNoPermitida`, 409); emite `PlacasCorregidas`. Si no se construye, `PUT /api/ordenes/{numero}/placas` responde 501 como las demás rutas P2 y la página no la muestra.

### 2.5 Empleado — raíz `Empleado`

Identidad `id_empleado`; nombre; `RolDeEmpleado` (Asesor, Técnico, Gerente, Compras, Caja). **Invariante:** exactamente un rol. Se usa para asignar técnicos (CA-035, CA-036), dirigir las alertas y autorizar las rutas por rol (ADR-012). Repositorio: `RepositorioDeEmpleados` (`obtener`, `por_token` en la infraestructura de seguridad).

## 3. Value Objects principales

| Value Object | Regla que valida |
|---|---|
| `Dinero` | MXN con `Decimal`, redondeo a 2 decimales (`ROUND_HALF_UP`), nunca negativo; máximo 9,999,999,999.99 (`NUMERIC(12,2)` de la base). |
| `NumeroOrden` | No vacío; se guarda en mayúsculas. |
| `Placas` | No vacías; se comparan sin mayúsculas, espacios ni guiones. Ya normalizadas, solo admiten `A-Z` y `0-9` y máximo 15 caracteres (como el `CHECK` y el `VARCHAR(15)` de la base). |
| `VIN` | 17 caracteres alfanuméricos (sin I, O, Q). Antes de validar se quitan los espacios de los extremos y se pasa a mayúsculas. |
| `Telefono` *(v3.1)* | 10 dígitos; se aceptan espacios, guiones y paréntesis y se guardan solo los dígitos. Solo espacios cuenta como no capturado. Mensaje: «El teléfono debe tener 10 dígitos, por ejemplo 81 1234 5678.» (RN-31). |
| `Correo` *(v3.1)* | Forma `nombre@dominio.algo`, sin espacios. Solo espacios cuenta como no capturado (RN-31). |
| Textos libres *(v3.1)* | Motivo de ingreso, descripción del trabajo y de la refacción, fallas y recomendaciones, falla adicional, observaciones del Gerente y motivos de cancelación y de corrección: máximo 1,000 caracteres (RN-31). |
| `VersionCotizacion` | Empieza en 1; se muestra como `v.1`. |
| `RefaccionCotizada` | Descripción no vacía, cantidad > 0, importe = precio × cantidad. |
| `LineaDeCotizacion` *(entidad)* | *(v3.1)* Su subtotal (mano de obra + refacciones) es mayor a $0.00: el taller no maneja trabajos sin costo (RN-32). |
| `EstadoDeRecepcion` | Kilometraje entre 0 y 2,000,000 (el tope es de la v3.1, RN-31), nivel de combustible de la lista (Reserva, 1/4, 1/2, 3/4, Lleno), fotos opcionales. Obligatorios al registrar una orden por la API; vacíos solo en las 60 órdenes importadas del profesor (no vienen en los datos). *(v3.1)* Junto con el motivo de ingreso, se corrige con `corregir_datos_de_recepcion` mientras la orden esté «Recibida» o «En Diagnóstico» (RN-29). |
| `Diagnostico` | Fallas encontradas (no vacío), trabajos y refacciones recomendados, técnico y fecha/hora (CA-032, H-PIA-05). |
| `Autorizante` | Nombre no vacío y rol (Cliente o Responsable de Flotilla). |
| `DecisionDelCliente` | Trabajos autorizados y no autorizados, autorizante, fecha/hora y tipo de cotización. |
| `Pago` | Monto, `FormaDePago` (Efectivo, Tarjeta, Transferencia) y fecha/hora. *(v3.1)* La forma de pago se corrige con `corregir_forma_de_pago` mientras la orden esté «Pagada»; se reemplaza el `Pago` con el mismo monto y la misma fecha (RN-30). |
| `CargoACredito` | Monto y fecha de registro; `fecha_vencimiento` = fecha de entrega + 15 días naturales, se fija al entregar (H-PIA-02). |
| `NotaDeResponsabilidad` | Fecha de salida, si ya se firmó y fecha de firma. |
| `Cancelacion` | Motivo (no vacío), fecha/hora y asesor (H-PIA-01). |

## 4. Specifications

Base: `Especificacion[T]` con `es_satisfecha_por(candidato) -> bool` y los combinadores `y()`, `o()`, `no()` (también como operadores `&`, `|`, `~`). Las especificaciones compuestas se arman con piezas pequeñas y reutilizables; cuando no se satisfacen, el Aggregate lanza el error del negocio correspondiente con un mensaje para el usuario (ADR-006).

| # | Specification | Composición | Candidato | Dónde se usa | RN / CA |
|---|---|---|---|---|---|
| E1 | `RequiereAprobacionGerencial` | `EsCotizacionInicial() & TotalMayorAlUmbral($15,000)` | `Cotizacion` | `Cotizacion.generar` decide el estado inicial; `Cotizacion.corregir` la vuelve a evaluar (v3.1) | RN-04, RN-26 · CA-005, CA-007, CA-016, CA-048, CA-049 |
| E2 | `AutorizanteValido` | `(EsClienteParticular() & AutorizaElCliente()) \| (EsClienteDeFlotilla() & AutorizaSuResponsableDeFlotilla())` | `(Cliente, Autorizante)` | `VerificadorDeAutorizante` antes de registrar la decisión | RN-07 · CA-010, CA-029 |
| E3 | `PuedeEntregarse` | `EstaPagada() \| EstaPorCobrarACredito() \| (EstaCotizada() & TieneRechazoTotal())` | `OrdenDeServicio` | `entregar` y `entregar_sin_reparacion` | RN-18 · CA-041, CA-042, CA-043 |
| E4 | `PuedeCancelarse` | `EstaRecibida() \| EstaEnDiagnostico()` | `OrdenDeServicio` | `cancelar` | RN-19 · CA-044, CA-045 |
| E5 | `PuedeIniciarTrabajo` | `TrabajoPendiente() & AsignadoAlTecnico(id) & ~OrdenPausadaPorRetiro()` | `(OrdenDeServicio, Trabajo)` | `iniciar_trabajo` | RN-14 · CA-014, CA-046 |
| E6 | `PuedeSolicitarRefaccion` | `TrabajoAutorizado() & (OrdenAutorizada() \| OrdenEnReparacion() \| OrdenEnEsperaDeRefaccion())` | `(OrdenDeServicio, Trabajo)` | `crear_solicitud_de_compra` | RN-09 · CA-019, CA-020 |
| E7 | `RequiereAlertaDeRefaccion` | `SolicitudPendiente() & MasDeDiasHabiles(3) & ~ClienteYaAvisado()` | `SolicitudDeCompra` + fecha de revisión | `ServicioDeRevisionDePlazos` | RN-11 · CA-023 |
| E8 | `RequiereRecontacto` | `PendienteDeAutorizacion() & FuePresentada() & MasDeHorasDesdeElUltimoContacto(48)` | `Cotizacion` + fecha de revisión | `ServicioDeRevisionDePlazos` | RN-12, RN-26 · CA-040, CA-051 |

En E2, `AutorizaElCliente` y `AutorizaSuResponsableDeFlotilla` comprueban el rol y el nombre del autorizante, sin distinguir mayúsculas, contra el cliente o su Responsable de Flotilla. *(v3.1, CA-063)* Tampoco cuentan los espacios repetidos ni los de los extremos; los acentos sí cuentan («Luis Pena» no es «Luis Peña»). *(v3.1, CA-064)* Si no se cumple para una flotilla, el mensaje dice la empresa, el nombre del Responsable de Flotilla y el rol con el que se registra la decisión.

En E8, el «último contacto» es la fecha de presentación o el recontacto más reciente **posterior** a ella. Al corregir una cotización la presentación vuelve a quedar vacía (`FuePresentada` no se cumple hasta presentarla otra vez) y los recontactos anteriores se conservan como historial, pero ya no cuentan (v3.1, CA-051).

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
| En Diagnóstico | (mismo estado) | `asignar_tecnico_para_diagnostico` *(v3.1: cambio de técnico)* | sin diagnóstico registrado y empleado con rol Técnico (RN-28) | `TecnicoDeDiagnosticoReasignado` | CA-054 |
| Recibida / En Diagnóstico | (mismo estado) | `corregir_datos_de_recepcion` *(v3.1)* | orden «Recibida» o «En Diagnóstico» (RN-29) | `DatosDeRecepcionCorregidos` | CA-057 |
| Pagada | (mismo estado) | `corregir_forma_de_pago` *(v3.1)* | orden «Pagada»; el monto no cambia (RN-30) | `FormaDePagoCorregida` | CA-058 |

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
- *(v3.1)* Una cotización adicional no se genera mientras otra espera la decisión del cliente (`OperacionDeCotizacionNoPermitida`, RN-33), y una refacción con la misma descripción (sin distinguir mayúsculas ni espacios repetidos) no se vuelve a solicitar para el mismo trabajo mientras su solicitud esté «Solicitada» (`SolicitudNoPermitida`, RN-34). Así un doble clic no duplica nada.
- La salida se registra solo con la orden «En Espera de Refacción». Una nota sin firmar se reemplaza si se registra otra salida y se descarta si la orden sale de la espera.

### 5.2 Cotización (6 estados)

| Desde | Hacia | Disparador | Guarda | Evento | CA |
|---|---|---|---|---|---|
| (inicio) | Pendiente de Aprobación Gerencial | `generar` | E1 se cumple | `CotizacionGenerada`, `AprobacionGerencialRequerida` | CA-007 |
| (inicio) | Pendiente de Autorización del Cliente | `generar` | E1 no se cumple (incluye todas las adicionales) | `CotizacionGenerada` | CA-005, CA-016 |
| Pendiente de Aprobación Gerencial | Pendiente de Autorización del Cliente | `aprobar_por_gerente` | — | `CotizacionAprobadaPorGerente` | CA-008 |
| Pendiente de Aprobación Gerencial | Requiere Ajuste | `rechazar_por_gerente` | observaciones no vacías | `CotizacionRechazadaPorGerente` | CA-009 |
| Requiere Ajuste | Pendiente de Autorización del Cliente | `ajustar` | al menos un trabajo | `CotizacionAjustada` | CA-009 |
| Pendiente de Aprobación Gerencial | (mismo estado) | `corregir` *(v3.1)* | motivo; E1 se sigue cumpliendo | `CotizacionCorregida` | CA-049 |
| Pendiente de Aprobación Gerencial | Pendiente de Autorización del Cliente | `corregir` *(v3.1)* | motivo; E1 ya no se cumple | `CotizacionCorregida` | CA-049 |
| Pendiente de Autorización del Cliente | Pendiente de Aprobación Gerencial | `corregir` *(v3.1, transición nueva)* | motivo; E1 se cumple | `CotizacionCorregida`, `AprobacionGerencialRequerida` | CA-048 |
| Pendiente de Autorización del Cliente | (mismo estado) | `corregir` *(v3.1)* | motivo; E1 no se cumple | `CotizacionCorregida` | CA-047 |
| Pendiente de Autorización del Cliente | (mismo estado) | `marcar_presentada`, `registrar_recontacto` | — | `CotizacionPresentada`, `RecontactoRegistrado` | CA-006, CA-040 |
| Pendiente de Autorización del Cliente | Autorizada | `registrar_decision` (todas las líneas) | E2 | `CotizacionAutorizada` | CA-010 |
| Pendiente de Autorización del Cliente | Autorizada Parcialmente | `registrar_decision` (algunas líneas) | E2 | `CotizacionAutorizada(parcial)` | CA-010 |
| Pendiente de Autorización del Cliente | Rechazada | `registrar_decision` (ninguna línea) | E2 | `CotizacionRechazadaPorCliente` | CA-012, CA-018 |

Estados finales: Autorizada, Autorizada Parcialmente y Rechazada. Aprobar dos veces, presentar una cotización que espera al Gerente o registrar una segunda decisión lanza `OperacionDeCotizacionNoPermitida` (409). Lo mismo ocurre al presentar dos veces (reiniciaría las 48 horas; para eso está el recontacto) o al registrar un recontacto de una cotización que no se ha presentado.

**Corrección (v3.1, H-PIA-21, ADR-018).** `corregir(lineas, motivo, asesor, fecha)` solo se acepta en «Pendiente de Aprobación Gerencial» y «Pendiente de Autorización del Cliente»; en «Requiere Ajuste» responde `OperacionDeCotizacionNoPermitida` pidiendo la cotización ajustada (RN-05 no cambia) y en los estados finales, indicando que el trabajo nuevo va en una cotización adicional. Un motivo vacío es `ValorInvalido` (422). Al corregir: se reemplazan las líneas (al menos un trabajo), se guarda la `CorreccionDeCotizacion`, `fecha_presentacion` vuelve a vacío y se evalúa E1. Si la cotización regresa a «Pendiente de Aprobación Gerencial», `fecha_aprobacion_gerencial` se borra (la anterior queda en el historial); si se queda con el cliente, se conserva. Las observaciones del Gerente se conservan. Una cotización ajustada que se corrige y sigue arriba de $15,000 regresa al Gerente: RN-05 solo protege el ajuste que él pidió y la corrección cambia el monto que revisó (RN-26). Las adicionales nunca cumplen E1, así que siempre se quedan con el cliente.

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
| `TecnicoDeDiagnosticoReasignado` *(v3.1)* | Orden | sale del panel del técnico anterior y aparece en el del nuevo (modelo de lectura) | CA-054 |
| `DiagnosticoRegistrado` | Orden | alerta al asesor: «lista para cotizar» | CA-032 |
| `AprobacionGerencialRequerida` | Cotización (al generar o al corregir) | alerta al Gerente | CA-007, CA-048 |
| `CotizacionAprobadaPorGerente` | Cotización | alerta al asesor: «ya puede presentarse» | CA-008 |
| `CotizacionRechazadaPorGerente` | Cotización | alerta al asesor con las observaciones | CA-009 |
| `CotizacionAutorizada` (adicional) | Cotización | alerta a cada técnico con trabajos asignados en la orden | CA-017 |
| `FallaAdicionalReportada` | Orden | alerta al asesor: «generar cotización adicional» | CA-034 |
| `RefaccionDisponible` | Orden | alertas al técnico y al asesor | CA-022 |
| `OrdenListaParaEntrega` | Orden | alerta al asesor | CA-015 |
| `OrdenCancelada` | Orden | se quita del panel del técnico | CA-044 |
| `CotizacionGenerada`, `CotizacionPresentada`, `RecontactoRegistrado`, `OrdenAutorizada`, `TrabajosAsignados`, `TrabajoIniciado`, `SolicitudDeCompraCreada`, `ClienteAvisadoDelRetraso`, `VehiculoRetirado`, `OrdenReactivada`, `PagoRegistrado`, `CargoACreditoRegistrado`, `VehiculoEntregado`, `CotizacionAjustada`, `CotizacionCorregida`, `DatosDeRecepcionCorregidos`, `FormaDePagoCorregida`, `PlacasCorregidas`, `CotizacionRechazadaPorCliente` | Orden / Cotización | bitácora de eventos (evidencia de la trazabilidad y de las pruebas de transición) | varios |

Las alertas por tiempo (CA-023 y CA-040) no vienen de un evento sino de la revisión periódica de plazos (E7 y E8, ADR-015).

## 7. Errores del dominio

| Error | Cuándo | HTTP (ADR-008) |
|---|---|---|
| `ValorInvalido`, `CotizacionSinTrabajos` | Un dato en sí es inválido (vacío, negativo, cantidad ≤ 0, servicio inhabilitado en los datos de entrada). | 422 |
| `TransicionDeEstadoNoPermitida` | La máquina de estados no permite el cambio. | 409 |
| `OperacionDeCotizacionNoPermitida` | La cotización no está en el estado que exige la acción (también al corregir en «Requiere Ajuste» o después de la decisión, v3.1). | 409 |
| `DiagnosticoRequerido`, `DiagnosticoNoModificable` | RN-02 y RN-03. | 409 |
| `AutorizanteNoValido` | E2 no se cumple. | 409 |
| `TrabajoNoAutorizado`, `SolicitudNoPermitida` | E6 no se cumple, o se intenta asignar trabajos de una orden sin trabajos autorizados (rechazo total, CA-012). | 409 |
| `TrabajoNoPermitido` | E5 no se cumple porque el vehículo está fuera del taller o el trabajo no está pendiente; también al asignar con el vehículo fuera o un trabajo ya iniciado, o al completar con el vehículo fuera. | 409 |
| `TrabajoDeOtroTecnico` | E5 no se cumple porque el trabajo está asignado a otro técnico o a ninguno; también al completar un trabajo ajeno o al registrar un diagnóstico asignado a otro técnico. | 403 |
| `PagoNoPermitido` | Monto distinto del total autorizado o pago de contado de una flotilla. | 409 |
| `EntregaNoPermitida` | E3 no se cumple. | 409 |
| `CancelacionNoPermitida` | E4 no se cumple. | 409 |
| `VehiculoConOrdenAbierta` | *(v3.1)* El vehículo ya tiene una orden abierta (RN-27), también cuando la base rechaza un segundo registro simultáneo. | 409 |
| `CorreccionNoPermitida` | *(v3.1)* Una corrección de la orden fuera del estado que la permite: cambiar el técnico de diagnóstico cuando el diagnóstico ya está registrado (RN-28) corregir la recepción después de la cotización (RN-29), la forma de pago fuera de «Pagada» (RN-30) o, en P2, las placas. | 409 |
| `EmpresaYaRegistrada` | *(v3.1)* Se registra una empresa de flotilla que ya existe con datos distintos de su Responsable de Flotilla; el mensaje dice el nombre y el teléfono del responsable registrado (CA-065). | 409 · Planeado |
| `OrdenNoEncontrada`, `CotizacionNoEncontrada`, `ClienteNoEncontrado`, `VehiculoNoEncontrado`, `EmpleadoNoEncontrado`, `TrabajoNoEncontrado`, `SolicitudNoEncontrada` | El identificador no existe. | 404 |

*(v3.1)* Los errores con **«409 · Planeado»** en la columna HTTP están aprobados (Fase 13) pero todavía no existen en el código; `tests/api/test_errores_http.py` solo compara los demás, y la Fase 14 quita la marca al crear cada uno.

Todos heredan de `ErrorDeDominio` y su mensaje está escrito para el usuario del taller (se devuelve tal cual en el campo `detalle` de la respuesta): dice qué pasó y qué puede hacer, sin términos internos («inhabilitado» es un término de este modelo; el usuario lee «servicios que el taller no ofrece por ahora»).

El mismo error puede tener mensajes distintos según el estado de la orden, para no sugerir acciones que no aplican: `EntregaNoPermitida` no pide el pago de una orden cancelada o cerrada, y `CancelacionNoPermitida` solo sugiere el rechazo total si la orden está «Cotizada» y el cliente aún no decide. El estado solo cambia el texto: el código HTTP y el tipo de error son los de la tabla.
