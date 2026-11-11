"""Implementaciones en memoria de los Repositories, con el mismo contrato que las de SQLAlchemy."""
from __future__ import annotations

from application.puertos import AlertaInterna, CatalogoDeServicios, RepositorioDeAlertas
from domain.clientes.cliente import Cliente
from domain.clientes.repositorio import RepositorioDeClientes
from domain.compartido.errores import (
    ClienteNoEncontrado,
    CorreccionNoPermitida,
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
from domain.ordenes.estados import esta_abierta
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.repositorio import RepositorioDeOrdenes
from domain.vehiculos.repositorio import RepositorioDeVehiculos
from domain.vehiculos.vehiculo import Vehiculo
from infrastructure.memoria.almacen import DatosEnMemoria


class RepositorioDeOrdenesEnMemoria(RepositorioDeOrdenes):
    def __init__(self, datos: DatosEnMemoria, vistos: list[RaizDeAgregado]) -> None:
        self._datos = datos
        self._vistos = vistos

    def obtener(self, numero: NumeroOrden) -> OrdenDeServicio:
        try:
            orden = self._datos.ordenes[str(numero)]
        except KeyError:
            raise OrdenNoEncontrada(
                f"No se encontró la orden de servicio {numero}. "
                "Revise el número e intente de nuevo."
            ) from None
        self._vistos.append(orden)
        return orden

    def agregar(self, orden: OrdenDeServicio) -> None:
        if str(orden.numero) in self._datos.ordenes:
            raise ValorInvalido(f"La orden {orden.numero} ya existe.")
        self._datos.ordenes[str(orden.numero)] = orden
        self._vistos.append(orden)

    def guardar(self, orden: OrdenDeServicio) -> None:
        self._datos.ordenes[str(orden.numero)] = orden
        self._vistos.append(orden)

    def siguiente_numero(self) -> NumeroOrden:
        self._datos.ultimo_folio_de_orden += 1
        return NumeroOrden(f"OS-{self._datos.ultimo_folio_de_orden:04d}")

    def abierta_del_vehiculo(self, placas: Placas) -> OrdenDeServicio | None:
        for numero in sorted(self._datos.ordenes):
            orden = self._datos.ordenes[numero]
            if orden.placas == placas and esta_abierta(orden.estado):
                self._vistos.append(orden)
                return orden
        return None


class RepositorioDeCotizacionesEnMemoria(RepositorioDeCotizaciones):
    def __init__(self, datos: DatosEnMemoria, vistos: list[RaizDeAgregado]) -> None:
        self._datos = datos
        self._vistos = vistos

    def obtener(self, id_cotizacion: str) -> Cotizacion:
        try:
            cotizacion = self._datos.cotizaciones[id_cotizacion]
        except KeyError:
            raise CotizacionNoEncontrada(
                f"No se encontró la cotización {id_cotizacion}. "
                "Revise el número e intente de nuevo."
            ) from None
        self._vistos.append(cotizacion)
        return cotizacion

    def agregar(self, cotizacion: Cotizacion) -> None:
        if cotizacion.id in self._datos.cotizaciones:
            raise ValorInvalido(f"La cotización {cotizacion.id} ya existe.")
        self._datos.cotizaciones[cotizacion.id] = cotizacion
        self._vistos.append(cotizacion)

    def guardar(self, cotizacion: Cotizacion) -> None:
        self._datos.cotizaciones[cotizacion.id] = cotizacion
        self._vistos.append(cotizacion)

    def de_la_orden(self, numero: NumeroOrden) -> list[Cotizacion]:
        cotizaciones = [c for c in self._datos.cotizaciones.values() if c.numero_orden == numero]
        self._vistos.extend(cotizaciones)
        return sorted(cotizaciones, key=lambda cotizacion: cotizacion.version.numero)

    def siguiente_version(self, numero: NumeroOrden) -> VersionCotizacion:
        versiones = [
            c.version.numero for c in self._datos.cotizaciones.values() if c.numero_orden == numero
        ]
        return VersionCotizacion(max(versiones, default=0) + 1)

    def siguiente_id(self) -> str:
        self._datos.ultimo_folio_de_cotizacion += 1
        return f"COT-{self._datos.ultimo_folio_de_cotizacion:04d}"


class RepositorioDeClientesEnMemoria(RepositorioDeClientes):
    def __init__(self, datos: DatosEnMemoria) -> None:
        self._datos = datos

    def obtener(self, id_cliente: str) -> Cliente:
        try:
            return self._datos.clientes[id_cliente]
        except KeyError:
            raise ClienteNoEncontrado(
                f"No se encontró el cliente {id_cliente}. "
                "Revise la clave e intente de nuevo."
            ) from None

    def agregar(self, cliente: Cliente) -> None:
        if cliente.id_cliente in self._datos.clientes:
            raise ValorInvalido(f"El cliente {cliente.id_cliente} ya existe.")
        self._datos.clientes[cliente.id_cliente] = cliente

    def guardar(self, cliente: Cliente) -> None:
        self._datos.clientes[cliente.id_cliente] = cliente

    def buscar_flotilla(self, empresa: str) -> Cliente | None:
        buscada = empresa.strip().casefold()
        for cliente in self._datos.clientes.values():
            if cliente.es_de_flotilla and (cliente.empresa or "").strip().casefold() == buscada:
                return cliente
        return None

    def siguiente_id(self) -> str:
        self._datos.ultimo_folio_de_cliente += 1
        return f"CLI-{self._datos.ultimo_folio_de_cliente:04d}"


class RepositorioDeVehiculosEnMemoria(RepositorioDeVehiculos):
    def __init__(self, datos: DatosEnMemoria) -> None:
        self._datos = datos

    def por_placas(self, placas: Placas) -> Vehiculo:
        try:
            return self._datos.vehiculos[str(placas)]
        except KeyError:
            raise VehiculoNoEncontrado(
                f"No hay un vehículo con las placas {placas}. "
                "Revíselas o registre el vehículo."
            ) from None

    def agregar(self, vehiculo: Vehiculo) -> None:
        if str(vehiculo.placas) in self._datos.vehiculos:
            raise ValorInvalido(
                f"Ya existe un vehículo con las placas {vehiculo.placas}. "
                "Revise el dato capturado."
            )
        self._exigir_vin_libre(vehiculo)
        self._datos.vehiculos[str(vehiculo.placas)] = vehiculo

    def guardar(self, vehiculo: Vehiculo) -> None:
        self._exigir_vin_libre(vehiculo)
        self._datos.vehiculos[str(vehiculo.placas)] = vehiculo

    def cambiar_placas(self, anteriores: Placas, nuevas: Placas) -> Vehiculo:
        vehiculo = self.por_placas(anteriores)
        _exigir_placas_libres(nuevas, str(nuevas) in self._datos.vehiculos)
        del self._datos.vehiculos[str(anteriores)]
        vehiculo.placas = nuevas
        self._datos.vehiculos[str(nuevas)] = vehiculo
        for orden in self._datos.ordenes.values():
            if orden.placas == anteriores:
                orden.placas = nuevas
        return vehiculo

    def _exigir_vin_libre(self, vehiculo: Vehiculo) -> None:
        """El VIN es único en la base (UNIQUE), así que aquí se rechaza igual."""
        for otro in self._datos.vehiculos.values():
            if otro.vin == vehiculo.vin and otro.placas != vehiculo.placas:
                raise ValorInvalido(
                    f"Ya existe un vehículo con el VIN {vehiculo.vin}. "
                    "Revise el dato capturado."
                )


class RepositorioDeEmpleadosEnMemoria(RepositorioDeEmpleados):
    def __init__(self, datos: DatosEnMemoria) -> None:
        self._datos = datos

    def obtener(self, id_empleado: str) -> Empleado:
        try:
            return self._datos.empleados[id_empleado]
        except KeyError:
            raise EmpleadoNoEncontrado(
                f"No se encontró el empleado {id_empleado}. "
                "Revise la clave e intente de nuevo."
            ) from None


class RepositorioDeAlertasEnMemoria(RepositorioDeAlertas):
    def __init__(self, datos: DatosEnMemoria) -> None:
        self._datos = datos

    def agregar(self, alerta: AlertaInterna) -> None:
        self._datos.alertas.append(alerta)

    def existe_clave(self, clave: str) -> bool:
        return any(alerta.clave == clave for alerta in self._datos.alertas)


class CatalogoDeServiciosEnMemoria(CatalogoDeServicios):
    def __init__(self, datos: DatosEnMemoria) -> None:
        self._datos = datos

    def servicios_inhabilitados_de_la_orden(self, numero: NumeroOrden) -> tuple[str, ...]:
        return tuple(sorted(self._datos.servicios_inhabilitados.get(str(numero), ())))


def _exigir_placas_libres(placas: Placas, ocupadas: bool) -> None:
    if ocupadas:
        raise CorreccionNoPermitida(
            f"Las placas {placas} ya pertenecen a otro vehículo. Revise el dato capturado."
        )

