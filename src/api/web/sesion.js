// Sesión del personal (interfaz-web.md §3). La clave es el mismo token que acepta la API
// (ADR-012) y se guarda en sessionStorage. La página solo decide qué menú mostrar: los permisos
// los decide la API en cada llamada.

import { borrarClave, consultarSesion, ErrorDeLaApi, guardarClave, leerClave } from "./api.js";
import { avisarAlLlegar, campo, conBotonOcupado, crear, limpiarAvisos, manejarError, marcarCampo } from "./ui.js";

export const SESION_TERMINADA = "Su sesión terminó. Escriba de nuevo su clave de acceso.";

let empleado = null;

/** `{ id_empleado, nombre, rol, puesto }` de la API, o `null` si nadie ha entrado. */
export function empleadoActual() {
  return empleado;
}

/** Hay una clave guardada de antes de recargar la página que todavía no se revisa. */
export function hayClavePorRevisar() {
  return empleado === null && leerClave() !== null;
}

/** Al recargar, se vuelve a preguntar a la API quién es: no se confía en lo guardado. */
export async function recuperarSesion() {
  if (!hayClavePorRevisar()) {
    return;
  }
  try {
    empleado = await consultarSesion(leerClave());
  } catch (error) {
    if (!(error instanceof ErrorDeLaApi) || ![401, 403].includes(error.codigo)) {
      throw error;
    }
    borrarClave();
    avisarAlLlegar("info", SESION_TERMINADA);
  }
}

export function cerrarSesion() {
  borrarClave();
  empleado = null;
}

/** La API dijo que la clave ya no sirve (la llamada ya borró la clave). */
export function sesionVencida() {
  empleado = null;
  avisarAlLlegar("info", SESION_TERMINADA);
}

// P-03 Inicio de sesión
export function mostrarEntrar(pantalla, alEntrar) {
  const boton = crear("button", { type: "submit", className: "boton" }, "Entrar");
  const formulario = crear(
    "form",
    { className: "tarjeta", noValidate: true },
    crear("h1", {}, "Entrar como personal del taller"),
    crear("p", { className: "nota" }, "Escriba la clave de acceso que le dio el taller."),
    campo("clave", "Clave de acceso", { type: "password", autocomplete: "current-password" }),
    crear(
      "div",
      { className: "acciones" },
      boton,
      crear("a", { className: "boton boton-secundario", href: "#/inicio" }, "Regresar al inicio"),
    ),
  );
  pantalla.replaceChildren(formulario);

  const entrada = formulario.querySelector("#clave");
  const entrar = async () => {
    limpiarAvisos();
    const clave = entrada.value.trim();
    if (clave === "") {
      marcarCampo(entrada, "Escriba su clave de acceso.");
      entrada.focus();
      return;
    }
    marcarCampo(entrada, null);
    try {
      empleado = await conBotonOcupado(boton, "Entrando…", () => consultarSesion(clave));
    } catch (error) {
      if (error instanceof ErrorDeLaApi) {
        marcarCampo(entrada, "");
        entrada.select();
      }
      manejarError(error, entrar);
      entrada.focus();
      return;
    }
    guardarClave(clave);
    alEntrar(empleado);
  };
  formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();
    entrar();
  });
  entrada.focus();
}
