"""Contrato planeado de la API REST (prefijo /api). Se valida contra las rutas citadas en datos.CA."""
import re

from datos import CA, PLANEADO

P1_PLANEADA, P2_PLANEADA = f"P1 · {PLANEADO}", f"P2 · {PLANEADO}"

A, T, G, CO, CJ, P, S, TODOS = ("Asesor", "Técnico", "Gerente", "Compras", "Caja", "Público",
                                "Sistema", "Cualquier empleado")

# (método, ruta, rol, descripción, éxito, errores, caso de uso, CA, prioridad, área)
RUTAS = [
    ("GET", "/api/sesion", TODOS, "Nombre y puesto del empleado de la clave de acceso (la usa la página al iniciar sesión, ADR-017). El token de Sistema responde 403: no es un empleado.", "200", "401, 403", "ConsultarSesion", [], P1_PLANEADA, "Sesión"),
    ("GET", "/health", P, "Salud del servicio (lo usa Render y Docker Compose).", "200", "—", "—", [], "P1", "Sistema"),
    # recepción
    ("GET", "/api/vehiculos/{placas}", A, "Buscar vehículo y cliente por placas.", "200", "401, 403, 404", "BuscarVehiculoPorPlacas", ["CA-003", "CA-004"], "P1", "Recepción"),
    ("PUT", "/api/vehiculos/{placas}", A, "Corregir el VIN, la marca, el modelo o el año del vehículo (las placas no cambian).", "200", "401, 403, 404, 409, 422", "ServicioDeRecepcion.corregir_vehiculo", ["CA-056"], P1_PLANEADA, "Recepción"),
    ("GET", "/api/clientes?tipo=Flotilla&empresa=", A, "Buscar la empresa de flotilla y su Responsable.", "200", "401, 403", "BuscarClientes", ["CA-028"], "P1", "Recepción"),
    ("POST", "/api/clientes", A, "Registrar cliente particular o de flotilla (con Responsable). *Planeado (H-PIA-28):* 409 si la empresa ya está registrada con otro responsable.", "201", "400, 401, 403, 422", "ServicioDeRecepcion.registrar_cliente", ["CA-028", "CA-059", "CA-065"], "P1", "Recepción"),
    ("PUT", "/api/clientes/{id}", A, "Corregir el nombre, el teléfono o el correo del cliente.", "200", "401, 403, 404, 422", "ServicioDeRecepcion.corregir_cliente", ["CA-055"], "P1", "Recepción"),
    ("POST", "/api/ordenes", A, "Registrar la orden: cliente, vehículo, motivo, kilometraje y combustible. Si las placas ya existen, reutiliza el registro y actualiza los datos enviados; 409 si el vehículo ya tiene una orden abierta (H-PIA-22).", "201", "400, 401, 403, 404, 409, 422", "ServicioDeRecepcion.registrar_orden", ["CA-001", "CA-002", "CA-004", "CA-052", "CA-059"], "P1", "Recepción"),
    ("POST", "/api/ordenes/{numero}/fotos", A, "Adjuntar foto de daños (multipart).", "201", "401, 403, 404, 422", "ServicioDeRecepcion.adjuntar_foto", ["CA-002"], "P2", "Recepción"),
    ("GET", "/api/ordenes/{numero}", f"{A}, {G}, {T}, {CJ}", "Expediente completo de la orden (estado, cotizaciones, trabajos, solicitudes, pagos), con el nombre y el tipo del cliente (y el nombre de su Responsable de Flotilla), la marca, el modelo y el año del vehículo y el nombre del técnico de diagnóstico y de cada trabajo (`interfaz-web.md` §7).", "200", "401, 403, 404", "ConsultarExpedienteDeOrden", [], "P1", "Recepción"),
    ("PUT", "/api/ordenes/{numero}/recepcion", A, "Corregir el kilometraje, el nivel de combustible o el motivo de ingreso (orden «Recibida» o «En Diagnóstico»).", "200", "401, 403, 404, 409, 422", "ServicioDeRecepcion.corregir_recepcion", ["CA-057"], P1_PLANEADA, "Recepción"),
    ("PUT", "/api/ordenes/{numero}/placas", A, "Corregir las placas mal capturadas (orden «Recibida» o «En Diagnóstico»). Mientras responda 501 no aparece en la página.", "200", "401, 403, 404, 409, 422", "ServicioDeRecepcion.corregir_placas", ["CA-066"], P2_PLANEADA, "Recepción"),
    # cancelación
    ("POST", "/api/ordenes/{numero}/cancelacion", A, "Cancelar la orden con motivo (solo sin cotización).", "200", "401, 403, 404, 409, 422", "ServicioDeCancelacion.cancelar", ["CA-044", "CA-045"], "P1", "Cancelación"),
    # diagnóstico
    ("POST", "/api/ordenes/{numero}/asignacion-diagnostico", A, "Asignar técnico para el diagnóstico, o cambiarlo mientras no haya diagnóstico (H-PIA-23).", "200", "401, 403, 404, 409, 422", "ServicioDeDiagnostico.asignar_tecnico", ["CA-035", "CA-054"], "P1", "Diagnóstico"),
    ("POST", "/api/ordenes/{numero}/diagnostico", T, "Registrar el diagnóstico (fallas y recomendaciones).", "201", "401, 403, 404, 409, 422", "ServicioDeDiagnostico.registrar_diagnostico", ["CA-032", "CA-033"], "P1", "Diagnóstico"),
    ("POST", "/api/ordenes/{numero}/fallas-adicionales", T, "Reportar una falla adicional durante la reparación.", "201", "401, 403, 404, 409, 422", "ServicioDeDiagnostico.reportar_falla_adicional", ["CA-034"], "P1", "Diagnóstico"),
    ("GET", "/api/tecnicos/me/panel", T, "Órdenes y trabajos asignados, en orden de la fila.", "200", "401, 403", "ConsultarPanelDelTecnico", ["CA-013", "CA-035", "CA-036", "CA-054"], "P1", "Diagnóstico"),
    ("GET", "/api/tecnicos", A, "Técnicos del taller (clave y nombre) para asignarlos.", "200", "401, 403", "ListarTecnicos", ["CA-053"], "P1", "Diagnóstico"),
    # cotización
    ("POST", "/api/ordenes/{numero}/cotizaciones", A, "Generar la cotización inicial (v.1).", "201", "401, 403, 404, 409, 422", "ServicioDeCotizacion.generar_inicial", ["CA-005", "CA-007", "CA-060"], "P1", "Cotización"),
    ("POST", "/api/ordenes/{numero}/cotizaciones-adicionales", A, "Generar una cotización adicional (v.2, v.3…).", "201", "401, 403, 404, 409, 422", "ServicioDeCotizacion.generar_adicional", ["CA-016", "CA-060", "CA-061"], "P1", "Cotización"),
    ("GET", "/api/cotizaciones/{id}", f"{A}, {G}", "Detalle de la cotización con su desglose, su estado y su historial de correcciones (H-PIA-21).", "200", "401, 403, 404", "ConsultarCotizacion", ["CA-005"], "P1", "Cotización"),
    ("GET", "/api/cotizaciones/{id}/pdf", A, "PDF de la cotización.", "200", "401, 403, 404", "ServicioDeCotizacion.generar_pdf", ["CA-005"], "P2", "Cotización"),
    ("POST", "/api/cotizaciones/{id}/presentacion", A, "Marcar como presentada (inicia las 48 h).", "200", "401, 403, 404, 409", "ServicioDeCotizacion.presentar", ["CA-006", "CA-007", "CA-051"], "P1", "Cotización"),
    ("POST", "/api/cotizaciones/{id}/revision-gerencial", G, "Aprobar o rechazar (con observaciones) una cotización mayor a $15,000.", "200", "401, 403, 404, 409, 422", "ServicioDeAprobacionGerencial.revisar", ["CA-008", "CA-009"], "P1", "Cotización"),
    ("PUT", "/api/cotizaciones/{id}/lineas", A, "Guardar la cotización ajustada según el Gerente.", "200", "401, 403, 404, 409, 422", "ServicioDeCotizacion.ajustar", ["CA-009"], "P1", "Cotización"),
    ("POST", "/api/cotizaciones/{id}/correcciones", A, "Corregir una cotización que espera al Gerente o al cliente (motivo obligatorio; guarda el historial y vuelve a evaluar la regla de $15,000).", "201", "401, 403, 404, 409, 422", "ServicioDeCotizacion.corregir", ["CA-047", "CA-048", "CA-049", "CA-050"], "P1", "Cotización"),
    ("POST", "/api/cotizaciones/{id}/recontactos", A, "Registrar el recontacto al cliente (48 h).", "201", "401, 403, 404, 409", "ServicioDeCotizacion.registrar_recontacto", ["CA-040"], "P1", "Cotización"),
    ("GET", "/api/gerencia/cotizaciones-por-aprobar", G, "Cotizaciones en «Pendiente de Aprobación Gerencial».", "200", "401, 403", "ListarCotizacionesPendientesDeAprobacion", ["CA-007"], "P1", "Cotización"),
    # autorización
    ("POST", "/api/cotizaciones/{id}/decision", A, "Registrar la decisión del cliente o del Responsable de Flotilla.", "200", "401, 403, 404, 409, 422", "ServicioDeAutorizacion.registrar_decision", ["CA-010", "CA-012", "CA-017", "CA-018", "CA-029", "CA-063", "CA-064"], "P1", "Autorización"),
    # reparación
    ("POST", "/api/ordenes/{numero}/asignacion-trabajos", A, "Asignar trabajos autorizados a un técnico.", "200", "401, 403, 404, 409, 422", "ServicioDeReparacion.asignar_trabajos", ["CA-011", "CA-012", "CA-036"], "P1", "Reparación"),
    ("POST", "/api/ordenes/{numero}/trabajos/{id}/inicio", T, "Pasar un trabajo a «En Progreso».", "200", "401, 403, 404, 409", "ServicioDeReparacion.iniciar_trabajo", ["CA-014", "CA-046"], "P1", "Reparación"),
    ("POST", "/api/ordenes/{numero}/trabajos/{id}/completado", T, "Pasar un trabajo a «Completado».", "200", "401, 403, 404, 409", "ServicioDeReparacion.completar_trabajo", ["CA-015"], "P1", "Reparación"),
    # refacciones
    ("POST", "/api/ordenes/{numero}/solicitudes-de-compra", T, "Crear solicitud de compra de una refacción no disponible.", "201", "401, 403, 404, 409, 422", "ServicioDeRefacciones.solicitar", ["CA-019", "CA-020", "CA-062"], "P1", "Refacciones"),
    ("GET", "/api/compras/solicitudes-pendientes", CO, "Solicitudes «Solicitada» con días hábiles transcurridos.", "200", "401, 403", "ListarSolicitudesPendientes", ["CA-021"], "P1", "Refacciones"),
    ("POST", "/api/ordenes/{numero}/solicitudes-de-compra/{id}/llegada", CO, "Registrar la llegada de la refacción.", "200", "401, 403, 404, 409", "ServicioDeRefacciones.registrar_llegada", ["CA-022"], "P1", "Refacciones"),
    ("POST", "/api/ordenes/{numero}/solicitudes-de-compra/{id}/aviso-al-cliente", A, "Registrar que se avisó al cliente del retraso.", "200", "401, 403, 404, 409", "ServicioDeRefacciones.registrar_aviso_al_cliente", ["CA-023"], "P1", "Refacciones"),
    # retiro
    ("POST", "/api/ordenes/{numero}/retiro", A, "Registrar la salida del vehículo y generar la Nota de Responsabilidad.", "201", "401, 403, 404, 409", "ServicioDeRetiro.registrar_salida", ["CA-024"], "P1", "Retiro anticipado"),
    ("GET", "/api/ordenes/{numero}/nota-de-responsabilidad/pdf", A, "PDF de la Nota de Responsabilidad para imprimir.", "200", "401, 403, 404, 409", "ServicioDeRetiro.generar_pdf_de_nota", ["CA-024"], "P2", "Retiro anticipado"),
    ("POST", "/api/ordenes/{numero}/retiro/firma", A, "Confirmar la firma de la nota (orden «Pausada por Retiro de Vehículo»).", "200", "401, 403, 404, 409", "ServicioDeRetiro.confirmar_firma", ["CA-024"], "P1", "Retiro anticipado"),
    ("POST", "/api/ordenes/{numero}/reactivacion", A, "Reactivar la orden cuando el vehículo regresa (al final de la fila).", "200", "401, 403, 404, 409", "ServicioDeRetiro.reactivar", ["CA-025"], "P1", "Retiro anticipado"),
    # caja
    ("POST", "/api/ordenes/{numero}/pago", CJ, "Registrar el pago de contado de un cliente particular.", "201", "401, 403, 404, 409, 422", "ServicioDeCaja.registrar_pago", ["CA-026"], "P1", "Caja"),
    ("PUT", "/api/ordenes/{numero}/pago", CJ, "Corregir la forma de pago mientras la orden está «Pagada».", "200", "401, 403, 404, 409, 422", "ServicioDeCaja.corregir_forma_de_pago", ["CA-058"], P1_PLANEADA, "Caja"),
    ("GET", "/api/ordenes/{numero}/recibo/pdf", CJ, "PDF del recibo interno.", "200", "401, 403, 404, 409", "ServicioDeCaja.generar_recibo", ["CA-027"], "P2", "Caja"),
    ("POST", "/api/ordenes/{numero}/cargo-a-credito", CJ, "Registrar el cargo a crédito de una flotilla.", "201", "401, 403, 404, 409", "ServicioDeCaja.registrar_cargo_a_credito", ["CA-039"], "P1", "Caja"),
    # entrega
    ("POST", "/api/ordenes/{numero}/entrega", A, "Entregar el vehículo y cerrar la orden (fija el vencimiento del crédito).", "200", "401, 403, 404, 409", "ServicioDeEntrega.entregar", ["CA-041", "CA-042"], "P1", "Entrega"),
    ("POST", "/api/ordenes/{numero}/entrega-sin-reparacion", A, "Entregar sin reparación tras un rechazo total.", "200", "401, 403, 404, 409", "ServicioDeEntrega.entregar_sin_reparacion", ["CA-043"], "P1", "Entrega"),
    # consultas
    ("GET", "/api/gerencia/ordenes", G, "Listado de órdenes abiertas y cerradas (filtro opcional `estado`).", "200", "401, 403", "ListarOrdenes", ["CA-030"], "P1", "Consultas"),
    ("GET", "/api/gerencia/ingresos-del-dia", G, "Total de pagos de contado de hoy (zona America/Monterrey).", "200", "401, 403", "ConsultarIngresosDelDia", ["CA-031"], "P1", "Consultas"),
    ("GET", "/api/consulta-de-estado?orden=&placas=", P, "Consulta pública del cliente (sin token).", "200", "404, 422", "ConsultarEstadoDeOrden", ["CA-037", "CA-038", "CA-066"], "P1", "Consultas"),
    ("GET", "/api/alertas", TODOS, "Alertas internas del empleado que hace la petición (el token de Sistema responde 403: no es un empleado).", "200", "401, 403", "ListarAlertas",
     ["CA-007", "CA-008", "CA-009", "CA-015", "CA-017", "CA-022", "CA-023", "CA-032", "CA-034", "CA-040", "CA-048"], "P1", "Consultas"),
    ("POST", "/api/revisiones/plazos", S, "Revisión de plazos de 3 días hábiles y 48 h (la llama un workflow programado).", "200", "401, 403", "ServicioDeRevisionDePlazos.revisar", ["CA-023", "CA-040", "CA-051"], "P1", "Sistema"),
]


def rutas_en_criterios():
    usadas = {}
    for c in CA.values():
        for m in re.findall(r"(GET|POST|PUT|PATCH|DELETE) (/[^\s·()]+)", c["ruta"]):
            usadas.setdefault(m, set()).add(c["id"])
    return usadas


def validar_rutas():
    usadas = rutas_en_criterios()
    definidas = {(m, r): set(cas) for m, r, *_x, cas, _p, _a in RUTAS}
    faltan = set(usadas) - set(definidas)
    assert not faltan, faltan
    for clave, cas in usadas.items():
        assert cas <= definidas[clave], (clave, cas - definidas[clave])
    return len(RUTAS)


if __name__ == "__main__":
    print(validar_rutas())
