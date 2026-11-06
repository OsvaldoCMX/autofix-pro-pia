"""Revisión periódica de plazos con E7 y E8 (US-012, US-023, ADR-015).

Es idempotente: cada alerta lleva una clave y no se repite aunque la revisión corra varias veces.
Una solicitud genera una sola alerta; una cotización, una por cada periodo de 48 horas.

Los candidatos se leen antes de abrir la Unidad de Trabajo: el lector usa su propia conexión y
no debe intercalarse con la transacción. Cada candidato se vuelve a evaluar ya dentro de ella.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from application.consultas.lector import LectorDeOrdenes
from application.puertos import AlertaInterna, Reloj
from application.resultados import ResultadoDeRevisionDePlazos
from application.unidad_de_trabajo import UnidadDeTrabajo
from domain.compartido.valores import NumeroOrden
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.especificaciones import RequiereRecontacto
from domain.ordenes.especificaciones import RequiereAlertaDeRefaccion
from domain.ordenes.orden_de_servicio import OrdenDeServicio
from domain.ordenes.solicitud_de_compra import SolicitudDeCompra


class ServicioDeRevisionDePlazos:
    def __init__(self, uow: UnidadDeTrabajo, lector: LectorDeOrdenes, reloj: Reloj) -> None:
        self._uow = uow
        self._lector = lector
        self._reloj = reloj

    def revisar(self) -> ResultadoDeRevisionDePlazos:
        ahora = self._reloj.ahora_en_el_taller()
        ordenes = self._lector.ordenes_con_solicitudes_pendientes()
        cotizaciones = self._lector.cotizaciones_presentadas_sin_decision()
        with self._uow as uow:
            refacciones = _revisar_refacciones(uow, ordenes, ahora)
            recontactos = _revisar_cotizaciones(uow, cotizaciones, ahora)
            uow.confirmar()
        return ResultadoDeRevisionDePlazos(refacciones, recontactos)


def _revisar_refacciones(
    uow: UnidadDeTrabajo, ordenes: Iterable[NumeroOrden], ahora: datetime
) -> int:
    regla = RequiereAlertaDeRefaccion(ahora)
    creadas = 0
    for numero in ordenes:
        orden = uow.ordenes.obtener(numero)
        for solicitud in orden.solicitudes:
            if regla.es_satisfecha_por(solicitud):
                alerta = _alerta_de_refaccion(orden, solicitud, ahora)
                creadas += _crear_si_es_nueva(uow, alerta)
    return creadas


def _revisar_cotizaciones(
    uow: UnidadDeTrabajo, cotizaciones: Iterable[str], ahora: datetime
) -> int:
    regla = RequiereRecontacto(ahora)
    creadas = 0
    for id_cotizacion in cotizaciones:
        cotizacion = uow.cotizaciones.obtener(id_cotizacion)
        if regla.es_satisfecha_por(cotizacion):
            orden = uow.ordenes.obtener(cotizacion.numero_orden)
            creadas += _crear_si_es_nueva(
                uow, _alerta_de_recontacto(orden.asesor, cotizacion, ahora)
            )
    return creadas


def _crear_si_es_nueva(uow: UnidadDeTrabajo, alerta: AlertaInterna) -> int:
    if alerta.clave is not None and uow.alertas.existe_clave(alerta.clave):
        return 0
    uow.alertas.agregar(alerta)
    return 1


def _alerta_de_refaccion(
    orden: OrdenDeServicio, solicitud: SolicitudDeCompra, ahora: datetime
) -> AlertaInterna:
    return AlertaInterna(
        "RefaccionRetrasada",
        f"La refacción «{solicitud.refaccion}» de la orden {orden.numero} lleva más de "
        "3 días hábiles sin llegar: avise al cliente.",
        ahora,
        destinatario=orden.asesor,
        numero_orden=str(orden.numero),
        clave=f"refaccion:{orden.numero}:{solicitud.id}",
    )


def _alerta_de_recontacto(
    asesor: str, cotizacion: Cotizacion, ahora: datetime
) -> AlertaInterna:
    ultimo_contacto = cotizacion.ultimo_contacto.astimezone(UTC).isoformat()
    return AlertaInterna(
        "CotizacionSinRespuesta",
        f"La cotización {cotizacion.id} de la orden {cotizacion.numero_orden} lleva más de "
        "48 horas sin respuesta: vuelva a contactar al cliente.",
        ahora,
        destinatario=asesor,
        numero_orden=str(cotizacion.numero_orden),
        id_cotizacion=cotizacion.id,
        clave=f"recontacto:{cotizacion.id}:{ultimo_contacto}",
    )
