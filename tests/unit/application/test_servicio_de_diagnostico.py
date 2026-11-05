"""ServicioDeDiagnostico (US-019, US-020)."""
from __future__ import annotations

import pytest

from application.comandos import (
    AsignarTecnicoParaDiagnostico,
    RegistrarDiagnostico,
    ReportarFallaAdicional,
)
from domain.compartido.errores import (
    DiagnosticoNoModificable,
    EmpleadoNoEncontrado,
    TrabajoDeOtroTecnico,
    TransicionDeEstadoNoPermitida,
    ValorInvalido,
)
from domain.ordenes.eventos import DiagnosticoRegistrado, TecnicoAsignadoParaDiagnostico
from tests.unit.application.escenarios import (
    AHORA,
    GERENTE,
    OTRO_TECNICO,
    TECNICO,
    Taller,
    cotizada,
    diagnosticada,
    en_diagnostico,
    recibida,
)


def test_ca_035_asigna_tecnico_y_pasa_a_en_diagnostico(taller: Taller) -> None:
    numero = recibida(taller)

    resultado = taller.diagnostico.asignar_tecnico(AsignarTecnicoParaDiagnostico(numero, TECNICO))

    assert resultado.estado == "En Diagnóstico"
    assert taller.datos.ordenes[numero].tecnico_de_diagnostico == TECNICO
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [TecnicoAsignadoParaDiagnostico]


def test_ca_035_empleado_sin_rol_tecnico_es_invalido(taller: Taller) -> None:
    numero = recibida(taller)

    with pytest.raises(ValorInvalido, match="no es Técnico"):
        taller.diagnostico.asignar_tecnico(AsignarTecnicoParaDiagnostico(numero, GERENTE))

    assert taller.datos.ordenes[numero].estado.value == "Recibida"


def test_ca_035_empleado_inexistente(taller: Taller) -> None:
    numero = recibida(taller)

    with pytest.raises(EmpleadoNoEncontrado):
        taller.diagnostico.asignar_tecnico(AsignarTecnicoParaDiagnostico(numero, "EMP-999"))


def test_ca_032_registra_diagnostico_con_hora_del_reloj(taller: Taller) -> None:
    numero = en_diagnostico(taller)

    resultado = taller.diagnostico.registrar_diagnostico(
        RegistrarDiagnostico(numero, TECNICO, "Balatas gastadas", "Cambiar balatas")
    )

    assert resultado.registrado_en == AHORA
    assert resultado.estado == "En Diagnóstico"
    assert taller.datos.ordenes[numero].diagnostico.fallas == "Balatas gastadas"
    eventos = taller.publicador.publicar.call_args.args[0]
    assert [type(evento) for evento in eventos] == [DiagnosticoRegistrado]


def test_rn_02_solo_el_tecnico_asignado_registra(taller: Taller) -> None:
    numero = en_diagnostico(taller)

    with pytest.raises(TrabajoDeOtroTecnico):
        taller.diagnostico.registrar_diagnostico(
            RegistrarDiagnostico(numero, OTRO_TECNICO, "Fallas", "Trabajos")
        )

    assert taller.datos.ordenes[numero].diagnostico is None


def test_rn_02_el_tecnico_corrige_antes_de_cotizar(taller: Taller) -> None:
    numero = diagnosticada(taller)

    taller.diagnostico.registrar_diagnostico(
        RegistrarDiagnostico(numero, TECNICO, "Fallas corregidas", "Trabajos")
    )

    assert taller.datos.ordenes[numero].diagnostico.fallas == "Fallas corregidas"


def test_ca_033_no_cambia_despues_de_cotizar(taller: Taller) -> None:
    numero, _ = cotizada(taller)

    with pytest.raises(DiagnosticoNoModificable):
        taller.diagnostico.registrar_diagnostico(
            RegistrarDiagnostico(numero, TECNICO, "Otra falla", "Otro trabajo")
        )

    assert taller.datos.ordenes[numero].diagnostico.fallas == "Balatas gastadas"


def test_rn_03_mensaje_indica_falla_adicional(taller: Taller) -> None:
    numero, _ = cotizada(taller)

    with pytest.raises(DiagnosticoNoModificable, match="falla adicional"):
        taller.diagnostico.registrar_diagnostico(
            RegistrarDiagnostico(numero, TECNICO, "Otra falla", "Otro trabajo")
        )


def test_ca_034_falla_fuera_de_reparacion_se_rechaza(taller: Taller) -> None:
    numero = en_diagnostico(taller)

    with pytest.raises(TransicionDeEstadoNoPermitida, match="En Reparación"):
        taller.diagnostico.reportar_falla_adicional(
            ReportarFallaAdicional(numero, TECNICO, "Fuga de aceite")
        )

    assert taller.datos.ordenes[numero].fallas_adicionales == ()
