// Pantallas del Personal de Compras (interfaz-web.md §4.5). Se construyen en la Fase 17.

import { pantallaEnPreparacion } from "./ui.js";

// Direcciones de interfaz-web.md §3; el menú del encabezado muestra estas entradas.
export const MENU = [
  { texto: "Solicitudes pendientes", direccion: "#/compras" },
];

export function mostrar(ruta, pantalla) {
  pantallaEnPreparacion(pantalla, MENU, ruta);
}
