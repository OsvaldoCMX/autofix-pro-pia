"""Domain Service: un vehículo tiene a lo más una orden abierta (RN-27, CA-052, H-PIA-22).

La regla cruza dos Aggregates (el Vehículo, por sus placas, y las Órdenes que ya existen), por eso
no pertenece a ninguno. Como respaldo ante dos registros al mismo tiempo, la base tiene un índice
único parcial con la misma lista de estados cerrados (`ESTADOS_DE_ORDEN_CERRADA`).
"""
from __future__ import annotations

from domain.compartido.errores import VehiculoConOrdenAbierta
from domain.compartido.valores import Placas
from domain.ordenes.orden_de_servicio import OrdenDeServicio


class VerificadorDeOrdenUnica:
    def verificar(self, placas: Placas, orden_abierta: OrdenDeServicio | None) -> None:
        if orden_abierta is not None:
            raise vehiculo_con_orden_abierta(placas, orden_abierta)


def vehiculo_con_orden_abierta(
    placas: Placas, orden_abierta: OrdenDeServicio | None
) -> VehiculoConOrdenAbierta:
    """El mismo mensaje sale del verificador y de la base cuando rechaza un registro simultáneo."""
    if orden_abierta is None:
        return VehiculoConOrdenAbierta(
            f"El vehículo con placas {placas} ya tiene una orden abierta. "
            "Búsquela por sus placas en lugar de registrar otra."
        )
    return VehiculoConOrdenAbierta(
        f"El vehículo con placas {placas} ya tiene abierta la orden {orden_abierta.numero} "
        f"(estado «{orden_abierta.estado.value}»). Ábrala en lugar de registrar otra."
    )
