// Alertas de todos los empleados (P-04, interfaz-web.md §4.1). La campana del encabezado cuenta
// las alertas de hoy (en la hora de Monterrey) y `#/alertas` muestra todas, las más recientes
// arriba, separadas en «Hoy» y «Anteriores». No hay «marcar como leída»: la API no lo tiene.

import { pedir } from "./api.js";
import { diaEnMonterrey, fechaYHora } from "./formato.js";
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

const masRecientesArriba = (alertas) =>
  [...alertas].sort((una, otra) => new Date(otra.creada_en) - new Date(una.creada_en));

/** Pone en la campana el número de alertas de hoy; si la API no responde, la deja sin número. */
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
  const deHoyCuantas = alertas.filter(deHoy).length;
  numero.textContent = String(deHoyCuantas);
  numero.hidden = deHoyCuantas === 0;
  campana.setAttribute("aria-label", `Alertas: ${deHoyCuantas} de hoy`);
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
  const titulo = crear("h1", {}, "Alertas");
  if (alertas.length === 0) {
    pantalla.replaceChildren(crear("section", { className: "tarjeta" }, titulo, crear("p", { className: "nota" }, "No tiene alertas.")));
    return;
  }
  const hoy = alertas.filter(deHoy);
  const anteriores = alertas.filter((alerta) => !deHoy(alerta));
  const secciones = [crear("section", { className: "tarjeta" }, titulo, grupo("Hoy", hoy, rol, "No tiene alertas de hoy."))];
  if (anteriores.length > 0) {
    secciones.push(crear("section", { className: "tarjeta" }, grupo("Anteriores", anteriores, rol)));
  }
  pantalla.replaceChildren(...secciones);
}

function grupo(nombre, alertas, rol, siEstaVacio) {
  const encabezado = crear("h2", {}, nombre);
  if (alertas.length === 0) {
    return crear("div", {}, encabezado, crear("p", { className: "nota" }, siEstaVacio));
  }
  return crear("div", {}, encabezado, crear("ul", { className: "alertas" }, ...alertas.map((alerta) => renglon(alerta, rol))));
}

function renglon(alerta, rol) {
  const destino = ORDEN_DEL_PUESTO[rol];
  const enlace =
    alerta.numero_orden && destino
      ? crear("a", { href: `${destino}${encodeURIComponent(alerta.numero_orden)}` }, `Abrir la orden ${alerta.numero_orden}`)
      : null;
  return crear(
    "li",
    { className: "alerta" },
    crear("span", { className: "nota" }, fechaYHora(alerta.creada_en)),
    crear("p", {}, alerta.mensaje),
    enlace,
  );
}
