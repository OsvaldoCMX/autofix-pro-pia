// Expediente de la orden, solo para consulta (A-03). Cada puesto le agrega sus botones: el Asesor
// en la Fase 16 y el Técnico en la Fase 17; el Gerente lo ve sin botones (interfaz-web.md §8).
// Todo lo que se muestra viene del expediente que manda la API; la página no calcula nada.

import { pedir } from "./api.js";
import { dinero, fecha, fechaYHora, numero } from "./formato.js";
import { crear, datos, etiquetaDeEstado, tabla } from "./ui.js";

export function cargarExpediente(numeroOrden) {
  return pedir("GET", "/api/ordenes/{numero}", { enRuta: { numero: numeroOrden } });
}

const fechaOpcional = (valor) => (valor ? fechaYHora(valor) : null);

function vacio(texto) {
  return crear("p", { className: "nota" }, texto);
}

function bloque(titulo, ...contenido) {
  return crear("section", { className: "tarjeta" }, crear("h2", {}, titulo), ...contenido);
}

/** «Cliente particular», o la empresa con su Responsable de Flotilla. */
export function descripcionDelCliente(expediente) {
  if (expediente.cliente_tipo === "Flotilla") {
    return `${expediente.empresa ?? expediente.cliente_nombre} (flotilla)`;
  }
  return expediente.cliente_nombre ?? expediente.id_cliente;
}

export function descripcionDelVehiculo(expediente) {
  const partes = [expediente.vehiculo_marca, expediente.vehiculo_modelo, expediente.vehiculo_anio];
  return partes.filter((parte) => parte !== null && parte !== undefined).join(" ");
}

function encabezado(expediente, acciones) {
  return crear(
    "section",
    { className: "tarjeta", "aria-label": "Datos de la orden" },
    crear("h1", {}, `Orden ${expediente.numero_orden}`),
    etiquetaDeEstado(expediente.estado),
    crear("p", { className: "placas" }, expediente.placas),
    datos([
      ["Cliente", descripcionDelCliente(expediente)],
      ["Responsable de Flotilla", expediente.responsable_nombre],
      ["Vehículo", descripcionDelVehiculo(expediente)],
      ["Fecha de ingreso", fechaYHora(expediente.fecha_ingreso)],
      ["Última actualización", fechaYHora(expediente.ultima_actualizacion)],
      ["Motivo de la cancelación", expediente.cancelacion_motivo],
    ]),
    acciones.length > 0 ? crear("div", { className: "acciones" }, ...acciones) : null,
  );
}

function recepcion(expediente) {
  return bloque(
    "Recepción",
    datos([
      ["Kilometraje", expediente.kilometraje === null ? null : `${numero(expediente.kilometraje)} km`],
      ["Nivel de combustible", expediente.nivel_de_combustible],
      ["Motivo de ingreso", expediente.motivo_de_ingreso],
    ]),
  );
}

function diagnostico(expediente) {
  const tecnico = expediente.tecnico_de_diagnostico_nombre ?? expediente.tecnico_de_diagnostico;
  return bloque(
    "Diagnóstico",
    datos([
      ["Técnico asignado", tecnico ?? "Todavía no se asigna un técnico."],
      ["Fallas encontradas", expediente.diagnostico_fallas ?? "Todavía no hay diagnóstico."],
      ["Recomendaciones", expediente.diagnostico_recomendaciones],
    ]),
  );
}

function refacciones(linea) {
  if (linea.refacciones.length === 0) {
    return "—";
  }
  return crear(
    "ul",
    { className: "lista-simple" },
    ...linea.refacciones.map((refaccion) =>
      crear(
        "li",
        {},
        `${refaccion.cantidad} × ${refaccion.descripcion} a ${dinero(refaccion.precio_unitario)} = ${dinero(refaccion.importe)}`,
      ),
    ),
  );
}

function correcciones(cotizacion) {
  if (cotizacion.correcciones.length === 0) {
    return null;
  }
  return crear(
    "div",
    {},
    crear("h4", {}, "Historial de correcciones"),
    tabla(
      ["Fecha", "Motivo", "Total anterior", "Total nuevo", "Estado anterior"],
      cotizacion.correcciones.map((correccion) => [
        fechaYHora(correccion.registrada_en),
        correccion.motivo,
        dinero(correccion.total_anterior),
        dinero(correccion.total_nuevo),
        correccion.estado_anterior,
      ]),
    ),
  );
}

/** Una cotización con su desglose; `acciones` son los botones que agrega cada puesto. */
export function vistaDeCotizacion(cotizacion, acciones = []) {
  return crear(
    "article",
    { className: "cotizacion" },
    crear("h3", {}, `Cotización ${cotizacion.id} · ${cotizacion.tipo} ${cotizacion.version}`),
    crear("p", {}, crear("span", { className: "estado-cotizacion" }, cotizacion.estado)),
    datos([
      ["Total", dinero(cotizacion.total)],
      ["Generada", fechaYHora(cotizacion.generada_en)],
      ["Aprobada por el Gerente", fechaOpcional(cotizacion.fecha_aprobacion_gerencial)],
      ["Observaciones del Gerente", cotizacion.observaciones_del_gerente],
      ["Presentada al cliente", fechaOpcional(cotizacion.fecha_presentacion)],
      ["Decidió", cotizacion.autorizante],
      ["Fecha de la decisión", fechaOpcional(cotizacion.fecha_decision)],
    ]),
    tabla(
      ["#", "Trabajo", "Mano de obra", "Refacciones", "Subtotal", "Decisión"],
      cotizacion.lineas.map((linea) => [
        String(linea.numero),
        linea.descripcion,
        dinero(linea.mano_de_obra),
        refacciones(linea),
        dinero(linea.subtotal),
        linea.decision ?? "—",
      ]),
    ),
    correcciones(cotizacion),
    acciones.length > 0 ? crear("div", { className: "acciones" }, ...acciones) : null,
  );
}

function cotizaciones(expediente, deCotizacion) {
  if (expediente.cotizaciones.length === 0) {
    return bloque("Cotizaciones", vacio("Todavía no hay cotizaciones."));
  }
  return bloque(
    "Cotizaciones",
    ...expediente.cotizaciones.map((cotizacion) => vistaDeCotizacion(cotizacion, deCotizacion(cotizacion))),
  );
}

function trabajos(expediente, deTrabajo) {
  if (expediente.trabajos.length === 0) {
    return bloque("Trabajos", vacio("Todavía no hay trabajos autorizados."));
  }
  return bloque(
    "Trabajos",
    tabla(
      ["Trabajo", "Importe", "Estado", "Técnico", ""],
      expediente.trabajos.map((trabajo) => [
        trabajo.descripcion,
        dinero(trabajo.importe),
        trabajo.estado,
        trabajo.tecnico_nombre ?? trabajo.tecnico ?? "Sin asignar",
        crear("div", { className: "acciones-en-tabla" }, ...deTrabajo(trabajo)),
      ]),
    ),
  );
}

function solicitudes(expediente, deSolicitud) {
  if (expediente.solicitudes.length === 0) {
    return bloque("Solicitudes de compra", vacio("No hay solicitudes de compra."));
  }
  const trabajoDe = (id) => expediente.trabajos.find((trabajo) => trabajo.id === id)?.descripcion ?? "";
  return bloque(
    "Solicitudes de compra",
    tabla(
      ["Refacción", "Cantidad", "Trabajo", "Estado", "Solicitada", "Llegó", "Aviso al cliente", ""],
      expediente.solicitudes.map((solicitud) => [
        solicitud.refaccion,
        String(solicitud.cantidad),
        trabajoDe(solicitud.id_trabajo),
        solicitud.estado,
        fechaYHora(solicitud.fecha_solicitud),
        fechaOpcional(solicitud.fecha_llegada) ?? "—",
        fechaOpcional(solicitud.fecha_aviso_al_cliente) ?? "—",
        crear("div", { className: "acciones-en-tabla" }, ...deSolicitud(solicitud)),
      ]),
    ),
  );
}

function fallasAdicionales(expediente) {
  if (expediente.fallas_adicionales.length === 0) {
    return bloque("Fallas adicionales", vacio("No hay fallas adicionales reportadas."));
  }
  return bloque(
    "Fallas adicionales",
    tabla(
      ["Falla", "Reportada"],
      expediente.fallas_adicionales.map((falla) => [falla.descripcion, fechaYHora(falla.reportada_en)]),
    ),
  );
}

function pagoYEntrega(expediente) {
  const pares = [
    ["Total autorizado", dinero(expediente.total_autorizado)],
    ["Pago", expediente.pago_monto ? `${dinero(expediente.pago_monto)} en ${expediente.pago_forma}` : null],
    ["Fecha del pago", fechaOpcional(expediente.pago_registrado_en)],
    ["Cargo a crédito", expediente.credito_monto ? dinero(expediente.credito_monto) : null],
    ["Vence el crédito", expediente.credito_fecha_vencimiento ? fecha(expediente.credito_fecha_vencimiento) : null],
    ["Salida antes de terminar", fechaOpcional(expediente.nota_fecha_salida)],
    ["Nota de Responsabilidad", expediente.nota_fecha_salida ? (expediente.nota_firmada ? "Firmada" : "Sin firmar") : null],
    ["Entregado", fechaOpcional(expediente.fecha_entrega)],
  ];
  return bloque("Pago y entrega", datos(pares));
}

/**
 * Todos los bloques del expediente. Opciones: `acciones` (botones de la orden, debajo del
 * encabezado), `zona` (lugar para los formularios que abren esos botones), `deCotizacion` y
 * `deSolicitud` y `deTrabajo` (botones de cada cotización, solicitud o trabajo).
 */
export function vistaDelExpediente(
  expediente,
  { acciones = [], zona = null, deCotizacion = () => [], deSolicitud = () => [], deTrabajo = () => [] } = {},
) {
  return [
    encabezado(expediente, acciones),
    zona,
    recepcion(expediente),
    diagnostico(expediente),
    cotizaciones(expediente, deCotizacion),
    trabajos(expediente, deTrabajo),
    solicitudes(expediente, deSolicitud),
    fallasAdicionales(expediente),
    pagoYEntrega(expediente),
  ].filter((elemento) => elemento !== null);
}
