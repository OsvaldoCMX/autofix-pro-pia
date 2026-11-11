// Piezas comunes de las pantallas: avisos, «Cargando…», botones ocupados, confirmaciones y
// campos marcados (interfaz-web.md §1 y §2). Todo texto de la API se escribe como texto, nunca
// como HTML.

import { ErrorDeLaApi, MENSAJE_SIN_CONEXION, SinConexion } from "./api.js";
import { grupoDeEstado } from "./formato.js";

/** Crea un elemento: `crear("p", { className: "nota" }, "Texto", otroElemento)`. */
export function crear(etiqueta, atributos = {}, ...hijos) {
  const elemento = document.createElement(etiqueta);
  for (const [nombre, valor] of Object.entries(atributos)) {
    if (nombre in elemento) {
      elemento[nombre] = valor;
    } else {
      elemento.setAttribute(nombre, valor);
    }
  }
  elemento.append(...hijos.filter((hijo) => hijo !== null && hijo !== undefined));
  return elemento;
}

// Avisos

const contenedorDeAvisos = () => document.getElementById("avisos");
let avisosPendientes = [];

export function limpiarAvisos() {
  contenedorDeAvisos().replaceChildren();
}

function mostrarAviso(tipo, texto, boton) {
  const aviso = crear("div", { className: `aviso aviso-${tipo}`, role: tipo === "error" ? "alert" : "status" });
  aviso.append(crear("span", {}, texto));
  if (boton) {
    aviso.append(boton);
  }
  contenedorDeAvisos().append(aviso);
  aviso.scrollIntoView({ block: "nearest" });
}

export const mostrarExito = (texto) => mostrarAviso("exito", texto);
export const mostrarError = (texto) => mostrarAviso("error", texto);
export const mostrarInfo = (texto) => mostrarAviso("info", texto);

/** Aviso que se muestra después de cambiar de pantalla (por ejemplo, «Su sesión terminó…»). */
export function avisarAlLlegar(tipo, texto) {
  avisosPendientes.push({ tipo, texto });
}

export function mostrarAvisosPendientes() {
  for (const { tipo, texto } of avisosPendientes) {
    mostrarAviso(tipo, texto);
  }
  avisosPendientes = [];
}

/** Muestra el error como corresponde: el `detalle` de la API o el aviso de «sistema iniciando». */
export function manejarError(error, reintentar) {
  if (error instanceof SinConexion) {
    const boton = crear("button", { type: "button", className: "boton boton-secundario" }, "Intentar de nuevo");
    boton.addEventListener("click", () => {
      limpiarAvisos();
      reintentar();
    });
    mostrarAviso("error", MENSAJE_SIN_CONEXION, boton);
    return;
  }
  if (error instanceof ErrorDeLaApi) {
    mostrarError(error.message);
    return;
  }
  throw error;
}

// Cargando y botones ocupados

export function mostrarCargando(contenedor) {
  contenedor.replaceChildren(crear("p", { className: "cargando" }, "Cargando…"));
}

/** Deshabilita el botón mientras se envía (contra el doble clic, interfaz-web.md §1.6). */
export async function conBotonOcupado(boton, textoOcupado, accion) {
  const textoOriginal = boton.textContent;
  boton.disabled = true;
  boton.textContent = textoOcupado;
  try {
    return await accion();
  } finally {
    boton.disabled = false;
    boton.textContent = textoOriginal;
  }
}

/** Botón que, al tocarlo, llama `alTocar(boton)`. */
export function boton(texto, alTocar, clase = "boton") {
  const elemento = crear("button", { type: "button", className: clase }, texto);
  elemento.addEventListener("click", () => alTocar(elemento));
  return elemento;
}

export const secundario = (texto, alTocar) => boton(texto, alTocar, "boton boton-secundario");

/** Envía la acción con el botón ocupado. Si sale bien, `alTerminar` recibe la respuesta. */
export async function enviar(botonOcupado, llamada, alTerminar) {
  limpiarAvisos();
  let respuesta;
  try {
    respuesta = await conBotonOcupado(botonOcupado, "Guardando…", llamada);
  } catch (error) {
    manejarError(error, () => enviar(botonOcupado, llamada, alTerminar));
    return;
  }
  alTerminar(respuesta);
}

export function formulario(titulo, ...contenido) {
  return crear("form", { className: "tarjeta", noValidate: true }, crear("h2", {}, titulo), ...contenido);
}

export function alEnviar(forma, accion) {
  forma.addEventListener("submit", (evento) => {
    evento.preventDefault();
    accion();
  });
}

/** Parte de la dirección escrita con `encodeURIComponent` (`OS%2D0001` → `OS-0001`). */
export function decodificar(texto) {
  try {
    return decodeURIComponent(texto);
  } catch {
    return texto;
  }
}

/** Una línea de la confirmación: texto, `{ destacado: "ABC123" }` (letra grande) o un elemento. */
function lineaDeConfirmacion(linea) {
  if (linea instanceof Node) {
    return linea;
  }
  if (linea?.destacado !== undefined) {
    return crear("p", { className: "destacado" }, linea.destacado);
  }
  return crear("p", {}, linea);
}

/**
 * Cuadro de confirmación con el verbo de la acción y «Regresar» (interfaz-web.md §1.5).
 * Responde `true` o `false`; con `motivo` (la etiqueta del campo), responde el texto escrito
 * o `null` si regresó. El motivo es obligatorio: sin texto no se cierra.
 */
export function confirmar({ titulo, lineas = [], verbo, motivo }) {
  return new Promise((resolver) => {
    const regresar = crear("button", { type: "button", className: "boton boton-secundario" }, "Regresar");
    const aceptar = crear("button", { type: "button", className: "boton" }, verbo);
    const campoDeMotivo = motivo ? areaDeTexto("confirmacion-motivo", motivo, { maxLength: 1000 }) : null;
    const cuadro = crear(
      "dialog",
      { className: "confirmacion" },
      crear("h2", {}, titulo),
      ...lineas.map(lineaDeConfirmacion),
      campoDeMotivo,
      crear("div", { className: "acciones" }, aceptar, regresar),
    );
    const cerrar = (respuesta) => {
      cuadro.close();
      cuadro.remove();
      resolver(respuesta);
    };
    aceptar.addEventListener("click", () => {
      if (!campoDeMotivo) {
        cerrar(true);
        return;
      }
      const entrada = campoDeMotivo.querySelector("textarea");
      const texto = entrada.value.trim();
      if (texto === "") {
        marcarCampo(entrada, `Escriba el ${motivo.toLowerCase()}.`);
        entrada.focus();
        return;
      }
      cerrar(texto);
    });
    const noConfirmar = motivo ? null : false;
    regresar.addEventListener("click", () => cerrar(noConfirmar));
    cuadro.addEventListener("cancel", (evento) => {
      evento.preventDefault();
      cerrar(noConfirmar);
    });
    document.body.append(cuadro);
    cuadro.showModal();
    regresar.focus();
  });
}

// Campos y estados

/** Marca el campo en rojo con un mensaje debajo (`""`: solo en rojo); `null` lo deja limpio. */
export function marcarCampo(campo, mensaje) {
  const ayuda = document.getElementById(`${campo.id}-ayuda`);
  campo.setAttribute("aria-invalid", mensaje === null ? "false" : "true");
  if (ayuda) {
    ayuda.textContent = mensaje ?? "";
  }
}

function conEtiqueta(entrada, etiqueta) {
  entrada.setAttribute("aria-describedby", `${entrada.id}-ayuda`);
  return crear(
    "div",
    { className: "campo" },
    crear("label", { htmlFor: entrada.id }, etiqueta),
    entrada,
    crear("span", { className: "ayuda-campo", id: `${entrada.id}-ayuda` }),
  );
}

/**
 * Un campo con su etiqueta y su lugar para el mensaje de error. Un campo de teléfono
 * (`type: "tel"`) no deja escribir letras (H2); el dominio vuelve a revisar el teléfono.
 */
export function campo(id, etiqueta, atributos = {}) {
  const entrada = crear("input", { id, name: id, type: "text", ...atributos });
  if (entrada.type === "tel") {
    entrada.inputMode = "tel";
    entrada.addEventListener("input", () => {
      const permitido = entrada.value.replace(/[^0-9 ()-]/g, "");
      if (permitido !== entrada.value) {
        entrada.value = permitido;
      }
    });
  }
  return conEtiqueta(entrada, etiqueta);
}

/** Campo de texto largo (motivos, descripciones). */
export function areaDeTexto(id, etiqueta, atributos = {}) {
  return conEtiqueta(crear("textarea", { id, name: id, rows: 3, ...atributos }), etiqueta);
}

/**
 * Lista desplegable. `opciones`: textos, o `{ valor, texto }`. Con `vacia`, la primera opción
 * es ese texto y no tiene valor (obliga a elegir).
 */
export function lista(id, etiqueta, opciones, { vacia, valor } = {}) {
  const elegir = crear("select", { id, name: id });
  if (vacia) {
    elegir.append(crear("option", { value: "" }, vacia));
  }
  for (const opcion of opciones) {
    const { valor: v, texto } = typeof opcion === "string" ? { valor: opcion, texto: opcion } : opcion;
    elegir.append(crear("option", { value: v }, texto));
  }
  if (valor !== undefined && valor !== null) {
    elegir.value = valor;
  }
  return conEtiqueta(elegir, etiqueta);
}

/** Casilla con su texto a la derecha; el área para tocar es todo el renglón. */
export function casilla(id, texto, atributos = {}) {
  return crear(
    "label",
    { className: "casilla", htmlFor: id },
    crear("input", { id, name: id, type: "checkbox", ...atributos }),
    crear("span", {}, texto),
  );
}

/**
 * Revisa los campos obligatorios de la página: `[[entrada, "Escriba …"], …]`. Marca los vacíos,
 * lleva el cursor al primero y responde si todos tienen dato. Solo ayuda: la API vuelve a validar.
 */
export function revisarObligatorios(pares) {
  let primero = null;
  for (const [entrada, mensaje] of pares) {
    const vacio = entrada.value.trim() === "";
    marcarCampo(entrada, vacio ? mensaje : null);
    primero ??= vacio ? entrada : null;
  }
  primero?.focus();
  return primero === null;
}

/** Lista `dl` de datos: `[["Placas", "ABC123"], …]`; se omiten los que no tienen valor. */
export function datos(pares) {
  const contenedor = crear("dl", { className: "datos" });
  for (const [titulo, valor] of pares) {
    if (valor !== null && valor !== undefined && valor !== "") {
      contenedor.append(crear("dt", {}, titulo), crear("dd", {}, valor));
    }
  }
  return contenedor;
}

/** Tabla sencilla: encabezados y renglones (cada celda es texto o un elemento). */
export function tabla(encabezados, renglones) {
  return crear(
    "div",
    { className: "tabla-con-desplazamiento" },
    crear(
      "table",
      { className: "tabla" },
      crear("thead", {}, crear("tr", {}, ...encabezados.map((texto) => crear("th", { scope: "col" }, texto)))),
      crear("tbody", {}, ...renglones.map((celdas) => crear("tr", {}, ...celdas.map((celda) => crear("td", {}, celda))))),
    ),
  );
}

/** El estado con su nombre del Glosario y el color de su grupo (interfaz-web.md §1.3). */
export function etiquetaDeEstado(estado) {
  return crear("span", { className: `estado estado-${grupoDeEstado(estado)}` }, estado);
}

// Íconos: dibujos sencillos en SVG escritos aquí mismo, sin librerías ni internet (Fase 18).
const ICONOS = {
  auto: '<path d="M5 11l1.5-4.5A2 2 0 0 1 8.4 5h7.2a2 2 0 0 1 1.9 1.5L19 11"/><rect x="3" y="11" width="18" height="6" rx="2"/><circle cx="7.5" cy="17.5" r="1.5"/><circle cx="16.5" cy="17.5" r="1.5"/>',
  llave: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3.5 17.5a1.4 1.4 0 0 0 2 2l5.8-5.8a4 4 0 0 0 5.4-5.4l-2.4 2.4-2.1-.4-.4-2.1z"/>',
  lupa: '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.4-4.4"/>',
  fila: '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/>',
  aprobar: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 14l2 2 4-4"/>',
  ordenes: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2.5h6V4"/><path d="M9 10h6M9 14h6M9 18h3"/>',
  ingresos: '<circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.5-1-1.6-1.5-3-1.5-1.7 0-3 .8-3 2s1.3 1.7 3 2 3 .8 3 2-1.3 2-3 2c-1.4 0-2.5-.5-3-1.5M12 6v2M12 16v2"/>',
  paquete: '<path d="M3 7.5l9-4.5 9 4.5v9l-9 4.5-9-4.5z"/><path d="M3 7.5l9 4.5 9-4.5M12 12v9"/>',
  cobro: '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M6 10v4M18 10v4"/>',
  campana: '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 21h4"/>',
};

/** Ícono decorativo (`aria-hidden`): el texto de al lado siempre dice qué es. */
export function icono(nombre, clase = "icono") {
  const contenedor = crear("span", { className: clase, "aria-hidden": "true" });
  contenedor.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONOS[nombre]}</svg>`;
  return contenedor;
}
