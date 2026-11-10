// Pantallas del Técnico (interfaz-web.md §4.3). Se construyen en la Fase 17.

import { pantallaEnPreparacion } from "./ui.js";

// Direcciones de interfaz-web.md §3; el menú del encabezado muestra estas entradas.
export const MENU = [
  { texto: "Mi fila de trabajo", direccion: "#/tecnico" },
];

export function mostrar(ruta, pantalla) {
  pantallaEnPreparacion(pantalla, MENU, ruta);
}
