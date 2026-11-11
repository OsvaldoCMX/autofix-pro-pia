// Pantallas del Personal de Caja (interfaz-web.md §4.6). El monto del pago es el total autorizado
// que manda la API (AU-35): la página no lo calcula ni deja escribirlo.

import { pedir } from "./api.js";
import { cargarExpediente, descripcionDelCliente } from "./expediente.js";
import { dinero, fecha, fechaYHora } from "./formato.js";
import {
  alEnviar,
  boton,
  campo,
  confirmar,
  crear,
  datos,
  decodificar,
  enviar,
  etiquetaDeEstado,
  formulario,
  limpiarAvisos,
  lista,
  manejarError,
  mostrarCargando,
  mostrarExito,
  revisarObligatorios,
  secundario,
} from "./ui.js";

// Direcciones de interfaz-web.md §3; el encabezado y las tarjetas del menú muestran estas entradas.
export const MENU = [
  { texto: "Buscar orden", direccion: "#/caja", icono: "cobro" },
];

const FORMAS_DE_PAGO = ["Efectivo", "Tarjeta", "Transferencia"];
const LISTA_PARA_ENTREGA = "Lista para Entrega";

export function mostrar(ruta, pantalla) {
  const orden = /^\/caja\/orden\/(.+)$/.exec(ruta);
  if (orden) {
    mostrarOrden(pantalla, decodificar(orden[1]));
    return;
  }
  mostrarBusqueda(pantalla);
}

// ---------------------------------------------------------------- K-01 Buscar orden

function formularioDeBusqueda() {
  const forma = crear(
    "form",
    { className: "tarjeta", noValidate: true },
    crear("h1", {}, "Buscar orden"),
    campo("caja-orden", "Número de orden", { autocomplete: "off", maxLength: 20, placeholder: "OS-0001" }),
    crear("div", { className: "acciones" }, crear("button", { type: "submit", className: "boton" }, "Buscar")),
  );
  const orden = forma.querySelector("#caja-orden");
  alEnviar(forma, () => {
    limpiarAvisos();
    if (revisarObligatorios([[orden, "Escriba el número de orden."]])) {
      window.location.hash = `#/caja/orden/${encodeURIComponent(orden.value.trim().toUpperCase())}`;
    }
  });
  return forma;
}

function mostrarBusqueda(pantalla) {
  const forma = formularioDeBusqueda();
  pantalla.replaceChildren(forma);
  forma.querySelector("#caja-orden").focus();
}

async function mostrarOrden(pantalla, numeroOrden) {
  mostrarCargando(pantalla);
  let expediente;
  try {
    expediente = await cargarExpediente(numeroOrden);
  } catch (error) {
    pantalla.replaceChildren(formularioDeBusqueda());
    manejarError(error, () => mostrarOrden(pantalla, numeroOrden));
    return;
  }
  const zona = crear("div");
  const contexto = { expediente, zona, numero: expediente.numero_orden, recargar: () => mostrarOrden(pantalla, expediente.numero_orden) };
  const acciones = accionesDeCobro(contexto);
  const cobraDeContado = expediente.estado === LISTA_PARA_ENTREGA && expediente.cliente_tipo === "Particular";
  if (cobraDeContado) {
    zona.append(formularioDePago(contexto));
  }
  pantalla.replaceChildren(
    crear(
      "section",
      { className: "tarjeta", "aria-label": "Datos de la orden" },
      crear("h1", {}, `Orden ${expediente.numero_orden}`),
      etiquetaDeEstado(expediente.estado),
      crear("p", { className: "placas" }, expediente.placas),
      datos([
        ["Cliente", descripcionDelCliente(expediente)],
        ["Tipo de cliente", expediente.cliente_tipo],
        ["Responsable de Flotilla", expediente.responsable_nombre],
        ["Total autorizado", dinero(expediente.total_autorizado)],
        ["Pago", expediente.pago_monto ? `${dinero(expediente.pago_monto)} en ${expediente.pago_forma}` : null],
        ["Fecha del pago", expediente.pago_registrado_en ? fechaYHora(expediente.pago_registrado_en) : null],
        ["Cargo a crédito", expediente.credito_monto ? dinero(expediente.credito_monto) : null],
        ["Vence el crédito", expediente.credito_fecha_vencimiento ? fecha(expediente.credito_fecha_vencimiento) : null],
      ]),
      acciones.length > 0 ? crear("div", { className: "acciones" }, ...acciones) : null,
      acciones.length === 0 && !cobraDeContado
        ? crear("p", { className: "nota" }, "Esta orden no tiene nada por cobrar en su estado actual.")
        : null,
    ),
    zona,
    crear("div", { className: "acciones" }, crear("a", { className: "boton boton-secundario", href: "#/caja" }, "Buscar otra orden")),
  );
}

// ---------------------------------------------------------------- K-02 Cobrar

/**
 * Los botones de cobro según el tipo de cliente y el estado (tabla de §4.6). El pago de contado
 * no lleva botón para abrirlo: su formulario ya aparece debajo de los datos de la orden.
 */
function accionesDeCobro(contexto) {
  const { estado, cliente_tipo: tipo } = contexto.expediente;
  const acciones = [];
  if (estado === LISTA_PARA_ENTREGA && tipo === "Flotilla") {
    acciones.push(boton("Registrar cargo a crédito", (elemento) => cargarACredito(contexto, elemento)));
  }
  if (estado === "Pagada") {
    acciones.push(secundario("Corregir forma de pago", () => abrirCorreccionDeForma(contexto)));
  }
  return acciones;
}

function abrirEnLaZona(contexto, forma) {
  limpiarAvisos();
  contexto.zona.replaceChildren(forma);
  forma.scrollIntoView({ block: "start" });
  forma.querySelector("select")?.focus();
}

const cerrarLaZona = (contexto) => secundario("Regresar", () => contexto.zona.replaceChildren());

function identificacion(expediente) {
  return [`Orden ${expediente.numero_orden}`, { destacado: expediente.placas }, `Cliente: ${descripcionDelCliente(expediente)}`];
}

// Pago de contado de un cliente particular (CA-026; AU-34, AU-35).
function formularioDePago(contexto) {
  const { expediente } = contexto;
  const total = dinero(expediente.total_autorizado);
  const registrar = crear("button", { type: "submit", className: "boton" }, "Registrar pago");
  const forma = formulario(
    "Cobrar",
    campo("pago-monto", "Monto (total autorizado)", { value: total, readOnly: true }),
    lista("pago-forma", "Forma de pago", FORMAS_DE_PAGO, { vacia: "Elija la forma de pago" }),
    crear("div", { className: "acciones" }, registrar),
  );
  const elegir = forma.querySelector("#pago-forma");
  alEnviar(forma, async () => {
    if (!revisarObligatorios([[elegir, "Elija la forma de pago."]])) {
      return;
    }
    const confirmado = await confirmar({
      titulo: `¿Registrar pago de ${total} en ${elegir.value}?`,
      lineas: identificacion(expediente),
      verbo: "Registrar pago",
    });
    if (!confirmado) {
      return;
    }
    await enviar(
      registrar,
      () =>
        pedir("POST", "/api/ordenes/{numero}/pago", {
          enRuta: { numero: contexto.numero },
          cuerpo: { monto: expediente.total_autorizado, forma: elegir.value },
        }),
      (pago) => {
        mostrarExito(`Pago de la orden ${pago.numero_orden} registrado: ${dinero(pago.monto)} en ${pago.forma}. La orden está «${pago.estado}».`);
        contexto.recargar();
      },
    );
  });
  return forma;
}

// Cargo a crédito de una flotilla (CA-039).
async function cargarACredito(contexto, elemento) {
  const { expediente } = contexto;
  const empresa = expediente.empresa ?? expediente.cliente_nombre;
  const confirmado = await confirmar({
    titulo: `¿Registrar cargo a crédito de ${dinero(expediente.total_autorizado)} para ${empresa}?`,
    lineas: [`Orden ${expediente.numero_orden}`, { destacado: expediente.placas }],
    verbo: "Registrar cargo a crédito",
  });
  if (!confirmado) {
    return;
  }
  await enviar(
    elemento,
    () => pedir("POST", "/api/ordenes/{numero}/cargo-a-credito", { enRuta: { numero: contexto.numero } }),
    (cargo) => {
      mostrarExito(`Cargo a crédito de la orden ${cargo.numero_orden} registrado: ${dinero(cargo.monto)}. La orden está «${cargo.estado}».`);
      contexto.recargar();
    },
  );
}

// Corregir la forma de pago mientras la orden está «Pagada» (CA-058; AU-34).
function abrirCorreccionDeForma(contexto) {
  const anterior = contexto.expediente.pago_forma;
  const guardar = crear("button", { type: "submit", className: "boton" }, "Guardar corrección");
  const forma = formulario(
    "Corregir forma de pago",
    crear("p", {}, `Forma de pago registrada: ${anterior}.`),
    lista("pago-forma-nueva", "Forma de pago correcta", FORMAS_DE_PAGO.filter((opcion) => opcion !== anterior), {
      vacia: "Elija la forma de pago",
    }),
    crear("div", { className: "acciones" }, guardar, cerrarLaZona(contexto)),
  );
  abrirEnLaZona(contexto, forma);
  const elegir = forma.querySelector("#pago-forma-nueva");
  alEnviar(forma, async () => {
    if (!revisarObligatorios([[elegir, "Elija la forma de pago."]])) {
      return;
    }
    const confirmado = await confirmar({
      titulo: `¿Cambiar la forma de pago de ${anterior} a ${elegir.value}?`,
      lineas: identificacion(contexto.expediente),
      verbo: "Cambiar forma de pago",
    });
    if (!confirmado) {
      return;
    }
    await enviar(
      guardar,
      () => pedir("PUT", "/api/ordenes/{numero}/pago", { enRuta: { numero: contexto.numero }, cuerpo: { forma: elegir.value } }),
      (pago) => {
        mostrarExito(`Forma de pago de la orden ${pago.numero_orden} corregida: ${pago.forma}.`);
        contexto.recargar();
      },
    );
  });
}
