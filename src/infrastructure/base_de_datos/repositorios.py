"""Repositories con SQLAlchemy: el mismo contrato que las versiones en memoria (ADR-004).

`agregar` y `guardar` escriben en la transacción de la Unidad de Trabajo; `obtener` solo lee, así
que un manejador de alertas que consulta una orden no la sobreescribe con datos viejos. Dentro de
una Unidad de Trabajo, pedir dos veces lo mismo devuelve el mismo objeto.

`obtener` bloquea la orden o la cotización hasta el final de la transacción (`FOR UPDATE`): si dos
peticiones la cambian a la vez, la segunda espera y decide con el estado ya actualizado.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Connection, Table, delete, func, insert, select, update

from application.puertos import AlertaInterna, CatalogoDeServicios, RepositorioDeAlertas
from domain.clientes.cliente import Cliente, TipoCliente
from domain.clientes.repositorio import RepositorioDeClientes
from domain.compartido.errores import (
    ClienteNoEncontrado,
    CotizacionNoEncontrada,
    EmpleadoNoEncontrado,
    OrdenNoEncontrada,
    ValorInvalido,
    VehiculoNoEncontrado,
)
from domain.compartido.eventos import RaizDeAgregado
from domain.compartido.valores import NumeroOrden, Placas
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.repositorio import RepositorioDeCotizaciones
from domain.cotizaciones.valores import VersionCotizacion
from domain.empleados.empleado import Empleado
from domain.empleados.repositorio import RepositorioDeEmpleados
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.repositorio import RepositorioDeOrdenes
from domain.vehiculos.repositorio import RepositorioDeVehiculos
from domain.vehiculos.vehiculo import Vehiculo
from infrastructure.base_de_datos import mapeo
from infrastructure.base_de_datos.tablas import (
    alertas_internas,
    catalogo_servicios,
    clientes,
    correcciones_de_cotizacion,
    cotizaciones,
    empleados,
    fallas_adicionales,
    lineas_de_cotizacion,
    ordenes,
    recontactos,
    refacciones_cotizadas,
    secuencias,
    servicios_solicitados,
    solicitudes_de_compra,
    trabajos,
    vehiculos,
)


def siguiente_folio(conexion: Connection, nombre: str) -> int:
    """Avanza una secuencia. Se revierte con la transacción: un folio fallido no se pierde."""
    valor = conexion.execute(
        update(secuencias)
        .where(secuencias.c.nombre == nombre)
        .values(ultimo_valor=secuencias.c.ultimo_valor + 1)
        .returning(secuencias.c.ultimo_valor)
    ).scalar_one_or_none()
    if valor is None:
        raise LookupError(f"Falta la secuencia «{nombre}»: ejecute database/01_esquema.sql.")
    return valor


def cargar_orden(
    conexion: Connection, numero: str, bloquear: bool = False
) -> OrdenDeServicio | None:
    consulta = select(ordenes).where(ordenes.c.numero == numero)
    if bloquear:
        consulta = consulta.with_for_update()
    fila = conexion.execute(consulta).mappings().first()
    if fila is None:
        return None
    return mapeo.orden_desde_filas(
        mapeo.FilasDeOrden(
            fila,
            _filas_internas(conexion, trabajos, numero),
            _filas_internas(conexion, solicitudes_de_compra, numero),
            _filas_internas(conexion, fallas_adicionales, numero),
        )
    )


def _filas_internas(conexion: Connection, tabla: Table, numero: str) -> Sequence[Any]:
    consulta = select(tabla).where(tabla.c.numero_orden == numero).order_by(tabla.c.id)
    return conexion.execute(consulta).mappings().all()


def cargar_cotizacion(
    conexion: Connection, id_cotizacion: str, bloquear: bool = False
) -> Cotizacion | None:
    consulta = select(cotizaciones).where(cotizaciones.c.id == id_cotizacion)
    if bloquear:
        consulta = consulta.with_for_update()
    fila = conexion.execute(consulta).mappings().first()
    if fila is None:
        return None
    lineas = select(lineas_de_cotizacion).where(
        lineas_de_cotizacion.c.id_cotizacion == id_cotizacion
    )
    refacciones = select(refacciones_cotizadas).where(
        refacciones_cotizadas.c.id_cotizacion == id_cotizacion
    )
    contactos = select(recontactos).where(recontactos.c.id_cotizacion == id_cotizacion)
    corregidas = select(correcciones_de_cotizacion).where(
        correcciones_de_cotizacion.c.id_cotizacion == id_cotizacion
    )
    return mapeo.cotizacion_desde_filas(
        mapeo.FilasDeCotizacion(
            fila,
            conexion.execute(lineas.order_by(lineas_de_cotizacion.c.numero)).mappings().all(),
            conexion.execute(
                refacciones.order_by(
                    refacciones_cotizadas.c.numero_linea, refacciones_cotizadas.c.posicion
                )
            )
            .mappings()
            .all(),
            conexion.execute(contactos.order_by(recontactos.c.id)).mappings().all(),
            conexion.execute(corregidas.order_by(correcciones_de_cotizacion.c.id))
            .mappings()
            .all(),
        )
    )


def _insertar(conexion: Connection, tabla: Table, filas: Sequence[Any]) -> None:
    if filas:
        conexion.execute(insert(tabla), list(filas))


def _guardar_fila(conexion: Connection, tabla: Table, llave: Any, fila: dict[str, Any]) -> None:
    """Actualiza la fila o la crea si aún no existe, como hace `guardar` en memoria."""
    if conexion.execute(update(tabla).where(llave).values(fila)).rowcount == 0:
        conexion.execute(insert(tabla).values(fila))


class RepositorioDeOrdenesSqlAlchemy(RepositorioDeOrdenes):
    def __init__(self, conexion: Connection, vistos: list[RaizDeAgregado]) -> None:
        self._conexion = conexion
        self._vistos = vistos
        self._cargadas: dict[str, OrdenDeServicio] = {}

    def obtener(self, numero: NumeroOrden) -> OrdenDeServicio:
        clave = str(numero)
        if clave in self._cargadas:
            return self._cargadas[clave]
        orden = cargar_orden(self._conexion, clave, bloquear=True)
        if orden is None:
            raise OrdenNoEncontrada(
                f"No se encontró la orden de servicio {numero}. "
                "Revise el número e intente de nuevo."
            )
        self._recordar(orden)
        return orden

    def agregar(self, orden: OrdenDeServicio) -> None:
        clave = str(orden.numero)
        if self._conexion.execute(
            select(ordenes.c.numero).where(ordenes.c.numero == clave)
        ).first():
            raise ValorInvalido(f"La orden {orden.numero} ya existe.")
        self._escribir(orden)
        self._recordar(orden)

    def guardar(self, orden: OrdenDeServicio) -> None:
        self._escribir(orden)
        self._recordar(orden)

    def siguiente_numero(self) -> NumeroOrden:
        return NumeroOrden(f"OS-{siguiente_folio(self._conexion, 'orden'):04d}")

    def _escribir(self, orden: OrdenDeServicio) -> None:
        filas = mapeo.filas_de_orden(orden)
        numero = str(orden.numero)
        _guardar_fila(self._conexion, ordenes, ordenes.c.numero == numero, dict(filas.orden))
        # Las solicitudes apuntan a los trabajos: se borran antes y se insertan después de ellos.
        for tabla in (solicitudes_de_compra, fallas_adicionales, trabajos):
            self._conexion.execute(delete(tabla).where(tabla.c.numero_orden == numero))
        _insertar(self._conexion, trabajos, filas.trabajos)
        _insertar(self._conexion, solicitudes_de_compra, filas.solicitudes)
        _insertar(self._conexion, fallas_adicionales, filas.fallas)

    def _recordar(self, orden: OrdenDeServicio) -> None:
        self._cargadas[str(orden.numero)] = orden
        self._vistos.append(orden)


class RepositorioDeCotizacionesSqlAlchemy(RepositorioDeCotizaciones):
    def __init__(self, conexion: Connection, vistos: list[RaizDeAgregado]) -> None:
        self._conexion = conexion
        self._vistos = vistos
        self._cargadas: dict[str, Cotizacion] = {}

    def obtener(self, id_cotizacion: str) -> Cotizacion:
        if id_cotizacion in self._cargadas:
            return self._cargadas[id_cotizacion]
        cotizacion = cargar_cotizacion(self._conexion, id_cotizacion, bloquear=True)
        if cotizacion is None:
            raise CotizacionNoEncontrada(
                f"No se encontró la cotización {id_cotizacion}. "
                "Revise el número e intente de nuevo."
            )
        self._recordar(cotizacion)
        return cotizacion

    def agregar(self, cotizacion: Cotizacion) -> None:
        if self._conexion.execute(
            select(cotizaciones.c.id).where(cotizaciones.c.id == cotizacion.id)
        ).first():
            raise ValorInvalido(f"La cotización {cotizacion.id} ya existe.")
        self._escribir(cotizacion)
        self._recordar(cotizacion)

    def guardar(self, cotizacion: Cotizacion) -> None:
        self._escribir(cotizacion)
        self._recordar(cotizacion)

    def de_la_orden(self, numero: NumeroOrden) -> list[Cotizacion]:
        ids = self._conexion.execute(
            select(cotizaciones.c.id)
            .where(cotizaciones.c.numero_orden == str(numero))
            .order_by(cotizaciones.c.version)
        ).scalars()
        return [self.obtener(id_cotizacion) for id_cotizacion in ids.all()]

    def siguiente_version(self, numero: NumeroOrden) -> VersionCotizacion:
        ultima = self._conexion.execute(
            select(func.max(cotizaciones.c.version)).where(
                cotizaciones.c.numero_orden == str(numero)
            )
        ).scalar_one()
        return VersionCotizacion((ultima or 0) + 1)

    def siguiente_id(self) -> str:
        return f"COT-{siguiente_folio(self._conexion, 'cotizacion'):04d}"

    def _escribir(self, cotizacion: Cotizacion) -> None:
        filas = mapeo.filas_de_cotizacion(cotizacion)
        id_cotizacion = cotizacion.id
        _guardar_fila(
            self._conexion,
            cotizaciones,
            cotizaciones.c.id == id_cotizacion,
            dict(filas.cotizacion),
        )
        # Ajustar o corregir una cotización cambia sus líneas: las partes internas se reemplazan.
        for tabla in (
            refacciones_cotizadas,
            lineas_de_cotizacion,
            recontactos,
            correcciones_de_cotizacion,
        ):
            self._conexion.execute(delete(tabla).where(tabla.c.id_cotizacion == id_cotizacion))
        _insertar(self._conexion, lineas_de_cotizacion, filas.lineas)
        _insertar(self._conexion, refacciones_cotizadas, filas.refacciones)
        _insertar(self._conexion, recontactos, filas.recontactos)
        _insertar(self._conexion, correcciones_de_cotizacion, filas.correcciones)

    def _recordar(self, cotizacion: Cotizacion) -> None:
        self._cargadas[cotizacion.id] = cotizacion
        self._vistos.append(cotizacion)


class RepositorioDeClientesSqlAlchemy(RepositorioDeClientes):
    def __init__(self, conexion: Connection) -> None:
        self._conexion = conexion
        self._cargados: dict[str, Cliente] = {}

    def obtener(self, id_cliente: str) -> Cliente:
        if id_cliente in self._cargados:
            return self._cargados[id_cliente]
        fila = (
            self._conexion.execute(select(clientes).where(clientes.c.id == id_cliente))
            .mappings()
            .first()
        )
        if fila is None:
            raise ClienteNoEncontrado(
                f"No se encontró el cliente {id_cliente}. "
                "Revise la clave e intente de nuevo."
            )
        cliente = mapeo.cliente_desde_fila(fila)
        self._cargados[id_cliente] = cliente
        return cliente

    def agregar(self, cliente: Cliente) -> None:
        if self._conexion.execute(
            select(clientes.c.id).where(clientes.c.id == cliente.id_cliente)
        ).first():
            raise ValorInvalido(f"El cliente {cliente.id_cliente} ya existe.")
        self.guardar(cliente)

    def guardar(self, cliente: Cliente) -> None:
        _guardar_fila(
            self._conexion,
            clientes,
            clientes.c.id == cliente.id_cliente,
            mapeo.fila_de_cliente(cliente),
        )
        self._cargados[cliente.id_cliente] = cliente

    def buscar_flotilla(self, empresa: str) -> Cliente | None:
        """Compara en Python: `lower()` de SQLite no entiende acentos y daría otro resultado."""
        buscada = empresa.strip().casefold()
        filas = self._conexion.execute(
            select(clientes.c.id, clientes.c.empresa)
            .where(clientes.c.tipo == TipoCliente.FLOTILLA.value)
            .order_by(clientes.c.id)
        ).all()
        for fila in filas:
            if (fila.empresa or "").strip().casefold() == buscada:
                return self.obtener(fila.id)
        return None

    def siguiente_id(self) -> str:
        return f"CLI-{siguiente_folio(self._conexion, 'cliente'):04d}"


class RepositorioDeVehiculosSqlAlchemy(RepositorioDeVehiculos):
    def __init__(self, conexion: Connection) -> None:
        self._conexion = conexion
        self._cargados: dict[str, Vehiculo] = {}

    def por_placas(self, placas: Placas) -> Vehiculo:
        clave = str(placas)
        if clave in self._cargados:
            return self._cargados[clave]
        fila = (
            self._conexion.execute(select(vehiculos).where(vehiculos.c.placas == clave))
            .mappings()
            .first()
        )
        if fila is None:
            raise VehiculoNoEncontrado(
                f"No hay un vehículo con las placas {placas}. "
                "Revíselas o registre el vehículo."
            )
        vehiculo = mapeo.vehiculo_desde_fila(fila)
        self._cargados[clave] = vehiculo
        return vehiculo

    def agregar(self, vehiculo: Vehiculo) -> None:
        if self._conexion.execute(
            select(vehiculos.c.placas).where(vehiculos.c.placas == str(vehiculo.placas))
        ).first():
            raise ValorInvalido(
                f"Ya existe un vehículo con las placas {vehiculo.placas}. "
                "Revise el dato capturado."
            )
        self.guardar(vehiculo)

    def guardar(self, vehiculo: Vehiculo) -> None:
        self._exigir_vin_libre(vehiculo)
        clave = str(vehiculo.placas)
        _guardar_fila(
            self._conexion,
            vehiculos,
            vehiculos.c.placas == clave,
            mapeo.fila_de_vehiculo(vehiculo),
        )
        self._cargados[clave] = vehiculo

    def _exigir_vin_libre(self, vehiculo: Vehiculo) -> None:
        """Responde con el error del negocio, no con el de la restricción UNIQUE."""
        if self._conexion.execute(
            select(vehiculos.c.placas).where(
                vehiculos.c.vin == str(vehiculo.vin), vehiculos.c.placas != str(vehiculo.placas)
            )
        ).first():
            raise ValorInvalido(
                f"Ya existe un vehículo con el VIN {vehiculo.vin}. "
                "Revise el dato capturado."
            )


class RepositorioDeEmpleadosSqlAlchemy(RepositorioDeEmpleados):
    def __init__(self, conexion: Connection) -> None:
        self._conexion = conexion

    def obtener(self, id_empleado: str) -> Empleado:
        fila = (
            self._conexion.execute(select(empleados).where(empleados.c.id == id_empleado))
            .mappings()
            .first()
        )
        if fila is None:
            raise EmpleadoNoEncontrado(
                f"No se encontró el empleado {id_empleado}. "
                "Revise la clave e intente de nuevo."
            )
        return mapeo.empleado_desde_fila(fila)


class RepositorioDeAlertasSqlAlchemy(RepositorioDeAlertas):
    def __init__(self, conexion: Connection) -> None:
        self._conexion = conexion

    def agregar(self, alerta: AlertaInterna) -> None:
        self._conexion.execute(insert(alertas_internas).values(mapeo.fila_de_alerta(alerta)))

    def existe_clave(self, clave: str) -> bool:
        consulta = select(alertas_internas.c.id).where(alertas_internas.c.clave == clave)
        return self._conexion.execute(consulta).first() is not None


class CatalogoDeServiciosSqlAlchemy(CatalogoDeServicios):
    def __init__(self, conexion: Connection) -> None:
        self._conexion = conexion

    def servicios_inhabilitados_de_la_orden(self, numero: NumeroOrden) -> tuple[str, ...]:
        consulta = (
            select(catalogo_servicios.c.recurso_id)
            .join(
                servicios_solicitados,
                servicios_solicitados.c.recurso_id == catalogo_servicios.c.recurso_id,
            )
            .where(
                servicios_solicitados.c.numero_orden == str(numero),
                catalogo_servicios.c.habilitado.is_(False),
            )
            .order_by(catalogo_servicios.c.recurso_id)
        )
        return tuple(self._conexion.execute(consulta).scalars())
