"""Vistas de lectura (DTO): modelos planos que no exponen los Aggregates (ADR-003).

Los importes viajan como texto con dos decimales («1500.00»). Las funciones `vista_de_…` arman
cada vista desde su Aggregate, para que todos los lectores calculen lo mismo.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import date, datetime

from domain.clientes.cliente import Cliente
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.valores import CorreccionDeCotizacion
from domain.ordenes.estados import EstadoOrden, EstadoTrabajo
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.solicitud_de_compra import SolicitudDeCompra
from domain.ordenes.trabajo import Trabajo
from domain.vehiculos.vehiculo import Vehiculo

_TRABAJOS_ABIERTOS = (EstadoTrabajo.PENDIENTE, EstadoTrabajo.EN_PROGRESO)


@dataclass(frozen=True)
class ClienteVista:
    id_cliente: str
    nombre: str
    tipo: str
    telefono: str | None
    correo: str | None
    empresa: str | None
    responsable_nombre: str | None
    responsable_telefono: str | None
    responsable_correo: str | None


@dataclass(frozen=True)
class VehiculoConClienteVista:
    placas: str
    vin: str
    marca: str
    modelo: str
    anio: int
    cliente: ClienteVista


@dataclass(frozen=True)
class TrabajoVista:
    id: int
    descripcion: str
    importe: str
    estado: str
    tecnico: str | None
    tecnico_nombre: str | None = None


@dataclass(frozen=True)
class OrdenDelPanelVista:
    numero_orden: str
    estado: str
    placas: str
    motivo_de_ingreso: str
    fecha_ingreso_a_fila: datetime
    diagnostico_asignado: bool
    trabajos: tuple[TrabajoVista, ...]


@dataclass(frozen=True)
class SolicitudVista:
    numero_orden: str
    id: int
    id_trabajo: int
    refaccion: str
    cantidad: int
    estado: str
    fecha_solicitud: datetime
    fecha_llegada: datetime | None
    fecha_aviso_al_cliente: datetime | None


@dataclass(frozen=True)
class SolicitudPendienteVista:
    numero_orden: str
    id_solicitud: int
    refaccion: str
    cantidad: int
    fecha_solicitud: datetime
    dias_habiles_transcurridos: int


@dataclass(frozen=True)
class CotizacionPendienteVista:
    id_cotizacion: str
    numero_orden: str
    version: str
    total: str


@dataclass(frozen=True)
class RefaccionVista:
    descripcion: str
    cantidad: int
    precio_unitario: str
    importe: str


@dataclass(frozen=True)
class LineaVista:
    numero: int
    descripcion: str
    mano_de_obra: str
    refacciones: tuple[RefaccionVista, ...]
    subtotal: str
    decision: str | None


@dataclass(frozen=True)
class TecnicoVista:
    """Técnico del taller para elegirlo por su nombre al asignar (CA-053)."""

    id_empleado: str
    nombre: str


@dataclass(frozen=True)
class CorreccionVista:
    """Una corrección del historial de la cotización (H-PIA-21)."""

    asesor: str
    registrada_en: datetime
    motivo: str
    total_anterior: str
    total_nuevo: str
    estado_anterior: str
    estado_nuevo: str
    fecha_presentacion_anterior: datetime | None
    fecha_aprobacion_gerencial_anterior: datetime | None


@dataclass(frozen=True)
class CotizacionVista:
    id: str
    numero_orden: str
    tipo: str
    version: str
    estado: str
    total: str
    generada_en: datetime
    fecha_aprobacion_gerencial: datetime | None
    observaciones_del_gerente: str | None
    fecha_presentacion: datetime | None
    autorizante: str | None
    fecha_decision: datetime | None
    lineas: tuple[LineaVista, ...]
    correcciones: tuple[CorreccionVista, ...] = ()


@dataclass(frozen=True)
class FallaAdicionalVista:
    id: int
    descripcion: str
    tecnico: str
    reportada_en: datetime


@dataclass(frozen=True)
class ExpedienteDeOrdenVista:
    numero_orden: str
    estado: str
    id_cliente: str
    placas: str
    asesor: str
    motivo_de_ingreso: str
    fecha_ingreso: datetime
    ultima_actualizacion: datetime
    kilometraje: int | None
    nivel_de_combustible: str | None
    tecnico_de_diagnostico: str | None
    diagnostico_fallas: str | None
    diagnostico_recomendaciones: str | None
    rechazo_total: bool
    total_autorizado: str
    pago_monto: str | None
    pago_forma: str | None
    pago_registrado_en: datetime | None
    credito_monto: str | None
    credito_fecha_vencimiento: date | None
    nota_fecha_salida: datetime | None
    nota_firmada: bool
    fecha_entrega: datetime | None
    cancelacion_motivo: str | None
    cotizaciones: tuple[CotizacionVista, ...]
    trabajos: tuple[TrabajoVista, ...]
    solicitudes: tuple[SolicitudVista, ...]
    fallas_adicionales: tuple[FallaAdicionalVista, ...]
    # Lo que la página necesita de otros Aggregates (interfaz-web.md §7, Fase 14)
    cliente_nombre: str | None = None
    cliente_tipo: str | None = None
    empresa: str | None = None
    responsable_nombre: str | None = None
    vehiculo_marca: str | None = None
    vehiculo_modelo: str | None = None
    vehiculo_anio: int | None = None
    tecnico_de_diagnostico_nombre: str | None = None


@dataclass(frozen=True)
class DatosRelacionados:
    """Datos del cliente, del vehículo y de los empleados que muestra el expediente.

    Los lectores los arman desde la base o la memoria; nunca se validan con las reglas de
    captura, porque solo se leen (condición del equipo, Fase 14).
    """

    cliente_nombre: str | None = None
    cliente_tipo: str | None = None
    empresa: str | None = None
    responsable_nombre: str | None = None
    vehiculo_marca: str | None = None
    vehiculo_modelo: str | None = None
    vehiculo_anio: int | None = None
    nombres_de_empleados: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class OrdenResumenVista:
    numero_orden: str
    estado: str
    abierta: bool
    id_cliente: str
    placas: str
    fecha_ingreso: datetime
    ultima_actualizacion: datetime


@dataclass(frozen=True)
class IngresosDelDiaVista:
    fecha: date
    total: str


@dataclass(frozen=True)
class EstadoDeOrdenVista:
    """Lo único que ve el cliente en la consulta pública (CA-037)."""

    numero_orden: str
    estado: str
    fecha_ingreso: datetime
    ultima_actualizacion: datetime


def vista_de_cliente(cliente: Cliente) -> ClienteVista:
    responsable = cliente.responsable
    return ClienteVista(
        cliente.id_cliente,
        cliente.nombre,
        cliente.tipo.value,
        cliente.telefono,
        cliente.correo,
        cliente.empresa,
        responsable.nombre if responsable else None,
        responsable.telefono if responsable else None,
        responsable.correo if responsable else None,
    )


def vista_de_trabajo(trabajo: Trabajo) -> TrabajoVista:
    return TrabajoVista(
        trabajo.id,
        trabajo.descripcion,
        str(trabajo.importe.monto),
        trabajo.estado.value,
        trabajo.tecnico,
    )


def vista_de_solicitud(orden: OrdenDeServicio, solicitud: SolicitudDeCompra) -> SolicitudVista:
    return SolicitudVista(
        str(orden.numero),
        solicitud.id,
        solicitud.id_trabajo,
        solicitud.refaccion,
        solicitud.cantidad,
        solicitud.estado.value,
        solicitud.fecha_solicitud,
        solicitud.fecha_llegada,
        solicitud.fecha_aviso_al_cliente,
    )


def vista_de_cotizacion(cotizacion: Cotizacion) -> CotizacionVista:
    decision = cotizacion.decision
    return CotizacionVista(
        cotizacion.id,
        str(cotizacion.numero_orden),
        cotizacion.tipo.value,
        str(cotizacion.version),
        cotizacion.estado.value,
        str(cotizacion.total.monto),
        cotizacion.generada_en,
        cotizacion.fecha_aprobacion_gerencial,
        cotizacion.observaciones_del_gerente,
        cotizacion.fecha_presentacion,
        decision.autorizante.nombre if decision else None,
        decision.registrada_en if decision else None,
        tuple(
            LineaVista(
                linea.numero,
                linea.descripcion,
                str(linea.mano_de_obra.monto),
                tuple(
                    RefaccionVista(
                        refaccion.descripcion,
                        refaccion.cantidad,
                        str(refaccion.precio_unitario.monto),
                        str(refaccion.importe.monto),
                    )
                    for refaccion in linea.refacciones
                ),
                str(linea.subtotal.monto),
                linea.decision.value if linea.decision else None,
            )
            for linea in cotizacion.lineas
        ),
        tuple(_vista_de_correccion(correccion) for correccion in cotizacion.correcciones),
    )


def _vista_de_correccion(correccion: CorreccionDeCotizacion) -> CorreccionVista:
    return CorreccionVista(
        correccion.asesor,
        correccion.registrada_en,
        correccion.motivo,
        str(correccion.total_anterior.monto),
        str(correccion.total_nuevo.monto),
        correccion.estado_anterior.value,
        correccion.estado_nuevo.value,
        correccion.fecha_presentacion_anterior,
        correccion.fecha_aprobacion_gerencial_anterior,
    )


def vista_de_expediente(
    orden: OrdenDeServicio,
    cotizaciones: list[Cotizacion],
    relacionados: DatosRelacionados | None = None,
) -> ExpedienteDeOrdenVista:
    datos = relacionados or DatosRelacionados()
    nombres = datos.nombres_de_empleados
    recepcion = orden.estado_de_recepcion
    diagnostico = orden.diagnostico
    pago = orden.pago
    credito = orden.cargo_a_credito
    nota = orden.nota_de_responsabilidad
    return ExpedienteDeOrdenVista(
        str(orden.numero),
        orden.estado.value,
        orden.id_cliente,
        str(orden.placas),
        orden.asesor,
        orden.motivo_de_ingreso,
        orden.fecha_ingreso,
        orden.ultima_actualizacion,
        recepcion.kilometraje if recepcion else None,
        recepcion.nivel_de_combustible.value if recepcion else None,
        orden.tecnico_de_diagnostico,
        diagnostico.fallas if diagnostico else None,
        diagnostico.recomendaciones if diagnostico else None,
        orden.rechazo_total,
        str(orden.total_autorizado.monto),
        str(pago.monto.monto) if pago else None,
        pago.forma.value if pago else None,
        pago.registrado_en if pago else None,
        str(credito.monto.monto) if credito else None,
        credito.fecha_vencimiento if credito else None,
        nota.fecha_salida if nota else None,
        nota.firmada if nota else False,
        orden.fecha_entrega,
        orden.cancelacion.motivo if orden.cancelacion else None,
        tuple(vista_de_cotizacion(cotizacion) for cotizacion in cotizaciones),
        tuple(
            replace(vista_de_trabajo(trabajo), tecnico_nombre=nombres.get(trabajo.tecnico or ""))
            for trabajo in orden.trabajos
        ),
        tuple(vista_de_solicitud(orden, solicitud) for solicitud in orden.solicitudes),
        tuple(
            FallaAdicionalVista(falla.id, falla.descripcion, falla.tecnico, falla.reportada_en)
            for falla in orden.fallas_adicionales
        ),
        datos.cliente_nombre,
        datos.cliente_tipo,
        datos.empresa,
        datos.responsable_nombre,
        datos.vehiculo_marca,
        datos.vehiculo_modelo,
        datos.vehiculo_anio,
        nombres.get(orden.tecnico_de_diagnostico or ""),
    )


def vista_de_vehiculo(vehiculo: Vehiculo, cliente: Cliente) -> VehiculoConClienteVista:
    return VehiculoConClienteVista(
        str(vehiculo.placas),
        str(vehiculo.vin),
        vehiculo.marca,
        vehiculo.modelo,
        vehiculo.anio,
        vista_de_cliente(cliente),
    )


def vista_del_panel(orden: OrdenDeServicio, id_tecnico: str) -> OrdenDelPanelVista | None:
    """Lo que el técnico ve de la orden, o `None` si no tiene nada asignado o no está en la fila."""
    trabajos = tuple(
        vista_de_trabajo(trabajo)
        for trabajo in orden.trabajos
        if trabajo.tecnico == id_tecnico and trabajo.estado in _TRABAJOS_ABIERTOS
    )
    diagnostico_asignado = (
        orden.estado is EstadoOrden.EN_DIAGNOSTICO and orden.tecnico_de_diagnostico == id_tecnico
    )
    if orden.fecha_ingreso_a_fila is None or not (trabajos or diagnostico_asignado):
        return None
    return OrdenDelPanelVista(
        str(orden.numero),
        orden.estado.value,
        str(orden.placas),
        orden.motivo_de_ingreso,
        orden.fecha_ingreso_a_fila,
        diagnostico_asignado,
        trabajos,
    )
