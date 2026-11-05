"""ServicioDeReparacion (US-006, US-008, US-020)."""
from __future__ import annotations

import pytest

from application.comandos import AsignarTrabajos, CompletarTrabajo, IniciarTrabajo
from domain.compartido.errores import (
    EmpleadoNoEncontrado,
    TrabajoDeOtroTecnico,
    TrabajoNoAutorizado,
    TrabajoNoEncontrado,
    TrabajoNoPermitido,
    TransicionDeEstadoNoPermitida,
    ValorInvalido,
)
from domain.ordenes.eventos import OrdenListaParaEntrega, TrabajoIniciado, TrabajosAsignados
from tests.unit.application.escenarios import (
    GERENTE,
    OTRO_TECNICO,
    TECNICO,
    Taller,
    asignada,
    autorizada,
    con_adicional,
    cotizada,
    decidir,
    en_espera,
    en_reparacion,
    pausada,
)


def test_ca_011_solo_asigna_autorizados(taller: Taller) -> None:
    numero, _ = autorizada(taller, lineas=(1,))

    with pytest.raises(TrabajoNoAutorizado, match="no fue autorizado"):
        taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1, 2), TECNICO))

    assert taller.datos.ordenes[numero].trabajos[0].tecnico is None


def test_ca_012_no_asigna_tras_rechazo_total(taller: Taller) -> None:
    numero, id_cotizacion = cotizada(taller)
    decidir(taller, id_cotizacion, ())

    with pytest.raises(TrabajoNoAutorizado):
        taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1,), TECNICO))


def test_ca_036_asigna_al_tecnico(taller: Taller) -> None:
    numero, _ = autorizada(taller)

    resultado = taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1, 2), TECNICO))

    assert resultado.ids_trabajos == (1, 2)
    assert resultado.tecnico == TECNICO
    assert [t.tecnico for t in taller.datos.ordenes[numero].trabajos] == [TECNICO, TECNICO]
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [TrabajosAsignados]


def test_ca_036_empleado_sin_rol_tecnico_es_invalido(taller: Taller) -> None:
    numero, _ = autorizada(taller)

    with pytest.raises(ValorInvalido, match="no es Técnico"):
        taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1,), GERENTE))


def test_ca_036_empleado_inexistente(taller: Taller) -> None:
    numero, _ = autorizada(taller)

    with pytest.raises(EmpleadoNoEncontrado):
        taller.reparacion.asignar_trabajos(AsignarTrabajos(numero, (1,), "EMP-999"))


def test_ca_014_iniciar_pasa_a_en_reparacion(taller: Taller) -> None:
    numero = asignada(taller)

    resultado = taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 1, TECNICO))

    assert resultado.estado_trabajo == "En Progreso"
    assert resultado.estado_orden == "En Reparación"
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [TrabajoIniciado]


def test_ca_014_iniciar_en_espera_mantiene_la_espera(taller: Taller) -> None:
    numero = en_espera(taller)

    resultado = taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 1, TECNICO))

    assert resultado.estado_orden == "En Espera de Refacción"
    assert taller.datos.ordenes[numero].estado_antes_de_espera.value == "En Reparación"


def test_ca_015_ultimo_trabajo_pasa_a_lista(taller: Taller) -> None:
    numero = en_reparacion(taller)
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 2, TECNICO))
    primero = taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 1, TECNICO))

    ultimo = taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 2, TECNICO))

    assert primero.estado_orden == "En Reparación"
    assert ultimo.estado_trabajo == "Completado"
    assert ultimo.estado_orden == "Lista para Entrega"
    tipos = [type(evento) for evento in taller.publicador.publicar.call_args.args[0]]
    assert tipos == [OrdenListaParaEntrega]


def test_ca_046_no_inicia_con_vehiculo_fuera(taller: Taller) -> None:
    numero = pausada(taller)

    with pytest.raises(TrabajoNoPermitido, match="no está en el taller"):
        taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 1, TECNICO))

    assert taller.datos.ordenes[numero].trabajos[0].estado.value == "Pendiente"


def test_rn_14_otro_tecnico_no_inicia(taller: Taller) -> None:
    numero = asignada(taller)

    with pytest.raises(TrabajoDeOtroTecnico):
        taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 1, OTRO_TECNICO))


def test_rn_14_otro_tecnico_no_completa(taller: Taller) -> None:
    numero = en_reparacion(taller)

    with pytest.raises(TrabajoDeOtroTecnico):
        taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 1, OTRO_TECNICO))


def test_rn_15_con_adicional_pendiente_no_pasa_a_lista(taller: Taller) -> None:
    numero, _ = con_adicional(taller)
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 2, TECNICO))
    taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 1, TECNICO))

    resultado = taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 2, TECNICO))

    assert resultado.estado_orden == "En Reparación"


def test_rn_15_con_refaccion_pendiente_no_se_completa_el_ultimo(taller: Taller) -> None:
    numero = en_espera(taller, iniciada=True)
    taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 2, TECNICO))
    taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 1, TECNICO))

    with pytest.raises(TransicionDeEstadoNoPermitida, match="refacciones pendientes"):
        taller.reparacion.completar_trabajo(CompletarTrabajo(numero, 2, TECNICO))

    assert taller.datos.ordenes[numero].trabajos[1].estado.value == "En Progreso"


def test_trabajo_inexistente(taller: Taller) -> None:
    numero = asignada(taller)

    with pytest.raises(TrabajoNoEncontrado):
        taller.reparacion.iniciar_trabajo(IniciarTrabajo(numero, 9, TECNICO))
