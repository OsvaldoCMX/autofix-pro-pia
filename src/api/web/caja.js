// Pantallas del Personal de Caja (interfaz-web.md §4.6). Se construyen en la Fase 17.

import { pantallaEnPreparacion } from "./ui.js";

// Direcciones de interfaz-web.md §3; el menú del encabezado muestra estas entradas.
export const MENU = [
  { texto: "Buscar orden", direccion: "#/caja" },
];

export function mostrar(ruta, pantalla) {
  pantallaEnPreparacion(pantalla, MENU, ruta);
}
