"""Recepción del vehículo: clientes, vehículos, apertura de la orden y correcciones de datos.

US-001 a US-003, US-016 y US-027 (H-PIA-24).
"""
from __future__ import annotations

from application.comandos import (
    CorregirCliente,
    CorregirPlacas,
    CorregirRecepcion,
    CorregirVehiculo,
    DatosDeVehiculo,
    RegistrarCliente,
    RegistrarOrden,
)
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import (
    ResultadoDeCliente,
    ResultadoDeOrden,
    ResultadoDeRecepcion,
    ResultadoDeVehiculo,
)
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.clientes.cliente import Cliente, ResponsableDeFlotilla, TipoCliente
from domain.compartido.errores import ValorInvalido, VehiculoNoEncontrado
from domain.compartido.valores import VIN, NumeroOrden, Placas
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.valores import EstadoDeRecepcion
from domain.servicios.verificador_de_orden_unica import VerificadorDeOrdenUnica
from domain.vehiculos.vehiculo import Vehiculo


class ServicioDeRecepcion:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador

    def _anio_actual(self) -> int:
        return self._reloj.ahora_en_el_taller().year

    def registrar_cliente(self, comando: RegistrarCliente) -> ResultadoDeCliente:
        with self._uow as uow:
            cliente = _obtener_o_crear_cliente(uow, comando)
            uow.confirmar()
        return _resultado_de_cliente(cliente)

    def corregir_cliente(self, comando: CorregirCliente) -> ResultadoDeCliente:
        """RN-29: con las mismas validaciones del registro; no cambia órdenes ni cotizaciones."""
        with self._uow as uow:
            cliente = uow.clientes.obtener(comando.id_cliente)
            cliente.actualizar_contacto(comando.nombre, comando.telefono, comando.correo)
            uow.clientes.guardar(cliente)
            uow.confirmar()
        return _resultado_de_cliente(cliente)

    def corregir_vehiculo(self, comando: CorregirVehiculo) -> ResultadoDeVehiculo:
        """RN-29: el VIN no puede ser el de otro vehículo (lo revisa el repositorio)."""
        with self._uow as uow:
            vehiculo = uow.vehiculos.por_placas(Placas(comando.placas))
            vehiculo.actualizar_datos(
                VIN(comando.vin), comando.marca, comando.modelo, comando.anio, self._anio_actual()
            )
            uow.vehiculos.guardar(vehiculo)
            uow.confirmar()
        return ResultadoDeVehiculo(
            str(vehiculo.placas), str(vehiculo.vin), vehiculo.marca, vehiculo.modelo, vehiculo.anio
        )

    def corregir_recepcion(self, comando: CorregirRecepcion) -> ResultadoDeRecepcion:
        recepcion = EstadoDeRecepcion.capturado(comando.kilometraje, comando.nivel_de_combustible)
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.corregir_datos_de_recepcion(
                recepcion, comando.motivo_de_ingreso, self._reloj.ahora()
            )
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeRecepcion(
            str(orden.numero),
            orden.estado.value,
            recepcion.kilometraje,
            recepcion.nivel_de_combustible.value,
            orden.motivo_de_ingreso,
        )

    def corregir_placas(self, comando: CorregirPlacas) -> ResultadoDeOrden:
        """RN-35: el vehículo y sus órdenes cambian de placas en la misma Unidad de Trabajo."""
        nuevas = Placas(comando.placas)
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.exigir_placas_corregibles()
            if nuevas != orden.placas:
                uow.vehiculos.cambiar_placas(orden.placas, nuevas)
                orden.corregir_placas(nuevas, self._reloj.ahora())
                uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeOrden(
            str(orden.numero), orden.estado.value, orden.id_cliente, str(orden.placas),
            orden.fecha_ingreso,
        )

    def registrar_orden(self, comando: RegistrarOrden) -> ResultadoDeOrden:
        ahora = self._reloj.ahora()
        placas = Placas(comando.placas)
        recepcion = EstadoDeRecepcion.capturado(comando.kilometraje, comando.nivel_de_combustible)
        with self._uow as uow:
            VerificadorDeOrdenUnica().verificar(placas, uow.ordenes.abierta_del_vehiculo(placas))
            cliente = _preparar_cliente_y_vehiculo(uow, placas, comando, self._anio_actual())
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
    uow: UnidadDeTrabajo, placas: Placas, comando: RegistrarOrden, anio_actual: int
) -> Cliente:
    try:
        vehiculo = uow.vehiculos.por_placas(placas)
    except VehiculoNoEncontrado:
        return _registrar_vehiculo_nuevo(uow, placas, comando, anio_actual)
    return _reutilizar_vehiculo(uow, vehiculo, comando, anio_actual)


def _reutilizar_vehiculo(
    uow: UnidadDeTrabajo, vehiculo: Vehiculo, comando: RegistrarOrden, anio_actual: int
) -> Cliente:
    """Cliente recurrente (CA-003): se usan sus registros y se actualiza lo que el asesor envió."""
    if comando.id_cliente is not None and comando.id_cliente != vehiculo.id_cliente:
        raise ValorInvalido(
            f"El vehículo con placas {vehiculo.placas} pertenece a otro cliente. "
            "Revise las placas o el cliente seleccionado."
        )
    cliente = uow.clientes.obtener(vehiculo.id_cliente)
    if comando.cliente is not None:
        _actualizar_cliente(uow, cliente, comando.cliente)
    if comando.vehiculo is not None:
        vehiculo.actualizar_datos(
            VIN(comando.vehiculo.vin),
            comando.vehiculo.marca,
            comando.vehiculo.modelo,
            comando.vehiculo.anio,
            anio_actual,
        )
        uow.vehiculos.guardar(vehiculo)
    return cliente


def _registrar_vehiculo_nuevo(
    uow: UnidadDeTrabajo, placas: Placas, comando: RegistrarOrden, anio_actual: int
) -> Cliente:
    """Placas no registradas (CA-004): se crea el registro desde cero."""
    if comando.vehiculo is None:
        raise ValorInvalido(
            f"Las placas {placas} no están registradas: capture los datos del vehículo."
        )
    cliente = _cliente_del_vehiculo_nuevo(uow, comando)
    uow.vehiculos.agregar(
        _nuevo_vehiculo(placas, comando.vehiculo, cliente.id_cliente, anio_actual)
    )
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
    """Una empresa ya registrada no se duplica: se devuelve con su Responsable (CA-028).

    Si llegan datos distintos de su Responsable, se avisa en lugar de ignorarlos (CA-065).
    """
    if datos.tipo is TipoCliente.FLOTILLA and datos.empresa:
        existente = uow.clientes.buscar_flotilla(datos.empresa)
        if existente is not None:
            existente.exigir_mismo_responsable(
                datos.responsable_nombre, datos.responsable_telefono, datos.responsable_correo
            )
            return existente
    cliente = Cliente.registrar(
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
    return ResponsableDeFlotilla.capturar(
        datos.responsable_nombre, datos.responsable_telefono or "", datos.responsable_correo or ""
    )


def _nuevo_vehiculo(
    placas: Placas, datos: DatosDeVehiculo, id_cliente: str, anio_actual: int
) -> Vehiculo:
    return Vehiculo.registrar(
        placas, VIN(datos.vin), datos.marca, datos.modelo, datos.anio, id_cliente, anio_actual
    )


def _resultado_de_cliente(cliente: Cliente) -> ResultadoDeCliente:
    return ResultadoDeCliente(
        cliente.id_cliente,
        cliente.nombre,
        cliente.tipo.value,
        cliente.empresa,
        cliente.responsable.nombre if cliente.responsable else None,
        cliente.telefono,
        cliente.correo,
    )
