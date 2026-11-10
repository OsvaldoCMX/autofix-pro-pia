"""Commands: los datos que recibe cada caso de uso (ADR-003). No contienen reglas de negocio.

Los empleados se identifican por su id; la API lo toma del token, no del cuerpo de la petición.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from domain.clientes.cliente import TipoCliente
from domain.cotizaciones.valores import RolDeAutorizante
from domain.ordenes.valores import FormaDePago, NivelDeCombustible


# ------------------------------------------------------------------ recepción
@dataclass(frozen=True)
class RegistrarCliente:
    nombre: str
    tipo: TipoCliente = TipoCliente.PARTICULAR
    telefono: str | None = None
    correo: str | None = None
    empresa: str | None = None
    responsable_nombre: str | None = None
    responsable_telefono: str | None = None
    responsable_correo: str | None = None


@dataclass(frozen=True)
class CorregirCliente:
    """Corrige el nombre, el teléfono o el correo mal capturados (CA-055, H-PIA-24)."""

    id_cliente: str
    nombre: str
    telefono: str | None = None
    correo: str | None = None


@dataclass(frozen=True)
class CorregirRecepcion:
    """Corrige el kilometraje, el combustible o el motivo antes de la cotización (CA-057)."""

    numero_orden: str
    kilometraje: int
    nivel_de_combustible: NivelDeCombustible
    motivo_de_ingreso: str


@dataclass(frozen=True)
class CorregirVehiculo:
    """Corrige el VIN, la marca, el modelo o el año; las placas no cambian (CA-056)."""

    placas: str
    vin: str
    marca: str
    modelo: str
    anio: int


@dataclass(frozen=True)
class DatosDeVehiculo:
    vin: str
    marca: str
    modelo: str
    anio: int


@dataclass(frozen=True)
class RegistrarOrden:
    """Con placas nuevas, `vehiculo` es obligatorio y el cliente se da por id o por sus datos."""

    asesor: str
    placas: str
    motivo_de_ingreso: str
    kilometraje: int
    nivel_de_combustible: NivelDeCombustible
    vehiculo: DatosDeVehiculo | None = None
    id_cliente: str | None = None
    cliente: RegistrarCliente | None = None


# ------------------------------------------------------------------ cancelación
@dataclass(frozen=True)
class CancelarOrden:
    numero_orden: str
    motivo: str
    asesor: str


# ------------------------------------------------------------------ diagnóstico
@dataclass(frozen=True)
class AsignarTecnicoParaDiagnostico:
    numero_orden: str
    tecnico: str


@dataclass(frozen=True)
class RegistrarDiagnostico:
    numero_orden: str
    tecnico: str
    fallas: str
    recomendaciones: str


@dataclass(frozen=True)
class ReportarFallaAdicional:
    numero_orden: str
    tecnico: str
    descripcion: str


# ------------------------------------------------------------------ cotización
@dataclass(frozen=True)
class RefaccionPropuesta:
    descripcion: str
    cantidad: int
    precio_unitario: Decimal


@dataclass(frozen=True)
class TrabajoPropuesto:
    numero: int
    descripcion: str
    mano_de_obra: Decimal
    refacciones: tuple[RefaccionPropuesta, ...] = ()


@dataclass(frozen=True)
class GenerarCotizacion:
    numero_orden: str
    trabajos: tuple[TrabajoPropuesto, ...]


@dataclass(frozen=True)
class PresentarCotizacion:
    id_cotizacion: str


@dataclass(frozen=True)
class AjustarCotizacion:
    id_cotizacion: str
    trabajos: tuple[TrabajoPropuesto, ...]


@dataclass(frozen=True)
class CorregirCotizacion:
    """El asesor corrige una cotización antes de la decisión del cliente (H-PIA-21)."""

    id_cotizacion: str
    trabajos: tuple[TrabajoPropuesto, ...]
    motivo: str
    asesor: str


@dataclass(frozen=True)
class RegistrarRecontacto:
    id_cotizacion: str
    asesor: str


@dataclass(frozen=True)
class RevisarCotizacion:
    id_cotizacion: str
    aprobada: bool
    observaciones: str = ""


# ------------------------------------------------------------------ autorización
@dataclass(frozen=True)
class RegistrarDecisionDelCliente:
    id_cotizacion: str
    lineas_autorizadas: tuple[int, ...]
    nombre_del_autorizante: str
    rol_del_autorizante: RolDeAutorizante


# ------------------------------------------------------------------ reparación
@dataclass(frozen=True)
class AsignarTrabajos:
    numero_orden: str
    ids_trabajos: tuple[int, ...]
    tecnico: str


@dataclass(frozen=True)
class IniciarTrabajo:
    numero_orden: str
    id_trabajo: int
    tecnico: str


@dataclass(frozen=True)
class CompletarTrabajo:
    numero_orden: str
    id_trabajo: int
    tecnico: str


# ------------------------------------------------------------------ refacciones
@dataclass(frozen=True)
class SolicitarRefaccion:
    numero_orden: str
    id_trabajo: int
    refaccion: str
    cantidad: int


@dataclass(frozen=True)
class RegistrarLlegadaDeRefaccion:
    numero_orden: str
    id_solicitud: int


@dataclass(frozen=True)
class RegistrarAvisoAlCliente:
    numero_orden: str
    id_solicitud: int


# ------------------------------------------------------------------ retiro anticipado
@dataclass(frozen=True)
class RegistrarSalida:
    numero_orden: str


@dataclass(frozen=True)
class ConfirmarFirmaDeNota:
    numero_orden: str


@dataclass(frozen=True)
class ReactivarOrden:
    numero_orden: str


# ------------------------------------------------------------------ caja
@dataclass(frozen=True)
class RegistrarPago:
    numero_orden: str
    monto: Decimal
    forma: FormaDePago


@dataclass(frozen=True)
class CorregirFormaDePago:
    """Caja corrige la forma de pago antes de la entrega (CA-058)."""

    numero_orden: str
    forma: FormaDePago


@dataclass(frozen=True)
class RegistrarCargoACredito:
    numero_orden: str


# ------------------------------------------------------------------ entrega
@dataclass(frozen=True)
class RegistrarEntrega:
    numero_orden: str


@dataclass(frozen=True)
class EntregarSinReparacion:
    numero_orden: str
