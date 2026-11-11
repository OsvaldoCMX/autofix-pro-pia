# Revisión de la interfaz como usuario del taller

**Fase 18 del [plan de implementación](../plan-de-implementacion.md)** · Equipo 6 · rama `interfaz-web`

Lista de verificación que el equipo ejecuta **a mano**, en el navegador, como lo haría el profesor: un usuario del taller que se equivoca al capturar, da doble clic y no sabe de computadoras. Cada paso dice qué hacer y qué debe pasar; la columna **«Resultado»** la llena el equipo con «Bien» o con lo que salió (el mensaje exacto, entre comillas). Lo que falle se anota como hallazgo (§7), se corrige y se vuelve a probar.

Las pantallas (P-01, A-01, …) son las de [`interfaz-web.md`](../interfaz-web.md) §4; las filas AU-xx son las de [`auditoria-errores-de-usuario.md`](../auditoria-errores-de-usuario.md).

## 1. Preparación

1. Copiar el repositorio a `C:` (desde la USB `I:`, Docker monta `database/` vacía y la base queda sin tablas).
2. `docker compose up --build` y abrir `http://localhost:8000/` en Chrome. Debe verse la portada (P-01).
3. Las claves de acceso son las de `.env.example` (tabla «Tokens locales» del `README.md`): Asesor Laura Méndez, Técnicos Carlos Ruiz y Diego Salinas, Gerente Patricia Garza, Compras Jorge Treviño y Caja Sofía Leal.
4. La base empieza con las 60 órdenes «Recibida» del profesor (`AUT-O001` a `AUT-O060`). Para repetir la revisión desde cero: `docker compose down -v` y volver a levantar.
5. Para cambiar de puesto: «Cerrar sesión» y entrar con la clave del siguiente.

**Ejecutada por:** ______________________ **Fecha:** ____/____/2026 **Commit revisado:** ______________

## 2. Los 6 escenarios del guion, desde la página

Los mismos escenarios del «Guion de demostración» del `README.md`, pero con los botones de la página en lugar de Swagger.

### 2.1 Orden particular completa (`AUT-O001`, placas `PIAAUT001`)

| # | Puesto | Qué hacer | Qué debe pasar | Resultado |
|---|---|---|---|---|
| 1 | Cliente | P-01 → «Consulta tu vehículo»; orden `AUT-O001`, placas `PIAAUT001`, «Consultar». | Estado «Recibida» en azul, con su frase debajo y las fechas. Nada se puede modificar. | |
| 2 | Asesor | A-01: abrir la orden `AUT-O001` → «Asignar técnico para el diagnóstico» → Carlos Ruiz → confirmar. | Aviso verde; la orden queda «En Diagnóstico». | |
| 3 | Técnico (Carlos) | T-01: la orden aparece en su fila → abrirla → «Registrar diagnóstico» con fallas y recomendaciones. | Aviso verde; el diagnóstico aparece en el expediente. | |
| 4 | Asesor | «Generar cotización»: un trabajo «Cambio de balatas», mano de obra `3000.00` → confirmar. | El total preliminar dice $3,000.00; al guardar, la cotización queda «Pendiente de Autorización del Cliente». | |
| 5 | Asesor | «Presentar cotización al cliente». | Aviso verde. | |
| 6 | Asesor | «Registrar decisión del cliente»: el nombre y el rol ya vienen escritos; marcar el trabajo → «Registrar autorización» → confirmar. | La confirmación dice qué se autoriza; la orden queda «Autorizada». | |
| 7 | Asesor | «Asignar trabajos» → Carlos Ruiz → confirmar. | El trabajo queda asignado a Carlos Ruiz. | |
| 8 | Técnico | «Iniciar trabajo» y después «Terminar trabajo» → confirmar. | La orden pasa a «En Reparación» y después a «Lista para Entrega»; el Asesor recibe la alerta. | |
| 9 | Caja | K-01: buscar `AUT-O001` → «Registrar pago»: el monto ya viene escrito, elegir Tarjeta → confirmar. | «¿Registrar pago de $3,000.00 en Tarjeta?»; la orden queda «Pagada». | |
| 10 | Asesor | «Entregar vehículo» → confirmar. | La confirmación trae folio, placas y cliente; la orden queda «Cerrada». | |
| 11 | Gerente | G-03 «Ingresos del día». | Incluye los $3,000.00. | |

### 2.2 Transiciones inválidas (`AUT-O002`)

En la página estas acciones no se pueden intentar porque sus botones no aparecen; se revisa que no aparezcan.

| # | Puesto | Qué hacer | Qué debe pasar | Resultado |
|---|---|---|---|---|
| 1 | Asesor | Abrir `AUT-O002` («Recibida»). | No aparecen «Entregar vehículo» ni «Generar cotización». Sí aparecen «Asignar técnico para el diagnóstico» y «Cancelar orden». | |
| 2 | Caja | Buscar `AUT-O002`. | No aparece ningún botón de cobro ni de entrega. | |
| 3 | Sin sesión | Escribir en la barra de direcciones `#/asesor/orden/AUT-O002`. | Lleva al inicio de sesión; no muestra la orden. | |

### 2.3 Aprobación gerencial (`AUT-O003`, más de $15,000)

| # | Puesto | Qué hacer | Qué debe pasar | Resultado |
|---|---|---|---|---|
| 1 | Asesor y Técnico | Asignar el diagnóstico de `AUT-O003` y registrarlo (como en 2.1, pasos 2 y 3). | La orden queda «En Diagnóstico» con su diagnóstico. | |
| 2 | Asesor | Generar cotización: «Reparación de motor», mano de obra `20000.00`. | La cotización queda «Pendiente de Aprobación Gerencial»; no aparece «Presentar cotización al cliente». | |
| 3 | Gerente | La campana muestra una alerta nueva; G-01 muestra la cotización con su desglose. | La alerta lleva al expediente de la orden. | |
| 4 | Gerente | «Aprobar» → confirmar. | «¿Aprobar la cotización de $20,000.00 de la orden AUT-O003?»; queda «Pendiente de Autorización del Cliente». | |
| 5 | Asesor | «Presentar cotización al cliente». | Aviso verde. | |

### 2.4 Flotilla con crédito (orden nueva, placas `FLT0001`)

| # | Puesto | Qué hacer | Qué debe pasar | Resultado |
|---|---|---|---|---|
| 1 | Asesor | A-01: buscar `FLT0001` → «Registrar vehículo nuevo» → tipo Flotilla, empresa «Transportes Norte», responsable Ana Torres (teléfono de 10 dígitos), vehículo Nissan NP300 2022, VIN `1HGCM82633A000001`, 80000 km, 3/4, «Servicio de frenos» → «Registrar orden» → confirmar. | La confirmación muestra las placas en letra grande; se abre el expediente de la orden nueva. | |
| 2 | Asesor, Técnico | Diagnóstico, cotización de `3000.00` y presentarla (como en 2.1, pasos 2 a 5). | La cotización queda presentada. | |
| 3 | Asesor | «Registrar decisión del cliente». | Quien decide ya viene escrito: Ana Torres, «Responsable de Flotilla» (no se puede elegir «Cliente»). La orden queda «Autorizada». | |
| 4 | Asesor y Técnico | Asignar, iniciar y terminar el trabajo. | «Lista para Entrega». | |
| 5 | Caja | Buscar la orden. | No aparece «Registrar pago»; aparece «Registrar cargo a crédito» → confirmar → «Por Cobrar (Crédito)». | |
| 6 | Asesor | «Entregar vehículo» → confirmar. | «Cerrada», con la fecha de vencimiento del crédito (15 días). | |

### 2.5 Cancelación

| # | Puesto | Qué hacer | Qué debe pasar | Resultado |
|---|---|---|---|---|
| 1 | Asesor | Abrir `AUT-O004` → «Cancelar orden» con el motivo vacío. | No deja confirmar sin motivo. | |
| 2 | Asesor | Motivo «El cliente desiste» → confirmar. | La confirmación trae folio, placas y motivo; la orden queda «Cancelada». | |
| 3 | Asesor | Abrir `AUT-O003` (ya tiene cotización). | No aparece «Cancelar orden». | |
| 4 | Gerente | G-02 «Órdenes», filtro «Cancelada». | Aparece `AUT-O004`. | |

### 2.6 Consulta pública

| # | Qué hacer | Qué debe pasar | Resultado |
|---|---|---|---|
| 1 | Consultar `AUT-O001` con `PIAAUT001`. | «Cerrada», con su frase debajo. | |
| 2 | Consultar `AUT-O001` con `XXX000`. | Un mensaje que no revela nada de la orden. | |
| 3 | Consultar `aut-o001` (minúsculas, con espacios) y `PIA-AUT-001`. | Se encuentra la orden. | |
| 4 | Dejar vacío el número de orden o las placas. | Pide el dato que falta, sin llamar al sistema. | |

## 3. Filas de prioridad Alta de la auditoría

Intentar el error y anotar **qué mensaje sale**, palabra por palabra.

| # | AU | Qué intentar | Qué debe pasar | Resultado |
|---|---|---|---|---|
| 1 | AU-01 | Registrar una orden con placas `XYZ999` y luego, en el expediente, «Corregir placas» a `XYZ998`. | La confirmación muestra las placas anteriores y las nuevas en letra grande; la consulta pública funciona con `XYZ998`. | |
| 2 | AU-36 | Consultar esa orden con las placas viejas `XYZ999`. | Mensaje de que no coincide. | |
| 3 | AU-02 | A-01 → «Corregir datos del cliente»: cambiar el nombre, el teléfono y el correo. | Se guardan; la decisión del cliente usa el nombre nuevo. | |
| 4 | AU-03 | «Corregir datos del vehículo»: VIN, marca, modelo y año. | Se guardan; las placas no se pueden editar ahí. | |
| 5 | AU-05 | En una orden «Recibida», «Corregir datos de recepción»: kilometraje, combustible y motivo. | Se guardan. En una orden «Autorizada», el botón no aparece. | |
| 6 | AU-06 | Buscar unas placas con una orden abierta. | No aparece «Registrar nueva orden»; aparece «Abrir la orden …». | |
| 7 | AU-06 | Registrar una orden nueva dando doble clic en «Registrar orden» (en la confirmación). | Se abre una sola orden; el botón dice «Guardando…» mientras tanto. | |
| 8 | AU-08 | Teléfono con letras (`81abc12345`), con 7 dígitos y solo con espacios; correo `hola`. | El campo de teléfono no deja escribir letras. Con 7 dígitos: «El teléfono debe tener 10 dígitos; usted escribió 7.» Correo: mensaje que pide la forma nombre@dominio.algo. | |
| 9 | AU-09 | Buscar el año 2099 en la lista de años. | No aparece; el último es el año actual + 1. | |
| 10 | AU-12, AU-13 | Asignar el diagnóstico a Carlos Ruiz y después «Cambiar técnico de diagnóstico» a Diego Salinas. | La lista muestra nombres, no claves; la confirmación dice el nombre; la orden queda con Diego. | |
| 11 | AU-14 | En la decisión del cliente, no marcar ningún trabajo. | «Registrar autorización» está deshabilitado; el rechazo total tiene su propio botón y su propia confirmación. | |
| 12 | AU-17 | Con la cotización «Pendiente de Autorización del Cliente», «Corregir cotización»: cambiar un importe, con motivo. | Confirmación con el total anterior y el nuevo; el historial de correcciones aparece en el expediente. | |
| 13 | AU-17 | Corregir sin motivo. | Pide el motivo. | |
| 14 | AU-18 | Cotización con un trabajo de mano de obra `0.00` y sin refacciones. | La confirmación avisa «el trabajo 1 vale $0.00»; al guardar: «El trabajo 1 vale $0.00: capture su mano de obra o sus refacciones.» | |
| 15 | AU-28 | Técnico: «Solicitar refacción» dos veces con la misma refacción del mismo trabajo. | La segunda se rechaza con un mensaje claro. | |

## 4. Datos absurdos en cada formulario

| # | Formulario | Qué intentar | Qué debe pasar | Resultado |
|---|---|---|---|---|
| 1 | A-02 Nueva orden | Todo vacío → «Registrar orden». | Marca en rojo cada campo obligatorio, con un mensaje que dice qué escribir. | |
| 2 | A-02 | Nombre, marca y motivo con solo espacios. | Cuentan como vacíos. | |
| 3 | A-02 | Kilometraje `-5`, `abc` y `3000000`. | Mensajes claros; no se acepta más de 2,000,000. | |
| 4 | A-02 | VIN de 16 caracteres o con la letra O. | «El VIN debe tener 17 letras y números, sin las letras I, O ni Q.» | |
| 5 | A-02 | Placas `AB#12` o `ÑAB123`. | Mensaje claro sobre las placas. | |
| 6 | A-02 | Pegar un texto de más de 1,000 caracteres en el motivo. | El campo no deja escribir más de 1,000. | |
| 7 | A-05 Cotización | Mano de obra `-1500`. | «La mano de obra no puede ser negativa. Escriba la cantidad en pesos, por ejemplo 1500.00.» | |
| 8 | A-05 | Precio de refacción `-10`. | «El precio de la refacción no puede ser negativo. Escriba la cantidad en pesos, por ejemplo 1500.00.» | |
| 9 | A-05 | Mano de obra `abc`, `1,500.00` y `$1500`. | Un mensaje que pide la cantidad en pesos con el ejemplo 1500.00. | |
| 10 | A-05 | Cantidad de refacción `0`, `-1` y `1.5`. | «Escriba una cantidad de 1 o más.» | |
| 11 | A-05 | Quitar todos los trabajos → guardar. | «Agregue al menos un trabajo.» | |
| 12 | A-05 | Doble clic en «Guardar cotización» de la confirmación. | Se guarda una sola cotización. | |
| 13 | A-05 | Cotización adicional dos veces seguidas. | La segunda se rechaza con un mensaje claro. | |
| 14 | T-02 Diagnóstico | Fallas vacías o solo espacios. | Pide las fallas; las recomendaciones son opcionales. | |
| 15 | T-02 Refacción | Cantidad `0` o vacía. | Mensaje claro. | |
| 16 | T-02 Falla adicional | Doble clic en «Reportar falla al asesor». | Una sola falla y una sola alerta. | |
| 17 | G-01 | «Rechazar con observaciones» con el campo vacío. | Pide las observaciones. | |
| 18 | G-02 | Cambiar el filtro de estado a cada opción. | Solo los 13 estados del Glosario y «Todas». | |
| 19 | K-02 | Intentar cambiar el monto del pago. | Es de solo lectura (AU-35). | |
| 20 | K-02 | Doble clic en «Registrar pago». | Un solo pago; el segundo, si llega, responde que ya estaba registrado. | |
| 21 | C-01 | Doble clic en «Registrar llegada». | Una sola llegada. | |
| 22 | A-01 | Escribir placas (`ABC1234`) en «¿Ya tiene el número de orden?». | «Eso parecen unas placas. Búsquelas arriba, en «Buscar por placas».» | |
| 23 | A-01 | Escribir `os-0001` (minúsculas) en el número de orden. | Abre el expediente (o dice que no existe, si no hay esa orden). | |
| 24 | Todas | Revisar que ningún mensaje tenga códigos (404, 422), inglés, llaves `{ }` ni nombres de clases. | Ninguno. | |

## 5. Sesión, navegación y sin conexión

| # | Qué intentar | Qué debe pasar | Resultado |
|---|---|---|---|
| 1 | Entrar con una clave inventada. | El mensaje de clave inválida de la API; no entra. | |
| 2 | Entrar con la clave de Sistema. | «Esta clave es del sistema automático, no de un empleado del taller…». | |
| 3 | Entrar con cada uno de los 5 puestos. | Saludo «Hola, nombre · puesto», solo el menú de su puesto y la campana. | |
| 4 | Con sesión, recargar la página (F5) en un expediente. | Sigue en la misma pantalla, con la sesión abierta. | |
| 5 | Como Técnico, escribir `#/gerente/ordenes` en la barra de direcciones. | «Esa pantalla es de otro puesto del taller. Le mostramos su menú.» | |
| 6 | «Cerrar sesión» y presionar «Atrás» en el navegador. | No vuelve a mostrar datos del puesto; pide la clave. | |
| 7 | Cerrar la pestaña y abrir de nuevo la página. | Pide la clave otra vez (la sesión se borra al cerrar la pestaña). | |
| 8 | Apagar la API (`docker compose stop app`) y presionar un botón. | «El sistema está iniciando, espere unos segundos e intente de nuevo.» con «Intentar de nuevo». | |
| 9 | Encender la API (`docker compose start app`) y presionar «Intentar de nuevo». | La pantalla carga sin recargar la página. | |
| 10 | Abrir `/docs` y `/health`. | Siguen funcionando igual. | |
| 11 | Ver la página en una tablet o con la ventana angosta (unos 800 px). | Todo se lee y los botones se pueden tocar; nada queda cortado. | |
| 12 | Con alertas en la campana, abrir «Alertas». | El número de la campana queda en 0. | |
| 13 | Provocar una alerta nueva (por ejemplo, el Técnico registra un diagnóstico) y volver a entrar como el Asesor. | La campana cuenta solo la alerta nueva; en «Alertas» esa lleva la etiqueta «Nueva» y las anteriores no. | |
| 14 | Entrar con otro empleado en el mismo navegador. | Su campana cuenta sus propias alertas sin ver (la visita se guarda por empleado). | |
| 15 | Abrir la página en una ventana privada o en otro navegador. | Sin visita guardada, la campana cuenta las alertas de hoy y nada falla. | |

## 6. Aspecto

| # | Qué revisar | Qué debe pasar | Resultado |
|---|---|---|---|
| 1 | Portada (P-01). | Nombre del taller, una frase corta y dos tarjetas grandes con ícono: «Consulta tu vehículo» y «Personal del taller». | |
| 2 | Encabezado y pie de página en todas las pantallas. | Iguales en todas; el pie dice «AutoFix Pro · Sistema de órdenes de servicio del taller». | |
| 3 | Pantalla principal de cada puesto. | Arriba, las opciones del menú del puesto como tarjetas grandes con ícono. | |
| 4 | Colores de los estados. | Los de `interfaz-web.md` §1, siempre con el nombre del estado escrito. | |
| 5 | Botones. | Con verbos claros; nunca «Enviar», «OK» ni «Submit». | |

## 7. Hallazgos del equipo

Lo que encontró el equipo al probar la página. Cada hallazgo se corrige en esta fase y se vuelve a probar aquí.

| # | Pantalla | Qué pasaba | Corrección | Cómo volver a probarlo | Resultado |
|---|---|---|---|---|---|
| H1 | A-01 | Con placas en «Número de orden» salía «No se encontró la orden de servicio ABC1234…», y la pantalla no dejaba claro que lo normal es buscar por placas. | Si el texto no parece un folio, la página dice «Eso parecen unas placas. Búsquelas arriba, en «Buscar por placas».»; el número de orden queda como opción secundaria («¿Ya tiene el número de orden?»). | §4, filas 22 y 23. | |
| H2 | A-02, A-06 | Un teléfono con letras decía «El teléfono debe tener 10 dígitos, por ejemplo 81 1234 5678.» | Dominio: con letras, «El teléfono solo puede llevar números. Escriba los 10 dígitos, sin letras.»; con otra cantidad, «El teléfono debe tener 10 dígitos; usted escribió N.». El campo no deja escribir letras. | §3, fila 8. | |
| H3 | A-05 | El mensaje de un trabajo de $0.00 repetía toda la descripción. | «El trabajo 1 vale $0.00: capture su mano de obra o sus refacciones.» | §3, fila 14. | |
| H4 | A-05 | Un importe negativo decía «Escriba un importe, por ejemplo 1500.00 (sin signo de menos).» | «La mano de obra no puede ser negativa. Escriba la cantidad en pesos, por ejemplo 1500.00.» (y lo mismo para el precio de la refacción y el monto). | §4, filas 7 y 8. | |
| H5 | A-05, G-01 | Después del rechazo del Gerente, el Asesor podía ajustar **subiendo** el total y la cotización iba al cliente sin que el Gerente viera ese monto (hueco de RN-05). | Regla nueva (H-PIA-30): la versión ajustada va al cliente si su total es igual o menor al que rechazó el Gerente; si es mayor, regresa a «Pendiente de Aprobación Gerencial» y se avisa al Gerente. | Cotización de $20,000.00 → el Gerente la rechaza → ajustar a $21,000.00: vuelve al Gerente con alerta. Otra: rechazar $20,000.00 y ajustar a $18,000.00: va al cliente. | |
| H6 | P-04 | La campana seguía mostrando el número aunque el empleado ya hubiera visto las alertas. | La página guarda en `localStorage`, por empleado, cuándo abrió «Alertas» por última vez; la campana cuenta solo las alertas posteriores y queda en 0 al abrirlas; las posteriores a la visita anterior llevan «Nueva». Solo en la página: la API no cambia. | §5, filas 12 a 15. | |
