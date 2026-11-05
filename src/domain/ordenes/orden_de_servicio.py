"""Aggregate Orden de Servicio (raíz: OrdenDeServicio).

Es el expediente del servicio. Sus invariantes están en modelo-de-dominio.md §2.1. Cada método
valida antes de modificar nada, para no dejar el Aggregate a medias.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import NoReturn

from domain.compartido.errores import (
    CancelacionNoPermitida,
    DiagnosticoNoModificable,
    DiagnosticoRequerido,
    EntregaNoPermitida,
    PagoNoPermitido,
    SolicitudNoEncontrada,
    SolicitudNoPermitida,
    TrabajoDeOtroTecnico,
    TrabajoNoAutorizado,
    TrabajoNoEncontrado,
    TrabajoNoPermitido,
    TransicionDeEstadoNoPermitida,
    ValorInvalido,
)
from domain.compartido.eventos import RaizDeAgregado
from domain.compartido.valores import Dinero, NumeroOrden, Placas, texto_requerido
from domain.cotizaciones.valores import DecisionDelCliente, TipoCotizacion, TrabajoDecidido
from domain.ordenes import eventos as ev
from domain.ordenes.especificaciones import (
    PuedeCancelarse,
    PuedeEntregarse,
    PuedeIniciarTrabajo,
    PuedeSolicitarRefaccion,
)
from domain.ordenes.estados import MAQUINA_DE_ORDEN, EstadoOrden, EstadoTrabajo
from domain.ordenes.falla_adicional import FallaAdicional
from domain.ordenes.solicitud_de_compra import SolicitudDeCompra
from domain.ordenes.trabajo import Trabajo
from domain.ordenes.valores import (
    Cancelacion,
    CargoACredito,
    Diagnostico,
    EstadoDeRecepcion,
    NotaDeResponsabilidad,
    Pago,
)

_O = EstadoOrden


class OrdenDeServicio(RaizDeAgregado):
    def __init__(
        self,
        numero: NumeroOrden,
        id_cliente: str,
        es_cliente_de_flotilla: bool,
        placas: Placas,
        asesor: str,
        motivo_de_ingreso: str,
        fecha_ingreso: datetime,
        estado_de_recepcion: EstadoDeRecepcion | None = None,
    ) -> None:
        super().__init__()
        self.numero = numero
        self.id_cliente = id_cliente
        self.es_cliente_de_flotilla = es_cliente_de_flotilla
        self.placas = placas
        self.asesor = asesor
        self.motivo_de_ingreso = texto_requerido(
            motivo_de_ingreso, "La orden debe indicar el motivo de ingreso."
        )
        self.fecha_ingreso = fecha_ingreso
        self.estado_de_recepcion = estado_de_recepcion
        self.estado = _O.RECIBIDA
        self.ultima_actualizacion = fecha_ingreso
        self.fecha_ingreso_a_fila: datetime | None = fecha_ingreso
        self.tecnico_de_diagnostico: str | None = None
        self.diagnostico: Diagnostico | None = None
        self.cotizada = False
        self.rechazo_total = False
        self.adicionales_pendientes = 0
        self.nota_de_responsabilidad: NotaDeResponsabilidad | None = None
        self.pago: Pago | None = None
        self.cargo_a_credito: CargoACredito | None = None
        self.fecha_entrega: datetime | None = None
        self.cancelacion: Cancelacion | None = None
        self._trabajos: dict[int, Trabajo] = {}
        self._solicitudes: dict[int, SolicitudDeCompra] = {}
        self._fallas: dict[int, FallaAdicional] = {}

    @classmethod
    def registrar(
        cls,
        numero: NumeroOrden,
        id_cliente: str,
        es_cliente_de_flotilla: bool,
        placas: Placas,
        asesor: str,
        motivo_de_ingreso: str,
        recepcion: EstadoDeRecepcion,
        fecha: datetime,
    ) -> OrdenDeServicio:
        orden = cls(
            numero, id_cliente, es_cliente_de_flotilla, placas, asesor, motivo_de_ingreso, fecha,
            recepcion,
        )
        orden._registrar(ev.OrdenRecibida(fecha, str(numero), id_cliente, str(placas), asesor))
        return orden

    # ------------------------------------------------------------------ consultas
    @property
    def trabajos(self) -> tuple[Trabajo, ...]:
        return tuple(self._trabajos[i] for i in sorted(self._trabajos))

    @property
    def solicitudes(self) -> tuple[SolicitudDeCompra, ...]:
        return tuple(self._solicitudes[i] for i in sorted(self._solicitudes))

    @property
    def fallas_adicionales(self) -> tuple[FallaAdicional, ...]:
        return tuple(self._fallas[i] for i in sorted(self._fallas))

    @property
    def total_autorizado(self) -> Dinero:
        total = Dinero.cero()
        for trabajo in self._trabajos.values():
            if trabajo.esta_autorizado:
                total = total + trabajo.importe
        return total

    @property
    def estado_antes_de_espera(self) -> EstadoOrden | None:
        """Estado al que regresará cuando ya no falten refacciones (CA-022, CA-025)."""
        if self.estado in (_O.EN_ESPERA_DE_REFACCION, _O.PAUSADA_POR_RETIRO_DE_VEHICULO):
            return self._estado_de_regreso()
        return None

    # ------------------------------------------------------------------ diagnóstico
    def asignar_tecnico_para_diagnostico(self, tecnico: str, fecha: datetime) -> None:
        self._cambiar_estado(_O.EN_DIAGNOSTICO, fecha)
        self.tecnico_de_diagnostico = tecnico
        self._registrar(ev.TecnicoAsignadoParaDiagnostico(fecha, str(self.numero), tecnico))

    def registrar_diagnostico(self, diagnostico: Diagnostico) -> None:
        if self.cotizada:
            raise DiagnosticoNoModificable()
        if self.estado is not _O.EN_DIAGNOSTICO:
            raise TransicionDeEstadoNoPermitida(
                f"Solo se registra el diagnóstico de una orden «{_O.EN_DIAGNOSTICO.value}»; "
                f"la orden {self.numero} está en «{self.estado.value}»."
            )
        if diagnostico.tecnico != self.tecnico_de_diagnostico:
            raise TrabajoDeOtroTecnico("El diagnóstico de esta orden está asignado a otro técnico.")
        self.diagnostico = diagnostico
        self.ultima_actualizacion = diagnostico.registrado_en
        self._registrar(
            ev.DiagnosticoRegistrado(
                diagnostico.registrado_en, str(self.numero), diagnostico.tecnico, self.asesor
            )
        )

    def reportar_falla_adicional(
        self, descripcion: str, tecnico: str, fecha: datetime
    ) -> FallaAdicional:
        self._exigir_en_reparacion("reportar una falla adicional")
        falla = FallaAdicional(len(self._fallas) + 1, descripcion, tecnico, fecha)
        self._fallas[falla.id] = falla
        self.ultima_actualizacion = fecha
        self._registrar(
            ev.FallaAdicionalReportada(
                fecha, str(self.numero), falla.id, falla.descripcion, self.asesor
            )
        )
        return falla

    # ------------------------------------------------------------------ cotización y decisión
    def marcar_cotizada(self, fecha: datetime) -> None:
        if self.diagnostico is None:
            raise DiagnosticoRequerido(
                "No se puede cotizar una orden sin diagnóstico registrado por el técnico."
            )
        self._cambiar_estado(_O.COTIZADA, fecha)
        self.cotizada = True

    def registrar_cotizacion_adicional_pendiente(self, fecha: datetime) -> None:
        self._exigir_en_reparacion("generar una cotización adicional")
        self.adicionales_pendientes += 1
        self.ultima_actualizacion = fecha

    def aplicar_decision(self, decision: DecisionDelCliente) -> None:
        """Convierte la decisión del cliente sobre una cotización en trabajos de la orden."""
        if decision.tipo_cotizacion is TipoCotizacion.ADICIONAL:
            self._aplicar_decision_adicional(decision)
        else:
            self._aplicar_decision_inicial(decision)

    def _aplicar_decision_inicial(self, decision: DecisionDelCliente) -> None:
        if self.estado is not _O.COTIZADA:
            raise TransicionDeEstadoNoPermitida(
                "La decisión de la cotización inicial solo aplica a una orden "
                f"«{_O.COTIZADA.value}»; la orden {self.numero} está en «{self.estado.value}»."
            )
        if decision.es_rechazo_total:
            self.rechazo_total = True
            self.ultima_actualizacion = decision.registrada_en
            return
        self._cambiar_estado(_O.AUTORIZADA, decision.registrada_en)
        self._agregar_trabajos(decision)
        self._registrar(
            ev.OrdenAutorizada(decision.registrada_en, str(self.numero), decision.id_cotizacion)
        )

    def _aplicar_decision_adicional(self, decision: DecisionDelCliente) -> None:
        if self.adicionales_pendientes == 0:
            raise TransicionDeEstadoNoPermitida(
                f"La orden {self.numero} no tiene una cotización adicional esperando decisión."
            )
        self._agregar_trabajos(decision)
        self.adicionales_pendientes -= 1
        self.ultima_actualizacion = decision.registrada_en
        self._pasar_a_lista_si_corresponde(decision.registrada_en)

    # ------------------------------------------------------------------ reparación
    def asignar_trabajos(self, ids: Iterable[int], tecnico: str, fecha: datetime) -> None:
        if not any(trabajo.esta_autorizado for trabajo in self._trabajos.values()):
            raise TrabajoNoAutorizado(f"La orden {self.numero} no tiene trabajos autorizados.")
        if self.estado is _O.PAUSADA_POR_RETIRO_DE_VEHICULO:
            raise TrabajoNoPermitido("No se asignan trabajos: el vehículo no está en el taller.")
        seleccion = tuple(self._trabajo(id_trabajo) for id_trabajo in ids)
        if not seleccion:
            raise ValorInvalido("Debe seleccionar al menos un trabajo para asignar.")
        for trabajo in seleccion:
            self._exigir_asignable(trabajo)
        for trabajo in seleccion:
            trabajo.asignar(tecnico)
        self.ultima_actualizacion = fecha
        ids_asignados = tuple(trabajo.id for trabajo in seleccion)
        self._registrar(ev.TrabajosAsignados(fecha, str(self.numero), ids_asignados, tecnico))

    def iniciar_trabajo(self, id_trabajo: int, tecnico: str, fecha: datetime) -> None:
        trabajo = self._trabajo(id_trabajo)
        if not PuedeIniciarTrabajo(tecnico).es_satisfecha_por((self, trabajo)):
            self._rechazar_inicio(trabajo, tecnico)
        trabajo.iniciar()
        if self.estado is _O.AUTORIZADA:
            self._cambiar_estado(_O.EN_REPARACION, fecha)
        self.ultima_actualizacion = fecha
        self._registrar(ev.TrabajoIniciado(fecha, str(self.numero), trabajo.id, tecnico))

    def completar_trabajo(self, id_trabajo: int, tecnico: str, fecha: datetime) -> None:
        trabajo = self._trabajo(id_trabajo)
        self._exigir_tecnico_asignado(trabajo, tecnico)
        self._exigir_vehiculo_en_el_taller()
        if self._es_el_ultimo_abierto(trabajo) and self._hay_solicitudes_pendientes():
            raise TransicionDeEstadoNoPermitida(
                "No se puede completar el último trabajo mientras haya refacciones pendientes: "
                "la orden no puede quedar lista para entrega."
            )
        trabajo.completar()
        self.ultima_actualizacion = fecha
        self._pasar_a_lista_si_corresponde(fecha)

    # ------------------------------------------------------------------ refacciones
    def crear_solicitud_de_compra(
        self, id_trabajo: int, refaccion: str, cantidad: int, fecha: datetime
    ) -> SolicitudDeCompra:
        trabajo = self._trabajo(id_trabajo)
        if not trabajo.esta_autorizado:
            raise TrabajoNoAutorizado(
                f"No se puede solicitar «{refaccion}»: el trabajo «{trabajo.descripcion}» "
                "no fue autorizado por el cliente."
            )
        if not PuedeSolicitarRefaccion().es_satisfecha_por((self, trabajo)):
            raise SolicitudNoPermitida(
                f"No se pueden solicitar refacciones del trabajo «{trabajo.descripcion}» "
                f"({trabajo.estado.value}) con la orden en «{self.estado.value}»."
            )
        solicitud = SolicitudDeCompra(
            len(self._solicitudes) + 1, trabajo.id, refaccion, cantidad, fecha
        )
        if self.estado is not _O.EN_ESPERA_DE_REFACCION:
            self._cambiar_estado(_O.EN_ESPERA_DE_REFACCION, fecha)
        self._solicitudes[solicitud.id] = solicitud
        self.ultima_actualizacion = fecha
        self._registrar(
            ev.SolicitudDeCompraCreada(
                fecha, str(self.numero), solicitud.id, trabajo.id, solicitud.refaccion, cantidad
            )
        )
        return solicitud

    def registrar_llegada_de_refaccion(self, id_solicitud: int, fecha: datetime) -> None:
        solicitud = self._solicitud(id_solicitud)
        solicitud.marcar_disponible(fecha)
        self.ultima_actualizacion = fecha
        self._registrar(
            ev.RefaccionDisponible(
                fecha,
                str(self.numero),
                solicitud.id,
                self._trabajos[solicitud.id_trabajo].tecnico,
                self.asesor,
            )
        )
        if self.estado is _O.EN_ESPERA_DE_REFACCION and not self._hay_solicitudes_pendientes():
            self._cambiar_estado(self._estado_de_regreso(), fecha)
            self.nota_de_responsabilidad = None

    def registrar_aviso_al_cliente(self, id_solicitud: int, fecha: datetime) -> None:
        solicitud = self._solicitud(id_solicitud)
        solicitud.registrar_aviso_al_cliente(fecha)
        self.ultima_actualizacion = fecha
        self._registrar(ev.ClienteAvisadoDelRetraso(fecha, str(self.numero), solicitud.id))

    # ------------------------------------------------------------------ retiro anticipado
    def registrar_salida(self, fecha: datetime) -> NotaDeResponsabilidad:
        if self.estado is not _O.EN_ESPERA_DE_REFACCION:
            raise TransicionDeEstadoNoPermitida(
                f"Solo se registra la salida de una orden «{_O.EN_ESPERA_DE_REFACCION.value}»; "
                f"la orden {self.numero} está en «{self.estado.value}»."
            )
        self.nota_de_responsabilidad = NotaDeResponsabilidad(fecha)
        self.ultima_actualizacion = fecha
        return self.nota_de_responsabilidad

    def confirmar_firma_de_nota(self, fecha: datetime) -> None:
        MAQUINA_DE_ORDEN.validar(self.estado, _O.PAUSADA_POR_RETIRO_DE_VEHICULO)
        if self.nota_de_responsabilidad is None:
            raise TransicionDeEstadoNoPermitida(
                "Primero debe registrarse la salida para generar la Nota de Responsabilidad."
            )
        self.nota_de_responsabilidad = self.nota_de_responsabilidad.firmar(fecha)
        self._cambiar_estado(_O.PAUSADA_POR_RETIRO_DE_VEHICULO, fecha)
        self.fecha_ingreso_a_fila = None
        self._registrar(ev.VehiculoRetirado(fecha, str(self.numero)))

    def reactivar(self, fecha: datetime) -> None:
        if self.estado is not _O.PAUSADA_POR_RETIRO_DE_VEHICULO:
            raise TransicionDeEstadoNoPermitida(
                f"Solo se reactiva una orden «{_O.PAUSADA_POR_RETIRO_DE_VEHICULO.value}»; "
                f"la orden {self.numero} está en «{self.estado.value}»."
            )
        nuevo = (
            _O.EN_ESPERA_DE_REFACCION
            if self._hay_solicitudes_pendientes()
            else self._estado_de_regreso()
        )
        self._cambiar_estado(nuevo, fecha)
        self.fecha_ingreso_a_fila = fecha
        self._registrar(ev.OrdenReactivada(fecha, str(self.numero), nuevo.value))

    # ------------------------------------------------------------------ caja
    def registrar_pago(self, pago: Pago) -> None:
        MAQUINA_DE_ORDEN.validar(self.estado, _O.PAGADA)
        if self.es_cliente_de_flotilla:
            raise PagoNoPermitido(
                "Las órdenes de flotilla se registran como cargo a crédito, "
                "no como pago de contado."
            )
        if pago.monto != self.total_autorizado:
            raise PagoNoPermitido(
                f"El pago debe cubrir el total autorizado de {self.total_autorizado}."
            )
        self._cambiar_estado(_O.PAGADA, pago.registrado_en)
        self.pago = pago
        self._registrar(
            ev.PagoRegistrado(
                pago.registrado_en, str(self.numero), str(pago.monto.monto), pago.forma.value
            )
        )

    def registrar_cargo_a_credito(self, fecha: datetime) -> None:
        MAQUINA_DE_ORDEN.validar(self.estado, _O.POR_COBRAR_CREDITO)
        if not self.es_cliente_de_flotilla:
            raise PagoNoPermitido("El cargo a crédito solo aplica a clientes de flotilla.")
        self._cambiar_estado(_O.POR_COBRAR_CREDITO, fecha)
        self.cargo_a_credito = CargoACredito(self.total_autorizado, fecha)
        self._registrar(
            ev.CargoACreditoRegistrado(fecha, str(self.numero), str(self.total_autorizado.monto))
        )

    # ------------------------------------------------------------------ entrega y cancelación
    def entregar(self, fecha: datetime) -> None:
        self._exigir_que_pueda_entregarse()
        self._cambiar_estado(_O.CERRADA, fecha)
        self.fecha_entrega = fecha
        vence = None
        if self.cargo_a_credito is not None:
            self.cargo_a_credito = self.cargo_a_credito.con_vencimiento(fecha)
            vence = str(self.cargo_a_credito.fecha_vencimiento)
        self._registrar(ev.VehiculoEntregado(fecha, str(self.numero), vence=vence))

    def entregar_sin_reparacion(self, fecha: datetime) -> None:
        self._exigir_que_pueda_entregarse()
        self._cambiar_estado(_O.CERRADA_SIN_REPARACION, fecha)
        self.fecha_entrega = fecha
        self._registrar(ev.VehiculoEntregado(fecha, str(self.numero), sin_reparacion=True))

    def cancelar(self, motivo: str, asesor: str, fecha: datetime) -> None:
        if not PuedeCancelarse().es_satisfecha_por(self):
            raise CancelacionNoPermitida(
                f"La orden {self.numero} (estado «{self.estado.value}») no se puede cancelar: "
                "una orden con cotización no se cancela; si el cliente no desea la reparación, "
                "se registra el rechazo total de la cotización."
            )
        cancelacion = Cancelacion(motivo, fecha, asesor)
        self._cambiar_estado(_O.CANCELADA, fecha)
        self.cancelacion = cancelacion
        self.fecha_ingreso_a_fila = None
        self._registrar(ev.OrdenCancelada(fecha, str(self.numero), cancelacion.motivo, asesor))

    # ------------------------------------------------------------------ apoyo
    def _agregar_trabajos(self, decision: DecisionDelCliente) -> None:
        for decidido in decision.autorizados:
            self._agregar_trabajo(decidido, decision.id_cotizacion, EstadoTrabajo.PENDIENTE)
        for decidido in decision.no_autorizados:
            self._agregar_trabajo(decidido, decision.id_cotizacion, EstadoTrabajo.NO_AUTORIZADO)

    def _agregar_trabajo(
        self, decidido: TrabajoDecidido, id_cotizacion: str, estado: EstadoTrabajo
    ) -> None:
        nuevo_id = len(self._trabajos) + 1
        self._trabajos[nuevo_id] = Trabajo(
            nuevo_id,
            decidido.descripcion,
            decidido.importe,
            estado,
            id_cotizacion,
            decidido.numero_linea,
        )

    def _trabajo(self, id_trabajo: int) -> Trabajo:
        try:
            return self._trabajos[id_trabajo]
        except KeyError:
            raise TrabajoNoEncontrado(
                f"La orden {self.numero} no tiene el trabajo {id_trabajo}."
            ) from None

    def _solicitud(self, id_solicitud: int) -> SolicitudDeCompra:
        try:
            return self._solicitudes[id_solicitud]
        except KeyError:
            raise SolicitudNoEncontrada(
                f"La orden {self.numero} no tiene la solicitud de compra {id_solicitud}."
            ) from None

    def _exigir_en_reparacion(self, accion: str) -> None:
        if self.estado is not _O.EN_REPARACION:
            raise TransicionDeEstadoNoPermitida(
                f"Solo se puede {accion} con la orden «{_O.EN_REPARACION.value}»; "
                f"la orden {self.numero} está en «{self.estado.value}»."
            )

    def _exigir_asignable(self, trabajo: Trabajo) -> None:
        if not trabajo.esta_autorizado:
            raise TrabajoNoAutorizado(
                f"El trabajo «{trabajo.descripcion}» no fue autorizado por el cliente."
            )
        if trabajo.estado is not EstadoTrabajo.PENDIENTE:
            raise TrabajoNoPermitido(
                f"El trabajo «{trabajo.descripcion}» ya está en «{trabajo.estado.value}»."
            )

    def _exigir_tecnico_asignado(self, trabajo: Trabajo, tecnico: str) -> None:
        if trabajo.tecnico != tecnico:
            raise TrabajoDeOtroTecnico(
                f"El trabajo «{trabajo.descripcion}» no está asignado a este técnico."
            )

    def _exigir_vehiculo_en_el_taller(self) -> None:
        if self.estado is _O.PAUSADA_POR_RETIRO_DE_VEHICULO:
            raise TrabajoNoPermitido(
                f"El vehículo de la orden {self.numero} no está en el taller: "
                "se retiró con Nota de Responsabilidad."
            )

    def _rechazar_inicio(self, trabajo: Trabajo, tecnico: str) -> NoReturn:
        self._exigir_tecnico_asignado(trabajo, tecnico)
        self._exigir_vehiculo_en_el_taller()
        raise TrabajoNoPermitido(
            f"El trabajo «{trabajo.descripcion}» está en «{trabajo.estado.value}»; "
            "solo se inicia un trabajo pendiente."
        )

    def _exigir_que_pueda_entregarse(self) -> None:
        if not PuedeEntregarse().es_satisfecha_por(self):
            raise EntregaNoPermitida(
                f"No se puede entregar el vehículo de la orden {self.numero} "
                f"(estado «{self.estado.value}»): primero debe registrarse el pago "
                "o el cargo a crédito."
            )

    def _hay_solicitudes_pendientes(self) -> bool:
        return any(solicitud.esta_pendiente for solicitud in self._solicitudes.values())

    def _estado_de_regreso(self) -> EstadoOrden:
        iniciado = any(trabajo.fue_iniciado for trabajo in self._trabajos.values())
        return _O.EN_REPARACION if iniciado else _O.AUTORIZADA

    def _es_el_ultimo_abierto(self, trabajo: Trabajo) -> bool:
        return all(
            otro.esta_completado
            for otro in self._trabajos.values()
            if otro.esta_autorizado and otro is not trabajo
        )

    def _pasar_a_lista_si_corresponde(self, fecha: datetime) -> None:
        autorizados = [t for t in self._trabajos.values() if t.esta_autorizado]
        if (
            self.estado is _O.EN_REPARACION
            and self.adicionales_pendientes == 0
            and all(trabajo.esta_completado for trabajo in autorizados)
        ):
            self._cambiar_estado(_O.LISTA_PARA_ENTREGA, fecha)
            self._registrar(ev.OrdenListaParaEntrega(fecha, str(self.numero), self.asesor))

    def _cambiar_estado(self, nuevo: EstadoOrden, fecha: datetime) -> None:
        MAQUINA_DE_ORDEN.validar(self.estado, nuevo)
        self.estado = nuevo
        self.ultima_actualizacion = fecha
