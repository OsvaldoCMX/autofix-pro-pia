"""Data Mapper: traducción explícita entre los Aggregates y las filas (ADR-004, ADR-009).

Leer reconstruye el Aggregate tal como estaba, sin ejecutar reglas ni generar eventos. Escribir
copia su estado a las columnas; `recibo_numero` y las fotos no están aquí: son de la Fase 10.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from application.puertos import AlertaInterna
from domain.clientes.cliente import Cliente, ResponsableDeFlotilla, TipoCliente
from domain.compartido.valores import VIN, Dinero, NumeroOrden, Placas
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.estados import EstadoCotizacion
from domain.cotizaciones.linea_de_cotizacion import DecisionDeLinea, LineaDeCotizacion
from domain.cotizaciones.valores import (
    Autorizante,
    CorreccionDeCotizacion,
    DecisionDelCliente,
    Recontacto,
    RefaccionCotizada,
    RolDeAutorizante,
    TipoCotizacion,
    TrabajoDecidido,
    VersionCotizacion,
)
from domain.empleados.empleado import Empleado, RolDeEmpleado
from domain.ordenes.estados import EstadoOrden, EstadoSolicitud, EstadoTrabajo
from domain.ordenes.falla_adicional import FallaAdicional
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.solicitud_de_compra import SolicitudDeCompra
from domain.ordenes.trabajo import Trabajo
from domain.ordenes.valores import (
    Cancelacion,
    CargoACredito,
    Diagnostico,
    EstadoDeRecepcion,
    FormaDePago,
    NivelDeCombustible,
    NotaDeResponsabilidad,
    Pago,
)
from domain.vehiculos.vehiculo import Vehiculo

Fila = Mapping[str, Any]


@dataclass(frozen=True)
class FilasDeOrden:
    orden: Fila
    trabajos: Sequence[Fila] = ()
    solicitudes: Sequence[Fila] = ()
    fallas: Sequence[Fila] = ()


@dataclass(frozen=True)
class FilasDeCotizacion:
    cotizacion: Fila
    lineas: Sequence[Fila] = ()
    refacciones: Sequence[Fila] = ()
    recontactos: Sequence[Fila] = ()
    correcciones: Sequence[Fila] = ()


def _monto(dinero: Dinero | None) -> Any:
    return dinero.monto if dinero is not None else None


# ------------------------------------------------------------------ Empleado
def empleado_desde_fila(fila: Fila) -> Empleado:
    return Empleado(fila["id"], fila["nombre"], RolDeEmpleado(fila["rol"]))


def fila_de_empleado(empleado: Empleado) -> dict[str, Any]:
    return {"id": empleado.id_empleado, "nombre": empleado.nombre, "rol": empleado.rol.value}


# ------------------------------------------------------------------ Cliente
def fila_de_cliente(cliente: Cliente) -> dict[str, Any]:
    responsable = cliente.responsable
    return {
        "id": cliente.id_cliente,
        "nombre": cliente.nombre,
        "telefono": cliente.telefono,
        "correo": cliente.correo,
        "tipo": cliente.tipo.value,
        "empresa": cliente.empresa,
        "responsable_nombre": responsable.nombre if responsable else None,
        "responsable_telefono": responsable.telefono if responsable else None,
        "responsable_correo": responsable.correo if responsable else None,
    }


def cliente_desde_fila(fila: Fila) -> Cliente:
    responsable = None
    if fila["responsable_nombre"] is not None:
        responsable = ResponsableDeFlotilla(
            fila["responsable_nombre"],
            fila["responsable_telefono"] or "",
            fila["responsable_correo"] or "",
        )
    return Cliente(
        fila["id"],
        fila["nombre"],
        TipoCliente(fila["tipo"]),
        fila["telefono"],
        fila["correo"],
        fila["empresa"],
        responsable,
    )


# ------------------------------------------------------------------ Vehículo
def fila_de_vehiculo(vehiculo: Vehiculo) -> dict[str, Any]:
    return {
        "placas": str(vehiculo.placas),
        "vin": str(vehiculo.vin),
        "marca": vehiculo.marca,
        "modelo": vehiculo.modelo,
        "anio": vehiculo.anio,
        "id_cliente": vehiculo.id_cliente,
    }


def vehiculo_desde_fila(fila: Fila) -> Vehiculo:
    return Vehiculo(
        Placas(fila["placas"]),
        VIN(fila["vin"]),
        fila["marca"],
        fila["modelo"],
        fila["anio"],
        fila["id_cliente"],
    )


# ------------------------------------------------------------------ Orden de Servicio
def filas_de_orden(orden: OrdenDeServicio) -> FilasDeOrden:
    numero = str(orden.numero)
    return FilasDeOrden(
        _fila_raiz_de_orden(orden),
        [_fila_de_trabajo(numero, trabajo) for trabajo in orden.trabajos],
        [_fila_de_solicitud(numero, solicitud) for solicitud in orden.solicitudes],
        [_fila_de_falla(numero, falla) for falla in orden.fallas_adicionales],
    )


def _fila_raiz_de_orden(orden: OrdenDeServicio) -> dict[str, Any]:
    regreso = orden.estado_antes_de_espera
    return {
        "numero": str(orden.numero),
        "id_cliente": orden.id_cliente,
        "es_cliente_de_flotilla": orden.es_cliente_de_flotilla,
        "placas": str(orden.placas),
        "asesor": orden.asesor,
        "motivo_de_ingreso": orden.motivo_de_ingreso,
        "estado": orden.estado.value,
        "fecha_ingreso": orden.fecha_ingreso,
        "ultima_actualizacion": orden.ultima_actualizacion,
        "tecnico_de_diagnostico": orden.tecnico_de_diagnostico,
        "cotizada": orden.cotizada,
        "rechazo_total": orden.rechazo_total,
        "adicionales_pendientes": orden.adicionales_pendientes,
        "fecha_ingreso_a_fila": orden.fecha_ingreso_a_fila,
        "estado_antes_de_espera": regreso.value if regreso else None,
        "fecha_entrega": orden.fecha_entrega,
        **_columnas_de_recepcion(orden.estado_de_recepcion),
        **_columnas_de_diagnostico(orden.diagnostico),
        **_columnas_de_nota(orden.nota_de_responsabilidad),
        **_columnas_de_pago(orden.pago),
        **_columnas_de_credito(orden.cargo_a_credito),
        **_columnas_de_cancelacion(orden.cancelacion),
    }


def _columnas_de_recepcion(recepcion: EstadoDeRecepcion | None) -> dict[str, Any]:
    return {
        "kilometraje": recepcion.kilometraje if recepcion else None,
        "nivel_combustible": recepcion.nivel_de_combustible.value if recepcion else None,
    }


def _columnas_de_diagnostico(diagnostico: Diagnostico | None) -> dict[str, Any]:
    return {
        "diagnostico_fallas": diagnostico.fallas if diagnostico else None,
        "diagnostico_recomendaciones": diagnostico.recomendaciones if diagnostico else None,
        "diagnostico_registrado_en": diagnostico.registrado_en if diagnostico else None,
    }


def _columnas_de_nota(nota: NotaDeResponsabilidad | None) -> dict[str, Any]:
    return {
        "nota_fecha_salida": nota.fecha_salida if nota else None,
        "nota_firmada": nota.firmada if nota else False,
        "nota_fecha_firma": nota.fecha_firma if nota else None,
    }


def _columnas_de_pago(pago: Pago | None) -> dict[str, Any]:
    return {
        "pago_monto": _monto(pago.monto) if pago else None,
        "pago_forma": pago.forma.value if pago else None,
        "pago_registrado_en": pago.registrado_en if pago else None,
    }


def _columnas_de_credito(credito: CargoACredito | None) -> dict[str, Any]:
    return {
        "credito_monto": _monto(credito.monto) if credito else None,
        "credito_registrado_en": credito.registrado_en if credito else None,
        "credito_fecha_vencimiento": credito.fecha_vencimiento if credito else None,
    }


def _columnas_de_cancelacion(cancelacion: Cancelacion | None) -> dict[str, Any]:
    return {
        "cancelacion_motivo": cancelacion.motivo if cancelacion else None,
        "cancelacion_registrada_en": cancelacion.registrada_en if cancelacion else None,
        "cancelacion_asesor": cancelacion.asesor if cancelacion else None,
    }


def _fila_de_trabajo(numero: str, trabajo: Trabajo) -> dict[str, Any]:
    return {
        "numero_orden": numero,
        "id": trabajo.id,
        "descripcion": trabajo.descripcion,
        "importe": _monto(trabajo.importe),
        "estado": trabajo.estado.value,
        "tecnico": trabajo.tecnico,
        "id_cotizacion": trabajo.id_cotizacion,
        "numero_linea": trabajo.numero_linea,
    }


def _fila_de_solicitud(numero: str, solicitud: SolicitudDeCompra) -> dict[str, Any]:
    return {
        "numero_orden": numero,
        "id": solicitud.id,
        "id_trabajo": solicitud.id_trabajo,
        "refaccion": solicitud.refaccion,
        "cantidad": solicitud.cantidad,
        "fecha_solicitud": solicitud.fecha_solicitud,
        "estado": solicitud.estado.value,
        "fecha_llegada": solicitud.fecha_llegada,
        "fecha_aviso_al_cliente": solicitud.fecha_aviso_al_cliente,
    }


def _fila_de_falla(numero: str, falla: FallaAdicional) -> dict[str, Any]:
    return {
        "numero_orden": numero,
        "id": falla.id,
        "descripcion": falla.descripcion,
        "tecnico": falla.tecnico,
        "reportada_en": falla.reportada_en,
    }


def orden_desde_filas(filas: FilasDeOrden) -> OrdenDeServicio:
    fila = filas.orden
    orden = OrdenDeServicio(
        NumeroOrden(fila["numero"]),
        fila["id_cliente"],
        fila["es_cliente_de_flotilla"],
        Placas(fila["placas"]),
        fila["asesor"],
        fila["motivo_de_ingreso"],
        fila["fecha_ingreso"],
        _recepcion_desde_fila(fila),
    )
    orden.estado = EstadoOrden(fila["estado"])
    orden.ultima_actualizacion = fila["ultima_actualizacion"]
    orden.fecha_ingreso_a_fila = fila["fecha_ingreso_a_fila"]
    orden.tecnico_de_diagnostico = fila["tecnico_de_diagnostico"]
    orden.cotizada = fila["cotizada"]
    orden.rechazo_total = fila["rechazo_total"]
    orden.adicionales_pendientes = fila["adicionales_pendientes"]
    orden.fecha_entrega = fila["fecha_entrega"]
    orden.diagnostico = _diagnostico_desde_fila(fila)
    orden.nota_de_responsabilidad = _nota_desde_fila(fila)
    orden.pago = _pago_desde_fila(fila)
    orden.cargo_a_credito = _credito_desde_fila(fila)
    orden.cancelacion = _cancelacion_desde_fila(fila)
    orden._trabajos = {f["id"]: _trabajo_desde_fila(f) for f in filas.trabajos}
    orden._solicitudes = {f["id"]: _solicitud_desde_fila(f) for f in filas.solicitudes}
    orden._fallas = {f["id"]: _falla_desde_fila(f) for f in filas.fallas}
    return orden


def _recepcion_desde_fila(fila: Fila) -> EstadoDeRecepcion | None:
    """Las órdenes importadas del profesor no traen estado de recepción."""
    if fila["kilometraje"] is None or fila["nivel_combustible"] is None:
        return None
    return EstadoDeRecepcion(fila["kilometraje"], NivelDeCombustible(fila["nivel_combustible"]))


def _diagnostico_desde_fila(fila: Fila) -> Diagnostico | None:
    if fila["diagnostico_fallas"] is None:
        return None
    return Diagnostico(
        fila["diagnostico_fallas"],
        fila["diagnostico_recomendaciones"] or "",
        fila["tecnico_de_diagnostico"],
        fila["diagnostico_registrado_en"],
    )


def _nota_desde_fila(fila: Fila) -> NotaDeResponsabilidad | None:
    if fila["nota_fecha_salida"] is None:
        return None
    return NotaDeResponsabilidad(
        fila["nota_fecha_salida"], fila["nota_firmada"], fila["nota_fecha_firma"]
    )


def _pago_desde_fila(fila: Fila) -> Pago | None:
    if fila["pago_monto"] is None:
        return None
    return Pago(
        Dinero(fila["pago_monto"]), FormaDePago(fila["pago_forma"]), fila["pago_registrado_en"]
    )


def _credito_desde_fila(fila: Fila) -> CargoACredito | None:
    if fila["credito_monto"] is None:
        return None
    return CargoACredito(
        Dinero(fila["credito_monto"]),
        fila["credito_registrado_en"],
        fila["credito_fecha_vencimiento"],
    )


def _cancelacion_desde_fila(fila: Fila) -> Cancelacion | None:
    if fila["cancelacion_motivo"] is None:
        return None
    return Cancelacion(
        fila["cancelacion_motivo"], fila["cancelacion_registrada_en"], fila["cancelacion_asesor"]
    )


def _trabajo_desde_fila(fila: Fila) -> Trabajo:
    trabajo = Trabajo(
        fila["id"],
        fila["descripcion"],
        Dinero(fila["importe"]),
        EstadoTrabajo(fila["estado"]),
        fila["id_cotizacion"],
        fila["numero_linea"],
    )
    trabajo.tecnico = fila["tecnico"]
    return trabajo


def _solicitud_desde_fila(fila: Fila) -> SolicitudDeCompra:
    solicitud = SolicitudDeCompra(
        fila["id"], fila["id_trabajo"], fila["refaccion"], fila["cantidad"], fila["fecha_solicitud"]
    )
    solicitud.estado = EstadoSolicitud(fila["estado"])
    solicitud.fecha_llegada = fila["fecha_llegada"]
    solicitud.fecha_aviso_al_cliente = fila["fecha_aviso_al_cliente"]
    return solicitud


def _falla_desde_fila(fila: Fila) -> FallaAdicional:
    return FallaAdicional(fila["id"], fila["descripcion"], fila["tecnico"], fila["reportada_en"])


# ------------------------------------------------------------------ Cotización
def filas_de_cotizacion(cotizacion: Cotizacion) -> FilasDeCotizacion:
    id_cotizacion = cotizacion.id
    decision = cotizacion.decision
    return FilasDeCotizacion(
        {
            "id": id_cotizacion,
            "numero_orden": str(cotizacion.numero_orden),
            "tipo": cotizacion.tipo.value,
            "version": cotizacion.version.numero,
            "estado": cotizacion.estado.value,
            "total": _monto(cotizacion.total),
            "generada_en": cotizacion.generada_en,
            "fecha_aprobacion_gerencial": cotizacion.fecha_aprobacion_gerencial,
            "observaciones_del_gerente": cotizacion.observaciones_del_gerente,
            "fecha_presentacion": cotizacion.fecha_presentacion,
            "decision_autorizante": decision.autorizante.nombre if decision else None,
            "decision_rol": decision.autorizante.rol.value if decision else None,
            "decision_registrada_en": decision.registrada_en if decision else None,
        },
        [_fila_de_linea(id_cotizacion, linea) for linea in cotizacion.lineas],
        [
            _fila_de_refaccion(id_cotizacion, linea.numero, posicion, refaccion)
            for linea in cotizacion.lineas
            for posicion, refaccion in enumerate(linea.refacciones, start=1)
        ],
        [
            {
                "id_cotizacion": id_cotizacion,
                "asesor": recontacto.asesor,
                "registrado_en": recontacto.registrado_en,
            }
            for recontacto in cotizacion.recontactos
        ],
        [_fila_de_correccion(id_cotizacion, correccion) for correccion in cotizacion.correcciones],
    )


def _fila_de_correccion(id_cotizacion: str, correccion: CorreccionDeCotizacion) -> dict[str, Any]:
    return {
        "id_cotizacion": id_cotizacion,
        "asesor": correccion.asesor,
        "registrada_en": correccion.registrada_en,
        "motivo": correccion.motivo,
        "total_anterior": _monto(correccion.total_anterior),
        "total_nuevo": _monto(correccion.total_nuevo),
        "estado_anterior": correccion.estado_anterior.value,
        "estado_nuevo": correccion.estado_nuevo.value,
        "fecha_presentacion_anterior": correccion.fecha_presentacion_anterior,
        "fecha_aprobacion_gerencial_anterior": correccion.fecha_aprobacion_gerencial_anterior,
    }


def _correccion_desde_fila(fila: Fila) -> CorreccionDeCotizacion:
    return CorreccionDeCotizacion(
        fila["asesor"],
        fila["registrada_en"],
        fila["motivo"],
        Dinero(fila["total_anterior"]),
        Dinero(fila["total_nuevo"]),
        EstadoCotizacion(fila["estado_anterior"]),
        EstadoCotizacion(fila["estado_nuevo"]),
        fila["fecha_presentacion_anterior"],
        fila["fecha_aprobacion_gerencial_anterior"],
    )


def _fila_de_linea(id_cotizacion: str, linea: LineaDeCotizacion) -> dict[str, Any]:
    return {
        "id_cotizacion": id_cotizacion,
        "numero": linea.numero,
        "descripcion": linea.descripcion,
        "mano_de_obra": _monto(linea.mano_de_obra),
        "decision": linea.decision.value if linea.decision else None,
    }


def _fila_de_refaccion(
    id_cotizacion: str, numero_linea: int, posicion: int, refaccion: RefaccionCotizada
) -> dict[str, Any]:
    return {
        "id_cotizacion": id_cotizacion,
        "numero_linea": numero_linea,
        "posicion": posicion,
        "descripcion": refaccion.descripcion,
        "cantidad": refaccion.cantidad,
        "precio_unitario": _monto(refaccion.precio_unitario),
    }


def cotizacion_desde_filas(filas: FilasDeCotizacion) -> Cotizacion:
    fila = filas.cotizacion
    cotizacion = Cotizacion(
        fila["id"],
        NumeroOrden(fila["numero_orden"]),
        TipoCotizacion(fila["tipo"]),
        VersionCotizacion(fila["version"]),
        [_linea_desde_filas(f, filas.refacciones) for f in filas.lineas],
        fila["generada_en"],
    )
    cotizacion.estado = EstadoCotizacion(fila["estado"])
    cotizacion.fecha_aprobacion_gerencial = fila["fecha_aprobacion_gerencial"]
    cotizacion.observaciones_del_gerente = fila["observaciones_del_gerente"]
    cotizacion.fecha_presentacion = fila["fecha_presentacion"]
    cotizacion.decision = _decision_desde_fila(fila, cotizacion)
    cotizacion._recontactos = [
        Recontacto(f["asesor"], f["registrado_en"]) for f in filas.recontactos
    ]
    cotizacion._correcciones = [_correccion_desde_fila(f) for f in filas.correcciones]
    return cotizacion


def _linea_desde_filas(fila: Fila, refacciones: Sequence[Fila]) -> LineaDeCotizacion:
    linea = LineaDeCotizacion(
        fila["numero"],
        fila["descripcion"],
        Dinero(fila["mano_de_obra"]),
        tuple(
            RefaccionCotizada(f["descripcion"], f["cantidad"], Dinero(f["precio_unitario"]))
            for f in refacciones
            if f["numero_linea"] == fila["numero"]
        ),
    )
    linea.decision = DecisionDeLinea(fila["decision"]) if fila["decision"] else None
    return linea


def _decision_desde_fila(fila: Fila, cotizacion: Cotizacion) -> DecisionDelCliente | None:
    if fila["decision_registrada_en"] is None:
        return None
    return DecisionDelCliente(
        cotizacion.id,
        _trabajos_decididos(cotizacion, DecisionDeLinea.AUTORIZADA),
        _trabajos_decididos(cotizacion, DecisionDeLinea.NO_AUTORIZADO),
        Autorizante(fila["decision_autorizante"], RolDeAutorizante(fila["decision_rol"])),
        fila["decision_registrada_en"],
        cotizacion.tipo,
    )


def _trabajos_decididos(
    cotizacion: Cotizacion, decision: DecisionDeLinea
) -> tuple[TrabajoDecidido, ...]:
    return tuple(
        TrabajoDecidido(linea.numero, linea.descripcion, linea.subtotal)
        for linea in cotizacion.lineas
        if linea.decision is decision
    )


# ------------------------------------------------------------------ Alerta interna
def fila_de_alerta(alerta: AlertaInterna) -> dict[str, Any]:
    rol = alerta.destinatario_rol
    return {
        "destinatario": alerta.destinatario,
        "destinatario_rol": rol.value if rol else None,
        "tipo": alerta.tipo,
        "mensaje": alerta.mensaje,
        "numero_orden": alerta.numero_orden,
        "id_cotizacion": alerta.id_cotizacion,
        "clave": alerta.clave,
        "creada_en": alerta.creada_en,
        "leida": alerta.leida,
    }


def alerta_desde_fila(fila: Fila) -> AlertaInterna:
    rol = fila["destinatario_rol"]
    return AlertaInterna(
        fila["tipo"],
        fila["mensaje"],
        fila["creada_en"],
        fila["destinatario"],
        RolDeEmpleado(rol) if rol else None,
        fila["numero_orden"],
        fila["id_cotizacion"],
        fila["clave"],
        fila["leida"],
    )
