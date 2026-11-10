"""Esquemas de recepción: clientes, vehículos, órdenes y expediente (US-001 a US-003, US-016)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import Field

from api.esquemas.comunes import (
    ANIO_MAXIMO,
    ANIO_MINIMO,
    EnteroNoNegativo,
    ModeloDeEntrada,
    ModeloDeSalida,
    TextoDeIdentificador,
    TextoDeMarca,
    TextoDeNombre,
    TextoDeTelefono,
    TextoDeVin,
    TextoLargo,
)
from api.esquemas.cotizaciones import CotizacionDetallada
from application.comandos import DatosDeVehiculo, RegistrarCliente, RegistrarOrden
from domain.clientes.cliente import TipoCliente
from domain.ordenes.valores import NivelDeCombustible


class NuevoCliente(ModeloDeEntrada):
    nombre: TextoDeNombre
    tipo: TipoCliente = TipoCliente.PARTICULAR
    telefono: TextoDeTelefono | None = None
    correo: TextoDeNombre | None = None
    empresa: TextoDeNombre | None = None
    responsable_nombre: TextoDeNombre | None = None
    responsable_telefono: TextoDeTelefono | None = None
    responsable_correo: TextoDeNombre | None = None

    def a_comando(self) -> RegistrarCliente:
        return RegistrarCliente(**self.model_dump())


class DatosDeContacto(ModeloDeEntrada):
    """Corrección de los datos del cliente (CA-055)."""

    nombre: TextoDeNombre
    telefono: TextoDeTelefono | None = None
    correo: TextoDeNombre | None = None


class DatosDeRecepcion(ModeloDeEntrada):
    """Corrección del estado de recepción (CA-057)."""

    kilometraje: EnteroNoNegativo
    nivel_de_combustible: NivelDeCombustible
    motivo_de_ingreso: TextoLargo


class NuevoVehiculo(ModeloDeEntrada):
    vin: TextoDeVin
    marca: TextoDeMarca
    modelo: TextoDeMarca
    anio: int = Field(ge=ANIO_MINIMO, le=ANIO_MAXIMO)

    def a_comando(self) -> DatosDeVehiculo:
        return DatosDeVehiculo(**self.model_dump())


class NuevaOrden(ModeloDeEntrada):
    """Con placas nuevas, `vehiculo` es obligatorio y el cliente se da por id o por sus datos."""

    placas: str
    motivo_de_ingreso: str
    kilometraje: EnteroNoNegativo
    nivel_de_combustible: NivelDeCombustible
    vehiculo: NuevoVehiculo | None = None
    id_cliente: TextoDeIdentificador | None = None
    cliente: NuevoCliente | None = None

    def a_comando(self, asesor: str) -> RegistrarOrden:
        return RegistrarOrden(
            asesor,
            self.placas,
            self.motivo_de_ingreso,
            self.kilometraje,
            self.nivel_de_combustible,
            self.vehiculo.a_comando() if self.vehiculo else None,
            self.id_cliente,
            self.cliente.a_comando() if self.cliente else None,
        )


class ClienteRegistrado(ModeloDeSalida):
    id_cliente: str
    nombre: str
    tipo: str
    empresa: str | None
    responsable_nombre: str | None


class ClienteCorregido(ModeloDeSalida):
    id_cliente: str
    nombre: str
    tipo: str
    telefono: str | None
    correo: str | None


class RecepcionCorregida(ModeloDeSalida):
    numero_orden: str
    estado: str
    kilometraje: int
    nivel_de_combustible: str
    motivo_de_ingreso: str


class VehiculoCorregido(ModeloDeSalida):
    placas: str
    vin: str
    marca: str
    modelo: str
    anio: int


class OrdenRegistrada(ModeloDeSalida):
    numero_orden: str
    estado: str
    id_cliente: str
    placas: str
    fecha_ingreso: datetime
    mensaje: str


class ClienteEncontrado(ModeloDeSalida):
    id_cliente: str
    nombre: str
    tipo: str
    telefono: str | None
    correo: str | None
    empresa: str | None
    responsable_nombre: str | None
    responsable_telefono: str | None
    responsable_correo: str | None


class VehiculoEncontrado(ModeloDeSalida):
    placas: str
    vin: str
    marca: str
    modelo: str
    anio: int
    cliente: ClienteEncontrado


class TrabajoDeOrden(ModeloDeSalida):
    id: int
    descripcion: str
    importe: str
    estado: str
    tecnico: str | None


class TrabajoDelExpediente(TrabajoDeOrden):
    tecnico_nombre: str | None


class SolicitudDeOrden(ModeloDeSalida):
    numero_orden: str
    id: int
    id_trabajo: int
    refaccion: str
    cantidad: int
    estado: str
    fecha_solicitud: datetime
    fecha_llegada: datetime | None
    fecha_aviso_al_cliente: datetime | None


class FallaDeOrden(ModeloDeSalida):
    id: int
    descripcion: str
    tecnico: str
    reportada_en: datetime


class ExpedienteDeOrden(ModeloDeSalida):
    numero_orden: str
    estado: str
    id_cliente: str
    placas: str
    asesor: str
    motivo_de_ingreso: str
    fecha_ingreso: datetime
    ultima_actualizacion: datetime
    kilometraje: int | None
    nivel_de_combustible: str | None
    tecnico_de_diagnostico: str | None
    diagnostico_fallas: str | None
    diagnostico_recomendaciones: str | None
    rechazo_total: bool
    total_autorizado: str
    pago_monto: str | None
    pago_forma: str | None
    pago_registrado_en: datetime | None
    credito_monto: str | None
    credito_fecha_vencimiento: date | None
    nota_fecha_salida: datetime | None
    nota_firmada: bool
    fecha_entrega: datetime | None
    cancelacion_motivo: str | None
    cotizaciones: list[CotizacionDetallada]
    trabajos: list[TrabajoDelExpediente]
    solicitudes: list[SolicitudDeOrden]
    fallas_adicionales: list[FallaDeOrden]
    cliente_nombre: str | None
    cliente_tipo: str | None
    empresa: str | None
    responsable_nombre: str | None
    vehiculo_marca: str | None
    vehiculo_modelo: str | None
    vehiculo_anio: int | None
    tecnico_de_diagnostico_nombre: str | None
