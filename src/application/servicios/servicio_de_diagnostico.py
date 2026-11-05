"""Asignación del técnico, diagnóstico y fallas adicionales (US-019, US-020)."""
from __future__ import annotations

from application.comandos import (
    AsignarTecnicoParaDiagnostico,
    RegistrarDiagnostico,
    ReportarFallaAdicional,
)
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import (
    ResultadoDeDiagnostico,
    ResultadoDeEstado,
    ResultadoDeFallaAdicional,
)
from application.servicios.apoyo import exigir_tecnico
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.compartido.valores import NumeroOrden
from domain.ordenes.valores import Diagnostico


class ServicioDeDiagnostico:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador

    def asignar_tecnico(self, comando: AsignarTecnicoParaDiagnostico) -> ResultadoDeEstado:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            exigir_tecnico(uow, comando.tecnico)
            orden.asignar_tecnico_para_diagnostico(comando.tecnico, self._reloj.ahora())
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeEstado(str(orden.numero), orden.estado.value)

    def registrar_diagnostico(self, comando: RegistrarDiagnostico) -> ResultadoDeDiagnostico:
        diagnostico = Diagnostico(
            comando.fallas, comando.recomendaciones, comando.tecnico, self._reloj.ahora()
        )
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.registrar_diagnostico(diagnostico)
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeDiagnostico(
            str(orden.numero), orden.estado.value, diagnostico.tecnico, diagnostico.registrado_en
        )

    def reportar_falla_adicional(
        self, comando: ReportarFallaAdicional
    ) -> ResultadoDeFallaAdicional:
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            falla = orden.reportar_falla_adicional(
                comando.descripcion, comando.tecnico, self._reloj.ahora()
            )
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeFallaAdicional(
            str(orden.numero), falla.id, falla.descripcion, falla.reportada_en
        )
