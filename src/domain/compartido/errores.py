"""Errores del dominio expresados en términos del negocio.

El mensaje está escrito para el usuario del taller y la API lo devuelve tal cual en `detalle`.
El Aggregate puede pasar un mensaje más específico, con el folio o el estado de la orden.
"""
from __future__ import annotations


class ErrorDeDominio(Exception):
    """Base de todos los errores de negocio."""

    mensaje_por_defecto = "No se pudo completar la operación."

    def __init__(self, mensaje: str | None = None) -> None:
        super().__init__(mensaje or self.mensaje_por_defecto)


class ValorInvalido(ErrorDeDominio):
    mensaje_por_defecto = "Uno de los datos capturados no es válido."


class CotizacionSinTrabajos(ErrorDeDominio):
    mensaje_por_defecto = "La cotización debe tener al menos un trabajo."


class TransicionDeEstadoNoPermitida(ErrorDeDominio):
    mensaje_por_defecto = "El cambio de estado solicitado no está permitido."


class OperacionDeCotizacionNoPermitida(ErrorDeDominio):
    mensaje_por_defecto = "La cotización no está en el estado que exige esta acción."


class DiagnosticoRequerido(ErrorDeDominio):
    mensaje_por_defecto = "Primero debe registrarse el diagnóstico de la orden."


class DiagnosticoNoModificable(ErrorDeDominio):
    mensaje_por_defecto = (
        "El diagnóstico ya no se puede modificar porque la cotización fue generada; "
        "los hallazgos nuevos se registran como falla adicional."
    )


class AutorizanteNoValido(ErrorDeDominio):
    mensaje_por_defecto = (
        "La decisión solo puede registrarse a nombre del cliente particular "
        "o del Responsable de Flotilla."
    )


class TrabajoNoAutorizado(ErrorDeDominio):
    mensaje_por_defecto = "El trabajo no está autorizado por el cliente."


class SolicitudNoPermitida(ErrorDeDominio):
    mensaje_por_defecto = "La orden no permite esta operación en su estado actual."


class TrabajoNoPermitido(ErrorDeDominio):
    mensaje_por_defecto = (
        "El trabajo no se puede iniciar: no está pendiente o el vehículo está fuera del taller."
    )


class TrabajoDeOtroTecnico(ErrorDeDominio):
    mensaje_por_defecto = "El trabajo está asignado a otro técnico."


class PagoNoPermitido(ErrorDeDominio):
    mensaje_por_defecto = (
        "El pago debe cubrir el total autorizado y las flotillas no pagan de contado."
    )


class EntregaNoPermitida(ErrorDeDominio):
    mensaje_por_defecto = (
        "No se puede entregar el vehículo: primero debe registrarse el pago "
        "o el cargo a crédito."
    )


class CancelacionNoPermitida(ErrorDeDominio):
    mensaje_por_defecto = (
        "La orden solo se puede cancelar en estado «Recibida» o «En Diagnóstico»."
    )


class VehiculoConOrdenAbierta(ErrorDeDominio):
    """RN-27: el vehículo ya tiene una orden abierta (H-PIA-22)."""


class CorreccionNoPermitida(ErrorDeDominio):
    """Una corrección de la orden fuera del estado que la permite (H-PIA-23 y H-PIA-24)."""


class OrdenNoEncontrada(ErrorDeDominio):
    mensaje_por_defecto = "No se encontró la orden de servicio."


class CotizacionNoEncontrada(ErrorDeDominio):
    mensaje_por_defecto = "No se encontró la cotización."


class ClienteNoEncontrado(ErrorDeDominio):
    mensaje_por_defecto = "No se encontró el cliente."


class VehiculoNoEncontrado(ErrorDeDominio):
    mensaje_por_defecto = "No se encontró el vehículo."


class EmpleadoNoEncontrado(ErrorDeDominio):
    mensaje_por_defecto = "No se encontró el empleado."


class TrabajoNoEncontrado(ErrorDeDominio):
    mensaje_por_defecto = "No se encontró el trabajo."


class SolicitudNoEncontrada(ErrorDeDominio):
    mensaje_por_defecto = "No se encontró la solicitud de compra."
