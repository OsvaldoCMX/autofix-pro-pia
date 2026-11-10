// Pantallas del Gerente de Taller (interfaz-web.md §4.4). Se construyen en la Fase 17.

import { pantallaEnPreparacion } from "./ui.js";

// Direcciones de interfaz-web.md §3; el menú del encabezado muestra estas entradas.
export const MENU = [
  { texto: "Cotizaciones por aprobar", direccion: "#/gerente" },
  { texto: "Órdenes", direccion: "#/gerente/ordenes" },
  { texto: "Ingresos del día", direccion: "#/gerente/ingresos" },
];

export function mostrar(ruta, pantalla) {
  pantallaEnPreparacion(pantalla, MENU, ruta);
}
