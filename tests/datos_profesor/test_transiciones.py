"""Las 20 transiciones de `transiciones_prueba.csv` contra su oráculo (datos-profesor §6)."""
from __future__ import annotations

import re
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from tests.datos_profesor.adaptador import (
    DATOS,
    ORACULOS,
    cargar_operacion,
    leer_csv,
    leer_operaciones,
)
from tests.datos_profesor.flujos import Flujo, ResultadoDelFlujo, eventos_de_la_bitacora
from tests.datos_profesor.reporte import Reporte

CASOS = leer_csv(DATOS / "transiciones_prueba.csv")
ORACULOS_DE_TRANSICIONES = {
    fila["caso_id"]: fila for fila in leer_csv(ORACULOS / "oraculos_transiciones.csv")
}
OPERACIONES = leer_operaciones()
CADENA_DE_AUT_O001 = [
    "TecnicoAsignadoParaDiagnostico",
    "DiagnosticoRegistrado",
    "CotizacionGenerada",
    "CotizacionPresentada",
    "CotizacionAutorizada",
    "OrdenAutorizada",
    "TrabajosAsignados",
    "TrabajoIniciado",
    "TrabajoIniciado",
    "OrdenListaParaEntrega",
    "PagoRegistrado",
    "VehiculoEntregado",
]


def _nombres_del_oraculo(texto: str) -> list[str]:
    """`VehiculoEntregado (cadena completa)` → [VehiculoEntregado]; `A + B` → [A, B]."""
    return re.findall(r"[A-Z]\w+", texto.split("(")[0])


def _accion(flujo: Flujo, nombre: str) -> Callable[[], None]:
    acciones = {
        "completar": flujo.completar,
        "cancelar": flujo.cancelar,
        "repetir_aprobacion": flujo.repetir_aprobacion,
        "saltar_estado": flujo.saltar_estado,
        "aprobar": flujo.aprobar,
    }
    return acciones[nombre]


def _coincide(
    oraculo: dict[str, str], resultado: ResultadoDelFlujo, eventos: list[str]
) -> bool:
    nombres = _nombres_del_oraculo(oraculo["evento_o_excepcion"])
    obtenidos = nombres == [resultado.error] if resultado.error else set(nombres) <= set(eventos)
    return (
        obtenidos
        and resultado.estado_final == oraculo["estado_final_esperado"]
        and resultado.http == int(oraculo["http"])
    )


@pytest.mark.parametrize("caso", CASOS, ids=lambda caso: caso["caso_id"])
def test_transicion_del_profesor(
    caso: dict[str, str],
    cliente: TestClient,
    motor: Engine,
    reporte_de_transiciones: Reporte,
    request: pytest.FixtureRequest,
) -> None:
    oraculo = ORACULOS_DE_TRANSICIONES[caso["caso_id"]]
    assert (caso["operacion_id"], caso["accion_sugerida"]) == (
        oraculo["operacion_id"],
        oraculo["accion"],
    )
    operacion = OPERACIONES[caso["operacion_id"]]
    cargar_operacion(motor, operacion)
    flujo = Flujo(cliente, operacion)

    resultado = flujo.ejecutar(_accion(flujo, caso["accion_sugerida"]))

    eventos = eventos_de_la_bitacora(motor)
    coincide = _coincide(oraculo, resultado, eventos)
    reporte_de_transiciones.anotar(
        caso["caso_id"],
        {
            **caso,
            "resultado_alumno": resultado.estado_final,
            "estado_final": resultado.estado_final,
            "evento_o_excepcion": resultado.error or " > ".join(eventos),
            "http": str(resultado.http),
            "coincide": "SI" if coincide else "NO",
            "prueba": request.node.name,
            "mensaje_del_dominio": resultado.detalle or "",
        },
    )

    assert coincide, f"{resultado} con eventos {eventos}; oráculo: {oraculo}"


def test_cadena_completa_de_eventos_al_completar(cliente: TestClient, motor: Engine) -> None:
    operacion = OPERACIONES["AUT-O001"]
    cargar_operacion(motor, operacion)
    flujo = Flujo(cliente, operacion)

    resultado = flujo.ejecutar(flujo.completar)

    assert resultado.estado_final == "Cerrada"
    assert eventos_de_la_bitacora(motor) == CADENA_DE_AUT_O001


def test_los_casos_coinciden_con_sus_oraculos() -> None:
    assert len(CASOS) == 20
    assert {caso["caso_id"] for caso in CASOS} == set(ORACULOS_DE_TRANSICIONES)
