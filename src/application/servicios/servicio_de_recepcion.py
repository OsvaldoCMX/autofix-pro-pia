"""Recepción del vehículo: clientes, vehículos y apertura de la orden (US-001 a US-003, US-016)."""
from __future__ import annotations

from application.comandos import DatosDeVehiculo, RegistrarCliente, RegistrarOrden
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import ResultadoDeCliente, ResultadoDeOrden
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.clientes.cliente import Cliente, ResponsableDeFlotilla, TipoCliente
from domain.compartido.errores import ValorInvalido, VehiculoNoEncontrado
from domain.compartido.valores import VIN, Placas
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.valores import EstadoDeRecepcion
from domain.vehiculos.vehiculo import Vehiculo


class ServicioDeRecepcion:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador

    def registrar_cliente(self, comando: RegistrarCliente) -> ResultadoDeCliente:
        with self._uow as uow:
            cliente = _obtener_o_crear_cliente(uow, comando)
            uow.confirmar()
        return _resultado_de_cliente(cliente)

    def registrar_orden(self, comando: RegistrarOrden) -> ResultadoDeOrden:
        ahora = self._reloj.ahora()
        placas = Placas(comando.placas)
        recepcion = EstadoDeRecepcion(comando.kilometraje, comando.nivel_de_combustible)
        with self._uow as uow:
            cliente = _preparar_cliente_y_vehiculo(uow, placas, comando)
            orden = OrdenDeServicio.registrar(
                uow.ordenes.siguiente_numero(),
                cliente.id_cliente,
                cliente.es_de_flotilla,
                placas,
                comando.asesor,
                comando.motivo_de_ingreso,
                recepcion,
                ahora,
            )
            uow.ordenes.agregar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeOrden(
            str(orden.numero),
            orden.estado.value,
            orden.id_cliente,
            str(placas),
            orden.fecha_ingreso,
        )


def _preparar_cliente_y_vehiculo(
    uow: UnidadDeTrabajo, placas: Placas, comando: RegistrarOrden
) -> Cliente:
    try:
        vehiculo = uow.vehiculos.por_placas(placas)
    except VehiculoNoEncontrado:
        return _registrar_vehiculo_nuevo(uow, placas, comando)
    return _reutilizar_vehiculo(uow, vehiculo, comando)


def _reutilizar_vehiculo(
    uow: UnidadDeTrabajo, vehiculo: Vehiculo, comando: RegistrarOrden
) -> Cliente:
    """Cliente recurrente (CA-003): se usan sus registros y se actualiza lo que el asesor envió."""
    if comando.id_cliente is not None and comando.id_cliente != vehiculo.id_cliente:
        raise ValorInvalido(f"El vehículo con placas {vehiculo.placas} pertenece a otro cliente.")
    cliente = uow.clientes.obtener(vehiculo.id_cliente)
    if comando.cliente is not None:
        _actualizar_cliente(uow, cliente, comando.cliente)
    if comando.vehiculo is not None:
        vehiculo.actualizar_datos(
            VIN(comando.vehiculo.vin),
            comando.vehiculo.marca,
            comando.vehiculo.modelo,
            comando.vehiculo.anio,
        )
        uow.vehiculos.guardar(vehiculo)
    return cliente


def _registrar_vehiculo_nuevo(
    uow: UnidadDeTrabajo, placas: Placas, comando: RegistrarOrden
) -> Cliente:
    """Placas no registradas (CA-004): se crea el registro desde cero."""
    if comando.vehiculo is None:
        raise ValorInvalido(
            f"Las placas {placas} no están registradas: capture los datos del vehículo."
        )
    cliente = _cliente_del_vehiculo_nuevo(uow, comando)
    uow.vehiculos.agregar(_nuevo_vehiculo(placas, comando.vehiculo, cliente.id_cliente))
    return cliente


def _cliente_del_vehiculo_nuevo(uow: UnidadDeTrabajo, comando: RegistrarOrden) -> Cliente:
    if comando.id_cliente is not None:
        cliente = uow.clientes.obtener(comando.id_cliente)
        if comando.cliente is not None:
            _actualizar_cliente(uow, cliente, comando.cliente)
        return cliente
    if comando.cliente is None:
        raise ValorInvalido("Indique el cliente existente o capture los datos del cliente nuevo.")
    return _obtener_o_crear_cliente(uow, comando.cliente)


def _actualizar_cliente(uow: UnidadDeTrabajo, cliente: Cliente, datos: RegistrarCliente) -> None:
    cliente.actualizar_contacto(datos.nombre, datos.telefono, datos.correo)
    uow.clientes.guardar(cliente)


def _obtener_o_crear_cliente(uow: UnidadDeTrabajo, datos: RegistrarCliente) -> Cliente:
    """Una empresa ya registrada no se duplica: se devuelve con su Responsable (CA-028)."""
    if datos.tipo is TipoCliente.FLOTILLA and datos.empresa:
        existente = uow.clientes.buscar_flotilla(datos.empresa)
        if existente is not None:
            return existente
    cliente = Cliente(
        uow.clientes.siguiente_id(),
        datos.nombre,
        datos.tipo,
        datos.telefono,
        datos.correo,
        datos.empresa,
        _responsable(datos),
    )
    uow.clientes.agregar(cliente)
    return cliente


def _responsable(datos: RegistrarCliente) -> ResponsableDeFlotilla | None:
    if datos.tipo is not TipoCliente.FLOTILLA or datos.responsable_nombre is None:
        return None
    return ResponsableDeFlotilla(
        datos.responsable_nombre, datos.responsable_telefono or "", datos.responsable_correo or ""
    )


def _nuevo_vehiculo(placas: Placas, datos: DatosDeVehiculo, id_cliente: str) -> Vehiculo:
    return Vehiculo(placas, VIN(datos.vin), datos.marca, datos.modelo, datos.anio, id_cliente)


def _resultado_de_cliente(cliente: Cliente) -> ResultadoDeCliente:
    return ResultadoDeCliente(
        cliente.id_cliente,
        cliente.nombre,
        cliente.tipo.value,
        cliente.empresa,
        cliente.responsable.nombre if cliente.responsable else None,
    )
