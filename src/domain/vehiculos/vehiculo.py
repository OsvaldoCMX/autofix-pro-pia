"""Aggregate Vehículo (raíz: Vehiculo)."""
from __future__ import annotations

from domain.compartido.errores import ValorInvalido
from domain.compartido.valores import VIN, Placas, texto_requerido

_ANIO_MINIMO = 1900  # CHECK de la tabla vehiculos
_ANIO_MAXIMO = 2100


class Vehiculo:
    """Se identifica por sus placas; pertenece a un cliente por identidad."""

    def __init__(
        self,
        placas: Placas,
        vin: VIN,
        marca: str,
        modelo: str,
        anio: int,
        id_cliente: str,
    ) -> None:
        if not _ANIO_MINIMO <= anio <= _ANIO_MAXIMO:
            raise ValorInvalido(
                f"El año del vehículo debe estar entre {_ANIO_MINIMO} y {_ANIO_MAXIMO}."
            )
        self.placas = placas
        self.vin = vin
        self.marca = texto_requerido(marca, "El vehículo debe tener marca.")
        self.modelo = texto_requerido(modelo, "El vehículo debe tener modelo.")
        self.anio = anio
        self.id_cliente = id_cliente

    def actualizar_datos(self, vin: VIN, marca: str, modelo: str, anio: int) -> None:
        """El asesor confirma o corrige los datos de un vehículo que regresa (CA-003)."""
        validado = Vehiculo(self.placas, vin, marca, modelo, anio, self.id_cliente)
        self.vin = validado.vin
        self.marca = validado.marca
        self.modelo = validado.modelo
        self.anio = validado.anio
