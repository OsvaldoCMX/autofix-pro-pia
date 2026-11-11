// Alertas de todos los empleados (P-04, interfaz-web.md §4.1). La campana del encabezado cuenta
// las alertas que llegaron después de la última vez que el empleado abrió `#/alertas` (H6, Fase
// 18); `#/alertas` muestra todas, las más recientes arriba, separadas en «Hoy» y «Anteriores», y
// marca como «Nueva» las que llegaron después de esa visita. La visita se guarda solo en este
// navegador (localStorage): la API no tiene «marcar como leída». Sin visita guardada, o si el
// navegador no deja guardarla, la campana cuenta las alertas de hoy (en la hora de Monterrey).

import { pedir } from "./api.js";
import { diaEnMonterrey, fechaYHora } from "./formato.js";
import { empleadoActual } from "./sesion.js";
import { crear, manejarError, mostrarCargando } from "./ui.js";

// La pantalla de la orden de cada puesto; Compras no abre el expediente (§4.5).
const ORDEN_DEL_PUESTO = {
  Asesor: "#/asesor/orden/",
  Técnico: "#/tecnico/orden/",
  Gerente: "#/gerente/orden/",
  Caja: "#/caja/orden/",
};

const cargarAlertas = () => pedir("GET", "/api/alertas");

const deHoy = (alerta) => diaEnMonterrey(alerta.creada_en) === diaEnMonterrey(new Date());

// ---------------------------------------------------------------- última visita (H6)

const claveDeVisita = () => {
  const empleado = empleadoActual();
  return empleado ? `autofix.alertas-vistas.${empleado.id_empleado}` : null;
};

/** Fecha de la última visita a `#/alertas` de este empleado, o `null` si no hay o falla. */
function ultimaVisita() {
  try {
    const clave = claveDeVisita();
    const guardada = clave ? window.localStorage.getItem(clave) : null;
    const fecha = guardada ? new Date(guardada) : null;
    return fecha && !Number.isNaN(fecha.getTime()) ? fecha : null;
  } catch {
    return null;
  }
}

/** Guarda la visita: ahora, o la alerta más nueva si su hora va adelante del reloj del navegador. */
function guardarVisita(alertas) {
  const fechas = [new Date(), ...alertas.map((alerta) => new Date(alerta.creada_en))];
  const visita = new Date(Math.max(...fechas.map((fecha) => fecha.getTime())));
  try {
    const clave = claveDeVisita();
    if (clave) {
      window.localStorage.setItem(clave, visita.toISOString());
    }
  } catch {
    // Sin localStorage, la campana sigue contando las alertas de hoy.
  }
}

const llegoDespues = (alerta, visita) => new Date(alerta.creada_en) > visita;

/** Las que cuenta la campana: las posteriores a la última visita o, sin visita, las de hoy. */
const sinVer = (alertas, visita) =>
  alertas.filter((alerta) => (visita ? llegoDespues(alerta, visita) : deHoy(alerta)));

const masRecientesArriba = (alertas) =>
  [...alertas].sort((una, otra) => new Date(otra.creada_en) - new Date(una.creada_en));

/** Pone en la campana el número de alertas sin ver; si la API no responde, la deja sin número. */
export async function actualizarCampana() {
  const numero = document.getElementById("campana-numero");
  const campana = document.getElementById("campana");
  let alertas;
  try {
    alertas = await cargarAlertas();
  } catch {
    numero.textContent = "";
    campana.setAttribute("aria-label", "Alertas");
    return;
  }
  ponerNumero(sinVer(alertas, ultimaVisita()).length);
}

function ponerNumero(cuantas) {
  const numero = document.getElementById("campana-numero");
  numero.textContent = String(cuantas);
  numero.hidden = cuantas === 0;
  document.getElementById("campana").setAttribute("aria-label", cuantas === 0 ? "Alertas" : `Alertas: ${cuantas} nuevas`);
}

// ---------------------------------------------------------------- P-04 Alertas

export async function mostrarAlertas(pantalla, rol) {
  mostrarCargando(pantalla);
  let alertas;
  try {
    alertas = masRecientesArriba(await cargarAlertas());
  } catch (error) {
    pantalla.replaceChildren();
    manejarError(error, () => mostrarAlertas(pantalla, rol));
    return;
  }
  const visitaAnterior = ultimaVisita();
  guardarVisita(alertas);
  ponerNumero(0);
  const esNueva = (alerta) => visitaAnterior !== null && llegoDespues(alerta, visitaAnterior);
  const titulo = crear("h1", {}, "Alertas");
  if (alertas.length === 0) {
    pantalla.replaceChildren(crear("section", { className: "tarjeta" }, titulo, crear("p", { className: "nota" }, "No tiene alertas.")));
    return;
  }
  const hoy = alertas.filter(deHoy);
  const anteriores = alertas.filter((alerta) => !deHoy(alerta));
  const secciones = [crear("section", { className: "tarjeta" }, titulo, grupo("Hoy", hoy, rol, esNueva, "No tiene alertas de hoy."))];
  if (anteriores.length > 0) {
    secciones.push(crear("section", { className: "tarjeta" }, grupo("Anteriores", anteriores, rol, esNueva)));
  }
  pantalla.replaceChildren(...secciones);
}

function grupo(nombre, alertas, rol, esNueva, siEstaVacio) {
  const encabezado = crear("h2", {}, nombre);
  if (alertas.length === 0) {
    return crear("div", {}, encabezado, crear("p", { className: "nota" }, siEstaVacio));
  }
  return crear("div", {}, encabezado, crear("ul", { className: "alertas" }, ...alertas.map((alerta) => renglon(alerta, rol, esNueva(alerta)))));
}

function renglon(alerta, rol, nueva) {
  const destino = ORDEN_DEL_PUESTO[rol];
  const enlace =
    alerta.numero_orden && destino
      ? crear("a", { href: `${destino}${encodeURIComponent(alerta.numero_orden)}` }, `Abrir la orden ${alerta.numero_orden}`)
      : null;
  return crear(
    "li",
    { className: nueva ? "alerta alerta-nueva" : "alerta" },
    nueva ? crear("span", { className: "etiqueta-nueva" }, "Nueva") : null,
    crear("span", { className: "nota" }, fechaYHora(alerta.creada_en)),
    crear("p", {}, alerta.mensaje),
    enlace,
  );
}
