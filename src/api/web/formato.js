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

/**
 * Importe que escribió el usuario ("1,500.5", "$1500") → centavos enteros (150050), o `null`
 * si no es un importe válido. Solo sirve para el total preliminar: el oficial lo da la API.
 */
export function aCentavos(texto) {
  const limpio = String(texto).replace(/[\s$,]/g, "");
  const partes = /^(\d{1,10})(?:\.(\d{0,2}))?$/.exec(limpio);
  if (!partes) {
    return null;
  }
  const [, enteros, centavos = ""] = partes;
  return Number(enteros) * 100 + Number(centavos.padEnd(2, "0"));
}

/** 150050 → "1500.50", el formato en que la API recibe los importes. */
export function deCentavos(centavos) {
  const texto = String(centavos).padStart(3, "0");
  return `${texto.slice(0, -2)}.${texto.slice(-2)}`;
}

/** 45000 → "45,000". */
export function numero(valor) {
  return String(valor).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/** Fecha sin hora de la API ("2026-11-25") → "25/11/2026", sin pasar por la zona horaria. */
export function fecha(textoFecha) {
  const partes = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(textoFecha));
  return partes ? `${partes[3]}/${partes[2]}/${partes[1]}` : String(textoFecha);
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
