// Pantallas del Asesor de Servicio (interfaz-web.md §4.2). Se construyen en la Fase 16.

import { pantallaEnPreparacion } from "./ui.js";

// Direcciones de interfaz-web.md §3; el menú del encabezado muestra estas entradas.
export const MENU = [
  { texto: "Buscar por placas", direccion: "#/asesor" },
];

export function mostrar(ruta, pantalla) {
  pantallaEnPreparacion(pantalla, MENU, ruta);
}
