// P-02 Consulta tu vehículo: pública, sin clave y sin modificar nada (CA-037, CA-038, AU-37).

import { consultarEstadoDeOrden } from "./api.js";
import { fechaYHora } from "./formato.js";
import { campo, conBotonOcupado, crear, etiquetaDeEstado, limpiarAvisos, manejarError, marcarCampo } from "./ui.js";

// Frase debajo del estado, para el cliente (interfaz-web.md §5).
const FRASE_DEL_ESTADO = {
  Recibida: "Recibimos su vehículo y abrimos su orden de servicio.",
  "En Diagnóstico": "Un técnico está revisando su vehículo.",
  Cotizada: "La cotización está lista; el taller le dará los detalles para que decida.",
  Autorizada: "Usted autorizó los trabajos; pronto empezaremos la reparación.",
  "En Reparación": "Estamos reparando su vehículo.",
  "En Espera de Refacción": "Estamos esperando una pieza para continuar.",
  "Pausada por Retiro de Vehículo":
    "Usted se llevó el vehículo mientras llega una pieza; al regresarlo continuamos.",
  "Lista para Entrega": "Su vehículo está listo. Puede pasar a pagar y recogerlo.",
  Pagada: "El pago está registrado; puede recoger su vehículo.",
  "Por Cobrar (Crédito)": "El servicio se cargó al crédito de su empresa; puede recoger el vehículo.",
  Cerrada: "Su vehículo ya fue entregado. ¡Gracias por su visita!",
  "Cerrada sin Reparación": "Su vehículo se entregó sin reparación, sin costo.",
  Cancelada: "La orden se canceló a petición suya, sin costo.",
};

function resultado(consulta) {
  return crear(
    "section",
    { className: "tarjeta", "aria-label": "Estado de su vehículo" },
    crear("h2", {}, `Orden ${consulta.numero_orden}`),
    etiquetaDeEstado(consulta.estado),
    crear("p", { className: "frase-de-estado" }, FRASE_DEL_ESTADO[consulta.estado] ?? ""),
    crear(
      "dl",
      { className: "datos" },
      crear("dt", {}, "Fecha de ingreso"),
      crear("dd", {}, fechaYHora(consulta.fecha_ingreso)),
      crear("dt", {}, "Última actualización"),
      crear("dd", {}, fechaYHora(consulta.ultima_actualizacion)),
    ),
  );
}

/** La página solo pide los dos datos; si no coinciden, lo dice la API. */
function camposVacios(orden, placas) {
  const vacios = [];
  for (const [entrada, mensaje] of [
    [orden, "Escriba el número de orden."],
    [placas, "Escriba las placas."],
  ]) {
    const vacio = entrada.value.trim() === "";
    marcarCampo(entrada, vacio ? mensaje : null);
    if (vacio) {
      vacios.push(entrada);
    }
  }
  return vacios;
}

export function mostrarConsulta(pantalla) {
  const boton = crear("button", { type: "submit", className: "boton" }, "Consultar");
  const formulario = crear(
    "form",
    { className: "tarjeta", noValidate: true },
    crear("h1", {}, "Consulta tu vehículo"),
    crear("p", { className: "nota" }, "Escriba el número de orden y las placas de su vehículo."),
    campo("orden", "Número de orden", { placeholder: "OS-0001", autocomplete: "off", maxLength: 20 }),
    campo("placas", "Placas", { autocomplete: "off", maxLength: 20 }),
    crear("div", { className: "acciones" }, boton, crear("a", { className: "boton boton-secundario", href: "#/inicio" }, "Regresar al inicio")),
  );
  const zonaDeResultado = crear("div");
  pantalla.replaceChildren(formulario, zonaDeResultado);

  const orden = formulario.querySelector("#orden");
  const placas = formulario.querySelector("#placas");
  const consultar = async () => {
    limpiarAvisos();
    zonaDeResultado.replaceChildren();
    const vacios = camposVacios(orden, placas);
    if (vacios.length > 0) {
      vacios[0].focus();
      return;
    }
    try {
      const consulta = await conBotonOcupado(boton, "Consultando…", () =>
        consultarEstadoDeOrden(orden.value.trim(), placas.value.trim()),
      );
      zonaDeResultado.replaceChildren(resultado(consulta));
    } catch (error) {
      manejarError(error, consultar);
    }
  };
  formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();
    consultar();
  });
  orden.focus();
}
