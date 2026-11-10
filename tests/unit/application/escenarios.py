"""Arma la aplicación en memoria para las pruebas, como lo hará el Composition Root."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TypeVar
from unittest.mock import Mock
from zoneinfo import ZoneInfo

from application.comandos import (
    AsignarTecnicoParaDiagnostico,
    AsignarTrabajos,
    CompletarTrabajo,
    ConfirmarFirmaDeNota,
    DatosDeVehiculo,
    GenerarCotizacion,
    IniciarTrabajo,
    RegistrarCargoACredito,
    RegistrarCliente,
    RegistrarDecisionDelCliente,
    RegistrarDiagnostico,
    RegistrarOrden,
    RegistrarPago,
    RegistrarSalida,
    SolicitarRefaccion,
    TrabajoPropuesto,
)
from application.consultas.lector import LectorDeOrdenes
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import ResultadoDeDecision
from application.servicios.servicio_de_aprobacion_gerencial import ServicioDeAprobacionGerencial
from application.servicios.servicio_de_autorizacion import ServicioDeAutorizacion
from application.servicios.servicio_de_caja import ServicioDeCaja
from application.servicios.servicio_de_cancelacion import ServicioDeCancelacion
from application.servicios.servicio_de_cotizacion import ServicioDeCotizacion
from application.servicios.servicio_de_diagnostico import ServicioDeDiagnostico
from application.servicios.servicio_de_entrega import ServicioDeEntrega
from application.servicios.servicio_de_recepcion import ServicioDeRecepcion
from application.servicios.servicio_de_refacciones import ServicioDeRefacciones
from application.servicios.servicio_de_reparacion import ServicioDeReparacion
from application.servicios.servicio_de_retiro import ServicioDeRetiro
from application.servicios.servicio_de_revision_de_plazos import ServicioDeRevisionDePlazos
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.clientes.cliente import TipoCliente
from domain.cotizaciones.valores import RolDeAutorizante
from domain.empleados.empleado import Empleado, RolDeEmpleado
from domain.ordenes.valores import FormaDePago, NivelDeCombustible
from infrastructure.memoria.almacen import AlmacenEnMemoria, DatosEnMemoria
from infrastructure.memoria.lector import LectorEnMemoria
from infrastructure.memoria.unidad_de_trabajo import UnidadDeTrabajoEnMemoria

S = TypeVar("S")

PARTICULAR = RegistrarCliente("Luis Peña", telefono="81-2222-0000", correo="luis@correo.test")
FLOTILLA = RegistrarCliente(
    "Transportes Norte SA",
    TipoCliente.FLOTILLA,
    "81-3333-0000",
    "contacto@norte.test",
    "Transportes Norte",
    "Ana Torres",
    "81-1111-0000",
    "ana@norte.test",
)
TOTAL_DE_DOS_TRABAJOS = Decimal("3000.00")
AUTORIZANTE_PARTICULAR = ("Luis Peña", RolDeAutorizante.CLIENTE)
AUTORIZANTE_DE_FLOTILLA = ("Ana Torres", RolDeAutorizante.RESPONSABLE_DE_FLOTILLA)
ZONA_DEL_TALLER = ZoneInfo("America/Monterrey")
AHORA = datetime(2026, 10, 5, 15, 0, tzinfo=UTC)  # lunes
ASESOR = "EMP-001"
TECNICO = "EMP-002"
OTRO_TECNICO = "EMP-003"
GERENTE = "EMP-004"
COMPRAS = "EMP-005"
CAJA = "EMP-006"
EMPLEADOS = (
    Empleado(ASESOR, "Laura Méndez", RolDeEmpleado.ASESOR),
    Empleado(TECNICO, "Carlos Ruiz", RolDeEmpleado.TECNICO),
    Empleado(OTRO_TECNICO, "Diego Salinas", RolDeEmpleado.TECNICO),
    Empleado(GERENTE, "Patricia Garza", RolDeEmpleado.GERENTE),
    Empleado(COMPRAS, "Jorge Treviño", RolDeEmpleado.COMPRAS),
    Empleado(CAJA, "Sofía Leal", RolDeEmpleado.CAJA),
)


def poner_hora(reloj: Mock, fecha: datetime) -> None:
    reloj.ahora.return_value = fecha.astimezone(UTC)
    reloj.ahora_en_el_taller.return_value = fecha.astimezone(ZONA_DEL_TALLER)


class Taller:
    """Almacén con los 6 empleados, reloj falso y publicador simulado."""

    def __init__(self, publicador: PublicadorDeEventos | None = None) -> None:
        self.almacen = AlmacenEnMemoria(EMPLEADOS)
        self.reloj = Mock(spec=Reloj)
        poner_hora(self.reloj, AHORA)
        self.publicador = publicador or Mock(spec=PublicadorDeEventos)

    def uow(self) -> UnidadDeTrabajo:
        return UnidadDeTrabajoEnMemoria(self.almacen)

    def lector(self) -> LectorDeOrdenes:
        return LectorEnMemoria(self.almacen)

    def ordenes_registradas(self) -> int:
        return len(self.datos.ordenes)

    def registrar_servicios_de_orden(
        self, numero: str, habilitados: tuple[str, ...], inhabilitados: tuple[str, ...]
    ) -> None:
        self.datos.servicios_inhabilitados[numero] = inhabilitados

    @property
    def datos(self) -> DatosEnMemoria:
        return self.almacen.datos

    def _armar(self, servicio: type[S]) -> S:
        return servicio(self.uow(), self.reloj, self.publicador)

    @property
    def recepcion(self) -> ServicioDeRecepcion:
        return self._armar(ServicioDeRecepcion)

    @property
    def cancelacion(self) -> ServicioDeCancelacion:
        return self._armar(ServicioDeCancelacion)

    @property
    def diagnostico(self) -> ServicioDeDiagnostico:
        return self._armar(ServicioDeDiagnostico)

    @property
    def cotizacion(self) -> ServicioDeCotizacion:
        return self._armar(ServicioDeCotizacion)

    @property
    def aprobacion(self) -> ServicioDeAprobacionGerencial:
        return self._armar(ServicioDeAprobacionGerencial)

    @property
    def autorizacion(self) -> ServicioDeAutorizacion:
        return self._armar(ServicioDeAutorizacion)

    @property
    def reparacion(self) -> ServicioDeReparacion:
        return self._armar(ServicioDeReparacion)

    @property
    def refacciones(self) -> ServicioDeRefacciones:
        return self._armar(ServicioDeRefacciones)

    @property
    def retiro(self) -> ServicioDeRetiro:
        return self._armar(ServicioDeRetiro)

    @property
    def caja(self) -> ServicioDeCaja:
        return self._armar(ServicioDeCaja)

    @property
    def entrega(self) -> ServicioDeEntrega:
        return self._armar(ServicioDeEntrega)

    @property
    def revision(self) -> ServicioDeRevisionDePlazos:
        return ServicioDeRevisionDePlazos(self.uow(), self.lector(), self.reloj)


# ------------------------------------------------------------------ pasos para llegar a un estado
def recibida(taller: Taller, flotilla: bool = False) -> str:
    consecutivo = taller.ordenes_registradas() + 1
    resultado = taller.recepcion.registrar_orden(
        RegistrarOrden(
            ASESOR,
            f"ABC{consecutivo:03d}",
            "Ruido al frenar",
            45000,
            NivelDeCombustible.MEDIO,
            DatosDeVehiculo(f"1HGCM82633A{consecutivo:06d}", "Nissan", "Versa", 2020),
            cliente=FLOTILLA if flotilla else PARTICULAR,
        )
    )
    return resultado.numero_orden


def en_diagnostico(taller: Taller, flotilla: bool = False, tecnico: str = TECNICO) -> str:
    numero = recibida(taller, flotilla)
    taller.diagnostico.asignar_tecnico(AsignarTecnicoParaDiagnostico(numero, tecnico))
    return numero


def diagnosticada(taller: Taller, flotilla: bool = False, tecnico: str = TECNICO) -> str:
    numero = en_diagnostico(taller, flotilla, tecnico)
    taller.diagnostico.registrar_diagnostico(
        RegistrarDiagnostico(numero, tecnico, "Balatas gastadas", "Cambiar balatas")
    )
    return numero


def trabajos(*importes: str) -> tuple[TrabajoPropuesto, ...]:
    return tuple(
        TrabajoPropuesto(numero, f"Trabajo {numero}", Decimal(importe))
        for numero, importe in enumerate(importes, start=1)
    )


def cotizada(
    taller: Taller, flotilla: bool = False, importes: tuple[str, ...] = ("1000.00", "2000.00")
) -> tuple[str, str]:
    """Devuelve el número de la orden y el id de su cotización inicial."""
    numero = diagnosticada(taller, flotilla)
    resultado = taller.cotizacion.generar_inicial(GenerarCotizacion(numero, trabajos(*importes)))
    return numero, resultado.id


def decidir(
    taller: Taller, id_cotizacion: str, lineas: tuple[int, ...], flotilla: bool = False
) -> ResultadoDeDecision:
    nombre, rol = AUTORIZANTE_DE_FLOTILLA if flotilla else AUTORIZANTE_PARTICULAR
    return taller.autorizacion.registrar_decision(
        RegistrarDecisionDelCliente(id_cotizacion, lineas, nombre, rol)
    )


def autorizada(
    taller: Taller, flotilla: bool = False, lineas: tuple[int, ...] = (1, 2)
) -> tuple[str, str]:
    numero, id_cotizacion = cotizada(taller, flotilla)
    decidir(taller, id_cotizacion, lineas, flotilla)
    return numero, id_cotizacion


def asignada(taller: Taller, flotilla: bool = False, tecnico: str = TECNICO) -> str:
    """Orden «Autorizada» con los trabajos 1 y 2 asignados al técnico."""
    numero, _ = autorizada(taller, flotilla)
    taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1, 2), tecnico))
    return numero


def en_reparacion(taller: Taller, flotilla: bool = False) -> str:
    """El trabajo 1 queda «En Progreso» y el 2 «Pendiente»."""
    numero = asignada(taller, flotilla)
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 1, TECNICO))
    return numero


def en_espera(taller: Taller, iniciada: bool = False) -> str:
    """Tiene la solicitud 1 pendiente, del trabajo 2."""
    numero = en_reparacion(taller) if iniciada else asignada(taller)
    taller.refacciones.solicitar(SolicitarRefaccion(numero, 2, "Balatas", 2))
    return numero


def pausada(taller: Taller, iniciada: bool = False) -> str:
    numero = en_espera(taller, iniciada)
    taller.retiro.registrar_salida(RegistrarSalida(numero))
    taller.retiro.confirmar_firma(ConfirmarFirmaDeNota(numero))
    return numero


def con_adicional(taller: Taller) -> tuple[str, str]:
    """Orden «En Reparación» con una cotización adicional v.2 de dos trabajos, sin decisión."""
    numero = en_reparacion(taller)
    resultado = taller.cotizacion.generar_adicional(
        GenerarCotizacion(numero, trabajos("500.00", "700.00"))
    )
    return numero, resultado.id


def lista(taller: Taller, flotilla: bool = False) -> str:
    numero = en_reparacion(taller, flotilla)
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 2, TECNICO))
    taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 1, TECNICO))
    taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 2, TECNICO))
    return numero


def pagada(taller: Taller) -> str:
    numero = lista(taller)
    taller.caja.registrar_pago(RegistrarPago(numero, TOTAL_DE_DOS_TRABAJOS, FormaDePago.TARJETA))
    return numero


def por_cobrar(taller: Taller) -> str:
    numero = lista(taller, flotilla=True)
    taller.caja.registrar_cargo_a_credito(RegistrarCargoACredito(numero))
    return numero
