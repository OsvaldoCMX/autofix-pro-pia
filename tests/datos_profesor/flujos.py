"""Las acciones de `transiciones_prueba.csv` como peticiones HTTP (datos-profesor §6).

Cada ruta llama a su caso de uso, así que los códigos que se comparan con el oráculo son los reales.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, select

from infrastructure.base_de_datos.tablas import eventos
from tests.api.pasos import ASESOR, CAJA, DIAGNOSTICO, ID_TECNICO, TECNICO, expediente_de
from tests.datos_profesor.adaptador import OperacionDelProfesor

ROL_DEL_AUTORIZANTE = "Cliente"
MOTIVO_DE_CANCELACION = "El cliente desistió"
FORMA_DE_PAGO = "Tarjeta"


class PasoRechazado(Exception):
    """El sistema rechazó un paso: es el resultado que se compara con el oráculo."""

    def __init__(self, codigo: int, error: str, detalle: str) -> None:
        super().__init__(detalle)
        self.codigo = codigo
        self.error = error
        self.detalle = detalle


@dataclass(frozen=True)
class ResultadoDelFlujo:
    estado_final: str
    http: int
    error: str | None = None
    detalle: str | None = None


class Flujo:
    """Una orden del profesor recorriendo el taller: técnico 1 de demostración (D-06)."""

    def __init__(self, cliente: TestClient, operacion: OperacionDelProfesor) -> None:
        self._cliente = cliente
        self._operacion = operacion
        self._ruta = f"/api/ordenes/{operacion.operacion_id}"
        self._ultimo_codigo = 0
        self.id_cotizacion = ""
        self.total = ""

    def ejecutar(self, accion: Callable[[], None]) -> ResultadoDelFlujo:
        numero = self._operacion.operacion_id
        try:
            accion()
        except PasoRechazado as rechazo:
            estado = expediente_de(self._cliente, numero)["estado"]
            return ResultadoDelFlujo(estado, rechazo.codigo, rechazo.error, rechazo.detalle)
        estado = expediente_de(self._cliente, numero)["estado"]
        return ResultadoDelFlujo(estado, self._ultimo_codigo)

    # ------------------------------------------------------------- acciones del profesor
    def completar(self) -> None:
        self.aprobar()
        self.asignar_trabajos()
        for id_trabajo in self._operacion.ids_de_trabajos:
            self._post(f"{self._ruta}/trabajos/{id_trabajo}/inicio", TECNICO, 200)
            self._post(f"{self._ruta}/trabajos/{id_trabajo}/completado", TECNICO, 200)
        self._post(f"{self._ruta}/pago", CAJA, 201, {"monto": self.total, "forma": FORMA_DE_PAGO})
        self._entregar()

    def cancelar(self) -> None:
        cuerpo = {"motivo": MOTIVO_DE_CANCELACION}
        self._post(f"{self._ruta}/cancelacion", ASESOR, 200, cuerpo)

    def repetir_aprobacion(self) -> None:
        self.aprobar()
        self._registrar_decision()

    def saltar_estado(self) -> None:
        self._entregar()

    def aprobar(self) -> None:
        cuerpo = {"tecnico": ID_TECNICO}
        self._post(f"{self._ruta}/asignacion-diagnostico", ASESOR, 200, cuerpo)
        self._post(f"{self._ruta}/diagnostico", TECNICO, 201, DIAGNOSTICO)
        cotizacion = self._post(
            f"{self._ruta}/cotizaciones", ASESOR, 201, self._operacion.trabajos()
        )
        self.id_cotizacion = cotizacion["id"]
        self.total = cotizacion["total"]
        self._post(f"/api/cotizaciones/{self.id_cotizacion}/presentacion", ASESOR, 200)
        self._registrar_decision()

    # ------------------------------------------------------------- pasos
    def asignar_trabajos(self) -> None:
        cuerpo = {"ids_trabajos": self._operacion.ids_de_trabajos, "tecnico": ID_TECNICO}
        self._post(f"{self._ruta}/asignacion-trabajos", ASESOR, 200, cuerpo)

    def entregar_sin_reparacion(self) -> None:
        self._post(f"{self._ruta}/entrega-sin-reparacion", ASESOR, 200)

    def _entregar(self) -> None:
        self._post(f"{self._ruta}/entrega", ASESOR, 200)

    def _registrar_decision(self) -> None:
        lineas = self._operacion.ids_de_trabajos if self._operacion.autorizado else []
        cuerpo = {
            "lineas_autorizadas": lineas,
            "nombre_del_autorizante": self._operacion.nombre_del_actor,
            "rol_del_autorizante": ROL_DEL_AUTORIZANTE,
        }
        self._post(f"/api/cotizaciones/{self.id_cotizacion}/decision", ASESOR, 200, cuerpo)

    def _post(
        self,
        ruta: str,
        encabezados: dict[str, str],
        codigo: int,
        cuerpo: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        respuesta = self._cliente.post(ruta, json=cuerpo, headers=encabezados)
        if respuesta.status_code != codigo:
            datos = respuesta.json()
            raise PasoRechazado(respuesta.status_code, datos["error"], datos["detalle"])
        self._ultimo_codigo = respuesta.status_code
        return respuesta.json()


def eventos_de_la_bitacora(motor: Engine) -> list[str]:
    with motor.connect() as conexion:
        consulta = select(eventos.c.tipo).order_by(eventos.c.id)
        return list(conexion.execute(consulta).scalars())
