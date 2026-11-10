"""Esquemas de cotización (US-004, US-005, US-023)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from api.esquemas.comunes import (
    EnteroPositivo,
    Importe,
    ModeloDeEntrada,
    ModeloDeSalida,
    TextoDeRefaccion,
    TextoLargo,
)
from application.comandos import RefaccionPropuesta, TrabajoPropuesto


class NuevaRefaccion(ModeloDeEntrada):
    descripcion: TextoDeRefaccion
    cantidad: EnteroPositivo
    precio_unitario: Importe

    def a_comando(self) -> RefaccionPropuesta:
        return RefaccionPropuesta(
            self.descripcion, self.cantidad, Decimal(self.precio_unitario)
        )


class NuevoTrabajo(ModeloDeEntrada):
    numero: EnteroPositivo
    descripcion: str
    mano_de_obra: Importe
    refacciones: list[NuevaRefaccion] = []

    def a_comando(self) -> TrabajoPropuesto:
        return TrabajoPropuesto(
            self.numero,
            self.descripcion,
            Decimal(self.mano_de_obra),
            tuple(refaccion.a_comando() for refaccion in self.refacciones),
        )


class DatosDeCotizacion(ModeloDeEntrada):
    trabajos: list[NuevoTrabajo]

    def a_trabajos(self) -> tuple[TrabajoPropuesto, ...]:
        return tuple(trabajo.a_comando() for trabajo in self.trabajos)


class DatosDeCorreccion(ModeloDeEntrada):
    """Los trabajos correctos y el motivo; el asesor sale de su clave de acceso (H-PIA-21)."""

    trabajos: list[NuevoTrabajo]
    motivo: TextoLargo

    def a_trabajos(self) -> tuple[TrabajoPropuesto, ...]:
        return tuple(trabajo.a_comando() for trabajo in self.trabajos)


class DatosDeRevision(ModeloDeEntrada):
    aprobada: bool
    observaciones: str = ""


class CotizacionRegistrada(ModeloDeSalida):
    """Las fechas solo aparecen cuando ya existen, como en el ejemplo de `docs/api/README.md`."""

    id: str
    numero_orden: str
    version: str
    tipo: str
    estado: str
    total: str
    fecha_presentacion: datetime | None = None
    fecha_aprobacion_gerencial: datetime | None = None


class RecontactoRegistrado(ModeloDeSalida):
    id_cotizacion: str
    estado: str
    registrado_en: datetime


class CotizacionPorAprobar(ModeloDeSalida):
    id_cotizacion: str
    numero_orden: str
    version: str
    total: str


class RefaccionDeLinea(ModeloDeSalida):
    descripcion: str
    cantidad: int
    precio_unitario: str
    importe: str


class LineaDetallada(ModeloDeSalida):
    numero: int
    descripcion: str
    mano_de_obra: str
    refacciones: list[RefaccionDeLinea]
    subtotal: str
    decision: str | None


class CorreccionDeCotizacion(ModeloDeSalida):
    asesor: str
    registrada_en: datetime
    motivo: str
    total_anterior: str
    total_nuevo: str
    estado_anterior: str
    estado_nuevo: str
    fecha_presentacion_anterior: datetime | None
    fecha_aprobacion_gerencial_anterior: datetime | None


class CotizacionDetallada(ModeloDeSalida):
    id: str
    numero_orden: str
    tipo: str
    version: str
    estado: str
    total: str
    generada_en: datetime
    fecha_aprobacion_gerencial: datetime | None
    observaciones_del_gerente: str | None
    fecha_presentacion: datetime | None
    autorizante: str | None
    fecha_decision: datetime | None
    lineas: list[LineaDetallada]
    correcciones: list[CorreccionDeCotizacion]
