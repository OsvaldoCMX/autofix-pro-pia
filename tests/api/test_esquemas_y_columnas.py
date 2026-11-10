"""Un dato que no cabe en su columna responde 422 y nunca 500 (pendiente de la Fase 4).

SQLite no hace cumplir `VARCHAR(n)`, así que los límites se comparan directo con `tablas.py`: la
prueba falla aunque esta ejecución no use PostgreSQL.
"""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import Column

from api.esquemas.autorizacion import DatosDeDecision
from api.esquemas.comunes import ENTERO_MAXIMO, PATRON_DE_IMPORTE
from api.esquemas.cotizaciones import NuevaRefaccion
from api.esquemas.diagnostico import AsignacionDeDiagnostico
from api.esquemas.recepcion import NuevaOrden, NuevoCliente, NuevoVehiculo
from api.esquemas.refacciones import NuevaSolicitud
from api.esquemas.reparacion import AsignacionDeTrabajos
from infrastructure.base_de_datos.tablas import (
    clientes,
    cotizaciones,
    empleados,
    ordenes,
    refacciones_cotizadas,
    solicitudes_de_compra,
    trabajos,
    vehiculos,
)
from tests.api.pasos import (
    ASESOR,
    TECNICO,
    asignada,
    cotizada,
    datos_de_orden,
    decision,
    diagnosticada,
    exigir,
    recibida,
)

LIMITES = [
    (NuevoCliente, "nombre", clientes.c.nombre),
    (NuevoCliente, "telefono", clientes.c.telefono),
    (NuevoCliente, "correo", clientes.c.correo),
    (NuevoCliente, "empresa", clientes.c.empresa),
    (NuevoCliente, "responsable_nombre", clientes.c.responsable_nombre),
    (NuevoCliente, "responsable_telefono", clientes.c.responsable_telefono),
    (NuevoCliente, "responsable_correo", clientes.c.responsable_correo),
    (NuevoVehiculo, "vin", vehiculos.c.vin),
    (NuevoVehiculo, "marca", vehiculos.c.marca),
    (NuevoVehiculo, "modelo", vehiculos.c.modelo),
    (NuevaOrden, "id_cliente", ordenes.c.id_cliente),
    (AsignacionDeDiagnostico, "tecnico", empleados.c.id),
    (AsignacionDeTrabajos, "tecnico", empleados.c.id),
    (NuevaRefaccion, "descripcion", refacciones_cotizadas.c.descripcion),
    (NuevaSolicitud, "refaccion", solicitudes_de_compra.c.refaccion),
    (DatosDeDecision, "nombre_del_autorizante", cotizaciones.c.decision_autorizante),
]


def _largo_maximo(modelo: type[BaseModel], campo: str) -> int:
    propiedad = modelo.model_json_schema()["properties"][campo]
    opciones = propiedad.get("anyOf", [propiedad])
    return next(opcion["maxLength"] for opcion in opciones if opcion.get("type") == "string")


@pytest.mark.parametrize(
    ("modelo", "campo", "columna"),
    LIMITES,
    ids=[f"{modelo.__name__}.{campo}" for modelo, campo, _ in LIMITES],
)
def test_el_limite_del_esquema_coincide_con_su_columna(
    modelo: type[BaseModel], campo: str, columna: Column[Any]
) -> None:
    assert _largo_maximo(modelo, campo) == columna.type.length


def test_el_entero_maximo_es_el_de_postgresql() -> None:
    assert ENTERO_MAXIMO == 2**31 - 1


def test_el_patron_de_importe_cabe_en_numeric_12_2() -> None:
    columna = trabajos.c.importe.type

    assert columna.scale == 2
    assert PATRON_DE_IMPORTE == rf"^[0-9]{{1,{columna.precision - columna.scale}}}\.[0-9]{{2}}$"


CLIENTE_COMPLETO = {
    "nombre": "n" * 120,
    "tipo": "Flotilla",
    "telefono": "(81)--1234--5678----",
    "correo": "c" * 110 + "@correo.mx",
    "empresa": "e" * 120,
    "responsable_nombre": "r" * 120,
    "responsable_telefono": "(81)--2222--3333----",
    "responsable_correo": "o" * 110 + "@correo.mx",
}


def test_los_textos_justo_en_el_limite_se_guardan(cliente: TestClient) -> None:
    respuesta = cliente.post("/api/clientes", json=CLIENTE_COMPLETO, headers=ASESOR)

    assert respuesta.status_code == 201
    encontrados = exigir(cliente.get("/api/clientes", params={"tipo": "Flotilla"}, headers=ASESOR), 200)
    assert encontrados[0]["nombre"] == "n" * 120
    assert encontrados[0]["responsable_telefono"] == "(81)--2222--3333----"


@pytest.mark.parametrize(
    ("campo", "nombre_claro"),
    [
        ("nombre", "nombre"),
        ("telefono", "teléfono"),
        ("correo", "correo"),
        ("empresa", "empresa"),
        ("responsable_nombre", "nombre del Responsable de Flotilla"),
        ("responsable_telefono", "teléfono del Responsable de Flotilla"),
        ("responsable_correo", "correo del Responsable de Flotilla"),
    ],
)
def test_un_caracter_de_mas_en_el_cliente_responde_422(
    cliente: TestClient, campo: str, nombre_claro: str
) -> None:
    cuerpo = {**CLIENTE_COMPLETO, campo: CLIENTE_COMPLETO[campo] + "x"}

    respuesta = cliente.post("/api/clientes", json=cuerpo, headers=ASESOR)

    assert respuesta.status_code == 422
    assert f"«{nombre_claro}»" in respuesta.json()["detalle"]
    assert "caracteres" in respuesta.json()["detalle"]


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("marca", "m" * 61), ("modelo", "m" * 61), ("vin", "1" * 18), ("anio", 1899), ("anio", 2101)],
)
def test_datos_del_vehiculo_fuera_de_limite_responden_422(
    cliente: TestClient, campo: str, valor: object
) -> None:
    datos = datos_de_orden()
    datos["vehiculo"] = {**datos["vehiculo"], campo: valor}

    respuesta = cliente.post("/api/ordenes", json=datos, headers=ASESOR)

    assert respuesta.status_code == 422


@pytest.mark.parametrize(
    "cambios",
    [
        {"kilometraje": 2**31},
        {"id_cliente": "x" * 21},
        {"placas": "A" * 16},
        {"nivel_de_combustible": "Medio"},
        {"motivo_de_ingreso": "con\x00nulo"},
    ],
    ids=["kilometraje", "id_cliente", "placas", "combustible", "motivo_con_nulo"],
)
def test_datos_de_la_orden_fuera_de_limite_responden_422(
    cliente: TestClient, cambios: dict[str, object]
) -> None:
    respuesta = cliente.post("/api/ordenes", json=datos_de_orden(**cambios), headers=ASESOR)

    assert respuesta.status_code == 422


def test_tecnico_demasiado_largo_responde_422(cliente: TestClient) -> None:
    numero = recibida(cliente)

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/asignacion-diagnostico", json={"tecnico": "x" * 21}, headers=ASESOR
    )

    assert respuesta.status_code == 422


@pytest.mark.parametrize(
    "refaccion",
    [
        {"descripcion": "d" * 201, "cantidad": 1, "precio_unitario": "1.00"},
        {"descripcion": "Balata", "cantidad": 2**31, "precio_unitario": "1.00"},
    ],
    ids=["descripcion", "cantidad"],
)
def test_refaccion_cotizada_fuera_de_limite_responde_422(
    cliente: TestClient, refaccion: dict[str, object]
) -> None:
    numero = diagnosticada(cliente)
    cuerpo = {
        "trabajos": [
            {"numero": 1, "descripcion": "T", "mano_de_obra": "1.00", "refacciones": [refaccion]}
        ]
    }

    respuesta = cliente.post(f"/api/ordenes/{numero}/cotizaciones", json=cuerpo, headers=ASESOR)

    assert respuesta.status_code == 422


def test_importes_que_suman_mas_de_lo_que_cabe_responden_422(cliente: TestClient) -> None:
    numero = diagnosticada(cliente)
    cuerpo = {
        "trabajos": [
            {"numero": 1, "descripcion": "A", "mano_de_obra": "9999999999.99"},
            {"numero": 2, "descripcion": "B", "mano_de_obra": "9999999999.99"},
        ]
    }

    respuesta = cliente.post(f"/api/ordenes/{numero}/cotizaciones", json=cuerpo, headers=ASESOR)

    assert respuesta.status_code == 422
    assert "máximo" in respuesta.json()["detalle"]


def test_nombre_del_autorizante_demasiado_largo_responde_422(cliente: TestClient) -> None:
    _, id_cotizacion = cotizada(cliente)
    cuerpo = {**decision([1]), "nombre_del_autorizante": "n" * 121}

    respuesta = cliente.post(f"/api/cotizaciones/{id_cotizacion}/decision", json=cuerpo, headers=ASESOR)

    assert respuesta.status_code == 422


@pytest.mark.parametrize(
    "cambios",
    [{"refaccion": "r" * 201}, {"cantidad": 2**31}, {"cantidad": 0}, {"id_trabajo": 2**31}],
    ids=["refaccion", "cantidad_grande", "cantidad_cero", "id_trabajo"],
)
def test_solicitud_fuera_de_limite_responde_422(
    cliente: TestClient, cambios: dict[str, object]
) -> None:
    numero = asignada(cliente)
    cuerpo = {"id_trabajo": 1, "refaccion": "Balatas", "cantidad": 1, **cambios}

    respuesta = cliente.post(
        f"/api/ordenes/{numero}/solicitudes-de-compra", json=cuerpo, headers=TECNICO
    )

    assert respuesta.status_code == 422


def test_folio_con_caracter_nulo_en_la_consulta_publica_responde_422(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/consulta-de-estado?orden=OS%000001&placas=ABC123")

    assert respuesta.status_code == 422


def test_cotizacion_con_caracter_nulo_en_la_ruta_responde_422(cliente: TestClient) -> None:
    assert cliente.get("/api/cotizaciones/COT%000001", headers=ASESOR).status_code == 422
