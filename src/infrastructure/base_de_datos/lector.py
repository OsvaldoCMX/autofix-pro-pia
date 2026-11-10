"""Lado de lectura (CQRS) con SQLAlchemy: responde lo mismo que el lector en memoria (ADR-003).

Cada consulta usa su propia conexión, sin bloquear filas. Lo que tiene datos derivados se arma
desde el Aggregate; las listas simples se leen directo de las columnas.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Connection, Engine, and_, func, or_, select

from application.consultas.lector import LectorDeOrdenes
from application.consultas.vistas import (
    ClienteVista,
    CotizacionPendienteVista,
    CotizacionVista,
    DatosRelacionados,
    EstadoDeOrdenVista,
    ExpedienteDeOrdenVista,
    OrdenDelPanelVista,
    OrdenResumenVista,
    SolicitudVista,
    TecnicoVista,
    VehiculoConClienteVista,
    vista_de_cliente,
    vista_de_cotizacion,
    vista_de_expediente,
    vista_de_vehiculo,
    vista_del_panel,
)
from application.puertos import AlertaInterna
from domain.clientes.cliente import TipoCliente
from domain.compartido.valores import Dinero, NumeroOrden, Placas
from domain.cotizaciones.estados import EstadoCotizacion
from domain.cotizaciones.valores import VersionCotizacion
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes.estados import (
    MAQUINA_DE_ORDEN,
    EstadoOrden,
    EstadoSolicitud,
    EstadoTrabajo,
)
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from infrastructure.base_de_datos import mapeo
from infrastructure.base_de_datos.repositorios import cargar_cotizacion, cargar_orden
from infrastructure.base_de_datos.tablas import (
    alertas_internas,
    clientes,
    cotizaciones,
    empleados,
    ordenes,
    solicitudes_de_compra,
    trabajos,
    vehiculos,
)

_TRABAJOS_ABIERTOS = (EstadoTrabajo.PENDIENTE.value, EstadoTrabajo.EN_PROGRESO.value)


class LectorDeOrdenesSqlAlchemy(LectorDeOrdenes):
    def __init__(self, motor: Engine) -> None:
        self._motor = motor

    def vehiculo_por_placas(self, placas: Placas) -> VehiculoConClienteVista | None:
        with self._motor.connect() as conexion:
            fila = (
                conexion.execute(select(vehiculos).where(vehiculos.c.placas == str(placas)))
                .mappings()
                .first()
            )
            if fila is None:
                return None
            cliente = (
                conexion.execute(select(clientes).where(clientes.c.id == fila["id_cliente"]))
                .mappings()
                .one()
            )
        return vista_de_vehiculo(mapeo.vehiculo_desde_fila(fila), mapeo.cliente_desde_fila(cliente))

    def clientes(self, tipo: TipoCliente | None, empresa: str | None) -> list[ClienteVista]:
        """El texto se compara en Python: `lower()` de SQLite no entiende acentos."""
        consulta = select(clientes).order_by(clientes.c.id)
        if tipo is not None:
            consulta = consulta.where(clientes.c.tipo == tipo.value)
        with self._motor.connect() as conexion:
            filas = conexion.execute(consulta).mappings().all()
        buscada = (empresa or "").strip().casefold()
        return [
            vista_de_cliente(mapeo.cliente_desde_fila(fila))
            for fila in filas
            if buscada in (fila["empresa"] or "").casefold()
        ]

    def tecnicos(self) -> list[TecnicoVista]:
        consulta = (
            select(empleados.c.id, empleados.c.nombre)
            .where(empleados.c.rol == RolDeEmpleado.TECNICO.value)
            .order_by(empleados.c.id)
        )
        with self._motor.connect() as conexion:
            return [TecnicoVista(fila.id, fila.nombre) for fila in conexion.execute(consulta)]

    def panel_del_tecnico(self, id_tecnico: str) -> list[OrdenDelPanelVista]:
        con_trabajos = select(trabajos.c.numero_orden).where(
            trabajos.c.tecnico == id_tecnico, trabajos.c.estado.in_(_TRABAJOS_ABIERTOS)
        )
        consulta = (
            select(ordenes.c.numero)
            .where(
                ordenes.c.fecha_ingreso_a_fila.is_not(None),
                or_(
                    ordenes.c.numero.in_(con_trabajos),
                    and_(
                        ordenes.c.estado == EstadoOrden.EN_DIAGNOSTICO.value,
                        ordenes.c.tecnico_de_diagnostico == id_tecnico,
                    ),
                ),
            )
            .order_by(ordenes.c.fecha_ingreso_a_fila, ordenes.c.numero)
        )
        with self._motor.connect() as conexion:
            numeros = conexion.execute(consulta).scalars().all()
            cargadas = [cargar_orden(conexion, numero) for numero in numeros]
        vistas = (vista_del_panel(orden, id_tecnico) for orden in cargadas)
        return [vista for vista in vistas if vista is not None]

    def solicitudes_pendientes(self) -> list[SolicitudVista]:
        consulta = (
            select(solicitudes_de_compra)
            .where(solicitudes_de_compra.c.estado == EstadoSolicitud.SOLICITADA.value)
            .order_by(solicitudes_de_compra.c.numero_orden, solicitudes_de_compra.c.id)
        )
        with self._motor.connect() as conexion:
            filas = conexion.execute(consulta).mappings().all()
        return [
            SolicitudVista(
                fila["numero_orden"],
                fila["id"],
                fila["id_trabajo"],
                fila["refaccion"],
                fila["cantidad"],
                fila["estado"],
                fila["fecha_solicitud"],
                fila["fecha_llegada"],
                fila["fecha_aviso_al_cliente"],
            )
            for fila in filas
        ]

    def cotizaciones_pendientes_de_aprobacion(self) -> list[CotizacionPendienteVista]:
        consulta = (
            select(cotizaciones)
            .where(
                cotizaciones.c.estado == EstadoCotizacion.PENDIENTE_DE_APROBACION_GERENCIAL.value
            )
            .order_by(cotizaciones.c.id)
        )
        with self._motor.connect() as conexion:
            filas = conexion.execute(consulta).mappings().all()
        return [
            CotizacionPendienteVista(
                fila["id"],
                fila["numero_orden"],
                str(VersionCotizacion(fila["version"])),
                str(Dinero(fila["total"]).monto),
            )
            for fila in filas
        ]

    def cotizacion(self, id_cotizacion: str) -> CotizacionVista | None:
        with self._motor.connect() as conexion:
            cotizacion = cargar_cotizacion(conexion, id_cotizacion)
        return vista_de_cotizacion(cotizacion) if cotizacion else None

    def expediente(self, numero: NumeroOrden) -> ExpedienteDeOrdenVista | None:
        with self._motor.connect() as conexion:
            orden = cargar_orden(conexion, str(numero))
            if orden is None:
                return None
            ids = conexion.execute(
                select(cotizaciones.c.id)
                .where(cotizaciones.c.numero_orden == str(numero))
                .order_by(cotizaciones.c.version)
            ).scalars()
            cargadas = [cargar_cotizacion(conexion, id_cotizacion) for id_cotizacion in ids.all()]
            relacionados = _relacionados(conexion, orden)
        return vista_de_expediente(orden, cargadas, relacionados)

    def ordenes(self, estado: EstadoOrden | None) -> list[OrdenResumenVista]:
        consulta = select(ordenes).order_by(ordenes.c.numero)
        if estado is not None:
            consulta = consulta.where(ordenes.c.estado == estado.value)
        with self._motor.connect() as conexion:
            filas = conexion.execute(consulta).mappings().all()
        return [
            OrdenResumenVista(
                fila["numero"],
                fila["estado"],
                not MAQUINA_DE_ORDEN.es_final(EstadoOrden(fila["estado"])),
                fila["id_cliente"],
                fila["placas"],
                fila["fecha_ingreso"],
                fila["ultima_actualizacion"],
            )
            for fila in filas
        ]

    def total_de_pagos_entre(self, desde: datetime, hasta: datetime) -> Decimal:
        consulta = select(func.sum(ordenes.c.pago_monto)).where(
            ordenes.c.pago_registrado_en >= desde, ordenes.c.pago_registrado_en < hasta
        )
        with self._motor.connect() as conexion:
            total = conexion.execute(consulta).scalar_one()
        return Dinero(total).monto if total is not None else Decimal(0)

    def estado_de_orden(self, numero: NumeroOrden, placas: Placas) -> EstadoDeOrdenVista | None:
        consulta = select(ordenes).where(
            ordenes.c.numero == str(numero), ordenes.c.placas == str(placas)
        )
        with self._motor.connect() as conexion:
            fila = conexion.execute(consulta).mappings().first()
        if fila is None:
            return None
        return EstadoDeOrdenVista(
            fila["numero"], fila["estado"], fila["fecha_ingreso"], fila["ultima_actualizacion"]
        )

    def alertas_de(self, id_empleado: str, rol: RolDeEmpleado) -> list[AlertaInterna]:
        consulta = (
            select(alertas_internas)
            .where(
                or_(
                    alertas_internas.c.destinatario == id_empleado,
                    alertas_internas.c.destinatario_rol == rol.value,
                )
            )
            .order_by(alertas_internas.c.creada_en, alertas_internas.c.id)
        )
        with self._motor.connect() as conexion:
            filas = conexion.execute(consulta).mappings().all()
        return [mapeo.alerta_desde_fila(fila) for fila in filas]

    def ordenes_con_solicitudes_pendientes(self) -> list[NumeroOrden]:
        consulta = (
            select(solicitudes_de_compra.c.numero_orden)
            .where(solicitudes_de_compra.c.estado == EstadoSolicitud.SOLICITADA.value)
            .distinct()
            .order_by(solicitudes_de_compra.c.numero_orden)
        )
        with self._motor.connect() as conexion:
            return [NumeroOrden(numero) for numero in conexion.execute(consulta).scalars()]

    def cotizaciones_presentadas_sin_decision(self) -> list[str]:
        consulta = (
            select(cotizaciones.c.id)
            .where(
                cotizaciones.c.estado
                == EstadoCotizacion.PENDIENTE_DE_AUTORIZACION_DEL_CLIENTE.value,
                cotizaciones.c.fecha_presentacion.is_not(None),
            )
            .order_by(cotizaciones.c.id)
        )
        with self._motor.connect() as conexion:
            return list(conexion.execute(consulta).scalars())


def _relacionados(conexion: Connection, orden: OrdenDeServicio) -> DatosRelacionados:
    """Lee las columnas tal como están guardadas, sin pasar por las reglas de captura."""
    cliente = conexion.execute(
        select(
            clientes.c.nombre,
            clientes.c.tipo,
            clientes.c.empresa,
            clientes.c.responsable_nombre,
        ).where(clientes.c.id == orden.id_cliente)
    ).first()
    vehiculo = conexion.execute(
        select(vehiculos.c.marca, vehiculos.c.modelo, vehiculos.c.anio).where(
            vehiculos.c.placas == str(orden.placas)
        )
    ).first()
    filas = conexion.execute(select(empleados.c.id, empleados.c.nombre)).all()
    nombres = {fila.id: fila.nombre for fila in filas}
    return DatosRelacionados(
        cliente.nombre if cliente else None,
        cliente.tipo if cliente else None,
        cliente.empresa if cliente else None,
        cliente.responsable_nombre if cliente else None,
        vehiculo.marca if vehiculo else None,
        vehiculo.modelo if vehiculo else None,
        vehiculo.anio if vehiculo else None,
        nombres,
    )
