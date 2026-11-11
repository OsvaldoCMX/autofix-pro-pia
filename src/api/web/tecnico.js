// Pantallas del Técnico (interfaz-web.md §4.3). Cada botón aparece solo en los estados de su
// tabla y solo en lo que tiene asignado; si aun así la API rechaza la acción, se muestra su
// mensaje tal cual. Los permisos los decide la API.

import { pedir } from "./api.js";
import { cargarExpediente, vistaDelExpediente } from "./expediente.js";
import { fechaYHora } from "./formato.js";
import { empleadoActual } from "./sesion.js";
import {
  alEnviar,
  areaDeTexto,
  boton,
  campo,
  confirmar,
  crear,
  datos,
  decodificar,
  enviar,
  etiquetaDeEstado,
  formulario,
  limpiarAvisos,
  manejarError,
  marcarCampo,
  mostrarCargando,
  mostrarExito,
  revisarObligatorios,
  secundario,
  tabla,
} from "./ui.js";

// Direcciones de interfaz-web.md §3; el encabezado y las tarjetas del menú muestran estas entradas.
export const MENU = [
  { texto: "Mi fila de trabajo", direccion: "#/tecnico", icono: "fila" },
];

const ESTADOS_EN_TRABAJO = ["Autorizada", "En Reparación", "En Espera de Refacción"];

export function mostrar(ruta, pantalla) {
  const orden = /^\/tecnico\/orden\/(.+)$/.exec(ruta);
  if (orden) {
    mostrarOrden(pantalla, decodificar(orden[1]));
    return;
  }
  mostrarFila(pantalla);
}

const direccionDeOrden = (numeroOrden) => `#/tecnico/orden/${encodeURIComponent(numeroOrden)}`;

// ---------------------------------------------------------------- T-01 Mi fila de trabajo

async function mostrarFila(pantalla) {
  mostrarCargando(pantalla);
  let panel;
  try {
    panel = await pedir("GET", "/api/tecnicos/me/panel");
  } catch (error) {
    pantalla.replaceChildren();
    manejarError(error, () => mostrarFila(pantalla));
    return;
  }
  const titulo = crear("h1", {}, "Mi fila de trabajo");
  if (panel.length === 0) {
    pantalla.replaceChildren(
      crear("section", { className: "tarjeta" }, titulo, crear("p", { className: "nota" }, "No tiene órdenes asignadas.")),
    );
    return;
  }
  pantalla.replaceChildren(
    crear(
      "section",
      { className: "tarjeta" },
      titulo,
      crear("p", { className: "nota" }, "La orden que lleva más tiempo en la fila está arriba."),
    ),
    ...panel.map(ordenDeLaFila),
  );
}

function ordenDeLaFila(orden, posicion) {
  const trabajos =
    orden.trabajos.length > 0
      ? tabla(["Mi trabajo", "Estado"], orden.trabajos.map((trabajo) => [trabajo.descripcion, trabajo.estado]))
      : null;
  return crear(
    "article",
    { className: "tarjeta" },
    crear("h2", {}, `${posicion + 1}. Orden ${orden.numero_orden}`),
    etiquetaDeEstado(orden.estado),
    crear("p", { className: "placas" }, orden.placas),
    datos([
      ["Motivo de ingreso", orden.motivo_de_ingreso],
      ["En la fila desde", fechaYHora(orden.fecha_ingreso_a_fila)],
      ["Diagnóstico", orden.diagnostico_asignado ? "Usted tiene asignado el diagnóstico de esta orden." : null],
    ]),
    trabajos,
    crear("div", { className: "acciones" }, crear("a", { className: "boton", href: direccionDeOrden(orden.numero_orden) }, "Abrir la orden")),
  );
}

// ---------------------------------------------------------------- T-02 Orden del técnico

async function mostrarOrden(pantalla, numeroOrden) {
  mostrarCargando(pantalla);
  let expediente;
  try {
    expediente = await cargarExpediente(numeroOrden);
  } catch (error) {
    pantalla.replaceChildren(regresarAMiFila());
    manejarError(error, () => mostrarOrden(pantalla, numeroOrden));
    return;
  }
  const zona = crear("div", { className: "zona-de-trabajo" });
  const contexto = {
    expediente,
    zona,
    numero: expediente.numero_orden,
    yo: empleadoActual()?.id_empleado,
    recargar: () => mostrarOrden(pantalla, expediente.numero_orden),
  };
  pantalla.replaceChildren(
    ...vistaDelExpediente(expediente, {
      acciones: accionesDeLaOrden(contexto),
      zona,
      deTrabajo: (trabajo) => accionesDelTrabajo(contexto, trabajo),
    }),
    regresarAMiFila(),
  );
}

function regresarAMiFila() {
  return crear("div", { className: "acciones" }, crear("a", { className: "boton boton-secundario", href: "#/tecnico" }, "Regresar a mi fila de trabajo"));
}

/** Los botones de la orden según su estado (tabla de botones de §4.3). */
function accionesDeLaOrden(contexto) {
  const { expediente, yo } = contexto;
  const acciones = [];
  const suDiagnostico = expediente.estado === "En Diagnóstico" && expediente.tecnico_de_diagnostico === yo;
  if (suDiagnostico && !expediente.diagnostico_fallas) {
    acciones.push(boton("Registrar diagnóstico", () => abrirDiagnostico(contexto, false)));
  }
  if (suDiagnostico && expediente.diagnostico_fallas && expediente.cotizaciones.length === 0) {
    acciones.push(secundario("Corregir diagnóstico", () => abrirDiagnostico(contexto, true)));
  }
  if (expediente.estado === "En Reparación") {
    acciones.push(secundario("Reportar falla adicional", () => abrirFallaAdicional(contexto)));
  }
  return acciones;
}

/** Los botones de cada trabajo: solo en los suyos. */
function accionesDelTrabajo(contexto, trabajo) {
  if (trabajo.tecnico !== contexto.yo) {
    return [];
  }
  const acciones = [];
  if (trabajo.estado === "Pendiente" && ESTADOS_EN_TRABAJO.includes(contexto.expediente.estado)) {
    acciones.push(boton("Iniciar trabajo", (elemento) => iniciarTrabajo(contexto, trabajo, elemento)));
  }
  if (trabajo.estado === "En Progreso") {
    acciones.push(boton("Terminar trabajo", (elemento) => terminarTrabajo(contexto, trabajo, elemento)));
  }
  const abierto = trabajo.estado === "Pendiente" || trabajo.estado === "En Progreso";
  if (abierto && ESTADOS_EN_TRABAJO.includes(contexto.expediente.estado)) {
    acciones.push(secundario("Solicitar refacción", () => abrirSolicitud(contexto, trabajo)));
  }
  return acciones;
}

/** Abre un formulario en la zona de trabajo, debajo del encabezado del expediente. */
function abrirEnLaZona(contexto, forma) {
  limpiarAvisos();
  contexto.zona.replaceChildren(forma);
  forma.scrollIntoView({ block: "start" });
  forma.querySelector("input, select, textarea")?.focus();
}

const cerrarLaZona = (contexto) => secundario("Regresar", () => contexto.zona.replaceChildren());

// Registrar o corregir el diagnóstico (CA-032, CA-033); al corregir, con el texto anterior (AU-26).
function abrirDiagnostico(contexto, esCorreccion) {
  const { expediente } = contexto;
  const guardar = crear("button", { type: "submit", className: "boton" }, esCorreccion ? "Guardar corrección" : "Guardar diagnóstico");
  const forma = formulario(
    esCorreccion ? "Corregir diagnóstico" : "Registrar diagnóstico",
    areaDeTexto("diagnostico-fallas", "Fallas encontradas", {
      maxLength: 1000,
      value: esCorreccion ? expediente.diagnostico_fallas : "",
    }),
    areaDeTexto("diagnostico-recomendaciones", "Recomendaciones (opcional)", {
      maxLength: 1000,
      value: esCorreccion ? (expediente.diagnostico_recomendaciones ?? "") : "",
    }),
    crear("div", { className: "acciones" }, guardar, cerrarLaZona(contexto)),
  );
  abrirEnLaZona(contexto, forma);
  const fallas = forma.querySelector("#diagnostico-fallas");
  const recomendaciones = forma.querySelector("#diagnostico-recomendaciones");
  alEnviar(forma, () => {
    if (!revisarObligatorios([[fallas, "Escriba las fallas encontradas."]])) {
      return;
    }
    const cuerpo = { fallas: fallas.value.trim(), recomendaciones: recomendaciones.value.trim() };
    return enviar(
      guardar,
      () => pedir("POST", "/api/ordenes/{numero}/diagnostico", { enRuta: { numero: contexto.numero }, cuerpo }),
      (diagnostico) => {
        const hecho = esCorreccion ? "corregido" : "guardado";
        mostrarExito(`Diagnóstico de la orden ${diagnostico.numero_orden} ${hecho}.`);
        contexto.recargar();
      },
    );
  });
}

// Iniciar un trabajo (CA-014, CA-046): sin confirmación, solo el botón ocupado.
function iniciarTrabajo(contexto, trabajo, elemento) {
  return enviar(
    elemento,
    () => pedir("POST", "/api/ordenes/{numero}/trabajos/{id}/inicio", { enRuta: { numero: contexto.numero, id: trabajo.id } }),
    (respuesta) => {
      mostrarExito(`Trabajo «${trabajo.descripcion}» iniciado. La orden está «${respuesta.estado_orden}».`);
      contexto.recargar();
    },
  );
}

// Terminar un trabajo (CA-015; AU-30): un trabajo terminado no regresa.
async function terminarTrabajo(contexto, trabajo, elemento) {
  const confirmado = await confirmar({
    titulo: `¿Terminó el trabajo «${trabajo.descripcion}»?`,
    lineas: [`Orden ${contexto.numero}`, { destacado: contexto.expediente.placas }, "Un trabajo terminado ya no se puede regresar."],
    verbo: "Terminar trabajo",
  });
  if (!confirmado) {
    return;
  }
  await enviar(
    elemento,
    () => pedir("POST", "/api/ordenes/{numero}/trabajos/{id}/completado", { enRuta: { numero: contexto.numero, id: trabajo.id } }),
    (respuesta) => {
      mostrarExito(`Trabajo «${trabajo.descripcion}» terminado. La orden está «${respuesta.estado_orden}».`);
      contexto.recargar();
    },
  );
}

// Solicitar una refacción que no hay en el taller (CA-019, CA-020, CA-062; AU-28).
function abrirSolicitud(contexto, trabajo) {
  const pedirla = crear("button", { type: "submit", className: "boton" }, "Pedir la refacción a Compras");
  const forma = formulario(
    `Solicitar refacción para «${trabajo.descripcion}»`,
    campo("solicitud-refaccion", "Refacción", { maxLength: 200, autocomplete: "off" }),
    campo("solicitud-cantidad", "Cantidad", { type: "number", min: 1, step: 1, inputMode: "numeric", value: "1" }),
    crear("div", { className: "acciones" }, pedirla, cerrarLaZona(contexto)),
  );
  abrirEnLaZona(contexto, forma);
  const refaccion = forma.querySelector("#solicitud-refaccion");
  const cantidad = forma.querySelector("#solicitud-cantidad");
  alEnviar(forma, async () => {
    if (!revisarObligatorios([[refaccion, "Escriba la refacción que necesita."]])) {
      return;
    }
    const texto = cantidad.value.trim();
    if (!/^\d+$/.test(texto) || Number(texto) < 1) {
      marcarCampo(cantidad, "Escriba una cantidad de 1 o más.");
      cantidad.focus();
      return;
    }
    marcarCampo(cantidad, null);
    const cuerpo = { id_trabajo: trabajo.id, refaccion: refaccion.value.trim(), cantidad: Number(texto) };
    const confirmado = await confirmar({
      titulo: "¿Solicitar la refacción a Compras?",
      lineas: [`Orden ${contexto.numero}`, `Trabajo: «${trabajo.descripcion}»`, `Refacción: ${cuerpo.refaccion}`, `Cantidad: ${cuerpo.cantidad}`],
      verbo: "Solicitar refacción",
    });
    if (!confirmado) {
      return;
    }
    await enviar(
      pedirla,
      () => pedir("POST", "/api/ordenes/{numero}/solicitudes-de-compra", { enRuta: { numero: contexto.numero }, cuerpo }),
      (solicitud) => {
        mostrarExito(`Refacción «${cuerpo.refaccion}» solicitada a Compras. La orden está «${solicitud.estado_orden}».`);
        contexto.recargar();
      },
    );
  });
}

// Reportar una falla adicional al asesor (CA-034; AU-29): botón ocupado y confirmación.
function abrirFallaAdicional(contexto) {
  const reportar = crear("button", { type: "submit", className: "boton" }, "Reportar falla al asesor");
  const forma = formulario(
    "Reportar falla adicional",
    areaDeTexto("falla-descripcion", "Descripción de la falla", { maxLength: 1000 }),
    crear("div", { className: "acciones" }, reportar, cerrarLaZona(contexto)),
  );
  abrirEnLaZona(contexto, forma);
  const descripcion = forma.querySelector("#falla-descripcion");
  alEnviar(forma, async () => {
    if (!revisarObligatorios([[descripcion, "Describa la falla que encontró."]])) {
      return;
    }
    const confirmado = await confirmar({
      titulo: "¿Reportar la falla al asesor?",
      lineas: [`Orden ${contexto.numero}`, { destacado: contexto.expediente.placas }, descripcion.value.trim()],
      verbo: "Reportar falla",
    });
    if (!confirmado) {
      return;
    }
    await enviar(
      reportar,
      () =>
        pedir("POST", "/api/ordenes/{numero}/fallas-adicionales", {
          enRuta: { numero: contexto.numero },
          cuerpo: { descripcion: descripcion.value.trim() },
        }),
      (falla) => {
        mostrarExito(`Falla adicional de la orden ${falla.numero_orden} reportada al asesor.`);
        contexto.recargar();
      },
    );
  });
}
