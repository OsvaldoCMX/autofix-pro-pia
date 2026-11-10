// Pantallas del Gerente de Taller (interfaz-web.md §4.4). La página no decide qué cotización va
// al Gerente (E1): la lista y el desglose los manda la API.

import { pedir } from "./api.js";
import { vistaDeCotizacion } from "./expediente.js";
import { dinero } from "./formato.js";
import {
  boton,
  confirmar,
  crear,
  enviar,
  manejarError,
  mostrarCargando,
  mostrarExito,
  pantallaEnPreparacion,
} from "./ui.js";

// Direcciones de interfaz-web.md §3; el menú del encabezado muestra estas entradas.
export const MENU = [
  { texto: "Cotizaciones por aprobar", direccion: "#/gerente" },
  { texto: "Órdenes", direccion: "#/gerente/ordenes" },
  { texto: "Ingresos del día", direccion: "#/gerente/ingresos" },
];

export function mostrar(ruta, pantalla) {
  if (ruta === "/gerente") {
    mostrarPorAprobar(pantalla);
    return;
  }
  pantallaEnPreparacion(pantalla, MENU, ruta);
}

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
