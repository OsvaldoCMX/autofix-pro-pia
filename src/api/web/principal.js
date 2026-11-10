// Lee la dirección después de `#` y muestra la pantalla que corresponde (interfaz-web.md §3).
// Con `#`, recargar la página nunca da error. Mandar a cada quien a su menú solo ayuda a navegar:
// los permisos los decide la API en cada llamada.

import { actualizarCampana, mostrarAlertas } from "./alertas.js";
import { cuandoVenzaLaSesion } from "./api.js";
import * as asesor from "./asesor.js";
import * as caja from "./caja.js";
import { mostrarConsulta } from "./cliente.js";
import * as compras from "./compras.js";
import * as gerente from "./gerente.js";
import {
  cerrarSesion,
  empleadoActual,
  hayClavePorRevisar,
  mostrarEntrar,
  recuperarSesion,
  sesionVencida,
} from "./sesion.js";
import * as tecnico from "./tecnico.js";
import {
  avisarAlLlegar,
  crear,
  limpiarAvisos,
  manejarError,
  mostrarAvisosPendientes,
  mostrarCargando,
} from "./ui.js";

const pantalla = document.getElementById("pantalla");
const OTRO_PUESTO = "Esa pantalla es de otro puesto del taller. Le mostramos su menú.";
const ALERTAS = "/alertas"; // P-04: de todos los puestos.

// Cada puesto tiene sus direcciones; el rol es el que manda la API en `GET /api/sesion`.
const PUESTOS = {
  Asesor: { inicio: "/asesor", modulo: asesor },
  Técnico: { inicio: "/tecnico", modulo: tecnico },
  Gerente: { inicio: "/gerente", modulo: gerente },
  Compras: { inicio: "/compras", modulo: compras },
  Caja: { inicio: "/caja", modulo: caja },
};

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
  "/entrar": (destino) => mostrarEntrar(destino, (empleado) => irA(PUESTOS[empleado.rol].inicio)),
};

function rutaActual() {
  const ruta = window.location.hash.replace(/^#/, "");
  return ruta === "" ? "/inicio" : ruta;
}

function irA(ruta) {
  window.location.replace(`#${ruta}`);
}

/** El rol dueño de la dirección (`/gerente/ordenes` → «Gerente»), o `undefined` si es pública. */
function rolDeLaRuta(ruta) {
  return Object.keys(PUESTOS).find((rol) => {
    const { inicio } = PUESTOS[rol];
    return ruta === inicio || ruta.startsWith(`${inicio}/`);
  });
}

/** A dónde debe ir cada quien: sin sesión, al inicio de sesión; con sesión, a su propio menú. */
function destinoDe(ruta, empleado) {
  const menuPropio = empleado ? PUESTOS[empleado.rol].inicio : null;
  if (ruta === ALERTAS) {
    return empleado ? ruta : "/entrar";
  }
  const rol = rolDeLaRuta(ruta);
  if (rol) {
    if (!empleado) {
      return "/entrar";
    }
    if (rol !== empleado.rol) {
      avisarAlLlegar("info", OTRO_PUESTO);
      return menuPropio;
    }
    return ruta;
  }
  if (ruta in PANTALLAS_PUBLICAS) {
    return empleado && ruta !== "/consulta" ? menuPropio : ruta;
  }
  return menuPropio ?? "/inicio";
}

function actualizarEncabezado(empleado, ruta) {
  const menu = document.getElementById("menu");
  const usuario = document.getElementById("usuario");
  menu.hidden = !empleado;
  usuario.hidden = !empleado;
  if (!empleado) {
    menu.replaceChildren();
    return;
  }
  document.getElementById("saludo").textContent = `Hola, ${empleado.nombre} · ${empleado.puesto}`;
  const campana = document.getElementById("campana");
  if (ruta === ALERTAS) {
    campana.setAttribute("aria-current", "page");
  } else {
    campana.removeAttribute("aria-current");
  }
  actualizarCampana();
  menu.replaceChildren(
    ...PUESTOS[empleado.rol].modulo.MENU.map(({ texto, direccion }) => {
      const enlace = crear("a", { href: direccion }, texto);
      if (direccion === `#${ruta}`) {
        enlace.setAttribute("aria-current", "page");
      }
      return enlace;
    }),
  );
}

async function navegar() {
  const ruta = rutaActual();
  limpiarAvisos();
  if (hayClavePorRevisar()) {
    mostrarCargando(pantalla);
  }
  try {
    await recuperarSesion();
  } catch (error) {
    pantalla.replaceChildren();
    manejarError(error, navegar);
    return;
  }
  const empleado = empleadoActual();
  const destino = destinoDe(ruta, empleado);
  if (destino !== ruta) {
    irA(destino);
    return;
  }
  actualizarEncabezado(empleado, ruta);
  mostrarAvisosPendientes();
  window.scrollTo(0, 0);
  const rol = rolDeLaRuta(ruta);
  if (ruta === ALERTAS) {
    mostrarAlertas(pantalla, empleado.rol);
  } else if (rol) {
    PUESTOS[rol].modulo.mostrar(ruta, pantalla);
  } else {
    PANTALLAS_PUBLICAS[ruta](pantalla);
  }
}

cuandoVenzaLaSesion(() => {
  sesionVencida();
  irA("/entrar");
});

document.getElementById("cerrar-sesion").addEventListener("click", () => {
  cerrarSesion();
  irA("/inicio");
});

window.addEventListener("hashchange", navegar);
navegar();
