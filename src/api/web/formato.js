// Formatos de la página (interfaz-web.md §1.4). La API manda los importes como texto ("1500.00")
// y las fechas en UTC; aquí solo se les da formato. El dinero nunca se convierte a número decimal.

const ZONA_DEL_TALLER = "America/Monterrey";

const FECHA_Y_HORA = new Intl.DateTimeFormat("es-MX", {
  timeZone: ZONA_DEL_TALLER,
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

/** "1500.00" → "$1,500.00"; "-35.5" → "-$35.50". Trabaja con el texto, sin sumar decimales. */
export function dinero(importe) {
  const texto = String(importe).trim();
  const partes = /^(-?)(\d+)(?:\.(\d{1,2}))?$/.exec(texto);
  if (!partes) {
    return texto;
  }
  const [, signo, enteros, centavos = ""] = partes;
  const conComas = enteros.replace(/^0+(?=\d)/, "").replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${signo}$${conComas}.${centavos.padEnd(2, "0")}`;
}

/** Fecha de la API (UTC) → "dd/mm/aaaa hh:mm" en la hora de Monterrey. */
export function fechaYHora(textoIso) {
  const fecha = new Date(textoIso);
  if (Number.isNaN(fecha.getTime())) {
    return String(textoIso);
  }
  const partes = Object.fromEntries(
    FECHA_Y_HORA.formatToParts(fecha).map(({ type, value }) => [type, value]),
  );
  return `${partes.day}/${partes.month}/${partes.year} ${partes.hour}:${partes.minute}`;
}

// Grupo de color de cada estado de la orden (interfaz-web.md §1.3).
const GRUPO_DE_ESTADO = {
  Recibida: "azul",
  "En Diagnóstico": "azul",
  Cotizada: "ambar",
  "En Espera de Refacción": "ambar",
  "Pausada por Retiro de Vehículo": "ambar",
  Autorizada: "morado",
  "En Reparación": "morado",
  "Lista para Entrega": "verde",
  Pagada: "verde",
  "Por Cobrar (Crédito)": "verde",
  Cerrada: "gris",
  "Cerrada sin Reparación": "gris",
  Cancelada: "rojo",
};

export function grupoDeEstado(estado) {
  return GRUPO_DE_ESTADO[estado] ?? "gris";
}
