# Auditoría «¿y si me equivoco?» — AutoFix Pro

**Fase 12 del [plan de implementación](plan-de-implementacion.md)** · Equipo 6 · 09/11/2026 · rama `interfaz-web`

## 1. Propósito y método

En la revisión del 09/11/2026 vimos que el profesor usa el sistema **como un usuario del taller**: se equivoca al capturar, da doble clic, escribe números negativos y espera un mensaje que entienda alguien que no sabe de computadoras. Esta auditoría busca esos huecos **antes** de construir la página web. No cambia código: solo propone. El equipo marca en la columna **«¿Se hace?»** qué propuestas pasan a la Fase 13.

**Qué se revisó.** Los documentos que pide la Fase 12 (`user-stories.md`, `gherkin/*.feature`, `glosario.md`, `api/README.md`, `architecture/modelo-de-dominio.md`) y el código de `src/domain`, `src/application/servicios`, `src/api/esquemas`, `src/api/errores.py` y `src/api/seguridad.py`. También se revisaron los repositorios para las placas y el VIN repetidos.

**Cómo se comprobó cada caso.**

- **Leyendo el código.** La columna «Qué hace hoy» lleva el archivo y la línea, con rutas desde la raíz del repositorio.
- **Probándolo.** Un script temporal, fuera del repositorio, armó la API igual que `tests/api/conftest.py`: SQLite en memoria, tokens falsos y sin leer `.env`. Ejecutó 209 casos y anotó la respuesta de cada uno. Los mensajes entre comillas son el `detalle` **exacto** que manda la API. La clave de prueba (R01, C07…) indica de qué caso salió. Al terminar, el script se borró.

**Columnas de las tablas.**

| Columna | Significado |
|---|---|
| ¿Se corrige? | **Sí**: el usuario puede corregir el error con lo que ya existe. **Parcial**: hay una salida indirecta (cancelar, abrir otra orden…). **No**: el dato queda mal para siempre. |
| ¿Mensaje claro? | **Sí**: dice qué pasó y qué hacer. **A medias**: dice qué pasó, pero no qué hacer, o usa palabras técnicas. **Sin mensaje**: el sistema acepta el error en silencio. |
| Prioridad | **Alta**: el profesor lo puede encontrar en una demo de 10 minutos. **Media**: es raro. **Baja**: es cosmético. |
| Tamaño | **Chico**: solo validación o mensaje. **Mediano**: método nuevo en el dominio, o ruta y caso de uso nuevos, con sus pruebas. **Grande**: tabla nueva o cambio en la máquina de estados. |
| Alternativa barata | Lo que puede hacer la página para que el error casi no ocurra: botón deshabilitado mientras se envía (contra el doble clic), confirmación antes de guardar, lista desplegable en lugar de texto libre o un dato llenado por la página. **Ojo (regla 7 de `CLAUDE.md`):** la página solo ayuda; quien use Swagger puede seguir mandando el dato malo. Si el hueco es de una regla del negocio, la regla va en el dominio. |
| ¿Se hace? | La llena el equipo: **Sí**, **No** o **Solo la alternativa**. |

## 2. Resumen: huecos de prioridad Alta

**H-PIA-21 · Corregir una cotización mal capturada (AU-17).** El equipo ya la decidió el 09/11/2026 y es el hueco que vio el profesor. Es **Grande**: transición nueva en la máquina de la cotización y tabla de historial. Va en la Fase 13 sin importar el orden de abajo.

El resto, ordenado **de más importante y más barato a menos importante y más caro**:

| # | ID | Hueco | Tamaño | Alternativa barata | ¿Se hace? |
|---|---|---|---|---|---|
| 1 | AU-14 | Si el asesor no marca ningún trabajo, se registra un rechazo total que no se puede deshacer. | Grande en el dominio · nada si se usa la alternativa | Confirmación que diga «El cliente autoriza: … / no autoriza: …» y un botón aparte para «El cliente rechaza todos los trabajos». | |
| 2 | AU-06 | El doble clic en «Registrar orden» abre dos órdenes del mismo vehículo. | Mediano | Botón deshabilitado mientras se envía y, al terminar, abrir el expediente de la orden nueva. | |
| 3 | AU-28 | El doble clic en «Solicitar refacción» crea dos solicitudes, y una solicitud hecha por error no se puede quitar. | Chico (no aceptar la misma solicitud pendiente dos veces) · Grande (cancelar una solicitud) | Botón deshabilitado y confirmación con el trabajo, la refacción y la cantidad. | |
| 4 | AU-08 | Teléfono y correo aceptan cualquier cosa («abc», «hola», solo espacios). | Chico | Campos de tipo teléfono y correo en la página. | |
| 5 | AU-09 | Se acepta un vehículo del año 2099. | Chico | Lista desplegable de años. | |
| 6 | AU-18 | Se puede generar una cotización de $0.00. | Chico (falta que el equipo decida la regla) | Aviso antes de guardar si un trabajo vale $0.00. | |
| 7 | AU-02 | El nombre, teléfono o correo del cliente mal escritos no se pueden corregir; con un nombre mal escrito, la decisión del cliente solo se acepta con ese mismo error. | Mediano (el método del dominio ya existe) | La página llena sola el nombre de quien autoriza (ver AU-15). | |
| 8 | AU-03 | El VIN, la marca, el modelo o el año mal capturados no se pueden corregir sin abrir otra orden. | Mediano (el método del dominio ya existe; puede ir en la misma pantalla que AU-02) | Confirmación con todos los datos antes de registrar la orden. | |
| 9 | AU-13 | No hay una ruta que liste a los técnicos: el asesor tendría que escribir la clave del empleado (`EMP-002`). | Mediano (consulta y ruta nuevas) | Ninguna sin inventar datos en la página. | |
| 10 | AU-12 | El técnico de diagnóstico equivocado no se puede cambiar. | Mediano | Lista desplegable con nombres (necesita AU-13) y confirmación «¿Asignar a Carlos Ruiz?». | |
| 11 | AU-05 | El kilometraje, el nivel de combustible y el motivo de ingreso mal capturados no se pueden corregir. | Mediano | Confirmación con el resumen antes de registrar la orden. | |
| 12 | AU-01 | Unas placas mal capturadas no se corrigen nunca: el VIN queda ocupado y el cliente no puede consultar con sus placas reales. | Mediano, el más delicado: cambia la llave del vehículo en dos tablas | Confirmación con las placas en letra grande antes de registrar. | |

## 3. Tablas por actor

### 3.1 Asesor de Servicio

| ID | Paso | Error posible del usuario | Qué hace hoy el sistema (archivo y línea) | ¿Se corrige? | ¿Mensaje claro? | Propuesta | Prioridad | Tamaño | Alternativa barata | ¿Se hace? |
|---|---|---|---|---|---|---|---|---|---|---|
| AU-01 | Registrar la orden (vehículo nuevo) | Placas mal capturadas (`XYZ999` en lugar de `XYZ998`). | Las placas son la identidad del vehículo y ningún método las cambia (`src/domain/vehiculos/vehiculo.py:11-40`). Si se vuelve a registrar con las placas correctas y el mismo VIN: «Ya existe un vehículo con el VIN 1HGCM82633A000002. Revise el dato capturado.» (`src/infrastructure/base_de_datos/repositorios.py:359-369`, R02). El cliente consulta con sus placas reales y recibe «No se encontró una orden con esos datos…» (R02). | No | A medias: no dice qué hacer, porque no hay salida. | Acción «Corregir placas» mientras la orden esté «Recibida» o «En Diagnóstico»: cambia las placas del vehículo y de sus órdenes. | Alta | Mediano (cambia la llave en `vehiculos` y en `ordenes`) | Confirmación con las placas en letra grande antes de guardar. | |
| AU-02 | Registrar la orden (datos del cliente) | Nombre, teléfono o correo mal escritos. | Solo se corrigen al abrir **otra** orden del mismo vehículo (`src/application/servicios/servicio_de_recepcion.py:68-88`); no hay ruta para editar al cliente. `Cliente.actualizar_contacto` ya existe (`src/domain/clientes/cliente.py:62-66`). Con el nombre mal escrito, la decisión del cliente se rechaza hasta que se escriba ese mismo error (`src/domain/clientes/especificaciones.py:13-14, 27-32`). | Parcial | Sin mensaje (el error pasa en silencio) | Ruta «Corregir datos del cliente» que use `actualizar_contacto`. | Alta | Mediano | La página llena sola el nombre en la decisión (AU-15). | |
| AU-03 | Registrar la orden (datos del vehículo) | VIN, marca, modelo o año mal capturados. | Igual que AU-02: solo con otra orden (`servicio_de_recepcion.py:80-87`). `Vehiculo.actualizar_datos` ya existe (`vehiculo.py:34-40`). | Parcial | Sin mensaje | Ruta «Corregir datos del vehículo» que use `actualizar_datos` (puede ir en la misma pantalla que AU-02). | Alta | Mediano | Confirmación con todos los datos antes de registrar. | |
| AU-04 | Registrar un cliente de flotilla | Responsable de Flotilla mal escrito, o la empresa cambió de responsable. | Nunca se corrige. Si se registra otra vez la misma empresa, el sistema devuelve la empresa existente e **ignora sin avisar** los datos nuevos del responsable (`servicio_de_recepcion.py:120-125`). Prueba R13: se mandó «Ana Torres Ruiz» y la respuesta trae `responsable_nombre: "Ana Torres"`. | No | Sin mensaje | (a) Avisar que la empresa ya existe y mostrar el responsable registrado. (b) Método `actualizar_responsable` en `Cliente` con su ruta. | Media | (a) Chico · (b) Mediano | Al escribir la empresa, la página la busca (`GET /api/clientes?tipo=Flotilla&empresa=`) y muestra el responsable registrado antes de guardar. | |
| AU-05 | Registrar la orden (estado de recepción) | Kilometraje, nivel de combustible o motivo de ingreso mal capturados. | Se fijan al crear la orden y ningún método los cambia (`src/domain/ordenes/orden_de_servicio.py:73-77`; `EstadoDeRecepcion` es inmutable, `src/domain/ordenes/valores.py:28-38`). | No | Sin mensaje | Método `corregir_datos_de_recepcion` mientras la orden esté «Recibida» o «En Diagnóstico». | Alta | Mediano | Confirmación con el resumen antes de registrar. | |
| AU-06 | Registrar la orden | Doble clic en «Registrar», o registrar dos veces el mismo vehículo. | Se abren dos órdenes «Recibida» del mismo vehículo: OS-0001 y OS-0002 (R01). No se revisa si el vehículo ya tiene una orden abierta (`servicio_de_recepcion.py:30-47`). | Parcial (se cancela la segunda con motivo, CA-044) | Sin mensaje | Regla nueva (la decide el equipo): un vehículo no puede tener dos órdenes abiertas. Mensaje sugerido: «El vehículo con placas XYZ998 ya tiene abierta la orden OS-0001 (estado «Recibida»). Ábrala en lugar de registrar otra.» | Alta | Mediano (consulta nueva en los dos repositorios) | Botón deshabilitado mientras se envía y, al terminar, abrir el expediente de la orden. | |
| AU-07 | Registrar un cliente particular (`POST /api/clientes`) | Doble clic. | Se crean dos clientes con los mismos datos: CLI-0010 y CLI-0011 (R14, `servicio_de_recepcion.py:120-136`). | No (no se borran) | Sin mensaje | Ninguna en el dominio: la página registra al cliente particular junto con la orden y no usa esta ruta. | Baja | — | Que la página no use esta ruta para particulares. | |
| AU-08 | Datos del cliente y del Responsable | Teléfono «abc», correo «hola», o solo espacios. | Se aceptan (R03): solo se revisa el largo (`src/api/esquemas/recepcion.py:29-30`, `src/domain/clientes/cliente.py:53-54`). El Responsable de Flotilla solo exige que no estén vacíos (`cliente.py:24-30`). | Parcial (con AU-02) | Sin mensaje | Validar en el dominio: un teléfono con 10 dígitos (se permiten espacios, guiones y paréntesis) y un correo con forma `nombre@dominio.algo`; solo espacios equivale a vacío. Mensajes del tipo «El teléfono debe tener 10 dígitos, por ejemplo 81 1234 5678.» | Alta | Chico | Campos de tipo teléfono y correo en la página. | |
| AU-09 | Datos del vehículo | Año imposible (2099). | Se acepta (R05): el rango es 1900–2100, igual que el `CHECK` de la base (`vehiculo.py:7-8, 23`; `src/api/esquemas/comunes.py:22-23`). 1899 sí se rechaza con un mensaje claro. | Parcial (con AU-03) | Sin mensaje (para 2099) | En el dominio: máximo el año actual + 1 (modelos del año siguiente). El `CHECK` de la base puede quedarse igual. | Alta | Chico | Lista desplegable de años. | |
| AU-10 | Estado de recepción | Kilometraje absurdo (2,000,000,000). | Se acepta (R06): el único tope es el del tipo `INTEGER` (`comunes.py:38`). Los negativos y las letras sí se rechazan con mensaje claro. | No (con AU-05, sí) | Sin mensaje | Tope razonable en el dominio (por ejemplo 2,000,000 km; el número lo decide el equipo). | Media | Chico | Campo numérico con máximo. | |
| AU-11 | Textos libres | Texto larguísimo (100,000 caracteres en el motivo de ingreso). | Se acepta (R11). No tienen límite el motivo de ingreso (`recepcion.py:54`), la descripción del trabajo (`src/api/esquemas/cotizaciones.py:30`), las observaciones del Gerente (`cotizaciones.py:52`), las fallas y recomendaciones (`src/api/esquemas/diagnostico.py:15-16`), la falla adicional (`diagnostico.py:20`) ni el motivo de cancelación (`src/api/esquemas/cancelacion.py:8`). En la base son `TEXT`. | — | Sin mensaje | Largo máximo en el esquema (por ejemplo 1,000). El mensaje ya existe: «El dato «…» no puede tener más de N caracteres.» | Baja | Chico | `maxlength` en los campos de la página. | |
| AU-12 | Asignar técnico para el diagnóstico | Se eligió al técnico equivocado. | Al intentar cambiarlo: «Solo se asigna técnico de diagnóstico a una orden «Recibida»; la orden OS-0013 está en «En Diagnóstico».» (D03, `orden_de_servicio.py:143-151`; la máquina solo permite Recibida → En Diagnóstico, `src/domain/ordenes/estados.py:44`). | No (solo se puede cancelar la orden) | A medias: no dice qué hacer | Método `reasignar_tecnico_de_diagnostico` mientras la orden esté «En Diagnóstico» y sin diagnóstico. No cambia de estado, así que no toca la máquina. | Alta | Mediano | Lista desplegable con nombres (necesita AU-13) y confirmación «¿Asignar a Carlos Ruiz?». | |
| AU-13 | Asignar técnico (diagnóstico o trabajos) | Clave del técnico mal escrita (`EMP-999`, `emp-002`). | Ninguna de las 43 rutas lista a los técnicos (`docs/api/README.md`). Con una clave mal escrita: «No se encontró el empleado EMP-999. Revise la clave e intente de nuevo.» (D01). Con la clave en minúsculas tampoco se encuentra (D02). | Sí | Sí (pero obliga a saber claves de memoria) | **Hallazgo para la Fase 13:** ruta para listar a los técnicos (clave y nombre). Se decide junto con `GET /api/sesion`. | Alta | Mediano | Ninguna sin inventar datos en la página (regla 1 de `CLAUDE.md`). | |
| AU-14 | Registrar la decisión del cliente | Marcó los trabajos equivocados, o no marcó ninguno. | Una lista vacía se registra como **rechazo total** sin preguntar: cotización «Rechazada» (A06). Ninguna decisión se puede deshacer: la segunda responde «No se puede registrar la decisión de la cotización v.1 porque está en «Autorizada Parcialmente»; …» (A04, `src/domain/cotizaciones/cotizacion.py:151-174`; los tres estados de decisión son finales). | No | Sin mensaje (el error se acepta) | Corregir la decisión en el dominio sería Grande (estados finales y trabajos ya creados en la orden). Se recomienda **solo la alternativa barata**. | Alta | Grande (dominio) · nada (alternativa) | Confirmación que diga qué se autoriza y qué no, y un botón aparte, «El cliente rechaza todos los trabajos». | |
| AU-15 | Registrar la decisión del cliente | Nombre de quien autoriza escrito distinto: sin acento («Luis Pena») o con doble espacio. | 409: «La decisión debe registrarse a nombre del cliente Luis Peña.» (A01). Con «Luis  Peña» (doble espacio) sale el mismo mensaje, aunque los dos nombres **se ven iguales** (`especificaciones.py:13-14` solo ignora mayúsculas). | Sí (escribiéndolo igual) | A medias (con doble espacio, confunde) | Ignorar los espacios repetidos al comparar. Ignorar acentos es un cambio de regla (E2) y lo decide el equipo. | Media | Chico | La página llena sola el nombre (del cliente o de su Responsable de Flotilla) a partir del expediente. | |
| AU-16 | Registrar la decisión (flotilla) | Escribió bien al Responsable, pero eligió el rol «Cliente». | 409: «Para la flotilla de Transportes Norte solo puede autorizar su Responsable de Flotilla; el conductor no puede autorizar.» (A05, `src/domain/servicios/verificador_de_autorizante.py:21-25`). Habla del conductor aunque el problema es el rol, y no dice el nombre del responsable. | Sí | A medias | Mensaje: «Para la flotilla de Transportes Norte, registre la decisión a nombre de su Responsable de Flotilla, Ana Torres, con el rol «Responsable de Flotilla».» | Media | Chico | La página fija el rol según el tipo de cliente. | |
| AU-17 | Corregir una cotización (**H-PIA-21**) | Importe o descripción mal capturados en una cotización que espera al Gerente o al cliente. | `ajustar` solo funciona en «Requiere Ajuste»: «No se puede ajustar la cotización v.1 porque está en «Pendiente de Autorización del Cliente»; debe estar en «Requiere Ajuste».» (C10, C14; `cotizacion.py:123-128`, `src/domain/cotizaciones/estados.py:27`). | No | A medias: el usuario no puede poner la cotización en «Requiere Ajuste» | Ya decidida por el equipo (09/11/2026; ver la Fase 13 del plan). | Alta | Grande (transición nueva y tabla de historial) | Confirmación con el total antes de generar la cotización. | |
| AU-18 | Generar cotización | Total de $0.00 (mano de obra de cero y sin refacciones). | Se acepta: COT-0001 con total «0.00» (C07; `src/domain/cotizaciones/linea_de_cotizacion.py:37-41` y `comunes.py:24` aceptan 0.00). | Parcial (con H-PIA-21) | Sin mensaje | Regla (la decide el equipo; ¿hay trabajos sin costo, por ejemplo garantías?): cada trabajo vale más de $0.00. | Alta | Chico | Aviso antes de guardar si un trabajo vale $0.00. | |
| AU-19 | Capturar importes (cotización y pago) | Importe negativo, sin decimales («1500»), con comas («1,500.00») o con signo de pesos. | Todos responden lo mismo: «El dato «mano de obra del trabajo 1» debe ser un importe con dos decimales, por ejemplo "1500.00".» (C02, K02; `src/api/errores.py:44-46, 53`). Con un negativo no dice que el importe no puede ser negativo. «1500» es un importe válido para el usuario. | Sí | A medias | En `api/errores.py`: si el dato empieza con «-», responder «El dato «…» no puede ser negativo.» | Media | Chico | La página usa un campo numérico y siempre envía el importe con dos decimales. | |
| AU-20 | Generar cotización adicional | Doble clic. | Se crean v.2 y v.3 iguales, las dos pendientes (F11). La orden no queda lista hasta decidir las dos (`orden_de_servicio.py:204-207`; `src/application/servicios/servicio_de_cotizacion.py:52-69`). | Parcial (se registra el rechazo total de la repetida) | Sin mensaje | Regla (la decide el equipo): no se genera otra adicional mientras haya una sin decisión. | Media | Chico | Botón deshabilitado mientras se envía. | |
| AU-21 | Registrar recontacto | Doble clic. | Se guardan dos recontactos (C12, `cotizacion.py:141-149`). Solo queda en el historial y no cambia el plazo de 48 horas. | — | Sin mensaje | Ninguna. | Baja | — | Botón deshabilitado. | |
| AU-22 | Avisar al cliente del retraso de una refacción | Registró el aviso de la solicitud equivocada. | No se puede deshacer y ya no vuelve a salir la alerta de esa solicitud (`src/domain/ordenes/solicitud_de_compra.py:50-56`). El doble clic sí responde: «El aviso al cliente ya estaba registrado.» (F07). | No | Sí | Ninguna en el dominio. | Baja | — | Confirmación con la refacción y la orden. | |
| AU-23 | Retiro anticipado: confirmar la firma | Confirmó la firma por error. | La orden pasa a «Pausada por Retiro de Vehículo» y sale de la fila (T02). Se puede reactivar, pero queda **al final de la fila** (`orden_de_servicio.py:351-379`). | Parcial | Sí | Ninguna en el dominio (deshacerlo sería una transición nueva). | Media | Grande (dominio) | Confirmación: «El cliente firmó la Nota de Responsabilidad y se lleva el vehículo. La orden perderá su lugar en la fila.» | |
| AU-24 | Entregar el vehículo, con o sin reparación | Entregó la orden equivocada. | «Cerrada» y «Cerrada sin Reparación» son estados finales (`orden_de_servicio.py:415-439`). La segunda entrega responde «El vehículo de la orden OS-0027 ya fue entregado; no hay nada más que registrar.» (E02). | No | Sí | Ninguna en el dominio. | Media | Grande (dominio) | Confirmación con el folio, las placas y el cliente (ya prevista en la Fase 13). | |
| AU-25 | Cancelar la orden | Canceló la orden equivocada. | «Cancelada» es un estado final (`orden_de_servicio.py:441-448`); la segunda cancelación responde «La orden OS-0029 ya está cancelada.» (X02). | Parcial (se registra otra orden; el vehículo y el cliente se reutilizan) | Sí | Ninguna en el dominio. | Media | Grande (dominio) | Confirmación con el folio, las placas y el motivo (ya prevista en la Fase 13). | |

**Pasos del Asesor revisados sin hueco.** Los mensajes de estos casos ya dicen qué pasó y qué hacer:

- Placas vacías, con «#» o «Ñ», o de más de 15 caracteres (R08).
- Placas con guiones, espacios o minúsculas: se normalizan (R08, R15).
- VIN de 16 o 18 caracteres o con «O» (R09).
- Nombre, marca o motivo con solo espacios (R04, R10, R11).
- Kilometraje negativo o con letras (R06).
- Nivel de combustible fuera de la lista (R07).
- Placas nuevas sin los datos del vehículo (R12).
- Cliente inexistente (R12).
- Placas de otro cliente: lo revela la lectura del código (`servicio_de_recepcion.py:72-76`).
- Cotizar sin diagnóstico (C01).
- Doble clic al generar la cotización inicial (C08).
- Trabajos repetidos o sin descripción, y refacción con cantidad 0 (C04 a C06).
- Total mayor al máximo (C09).
- Presentar dos veces o mientras espera al Gerente (C11, C14).
- Recontacto antes de presentar (C11).
- Asignar trabajos no autorizados, vacíos o inexistentes (P01, P02).
- Reasignar un trabajo pendiente (P03, permitido) o uno ya iniciado (P06).
- Cancelar una orden cotizada, en reparación o con rechazo total (A06, X04, X05).
- Entregar sin pago, o con «Entregar sin reparación» en lugar de la entrega normal (K05, E01, E03).
- Reactivar dos veces y registrar la salida dos veces (T02 y T04; la nota sin firmar se reemplaza).

### 3.2 Técnico

| ID | Paso | Error posible del usuario | Qué hace hoy el sistema (archivo y línea) | ¿Se corrige? | ¿Mensaje claro? | Propuesta | Prioridad | Tamaño | Alternativa barata | ¿Se hace? |
|---|---|---|---|---|---|---|---|---|---|---|
| AU-26 | Registrar el diagnóstico | Se equivocó al describir las fallas. | Antes de cotizar puede registrarlo otra vez y se reemplaza (D06; `orden_de_servicio.py:153-169`). Después, por RN-03, el mensaje es claro: «El diagnóstico ya no se puede modificar porque la cotización fue generada; los hallazgos nuevos se registran como falla adicional.» | Sí | Sí | Ninguna en el dominio. La página debe mostrar «Corregir diagnóstico» con el texto anterior ya escrito. | Baja | — | Formulario con el diagnóstico anterior ya escrito. | |
| AU-27 | Registrar el diagnóstico | Dejó vacío el campo de recomendaciones. | La API exige el campo: «Falta el dato «recomendaciones». Captúrelo e intente de nuevo.» (D05, `diagnostico.py:16`), aunque el dominio sí acepta recomendaciones vacías (`valores.py:53`). | Sí | Sí | Valor por omisión vacío en el esquema, para que la API y el dominio digan lo mismo. | Baja | Chico | La página siempre envía el campo. | |
| AU-28 | Solicitar una refacción | Doble clic, o pidió una pieza por error. | Se crean dos solicitudes iguales y Compras ve las dos (F01, F05). No existe forma de cancelar una solicitud: la máquina de la solicitud solo tiene «Solicitada» → «Disponible» (`solicitud_de_compra.py:41-48`, `orden_de_servicio.py:289-315`). La orden se queda «En Espera de Refacción» hasta que Compras registre una llegada que no ocurrió. | No | Sin mensaje | (a) Regla: no aceptar la misma refacción del mismo trabajo si ya hay una solicitud «Solicitada». (b) Estado nuevo para cancelar una solicitud. | Alta | (a) Chico · (b) Grande | Botón deshabilitado y confirmación con el trabajo, la refacción y la cantidad. | |
| AU-29 | Reportar una falla adicional | Doble clic, o la reportó por error. | Se guardan dos fallas y el asesor recibe dos alertas (F10, `orden_de_servicio.py:171-183`). No se pueden borrar. | No | Sin mensaje | Ninguna en el dominio: la falla solo avisa; el asesor decide si cotiza. | Baja | — | Botón deshabilitado. | |
| AU-30 | Completar un trabajo | Lo marcó como completado por error. | Un trabajo «Completado» no regresa. Si era el último, la orden pasa a «Lista para Entrega» y avisa al asesor (`orden_de_servicio.py:274-286, 621-629`). | No | Sin mensaje (se acepta) | Ninguna en el dominio. | Media | Grande (dominio) | Confirmación: «¿Terminó el trabajo «Cambio de balatas»?». | |

**Pasos del Técnico revisados sin hueco.**

- Fallas con solo espacios (D05).
- Diagnóstico de una orden asignada a otro técnico (D04): «El diagnóstico de esta orden está asignado a otro técnico.»
- Diagnóstico con la orden «Recibida» (D07).
- Iniciar un trabajo de otro técnico (P04).
- Iniciar dos veces (P05).
- Completar sin iniciar (P05).
- Iniciar con el vehículo fuera del taller (T03).
- Cantidad 0, negativa o con decimales (F02).
- Refacción sin descripción (F03).
- Trabajo inexistente (F04).
- Falla adicional fuera de «En Reparación» (F10).
- Completar el último trabajo con refacciones pendientes (mensaje en `orden_de_servicio.py:279-282`).

### 3.3 Gerente de Taller

| ID | Paso | Error posible del usuario | Qué hace hoy el sistema (archivo y línea) | ¿Se corrige? | ¿Mensaje claro? | Propuesta | Prioridad | Tamaño | Alternativa barata | ¿Se hace? |
|---|---|---|---|---|---|---|---|---|---|---|
| AU-31 | Revisar una cotización mayor a $15,000 | La aprobó, pero quería rechazarla. | No se puede cambiar: «No se puede rechazar la cotización v.1 porque está en «Pendiente de Autorización del Cliente»; debe estar en «Pendiente de Aprobación Gerencial».» (G04, `cotizacion.py:108-121`). Con H-PIA-21, el asesor podrá corregirla y la cotización regresa al Gerente si sigue arriba de $15,000. | Parcial (con H-PIA-21) | A medias: no dice qué hacer | Ninguna aparte de H-PIA-21. | Media | — | Confirmación «¿Aprobar la cotización de $20,000.00 de la orden OS-0019?». | |
| AU-32 | Revisar una cotización mayor a $15,000 | La rechazó por error. | Queda «Requiere Ajuste»; el asesor la «ajusta» con las mismas líneas y pasa al cliente sin volver al Gerente (G06, RN-05). | Sí | Sí | Ninguna. | Baja | — | Confirmación. | |

**Pasos del Gerente revisados sin hueco.**

- Rechazar sin observaciones o con solo espacios (G01).
- Aprobar dos veces (G04).
- Revisar una cotización que no espera al Gerente (G05).
- Filtro de estado inventado o en minúsculas (G07): el mensaje lista los 13 estados. Es largo pero claro, y en la página será una lista desplegable.
- Ingresos del día sin pagos: «0.00» (G08).

### 3.4 Personal de Compras

| ID | Paso | Error posible del usuario | Qué hace hoy el sistema (archivo y línea) | ¿Se corrige? | ¿Mensaje claro? | Propuesta | Prioridad | Tamaño | Alternativa barata | ¿Se hace? |
|---|---|---|---|---|---|---|---|---|---|---|
| AU-33 | Registrar la llegada de una refacción | Registró la llegada de la solicitud equivocada. | No se puede deshacer: la solicitud queda «Disponible», avisa al técnico y al asesor y, si era la última, la orden sale de la espera (`solicitud_de_compra.py:41-48`, `orden_de_servicio.py:317-332`). El doble clic sí responde: «La llegada de la refacción «Balata» ya estaba registrada.» (F06). | No | Sí (el doble clic) · sin mensaje (la equivocada) | Ninguna en el dominio (deshacerlo sería la transición «Disponible» → «Solicitada»). | Media | Grande (dominio) | Confirmación con la orden, la refacción y la cantidad. | |

**Pasos de Compras revisados sin hueco.**

- Solicitud inexistente o de otra orden (F06): «La orden OS-0022 no tiene la solicitud de compra 1.»
- La lista de pendientes muestra el folio, la refacción, la cantidad, la fecha y los días hábiles (F05).
- Compras no puede abrir el expediente de la orden (S05, 403); está bien según el contrato de la API.

### 3.5 Personal de Caja

| ID | Paso | Error posible del usuario | Qué hace hoy el sistema (archivo y línea) | ¿Se corrige? | ¿Mensaje claro? | Propuesta | Prioridad | Tamaño | Alternativa barata | ¿Se hace? |
|---|---|---|---|---|---|---|---|---|---|---|
| AU-34 | Registrar el pago de contado | Eligió la forma de pago equivocada (Tarjeta en lugar de Efectivo). | No se puede cambiar: el segundo intento responde «La orden OS-0027 ya tiene su pago registrado.» (K06, `orden_de_servicio.py:382-399`). Los ingresos del día no cambian (no dependen de la forma de pago), pero el recibo y el expediente quedan mal. | No | Sí (pero no hay salida) | Método `corregir_forma_de_pago` mientras la orden esté «Pagada» (antes de entregar). | Media | Mediano | Confirmación: «Registrar pago de $3,000.00 en Tarjeta». | |
| AU-35 | Registrar el pago de contado | Monto mal escrito. | Se rechaza con un mensaje claro que da el total: «El monto no coincide: el pago debe cubrir el total autorizado de $3,000.00 MXN. Corríjalo e intente de nuevo.» (K02). Un negativo o «3000» sin decimales caen en AU-19. | Sí | Sí | Ninguna. | Baja | — | La página muestra el total autorizado ya escrito. | |

**Pasos de Caja revisados sin hueco.**

- Cobrar antes de «Lista para Entrega» (K01).
- Pago de contado a una flotilla, o crédito a un particular (K04, K07): cada mensaje dice qué registrar en su lugar.
- Forma de pago fuera de la lista (K03).
- Doble clic en el pago o en el crédito (K06, K07).

### 3.6 Cliente (consulta pública)

| ID | Paso | Error posible del usuario | Qué hace hoy el sistema (archivo y línea) | ¿Se corrige? | ¿Mensaje claro? | Propuesta | Prioridad | Tamaño | Alternativa barata | ¿Se hace? |
|---|---|---|---|---|---|---|---|---|---|---|
| AU-36 | Consultar el estado de su vehículo | Sus placas reales no coinciden con las que capturó el asesor. | «No se encontró una orden con esos datos. Revise el número de orden y las placas e intente de nuevo.» (R02). El cliente no puede hacer nada: el error es del taller (AU-01). | No (depende de AU-01) | Sí, para el cliente | La resuelve AU-01. | Alta (junto con AU-01) | — | — | |
| AU-37 | Consultar el estado | No entiende el nombre de un estado («Por Cobrar (Crédito)», «Pausada por Retiro de Vehículo»). | Se muestra el nombre del estado tal cual (CA-037). | — | A medias | Mostrar, debajo del estado, una frase tomada del «Significado» de `glosario.md` §2. Se define en `docs/interfaz-web.md` (Fase 13). | Baja | Chico (solo la página) | — | |

**Pasos del Cliente revisados sin hueco.**

- Folio en minúsculas con espacios y placas con guion: se encuentra la orden (Q02).
- Datos que no coinciden (Q03): no revela nada.
- Placas con caracteres raros (Q04).
- Folio vacío o sin placas (Q05, Q06).

## 4. Datos absurdos (todas las pantallas)

| Tipo de dato absurdo | Dónde se probó | Resultado | Hueco |
|---|---|---|---|
| Negativos | Kilometraje (R06), mano de obra (C02), precio de refacción (C06), monto del pago (K02), cantidad (F02) | Se rechazan siempre. Con importes, el mensaje no dice «negativo». | AU-19 |
| Ceros | Mano de obra 0.00 (C07), cantidad 0 (C06, F02), número de trabajo 0 (C05), kilometraje 0 | Se acepta una cotización de $0.00; las cantidades y los números en 0 se rechazan; un kilometraje de 0 es válido (auto nuevo). | AU-18 |
| Textos vacíos o solo espacios | Nombre (R04), marca (R10), motivo (R11), fallas (D05), descripción del trabajo (C04), refacción (C06, F03), observaciones (G01), motivo de cancelación (X01), falla adicional (F10), teléfono y correo (R03) | Todos se rechazan con mensaje claro, **menos el teléfono y el correo**. | AU-08 |
| Textos larguísimos | Motivo de 100,000 caracteres (R11); nombre de 121, teléfono de 21 y marca de 61 (R03, R04, R10) | Los campos con límite se rechazan con mensaje claro; los de tipo `TEXT` aceptan cualquier largo. | AU-11 |
| Años imposibles | 1899 (R05), 2099 (R05), «dos mil» y 2020.5 (R05) | 2099 se acepta; los demás se rechazan con mensaje claro. | AU-09 |
| Importes con más de 2 decimales | 1500.005 (C02) | Se rechaza con el mensaje de AU-19. | AU-19 (solo el mensaje) |
| Importes enormes | 99999999999.00 (C02); suma de 9,999,999,999.99 + 1.00 (C09) | Se rechazan: «El importe es mayor al máximo permitido. Revise la cantidad capturada.» | — |
| Letras donde van números | Kilometraje (R06), año (R05), cantidad (F02), número de trabajo en la dirección (P07) | «El dato «…» debe ser un número entero.» En la dirección, el dato se llama «número de registro» (`api/errores.py:102`); la página nunca arma esa dirección con letras. | AU-38 |
| Placas con caracteres raros | «AB#12», «ÑAB123», 16 letras, solo espacios (R08) | Se rechazan con mensaje claro; guiones, espacios y minúsculas se normalizan. | — |
| Kilometrajes enormes | 2,000,000,000 (R06) | Se acepta. | AU-10 |

## 5. Inventario de mensajes de error

Los mensajes del dominio (`src/domain/compartido/errores.py` y los que arma cada Aggregate) y los de `src/api/errores.py`, revisados como los leería alguien que no sabe de computadoras. Los que ya dicen qué pasó y qué hacer se agrupan; los que fallan llevan su propio hueco.

| Mensaje (o familia de mensajes) | Ejemplo real | ¿Dice qué pasó? | ¿Dice qué hacer? | Hueco |
|---|---|---|---|---|
| Datos que faltan o que exceden su largo (`api/errores.py:49-51`) | «Falta el dato «motivo». Captúrelo e intente de nuevo.» | Sí | Sí | — |
| Números fuera de rango (`api/errores.py:54-61`) | «El dato «kilometraje» no puede ser menor que 0. Corríjalo e intente de nuevo.» | Sí | Sí | — |
| Opciones de una lista (`api/errores.py:64`) | «El dato «forma de pago» debe ser una de estas opciones: «Efectivo», «Tarjeta» o «Transferencia».» | Sí | Sí | — |
| Importe con formato incorrecto (`api/errores.py:44-46`) | «… debe ser un importe con dos decimales, por ejemplo "1500.00".» | A medias (negativo) | Sí | AU-19 |
| Dato desconocido (`api/errores.py:50`) | «El dato «color» no se reconoce. Quítelo e intente de nuevo.» | Sí | Sí | — (solo pasa desde Swagger) |
| Identificador en la dirección (`api/errores.py:102`) | «El dato «número de registro» debe ser un número entero.» | A medias | No | AU-38 |
| Sin clave o con clave inválida (`api/errores.py:131-134`) | «No pudimos identificarlo: falta su clave de acceso o no es válida. Revísela e intente de nuevo.» | Sí | Sí | — |
| Función de otro puesto (`api/errores.py:143`) | «Su rol no tiene permiso para usar esta función. Pida apoyo al área encargada.» | A medias («rol») | A medias («área encargada») | AU-39 |
| JSON mal formado y ruta inexistente (`api/errores.py:70-82`) | «La información enviada no tiene el formato correcto. Revísela e intente de nuevo.» | Sí | Sí | — |
| No encontrado, con folio (repositorios) | «No se encontró la orden de servicio OS-9999. Revise el número e intente de nuevo.» | Sí | Sí | — |
| Estado que no permite la acción (orden) | «Todavía no se puede cobrar la orden OS-0025: debe estar «Lista para Entrega» y ahora está en «En Reparación».» | Sí | Sí | — |
| Estado que no permite la acción (cotización, `cotizacion.py:213-218`) | «No se puede ajustar la cotización v.1 porque está en «Pendiente de Autorización del Cliente»; debe estar en «Requiere Ajuste».» | Sí | No: el usuario no puede poner la cotización en ese estado | AU-17, AU-31 |
| Técnico de diagnóstico ya asignado (`orden_de_servicio.py:144-148`) | «Solo se asigna técnico de diagnóstico a una orden «Recibida»; la orden OS-0013 está en «En Diagnóstico».» | Sí | No | AU-12 |
| VIN repetido (`repositorios.py:366-369`) | «Ya existe un vehículo con el VIN 1HGCM82633A000002. Revise el dato capturado.» | Sí | A medias: si el VIN está bien, no hay salida | AU-01 |
| Autorizante (`verificador_de_autorizante.py:21-28`) | «Para la flotilla de Transportes Norte solo puede autorizar su Responsable de Flotilla; el conductor no puede autorizar.» | A medias | No dice el nombre del responsable | AU-15, AU-16 |
| Pago, crédito, entrega y cancelación (`orden_de_servicio.py:536-605`) | «Las órdenes de flotilla no se pagan de contado: registre el cargo a crédito.» | Sí | Sí | — |
| Trabajo de otro técnico (`orden_de_servicio.py:503-508`) | «El trabajo «Trabajo 1» no está asignado a usted. Solicite que se lo asignen.» | Sí | Sí | — |
| Vehículo fuera del taller (`orden_de_servicio.py:510-515`) | «El vehículo de la orden OS-0026 no está en el taller: se retiró con Nota de Responsabilidad. Cuando regrese, reactive la orden para continuar.» | Sí | Sí | — |
| Función P2 (Fase 10 omitida) | «El PDF del recibo interno todavía no está disponible.» | Sí | — | — (la página no muestra funciones P2) |

Dos huecos de mensajes que no tienen fila en las tablas por actor:

| ID | Paso | Error posible del usuario | Qué hace hoy el sistema (archivo y línea) | ¿Se corrige? | ¿Mensaje claro? | Propuesta | Prioridad | Tamaño | Alternativa barata | ¿Se hace? |
|---|---|---|---|---|---|---|---|---|---|---|
| AU-38 | Cualquier acción con un identificador en la dirección | Trabajo o solicitud «0» o con letras. | «El dato «número de registro» no puede ser menor que 1.» (P07, `src/api/errores.py:102`). | Sí | A medias («número de registro») | Nombrarlo «número de trabajo o de solicitud», según la ruta. | Baja | Chico | La página arma la dirección con el identificador del expediente; el usuario nunca lo escribe. | |
| AU-39 | Usar una función de otro puesto | Un técnico intenta registrar una orden, o Compras intenta abrir el expediente. | «Su rol no tiene permiso para usar esta función. Pida apoyo al área encargada.» (S03, S05, D08, G03; `src/api/errores.py:143`). | — | A medias | «Esta función es de otro puesto del taller. Pida a la persona encargada que la realice.» | Baja | Chico | La página solo muestra los botones del puesto que inició sesión. | |

## 6. Siguiente paso

La fase se detiene aquí. El equipo llena la columna **«¿Se hace?»**. Lo aprobado se documenta en la Fase 13 (`docs/interfaz-web.md`, criterios desde CA-047, reglas desde RN-25 y hallazgos desde **H-PIA-21**, que hoy solo está anotado en esta auditoría y se agrega a `registro-de-cambios.md` en esa fase). AU-13 (ruta para listar a los técnicos) se decide en la Fase 13 junto con `GET /api/sesion`.
