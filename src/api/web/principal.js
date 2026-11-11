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
  icono,
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

/** Tarjeta grande con ícono que lleva a una pantalla (portada y menú de cada puesto). */
function tarjetaDeOpcion({ texto, direccion, icono: nombreDelIcono, detalle }, actual = false) {
  const tarjeta = crear(
    "a",
    { className: "tarjeta-opcion", href: direccion },
    icono(nombreDelIcono, "icono icono-grande"),
    crear(
      "span",
      { className: "tarjeta-opcion-textos" },
      crear("span", { className: "tarjeta-opcion-texto" }, texto),
      detalle ? crear("span", { className: "tarjeta-opcion-detalle" }, detalle) : null,
    ),
  );
  if (actual) {
    tarjeta.setAttribute("aria-current", "page");
  }
  return tarjeta;
}

// P-01 Inicio
function mostrarInicio() {
  pantalla.replaceChildren(
    crear(
      "section",
      { className: "portada" },
      icono("llave", "icono portada-logo"),
      crear("h1", {}, "AutoFix Pro"),
      crear("p", { className: "portada-frase" }, "Consulte cómo va el servicio de su vehículo o entre al sistema del taller."),
      crear(
        "div",
        { className: "opciones" },
        tarjetaDeOpcion({ texto: "Consulta tu vehículo", direccion: "#/consulta", icono: "auto", detalle: "Con su número de orden y sus placas." }),
        tarjetaDeOpcion({ texto: "Personal del taller", direccion: "#/entrar", icono: "llave", detalle: "Entre con su clave de acceso." }),
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

/** Arriba de las pantallas del menú del puesto, sus opciones como tarjetas grandes con ícono. */
function actualizarTarjetasDelMenu(empleado, ruta) {
  const tarjetas = document.getElementById("menu-tarjetas");
  const opciones = empleado ? PUESTOS[empleado.rol].modulo.MENU : [];
  const enElMenu = opciones.some(({ direccion }) => direccion === `#${ruta}`);
  tarjetas.hidden = !enElMenu;
  tarjetas.replaceChildren(
    ...(enElMenu ? opciones.map((opcion) => tarjetaDeOpcion(opcion, opcion.direccion === `#${ruta}`)) : []),
  );
}

function actualizarEncabezado(empleado, ruta) {
  const menu = document.getElementById("menu");
  const usuario = document.getElementById("usuario");
  menu.hidden = !empleado;
  usuario.hidden = !empleado;
  actualizarTarjetasDelMenu(empleado, ruta);
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
    actualizarTarjetasDelMenu(null, ruta);
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
