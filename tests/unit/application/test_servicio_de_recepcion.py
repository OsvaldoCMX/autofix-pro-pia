"""ServicioDeRecepcion (US-001, US-002, US-003, US-016)."""
from __future__ import annotations

import pytest

from application.comandos import DatosDeVehiculo, RegistrarCliente, RegistrarOrden
from domain.clientes.cliente import TipoCliente
from domain.compartido.errores import ClienteNoEncontrado, ValorInvalido
from domain.ordenes.eventos import OrdenRecibida
from domain.ordenes.valores import EstadoDeRecepcion, NivelDeCombustible
from tests.unit.application.escenarios import AHORA, ASESOR, FLOTILLA, PARTICULAR, Taller, recibida

VIN_1 = "1HGCM82633A004352"
VEHICULO = DatosDeVehiculo(VIN_1, "Nissan", "Versa", 2020)


def _comando(**cambios: object) -> RegistrarOrden:
    datos: dict[str, object] = {
        "asesor": ASESOR,
        "placas": "ABC-123",
        "motivo_de_ingreso": "Ruido al frenar",
        "kilometraje": 45000,
        "nivel_de_combustible": NivelDeCombustible.MEDIO,
        "vehiculo": VEHICULO,
        "cliente": PARTICULAR,
    }
    return RegistrarOrden(**{**datos, **cambios})  # type: ignore[arg-type]


def test_ca_001_registra_cliente_vehiculo_y_orden_recibida(taller: Taller) -> None:
    resultado = taller.recepcion.registrar_orden(_comando())

    assert resultado.numero_orden == "OS-0001"
    assert resultado.estado == "Recibida"
    assert resultado.id_cliente == "CLI-0001"
    assert resultado.placas == "ABC123"
    assert resultado.fecha_ingreso == AHORA
    assert taller.datos.clientes["CLI-0001"].nombre == "Luis Peña"
    assert taller.datos.vehiculos["ABC123"].marca == "Nissan"
    assert taller.datos.ordenes["OS-0001"].asesor == ASESOR


def test_ca_001_folios_consecutivos(taller: Taller) -> None:
    assert recibida(taller) == "OS-0001"
    assert recibida(taller) == "OS-0002"


def test_ca_001_publica_orden_recibida_despues_de_confirmar(taller: Taller) -> None:
    taller.recepcion.registrar_orden(_comando())

    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [OrdenRecibida]
    assert "OS-0001" in taller.datos.ordenes


def test_ca_002_guarda_kilometraje_y_combustible(taller: Taller) -> None:
    taller.recepcion.registrar_orden(_comando(nivel_de_combustible=NivelDeCombustible.LLENO))

    assert taller.datos.ordenes["OS-0001"].estado_de_recepcion == EstadoDeRecepcion(
        45000, NivelDeCombustible.LLENO
    )


def test_ca_003_reutiliza_vehiculo_y_cliente_por_placas(taller: Taller) -> None:
    taller.recepcion.registrar_orden(_comando())

    segunda = taller.recepcion.registrar_orden(_comando(vehiculo=None, cliente=None))

    assert segunda.numero_orden == "OS-0002"
    assert segunda.id_cliente == "CLI-0001"
    assert len(taller.datos.clientes) == 1
    assert len(taller.datos.vehiculos) == 1


def test_ca_003_actualiza_cliente_y_vehiculo(taller: Taller) -> None:
    taller.recepcion.registrar_orden(_comando())

    taller.recepcion.registrar_orden(
        _comando(
            vehiculo=DatosDeVehiculo(VIN_1, "Nissan", "Sentra", 2021),
            cliente=RegistrarCliente("Luis Peña Ruiz", telefono="81-9", correo="nuevo@correo.test"),
        )
    )

    cliente = taller.datos.clientes["CLI-0001"]
    vehiculo = taller.datos.vehiculos["ABC123"]
    assert (cliente.nombre, cliente.telefono) == ("Luis Peña Ruiz", "81-9")
    assert (vehiculo.modelo, vehiculo.anio) == ("Sentra", 2021)


def test_ca_003_placas_de_otro_cliente_es_invalido(taller: Taller) -> None:
    taller.recepcion.registrar_orden(_comando())

    with pytest.raises(ValorInvalido, match="otro cliente"):
        taller.recepcion.registrar_orden(_comando(id_cliente="CLI-9999"))

    assert len(taller.datos.ordenes) == 1


def test_ca_004_placas_nuevas_crean_el_registro(taller: Taller) -> None:
    taller.recepcion.registrar_orden(_comando())

    segunda = taller.recepcion.registrar_orden(
        _comando(
            placas="XYZ-999",
            vehiculo=DatosDeVehiculo("2HGCM82633A004353", "Toyota", "Yaris", 2019),
            cliente=None,
            id_cliente="CLI-0001",
        )
    )

    assert segunda.id_cliente == "CLI-0001"
    assert taller.datos.vehiculos["XYZ999"].marca == "Toyota"


def test_ca_004_cliente_existente_tambien_se_actualiza(taller: Taller) -> None:
    taller.recepcion.registrar_orden(_comando())

    taller.recepcion.registrar_orden(
        _comando(
            placas="XYZ-999",
            vehiculo=DatosDeVehiculo("2HGCM82633A004353", "Toyota", "Yaris", 2019),
            cliente=RegistrarCliente("Luis P.", telefono="81-7"),
            id_cliente="CLI-0001",
        )
    )

    assert taller.datos.clientes["CLI-0001"].nombre == "Luis P."


def test_ca_004_placas_nuevas_sin_datos_es_invalido(taller: Taller) -> None:
    with pytest.raises(ValorInvalido, match="datos del vehículo"):
        taller.recepcion.registrar_orden(_comando(vehiculo=None))

    assert taller.datos.ordenes == {}


def test_ca_004_placas_nuevas_sin_cliente_es_invalido(taller: Taller) -> None:
    with pytest.raises(ValorInvalido, match="cliente"):
        taller.recepcion.registrar_orden(_comando(cliente=None))


def test_ca_004_cliente_que_no_existe_lanza_cliente_no_encontrado(taller: Taller) -> None:
    with pytest.raises(ClienteNoEncontrado):
        taller.recepcion.registrar_orden(_comando(cliente=None, id_cliente="CLI-9999"))


def test_ca_028_registra_flotilla_con_responsable(taller: Taller) -> None:
    resultado = taller.recepcion.registrar_cliente(FLOTILLA)

    assert resultado.id_cliente == "CLI-0001"
    assert resultado.tipo == "Flotilla"
    assert resultado.empresa == "Transportes Norte"
    assert resultado.responsable_nombre == "Ana Torres"


def test_ca_028_registra_cliente_particular_sin_responsable(taller: Taller) -> None:
    resultado = taller.recepcion.registrar_cliente(PARTICULAR)

    assert (resultado.tipo, resultado.empresa, resultado.responsable_nombre) == (
        "Particular",
        None,
        None,
    )


def test_ca_028_no_duplica_flotilla_existente(taller: Taller) -> None:
    primera = taller.recepcion.registrar_cliente(FLOTILLA)

    segunda = taller.recepcion.registrar_cliente(FLOTILLA)

    assert segunda == primera
    assert len(taller.datos.clientes) == 1


def test_ca_028_flotilla_sin_responsable_es_invalida(taller: Taller) -> None:
    with pytest.raises(ValorInvalido, match="Responsable de Flotilla"):
        taller.recepcion.registrar_cliente(
            RegistrarCliente("Norte SA", TipoCliente.FLOTILLA, empresa="Norte")
        )

    assert taller.datos.clientes == {}


def test_rn_23_kilometraje_negativo_no_crea_nada(taller: Taller) -> None:
    with pytest.raises(ValorInvalido, match="kilometraje"):
        taller.recepcion.registrar_orden(_comando(kilometraje=-1))

    assert taller.datos.ordenes == {}
    assert taller.datos.clientes == {}
    assert taller.datos.vehiculos == {}
    taller.publicador.publicar.assert_not_called()


def test_rn_23_error_al_registrar_no_consume_folios(taller: Taller) -> None:
    with pytest.raises(ValorInvalido):
        taller.recepcion.registrar_orden(_comando(motivo_de_ingreso="  "))

    assert taller.recepcion.registrar_orden(_comando()).numero_orden == "OS-0001"
