"""Lector en memoria: arma las vistas de lectura a partir de los datos confirmados."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from application.consultas.lector import LectorDeOrdenes
from application.consultas.vistas import (
    ClienteVista,
    CotizacionPendienteVista,
    CotizacionVista,
    EstadoDeOrdenVista,
    ExpedienteDeOrdenVista,
    FallaAdicionalVista,
    LineaVista,
    OrdenDelPanelVista,
    OrdenResumenVista,
    RefaccionVista,
    SolicitudVista,
    TrabajoVista,
    VehiculoConClienteVista,
)
from application.puertos import AlertaInterna
from domain.clientes.cliente import Cliente, TipoCliente
from domain.compartido.valores import NumeroOrden, Placas
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.estados import EstadoCotizacion
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes.estados import MAQUINA_DE_ORDEN, EstadoOrden, EstadoTrabajo
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.solicitud_de_compra import SolicitudDeCompra
from domain.ordenes.trabajo import Trabajo
from infrastructure.memoria.almacen import AlmacenEnMemoria

_TRABAJOS_ABIERTOS = (EstadoTrabajo.PENDIENTE, EstadoTrabajo.EN_PROGRESO)


class LectorEnMemoria(LectorDeOrdenes):
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self._almacen = almacen

    def vehiculo_por_placas(self, placas: Placas) -> VehiculoConClienteVista | None:
        datos = self._almacen.datos
        vehiculo = datos.vehiculos.get(str(placas))
        if vehiculo is None:
            return None
        return VehiculoConClienteVista(
            str(vehiculo.placas),
            str(vehiculo.vin),
            vehiculo.marca,
            vehiculo.modelo,
            vehiculo.anio,
            _cliente(datos.clientes[vehiculo.id_cliente]),
        )

    def clientes(self, tipo: TipoCliente | None, empresa: str | None) -> list[ClienteVista]:
        buscada = (empresa or "").strip().casefold()
        return [
            _cliente(cliente)
            for cliente in self._almacen.datos.clientes.values()
            if (tipo is None or cliente.tipo is tipo)
            and buscada in (cliente.empresa or "").casefold()
        ]

    def panel_del_tecnico(self, id_tecnico: str) -> list[OrdenDelPanelVista]:
        panel = []
        for orden in self._almacen.datos.ordenes.values():
            trabajos = tuple(
                _trabajo(trabajo)
                for trabajo in orden.trabajos
                if trabajo.tecnico == id_tecnico and trabajo.estado in _TRABAJOS_ABIERTOS
            )
            diagnostico_asignado = (
                orden.estado is EstadoOrden.EN_DIAGNOSTICO
                and orden.tecnico_de_diagnostico == id_tecnico
            )
            if orden.fecha_ingreso_a_fila is not None and (trabajos or diagnostico_asignado):
                panel.append(
                    OrdenDelPanelVista(
                        str(orden.numero),
                        orden.estado.value,
                        str(orden.placas),
                        orden.motivo_de_ingreso,
                        orden.fecha_ingreso_a_fila,
                        diagnostico_asignado,
                        trabajos,
                    )
                )
        return sorted(panel, key=lambda vista: vista.fecha_ingreso_a_fila)

    def solicitudes_pendientes(self) -> list[SolicitudVista]:
        return [
            _solicitud(orden, solicitud)
            for orden in self._almacen.datos.ordenes.values()
            for solicitud in orden.solicitudes
            if solicitud.esta_pendiente
        ]

    def cotizaciones_pendientes_de_aprobacion(self) -> list[CotizacionPendienteVista]:
        return [
            CotizacionPendienteVista(
                cotizacion.id,
                str(cotizacion.numero_orden),
                str(cotizacion.version),
                str(cotizacion.total.monto),
            )
            for cotizacion in self._almacen.datos.cotizaciones.values()
            if cotizacion.estado is EstadoCotizacion.PENDIENTE_DE_APROBACION_GERENCIAL
        ]

    def cotizacion(self, id_cotizacion: str) -> CotizacionVista | None:
        cotizacion = self._almacen.datos.cotizaciones.get(id_cotizacion)
        return _cotizacion(cotizacion) if cotizacion else None

    def expediente(self, numero: NumeroOrden) -> ExpedienteDeOrdenVista | None:
        orden = self._almacen.datos.ordenes.get(str(numero))
        if orden is None:
            return None
        cotizaciones = sorted(
            (c for c in self._almacen.datos.cotizaciones.values() if c.numero_orden == numero),
            key=lambda cotizacion: cotizacion.version.numero,
        )
        return _expediente(orden, cotizaciones)

    def ordenes(self, estado: EstadoOrden | None) -> list[OrdenResumenVista]:
        return [
            OrdenResumenVista(
                str(orden.numero),
                orden.estado.value,
                not MAQUINA_DE_ORDEN.es_final(orden.estado),
                orden.id_cliente,
                str(orden.placas),
                orden.fecha_ingreso,
                orden.ultima_actualizacion,
            )
            for orden in self._almacen.datos.ordenes.values()
            if estado is None or orden.estado is estado
        ]

    def total_de_pagos_entre(self, desde: datetime, hasta: datetime) -> Decimal:
        return sum(
            (
                orden.pago.monto.monto
                for orden in self._almacen.datos.ordenes.values()
                if orden.pago is not None and desde <= orden.pago.registrado_en < hasta
            ),
            Decimal(0),
        )

    def estado_de_orden(self, numero: NumeroOrden, placas: Placas) -> EstadoDeOrdenVista | None:
        orden = self._almacen.datos.ordenes.get(str(numero))
        if orden is None or orden.placas != placas:
            return None
        return EstadoDeOrdenVista(
            str(orden.numero), orden.estado.value, orden.fecha_ingreso, orden.ultima_actualizacion
        )

    def alertas_de(self, id_empleado: str, rol: RolDeEmpleado) -> list[AlertaInterna]:
        return [
            alerta
            for alerta in self._almacen.datos.alertas
            if alerta.destinatario == id_empleado or alerta.destinatario_rol is rol
        ]

    def ordenes_con_solicitudes_pendientes(self) -> list[NumeroOrden]:
        return [
            orden.numero
            for orden in self._almacen.datos.ordenes.values()
            if any(solicitud.esta_pendiente for solicitud in orden.solicitudes)
        ]

    def cotizaciones_presentadas_sin_decision(self) -> list[str]:
        return [
            cotizacion.id
            for cotizacion in self._almacen.datos.cotizaciones.values()
            if cotizacion.estado is EstadoCotizacion.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE
            and cotizacion.fecha_presentacion is not None
        ]


def _cliente(cliente: Cliente) -> ClienteVista:
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


def _trabajo(trabajo: Trabajo) -> TrabajoVista:
    return TrabajoVista(
        trabajo.id,
        trabajo.descripcion,
        str(trabajo.importe.monto),
        trabajo.estado.value,
        trabajo.tecnico,
    )


def _solicitud(orden: OrdenDeServicio, solicitud: SolicitudDeCompra) -> SolicitudVista:
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


def _cotizacion(cotizacion: Cotizacion) -> CotizacionVista:
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
    )


def _expediente(
    orden: OrdenDeServicio, cotizaciones: list[Cotizacion]
) -> ExpedienteDeOrdenVista:
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
        tuple(_cotizacion(cotizacion) for cotizacion in cotizaciones),
        tuple(_trabajo(trabajo) for trabajo in orden.trabajos),
        tuple(_solicitud(orden, solicitud) for solicitud in orden.solicitudes),
        tuple(
            FallaAdicionalVista(falla.id, falla.descripcion, falla.tecnico, falla.reportada_en)
            for falla in orden.fallas_adicionales
        ),
    )
