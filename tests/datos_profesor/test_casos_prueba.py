"""Los 120 casos de `casos_prueba.csv` contra `oraculos_casos.csv` (datos-profesor §5)."""
from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from domain.compartido.errores import CotizacionSinTrabajos
from domain.compartido.valores import Dinero, NumeroOrden
from domain.cotizaciones.cotizacion import Cotizacion
from domain.cotizaciones.especificaciones import RequiereAprobacionGerencial
from domain.cotizaciones.linea_de_cotizacion import LineaDeCotizacion
from domain.cotizaciones.valores import TipoCotizacion, VersionCotizacion
from tests.api.pasos import ASESOR, exigir
from tests.datos_profesor.adaptador import (
    DATOS,
    ORACULOS,
    OperacionDelProfesor,
    cargar_operacion,
    leer_csv,
    leer_operaciones,
)
from tests.datos_profesor.flujos import Flujo
from tests.datos_profesor.reglas_de_referencia import (
    BENEFICIO_REFERENCIA,
    PUEDE_PROCESARSE,
    VALIDAR_OPERACION,
)
from tests.datos_profesor.reporte import Reporte

VERDADERO = "VERDADERO"
FALSO = "FALSO"
FECHA_DE_REFERENCIA = datetime(2026, 10, 26, 15, 0, tzinfo=UTC)
ORACULOS_DE_CASOS = {fila["caso_id"]: fila for fila in leer_csv(ORACULOS / "oraculos_casos.csv")}
CASOS = leer_csv(DATOS / "casos_prueba.csv")
OPERACIONES = leer_operaciones()
NO_AUTORIZADAS_COTIZABLES = sorted(
    numero
    for numero, operacion in OPERACIONES.items()
    if not operacion.autorizado
    and operacion.lineas
    and all(linea.habilitado for linea in operacion.lineas)
)


def _casos_de_tipo(tipo: str) -> list[dict[str, str]]:
    return [caso for caso in CASOS if caso["tipo_prueba"] == tipo]


def _texto(valor: bool) -> str:
    return VERDADERO if valor else FALSO


def _anotar(
    reporte: Reporte,
    caso: dict[str, str],
    nombre_de_prueba: str,
    obtenido: bool,
    referencia: bool,
    mensaje: str,
) -> None:
    oraculo = ORACULOS_DE_CASOS[caso["caso_id"]]
    coincide = (
        _texto(obtenido) == oraculo["esperado_autofix"]
        and _texto(referencia) == oraculo["referencia_profesor"]
    )
    reporte.anotar(
        caso["caso_id"],
        {
            **caso,
            "resultado_alumno": _texto(obtenido),
            "esperado_autofix": oraculo["esperado_autofix"],
            "referencia_profesor": oraculo["referencia_profesor"],
            "referencia_obtenida": _texto(referencia),
            "diferencia": oraculo["diferencia"],
            "coincide": "SI" if coincide else "NO",
            "prueba": nombre_de_prueba,
            "mensaje_del_dominio": mensaje,
        },
    )


@pytest.mark.parametrize(
    "caso", _casos_de_tipo("validar_operacion"), ids=lambda caso: caso["caso_id"]
)
def test_caso_validar_operacion(
    caso: dict[str, str],
    cliente: TestClient,
    motor: Engine,
    reporte_de_casos: Reporte,
    request: pytest.FixtureRequest,
) -> None:
    """El resultado sale del flujo real: VERDADERO solo si la orden llega a «Autorizada»."""
    operacion = OPERACIONES[caso["operacion_id"]]
    oraculo = ORACULOS_DE_CASOS[caso["caso_id"]]
    cargar_operacion(motor, operacion)
    flujo = Flujo(cliente, operacion)

    def recorrer() -> None:
        flujo.aprobar()
        if not operacion.autorizado:
            flujo.asignar_trabajos()

    resultado = flujo.ejecutar(recorrer)
    obtenido = resultado.estado_final == "Autorizada"
    referencia = PUEDE_PROCESARSE.es_satisfecha_por(operacion)
    mensaje = resultado.detalle or f"Orden «{resultado.estado_final}»: se puede reparar."
    _anotar(reporte_de_casos, caso, request.node.name, obtenido, referencia, mensaje)

    assert _texto(obtenido) == oraculo["esperado_autofix"], mensaje
    assert VALIDAR_OPERACION.es_satisfecha_por(operacion) is obtenido
    assert _texto(referencia) == oraculo["referencia_profesor"]
    assert bool(oraculo["diferencia"]) is (obtenido is not referencia)


@pytest.mark.parametrize(
    "caso", _casos_de_tipo("evaluar_beneficio"), ids=lambda caso: caso["caso_id"]
)
def test_caso_evaluar_beneficio(
    caso: dict[str, str], reporte_de_casos: Reporte, request: pytest.FixtureRequest
) -> None:
    """D-02: en AutoFix se evalúa E1 sobre una `Cotizacion` real; el beneficio es solo referencia."""
    operacion = OPERACIONES[caso["operacion_id"]]
    oraculo = ORACULOS_DE_CASOS[caso["caso_id"]]
    try:
        cotizacion = _cotizacion_de(operacion)
    except CotizacionSinTrabajos as error:
        obtenido, mensaje = False, str(error)
    else:
        obtenido = RequiereAprobacionGerencial().es_satisfecha_por(cotizacion)
        assert cotizacion.total.monto == operacion.total
        mensaje = f"Total {cotizacion.total.monto}: {'requiere' if obtenido else 'no requiere'} Gerente"
    referencia = BENEFICIO_REFERENCIA.es_satisfecha_por(operacion)
    _anotar(reporte_de_casos, caso, request.node.name, obtenido, referencia, mensaje)

    assert _texto(obtenido) == oraculo["esperado_autofix"], mensaje
    assert _texto(referencia) == oraculo["referencia_profesor"]


def _cotizacion_de(operacion: OperacionDelProfesor) -> Cotizacion:
    lineas = [
        LineaDeCotizacion(numero, linea.descripcion_de_trabajo, Dinero(linea.importe))
        for numero, linea in enumerate(operacion.lineas, start=1)
    ]
    return Cotizacion.generar(
        "COT-REFERENCIA",
        NumeroOrden(operacion.operacion_id),
        TipoCotizacion.INICIAL,
        VersionCotizacion(1),
        lineas,
        FECHA_DE_REFERENCIA,
    )


@pytest.mark.parametrize("numero", sorted(OPERACIONES))
def test_rn_23_total_del_profesor_con_decimal(numero: str) -> None:
    oraculo = ORACULOS_DE_CASOS[numero.replace("AUT-O", "AUT-B")]
    importe = re.search(r"\$([\d,]+\.\d{2})", oraculo["explicacion"])
    assert importe is not None
    assert OPERACIONES[numero].total == Decimal(importe.group(1).replace(",", ""))


def test_resumen_de_los_oraculos() -> None:
    """Los conteos publicados en datos-profesor §5."""
    assert {caso["caso_id"] for caso in CASOS} == set(ORACULOS_DE_CASOS)
    assert len(CASOS) == 120
    operaciones = list(OPERACIONES.values())
    autofix = [VALIDAR_OPERACION.es_satisfecha_por(operacion) for operacion in operaciones]
    profesor = [PUEDE_PROCESARSE.es_satisfecha_por(operacion) for operacion in operaciones]
    beneficio = [BENEFICIO_REFERENCIA.es_satisfecha_por(operacion) for operacion in operaciones]

    assert (sum(profesor), sum(autofix), sum(beneficio)) == (43, 46, 9)
    assert sum(a is p for a, p in zip(autofix, profesor, strict=True)) == 47
    assert max(operacion.total for operacion in operaciones) == Decimal("12887.00")


def test_hay_seis_operaciones_no_autorizadas_que_se_pueden_cotizar() -> None:
    assert len(NO_AUTORIZADAS_COTIZABLES) == 6


@pytest.mark.parametrize("numero", NO_AUTORIZADAS_COTIZABLES)
def test_ca_012_operaciones_no_autorizadas_quedan_rechazadas(
    numero: str, cliente: TestClient, motor: Engine
) -> None:
    operacion = OPERACIONES[numero]
    cargar_operacion(motor, operacion)
    flujo = Flujo(cliente, operacion)

    resultado = flujo.ejecutar(flujo.completar)

    cotizacion = exigir(cliente.get(f"/api/cotizaciones/{flujo.id_cotizacion}", headers=ASESOR), 200)
    assert cotizacion["estado"] == "Rechazada"
    assert resultado.estado_final == "Cotizada"
    assert (resultado.error, resultado.http) == ("TrabajoNoAutorizado", 409)


@pytest.mark.parametrize("numero", NO_AUTORIZADAS_COTIZABLES)
def test_ca_043_operaciones_no_autorizadas_se_entregan_sin_reparacion(
    numero: str, cliente: TestClient, motor: Engine
) -> None:
    operacion = OPERACIONES[numero]
    cargar_operacion(motor, operacion)
    flujo = Flujo(cliente, operacion)

    def recorrer() -> None:
        flujo.aprobar()
        flujo.entregar_sin_reparacion()

    resultado = flujo.ejecutar(recorrer)

    assert (resultado.estado_final, resultado.http) == ("Cerrada sin Reparación", 200)
