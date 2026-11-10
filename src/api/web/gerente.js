// Pantallas del Gerente de Taller (interfaz-web.md §4.4). La página no decide qué cotización va
// al Gerente (E1): la lista y el desglose los manda la API.

import { pedir } from "./api.js";
import { cargarExpediente, vistaDeCotizacion, vistaDelExpediente } from "./expediente.js";
import { dinero, fecha, fechaYHora } from "./formato.js";
import {
  boton,
  confirmar,
  crear,
  decodificar,
  enviar,
  etiquetaDeEstado,
  lista,
  manejarError,
  mostrarCargando,
  mostrarExito,
  tabla,
} from "./ui.js";

// Direcciones de interfaz-web.md §3; el menú del encabezado muestra estas entradas.
export const MENU = [
  { texto: "Cotizaciones por aprobar", direccion: "#/gerente" },
  { texto: "Órdenes", direccion: "#/gerente/ordenes" },
  { texto: "Ingresos del día", direccion: "#/gerente/ingresos" },
];

// Los 13 estados del Glosario (§2), en el orden del ciclo de vida, para el filtro de G-02.
const ESTADOS_DE_LA_ORDEN = [
  "Recibida",
  "En Diagnóstico",
  "Cotizada",
  "Autorizada",
  "En Reparación",
  "En Espera de Refacción",
  "Pausada por Retiro de Vehículo",
  "Lista para Entrega",
  "Pagada",
  "Por Cobrar (Crédito)",
  "Cerrada",
  "Cerrada sin Reparación",
  "Cancelada",
];

export function mostrar(ruta, pantalla) {
  const orden = /^\/gerente\/orden\/(.+)$/.exec(ruta);
  if (orden) {
    mostrarOrden(pantalla, decodificar(orden[1]));
    return;
  }
  if (ruta === "/gerente/ordenes") {
    mostrarOrdenes(pantalla);
    return;
  }
  if (ruta === "/gerente/ingresos") {
    mostrarIngresos(pantalla);
    return;
  }
  mostrarPorAprobar(pantalla);
}

const direccionDeOrden = (numeroOrden) => `#/gerente/orden/${encodeURIComponent(numeroOrden)}`;

// ---------------------------------------------------------------- G-01 Cotizaciones por aprobar

async function mostrarPorAprobar(pantalla) {
  mostrarCargando(pantalla);
  let detalles;
  try {
    const pendientes = await pedir("GET", "/api/gerencia/cotizaciones-por-aprobar");
    detalles = await Promise.all(
      pendientes.map((pendiente) => pedir("GET", "/api/cotizaciones/{id}", { enRuta: { id: pendiente.id_cotizacion } })),
    );
  } catch (error) {
    pantalla.replaceChildren();
    manejarError(error, () => mostrarPorAprobar(pantalla));
    return;
  }
  const recargar = () => mostrarPorAprobar(pantalla);
  const titulo = crear("h1", {}, "Cotizaciones por aprobar");
  if (detalles.length === 0) {
    pantalla.replaceChildren(
      crear("section", { className: "tarjeta" }, titulo, crear("p", { className: "nota" }, "No hay cotizaciones por aprobar.")),
    );
    return;
  }
  pantalla.replaceChildren(
    crear(
      "section",
      { className: "tarjeta" },
      titulo,
      crear("p", { className: "nota" }, "Cotizaciones de más de $15,000.00 que esperan su revisión."),
    ),
    ...detalles.map((cotizacion) =>
      crear(
        "section",
        { className: "tarjeta" },
        crear("h2", {}, `Orden ${cotizacion.numero_orden}`),
        crear("p", {}, crear("a", { href: direccionDeOrden(cotizacion.numero_orden) }, "Ver el expediente de la orden")),
        vistaDeCotizacion(cotizacion, [
          boton("Aprobar", (elemento) => aprobar(cotizacion, elemento, recargar)),
          boton("Rechazar con observaciones", (elemento) => rechazar(cotizacion, elemento, recargar), "boton boton-peligro"),
        ]),
      ),
    ),
  );
}

function revisar(cotizacion, cuerpo) {
  return pedir("POST", "/api/cotizaciones/{id}/revision-gerencial", { enRuta: { id: cotizacion.id }, cuerpo });
}

// Aprobar (CA-008; AU-31).
async function aprobar(cotizacion, elemento, recargar) {
  const confirmado = await confirmar({
    titulo: `¿Aprobar la cotización de ${dinero(cotizacion.total)} de la orden ${cotizacion.numero_orden}?`,
    lineas: [`Cotización ${cotizacion.id}`, "Después, el asesor podrá presentarla al cliente."],
    verbo: "Aprobar",
  });
  if (!confirmado) {
    return;
  }
  await enviar(
    elemento,
    () => revisar(cotizacion, { aprobada: true }),
    (revisada) => {
      mostrarExito(`Cotización ${revisada.id} de la orden ${revisada.numero_orden} aprobada. Quedó «${revisada.estado}».`);
      recargar();
    },
  );
}

// Rechazar con observaciones obligatorias (CA-009; AU-32).
async function rechazar(cotizacion, elemento, recargar) {
  const observaciones = await confirmar({
    titulo: `¿Rechazar la cotización de ${dinero(cotizacion.total)} de la orden ${cotizacion.numero_orden}?`,
    lineas: [`Cotización ${cotizacion.id}`, "El asesor verá este motivo y ajustará la cotización."],
    verbo: "Rechazar cotización",
    motivo: "Motivo del rechazo",
  });
  if (observaciones === null) {
    return;
  }
  await enviar(
    elemento,
    () => revisar(cotizacion, { aprobada: false, observaciones }),
    (revisada) => {
      mostrarExito(`Cotización ${revisada.id} de la orden ${revisada.numero_orden} rechazada. Quedó «${revisada.estado}».`);
      recargar();
    },
  );
}

// ---------------------------------------------------------------- G-02 Órdenes

function mostrarOrdenes(pantalla) {
  const opciones = [{ valor: "", texto: "Todas" }, ...ESTADOS_DE_LA_ORDEN];
  const filtro = lista("filtro-estado", "Estado", opciones);
  const resultado = crear("div");
  pantalla.replaceChildren(
    crear("section", { className: "tarjeta" }, crear("h1", {}, "Órdenes"), filtro),
    resultado,
  );
  const elegir = filtro.querySelector("select");
  const cargar = () => cargarOrdenes(resultado, elegir.value);
  elegir.addEventListener("change", cargar);
  cargar();
}

async function cargarOrdenes(resultado, estado) {
  mostrarCargando(resultado);
  let ordenes;
  try {
    ordenes = await pedir("GET", "/api/gerencia/ordenes", { parametros: estado ? { estado } : {} });
  } catch (error) {
    resultado.replaceChildren();
    manejarError(error, () => cargarOrdenes(resultado, estado));
    return;
  }
  if (ordenes.length === 0) {
    const texto = estado ? `No hay órdenes en «${estado}».` : "Todavía no hay órdenes.";
    resultado.replaceChildren(crear("section", { className: "tarjeta" }, crear("p", { className: "nota" }, texto)));
    return;
  }
  resultado.replaceChildren(
    crear(
      "section",
      { className: "tarjeta" },
      crear("p", { className: "nota" }, ordenes.length === 1 ? "1 orden." : `${ordenes.length} órdenes.`),
      tabla(
        ["Folio", "Placas", "Estado", "Ingreso", "Última actualización"],
        ordenes.map((orden) => [
          crear("a", { href: direccionDeOrden(orden.numero_orden) }, orden.numero_orden),
          orden.placas,
          etiquetaDeEstado(orden.estado),
          fechaYHora(orden.fecha_ingreso),
          fechaYHora(orden.ultima_actualizacion),
        ]),
      ),
    ),
  );
}

// Expediente solo para consulta: el Gerente no tiene botones en la orden.
async function mostrarOrden(pantalla, numeroOrden) {
  mostrarCargando(pantalla);
  const regresar = crear("div", { className: "acciones" }, crear("a", { className: "boton boton-secundario", href: "#/gerente/ordenes" }, "Regresar a órdenes"));
  let expediente;
  try {
    expediente = await cargarExpediente(numeroOrden);
  } catch (error) {
    pantalla.replaceChildren(regresar);
    manejarError(error, () => mostrarOrden(pantalla, numeroOrden));
    return;
  }
  pantalla.replaceChildren(...vistaDelExpediente(expediente), regresar);
}

// ---------------------------------------------------------------- G-03 Ingresos del día

async function mostrarIngresos(pantalla) {
  mostrarCargando(pantalla);
  let ingresos;
  try {
    ingresos = await pedir("GET", "/api/gerencia/ingresos-del-dia");
  } catch (error) {
    pantalla.replaceChildren();
    manejarError(error, () => mostrarIngresos(pantalla));
    return;
  }
  pantalla.replaceChildren(
    crear(
      "section",
      { className: "tarjeta" },
      crear("h1", {}, "Ingresos del día"),
      crear("p", { className: "importe-grande" }, dinero(ingresos.total)),
      crear("p", { className: "nota" }, `Pagos de contado del ${fecha(ingresos.fecha)}.`),
    ),
  );
}
