"""ServicioDeRefacciones (US-010, US-011, US-012)."""
from __future__ import annotations

import pytest

from application.comandos import (
    CompletarTrabajo,
    IniciarTrabajo,
    RegistrarAvisoAlCliente,
    RegistrarLlegadaDeRefaccion,
    SolicitarRefaccion,
)
from domain.compartido.errores import (
    SolicitudNoEncontrada,
    SolicitudNoPermitida,
    TrabajoNoAutorizado,
    ValorInvalido,
)
from domain.ordenes.eventos import (
    ClienteAvisadoDelRetraso,
    RefaccionDisponible,
    SolicitudDeCompraCreada,
)
from tests.unit.application.escenarios import (
    AHORA,
    TECNICO,
    Taller,
    asignada,
    autorizada,
    en_espera,
    en_reparacion,
)


def test_ca_019_crea_solicitud_y_pasa_a_espera(taller: Taller) -> None:
    numero = asignada(taller)

    resultado = taller.refacciones.solicitar(SolicitarRefaccion(numero, 1, "Balatas", 2))

    assert resultado.estado_solicitud == "Solicitada"
    assert resultado.estado_orden == "En Espera de Refacción"
    solicitud = taller.datos.ordenes[numero].solicitudes[0]
    assert (solicitud.refaccion, solicitud.cantidad) == ("Balatas", 2)
    assert solicitud.fecha_solicitud == AHORA
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [SolicitudDeCompraCreada]


def test_ca_020_trabajo_no_autorizado_se_rechaza(taller: Taller) -> None:
    numero, _ = autorizada(taller, lineas=(1,))

    with pytest.raises(TrabajoNoAutorizado, match="no fue autorizado"):
        taller.refacciones.solicitar(SolicitarRefaccion(numero, 2, "Balatas", 1))

    assert taller.datos.ordenes[numero].solicitudes == ()


def test_rn_09_trabajo_completado_se_rechaza(taller: Taller) -> None:
    numero = en_reparacion(taller)
    taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 1, TECNICO))

    with pytest.raises(SolicitudNoPermitida):
        taller.refacciones.solicitar(SolicitarRefaccion(numero, 1, "Balatas", 1))


def test_rn_23_cantidad_cero_es_invalida(taller: Taller) -> None:
    numero = asignada(taller)

    with pytest.raises(ValorInvalido, match="cantidad"):
        taller.refacciones.solicitar(SolicitarRefaccion(numero, 1, "Balatas", 0))

    assert taller.datos.ordenes[numero].estado.value == "Autorizada"


def test_ca_022_ultima_llegada_regresa_el_estado(taller: Taller) -> None:
    numero = en_espera(taller)

    resultado = taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))

    assert resultado.estado_solicitud == "Disponible"
    assert resultado.estado_orden == "Autorizada"
    assert taller.datos.ordenes[numero].solicitudes[0].fecha_llegada == AHORA
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [RefaccionDisponible]


def test_ca_022_con_un_trabajo_iniciado_regresa_a_en_reparacion(taller: Taller) -> None:
    numero = en_espera(taller)
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 1, TECNICO))

    resultado = taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))

    assert resultado.estado_orden == "En Reparación"


def test_rn_10_sigue_en_espera_con_otra_pendiente(taller: Taller) -> None:
    numero = en_espera(taller)
    taller.refacciones.solicitar(SolicitarRefaccion(numero, 1, "Filtro", 1))

    resultado = taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 1))

    assert resultado.estado_orden == "En Espera de Refacción"


def test_ca_023_registra_aviso_al_cliente(taller: Taller) -> None:
    numero = en_espera(taller)

    resultado = taller.refacciones.registrar_aviso_al_cliente(RegistrarAvisoAlCliente(numero, 1))

    assert resultado.estado_solicitud == "Solicitada"
    assert taller.datos.ordenes[numero].solicitudes[0].fecha_aviso_al_cliente == AHORA
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [ClienteAvisadoDelRetraso]


def test_ca_023_segundo_aviso_se_rechaza(taller: Taller) -> None:
    numero = en_espera(taller)
    taller.refacciones.registrar_aviso_al_cliente(RegistrarAvisoAlCliente(numero, 1))

    with pytest.raises(SolicitudNoPermitida):
        taller.refacciones.registrar_aviso_al_cliente(RegistrarAvisoAlCliente(numero, 1))


def test_solicitud_inexistente(taller: Taller) -> None:
    numero = en_espera(taller)

    with pytest.raises(SolicitudNoEncontrada):
        taller.refacciones.registrar_llegada(RegistrarLlegadaDeRefaccion(numero, 9))
