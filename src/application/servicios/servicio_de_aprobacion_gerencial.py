"""El Gerente aprueba o rechaza las cotizaciones de alto monto (US-005, CA-008, CA-009)."""
from __future__ import annotations

from application.comandos import RevisarCotizacion
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import ResultadoDeCotizacion
from application.servicios.servicio_de_cotizacion import resultado_de_cotizacion
from application.unidad_de_trabajo import UnidadDeTrabajo


class ServicioDeAprobacionGerencial:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador

    def revisar(self, comando: RevisarCotizacion) -> ResultadoDeCotizacion:
        ahora = self._reloj.ahora()
        with self._uow as uow:
            cotizacion = uow.cotizaciones.obtener(comando.id_cotizacion)
            if comando.aprobada:
                cotizacion.aprobar_por_gerente(ahora)
            else:
                cotizacion.rechazar_por_gerente(comando.observaciones, ahora)
            uow.cotizaciones.guardar(cotizacion)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return resultado_de_cotizacion(cotizacion)
