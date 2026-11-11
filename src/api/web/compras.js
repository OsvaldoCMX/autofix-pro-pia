// Pantallas del Personal de Compras (interfaz-web.md §4.5). Compras no abre el expediente: la API
// no se lo permite. Los días hábiles los calcula la API.

import { pedir } from "./api.js";
import { fechaYHora } from "./formato.js";
import { boton, confirmar, crear, enviar, manejarError, mostrarCargando, mostrarExito, tabla } from "./ui.js";

// Direcciones de interfaz-web.md §3; el encabezado y las tarjetas del menú muestran estas entradas.
export const MENU = [
  { texto: "Solicitudes pendientes", direccion: "#/compras", icono: "paquete" },
];

const DIAS_PARA_RESALTAR = 3;

export function mostrar(ruta, pantalla) {
  mostrarPendientes(pantalla);
}

// ---------------------------------------------------------------- C-01 Solicitudes pendientes

async function mostrarPendientes(pantalla) {
  mostrarCargando(pantalla);
  let solicitudes;
  try {
    solicitudes = await pedir("GET", "/api/compras/solicitudes-pendientes");
  } catch (error) {
    pantalla.replaceChildren();
    manejarError(error, () => mostrarPendientes(pantalla));
    return;
  }
  const titulo = crear("h1", {}, "Solicitudes pendientes");
  if (solicitudes.length === 0) {
    pantalla.replaceChildren(
      crear("section", { className: "tarjeta" }, titulo, crear("p", { className: "nota" }, "No hay solicitudes pendientes.")),
    );
    return;
  }
  const recargar = () => mostrarPendientes(pantalla);
  pantalla.replaceChildren(
    crear(
      "section",
      { className: "tarjeta" },
      titulo,
      crear("p", { className: "nota" }, `Las que llevan más de ${DIAS_PARA_RESALTAR} días hábiles aparecen resaltadas.`),
      tabla(
        ["Orden", "Refacción", "Cantidad", "Solicitada", "Días hábiles", ""],
        solicitudes.map((solicitud) => [
          solicitud.numero_orden,
          solicitud.refaccion,
          String(solicitud.cantidad),
          fechaYHora(solicitud.fecha_solicitud),
          diasTranscurridos(solicitud.dias_habiles_transcurridos),
          crear(
            "div",
            { className: "acciones-en-tabla" },
            boton("Registrar llegada", (elemento) => registrarLlegada(solicitud, elemento, recargar)),
          ),
        ]),
      ),
    ),
  );
}

/** El número de días; si pasa de 3, resaltado y con texto (el color nunca es la única señal). */
function diasTranscurridos(dias) {
  if (dias <= DIAS_PARA_RESALTAR) {
    return String(dias);
  }
  return crear("strong", { className: "retrasada" }, `${dias} (más de ${DIAS_PARA_RESALTAR})`);
}

// Registrar la llegada de la refacción (CA-022; AU-33).
async function registrarLlegada(solicitud, elemento, recargar) {
  const confirmado = await confirmar({
    titulo: `¿Registrar la llegada de «${solicitud.refaccion}»?`,
    lineas: [`Orden ${solicitud.numero_orden}`, `Refacción: ${solicitud.refaccion}`, `Cantidad: ${solicitud.cantidad}`],
    verbo: "Registrar llegada",
  });
  if (!confirmado) {
    return;
  }
  await enviar(
    elemento,
    () =>
      pedir("POST", "/api/ordenes/{numero}/solicitudes-de-compra/{id}/llegada", {
        enRuta: { numero: solicitud.numero_orden, id: solicitud.id_solicitud },
      }),
    (llegada) => {
      mostrarExito(`Llegada de «${solicitud.refaccion}» registrada. La orden ${llegada.numero_orden} está «${llegada.estado_orden}».`);
      recargar();
    },
  );
}
