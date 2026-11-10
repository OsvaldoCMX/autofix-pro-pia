"""Contrato de los Repositories: las mismas pruebas con memoria y con base de datos (ADR-004)."""
from __future__ import annotations

from collections.abc import Callable

import pytest

from application.comandos import CancelarOrden
from application.puertos import AlertaInterna
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.clientes.cliente import Cliente, ResponsableDeFlotilla, TipoCliente
from domain.compartido.errores import (
    ClienteNoEncontrado,
    CotizacionNoEncontrada,
    EmpleadoNoEncontrado,
    ErrorDeDominio,
    OrdenNoEncontrada,
    ValorInvalido,
    VehiculoConOrdenAbierta,
    VehiculoNoEncontrado,
)
from domain.compartido.valores import VIN, Dinero, NumeroOrden, Placas
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.linea_de_cotizacion import LineaDeCotizacion
from domain.cotizaciones.valores import TipoCotizacion, VersionCotizacion
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.valores import EstadoDeRecepcion, NivelDeCombustible
from domain.servicios.verificador_de_orden_unica import vehiculo_con_orden_abierta
from domain.vehiculos.vehiculo import Vehiculo
from tests.integration.apoyo_base import TallerEnBase
from tests.unit.application.escenarios import (
    AHORA,
    ASESOR,
    TECNICO,
    Taller,
    en_diagnostico,
    recibida,
)

ID_CLIENTE = "CLI-1"
NUMERO = NumeroOrden("OS-0001")
PLACAS = Placas("ABC1")
VIN_1 = "1HGCM82633A004352"
VIN_2 = "2HGCM82633A004353"


def _cliente(id_cliente: str = ID_CLIENTE) -> Cliente:
    return Cliente(id_cliente, "Luis", TipoCliente.PARTICULAR)


def _vehiculo(placas: str = "ABC1", vin: str = VIN_1) -> Vehiculo:
    return Vehiculo(Placas(placas), VIN(vin), "Nissan", "Versa", 2020, ID_CLIENTE)


def _orden() -> OrdenDeServicio:
    return OrdenDeServicio.registrar(
        NUMERO,
        ID_CLIENTE,
        False,
        PLACAS,
        ASESOR,
        "Ruido al frenar",
        EstadoDeRecepcion(1000, NivelDeCombustible.MEDIO),
        AHORA,
    )


def _cotizacion(id_cotizacion: str, tipo: TipoCotizacion, version: int) -> Cotizacion:
    return Cotizacion.generar(
        id_cotizacion,
        NUMERO,
        tipo,
        VersionCotizacion(version),
        [LineaDeCotizacion(1, "Afinación", Dinero("100"))],
        AHORA,
    )


def _con_orden(uow: UnidadDeTrabajo) -> OrdenDeServicio:
    """Registra lo que la orden necesita, en el orden que exigen las llaves foráneas."""
    uow.clientes.agregar(_cliente())
    uow.vehiculos.agregar(_vehiculo())
    orden = _orden()
    uow.ordenes.agregar(orden)
    return orden


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
    taller: Taller,
    consulta: Callable[[UnidadDeTrabajo], object],
    error: type[ErrorDeDominio],
) -> None:
    with pytest.raises(error), taller.uow() as uow:
        consulta(uow)


def test_obtener_empleado_devuelve_su_rol(taller: Taller) -> None:
    with taller.uow() as uow:
        empleado = uow.empleados.obtener(TECNICO)

    assert empleado.nombre == "Carlos Ruiz"
    assert empleado.tiene_rol(RolDeEmpleado.TECNICO)


def test_no_se_agrega_dos_veces_el_mismo_identificador(taller: Taller) -> None:
    with taller.uow() as uow:
        _con_orden(uow)
        uow.cotizaciones.agregar(_cotizacion("COT-1", TipoCotizacion.INICIAL, 1))

        with pytest.raises(ValorInvalido, match="orden"):
            uow.ordenes.agregar(_orden())
        with pytest.raises(ValorInvalido, match="cotización"):
            uow.cotizaciones.agregar(_cotizacion("COT-1", TipoCotizacion.INICIAL, 1))
        with pytest.raises(ValorInvalido, match="cliente"):
            uow.clientes.agregar(_cliente())
        with pytest.raises(ValorInvalido, match="placas"):
            uow.vehiculos.agregar(_vehiculo(vin=VIN_2))
        with pytest.raises(ValorInvalido, match="VIN"):
            uow.vehiculos.agregar(_vehiculo("ABC2", VIN_1))


def test_guardar_vehiculo_rechaza_el_vin_de_otro(taller: Taller) -> None:
    with taller.uow() as uow:
        uow.clientes.agregar(_cliente())
        uow.vehiculos.agregar(_vehiculo())
        segundo = _vehiculo("ABC2", VIN_2)
        uow.vehiculos.agregar(segundo)
        segundo.actualizar_datos(VIN(VIN_1), "Nissan", "Versa", 2020)

        with pytest.raises(ValorInvalido, match="VIN"):
            uow.vehiculos.guardar(segundo)


def test_guardar_crea_lo_que_aun_no_existe(taller: Taller) -> None:
    with taller.uow() as uow:
        uow.clientes.guardar(_cliente())
        uow.vehiculos.guardar(_vehiculo())
        uow.ordenes.guardar(_orden())
        uow.cotizaciones.guardar(_cotizacion("COT-1", TipoCotizacion.INICIAL, 1))
        uow.confirmar()

    with taller.uow() as uow:
        assert uow.clientes.obtener(ID_CLIENTE).nombre == "Luis"
        assert uow.vehiculos.por_placas(PLACAS).marca == "Nissan"
        assert uow.ordenes.obtener(NUMERO).motivo_de_ingreso == "Ruido al frenar"
        assert uow.cotizaciones.obtener("COT-1").total == Dinero("100")


def test_guardar_actualiza_lo_que_ya_existe(taller: Taller) -> None:
    with taller.uow() as uow:
        uow.clientes.agregar(_cliente())
        uow.vehiculos.agregar(_vehiculo())
        uow.confirmar()

    with taller.uow() as uow:
        cliente = uow.clientes.obtener(ID_CLIENTE)
        cliente.actualizar_contacto("Luis Peña", "81-2222", "luis@correo.test")
        uow.clientes.guardar(cliente)
        vehiculo = uow.vehiculos.por_placas(PLACAS)
        vehiculo.actualizar_datos(VIN(VIN_2), "Toyota", "Yaris", 2021)
        uow.vehiculos.guardar(vehiculo)
        uow.confirmar()

    with taller.uow() as uow:
        cliente = uow.clientes.obtener(ID_CLIENTE)
        vehiculo = uow.vehiculos.por_placas(PLACAS)

    assert (cliente.nombre, cliente.telefono, cliente.correo) == (
        "Luis Peña",
        "81-2222",
        "luis@correo.test",
    )
    assert (str(vehiculo.vin), vehiculo.marca, vehiculo.modelo, vehiculo.anio) == (
        VIN_2,
        "Toyota",
        "Yaris",
        2021,
    )


def test_folios_consecutivos_con_formato(taller: Taller) -> None:
    with taller.uow() as uow:
        assert [str(uow.ordenes.siguiente_numero()) for _ in range(2)] == ["OS-0001", "OS-0002"]
        assert [uow.cotizaciones.siguiente_id() for _ in range(2)] == ["COT-0001", "COT-0002"]
        assert [uow.clientes.siguiente_id() for _ in range(2)] == ["CLI-0001", "CLI-0002"]


def test_folios_se_revierten_con_la_transaccion(taller: Taller) -> None:
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


def test_rn_24_versiones_consecutivas_por_orden(taller: Taller) -> None:
    with taller.uow() as uow:
        _con_orden(uow)
        assert uow.cotizaciones.siguiente_version(NUMERO) == VersionCotizacion(1)
        uow.cotizaciones.agregar(_cotizacion("COT-1", TipoCotizacion.INICIAL, 1))
        assert uow.cotizaciones.siguiente_version(NUMERO) == VersionCotizacion(2)
        uow.cotizaciones.agregar(_cotizacion("COT-2", TipoCotizacion.ADICIONAL, 2))
        assert uow.cotizaciones.siguiente_version(NUMERO) == VersionCotizacion(3)


def test_rn_24_de_la_orden_devuelve_en_orden_de_version(taller: Taller) -> None:
    with taller.uow() as uow:
        _con_orden(uow)
        uow.cotizaciones.agregar(_cotizacion("COT-2", TipoCotizacion.ADICIONAL, 2))
        uow.cotizaciones.agregar(_cotizacion("COT-1", TipoCotizacion.INICIAL, 1))
        uow.confirmar()

    with taller.uow() as uow:
        cotizaciones = uow.cotizaciones.de_la_orden(NUMERO)

    assert [c.id for c in cotizaciones] == ["COT-1", "COT-2"]


def test_ca_028_buscar_flotilla_no_distingue_mayusculas_acentuadas(taller: Taller) -> None:
    """También con acentos, donde `lower()` de SQLite daría un resultado distinto."""
    flotilla = Cliente(
        "CLI-1",
        "Águila SA",
        TipoCliente.FLOTILLA,
        empresa="Transportes Águila",
        responsable=ResponsableDeFlotilla("Ana", "81-1", "ana@aguila.test"),
    )
    with taller.uow() as uow:
        uow.clientes.agregar(flotilla)
        uow.clientes.agregar(Cliente("CLI-2", "Transportes Águila", TipoCliente.PARTICULAR))
        uow.confirmar()

    with taller.uow() as uow:
        encontrada = uow.clientes.buscar_flotilla("  TRANSPORTES águila ")
        otra = uow.clientes.buscar_flotilla("Otra")

    assert encontrada.id_cliente == "CLI-1"
    assert encontrada.responsable.nombre == "Ana"
    assert otra is None


def test_obtener_dos_veces_devuelve_el_mismo_objeto(taller: Taller) -> None:
    with taller.uow() as uow:
        _con_orden(uow)
        uow.cotizaciones.agregar(_cotizacion("COT-1", TipoCotizacion.INICIAL, 1))
        uow.confirmar()

    with taller.uow() as uow:
        assert uow.ordenes.obtener(NUMERO) is uow.ordenes.obtener(NUMERO)
        assert uow.cotizaciones.obtener("COT-1") is uow.cotizaciones.obtener("COT-1")
        assert uow.cotizaciones.obtener("COT-1") is uow.cotizaciones.de_la_orden(NUMERO)[0]
        assert uow.clientes.obtener(ID_CLIENTE) is uow.clientes.obtener(ID_CLIENTE)
        assert uow.vehiculos.por_placas(PLACAS) is uow.vehiculos.por_placas(PLACAS)


def test_existe_clave_de_alerta(taller: Taller) -> None:
    alerta = AlertaInterna(
        "RefaccionRetrasada", "Avise al cliente", AHORA, destinatario=ASESOR, clave="refaccion:1:1"
    )
    with taller.uow() as uow:
        assert uow.alertas.existe_clave("refaccion:1:1") is False
        uow.alertas.agregar(alerta)
        assert uow.alertas.existe_clave("refaccion:1:1") is True
        assert uow.alertas.existe_clave("otra") is False



def test_catalogo_devuelve_los_servicios_inhabilitados_de_la_orden(taller: Taller) -> None:
    numero = en_diagnostico(taller)
    taller.registrar_servicios_de_orden(numero, ("AUT-P001",), ("AUT-P011", "AUT-P002"))

    with taller.uow() as uow:
        assert uow.catalogo.servicios_inhabilitados_de_la_orden(NumeroOrden(numero)) == (
            "AUT-P002",
            "AUT-P011",
        )
        assert uow.catalogo.servicios_inhabilitados_de_la_orden(NumeroOrden("OS-9999")) == ()


def _placas_de(taller: Taller, numero: str) -> Placas:
    with taller.uow() as uow:
        return uow.ordenes.obtener(NumeroOrden(numero)).placas


def test_rn_27_abierta_del_vehiculo_encuentra_la_orden_abierta(taller: Taller) -> None:
    numero = recibida(taller)
    placas = _placas_de(taller, numero)

    with taller.uow() as uow:
        abierta = uow.ordenes.abierta_del_vehiculo(placas)
        sin_ordenes = uow.ordenes.abierta_del_vehiculo(Placas("ZZZ999"))

    assert abierta is not None and str(abierta.numero) == numero
    assert sin_ordenes is None


def test_rn_27_una_orden_cancelada_ya_no_esta_abierta(taller: Taller) -> None:
    numero = recibida(taller)
    taller.cancelacion.cancelar(CancelarOrden(numero, "El cliente desistió", ASESOR))

    with taller.uow() as uow:
        assert uow.ordenes.abierta_del_vehiculo(_placas_de(taller, numero)) is None


def test_rn_27_si_la_base_rechaza_la_segunda_orden_lanza_el_mismo_error(
    taller_en_base: TallerEnBase,
) -> None:
    """Dos registros al mismo tiempo: el segundo se salta la revisión y lo detiene el índice."""
    numero = recibida(taller_en_base)

    with taller_en_base.uow() as uow:
        primera = uow.ordenes.obtener(NumeroOrden(numero))
        repetida = OrdenDeServicio.registrar(
            uow.ordenes.siguiente_numero(),
            primera.id_cliente,
            False,
            primera.placas,
            ASESOR,
            "Doble clic",
            EstadoDeRecepcion(1000, NivelDeCombustible.MEDIO),
            AHORA,
        )
        with pytest.raises(VehiculoConOrdenAbierta) as error:
            uow.ordenes.agregar(repetida)
        esperado = str(vehiculo_con_orden_abierta(primera.placas, primera))

    assert str(error.value) == esperado
    with taller_en_base.uow() as uow:
        assert uow.ordenes.abierta_del_vehiculo(primera.placas) is not None
