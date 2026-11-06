"""Ida y vuelta por la base: cada Aggregate se reconstruye exactamente como se guardó."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from application.comandos import (
    CancelarOrden,
    PresentarCotizacion,
    RegistrarEntrega,
    RegistrarLlegadaDeRefaccion,
    RegistrarRecontacto,
)
from domain.clientes.cliente import Cliente, TipoCliente
from domain.compartido.valores import VIN, Dinero, NumeroOrden, Placas
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.valores import RolDeAutorizante
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.valores import EstadoDeRecepcion, FormaDePago, NivelDeCombustible, Pago
from domain.vehiculos.vehiculo import Vehiculo
from infrastructure.base_de_datos.tablas import FechaUTC, ordenes
from tests.integration.apoyo_base import TallerEnBase
from tests.unit.application.escenarios import (
    AHORA,
    ASESOR,
    TECNICO,
    autorizada,
    cotizada,
    diagnosticada,
    en_espera,
    pagada,
    pausada,
    poner_hora,
    por_cobrar,
    recibida,
)


def _orden(taller: TallerEnBase, numero: str) -> OrdenDeServicio:
    with taller.uow() as uow:
        return uow.ordenes.obtener(NumeroOrden(numero))


def _cotizacion(taller: TallerEnBase, id_cotizacion: str) -> Cotizacion:
    with taller.uow() as uow:
        return uow.cotizaciones.obtener(id_cotizacion)


def _regreso_guardado(taller: TallerEnBase, numero: str) -> str | None:
    with taller.motor.connect() as conexion:
        return conexion.execute(
            select(ordenes.c.estado_antes_de_espera).where(ordenes.c.numero == numero)
        ).scalar_one()


def test_orden_recibida_conserva_todos_sus_datos(taller_en_base: TallerEnBase) -> None:
    numero = recibida(taller_en_base)

    orden = _orden(taller_en_base, numero)

    assert orden.numero == NumeroOrden("OS-0001")
    assert orden.placas == Placas("ABC001")
    assert orden.asesor == ASESOR
    assert orden.motivo_de_ingreso == "Ruido al frenar"
    assert orden.estado_de_recepcion == EstadoDeRecepcion(45000, NivelDeCombustible.MEDIO)
    assert orden.estado.value == "Recibida"
    assert orden.fecha_ingreso == AHORA
    assert orden.ultima_actualizacion == AHORA
    assert orden.fecha_ingreso_a_fila == AHORA
    assert orden.es_cliente_de_flotilla is False
    assert orden.nota_de_responsabilidad is None
    assert (orden.pago, orden.cargo_a_credito, orden.cancelacion) == (None, None, None)


def test_orden_importada_sin_estado_de_recepcion(taller_en_base: TallerEnBase) -> None:
    importada = OrdenDeServicio(
        NumeroOrden("AUT-O001"), "AUT-C001", False, Placas("PIAAUT001"), ASESOR, "Servicio", AHORA
    )
    with taller_en_base.uow() as uow:
        uow.clientes.agregar(Cliente("AUT-C001", "Propietario 01", TipoCliente.PARTICULAR))
        uow.vehiculos.agregar(
            Vehiculo(
                Placas("PIAAUT001"), VIN("AUT00000000000001"), "Ficticia", "R", 2020, "AUT-C001"
            )
        )
        uow.ordenes.agregar(importada)
        uow.confirmar()

    assert _orden(taller_en_base, "AUT-O001").estado_de_recepcion is None


def test_diagnostico_conserva_sus_datos(taller_en_base: TallerEnBase) -> None:
    numero = diagnosticada(taller_en_base)

    diagnostico = _orden(taller_en_base, numero).diagnostico

    assert diagnostico.fallas == "Balatas gastadas"
    assert diagnostico.recomendaciones == "Cambiar balatas"
    assert diagnostico.tecnico == TECNICO
    assert diagnostico.registrado_en == AHORA


def test_rn_16_pago_conserva_monto_exacto_y_forma(taller_en_base: TallerEnBase) -> None:
    numero = pagada(taller_en_base)

    assert _orden(taller_en_base, numero).pago == Pago(
        Dinero(Decimal("3000.00")), FormaDePago.TARJETA, AHORA
    )


def test_rn_17_credito_conserva_vencimiento(taller_en_base: TallerEnBase) -> None:
    numero = por_cobrar(taller_en_base)
    assert _orden(taller_en_base, numero).cargo_a_credito.fecha_vencimiento is None

    taller_en_base.entrega.entregar(RegistrarEntrega(numero))

    orden = _orden(taller_en_base, numero)
    assert orden.cargo_a_credito.monto == Dinero(Decimal("3000.00"))
    assert orden.cargo_a_credito.fecha_vencimiento == date(2026, 10, 20)
    assert orden.fecha_entrega == AHORA


def test_ca_024_nota_conserva_salida_y_firma(taller_en_base: TallerEnBase) -> None:
    numero = pausada(taller_en_base)

    nota = _orden(taller_en_base, numero).nota_de_responsabilidad

    assert (nota.fecha_salida, nota.firmada, nota.fecha_firma) == (AHORA, True, AHORA)


def test_ca_044_cancelacion_conserva_motivo_y_asesor(taller_en_base: TallerEnBase) -> None:
    numero = recibida(taller_en_base)
    taller_en_base.cancelacion.cancelar(CancelarOrden(numero, "El cliente desistió", ASESOR))

    orden = _orden(taller_en_base, numero)

    assert orden.cancelacion.motivo == "El cliente desistió"
    assert orden.cancelacion.asesor == ASESOR
    assert orden.cancelacion.registrada_en == AHORA
    assert orden.fecha_ingreso_a_fila is None


def test_ca_010_decision_se_reconstruye_con_su_autorizante(taller_en_base: TallerEnBase) -> None:
    numero, id_cotizacion = autorizada(taller_en_base, lineas=(1,))

    decision = _cotizacion(taller_en_base, id_cotizacion).decision
    trabajos = _orden(taller_en_base, numero).trabajos

    assert decision.id_cotizacion == id_cotizacion
    assert decision.autorizante.nombre == "Luis Peña"
    assert decision.autorizante.rol is RolDeAutorizante.CLIENTE
    assert [t.numero_linea for t in decision.autorizados] == [1]
    assert [t.numero_linea for t in decision.no_autorizados] == [2]
    assert decision.registrada_en == AHORA
    assert [(t.estado.value, t.id_cotizacion, t.numero_linea) for t in trabajos] == [
        ("Pendiente", id_cotizacion, 1),
        ("No Autorizado", id_cotizacion, 2),
    ]


def test_ca_040_recontactos_conservan_su_orden(taller_en_base: TallerEnBase) -> None:
    _, id_cotizacion = cotizada(taller_en_base)
    taller_en_base.cotizacion.presentar(PresentarCotizacion(id_cotizacion))
    for horas in (50, 100):
        poner_hora(taller_en_base.reloj, AHORA + timedelta(hours=horas))
        taller_en_base.cotizacion.registrar_recontacto(RegistrarRecontacto(id_cotizacion, ASESOR))

    cotizacion = _cotizacion(taller_en_base, id_cotizacion)

    assert [r.registrado_en for r in cotizacion.recontactos] == [
        AHORA + timedelta(hours=50),
        AHORA + timedelta(hours=100),
    ]
    assert cotizacion.ultimo_contacto == AHORA + timedelta(hours=100)
    assert cotizacion.fecha_presentacion == AHORA


def test_rn_23_importes_vuelven_como_decimal(taller_en_base: TallerEnBase) -> None:
    _, id_cotizacion = cotizada(taller_en_base, importes=("1234.56", "0.10"))

    cotizacion = _cotizacion(taller_en_base, id_cotizacion)

    montos = [linea.mano_de_obra.monto for linea in cotizacion.lineas]
    assert montos == [Decimal("1234.56"), Decimal("0.10")]
    assert all(isinstance(monto, Decimal) for monto in montos)
    assert cotizacion.total.monto == Decimal("1234.66")


def test_fechas_vuelven_en_utc_con_zona(taller_en_base: TallerEnBase) -> None:
    """La entrega se registra con la hora de Monterrey y se lee como el mismo instante en UTC."""
    numero = pagada(taller_en_base)
    taller_en_base.entrega.entregar(RegistrarEntrega(numero))

    orden = _orden(taller_en_base, numero)

    assert taller_en_base.reloj.ahora_en_el_taller().tzinfo == ZoneInfo("America/Monterrey")
    assert orden.fecha_entrega.tzinfo is UTC
    assert orden.fecha_entrega == AHORA
    assert orden.pago.registrado_en.utcoffset() == timedelta(0)


def test_fecha_sin_zona_se_rechaza(taller_en_base: TallerEnBase) -> None:
    with pytest.raises(ValueError, match="zona horaria"):
        FechaUTC().process_bind_param(datetime(2026, 10, 5, 12), taller_en_base.motor.dialect)


def test_estado_antes_de_espera_se_guarda_en_su_columna(taller_en_base: TallerEnBase) -> None:
    sin_iniciar = en_espera(taller_en_base)
    iniciada = en_espera(taller_en_base, iniciada=True)

    assert _regreso_guardado(taller_en_base, sin_iniciar) == "Autorizada"
    assert _regreso_guardado(taller_en_base, iniciada) == "En Reparación"
    assert _orden(taller_en_base, iniciada).estado_antes_de_espera.value == "En Reparación"

    taller_en_base.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(sin_iniciar, 1))

    assert _regreso_guardado(taller_en_base, sin_iniciar) is None


def test_reconstruir_no_genera_eventos(taller_en_base: TallerEnBase) -> None:
    numero, id_cotizacion = autorizada(taller_en_base)

    assert _orden(taller_en_base, numero).extraer_eventos() == []
    assert _cotizacion(taller_en_base, id_cotizacion).extraer_eventos() == []


def test_flotilla_conserva_su_responsable(taller_en_base: TallerEnBase) -> None:
    numero = recibida(taller_en_base, flotilla=True)

    with taller_en_base.uow() as uow:
        cliente = uow.clientes.obtener(uow.ordenes.obtener(NumeroOrden(numero)).id_cliente)

    assert cliente.tipo is TipoCliente.FLOTILLA
    assert cliente.empresa == "Transportes Norte"
    assert (
        cliente.responsable.nombre,
        cliente.responsable.telefono,
        cliente.responsable.correo,
    ) == ("Ana Torres", "81-1111", "ana@norte.test")
    assert _orden(taller_en_base, numero).es_cliente_de_flotilla is True
