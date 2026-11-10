// Lee la dirección después de `#` y muestra la pantalla que corresponde (interfaz-web.md §3).
// Con `#`, recargar la página nunca da error.

import { mostrarConsulta } from "./cliente.js";
import { crear, limpiarAvisos, mostrarAvisosPendientes } from "./ui.js";

const pantalla = document.getElementById("pantalla");

// P-01 Inicio
function mostrarInicio() {
  pantalla.replaceChildren(
    crear(
      "section",
      { className: "tarjeta" },
      crear("h1", {}, "Bienvenido a AutoFix Pro"),
      crear("p", { className: "nota" }, "¿Qué desea hacer?"),
      crear(
        "div",
        { className: "botones-grandes" },
        crear("a", { className: "boton", href: "#/consulta" }, "Consulta tu vehículo"),
        crear("a", { className: "boton boton-secundario", href: "#/entrar" }, "Entrar como personal del taller"),
      ),
    ),
  );
}

const PANTALLAS_PUBLICAS = {
  "/inicio": mostrarInicio,
  "/consulta": mostrarConsulta,
};

function rutaActual() {
  const ruta = window.location.hash.replace(/^#/, "");
  return ruta === "" ? "/inicio" : ruta;
}

export function irA(direccion) {
  window.location.replace(direccion);
}

function navegar() {
  const ruta = rutaActual();
  const mostrar = PANTALLAS_PUBLICAS[ruta];
  if (!mostrar) {
    irA("#/inicio");
    return;
  }
  limpiarAvisos();
  mostrarAvisosPendientes();
  window.scrollTo(0, 0);
  mostrar(pantalla);
}

window.addEventListener("hashchange", navegar);
navegar();
