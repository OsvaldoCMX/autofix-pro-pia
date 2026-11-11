"""Aggregate Orden de Servicio (raíz: OrdenDeServicio).

Es el expediente del servicio. Sus invariantes están en modelo-de-dominio.md §2.1. Cada método
valida antes de modificar nada, para no dejar el Aggregate a medias.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime
from typing import NoReturn

from domain.compartido.errores import (
    CancelacionNoPermitida,
    CorreccionNoPermitida,
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
from domain.ordenes.estados import MAQUINA_DE_ORDEN, EstadoOrden, EstadoSolicitud, EstadoTrabajo
from domain.ordenes.falla_adicional import FallaAdicional
from domain.ordenes.solicitud_de_compra import SolicitudDeCompra
from domain.ordenes.trabajo import Trabajo
from domain.ordenes.valores import (
    Cancelacion,
    CargoACredito,
    Diagnostico,
    EstadoDeRecepcion,
    FormaDePago,
    NotaDeResponsabilidad,
    Pago,
)

_O = EstadoOrden
_ORDEN_CERRADA = (_O.CERRADA, _O.CERRADA_SIN_REPARACION)
_REGRESO_DEL_VEHICULO = "Cuando regrese, reactive la orden para continuar."


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
        """Asigna el técnico (CA-035) o lo cambia antes del diagnóstico (CA-054, RN-28)."""
        if self.estado is _O.EN_DIAGNOSTICO:
            self._cambiar_tecnico_de_diagnostico(tecnico, fecha)
            return
        if not MAQUINA_DE_ORDEN.permite(self.estado, _O.EN_DIAGNOSTICO):
            raise TransicionDeEstadoNoPermitida(
                "El técnico de diagnóstico solo se asigna o se cambia antes del diagnóstico "
                f"(orden «{_O.RECIBIDA.value}» o «{_O.EN_DIAGNOSTICO.value}»); "
                f"la orden {self.numero} está en «{self.estado.value}»."
            )
        self._cambiar_estado(_O.EN_DIAGNOSTICO, fecha)
        self.tecnico_de_diagnostico = tecnico
        self._registrar(ev.TecnicoAsignadoParaDiagnostico(fecha, str(self.numero), tecnico))

    def corregir_datos_de_recepcion(
        self, recepcion: EstadoDeRecepcion, motivo_de_ingreso: str, fecha: datetime
    ) -> None:
        """RN-29: solo antes de la cotización; no cambia el estado de la orden (CA-057)."""
        if self.estado not in (_O.RECIBIDA, _O.EN_DIAGNOSTICO):
            raise CorreccionNoPermitida(
                f"Los datos de recepción de la orden {self.numero} solo se corrigen antes de la "
                f"cotización (orden «{_O.RECIBIDA.value}» o «{_O.EN_DIAGNOSTICO.value}»); "
                f"ahora está en «{self.estado.value}»."
            )
        motivo = texto_requerido(motivo_de_ingreso, "La orden debe indicar el motivo de ingreso.")
        self.estado_de_recepcion = recepcion
        self.motivo_de_ingreso = motivo
        self.ultima_actualizacion = fecha
        self._registrar(
            ev.DatosDeRecepcionCorregidos(
                fecha,
                str(self.numero),
                recepcion.kilometraje,
                recepcion.nivel_de_combustible.value,
                motivo,
            )
        )

    def exigir_placas_corregibles(self) -> None:
        """RN-35: las placas solo se corrigen antes de la cotización."""
        if self.estado not in (_O.RECIBIDA, _O.EN_DIAGNOSTICO):
            raise CorreccionNoPermitida(
                f"Las placas de la orden {self.numero} solo se corrigen antes de la cotización "
                f"(orden «{_O.RECIBIDA.value}» o «{_O.EN_DIAGNOSTICO.value}»); "
                f"ahora está en «{self.estado.value}»."
            )

    def corregir_placas(self, placas: Placas, fecha: datetime) -> None:
        """El vehículo ya cambió sus placas; la orden las toma (CA-066, RN-35)."""
        self.exigir_placas_corregibles()
        anteriores = self.placas
        self.placas = placas
        self.ultima_actualizacion = fecha
        self._registrar(
            ev.PlacasCorregidas(fecha, str(self.numero), str(anteriores), str(placas))
        )

    def _cambiar_tecnico_de_diagnostico(self, tecnico: str, fecha: datetime) -> None:
        """No cambia el estado: la orden sale del panel del técnico anterior (RN-28)."""
        if self.diagnostico is not None:
            raise CorreccionNoPermitida(
                f"El diagnóstico de la orden {self.numero} ya está registrado; "
                "ya no se puede cambiar el técnico."
            )
        anterior = self.tecnico_de_diagnostico
        if anterior == tecnico:
            return
        self.tecnico_de_diagnostico = tecnico
        self.ultima_actualizacion = fecha
        self._registrar(
            ev.TecnicoDeDiagnosticoReasignado(fecha, str(self.numero), anterior or "", tecnico)
        )

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
                f"Todavía no se puede cotizar la orden {self.numero}: "
                "falta que el técnico registre el diagnóstico."
            )
        if self.estado is _O.COTIZADA:
            raise TransicionDeEstadoNoPermitida(
                f"La orden {self.numero} ya tiene su cotización inicial."
            )
        if not MAQUINA_DE_ORDEN.permite(self.estado, _O.COTIZADA):
            raise TransicionDeEstadoNoPermitida(
                f"Solo se cotiza una orden «{_O.EN_DIAGNOSTICO.value}»; "
                f"la orden {self.numero} está en «{self.estado.value}»."
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
            raise TrabajoNoAutorizado(
                f"La orden {self.numero} no tiene trabajos autorizados: "
                "el cliente rechazó la cotización o aún no decide."
            )
        if self.estado is _O.PAUSADA_POR_RETIRO_DE_VEHICULO:
            raise TrabajoNoPermitido(
                f"No se asignan trabajos: el vehículo no está en el taller. {_REGRESO_DEL_VEHICULO}"
            )
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
                "No se puede completar el último trabajo mientras haya refacciones pendientes. "
                "Podrá completarlo cuando se registre su llegada."
            )
        self._exigir_completable(trabajo)
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
        self._exigir_refaccion_no_solicitada(trabajo, refaccion)
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

    def _exigir_refaccion_no_solicitada(self, trabajo: Trabajo, refaccion: str) -> None:
        """RN-34: la misma refacción no se pide dos veces mientras su solicitud esté pendiente."""
        buscada = _sin_espacios_de_mas(refaccion)
        for solicitud in self._solicitudes.values():
            if (
                solicitud.id_trabajo == trabajo.id
                and solicitud.estado is EstadoSolicitud.SOLICITADA
                and _sin_espacios_de_mas(solicitud.refaccion) == buscada
            ):
                raise SolicitudNoPermitida(
                    f"La refacción «{solicitud.refaccion}» del trabajo «{trabajo.descripcion}» "
                    "ya está solicitada y Compras la está gestionando."
                )

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
        if not MAQUINA_DE_ORDEN.permite(self.estado, _O.PAUSADA_POR_RETIRO_DE_VEHICULO):
            raise TransicionDeEstadoNoPermitida(
                f"Solo se confirma la firma de una orden «{_O.EN_ESPERA_DE_REFACCION.value}» "
                f"con salida registrada; la orden {self.numero} está en «{self.estado.value}»."
            )
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
        self._exigir_cobrable(_O.PAGADA)
        if self.es_cliente_de_flotilla:
            raise PagoNoPermitido(
                "Las órdenes de flotilla no se pagan de contado: registre el cargo a crédito."
            )
        if pago.monto != self.total_autorizado:
            raise PagoNoPermitido(
                "El monto no coincide: el pago debe cubrir el total autorizado de "
                f"{self.total_autorizado}. Corríjalo e intente de nuevo."
            )
        self._cambiar_estado(_O.PAGADA, pago.registrado_en)
        self.pago = pago
        self._registrar(
            ev.PagoRegistrado(
                pago.registrado_en, str(self.numero), str(pago.monto.monto), pago.forma.value
            )
        )

    def corregir_forma_de_pago(self, forma: FormaDePago, fecha: datetime) -> None:
        """RN-30: solo con la orden «Pagada»; el monto y la fecha del pago no cambian."""
        if self.estado is not _O.PAGADA or self.pago is None:
            raise CorreccionNoPermitida(self._por_que_no_se_corrige_el_pago())
        anterior = self.pago.forma
        if anterior is forma:
            return
        self.pago = replace(self.pago, forma=forma)
        self.ultima_actualizacion = fecha
        self._registrar(
            ev.FormaDePagoCorregida(fecha, str(self.numero), anterior.value, forma.value)
        )

    def _por_que_no_se_corrige_el_pago(self) -> str:
        if self.pago is not None:
            return (
                f"El vehículo de la orden {self.numero} ya se entregó; "
                "la forma de pago ya no se corrige."
            )
        return (
            f"La orden {self.numero} no tiene un pago de contado que corregir "
            f"(estado «{self.estado.value}»)."
        )

    def registrar_cargo_a_credito(self, fecha: datetime) -> None:
        self._exigir_cobrable(_O.POR_COBRAR_CREDITO)
        if not self.es_cliente_de_flotilla:
            raise PagoNoPermitido(
                "El cargo a crédito solo aplica a clientes de flotilla. "
                "Para este cliente, registre el pago de contado."
            )
        self._cambiar_estado(_O.POR_COBRAR_CREDITO, fecha)
        self.cargo_a_credito = CargoACredito(self.total_autorizado, fecha)
        self._registrar(
            ev.CargoACreditoRegistrado(fecha, str(self.numero), str(self.total_autorizado.monto))
        )

    # ------------------------------------------------------------------ entrega y cancelación
    def entregar(self, fecha: datetime) -> None:
        self._exigir_que_pueda_entregarse()
        if not MAQUINA_DE_ORDEN.permite(self.estado, _O.CERRADA):
            raise TransicionDeEstadoNoPermitida(
                f"El cliente de la orden {self.numero} rechazó toda la cotización: "
                "use «Entregar sin reparación»."
            )
        self._cambiar_estado(_O.CERRADA, fecha)
        self.fecha_entrega = fecha
        vence = None
        if self.cargo_a_credito is not None:
            self.cargo_a_credito = self.cargo_a_credito.con_vencimiento(fecha)
            vence = str(self.cargo_a_credito.fecha_vencimiento)
        self._registrar(ev.VehiculoEntregado(fecha, str(self.numero), vence=vence))

    def entregar_sin_reparacion(self, fecha: datetime) -> None:
        self._exigir_que_pueda_entregarse()
        if not MAQUINA_DE_ORDEN.permite(self.estado, _O.CERRADA_SIN_REPARACION):
            raise TransicionDeEstadoNoPermitida(
                f"La orden {self.numero} ya tiene pago o cargo a crédito: "
                "registre la entrega normal, no «Entregar sin reparación»."
            )
        self._cambiar_estado(_O.CERRADA_SIN_REPARACION, fecha)
        self.fecha_entrega = fecha
        self._registrar(ev.VehiculoEntregado(fecha, str(self.numero), sin_reparacion=True))

    def cancelar(self, motivo: str, asesor: str, fecha: datetime) -> None:
        if not PuedeCancelarse().es_satisfecha_por(self):
            raise CancelacionNoPermitida(self._motivo_de_no_cancelar())
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
                f"El trabajo «{trabajo.descripcion}» no está asignado a usted. "
                "Solicite que se lo asignen."
            )

    def _exigir_vehiculo_en_el_taller(self) -> None:
        if self.estado is _O.PAUSADA_POR_RETIRO_DE_VEHICULO:
            raise TrabajoNoPermitido(
                f"El vehículo de la orden {self.numero} no está en el taller: "
                f"se retiró con Nota de Responsabilidad. {_REGRESO_DEL_VEHICULO}"
            )

    def _exigir_completable(self, trabajo: Trabajo) -> None:
        if trabajo.estado is EstadoTrabajo.PENDIENTE:
            raise TransicionDeEstadoNoPermitida(
                f"El trabajo «{trabajo.descripcion}» aún no se inicia: "
                "inícielo antes de marcarlo como completado."
            )
        if trabajo.esta_completado:
            raise TransicionDeEstadoNoPermitida(
                f"El trabajo «{trabajo.descripcion}» ya está completado."
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
            raise EntregaNoPermitida(self._motivo_de_no_entregar())

    def _motivo_de_no_entregar(self) -> str:
        """El mensaje solo pide el pago si la orden todavía puede llegar a cobrarse."""
        if self.estado is _O.CANCELADA:
            return (
                f"La orden {self.numero} está cancelada, "
                "así que ya no se registra su entrega ni su cobro."
            )
        if self.estado in _ORDEN_CERRADA:
            return (
                f"El vehículo de la orden {self.numero} ya fue entregado; "
                "no hay nada más que registrar."
            )
        inicio = f"El vehículo de la orden {self.numero} todavía no se puede entregar: "
        if self.estado is _O.LISTA_PARA_ENTREGA:
            return f"{inicio}primero debe registrarse el pago o el cargo a crédito en Caja."
        if self.estado is _O.COTIZADA:
            return (
                f"{inicio}el cliente aún no decide sobre la cotización. "
                "Si la rechaza por completo, registre el rechazo total; si la autoriza, "
                "al terminar la reparación primero debe registrarse el pago o el cargo a crédito."
            )
        return (
            f"{inicio}su servicio sigue en proceso (estado «{self.estado.value}»). "
            f"Cuando esté «{_O.LISTA_PARA_ENTREGA.value}», "
            "primero debe registrarse el pago o el cargo a crédito."
        )

    def _exigir_cobrable(self, nuevo: EstadoOrden) -> None:
        if not MAQUINA_DE_ORDEN.permite(self.estado, nuevo):
            raise TransicionDeEstadoNoPermitida(self._motivo_de_no_cobrar())

    def _motivo_de_no_cobrar(self) -> str:
        if self.estado is _O.CANCELADA:
            return f"La orden {self.numero} está cancelada: no genera ningún cobro."
        if self.estado in _ORDEN_CERRADA:
            return f"La orden {self.numero} ya está cerrada: no hay cobro pendiente."
        if self.estado is _O.PAGADA:
            return f"La orden {self.numero} ya tiene su pago registrado."
        if self.estado is _O.POR_COBRAR_CREDITO:
            return f"La orden {self.numero} ya tiene registrado un cargo a crédito."
        return (
            f"Todavía no se puede cobrar la orden {self.numero}: debe estar "
            f"«{_O.LISTA_PARA_ENTREGA.value}» y ahora está en «{self.estado.value}»."
        )

    def _motivo_de_no_cancelar(self) -> str:
        """Solo sugiere el rechazo total mientras todavía se puede registrar (CA-045)."""
        if self.estado is _O.CANCELADA:
            return f"La orden {self.numero} ya está cancelada."
        if self.estado in _ORDEN_CERRADA:
            return (
                f"La orden {self.numero} ya está cerrada y su vehículo fue entregado: "
                "no se puede cancelar."
            )
        if self.estado is not _O.COTIZADA:
            return (
                f"La orden {self.numero} (estado «{self.estado.value}») no se puede cancelar: "
                "el cliente ya autorizó trabajos."
            )
        inicio = f"La orden {self.numero} ya tiene cotización, por lo que no se cancela. "
        if self.rechazo_total:
            return f"{inicio}El rechazo total ya está registrado: use «Entregar sin reparación»."
        return (
            f"{inicio}Si el cliente no desea la reparación, "
            "se registra el rechazo total de la cotización."
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


def _sin_espacios_de_mas(texto: str) -> str:
    """Compara textos sin distinguir mayúsculas ni espacios repetidos o en los extremos."""
    return " ".join(texto.split()).casefold()

