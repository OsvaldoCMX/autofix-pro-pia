// Todas las llamadas a la API, la clave de acceso y el manejo de errores (interfaz-web.md §2, §3).
// La página muestra el `detalle` de los errores tal cual lo manda la API (regla 6 de CLAUDE.md).

const LLAVE_DE_LA_CLAVE = "autofix.clave";

export const MENSAJE_SIN_CONEXION =
  "El sistema está iniciando, espere unos segundos e intente de nuevo.";

/** La API respondió con un error: `message` es su `detalle`, sin cambios. */
export class ErrorDeLaApi extends Error {
  constructor(detalle, codigo) {
    super(detalle);
    this.codigo = codigo;
  }
}

/** No hubo respuesta, o la respuesta no es de la API (por ejemplo, Render despertando). */
export class SinConexion extends Error {
  constructor() {
    super(MENSAJE_SIN_CONEXION);
  }
}

// sessionStorage puede no estar disponible (navegación privada estricta): la página sigue sin él.
export function leerClave() {
  try {
    return sessionStorage.getItem(LLAVE_DE_LA_CLAVE);
  } catch {
    return null;
  }
}

export function guardarClave(clave) {
  try {
    sessionStorage.setItem(LLAVE_DE_LA_CLAVE, clave);
  } catch {
    // Sin almacenamiento, la sesión dura hasta recargar la página.
  }
}

export function borrarClave() {
  try {
    sessionStorage.removeItem(LLAVE_DE_LA_CLAVE);
  } catch {
    // Nada que borrar.
  }
}

let alVencerLaSesion = () => {};

/** Qué hacer cuando la API dice que la clave guardada ya no sirve (la define sesion.js). */
export function cuandoVenzaLaSesion(funcion) {
  alVencerLaSesion = funcion;
}

function encabezados(clave, conCuerpo) {
  const resultado = { Accept: "application/json" };
  // Una clave con letras como «ñ» no puede ir en el encabezado: se envía sin clave y la API
  // responde con su propio mensaje de clave no válida.
  if (clave && /^[\x20-\x7e]+$/.test(clave)) {
    resultado.Authorization = `Bearer ${clave}`;
  }
  if (conCuerpo) {
    resultado["Content-Type"] = "application/json";
  }
  return resultado;
}

async function leerJson(respuesta) {
  try {
    return await respuesta.json();
  } catch {
    return undefined;
  }
}

/** "/api/ordenes/{numero}" con `{ numero: "OS-0001" }` → "/api/ordenes/OS-0001" (AU-38). */
function armarRuta(ruta, enRuta = {}) {
  return ruta.replace(/\{(\w+)\}/g, (_, nombre) => encodeURIComponent(String(enRuta[nombre])));
}

async function enviar(metodo, ruta, { cuerpo, parametros, clave, enRuta } = {}) {
  const url = new URL(armarRuta(ruta, enRuta), window.location.origin);
  for (const [nombre, valor] of Object.entries(parametros ?? {})) {
    url.searchParams.set(nombre, valor);
  }
  const conCuerpo = cuerpo !== undefined;
  let respuesta;
  try {
    respuesta = await fetch(url, {
      method: metodo,
      headers: encabezados(clave, conCuerpo),
      body: conCuerpo ? JSON.stringify(cuerpo) : undefined,
    });
  } catch {
    throw new SinConexion();
  }
  const datos = await leerJson(respuesta);
  if (respuesta.ok && datos !== undefined) {
    return datos;
  }
  if (typeof datos?.detalle !== "string") {
    throw new SinConexion();
  }
  throw new ErrorDeLaApi(datos.detalle, respuesta.status);
}

/**
 * Llamada de una pantalla del personal: usa la clave guardada. La ruta se escribe como en el
 * contrato de la API y sus partes van en `enRuta`:
 * `pedir("POST", "/api/ordenes/{numero}/entrega", { enRuta: { numero } })`.
 */
export async function pedir(metodo, ruta, opciones = {}) {
  try {
    return await enviar(metodo, ruta, { ...opciones, clave: leerClave() });
  } catch (error) {
    if (error instanceof ErrorDeLaApi && error.codigo === 401) {
      borrarClave();
      alVencerLaSesion();
    }
    throw error;
  }
}

/** Inicio de sesión (P-03): con la clave que escribió el empleado, todavía sin guardar. */
export function consultarSesion(clave) {
  return enviar("GET", "/api/sesion", { clave });
}

// Consulta pública del cliente (P-02): sin clave.
export function consultarEstadoDeOrden(orden, placas) {
  return enviar("GET", "/api/consulta-de-estado", { parametros: { orden, placas } });
}
