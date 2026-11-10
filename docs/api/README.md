# API REST — contrato planeado (PIA)

Contrato de la API que se implementa con FastAPI (ADR-008). Cuando la API esté lista, FastAPI genera el contrato real en `/openapi.json` y Swagger UI en `/docs`; se exporta una copia a `docs/api/openapi.json` (`python -m api.exportar_openapi` o `curl http://localhost:8000/openapi.json -o docs/api/openapi.json`).

## Convenciones

- Base: `http://localhost:8000` (Docker Compose) y la URL de Render en producción. Prefijo `/api`.
- Autenticación: `Authorization: Bearer <token>` del empleado (ADR-012). Públicas: `/health`, `/docs`, `/openapi.json`, `/api/consulta-de-estado`.
- Errores con el formato `{"error": "<TipoDeError>", "detalle": "<mensaje para el usuario>", "codigo": <http>}`.
- **201** crea · **200** acción o consulta · **400** JSON mal formado · **401** sin token o token inválido · **403** rol no permitido o trabajo de otro técnico · **404** no existe · **409** regla o transición violada · **422** dato inválido · **501** función P2 aún no implementada.
- Además de los errores que lista cada ruta, cualquier ruta con cuerpo JSON responde **400** si está mal formado, y cualquier ruta que reciba datos (cuerpo, ruta o parámetros) responde **422** si uno es inválido. FastAPI lee el JSON antes de revisar el token: un JSON mal formado responde 400 aunque falte el token.
- Importes como texto con dos decimales (`"1500.00"`); fechas ISO 8601 con zona horaria.
- **Planeado** en la columna Prioridad: la ruta está aprobada (Fase 13, revisión del 09/11/2026) y todavía no existe en la API; la Fase 14 quita la marca al construirla (`tests/api/test_contrato.py` comprueba que una ruta planeada aún no exista).

## Rutas (51)

### Sesión

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/sesion` | Cualquier empleado | Nombre y puesto del empleado de la clave de acceso (la usa la página al iniciar sesión, ADR-017). El token de Sistema responde 403: no es un empleado. | 200 | 401, 403 | `ConsultarSesion` | — | P1 · Planeado |

### Sistema

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| GET | `/health` | Público | Salud del servicio (lo usa Render y Docker Compose). | 200 | — | — | — | P1 |
| POST | `/api/revisiones/plazos` | Sistema | Revisión de plazos de 3 días hábiles y 48 h (la llama un workflow programado). | 200 | 401, 403 | `ServicioDeRevisionDePlazos.revisar` | CA-023, CA-040, CA-051 | P1 |

### Recepción

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/vehiculos/{placas}` | Asesor | Buscar vehículo y cliente por placas. | 200 | 401, 403, 404 | `BuscarVehiculoPorPlacas` | CA-003, CA-004 | P1 |
| PUT | `/api/vehiculos/{placas}` | Asesor | Corregir el VIN, la marca, el modelo o el año del vehículo (las placas no cambian). | 200 | 401, 403, 404, 409, 422 | `ServicioDeRecepcion.corregir_vehiculo` | CA-056 | P1 · Planeado |
| GET | `/api/clientes?tipo=Flotilla&empresa=` | Asesor | Buscar la empresa de flotilla y su Responsable. | 200 | 401, 403 | `BuscarClientes` | CA-028 | P1 |
| POST | `/api/clientes` | Asesor | Registrar cliente particular o de flotilla (con Responsable). *Planeado (H-PIA-28):* 409 si la empresa ya está registrada con otro responsable. | 201 | 400, 401, 403, 422 | `ServicioDeRecepcion.registrar_cliente` | CA-028, CA-059, CA-065 | P1 |
| PUT | `/api/clientes/{id}` | Asesor | Corregir el nombre, el teléfono o el correo del cliente. | 200 | 401, 403, 404, 422 | `ServicioDeRecepcion.corregir_cliente` | CA-055 | P1 · Planeado |
| POST | `/api/ordenes` | Asesor | Registrar la orden: cliente, vehículo, motivo, kilometraje y combustible. Si las placas ya existen, reutiliza el registro y actualiza los datos enviados. *Planeado (H-PIA-22):* 409 si el vehículo ya tiene una orden abierta. | 201 | 400, 401, 403, 404, 422 | `ServicioDeRecepcion.registrar_orden` | CA-001, CA-002, CA-004, CA-052, CA-059 | P1 |
| POST | `/api/ordenes/{numero}/fotos` | Asesor | Adjuntar foto de daños (multipart). | 201 | 401, 403, 404, 422 | `ServicioDeRecepcion.adjuntar_foto` | CA-002 | P2 |
| GET | `/api/ordenes/{numero}` | Asesor, Gerente, Técnico, Caja | Expediente completo de la orden (estado, cotizaciones, trabajos, solicitudes, pagos). *Planeado (Fase 14):* también el nombre y el tipo del cliente (y su Responsable de Flotilla), la marca, el modelo y el año del vehículo y el nombre del técnico de diagnóstico y de cada trabajo (`interfaz-web.md` §7). | 200 | 401, 403, 404 | `ConsultarExpedienteDeOrden` | — | P1 |
| PUT | `/api/ordenes/{numero}/recepcion` | Asesor | Corregir el kilometraje, el nivel de combustible o el motivo de ingreso (orden «Recibida» o «En Diagnóstico»). | 200 | 401, 403, 404, 409, 422 | `ServicioDeRecepcion.corregir_recepcion` | CA-057 | P1 · Planeado |
| PUT | `/api/ordenes/{numero}/placas` | Asesor | Corregir las placas mal capturadas (orden «Recibida» o «En Diagnóstico»). Mientras responda 501 no aparece en la página. | 200 | 401, 403, 404, 409, 422 | `ServicioDeRecepcion.corregir_placas` | CA-066 | P2 · Planeado |

### Cancelación

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/ordenes/{numero}/cancelacion` | Asesor | Cancelar la orden con motivo (solo sin cotización). | 200 | 401, 403, 404, 409, 422 | `ServicioDeCancelacion.cancelar` | CA-044, CA-045 | P1 |

### Diagnóstico

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/ordenes/{numero}/asignacion-diagnostico` | Asesor | Asignar técnico para el diagnóstico. *Planeado (H-PIA-23):* también lo cambia mientras no haya diagnóstico. | 200 | 401, 403, 404, 409, 422 | `ServicioDeDiagnostico.asignar_tecnico` | CA-035, CA-054 | P1 |
| POST | `/api/ordenes/{numero}/diagnostico` | Técnico | Registrar el diagnóstico (fallas y recomendaciones). | 201 | 401, 403, 404, 409, 422 | `ServicioDeDiagnostico.registrar_diagnostico` | CA-032, CA-033 | P1 |
| POST | `/api/ordenes/{numero}/fallas-adicionales` | Técnico | Reportar una falla adicional durante la reparación. | 201 | 401, 403, 404, 409, 422 | `ServicioDeDiagnostico.reportar_falla_adicional` | CA-034 | P1 |
| GET | `/api/tecnicos/me/panel` | Técnico | Órdenes y trabajos asignados, en orden de la fila. | 200 | 401, 403 | `ConsultarPanelDelTecnico` | CA-013, CA-035, CA-036, CA-054 | P1 |
| GET | `/api/tecnicos` | Asesor | Técnicos del taller (clave y nombre) para asignarlos. | 200 | 401, 403 | `ListarTecnicos` | CA-053 | P1 · Planeado |

### Cotización

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/ordenes/{numero}/cotizaciones` | Asesor | Generar la cotización inicial (v.1). | 201 | 401, 403, 404, 409, 422 | `ServicioDeCotizacion.generar_inicial` | CA-005, CA-007, CA-060 | P1 |
| POST | `/api/ordenes/{numero}/cotizaciones-adicionales` | Asesor | Generar una cotización adicional (v.2, v.3…). | 201 | 401, 403, 404, 409, 422 | `ServicioDeCotizacion.generar_adicional` | CA-016, CA-060, CA-061 | P1 |
| GET | `/api/cotizaciones/{id}` | Asesor, Gerente | Detalle de la cotización con su desglose, su estado y su historial de correcciones (H-PIA-21). | 200 | 401, 403, 404 | `ConsultarCotizacion` | CA-005 | P1 |
| GET | `/api/cotizaciones/{id}/pdf` | Asesor | PDF de la cotización. | 200 | 401, 403, 404 | `ServicioDeCotizacion.generar_pdf` | CA-005 | P2 |
| POST | `/api/cotizaciones/{id}/presentacion` | Asesor | Marcar como presentada (inicia las 48 h). | 200 | 401, 403, 404, 409 | `ServicioDeCotizacion.presentar` | CA-006, CA-007, CA-051 | P1 |
| POST | `/api/cotizaciones/{id}/revision-gerencial` | Gerente | Aprobar o rechazar (con observaciones) una cotización mayor a $15,000. | 200 | 401, 403, 404, 409, 422 | `ServicioDeAprobacionGerencial.revisar` | CA-008, CA-009 | P1 |
| PUT | `/api/cotizaciones/{id}/lineas` | Asesor | Guardar la cotización ajustada según el Gerente. | 200 | 401, 403, 404, 409, 422 | `ServicioDeCotizacion.ajustar` | CA-009 | P1 |
| POST | `/api/cotizaciones/{id}/correcciones` | Asesor | Corregir una cotización que espera al Gerente o al cliente (motivo obligatorio; guarda el historial y vuelve a evaluar la regla de $15,000). | 201 | 401, 403, 404, 409, 422 | `ServicioDeCotizacion.corregir` | CA-047, CA-048, CA-049, CA-050 | P1 |
| POST | `/api/cotizaciones/{id}/recontactos` | Asesor | Registrar el recontacto al cliente (48 h). | 201 | 401, 403, 404, 409 | `ServicioDeCotizacion.registrar_recontacto` | CA-040 | P1 |
| GET | `/api/gerencia/cotizaciones-por-aprobar` | Gerente | Cotizaciones en «Pendiente de Aprobación Gerencial». | 200 | 401, 403 | `ListarCotizacionesPendientesDeAprobacion` | CA-007 | P1 |

### Autorización

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/cotizaciones/{id}/decision` | Asesor | Registrar la decisión del cliente o del Responsable de Flotilla. | 200 | 401, 403, 404, 409, 422 | `ServicioDeAutorizacion.registrar_decision` | CA-010, CA-012, CA-017, CA-018, CA-029, CA-063, CA-064 | P1 |

### Reparación

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/ordenes/{numero}/asignacion-trabajos` | Asesor | Asignar trabajos autorizados a un técnico. | 200 | 401, 403, 404, 409, 422 | `ServicioDeReparacion.asignar_trabajos` | CA-011, CA-012, CA-036 | P1 |
| POST | `/api/ordenes/{numero}/trabajos/{id}/inicio` | Técnico | Pasar un trabajo a «En Progreso». | 200 | 401, 403, 404, 409 | `ServicioDeReparacion.iniciar_trabajo` | CA-014, CA-046 | P1 |
| POST | `/api/ordenes/{numero}/trabajos/{id}/completado` | Técnico | Pasar un trabajo a «Completado». | 200 | 401, 403, 404, 409 | `ServicioDeReparacion.completar_trabajo` | CA-015 | P1 |

### Refacciones

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/ordenes/{numero}/solicitudes-de-compra` | Técnico | Crear solicitud de compra de una refacción no disponible. | 201 | 401, 403, 404, 409, 422 | `ServicioDeRefacciones.solicitar` | CA-019, CA-020, CA-062 | P1 |
| GET | `/api/compras/solicitudes-pendientes` | Compras | Solicitudes «Solicitada» con días hábiles transcurridos. | 200 | 401, 403 | `ListarSolicitudesPendientes` | CA-021 | P1 |
| POST | `/api/ordenes/{numero}/solicitudes-de-compra/{id}/llegada` | Compras | Registrar la llegada de la refacción. | 200 | 401, 403, 404, 409 | `ServicioDeRefacciones.registrar_llegada` | CA-022 | P1 |
| POST | `/api/ordenes/{numero}/solicitudes-de-compra/{id}/aviso-al-cliente` | Asesor | Registrar que se avisó al cliente del retraso. | 200 | 401, 403, 404, 409 | `ServicioDeRefacciones.registrar_aviso_al_cliente` | CA-023 | P1 |

### Retiro anticipado

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/ordenes/{numero}/retiro` | Asesor | Registrar la salida del vehículo y generar la Nota de Responsabilidad. | 201 | 401, 403, 404, 409 | `ServicioDeRetiro.registrar_salida` | CA-024 | P1 |
| GET | `/api/ordenes/{numero}/nota-de-responsabilidad/pdf` | Asesor | PDF de la Nota de Responsabilidad para imprimir. | 200 | 401, 403, 404, 409 | `ServicioDeRetiro.generar_pdf_de_nota` | CA-024 | P2 |
| POST | `/api/ordenes/{numero}/retiro/firma` | Asesor | Confirmar la firma de la nota (orden «Pausada por Retiro de Vehículo»). | 200 | 401, 403, 404, 409 | `ServicioDeRetiro.confirmar_firma` | CA-024 | P1 |
| POST | `/api/ordenes/{numero}/reactivacion` | Asesor | Reactivar la orden cuando el vehículo regresa (al final de la fila). | 200 | 401, 403, 404, 409 | `ServicioDeRetiro.reactivar` | CA-025 | P1 |

### Caja

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/ordenes/{numero}/pago` | Caja | Registrar el pago de contado de un cliente particular. | 201 | 401, 403, 404, 409, 422 | `ServicioDeCaja.registrar_pago` | CA-026 | P1 |
| PUT | `/api/ordenes/{numero}/pago` | Caja | Corregir la forma de pago mientras la orden está «Pagada». | 200 | 401, 403, 404, 409, 422 | `ServicioDeCaja.corregir_forma_de_pago` | CA-058 | P1 · Planeado |
| GET | `/api/ordenes/{numero}/recibo/pdf` | Caja | PDF del recibo interno. | 200 | 401, 403, 404, 409 | `ServicioDeCaja.generar_recibo` | CA-027 | P2 |
| POST | `/api/ordenes/{numero}/cargo-a-credito` | Caja | Registrar el cargo a crédito de una flotilla. | 201 | 401, 403, 404, 409 | `ServicioDeCaja.registrar_cargo_a_credito` | CA-039 | P1 |

### Entrega

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/ordenes/{numero}/entrega` | Asesor | Entregar el vehículo y cerrar la orden (fija el vencimiento del crédito). | 200 | 401, 403, 404, 409 | `ServicioDeEntrega.entregar` | CA-041, CA-042 | P1 |
| POST | `/api/ordenes/{numero}/entrega-sin-reparacion` | Asesor | Entregar sin reparación tras un rechazo total. | 200 | 401, 403, 404, 409 | `ServicioDeEntrega.entregar_sin_reparacion` | CA-043 | P1 |

### Consultas

| Método | Ruta | Rol | Descripción | Éxito | Errores | Caso de uso | Criterios | Prioridad |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/gerencia/ordenes` | Gerente | Listado de órdenes abiertas y cerradas (filtro opcional `estado`). | 200 | 401, 403 | `ListarOrdenes` | CA-030 | P1 |
| GET | `/api/gerencia/ingresos-del-dia` | Gerente | Total de pagos de contado de hoy (zona America/Monterrey). | 200 | 401, 403 | `ConsultarIngresosDelDia` | CA-031 | P1 |
| GET | `/api/consulta-de-estado?orden=&placas=` | Público | Consulta pública del cliente (sin token). | 200 | 404, 422 | `ConsultarEstadoDeOrden` | CA-037, CA-038, CA-066 | P1 |
| GET | `/api/alertas` | Cualquier empleado | Alertas internas del empleado que hace la petición (el token de Sistema responde 403: no es un empleado). | 200 | 401, 403 | `ListarAlertas` | CA-007, CA-008, CA-009, CA-015, CA-017, CA-022, CA-023, CA-032, CA-034, CA-040, CA-048 | P1 |

## Ejemplos

**Registrar una orden** (`POST /api/ordenes`, token de Asesor) → respuesta `201` con el mensaje de éxito de CA-001:

```json
{"numero_orden": "OS-0001", "estado": "Recibida", "id_cliente": "CLI-0001", "placas": "ABC123",
 "fecha_ingreso": "2026-10-05T15:00:00Z", "mensaje": "Orden OS-0001 registrada correctamente."}
```

**Generar la cotización inicial** (`POST /api/ordenes/AUT-O007/cotizaciones`, token de Asesor):

```json
{
  "trabajos": [
    {"numero": 1, "descripcion": "Afinación 07 (AUT-P007) x1", "mano_de_obra": "785.00", "refacciones": []},
    {"numero": 2, "descripcion": "Cambio aceite 12 (AUT-P012) x2", "mano_de_obra": "2280.00", "refacciones": []}
  ]
}
```

Respuesta `201`:

```json
{"id": "COT-0001", "numero_orden": "AUT-O007", "version": "v.1", "tipo": "Inicial",
 "estado": "Pendiente de Autorización del Cliente", "total": "3065.00"}
```

**Entregar sin pago registrado** (`POST /api/ordenes/AUT-O006/entrega` con la orden «Autorizada») → `409`:

```json
{"error": "EntregaNoPermitida", "codigo": 409,
 "detalle": "El vehículo de la orden AUT-O006 todavía no se puede entregar: su servicio sigue en proceso (estado «Autorizada»). Cuando esté «Lista para Entrega», primero debe registrarse el pago o el cargo a crédito."}
```

**Consulta pública con datos que no coinciden** (`GET /api/consulta-de-estado?orden=AUT-O007&placas=XXX000`) → `404`:

```json
{"error": "OrdenNoEncontrada", "detalle": "No se encontró una orden con esos datos. Revise el número de orden y las placas e intente de nuevo.", "codigo": 404}
```

Los importes del ejemplo salen de los datos del profesor: AUT-O007 tiene AUT-P007 × 1 ($785.00) y AUT-P012 × 2 ($1,140.00) = $785.00 + $2,280.00 = **$3,065.00**.

**Cotizar una orden con un servicio inhabilitado** (`POST /api/ordenes/AUT-O005/cotizaciones`, D-05 y H-PIA-19) → `422`, y la orden sigue «En Diagnóstico»:

```json
{"error": "ValorInvalido", "codigo": 422,
 "detalle": "No se puede cotizar la orden AUT-O005: incluye servicios que el taller no ofrece por ahora (AUT-P011). Informe al cliente."}
```
