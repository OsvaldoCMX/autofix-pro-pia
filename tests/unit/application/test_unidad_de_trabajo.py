"""Unidad de Trabajo y repositorios en memoria (ADR-002, ADR-016)."""
from __future__ import annotations

from collections.abc import Callable

import pytest

from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.clientes.cliente import Cliente, ResponsableDeFlotilla, TipoCliente
from domain.compartido.errores import (
    ClienteNoEncontrado,
    CotizacionNoEncontrada,
    EmpleadoNoEncontrado,
    ErrorDeDominio,
    OrdenNoEncontrada,
    ValorInvalido,
    VehiculoNoEncontrado,
)
from domain.compartido.valores import VIN, Dinero, NumeroOrden, Placas
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.linea_de_cotizacion import LineaDeCotizacion
from domain.cotizaciones.valores import TipoCotizacion, VersionCotizacion
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.valores import EstadoDeRecepcion, NivelDeCombustible
from domain.vehiculos.vehiculo import Vehiculo
from tests.unit.application.escenarios import AHORA, ASESOR, TECNICO, Taller

VIN_1 = "1HGCM82633A004352"
VIN_2 = "2HGCM82633A004353"
NUMERO = NumeroOrden("OS-0001")


def _orden() -> OrdenDeServicio:
    return OrdenDeServicio.registrar(
        NUMERO,
        "CLI-0001",
        False,
        Placas("ABC123"),
        ASESOR,
        "Ruido al frenar",
        EstadoDeRecepcion(1000, NivelDeCombustible.MEDIO),
        AHORA,
    )


def _cotizacion(id_cotizacion: str, tipo: TipoCotizacion, version: int) -> Cotizacion:
    linea = LineaDeCotizacion(1, "Afinación", Dinero("100"))
    return Cotizacion.generar(
        id_cotizacion, NUMERO, tipo, VersionCotizacion(version), [linea], AHORA
    )


def _vehiculo(placas: str, vin: str) -> Vehiculo:
    return Vehiculo(Placas(placas), VIN(vin), "Nissan", "Versa", 2020, "CLI-1")


def test_confirmar_guarda_los_cambios() -> None:
    taller = Taller()

    with taller.uow() as uow:
        uow.ordenes.agregar(_orden())
        uow.confirmar()

    assert "OS-0001" in taller.datos.ordenes


def test_sin_confirmar_no_guarda() -> None:
    taller = Taller()

    with taller.uow() as uow:
        uow.ordenes.agregar(_orden())

    assert taller.datos.ordenes == {}


def test_rn_22_error_revierte_los_dos_aggregates() -> None:
    taller = Taller()
    with taller.uow() as uow:
        uow.ordenes.agregar(_orden())
        uow.confirmar()

    with pytest.raises(ValorInvalido), taller.uow() as uow:
        uow.ordenes.obtener(NUMERO).asignar_tecnico_para_diagnostico(TECNICO, AHORA)
        uow.clientes.agregar(Cliente("CLI-0001", "Luis", TipoCliente.PARTICULAR))
        raise ValorInvalido("Falla a la mitad de la operación.")

    assert taller.datos.clientes == {}
    assert taller.datos.ordenes["OS-0001"].tecnico_de_diagnostico is None


def test_folios_se_revierten_con_la_transaccion() -> None:
    taller = Taller()

    with taller.uow() as uow:
        assert str(uow.ordenes.siguiente_numero()) == "OS-0001"
        assert uow.cotizaciones.siguiente_id() == "COT-0001"
        assert uow.clientes.siguiente_id() == "CLI-0001"

    with taller.uow() as uow:
        assert str(uow.ordenes.siguiente_numero()) == "OS-0001"
        assert uow.cotizaciones.siguiente_id() == "COT-0001"
        assert uow.clientes.siguiente_id() == "CLI-0001"
        uow.confirmar()

    with taller.uow() as uow:
        assert str(uow.ordenes.siguiente_numero()) == "OS-0002"
        assert uow.cotizaciones.siguiente_id() == "COT-0002"
        assert uow.clientes.siguiente_id() == "CLI-0002"


def test_bitacora_guarda_cada_evento() -> None:
    taller = Taller()

    with taller.uow() as uow:
        uow.ordenes.agregar(_orden())
        uow.confirmar()

    registro = taller.datos.bitacora[0]
    assert (registro.tipo, registro.agregado, registro.id_agregado) == (
        "OrdenRecibida",
        "Orden",
        "OS-0001",
    )


def test_bitacora_no_guarda_nada_si_no_se_confirma() -> None:
    taller = Taller()

    with taller.uow() as uow:
        uow.ordenes.agregar(_orden())

    assert taller.datos.bitacora == []


def test_eventos_disponibles_solo_al_confirmar() -> None:
    uow = Taller().uow()

    with uow:
        uow.ordenes.agregar(_orden())
        assert uow.eventos_confirmados() == []
        uow.confirmar()

    assert [type(e).__name__ for e in uow.eventos_confirmados()] == ["OrdenRecibida"]


def test_mismo_aggregate_visto_dos_veces_no_repite_eventos() -> None:
    uow = Taller().uow()

    with uow:
        orden = _orden()
        uow.ordenes.agregar(orden)
        uow.ordenes.guardar(orden)
        uow.confirmar()

    assert len(uow.eventos_confirmados()) == 1


@pytest.mark.parametrize(
    ("consulta", "error"),
    [
        (lambda uow: uow.ordenes.obtener(NumeroOrden("OS-9")), OrdenNoEncontrada),
        (lambda uow: uow.cotizaciones.obtener("COT-9"), CotizacionNoEncontrada),
        (lambda uow: uow.clientes.obtener("CLI-9"), ClienteNoEncontrado),
        (lambda uow: uow.vehiculos.por_placas(Placas("XXX")), VehiculoNoEncontrado),
        (lambda uow: uow.empleados.obtener("EMP-9"), EmpleadoNoEncontrado),
    ],
)
def test_obtener_lo_que_no_existe_lanza_el_error_del_negocio(
    consulta: Callable[[UnidadDeTrabajo], object], error: type[ErrorDeDominio]
) -> None:
    with pytest.raises(error), Taller().uow() as uow:
        consulta(uow)


def test_no_se_agrega_dos_veces_el_mismo_identificador() -> None:
    with Taller().uow() as uow:
        uow.ordenes.agregar(_orden())
        uow.cotizaciones.agregar(_cotizacion("COT-1", TipoCotizacion.INICIAL, 1))
        uow.clientes.agregar(Cliente("CLI-1", "Luis", TipoCliente.PARTICULAR))
        uow.vehiculos.agregar(_vehiculo("ABC1", VIN_1))

        with pytest.raises(ValorInvalido, match="orden"):
            uow.ordenes.agregar(_orden())
        with pytest.raises(ValorInvalido, match="cotización"):
            uow.cotizaciones.agregar(_cotizacion("COT-1", TipoCotizacion.INICIAL, 1))
        with pytest.raises(ValorInvalido, match="cliente"):
            uow.clientes.agregar(Cliente("CLI-1", "Otro", TipoCliente.PARTICULAR))
        with pytest.raises(ValorInvalido, match="placas"):
            uow.vehiculos.agregar(_vehiculo("ABC1", VIN_2))
        with pytest.raises(ValorInvalido, match="VIN"):
            uow.vehiculos.agregar(_vehiculo("ABC2", VIN_1))


def test_guardar_vehiculo_rechaza_el_vin_de_otro_vehiculo() -> None:
    with Taller().uow() as uow:
        uow.vehiculos.agregar(_vehiculo("ABC1", VIN_1))
        segundo = _vehiculo("ABC2", VIN_2)
        uow.vehiculos.agregar(segundo)
        segundo.actualizar_datos(VIN(VIN_1), "Nissan", "Versa", 2020)

        with pytest.raises(ValorInvalido, match="VIN"):
            uow.vehiculos.guardar(segundo)


def test_rn_24_versiones_de_la_orden_en_orden() -> None:
    taller = Taller()
    with taller.uow() as uow:
        assert uow.cotizaciones.siguiente_version(NUMERO) == VersionCotizacion(1)
        uow.cotizaciones.agregar(_cotizacion("COT-2", TipoCotizacion.ADICIONAL, 2))
        uow.cotizaciones.agregar(_cotizacion("COT-1", TipoCotizacion.INICIAL, 1))

        assert uow.cotizaciones.siguiente_version(NUMERO) == VersionCotizacion(3)
        assert [c.id for c in uow.cotizaciones.de_la_orden(NUMERO)] == ["COT-1", "COT-2"]


def test_buscar_flotilla_no_distingue_mayusculas_ni_espacios() -> None:
    flotilla = Cliente(
        "CLI-1",
        "Norte SA",
        TipoCliente.FLOTILLA,
        empresa="Transportes Norte",
        responsable=ResponsableDeFlotilla("Ana", "81-1", "ana@norte.test"),
    )
    with Taller().uow() as uow:
        uow.clientes.agregar(flotilla)
        uow.clientes.agregar(Cliente("CLI-2", "Transportes Norte", TipoCliente.PARTICULAR))

        assert uow.clientes.buscar_flotilla("  transportes NORTE ") is flotilla
        assert uow.clientes.buscar_flotilla("Otra") is None
