// Pantallas del Asesor de Servicio (interfaz-web.md §4.2). Cada botón aparece solo en los estados
// de la tabla de A-03; si aun así la API rechaza la acción, se muestra su mensaje tal cual. La
// página no decide reglas del negocio: el total oficial, el paso por el Gerente (E1) y los
// estados nuevos los dice la respuesta de la API.

import { ErrorDeLaApi, pedir } from "./api.js";
import {
  cargarExpediente,
  descripcionDelCliente,
  vistaDelExpediente,
} from "./expediente.js";
import { aCentavos, deCentavos, dinero, fecha, numero } from "./formato.js";
import {
  areaDeTexto,
  avisarAlLlegar,
  campo,
  casilla,
  conBotonOcupado,
  confirmar,
  crear,
  datos,
  limpiarAvisos,
  lista,
  manejarError,
  marcarCampo,
  mostrarCargando,
  mostrarError,
  mostrarExito,
  revisarObligatorios,
} from "./ui.js";

// Direcciones de interfaz-web.md §3; el menú del encabezado muestra estas entradas.
export const MENU = [
  { texto: "Buscar por placas", direccion: "#/asesor" },
];

const NIVELES_DE_COMBUSTIBLE = ["Reserva", "1/4", "1/2", "3/4", "Lleno"];
const KILOMETRAJE_MAXIMO = 2000000; // Solo ayuda a capturar; el tope lo valida el dominio (AU-10).
const ESTADOS_CON_TRABAJOS_POR_ASIGNAR = ["Autorizada", "En Reparación", "En Espera de Refacción"];
const PENDIENTE_DEL_GERENTE = "Pendiente de Aprobación Gerencial";
const PENDIENTE_DEL_CLIENTE = "Pendiente de Autorización del Cliente";

let siguienteId = 0;
const nuevoId = (prefijo) => `${prefijo}-${++siguienteId}`;

export function mostrar(ruta, pantalla) {
  const orden = /^\/asesor\/orden\/(.+)$/.exec(ruta);
  if (orden) {
    mostrarOrden(pantalla, decodificar(orden[1]));
    return;
  }
  mostrarBusqueda(pantalla);
}

function decodificar(texto) {
  try {
    return decodeURIComponent(texto);
  } catch {
    return texto;
  }
}

function irAOrden(numeroOrden) {
  window.location.hash = `#/asesor/orden/${encodeURIComponent(numeroOrden)}`;
}

function boton(texto, alTocar, clase = "boton") {
  const elemento = crear("button", { type: "button", className: clase }, texto);
  elemento.addEventListener("click", () => alTocar(elemento));
  return elemento;
}

const secundario = (texto, alTocar) => boton(texto, alTocar, "boton boton-secundario");

/** Envía la acción con el botón ocupado. Si sale bien, `alTerminar` recibe la respuesta. */
async function enviar(botonOcupado, llamada, alTerminar) {
  limpiarAvisos();
  let respuesta;
  try {
    respuesta = await conBotonOcupado(botonOcupado, "Guardando…", llamada);
  } catch (error) {
    manejarError(error, () => enviar(botonOcupado, llamada, alTerminar));
    return;
  }
  alTerminar(respuesta);
}

function formulario(titulo, ...contenido) {
  return crear("form", { className: "tarjeta", noValidate: true }, crear("h2", {}, titulo), ...contenido);
}

function alEnviar(forma, accion) {
  forma.addEventListener("submit", (evento) => {
    evento.preventDefault();
    accion();
  });
}

const valorDe = (contenedor, selector) => contenedor.querySelector(selector).value.trim();
const opcional = (texto) => (texto === "" ? null : texto);

// ---------------------------------------------------------------- A-01 Buscar por placas

function mostrarBusqueda(pantalla) {
  const botonBuscar = crear("button", { type: "submit", className: "boton" }, "Buscar");
  const porPlacas = crear(
    "form",
    { className: "tarjeta", noValidate: true },
    crear("h1", {}, "Buscar por placas"),
    crear("p", { className: "nota" }, "Escriba las placas del vehículo que llega al taller."),
    campo("buscar-placas", "Placas", { autocomplete: "off", maxLength: 20 }),
    crear("div", { className: "acciones" }, botonBuscar),
  );
  const porOrden = formulario(
    "Abrir una orden",
    campo("abrir-orden", "Número de orden", { autocomplete: "off", maxLength: 20, placeholder: "OS-0001" }),
    crear("div", { className: "acciones" }, crear("button", { type: "submit", className: "boton boton-secundario" }, "Abrir expediente")),
  );
  const resultado = crear("div");
  pantalla.replaceChildren(porPlacas, resultado, porOrden);

  const placas = porPlacas.querySelector("#buscar-placas");
  const buscar = async () => {
    limpiarAvisos();
    resultado.replaceChildren();
    if (!revisarObligatorios([[placas, "Escriba las placas."]])) {
      return;
    }
    const texto = placas.value.trim();
    try {
      const vehiculo = await conBotonOcupado(botonBuscar, "Buscando…", () =>
        pedir("GET", "/api/vehiculos/{placas}", { enRuta: { placas: texto } }),
      );
      resultado.replaceChildren(vehiculoEncontrado(pantalla, vehiculo));
    } catch (error) {
      if (error instanceof ErrorDeLaApi && error.codigo === 404) {
        mostrarError(error.message);
        resultado.replaceChildren(vehiculoNoRegistrado(pantalla, texto));
        return;
      }
      manejarError(error, buscar);
    }
  };
  alEnviar(porPlacas, buscar);

  const orden = porOrden.querySelector("#abrir-orden");
  alEnviar(porOrden, () => {
    limpiarAvisos();
    if (revisarObligatorios([[orden, "Escriba el número de orden."]])) {
      irAOrden(orden.value.trim().toUpperCase());
    }
  });
  placas.focus();
}

function datosDelCliente(cliente) {
  const responsable = [cliente.responsable_nombre, cliente.responsable_telefono, cliente.responsable_correo]
    .filter(Boolean)
    .join(" · ");
  return [
    ["Cliente", cliente.nombre],
    ["Tipo de cliente", cliente.tipo],
    ["Teléfono", cliente.telefono],
    ["Correo", cliente.correo],
    ["Empresa", cliente.empresa],
    ["Responsable de Flotilla", responsable],
  ];
}

function vehiculoEncontrado(pantalla, vehiculo) {
  const abierta = vehiculo.orden_abierta;
  const acciones = [];
  if (abierta) {
    acciones.push(boton(`Abrir la orden ${abierta.numero_orden}`, () => irAOrden(abierta.numero_orden)));
  } else {
    acciones.push(boton("Registrar nueva orden", () => mostrarNuevaOrden(pantalla, { placas: vehiculo.placas, vehiculo })));
  }
  return crear(
    "section",
    { className: "tarjeta", "aria-label": "Vehículo encontrado" },
    crear("h2", {}, "Vehículo encontrado"),
    crear("p", { className: "placas" }, vehiculo.placas),
    datos([
      ["Vehículo", `${vehiculo.marca} ${vehiculo.modelo} ${vehiculo.anio}`],
      ["VIN", vehiculo.vin],
      ...datosDelCliente(vehiculo.cliente),
    ]),
    abierta
      ? crear("p", { className: "aviso aviso-info" }, `Este vehículo tiene abierta la orden ${abierta.numero_orden} (estado «${abierta.estado}»).`)
      : null,
    crear("div", { className: "acciones" }, ...acciones),
  );
}

function vehiculoNoRegistrado(pantalla, placas) {
  return crear(
    "section",
    { className: "tarjeta" },
    crear("h2", {}, "Vehículo no registrado"),
    crear("p", { className: "placas" }, placas.toUpperCase()),
    crear("div", { className: "acciones" }, boton("Registrar vehículo nuevo", () => mostrarNuevaOrden(pantalla, { placas, vehiculo: null }))),
  );
}

// ---------------------------------------------------------------- A-02 Nueva orden

function aniosPosibles() {
  const ultimo = new Date().getFullYear() + 1; // Modelos del año siguiente (AU-09).
  const anios = [];
  for (let anio = ultimo; anio >= 1900; anio -= 1) {
    anios.push(String(anio));
  }
  return anios;
}

function camposDeParticular(cliente = {}) {
  return [
    campo("cliente-nombre", "Nombre del cliente", { maxLength: 120, autocomplete: "off", value: cliente.nombre ?? "" }),
    campo("cliente-telefono", "Teléfono", { type: "tel", maxLength: 20, autocomplete: "off", value: cliente.telefono ?? "" }),
    campo("cliente-correo", "Correo", { type: "email", maxLength: 120, autocomplete: "off", value: cliente.correo ?? "" }),
  ];
}

/** El vehículo ya está registrado: su cliente no cambia aquí (la API lo exige). */
function bloqueDeClienteExistente(vehiculo) {
  const { cliente } = vehiculo;
  if (cliente.tipo === "Flotilla") {
    return {
      elemento: crear(
        "fieldset",
        {},
        crear("legend", {}, "Cliente"),
        datos(datosDelCliente(cliente)),
        crear("p", { className: "nota" }, "Si algún dato está mal, corríjalo desde «Corregir datos del cliente»."),
      ),
      leer: () => ({ nombre: `${cliente.empresa ?? cliente.nombre} (flotilla)`, cuerpo: { id_cliente: cliente.id_cliente } }),
    };
  }
  return {
    elemento: crear("fieldset", {}, crear("legend", {}, "Cliente"), ...camposDeParticular(cliente)),
    leer: (forma) => {
      const particular = leerClienteParticular(forma);
      if (particular) {
        particular.cuerpo.id_cliente = cliente.id_cliente;
      }
      return particular;
    },
  };
}

/** Vehículo nuevo: cliente particular (va dentro de la orden, AU-07) o empresa de flotilla. */
function bloqueDeClienteNuevo() {
  const tipo = lista("cliente-tipo", "Tipo de cliente", ["Particular", "Flotilla"], { valor: "Particular" });
  const particular = crear("div", {}, ...camposDeParticular());
  const flotilla = bloqueDeFlotilla();
  flotilla.elemento.hidden = true;
  const elegir = tipo.querySelector("select");
  elegir.addEventListener("change", () => {
    particular.hidden = elegir.value !== "Particular";
    flotilla.elemento.hidden = elegir.value !== "Flotilla";
  });
  return {
    elemento: crear("fieldset", {}, crear("legend", {}, "Cliente"), tipo, particular, flotilla.elemento),
    leer: (forma) => (elegir.value === "Flotilla" ? flotilla.leer() : leerClienteParticular(forma)),
  };
}

/**
 * Empresa de flotilla (CA-028, CA-065): se busca y se muestra a su Responsable. Si es nueva, se
 * piden los datos del Responsable y la empresa se registra antes de la orden (`POST /api/clientes`).
 */
function bloqueDeFlotilla() {
  let elegida = null;
  const empresa = campo("flotilla-empresa", "Empresa", { maxLength: 120, autocomplete: "off" });
  const entrada = empresa.querySelector("input");
  const resultados = crear("div", { className: "empresas" });
  const nueva = crear(
    "div",
    { hidden: true },
    crear("p", { className: "aviso aviso-info" }, "Empresa nueva: capture los datos de su Responsable de Flotilla. La empresa se registrará junto con la orden."),
    campo("flotilla-telefono", "Teléfono de la empresa (opcional)", { type: "tel", maxLength: 20, autocomplete: "off" }),
    campo("flotilla-correo", "Correo de la empresa (opcional)", { type: "email", maxLength: 120, autocomplete: "off" }),
    campo("responsable-nombre", "Nombre del Responsable de Flotilla", { maxLength: 120, autocomplete: "off" }),
    campo("responsable-telefono", "Teléfono del Responsable", { type: "tel", maxLength: 20, autocomplete: "off" }),
    campo("responsable-correo", "Correo del Responsable", { type: "email", maxLength: 120, autocomplete: "off" }),
  );
  const elemento = crear(
    "div",
    {},
    empresa,
    crear("div", { className: "acciones" }, secundario("Buscar empresa", (elementoBoton) => buscarEmpresa(elementoBoton))),
    resultados,
    nueva,
  );
  entrada.addEventListener("input", () => {
    elegida = null;
    resultados.replaceChildren();
    nueva.hidden = true;
  });

  function elegir(cliente) {
    elegida = cliente;
    nueva.hidden = true;
    marcarCampo(entrada, null);
    resultados.replaceChildren(
      crear("p", { className: "aviso aviso-exito" }, `Empresa elegida: ${cliente.empresa} · Responsable de Flotilla: ${cliente.responsable_nombre}`),
    );
  }

  function registrarNueva() {
    resultados.replaceChildren();
    nueva.hidden = false;
    nueva.querySelector("input").focus();
  }

  async function buscarEmpresa(elementoBoton) {
    limpiarAvisos();
    if (!revisarObligatorios([[entrada, "Escriba el nombre de la empresa."]])) {
      return;
    }
    let encontradas;
    try {
      encontradas = await conBotonOcupado(elementoBoton, "Buscando…", () =>
        pedir("GET", "/api/clientes", { parametros: { tipo: "Flotilla", empresa: entrada.value.trim() } }),
      );
    } catch (error) {
      manejarError(error, () => buscarEmpresa(elementoBoton));
      return;
    }
    elegida = null;
    if (encontradas.length === 0) {
      registrarNueva();
      return;
    }
    nueva.hidden = true;
    resultados.replaceChildren(
      ...encontradas.map((cliente) =>
        crear(
          "div",
          { className: "empresa" },
          crear("span", {}, `${cliente.empresa} · Responsable: ${[cliente.responsable_nombre, cliente.responsable_telefono].filter(Boolean).join(" · ")}`),
          secundario("Usar esta empresa", () => elegir(cliente)),
        ),
      ),
      secundario("No es ninguna: registrar empresa nueva", registrarNueva),
    );
  }

  function leer() {
    if (elegida) {
      return { nombre: `${elegida.empresa} (flotilla)`, cuerpo: { id_cliente: elegida.id_cliente } };
    }
    if (nueva.hidden) {
      marcarCampo(entrada, entrada.value.trim() === "" ? "Escriba el nombre de la empresa." : "Busque la empresa con «Buscar empresa».");
      entrada.focus();
      return null;
    }
    const [nombre, telefono, correo] = ["#responsable-nombre", "#responsable-telefono", "#responsable-correo"].map((selector) =>
      nueva.querySelector(selector),
    );
    const completos = revisarObligatorios([
      [entrada, "Escriba el nombre de la empresa."],
      [nombre, "Escriba el nombre del Responsable de Flotilla."],
      [telefono, "Escriba el teléfono del Responsable."],
      [correo, "Escriba el correo del Responsable."],
    ]);
    if (!completos) {
      return null;
    }
    const texto = entrada.value.trim();
    return {
      nombre: `${texto} (flotilla nueva) · Responsable: ${nombre.value.trim()}`,
      cuerpo: {},
      // El cliente de flotilla es la empresa: su nombre es el mismo texto de la empresa.
      nuevaEmpresa: {
        nombre: texto,
        tipo: "Flotilla",
        telefono: opcional(valorDe(nueva, "#flotilla-telefono")),
        correo: opcional(valorDe(nueva, "#flotilla-correo")),
        empresa: texto,
        responsable_nombre: nombre.value.trim(),
        responsable_telefono: telefono.value.trim(),
        responsable_correo: correo.value.trim(),
      },
      registrada: elegir,
    };
  }

  return { elemento, leer };
}

function bloqueDeVehiculo(placas, vehiculo) {
  return crear(
    "fieldset",
    {},
    crear("legend", {}, "Vehículo"),
    campo("orden-placas", "Placas", { maxLength: 20, autocomplete: "off", value: placas, readOnly: Boolean(vehiculo) }),
    campo("orden-vin", "VIN (número de serie)", { maxLength: 17, autocomplete: "off", value: vehiculo?.vin ?? "" }),
    campo("orden-marca", "Marca", { maxLength: 60, autocomplete: "off", value: vehiculo?.marca ?? "" }),
    campo("orden-modelo", "Modelo", { maxLength: 60, autocomplete: "off", value: vehiculo?.modelo ?? "" }),
    lista("orden-anio", "Año", aniosPosibles(), { vacia: "Elija el año", valor: vehiculo ? String(vehiculo.anio) : null }),
  );
}

function camposDeRecepcion(prefijo, actual = {}) {
  return [
    campo(`${prefijo}-kilometraje`, "Kilometraje", {
      type: "number",
      min: 0,
      max: KILOMETRAJE_MAXIMO,
      step: 1,
      inputMode: "numeric",
      value: actual.kilometraje ?? "",
    }),
    lista(`${prefijo}-combustible`, "Nivel de combustible", NIVELES_DE_COMBUSTIBLE, {
      vacia: "Elija el nivel",
      valor: actual.nivel_de_combustible,
    }),
    areaDeTexto(`${prefijo}-motivo`, "Motivo de ingreso", { maxLength: 1000, value: actual.motivo_de_ingreso ?? "" }),
  ];
}

/** Revisa y lee los datos de recepción; `null` si falta alguno (la página solo ayuda). */
function leerRecepcion(contenedor, prefijo) {
  const kilometraje = contenedor.querySelector(`#${prefijo}-kilometraje`);
  const combustible = contenedor.querySelector(`#${prefijo}-combustible`);
  const motivo = contenedor.querySelector(`#${prefijo}-motivo`);
  const completos = revisarObligatorios([
    [kilometraje, "Escriba el kilometraje."],
    [combustible, "Elija el nivel de combustible."],
    [motivo, "Escriba el motivo de ingreso."],
  ]);
  if (!completos) {
    return null;
  }
  const kilometros = kilometraje.value.replace(/[\s,]/g, "");
  if (!/^\d+$/.test(kilometros)) {
    marcarCampo(kilometraje, "Escriba el kilometraje con números enteros, sin signos.");
    kilometraje.focus();
    return null;
  }
  return {
    kilometraje: Number(kilometros),
    nivel_de_combustible: combustible.value,
    motivo_de_ingreso: motivo.value.trim(),
  };
}

function mostrarNuevaOrden(pantalla, { placas, vehiculo }) {
  limpiarAvisos();
  const registrar = crear("button", { type: "submit", className: "boton" }, "Registrar orden");
  const cliente = vehiculo ? bloqueDeClienteExistente(vehiculo) : bloqueDeClienteNuevo();
  const forma = crear(
    "form",
    { className: "tarjeta", noValidate: true },
    crear("h1", {}, "Nueva orden"),
    cliente.elemento,
    bloqueDeVehiculo(placas.toUpperCase(), vehiculo),
    crear("fieldset", {}, crear("legend", {}, "Recepción"), ...camposDeRecepcion("orden")),
    crear("div", { className: "acciones" }, registrar, secundario("Regresar", () => mostrarBusqueda(pantalla))),
  );
  pantalla.replaceChildren(forma);
  alEnviar(forma, () => registrarOrden(forma, registrar, cliente.leer));
  window.scrollTo(0, 0);
  forma.querySelector("input:not([readonly]), select")?.focus();
}

function leerVehiculo(forma) {
  const [placas, vin, marca, modelo, anio] = ["#orden-placas", "#orden-vin", "#orden-marca", "#orden-modelo", "#orden-anio"].map(
    (selector) => forma.querySelector(selector),
  );
  const completos = revisarObligatorios([
    [placas, "Escriba las placas."],
    [vin, "Escriba el VIN."],
    [marca, "Escriba la marca."],
    [modelo, "Escriba el modelo."],
    [anio, "Elija el año."],
  ]);
  if (!completos) {
    return null;
  }
  return {
    placas: placas.value.trim(),
    vehiculo: { vin: vin.value.trim(), marca: marca.value.trim(), modelo: modelo.value.trim(), anio: Number(anio.value) },
  };
}

/** El cliente particular se registra junto con la orden (AU-07): `{ cuerpo, nombre }` o `null`. */
function leerClienteParticular(forma) {
  const nombre = forma.querySelector("#cliente-nombre");
  if (!revisarObligatorios([[nombre, "Escriba el nombre del cliente."]])) {
    return null;
  }
  return {
    nombre: nombre.value.trim(),
    cuerpo: {
      cliente: {
        nombre: nombre.value.trim(),
        tipo: "Particular",
        telefono: opcional(valorDe(forma, "#cliente-telefono")),
        correo: opcional(valorDe(forma, "#cliente-correo")),
      },
    },
  };
}

/** Registra primero la empresa de flotilla nueva, si la hay, y después la orden. */
async function enviarOrden(cliente, cuerpo) {
  if (cliente.nuevaEmpresa) {
    const empresa = await pedir("POST", "/api/clientes", { cuerpo: cliente.nuevaEmpresa });
    // Si la orden falla, el siguiente intento ya usa la empresa registrada.
    cliente.registrada(empresa);
    cliente.nuevaEmpresa = null;
    cuerpo.id_cliente = empresa.id_cliente;
  }
  return pedir("POST", "/api/ordenes", { cuerpo });
}

/** `leerCliente(forma)` da `{ nombre, cuerpo, nuevaEmpresa? }` o `null` si falta algún dato. */
async function registrarOrden(forma, registrar, leerCliente) {
  limpiarAvisos();
  // Se revisan todos los bloques para marcar de una vez todo lo que falta.
  const recepcion = leerRecepcion(forma, "orden");
  const vehiculo = leerVehiculo(forma);
  const cliente = leerCliente(forma);
  if (!recepcion || !vehiculo || !cliente) {
    return;
  }
  const cuerpo = { placas: vehiculo.placas, ...recepcion, vehiculo: vehiculo.vehiculo, ...cliente.cuerpo };
  const { marca, modelo, anio } = vehiculo.vehiculo;
  const confirmado = await confirmar({
    titulo: "¿Registrar la orden?",
    lineas: [
      "Placas:",
      { destacado: vehiculo.placas.toUpperCase() },
      `Vehículo: ${marca} ${modelo} ${anio}`,
      `Cliente: ${cliente.nombre}`,
      `Kilometraje: ${numero(recepcion.kilometraje)} km · Combustible: ${recepcion.nivel_de_combustible}`,
      `Motivo: ${recepcion.motivo_de_ingreso}`,
    ],
    verbo: "Registrar orden",
  });
  if (!confirmado) {
    return;
  }
  await enviar(registrar, () => enviarOrden(cliente, cuerpo), (orden) => {
    avisarAlLlegar("exito", orden.mensaje);
    irAOrden(orden.numero_orden);
  });
}

// ---------------------------------------------------------------- A-03 Expediente

async function mostrarOrden(pantalla, numeroOrden) {
  mostrarCargando(pantalla);
  let expediente;
  try {
    expediente = await cargarExpediente(numeroOrden);
  } catch (error) {
    pantalla.replaceChildren(regresarABuscar());
    manejarError(error, () => mostrarOrden(pantalla, numeroOrden));
    return;
  }
  const zona = crear("div", { className: "zona-de-trabajo" });
  const contexto = {
    pantalla,
    expediente,
    zona,
    numero: expediente.numero_orden,
    recargar: () => mostrarOrden(pantalla, expediente.numero_orden),
  };
  pantalla.replaceChildren(
    ...vistaDelExpediente(expediente, {
      acciones: accionesDeLaOrden(contexto),
      zona,
      deCotizacion: (cotizacion) => accionesDeCotizacion(contexto, cotizacion),
    }),
    regresarABuscar(),
  );
}

function regresarABuscar() {
  return crear("div", { className: "acciones" }, crear("a", { className: "boton boton-secundario", href: "#/asesor" }, "Regresar a buscar por placas"));
}

/** Los botones de la orden según su estado (tabla de botones de A-03). */
function accionesDeLaOrden(contexto) {
  const { expediente } = contexto;
  const { estado } = expediente;
  const conDiagnostico = Boolean(expediente.diagnostico_fallas);
  const acciones = [];
  if (estado === "Recibida") {
    acciones.push(boton("Asignar técnico para el diagnóstico", () => abrirAsignacionDeDiagnostico(contexto, false)));
  }
  if (estado === "En Diagnóstico" && !conDiagnostico) {
    acciones.push(boton("Cambiar técnico de diagnóstico", () => abrirAsignacionDeDiagnostico(contexto, true)));
  }
  if (estado === "En Diagnóstico" && conDiagnostico && expediente.cotizaciones.length === 0) {
    acciones.push(boton("Generar cotización", () => mostrarEditor(contexto, "generar")));
  }
  const hayPendientes = expediente.trabajos.some((trabajo) => trabajo.estado === "Pendiente");
  if (ESTADOS_CON_TRABAJOS_POR_ASIGNAR.includes(estado) && hayPendientes) {
    acciones.push(boton("Asignar trabajos", () => abrirAsignacionDeTrabajos(contexto)));
  }
  if (estado === "Pagada" || estado === "Por Cobrar (Crédito)") {
    acciones.push(boton("Entregar vehículo", (elemento) => entregar(contexto, elemento)));
  }
  if (estado === "Cotizada" && expediente.rechazo_total) {
    acciones.push(boton("Entregar sin reparación", (elemento) => entregarSinReparacion(contexto, elemento)));
  }
  if (estado === "Recibida" || estado === "En Diagnóstico") {
    acciones.push(boton("Cancelar orden", (elemento) => cancelar(contexto, elemento), "boton boton-peligro"));
  }
  return acciones;
}

function accionesDeCotizacion(contexto, cotizacion) {
  const acciones = [];
  const delCliente = cotizacion.estado === PENDIENTE_DEL_CLIENTE;
  if (delCliente && !cotizacion.fecha_presentacion) {
    acciones.push(boton("Presentar cotización al cliente", (elemento) => presentar(contexto, cotizacion, elemento)));
  }
  if (delCliente) {
    acciones.push(boton("Registrar decisión del cliente", () => mostrarDecision(contexto, cotizacion)));
  }
  if (cotizacion.estado === "Requiere Ajuste") {
    acciones.push(boton("Ajustar cotización", () => mostrarEditor(contexto, "ajustar", cotizacion)));
  }
  if (delCliente || cotizacion.estado === PENDIENTE_DEL_GERENTE) {
    acciones.push(secundario("Corregir cotización", () => mostrarEditor(contexto, "corregir", cotizacion)));
  }
  return acciones;
}

/** Abre un formulario en la zona de trabajo, debajo del encabezado del expediente. */
function abrirEnLaZona(contexto, forma) {
  limpiarAvisos();
  contexto.zona.replaceChildren(forma);
  forma.scrollIntoView({ block: "start" });
  forma.querySelector("input, select, textarea")?.focus();
}

const cerrarLaZona = (contexto) => secundario("Regresar", () => contexto.zona.replaceChildren());

async function opcionesDeTecnicos(contexto) {
  contexto.zona.replaceChildren(crear("p", { className: "tarjeta cargando" }, "Cargando…"));
  try {
    const tecnicos = await pedir("GET", "/api/tecnicos");
    return tecnicos.map((tecnico) => ({ valor: tecnico.id_empleado, texto: tecnico.nombre }));
  } catch (error) {
    contexto.zona.replaceChildren();
    manejarError(error, () => contexto.recargar());
    return null;
  }
}

const textoElegido = (elegir) => elegir.options[elegir.selectedIndex].textContent;

// Asignar o cambiar el técnico de diagnóstico (CA-035, CA-053, CA-054; AU-12, AU-13).
async function abrirAsignacionDeDiagnostico(contexto, esCambio) {
  const opciones = await opcionesDeTecnicos(contexto);
  if (!opciones) {
    return;
  }
  const titulo = esCambio ? "Cambiar técnico de diagnóstico" : "Asignar técnico para el diagnóstico";
  const asignar = crear("button", { type: "submit", className: "boton" }, "Asignar técnico");
  const forma = formulario(
    titulo,
    lista("tecnico-diagnostico", "Técnico", opciones, { vacia: "Elija un técnico" }),
    crear("div", { className: "acciones" }, asignar, cerrarLaZona(contexto)),
  );
  abrirEnLaZona(contexto, forma);
  const elegir = forma.querySelector("#tecnico-diagnostico");
  alEnviar(forma, async () => {
    if (!revisarObligatorios([[elegir, "Elija un técnico."]])) {
      return;
    }
    const nombre = textoElegido(elegir);
    const confirmado = await confirmar({
      titulo: `¿Asignar el diagnóstico de la orden ${contexto.numero} a ${nombre}?`,
      lineas: [{ destacado: contexto.expediente.placas }],
      verbo: "Asignar técnico",
    });
    if (!confirmado) {
      return;
    }
    await enviar(
      asignar,
      () => pedir("POST", "/api/ordenes/{numero}/asignacion-diagnostico", { enRuta: { numero: contexto.numero }, cuerpo: { tecnico: elegir.value } }),
      (orden) => {
        mostrarExito(`Diagnóstico de la orden ${orden.numero_orden} asignado a ${nombre}. La orden está «${orden.estado}».`);
        contexto.recargar();
      },
    );
  });
}

const entreComillas = (textos) => {
  const citados = textos.map((texto) => `«${texto}»`);
  return citados.length > 1 ? `${citados.slice(0, -1).join(", ")} y ${citados.at(-1)}` : citados[0];
};

// Asignar trabajos autorizados a un técnico (CA-011, CA-036).
async function abrirAsignacionDeTrabajos(contexto) {
  const opciones = await opcionesDeTecnicos(contexto);
  if (!opciones) {
    return;
  }
  const pendientes = contexto.expediente.trabajos.filter((trabajo) => trabajo.estado === "Pendiente");
  const asignar = crear("button", { type: "submit", className: "boton", disabled: true }, "Asignar los trabajos marcados");
  const casillas = pendientes.map((trabajo) => {
    const asignado = trabajo.tecnico_nombre ?? trabajo.tecnico;
    const texto = `${trabajo.descripcion} (${dinero(trabajo.importe)})${asignado ? ` · ahora con ${asignado}` : ""}`;
    return casilla(`trabajo-${trabajo.id}`, texto, { value: String(trabajo.id) });
  });
  const forma = formulario(
    "Asignar trabajos",
    crear("p", { className: "nota" }, "Marque los trabajos y elija al técnico que los hará."),
    crear("div", { className: "casillas" }, ...casillas),
    lista("tecnico-trabajos", "Técnico", opciones, { vacia: "Elija un técnico" }),
    crear("div", { className: "acciones" }, asignar, cerrarLaZona(contexto)),
  );
  abrirEnLaZona(contexto, forma);
  const marcados = () => [...forma.querySelectorAll(".casillas input:checked")];
  forma.addEventListener("change", () => {
    asignar.disabled = marcados().length === 0;
  });
  const elegir = forma.querySelector("#tecnico-trabajos");
  alEnviar(forma, async () => {
    const ids = marcados().map((entrada) => Number(entrada.value));
    if (ids.length === 0 || !revisarObligatorios([[elegir, "Elija un técnico."]])) {
      return;
    }
    const nombre = textoElegido(elegir);
    const descripciones = pendientes.filter((trabajo) => ids.includes(trabajo.id)).map((trabajo) => trabajo.descripcion);
    const confirmado = await confirmar({
      titulo: `¿Asignar ${entreComillas(descripciones)} a ${nombre}?`,
      lineas: [`Orden ${contexto.numero}`],
      verbo: "Asignar trabajos",
    });
    if (!confirmado) {
      return;
    }
    await enviar(
      asignar,
      () => pedir("POST", "/api/ordenes/{numero}/asignacion-trabajos", { enRuta: { numero: contexto.numero }, cuerpo: { ids_trabajos: ids, tecnico: elegir.value } }),
      (respuesta) => {
        mostrarExito(`Trabajos asignados a ${nombre}. La orden está «${respuesta.estado}».`);
        contexto.recargar();
      },
    );
  });
}

// Presentar la cotización al cliente (CA-006, CA-051): sin confirmación, solo el botón ocupado.
function presentar(contexto, cotizacion, elemento) {
  return enviar(
    elemento,
    () => pedir("POST", "/api/cotizaciones/{id}/presentacion", { enRuta: { id: cotizacion.id } }),
    (respuesta) => {
      mostrarExito(`Cotización ${respuesta.id} presentada al cliente. Desde ahora corre el plazo de 48 horas para su respuesta.`);
      contexto.recargar();
    },
  );
}

/** Folio, placas y cliente: lo que identifica a la orden en las confirmaciones (AU-24, AU-25). */
function identificacion(expediente) {
  return [`Orden ${expediente.numero_orden}`, { destacado: expediente.placas }, `Cliente: ${descripcionDelCliente(expediente)}`];
}

// Entregar el vehículo (CA-041, CA-042).
async function entregar(contexto, elemento) {
  const confirmado = await confirmar({
    titulo: "¿Entregar el vehículo al cliente?",
    lineas: [...identificacion(contexto.expediente), "La orden se cerrará."],
    verbo: "Entregar vehículo",
  });
  if (!confirmado) {
    return;
  }
  await enviar(
    elemento,
    () => pedir("POST", "/api/ordenes/{numero}/entrega", { enRuta: { numero: contexto.numero } }),
    (entrega) => {
      const credito = entrega.fecha_vencimiento_credito ? ` El crédito vence el ${fecha(entrega.fecha_vencimiento_credito)}.` : "";
      mostrarExito(`Vehículo entregado. La orden ${entrega.numero_orden} quedó «${entrega.estado}».${credito}`);
      contexto.recargar();
    },
  );
}

// Entregar sin reparación tras el rechazo total (CA-043).
async function entregarSinReparacion(contexto, elemento) {
  const confirmado = await confirmar({
    titulo: "¿Entregar el vehículo sin reparación?",
    lineas: [...identificacion(contexto.expediente), "El cliente rechazó todos los trabajos. La orden se cerrará sin reparación."],
    verbo: "Entregar sin reparación",
  });
  if (!confirmado) {
    return;
  }
  await enviar(
    elemento,
    () => pedir("POST", "/api/ordenes/{numero}/entrega-sin-reparacion", { enRuta: { numero: contexto.numero } }),
    (entrega) => {
      mostrarExito(`Vehículo entregado sin reparación. La orden ${entrega.numero_orden} quedó «${entrega.estado}».`);
      contexto.recargar();
    },
  );
}

// Cancelar la orden con motivo obligatorio (CA-044, CA-045; AU-25).
async function cancelar(contexto, elemento) {
  const motivo = await confirmar({
    titulo: "¿Cancelar la orden?",
    lineas: [...identificacion(contexto.expediente), "La orden se cancelará sin costo para el cliente."],
    verbo: "Cancelar orden",
    motivo: "Motivo de la cancelación",
  });
  if (motivo === null) {
    return;
  }
  await enviar(
    elemento,
    () => pedir("POST", "/api/ordenes/{numero}/cancelacion", { enRuta: { numero: contexto.numero }, cuerpo: { motivo } }),
    (orden) => {
      mostrarExito(`La orden ${orden.numero_orden} quedó «${orden.estado}».`);
      contexto.recargar();
    },
  );
}

// ---------------------------------------------------------------- A-04 Decisión del cliente

/** Quién decide lo llena la página con los datos del cliente (AU-15, AU-16). */
function autorizanteDe(expediente) {
  if (expediente.cliente_tipo === "Flotilla") {
    return { nombre: expediente.responsable_nombre, rol: "Responsable de Flotilla", quien: "El Responsable de Flotilla" };
  }
  return { nombre: expediente.cliente_nombre, rol: "Cliente", quien: "El cliente" };
}

function mostrarDecision(contexto, cotizacion) {
  limpiarAvisos();
  const { expediente, pantalla } = contexto;
  const autorizante = autorizanteDe(expediente);
  const registrar = crear("button", { type: "submit", className: "boton", disabled: true }, "Registrar autorización");
  const rechazar = boton("El cliente rechaza todos los trabajos", (elemento) => decidir([], elemento), "boton boton-peligro");
  const casillas = cotizacion.lineas.map((linea) =>
    crear(
      "div",
      { className: "linea-de-decision" },
      crear("span", {}, `${linea.numero}. ${linea.descripcion} — ${dinero(linea.subtotal)}`),
      casilla(nuevoId("autoriza"), "Autoriza", { value: String(linea.numero) }),
    ),
  );
  const forma = crear(
    "form",
    { className: "tarjeta", noValidate: true },
    crear("h1", {}, "Decisión del cliente"),
    crear("p", { className: "placas" }, expediente.placas),
    datos([
      ["Orden", expediente.numero_orden],
      ["Cotización", `${cotizacion.id} · ${cotizacion.tipo} ${cotizacion.version}`],
      ["Total", dinero(cotizacion.total)],
      ["Decide", autorizante.nombre ? `${autorizante.nombre} (${autorizante.rol})` : null],
      ["Empresa", expediente.cliente_tipo === "Flotilla" ? expediente.empresa : null],
    ]),
    crear("p", { className: "nota" }, "Si el nombre está mal, primero corrija los datos del cliente."),
    crear("div", { className: "casillas" }, ...casillas),
    crear("div", { className: "acciones" }, registrar, rechazar, secundario("Regresar al expediente", () => contexto.recargar())),
  );
  pantalla.replaceChildren(forma);
  window.scrollTo(0, 0);
  if (!autorizante.nombre) {
    mostrarError("No sabemos quién decide por este cliente. Corrija primero los datos del cliente.");
    registrar.disabled = true;
    rechazar.disabled = true;
    return;
  }
  const marcadas = () => [...forma.querySelectorAll(".casillas input:checked")].map((entrada) => Number(entrada.value));
  forma.addEventListener("change", () => {
    registrar.disabled = marcadas().length === 0;
  });
  alEnviar(forma, () => {
    if (marcadas().length > 0) {
      decidir(marcadas(), registrar);
    }
  });

  async function decidir(autorizadas, elemento) {
    limpiarAvisos();
    const descripcion = (linea) => linea.descripcion;
    const si = cotizacion.lineas.filter((linea) => autorizadas.includes(linea.numero)).map(descripcion);
    const no = cotizacion.lineas.filter((linea) => !autorizadas.includes(linea.numero)).map(descripcion);
    const rechazoTotal = autorizadas.length === 0;
    const confirmado = await confirmar({
      titulo: rechazoTotal ? "¿Registrar que el cliente rechaza todos los trabajos?" : "¿Registrar la decisión del cliente?",
      lineas: [
        `Orden ${expediente.numero_orden} · Decide: ${autorizante.nombre} (${autorizante.rol})`,
        `${autorizante.quien} autoriza: ${si.length > 0 ? entreComillas(si) : "ningún trabajo"}.`,
        `No autoriza: ${no.length > 0 ? entreComillas(no) : "ninguno"}.`,
      ],
      verbo: rechazoTotal ? "Registrar rechazo" : "Registrar autorización",
    });
    if (!confirmado) {
      return;
    }
    const cuerpo = { lineas_autorizadas: autorizadas, nombre_del_autorizante: autorizante.nombre, rol_del_autorizante: autorizante.rol };
    await enviar(
      elemento,
      () => pedir("POST", "/api/cotizaciones/{id}/decision", { enRuta: { id: cotizacion.id }, cuerpo }),
      (decision) => {
        mostrarExito(`Decisión registrada. La orden ${expediente.numero_orden} quedó «${decision.estado_orden}».`);
        contexto.recargar();
      },
    );
  }
}

// ---------------------------------------------------------------- A-05 Cotización

const TITULOS_DEL_EDITOR = {
  generar: { titulo: "Generar cotización", guardar: "Guardar cotización" },
  ajustar: { titulo: "Ajustar cotización", guardar: "Guardar cotización ajustada" },
  corregir: { titulo: "Corregir cotización", guardar: "Guardar corrección" },
};

/** Envía la cotización por la ruta de cada modo; el total oficial lo calcula la API. */
function enviarCotizacion(modo, contexto, cotizacion, trabajos, motivo) {
  const enRuta = { numero: contexto.numero, id: cotizacion?.id };
  if (modo === "ajustar") {
    return pedir("PUT", "/api/cotizaciones/{id}/lineas", { enRuta, cuerpo: { trabajos } });
  }
  if (modo === "corregir") {
    return pedir("POST", "/api/cotizaciones/{id}/correcciones", { enRuta, cuerpo: { trabajos, motivo } });
  }
  return pedir("POST", "/api/ordenes/{numero}/cotizaciones", { enRuta, cuerpo: { trabajos } });
}

function filaDeRefaccion(refaccion = {}) {
  const fila = crear(
    "div",
    { className: "refaccion" },
    campo(nuevoId("refaccion"), "Refacción", { maxLength: 200, autocomplete: "off", value: refaccion.descripcion ?? "" }),
    campo(nuevoId("cantidad"), "Cantidad", { type: "number", min: 1, step: 1, inputMode: "numeric", value: refaccion.cantidad ?? "1" }),
    campo(nuevoId("precio"), "Precio unitario", { inputMode: "decimal", placeholder: "0.00", autocomplete: "off", value: refaccion.precio_unitario ?? "" }),
  );
  const [descripcion, cantidad, precio] = fila.querySelectorAll("input");
  descripcion.dataset.parte = "descripcion";
  cantidad.dataset.parte = "cantidad";
  precio.dataset.parte = "precio";
  fila.append(secundario("Quitar refacción", () => {
    const editor = fila.closest("form");
    fila.remove();
    editor?.dispatchEvent(new Event("input"));
  }));
  return fila;
}

function bloqueDeTrabajo(trabajo = {}) {
  const refacciones = crear("div", { className: "refacciones" }, ...(trabajo.refacciones ?? []).map(filaDeRefaccion));
  const bloque = crear(
    "fieldset",
    { className: "trabajo" },
    crear("legend", {}, "Trabajo"),
    campo(nuevoId("trabajo"), "Descripción del trabajo", { maxLength: 1000, autocomplete: "off", value: trabajo.descripcion ?? "" }),
    campo(nuevoId("mano"), "Mano de obra", { inputMode: "decimal", placeholder: "0.00", autocomplete: "off", value: trabajo.mano_de_obra ?? "" }),
    crear("h3", {}, "Refacciones"),
    refacciones,
    crear("p", { className: "subtotal" }),
  );
  const [descripcion, manoDeObra] = bloque.querySelectorAll("input");
  descripcion.dataset.parte = "trabajo";
  manoDeObra.dataset.parte = "mano";
  bloque.append(
    crear(
      "div",
      { className: "acciones" },
      secundario("Agregar refacción", () => {
        refacciones.append(filaDeRefaccion());
        refacciones.lastElementChild.querySelector("input").focus();
      }),
      secundario("Quitar trabajo", () => {
        const editor = bloque.closest("form");
        bloque.remove();
        editor?.dispatchEvent(new Event("input"));
      }),
    ),
  );
  return bloque;
}

/** Centavos de un trabajo para el total preliminar; lo que no se entiende cuenta como 0. */
function centavosDelTrabajo(bloque) {
  let total = aCentavos(bloque.querySelector('[data-parte="mano"]').value) ?? 0;
  for (const fila of bloque.querySelectorAll(".refaccion")) {
    const cantidad = Number(fila.querySelector('[data-parte="cantidad"]').value);
    const precio = aCentavos(fila.querySelector('[data-parte="precio"]').value) ?? 0;
    total += Number.isInteger(cantidad) && cantidad > 0 ? cantidad * precio : 0;
  }
  return total;
}

function actualizarTotales(forma, lugarDelTotal) {
  let total = 0;
  const bloques = [...forma.querySelectorAll(".trabajo")];
  bloques.forEach((bloque, indice) => {
    const subtotal = centavosDelTrabajo(bloque);
    total += subtotal;
    bloque.querySelector("legend").textContent = `Trabajo ${indice + 1}`;
    bloque.querySelector(".subtotal").textContent = `Subtotal preliminar: ${dinero(deCentavos(subtotal))}`;
  });
  lugarDelTotal.textContent = `Total preliminar: ${dinero(deCentavos(total))}`;
  return total;
}

const MENSAJE_DE_IMPORTE = "Escriba un importe, por ejemplo 1500.00 (sin signo de menos).";

/** Lee y revisa los trabajos: la lista para la API, o `null` si hay que corregir algo. */
function leerTrabajos(forma) {
  const bloques = [...forma.querySelectorAll(".trabajo")];
  let primero = null;
  const revisar = (entrada, valido, mensaje) => {
    marcarCampo(entrada, valido ? null : mensaje);
    primero ??= valido ? null : entrada;
  };
  const trabajos = bloques.map((bloque, indice) => {
    const descripcion = bloque.querySelector('[data-parte="trabajo"]');
    const mano = bloque.querySelector('[data-parte="mano"]');
    revisar(descripcion, descripcion.value.trim() !== "", "Escriba qué trabajo se hará.");
    revisar(mano, aCentavos(mano.value) !== null, MENSAJE_DE_IMPORTE);
    const refacciones = [...bloque.querySelectorAll(".refaccion")].map((fila) => {
      const nombre = fila.querySelector('[data-parte="descripcion"]');
      const cantidad = fila.querySelector('[data-parte="cantidad"]');
      const precio = fila.querySelector('[data-parte="precio"]');
      revisar(nombre, nombre.value.trim() !== "", "Escriba la refacción.");
      revisar(cantidad, /^\d+$/.test(cantidad.value.trim()) && Number(cantidad.value) >= 1, "Escriba una cantidad de 1 o más.");
      revisar(precio, aCentavos(precio.value) !== null, MENSAJE_DE_IMPORTE);
      return {
        descripcion: nombre.value.trim(),
        cantidad: Number(cantidad.value),
        precio_unitario: deCentavos(aCentavos(precio.value) ?? 0),
      };
    });
    return {
      numero: indice + 1,
      descripcion: descripcion.value.trim(),
      mano_de_obra: deCentavos(aCentavos(mano.value) ?? 0),
      refacciones,
    };
  });
  primero?.focus();
  return primero === null ? trabajos : null;
}

/**
 * A-05: generar, ajustar o corregir una cotización. Muestra un total preliminar mientras se
 * captura; el total oficial y si va al Gerente los dice la respuesta de la API.
 */
function mostrarEditor(contexto, modo, cotizacion = null) {
  limpiarAvisos();
  const { pantalla, expediente } = contexto;
  const textos = TITULOS_DEL_EDITOR[modo];
  const guardar = crear("button", { type: "submit", className: "boton" }, textos.guardar);
  const total = crear("p", { className: "total-preliminar" });
  const trabajos = crear("div", { className: "trabajos" });
  const lineas = cotizacion?.lineas ?? [{}];
  trabajos.append(...lineas.map(bloqueDeTrabajo));
  const forma = crear(
    "form",
    { className: "tarjeta", noValidate: true },
    crear("h1", {}, textos.titulo),
    crear("p", { className: "placas" }, expediente.placas),
    datos([
      ["Orden", expediente.numero_orden],
      ["Cotización", cotizacion ? `${cotizacion.id} · ${cotizacion.tipo} ${cotizacion.version}` : null],
      ["Total actual", cotizacion ? dinero(cotizacion.total) : null],
      ["Observaciones del Gerente", modo === "ajustar" ? (cotizacion.observaciones_del_gerente ?? "—") : null],
    ]),
    modo === "corregir"
      ? crear("p", { className: "aviso aviso-info" }, "La cotización se volverá a presentar al cliente; si es la inicial y supera $15,000.00, regresará al Gerente.")
      : null,
    trabajos,
    crear("div", { className: "acciones" }, secundario("Agregar trabajo", () => {
      trabajos.append(bloqueDeTrabajo());
      actualizarTotales(forma, total);
      trabajos.lastElementChild.querySelector("input").focus();
    })),
    total,
    crear("p", { className: "nota" }, "El total oficial lo calcula el sistema al guardar."),
    modo === "corregir" ? areaDeTexto("motivo-correccion", "Motivo de la corrección", { maxLength: 1000 }) : null,
    crear("div", { className: "acciones" }, guardar, secundario("Regresar al expediente", () => contexto.recargar())),
  );
  pantalla.replaceChildren(forma);
  window.scrollTo(0, 0);
  forma.addEventListener("input", () => actualizarTotales(forma, total));
  actualizarTotales(forma, total);
  forma.querySelector("input")?.focus();
  alEnviar(forma, () => guardarCotizacion(contexto, modo, cotizacion, forma, guardar));
}

async function guardarCotizacion(contexto, modo, cotizacion, forma, guardar) {
  limpiarAvisos();
  const bloques = [...forma.querySelectorAll(".trabajo")];
  if (bloques.length === 0) {
    mostrarError("Agregue al menos un trabajo.");
    return;
  }
  const trabajos = leerTrabajos(forma);
  const motivo = forma.querySelector("#motivo-correccion");
  if (!trabajos || (motivo && !revisarObligatorios([[motivo, "Escriba el motivo de la corrección."]]))) {
    return;
  }
  const total = deCentavos(actualizarTotales(forma, forma.querySelector(".total-preliminar")));
  const enCero = bloques
    .filter((bloque) => centavosDelTrabajo(bloque) === 0)
    .map((bloque) => `Atención: el trabajo «${bloque.querySelector('[data-parte="trabajo"]').value.trim()}» vale $0.00.`);
  const numeroOrden = contexto.numero;
  const titulos = {
    generar: `¿Guardar la cotización de la orden ${numeroOrden}?`,
    ajustar: `¿Guardar la cotización ${cotizacion?.id} ajustada?`,
    corregir: `¿Guardar la corrección de la cotización ${cotizacion?.id}?`,
  };
  const confirmado = await confirmar({
    titulo: titulos[modo],
    lineas: [
      cotizacion ? `Total anterior: ${dinero(cotizacion.total)}` : null,
      `Total preliminar: ${dinero(total)}`,
      ...enCero,
      "El total oficial lo calcula el sistema al guardar.",
    ].filter(Boolean),
    verbo: TITULOS_DEL_EDITOR[modo].guardar,
  });
  if (!confirmado) {
    return;
  }
  await enviar(
    guardar,
    () => enviarCotizacion(modo, contexto, cotizacion, trabajos, motivo?.value.trim()),
    (guardada) => {
      mostrarExito(`Cotización ${guardada.id} guardada. Total: ${dinero(guardada.total)}. Estado: «${guardada.estado}».`);
      contexto.recargar();
    },
  );
}
