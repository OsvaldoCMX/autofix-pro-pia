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

/** Cuadro de confirmación con el verbo de la acción y «Regresar» (interfaz-web.md §1.5). */
export function confirmar({ titulo, lineas = [], verbo }) {
  return new Promise((resolver) => {
    const regresar = crear("button", { type: "button", className: "boton boton-secundario" }, "Regresar");
    const aceptar = crear("button", { type: "button", className: "boton" }, verbo);
    const cuadro = crear(
      "dialog",
      { className: "confirmacion" },
      crear("h2", {}, titulo),
      ...lineas.map((linea) => crear("p", {}, linea)),
      crear("div", { className: "acciones" }, aceptar, regresar),
    );
    const cerrar = (respuesta) => {
      cuadro.close();
      cuadro.remove();
      resolver(respuesta);
    };
    aceptar.addEventListener("click", () => cerrar(true));
    regresar.addEventListener("click", () => cerrar(false));
    cuadro.addEventListener("cancel", (evento) => {
      evento.preventDefault();
      cerrar(false);
    });
    document.body.append(cuadro);
    cuadro.showModal();
    regresar.focus();
  });
}

// Campos y estados

/** Marca el campo en rojo con un mensaje debajo; `null` lo deja limpio. */
export function marcarCampo(campo, mensaje) {
  const ayuda = document.getElementById(`${campo.id}-ayuda`);
  campo.setAttribute("aria-invalid", mensaje ? "true" : "false");
  if (ayuda) {
    ayuda.textContent = mensaje ?? "";
  }
}

/** Un campo con su etiqueta y su lugar para el mensaje de error. */
export function campo(id, etiqueta, atributos = {}) {
  const entrada = crear("input", { id, name: id, type: "text", ...atributos });
  entrada.setAttribute("aria-describedby", `${id}-ayuda`);
  return crear(
    "div",
    { className: "campo" },
    crear("label", { htmlFor: id }, etiqueta),
    entrada,
    crear("span", { className: "ayuda-campo", id: `${id}-ayuda` }),
  );
}

/** El estado con su nombre del Glosario y el color de su grupo (interfaz-web.md §1.3). */
export function etiquetaDeEstado(estado) {
  return crear("span", { className: `estado estado-${grupoDeEstado(estado)}` }, estado);
}
