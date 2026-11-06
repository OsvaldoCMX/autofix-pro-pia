"""Puertos: lo que la aplicación necesita del exterior, expresado como interfaces (ADR-004)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from domain.compartido.errores import ValorInvalido
from domain.compartido.eventos import EventoDeDominio
from domain.compartido.valores import NumeroOrden
from domain.cotizaciones.cotizacion import Cotizacion
from domain.empleados.empleado import RolDeEmpleado
from domain.ordenes.orden_de_servicio import OrdenDeServicio


class Reloj(ABC):
    @abstractmethod
    def ahora(self) -> datetime:
        """Fecha y hora actual en UTC; es la que se guarda."""

    @abstractmethod
    def ahora_en_el_taller(self) -> datetime:
        """El mismo instante en la zona del taller: define «hoy», los días hábiles y el crédito."""


class CatalogoDeServicios(ABC):
    """Catálogo de referencia del paquete del profesor (ADR-013, D-05)."""

    @abstractmethod
    def servicios_inhabilitados_de_la_orden(self, numero: NumeroOrden) -> tuple[str, ...]:
        """Servicios solicitados en la orden que no se pueden cotizar, ordenados por su id."""


class PublicadorDeEventos(ABC):
    @abstractmethod
    def publicar(self, eventos: list[EventoDeDominio]) -> None:
        """Entrega los eventos ya confirmados a quienes reaccionan a ellos (ADR-016)."""


class GeneradorDeDocumentos(ABC):
    """Documentos P2 (ADR-014): los servicios que los usan se construyen en la Fase 10."""

    @abstractmethod
    def cotizacion(self, cotizacion: Cotizacion) -> bytes: ...

    @abstractmethod
    def nota_de_responsabilidad(self, orden: OrdenDeServicio) -> bytes: ...

    @abstractmethod
    def recibo_interno(self, orden: OrdenDeServicio) -> bytes: ...


@dataclass(frozen=True)
class AlertaInterna:
    """Aviso en el panel de un empleado o de todo un rol; no es correo ni SMS (Glosario)."""

    tipo: str
    mensaje: str
    creada_en: datetime
    destinatario: str | None = None
    destinatario_rol: RolDeEmpleado | None = None
    numero_orden: str | None = None
    id_cotizacion: str | None = None
    clave: str | None = None
    leida: bool = False

    def __post_init__(self) -> None:
        if self.destinatario is None and self.destinatario_rol is None:
            raise ValorInvalido("Una alerta debe dirigirse a un empleado o a un rol.")


class RepositorioDeAlertas(ABC):
    @abstractmethod
    def agregar(self, alerta: AlertaInterna) -> None: ...

    @abstractmethod
    def existe_clave(self, clave: str) -> bool:
        """Evita repetir una alerta de la revisión de plazos (ADR-015)."""
