"""Lector en memoria: arma las vistas de lectura a partir de los datos confirmados."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from application.consultas.lector import LectorDeOrdenes
from application.consultas.vistas import (
    ClienteVista,
    CotizacionPendienteVista,
    CotizacionVista,
    DatosRelacionados,
    EstadoDeOrdenVista,
    ExpedienteDeOrdenVista,
    OrdenAbiertaVista,
    OrdenDelPanelVista,
    OrdenResumenVista,
    SolicitudVista,
    TecnicoVista,
    VehiculoConClienteVista,
    vista_de_cliente,
    vista_de_cotizacion,
    vista_de_expediente,
    vista_de_solicitud,
    vista_de_vehiculo,
    vista_del_panel,
)
from application.puertos import AlertaInterna
from domain.clientes.cliente import TipoCliente
from domain.compartido.valores import NumeroOrden, Placas
from domain.cotizaciones.estados import EstadoCotizacion
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes.estados import MAQUINA_DE_ORDEN, EstadoOrden, esta_abierta
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from infrastructure.memoria.almacen import AlmacenEnMemoria


class LectorEnMemoria(LectorDeOrdenes):
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self._almacen = almacen

    def vehiculo_por_placas(self, placas: Placas) -> VehiculoConClienteVista | None:
        datos = self._almacen.datos
        vehiculo = datos.vehiculos.get(str(placas))
        if vehiculo is None:
            return None
        abiertas = [
            OrdenAbiertaVista(numero, orden.estado.value)
            for numero, orden in datos.ordenes.items()
            if orden.placas == placas and esta_abierta(orden.estado)
        ]
        abierta = min(abiertas, key=lambda vista: vista.numero_orden, default=None)
        return vista_de_vehiculo(vehiculo, datos.clientes[vehiculo.id_cliente], abierta)

    def clientes(self, tipo: TipoCliente | None, empresa: str | None) -> list[ClienteVista]:
        buscada = (empresa or "").strip().casefold()
        return [
            vista_de_cliente(cliente)
            for cliente in self._almacen.datos.clientes.values()
            if (tipo is None or cliente.tipo is tipo)
            and buscada in (cliente.empresa or "").casefold()
        ]

    def tecnicos(self) -> list[TecnicoVista]:
        empleados = sorted(self._almacen.datos.empleados.values(), key=lambda e: e.id_empleado)
        return [
            TecnicoVista(empleado.id_empleado, empleado.nombre)
            for empleado in empleados
            if empleado.rol is RolDeEmpleado.TECNICO
        ]

    def panel_del_tecnico(self, id_tecnico: str) -> list[OrdenDelPanelVista]:
        vistas = (
            vista_del_panel(orden, id_tecnico) for orden in self._almacen.datos.ordenes.values()
        )
        panel = [vista for vista in vistas if vista is not None]
        return sorted(panel, key=lambda vista: vista.fecha_ingreso_a_fila)

    def solicitudes_pendientes(self) -> list[SolicitudVista]:
        return [
            vista_de_solicitud(orden, solicitud)
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
        return vista_de_cotizacion(cotizacion) if cotizacion else None

    def expediente(self, numero: NumeroOrden) -> ExpedienteDeOrdenVista | None:
        orden = self._almacen.datos.ordenes.get(str(numero))
        if orden is None:
            return None
        cotizaciones = sorted(
            (c for c in self._almacen.datos.cotizaciones.values() if c.numero_orden == numero),
            key=lambda cotizacion: cotizacion.version.numero,
        )
        return vista_de_expediente(orden, cotizaciones, self._relacionados(orden))

    def _relacionados(self, orden: OrdenDeServicio) -> DatosRelacionados:
        datos = self._almacen.datos
        cliente = datos.clientes.get(orden.id_cliente)
        vehiculo = datos.vehiculos.get(str(orden.placas))
        return DatosRelacionados(
            cliente.nombre if cliente else None,
            cliente.tipo.value if cliente else None,
            cliente.empresa if cliente else None,
            cliente.responsable.nombre if cliente and cliente.responsable else None,
            vehiculo.marca if vehiculo else None,
            vehiculo.modelo if vehiculo else None,
            vehiculo.anio if vehiculo else None,
            {empleado.id_empleado: empleado.nombre for empleado in datos.empleados.values()},
        )

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
