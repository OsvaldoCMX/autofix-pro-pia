"""Generar, presentar, ajustar y recontactar cotizaciones (US-004, US-009, US-023).

No decide si se requiere al Gerente: eso lo resuelve la Specification E1 dentro de `Cotizacion`.
"""
from __future__ import annotations

from application.comandos import (
    AjustarCotizacion,
    GenerarCotizacion,
    PresentarCotizacion,
    RegistrarRecontacto,
    TrabajoPropuesto,
)
from application.puertos import PublicadorDeEventos, Reloj
from application.resultados import ResultadoDeCotizacion, ResultadoDeRecontacto
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.compartido.errores import ValorInvalido
from domain.compartido.valores import Dinero, NumeroOrden
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.linea_de_cotizacion import LineaDeCotizacion
from domain.cotizaciones.valores import RefaccionCotizada, TipoCotizacion, VersionCotizacion


class ServicioDeCotizacion:
    def __init__(
        self, uow: UnidadDeTrabajo, reloj: Reloj, publicador: PublicadorDeEventos
    ) -> None:
        self._uow = uow
        self._reloj = reloj
        self._publicador = publicador

    def generar_inicial(self, comando: GenerarCotizacion) -> ResultadoDeCotizacion:
        ahora = self._reloj.ahora()
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.marcar_cotizada(ahora)
            _exigir_servicios_habilitados(uow, orden.numero)
            cotizacion = Cotizacion.generar(
                uow.cotizaciones.siguiente_id(),
                orden.numero,
                TipoCotizacion.INICIAL,
                VersionCotizacion(1),
                a_lineas(comando.trabajos),
                ahora,
            )
            uow.cotizaciones.agregar(cotizacion)
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return resultado_de_cotizacion(cotizacion)

    def generar_adicional(self, comando: GenerarCotizacion) -> ResultadoDeCotizacion:
        ahora = self._reloj.ahora()
        with self._uow as uow:
            orden = uow.ordenes.obtener(NumeroOrden(comando.numero_orden))
            orden.registrar_cotizacion_adicional_pendiente(ahora)
            cotizacion = Cotizacion.generar(
                uow.cotizaciones.siguiente_id(),
                orden.numero,
                TipoCotizacion.ADICIONAL,
                uow.cotizaciones.siguiente_version(orden.numero),
                a_lineas(comando.trabajos),
                ahora,
            )
            uow.cotizaciones.agregar(cotizacion)
            uow.ordenes.guardar(orden)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return resultado_de_cotizacion(cotizacion)

    def presentar(self, comando: PresentarCotizacion) -> ResultadoDeCotizacion:
        with self._uow as uow:
            cotizacion = uow.cotizaciones.obtener(comando.id_cotizacion)
            cotizacion.marcar_presentada(self._reloj.ahora())
            uow.cotizaciones.guardar(cotizacion)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return resultado_de_cotizacion(cotizacion)

    def ajustar(self, comando: AjustarCotizacion) -> ResultadoDeCotizacion:
        with self._uow as uow:
            cotizacion = uow.cotizaciones.obtener(comando.id_cotizacion)
            cotizacion.ajustar(a_lineas(comando.trabajos), self._reloj.ahora())
            uow.cotizaciones.guardar(cotizacion)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return resultado_de_cotizacion(cotizacion)

    def registrar_recontacto(self, comando: RegistrarRecontacto) -> ResultadoDeRecontacto:
        ahora = self._reloj.ahora()
        with self._uow as uow:
            cotizacion = uow.cotizaciones.obtener(comando.id_cotizacion)
            cotizacion.registrar_recontacto(comando.asesor, ahora)
            uow.cotizaciones.guardar(cotizacion)
            uow.confirmar()
        self._publicador.publicar(uow.eventos_confirmados())
        return ResultadoDeRecontacto(cotizacion.id, cotizacion.estado.value, ahora)


def _exigir_servicios_habilitados(uow: UnidadDeTrabajo, numero: NumeroOrden) -> None:
    """D-05: un servicio inhabilitado es un dato inválido y esa orden no se puede cotizar."""
    inhabilitados = uow.catalogo.servicios_inhabilitados_de_la_orden(numero)
    if inhabilitados:
        raise ValorInvalido(
            f"No se puede cotizar la orden {numero}: incluye servicios que el taller "
            f"no ofrece por ahora ({', '.join(inhabilitados)}). Informe al cliente."
        )


def a_lineas(trabajos: tuple[TrabajoPropuesto, ...]) -> list[LineaDeCotizacion]:
    """Traduce los datos de entrada a objetos del dominio, que validan sus propias reglas."""
    return [
        LineaDeCotizacion(
            trabajo.numero,
            trabajo.descripcion,
            Dinero(trabajo.mano_de_obra),
            tuple(
                RefaccionCotizada(r.descripcion, r.cantidad, Dinero(r.precio_unitario))
                for r in trabajo.refacciones
            ),
        )
        for trabajo in trabajos
    ]


def resultado_de_cotizacion(cotizacion: Cotizacion) -> ResultadoDeCotizacion:
    return ResultadoDeCotizacion(
        cotizacion.id,
        str(cotizacion.numero_orden),
        str(cotizacion.version),
        cotizacion.tipo.value,
        cotizacion.estado.value,
        str(cotizacion.total.monto),
        cotizacion.fecha_presentacion,
        cotizacion.fecha_aprobacion_gerencial,
    )
