# Interfaz web — AutoFix Pro

**Fase 13 del [plan de implementación](plan-de-implementacion.md)** · Equipo 6 · 09/11/2026 · rama `interfaz-web` · decisión de arquitectura: [ADR-017](architecture/adr/ADR-017-interfaz-web.md)

Este documento dice **qué pantallas** tiene la página web, qué ve cada usuario, qué botones tiene, en qué estados aparece cada botón, qué ruta de la API llama y qué criterios cubre. La página se construye en las Fases 15 a 17 y se revisa a mano en la Fase 18. Según la regla 1 de `CLAUDE.md`, ninguna pantalla se programa hasta que el equipo apruebe este documento; si una pantalla necesita algo que no está aquí, primero se cambia este documento.

**Estado:** aprobado por el equipo (09/11/2026).

## 1. Principios

1. **Usuario no técnico.** Todo texto va en español sencillo: sin códigos HTTP, sin JSON, sin nombres de clases y sin inglés. Letras y botones grandes, legibles en laptop y en tablet.
2. **Botones con verbos claros.** «Registrar llegada del vehículo», «Presentar cotización al cliente», «Registrar pago»; nunca «Enviar», «OK» ni «Submit».
3. **Nombres del Glosario.** Los estados se muestran con su nombre exacto (`glosario.md` §2), con un color por grupo:

   | Grupo | Estados de la orden | Color |
   |---|---|---|
   | Recepción y diagnóstico | Recibida, En Diagnóstico | azul |
   | Esperando al cliente o al taller | Cotizada, En Espera de Refacción, Pausada por Retiro de Vehículo | ámbar |
   | En trabajo | Autorizada, En Reparación | morado |
   | Lista o cobrada | Lista para Entrega, Pagada, Por Cobrar (Crédito) | verde |
   | Terminada | Cerrada, Cerrada sin Reparación | gris |
   | Cancelada | Cancelada | rojo |

   El color nunca es la única señal: el nombre del estado siempre está escrito.
4. **Formatos.** Montos como `$1,500.00`; fechas como `dd/mm/aaaa hh:mm`, en la hora de Monterrey (America/Monterrey). La API manda los importes como texto (`"1500.00"`) y las fechas en UTC; la página solo les da formato. El dinero se maneja como texto o centavos enteros, **nunca** sumando números decimales de JavaScript.
5. **Confirmación antes de lo que no se deshace.** Un cuadro de confirmación con el folio, las placas y lo que va a pasar, y dos botones: el verbo de la acción y «Regresar». Lo llevan: cancelar la orden, registrar la decisión del cliente, registrar el pago, el cargo a crédito, la entrega y la entrega sin reparación, y las acciones que la auditoría resolvió «solo con la alternativa» (§6).
6. **Contra el doble clic.** Mientras se envía, el botón se deshabilita y dice «Guardando…». Se vuelve a habilitar al recibir la respuesta. Además, la API rechaza los repetidos que importan (CA-052, CA-061, CA-062).
7. **Solo los botones del puesto.** Cada puesto ve solo sus pantallas y sus botones (AU-39). Un botón solo aparece en los estados en los que la acción tiene sentido; si aun así la API rechaza la acción, se muestra su mensaje.
8. **La regla vive en el dominio** (regla 7 de `CLAUDE.md`). Las validaciones de la página (campos obligatorios, números mayores o iguales a 0, listas desplegables, largo máximo) solo ayudan; la API vuelve a validar todo. La página **no decide reglas del negocio**: por ejemplo, puede mostrar un total preliminar mientras se captura una cotización, pero no decide si va al Gerente (E1); eso lo dice la respuesta de la API.
9. **Sin funciones P2.** No aparecen las fotos de daños, los PDF (cotización, Nota de Responsabilidad, recibo interno) ni la corrección de placas mientras sus rutas respondan 501 (decisiones técnicas §8).

## 2. Mensajes

| Situación | Qué ve el usuario |
|---|---|
| Acción exitosa | Un aviso verde arriba de la pantalla: el `mensaje` de la respuesta de la API si lo trae, o uno corto con el folio («Cotización COT-0001 guardada.», «Pago de la orden OS-0007 registrado.»). Después se recarga el expediente o la lista. |
| Error de la API | Un aviso rojo con el **`detalle` tal cual** lo manda la API. La página no lo traduce ni lo cambia: si un mensaje no se entiende, se corrige en el dominio o en `src/api/errores.py` (regla 6 de `CLAUDE.md`). Si el error es de un campo, el campo se marca en rojo. |
| Sin conexión, o Render despertando (no hay respuesta, o la respuesta no es de la API) | «El sistema está iniciando, espere unos segundos e intente de nuevo.» con un botón «Intentar de nuevo». |
| Sesión vencida (la API responde que la clave falta o no es válida en una pantalla del personal) | Regresa al inicio de sesión con el aviso «Su sesión terminó. Escriba de nuevo su clave de acceso.» |
| Lista vacía | Una frase que diga qué significa, por ejemplo «No hay solicitudes pendientes.», «No tiene órdenes asignadas.» |
| Cargando | «Cargando…» en el lugar de la información, sin bloquear la pantalla completa. |

## 3. Sesión y navegación

- **Inicio de sesión:** solo pide la **clave de acceso** del empleado: es el mismo token que ya acepta la API (ADR-012). La página llama `GET /api/sesion`; si la clave es válida, guarda la clave en `sessionStorage` (se borra al cerrar la pestaña) y saluda con el nombre y el puesto: «Hola, Laura Méndez · Asesor de Servicio». Con una clave inválida muestra el `detalle` de la API. La clave de Sistema no tiene pantalla: la API responde que no es de un empleado y la página muestra ese mensaje.
- **Cerrar sesión:** botón siempre visible arriba a la derecha; borra la clave de `sessionStorage` y regresa al inicio.
- **Navegación con `#`** para que recargar la página no dé error: `#/inicio`, `#/consulta`, `#/entrar`, `#/asesor`, `#/asesor/orden/OS-0001`, `#/tecnico`, `#/tecnico/orden/OS-0001`, `#/gerente`, `#/gerente/ordenes`, `#/compras`, `#/caja`, `#/caja/orden/OS-0001` y `#/alertas`. Si un puesto abre una dirección de otro puesto, regresa a su propio menú.
- **Nunca** se escriben claves reales en el código de la página (regla 5 de `CLAUDE.md`).

## 4. Pantallas

Cada pantalla tiene un identificador (P = pública y comunes, A = Asesor, T = Técnico, G = Gerente, C = Compras, K = Caja) para la lista de revisión de la Fase 18.

### 4.1 Públicas y comunes

| ID | Pantalla | Qué ve y qué hace | Ruta de la API | Criterios |
|---|---|---|---|---|
| P-01 | Inicio | Dos botones grandes: «Consulta tu vehículo» y «Entrar como personal del taller». | — | — |
| P-02 | Consulta tu vehículo (sin clave) | Campos «Número de orden» y «Placas», botón «Consultar». Muestra el estado (con su color y, debajo, la frase de §5), la fecha de ingreso y la fecha de la última actualización. No permite modificar nada. Si no coincide, muestra el `detalle` de la API. | `GET /api/consulta-de-estado?orden=&placas=` | CA-037, CA-038 (AU-37) |
| P-03 | Inicio de sesión | Campo «Clave de acceso» (oculta mientras se escribe) y botón «Entrar». Al entrar, el menú de su puesto. | `GET /api/sesion` | — (ADR-017) |
| P-04 | Alertas (todos los empleados) | Campana con el número de alertas en el encabezado; al abrirla, la lista con la fecha y el texto de cada alerta y un enlace a la orden si la trae. | `GET /api/alertas` | CA-007, CA-008, CA-009, CA-015, CA-017, CA-022, CA-023, CA-032, CA-034, CA-040, CA-048 |

### 4.2 Asesor de Servicio

| ID | Pantalla | Qué ve y qué hace | Ruta de la API | Criterios |
|---|---|---|---|---|
| A-01 | Buscar por placas (pantalla principal) | Campo «Placas» y botón «Buscar». Si el vehículo existe, muestra al cliente y al vehículo con los botones «Registrar nueva orden» (abre A-02 con los datos ya escritos), «Corregir datos del cliente» y «Corregir datos del vehículo». Si no existe, el botón «Registrar vehículo nuevo» abre A-02 vacía. También tiene un campo «Número de orden» para abrir un expediente. | `GET /api/vehiculos/{placas}` | CA-003, CA-004 |
| A-02 | Nueva orden | Tres bloques: **Cliente** (tipo Particular o Flotilla; particular: nombre, teléfono y correo; flotilla: empresa, y la página busca la empresa y muestra a su Responsable de Flotilla registrado; si la empresa es nueva, pide los datos del responsable), **Vehículo** (placas, VIN, marca, modelo y año en lista desplegable) y **Recepción** (kilometraje, nivel de combustible en lista desplegable y motivo de ingreso). Botón «Registrar orden» → confirmación con el resumen y las placas en letra grande → abre el expediente de la orden nueva. El cliente particular se registra **junto con la orden** (la página no usa `POST /api/clientes` para particulares, AU-07); la empresa de flotilla nueva se registra antes con `POST /api/clientes`. No hay fotos (P2). | `GET /api/clientes?tipo=Flotilla&empresa=` · `POST /api/clientes` · `POST /api/ordenes` | CA-001, CA-002, CA-028, CA-052, CA-059, CA-065 (AU-01, AU-03, AU-05) |
| A-03 | Expediente de la orden | Encabezado con el folio, el estado y las placas; bloques de cliente, vehículo, recepción, diagnóstico, cotizaciones (cada una con su versión, estado, total, desglose e historial de correcciones), trabajos, solicitudes de compra, fallas adicionales, pago o crédito y entrega. Los botones de la tabla A-03 aparecen según el estado. | `GET /api/ordenes/{numero}` · `GET /api/cotizaciones/{id}` | — (consulta; cada botón lleva sus criterios) |
| A-04 | Decisión del cliente | Lista de los trabajos de la cotización con su importe y una casilla «Autoriza» por trabajo. El nombre y el rol de quien decide los **llena la página** con el cliente (rol «Cliente») o, si es flotilla, con su Responsable de Flotilla (rol «Responsable de Flotilla»); no se escriben a mano (AU-15, AU-16). Si el nombre está mal, primero se corrigen los datos del cliente. Botón «Registrar autorización» (deshabilitado si no hay ningún trabajo marcado) → confirmación «El cliente autoriza: … / No autoriza: …». Botón aparte, «El cliente rechaza todos los trabajos» → confirmación propia (AU-14). | `POST /api/cotizaciones/{id}/decision` | CA-010, CA-012, CA-017, CA-018, CA-029, CA-063, CA-064 |
| A-05 | Generar, ajustar o corregir una cotización | Tabla de trabajos: descripción, mano de obra y refacciones (descripción, cantidad y precio). Muestra un **total preliminar** mientras se captura; el total oficial y si va al Gerente los dice la respuesta de la API. Antes de guardar, aviso si un trabajo vale $0.00. **Generar:** botón «Guardar cotización» → confirmación con el total. **Ajustar** (cotización «Requiere Ajuste»): muestra las observaciones del Gerente y los trabajos actuales; botón «Guardar cotización ajustada». **Corregir** (cotización «Pendiente de Aprobación Gerencial» o «Pendiente de Autorización del Cliente»): trabajos actuales ya escritos y el campo obligatorio «Motivo de la corrección»; aviso «La cotización se volverá a presentar al cliente; si es la inicial y supera $15,000.00, regresará al Gerente.»; botón «Guardar corrección». | `POST /api/ordenes/{numero}/cotizaciones` · `POST /api/ordenes/{numero}/cotizaciones-adicionales` · `PUT /api/cotizaciones/{id}/lineas` · `POST /api/cotizaciones/{id}/correcciones` | CA-005, CA-007, CA-009, CA-016, CA-047 a CA-050, CA-060, CA-061 |
| A-06 | Corregir datos | Tres formularios con los datos actuales ya escritos: **cliente** (nombre, teléfono y correo), **vehículo** (VIN, marca, modelo y año; las placas no se editan aquí) y **recepción** (kilometraje, nivel de combustible y motivo). Botón «Guardar corrección». | `PUT /api/clientes/{id}` · `PUT /api/vehiculos/{placas}` · `PUT /api/ordenes/{numero}/recepcion` | CA-055, CA-056, CA-057 |
| A-07 | Alertas | P-04. Las alertas de «lista para cotizar», «ya puede presentarse», «rechazada por el Gerente», «sin respuesta en 48 horas», «refacción retrasada» y «lista para entrega» llevan a su orden. | `GET /api/alertas` | ver P-04 |

**Botones del expediente (A-03) para el Asesor**

| Botón | Aparece cuando | Confirmación | Ruta | Criterios |
|---|---|---|---|---|
| Asignar técnico para el diagnóstico | Orden «Recibida» | «¿Asignar el diagnóstico de la orden OS-0013 a Carlos Ruiz?» (lista desplegable con los nombres, AU-12, AU-13) | `GET /api/tecnicos` · `POST /api/ordenes/{numero}/asignacion-diagnostico` | CA-035, CA-053 |
| Cambiar técnico de diagnóstico | Orden «En Diagnóstico» sin diagnóstico | La misma, con el técnico nuevo | las mismas | CA-054 |
| Corregir datos de recepción | Orden «Recibida» o «En Diagnóstico» | — | `PUT /api/ordenes/{numero}/recepcion` | CA-057 |
| Corregir datos del cliente / del vehículo | Siempre | — | `PUT /api/clientes/{id}` · `PUT /api/vehiculos/{placas}` | CA-055, CA-056 |
| Generar cotización | Orden «En Diagnóstico» con diagnóstico registrado | Con el total preliminar | `POST /api/ordenes/{numero}/cotizaciones` | CA-005, CA-007, CA-060 |
| Presentar cotización al cliente | Cotización «Pendiente de Autorización del Cliente» sin presentar | — | `POST /api/cotizaciones/{id}/presentacion` | CA-006, CA-051 |
| Registrar recontacto | Cotización «Pendiente de Autorización del Cliente» ya presentada | — (AU-21: solo el botón ocupado) | `POST /api/cotizaciones/{id}/recontactos` | CA-040 |
| Corregir cotización | Cotización «Pendiente de Aprobación Gerencial» o «Pendiente de Autorización del Cliente» | Con el total anterior y el nuevo | `POST /api/cotizaciones/{id}/correcciones` | CA-047 a CA-050 |
| Guardar cotización ajustada | Cotización «Requiere Ajuste» | Con el total | `PUT /api/cotizaciones/{id}/lineas` | CA-009 |
| Registrar decisión del cliente | Cotización «Pendiente de Autorización del Cliente» | En A-04 | `POST /api/cotizaciones/{id}/decision` | CA-010, CA-012, CA-017, CA-018 |
| Asignar trabajos | Trabajos «Pendiente» en una orden «Autorizada», «En Reparación» o «En Espera de Refacción» | «¿Asignar «Cambio de balatas» a Diego Salinas?» | `GET /api/tecnicos` · `POST /api/ordenes/{numero}/asignacion-trabajos` | CA-011, CA-036 |
| Generar cotización adicional | Orden «En Reparación» | Con el total preliminar | `POST /api/ordenes/{numero}/cotizaciones-adicionales` | CA-016, CA-061 |
| Avisar al cliente del retraso | Solicitud «Solicitada» sin aviso registrado | «¿Registrar que avisó al cliente del retraso de «Balata» (orden OS-0022)?» (AU-22) | `POST /api/ordenes/{numero}/solicitudes-de-compra/{id}/aviso-al-cliente` | CA-023 |
| Registrar salida del vehículo | Orden «En Espera de Refacción» | «El cliente se lleva el vehículo antes de terminar la reparación.» | `POST /api/ordenes/{numero}/retiro` | CA-024 |
| Confirmar firma de la Nota de Responsabilidad | Orden «En Espera de Refacción» con la salida registrada | «El cliente firmó la Nota de Responsabilidad y se lleva el vehículo. La orden perderá su lugar en la fila.» (AU-23) | `POST /api/ordenes/{numero}/retiro/firma` | CA-024 |
| Reactivar orden | Orden «Pausada por Retiro de Vehículo» | «El vehículo regresó al taller. La orden quedará al final de la fila.» | `POST /api/ordenes/{numero}/reactivacion` | CA-025 |
| Entregar vehículo | Orden «Pagada» o «Por Cobrar (Crédito)» | Con el folio, las placas y el cliente (AU-24) | `POST /api/ordenes/{numero}/entrega` | CA-041, CA-042 |
| Entregar sin reparación | Orden «Cotizada» con rechazo total | Con el folio, las placas y el cliente | `POST /api/ordenes/{numero}/entrega-sin-reparacion` | CA-043 |
| Cancelar orden | Orden «Recibida» o «En Diagnóstico» | Con el folio, las placas y el motivo obligatorio (AU-25) | `POST /api/ordenes/{numero}/cancelacion` | CA-044, CA-045 |

### 4.3 Técnico

| ID | Pantalla | Qué ve y qué hace | Ruta de la API | Criterios |
|---|---|---|---|---|
| T-01 | Mi fila de trabajo (pantalla principal) | Las órdenes y trabajos que tiene asignados, en el orden de la fila (la más antigua arriba), con el estado de cada uno. | `GET /api/tecnicos/me/panel` | CA-013, CA-035, CA-036, CA-054 |
| T-02 | Orden del técnico | El expediente con los botones de abajo. | `GET /api/ordenes/{numero}` | — |
| T-03 | Alertas | P-04 («refacción disponible», «trabajos de una cotización adicional»). | `GET /api/alertas` | CA-017, CA-022 |

| Botón | Aparece cuando | Confirmación | Ruta | Criterios |
|---|---|---|---|---|
| Registrar diagnóstico | Orden «En Diagnóstico» asignada a él, sin diagnóstico | — (fallas obligatorias; recomendaciones opcionales) | `POST /api/ordenes/{numero}/diagnostico` | CA-032 |
| Corregir diagnóstico | Orden «En Diagnóstico» con diagnóstico (todavía sin cotización); el formulario trae el texto anterior ya escrito (AU-26) | — | `POST /api/ordenes/{numero}/diagnostico` | CA-032, CA-033 |
| Iniciar trabajo | Trabajo «Pendiente» suyo, con el vehículo en el taller | — | `POST /api/ordenes/{numero}/trabajos/{id}/inicio` | CA-014, CA-046 |
| Terminar trabajo | Trabajo «En Progreso» suyo | «¿Terminó el trabajo «Cambio de balatas»?» (AU-30) | `POST /api/ordenes/{numero}/trabajos/{id}/completado` | CA-015 |
| Solicitar refacción | Trabajo suyo «Pendiente» o «En Progreso» en una orden «Autorizada», «En Reparación» o «En Espera de Refacción» | Con el trabajo, la refacción y la cantidad (AU-28) | `POST /api/ordenes/{numero}/solicitudes-de-compra` | CA-019, CA-020, CA-062 |
| Reportar falla adicional | Orden «En Reparación» | «¿Reportar la falla al asesor?» (AU-29: solo el botón ocupado y esta confirmación) | `POST /api/ordenes/{numero}/fallas-adicionales` | CA-034 |

### 4.4 Gerente de Taller

| ID | Pantalla | Qué ve y qué hace | Ruta de la API | Criterios |
|---|---|---|---|---|
| G-01 | Cotizaciones por aprobar (pantalla principal) | Cada cotización con su orden, total, desglose e historial de correcciones. Botón «Aprobar» → confirmación «¿Aprobar la cotización de $20,000.00 de la orden OS-0019?» (AU-31). Botón «Rechazar con observaciones» → campo obligatorio y confirmación (AU-32). | `GET /api/gerencia/cotizaciones-por-aprobar` · `GET /api/cotizaciones/{id}` · `POST /api/cotizaciones/{id}/revision-gerencial` | CA-007, CA-008, CA-009, CA-048, CA-049 |
| G-02 | Órdenes | Lista con folio, placas, estado y fechas; filtro por estado en lista desplegable con los 13 estados del Glosario y «Todas». Al tocar una orden, su expediente **solo para consulta**. | `GET /api/gerencia/ordenes` · `GET /api/ordenes/{numero}` | CA-030 |
| G-03 | Ingresos del día | El total de los pagos de contado de hoy, como `$12,500.00`, y la fecha. | `GET /api/gerencia/ingresos-del-dia` | CA-031 |
| G-04 | Alertas | P-04 («cotización por aprobar»). | `GET /api/alertas` | CA-007, CA-048 |

### 4.5 Personal de Compras

| ID | Pantalla | Qué ve y qué hace | Ruta de la API | Criterios |
|---|---|---|---|---|
| C-01 | Solicitudes pendientes (pantalla principal) | Folio de la orden, refacción, cantidad, fecha de solicitud y días hábiles transcurridos (las de más de 3 días, resaltadas). Botón «Registrar llegada» → confirmación con la orden, la refacción y la cantidad (AU-33). Compras no abre el expediente (la API no se lo permite). | `GET /api/compras/solicitudes-pendientes` · `POST /api/ordenes/{numero}/solicitudes-de-compra/{id}/llegada` | CA-021, CA-022 |
| C-02 | Alertas | P-04. | `GET /api/alertas` | — |

### 4.6 Personal de Caja

| ID | Pantalla | Qué ve y qué hace | Ruta de la API | Criterios |
|---|---|---|---|---|
| K-01 | Buscar orden (pantalla principal) | Campo «Número de orden». Muestra el folio, el cliente y su tipo, el estado, el total autorizado y, si ya hay, el pago o el crédito. | `GET /api/ordenes/{numero}` | — |
| K-02 | Cobrar | Botones según el tipo de cliente, abajo. | ver abajo | CA-026, CA-039, CA-058 |
| K-03 | Alertas | P-04. | `GET /api/alertas` | — |

| Botón | Aparece cuando | Confirmación | Ruta | Criterios |
|---|---|---|---|---|
| Registrar pago | Cliente particular, orden «Lista para Entrega» | El monto viene **ya escrito** con el total autorizado que manda la API (AU-35) y la forma de pago se elige de una lista: «¿Registrar pago de $3,000.00 en Tarjeta?» | `POST /api/ordenes/{numero}/pago` | CA-026 |
| Registrar cargo a crédito | Cliente de flotilla, orden «Lista para Entrega» | «¿Registrar cargo a crédito de $3,000.00 para Transportes Norte?» | `POST /api/ordenes/{numero}/cargo-a-credito` | CA-039 |
| Corregir forma de pago | Orden «Pagada» | «¿Cambiar la forma de pago de Efectivo a Tarjeta?» | `PUT /api/ordenes/{numero}/pago` | CA-058 |

El recibo interno en PDF (CA-027) no aparece: es P2 y su ruta responde 501.

### 4.7 Sin pantalla

- **Sistema:** la revisión de plazos (`POST /api/revisiones/plazos`) la llama el workflow programado; no tiene pantalla.
- **Funciones P2:** fotos de daños, PDF de la cotización, de la Nota de Responsabilidad y del recibo, y la corrección de placas (`PUT /api/ordenes/{numero}/placas`) no aparecen mientras respondan 501.
- **Swagger** (`/docs`) sigue disponible para la parte técnica.

## 5. Frase debajo del estado (consulta del cliente, AU-37)

En la consulta pública, debajo del estado se muestra una frase tomada del «Significado» de `glosario.md` §2, escrita para el cliente:

| Estado | Frase |
|---|---|
| Recibida | Recibimos su vehículo y abrimos su orden de servicio. |
| En Diagnóstico | Un técnico está revisando su vehículo. |
| Cotizada | La cotización está lista; el taller le dará los detalles para que decida. |
| Autorizada | Usted autorizó los trabajos; pronto empezaremos la reparación. |
| En Reparación | Estamos reparando su vehículo. |
| En Espera de Refacción | Estamos esperando una pieza para continuar. |
| Pausada por Retiro de Vehículo | Usted se llevó el vehículo mientras llega una pieza; al regresarlo continuamos. |
| Lista para Entrega | Su vehículo está listo. Puede pasar a pagar y recogerlo. |
| Pagada | El pago está registrado; puede recoger su vehículo. |
| Por Cobrar (Crédito) | El servicio se cargó al crédito de su empresa; puede recoger el vehículo. |
| Cerrada | Su vehículo ya fue entregado. ¡Gracias por su visita! |
| Cerrada sin Reparación | Su vehículo se entregó sin reparación, sin costo. |
| Cancelada | La orden se canceló a petición suya, sin costo. |

## 6. Lo que resuelve la página (auditoría «solo la alternativa»)

| AU | Hueco | Cómo lo resuelve la página | Pantalla |
|---|---|---|---|
| AU-07 | Doble clic al registrar un cliente particular | El particular se registra junto con la orden; la página no usa `POST /api/clientes` para particulares. | A-02 |
| AU-14 | Una decisión sin trabajos marcados se registra como rechazo total | Confirmación con lo autorizado y lo no autorizado, y un botón aparte para el rechazo total. | A-04 |
| AU-21 | Doble clic en «Registrar recontacto» | Botón ocupado mientras se envía. | A-03 |
| AU-22 | Aviso de retraso de la solicitud equivocada | Confirmación con la refacción y la orden. | A-03 |
| AU-23 | Firma de la nota confirmada por error | Confirmación que avisa que la orden pierde su lugar en la fila. | A-03 |
| AU-24, AU-25 | Entregar o cancelar la orden equivocada | Confirmación con folio, placas y cliente (y el motivo, al cancelar). | A-03 |
| AU-26 | Diagnóstico mal descrito | «Corregir diagnóstico» con el texto anterior ya escrito. | T-02 |
| AU-29 | Doble clic en «Reportar falla adicional» | Botón ocupado y confirmación. | T-02 |
| AU-30 | Trabajo terminado por error | Confirmación «¿Terminó el trabajo…?». | T-02 |
| AU-31, AU-32 | El Gerente aprueba o rechaza por error | Confirmación con el monto y la orden. | G-01 |
| AU-33 | Llegada registrada de la solicitud equivocada | Confirmación con la orden, la refacción y la cantidad. | C-01 |
| AU-35 | Monto del pago mal escrito | El monto viene ya escrito con el total autorizado. | K-02 |

También ayudan, aunque la regla vive en el dominio: los campos de teléfono y correo, la lista desplegable de años y el máximo del kilometraje (AU-08 a AU-10), el `maxlength` de los textos (AU-11), el nombre y el rol del autorizante llenados por la página (AU-15, AU-16), la lista de técnicos con nombres (AU-12, AU-13) y que los identificadores de las direcciones los arme la página, no el usuario (AU-38).

## 7. Datos que la página necesita y la API todavía no da

Según el plan (Fases 16 y 17), si una pantalla necesita un dato que la API no da, se agrega a la API con su prueba y se documenta en `scripts/docs/rutas.py`; la página no lo adivina ni lo calcula.

| Dato | Lo necesita | Dónde se agregaría |
|---|---|---|
| Nombre y tipo del cliente (y su Responsable de Flotilla), marca, modelo y año del vehículo | A-03, A-04, K-01, K-02 (pago o crédito según el tipo) | Expediente `GET /api/ordenes/{numero}` (hoy solo trae `id_cliente` y `placas`). **Se agrega en la Fase 14** (punto 5 de su orden de prioridad). |
| Historial de correcciones de la cotización | A-03, G-01 | `GET /api/cotizaciones/{id}` y el expediente (lo agrega la Fase 14 con H-PIA-21) |
| Nombre del técnico asignado | A-03, G-02 | Hoy el expediente trae la clave (`EMP-002`). **Se agrega al expediente en la Fase 14** (punto 5), junto con los datos del cliente y del vehículo. |
| Nombre y puesto del empleado de la clave | P-03 | `GET /api/sesion` (Fase 15) |

## 8. Estructura de archivos (Fase 15)

`src/api/web/`: `index.html`, `estilos.css` y módulos JavaScript: `api.js` (todas las llamadas, la clave y el manejo de errores en un solo lugar), `sesion.js`, `formato.js` (dinero y fechas), `ui.js` (mensajes, confirmaciones y botones ocupados) y uno por puesto: `asesor.js`, `tecnico.js`, `gerente.js`, `compras.js`, `caja.js` y `cliente.js`. Sin Node, sin npm y sin paso de compilación (ADR-017).
