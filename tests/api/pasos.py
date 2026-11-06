"""Tokens de prueba y pasos HTTP para llegar a cada estado, como lo haría el taller."""
from __future__ import annotations

from itertools import count
from typing import Any

from fastapi.testclient import TestClient

TOKENS = {
    "TOKEN_ASESOR": "token-asesor",
    "TOKEN_TECNICO": "token-tecnico",
    "TOKEN_TECNICO_2": "token-tecnico-2",
    "TOKEN_GERENTE": "token-gerente",
    "TOKEN_COMPRAS": "token-compras",
    "TOKEN_CAJA": "token-caja",
    "TOKEN_SISTEMA": "token-sistema",
}


def con_token(variable: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKENS[variable]}"}


ASESOR = con_token("TOKEN_ASESOR")
TECNICO = con_token("TOKEN_TECNICO")
OTRO_TECNICO = con_token("TOKEN_TECNICO_2")
GERENTE = con_token("TOKEN_GERENTE")
COMPRAS = con_token("TOKEN_COMPRAS")
CAJA = con_token("TOKEN_CAJA")
SISTEMA = con_token("TOKEN_SISTEMA")

ID_ASESOR = "EMP-001"
ID_TECNICO = "EMP-002"
ID_OTRO_TECNICO = "EMP-003"

CLIENTE_PARTICULAR = {
    "nombre": "Luis Peña",
    "telefono": "81-2222",
    "correo": "luis@correo.test",
}
CLIENTE_DE_FLOTILLA = {
    "nombre": "Transportes Norte SA",
    "tipo": "Flotilla",
    "telefono": "81-3333",
    "correo": "contacto@norte.test",
    "empresa": "Transportes Norte",
    "responsable_nombre": "Ana Torres",
    "responsable_telefono": "81-1111",
    "responsable_correo": "ana@norte.test",
}

DIAGNOSTICO = {"fallas": "Balatas gastadas", "recomendaciones": "Cambiar balatas"}
AUTORIZANTE_PARTICULAR = ("Luis Peña", "Cliente")
AUTORIZANTE_DE_FLOTILLA = ("Ana Torres", "Responsable de Flotilla")

_consecutivo = count(1)


def datos_de_orden(flotilla: bool = False, **cambios: Any) -> dict[str, Any]:
    """Cuerpo válido de `POST /api/ordenes`, con placas y VIN que no se repiten."""
    numero = next(_consecutivo)
    return {
        "placas": f"ABC{numero:03d}",
        "motivo_de_ingreso": "Ruido al frenar",
        "kilometraje": 45000,
        "nivel_de_combustible": "1/2",
        "vehiculo": {
            "vin": f"1HGCM82633A{numero:06d}",
            "marca": "Nissan",
            "modelo": "Versa",
            "anio": 2020,
        },
        "cliente": CLIENTE_DE_FLOTILLA if flotilla else CLIENTE_PARTICULAR,
        **cambios,
    }


def exigir(respuesta: Any, codigo: int) -> dict[str, Any]:
    """Un paso previo que falla debe detener la prueba con un mensaje claro."""
    assert respuesta.status_code == codigo, respuesta.text
    return respuesta.json()


def alertas_de(cliente: TestClient, encabezados: dict[str, str]) -> list[dict[str, Any]]:
    return exigir(cliente.get("/api/alertas", headers=encabezados), 200)


def tipos_de_alertas(cliente: TestClient, encabezados: dict[str, str]) -> list[str]:
    return [alerta["tipo"] for alerta in alertas_de(cliente, encabezados)]


def panel_de(cliente: TestClient, encabezados: dict[str, str]) -> list[dict[str, Any]]:
    return exigir(cliente.get("/api/tecnicos/me/panel", headers=encabezados), 200)


def expediente_de(cliente: TestClient, numero: str) -> dict[str, Any]:
    return exigir(cliente.get(f"/api/ordenes/{numero}", headers=ASESOR), 200)


# ------------------------------------------------------------------ pasos para llegar a un estado
def recibida(cliente: TestClient, flotilla: bool = False) -> str:
    cuerpo = datos_de_orden(flotilla)
    return exigir(cliente.post("/api/ordenes", json=cuerpo, headers=ASESOR), 201)["numero_orden"]


def en_diagnostico(
    cliente: TestClient, flotilla: bool = False, tecnico: str = ID_TECNICO
) -> str:
    numero = recibida(cliente, flotilla)
    exigir(
        cliente.post(
            f"/api/ordenes/{numero}/asignacion-diagnostico",
            json={"tecnico": tecnico},
            headers=ASESOR,
        ),
        200,
    )
    return numero


def diagnosticada(cliente: TestClient, flotilla: bool = False) -> str:
    numero = en_diagnostico(cliente, flotilla)
    exigir(cliente.post(f"/api/ordenes/{numero}/diagnostico", json=DIAGNOSTICO, headers=TECNICO), 201)
    return numero


def trabajos(*importes: str) -> dict[str, Any]:
    """Cuerpo de una cotización con un trabajo de mano de obra por importe."""
    return {
        "trabajos": [
            {"numero": numero, "descripcion": f"Trabajo {numero}", "mano_de_obra": importe}
            for numero, importe in enumerate(importes, start=1)
        ]
    }


def cotizada(
    cliente: TestClient, flotilla: bool = False, importes: tuple[str, ...] = ("1000.00", "2000.00")
) -> tuple[str, str]:
    """Devuelve el número de la orden y el id de su cotización inicial."""
    numero = diagnosticada(cliente, flotilla)
    cotizacion = exigir(
        cliente.post(f"/api/ordenes/{numero}/cotizaciones", json=trabajos(*importes), headers=ASESOR),
        201,
    )
    return numero, cotizacion["id"]


def por_aprobar(cliente: TestClient) -> tuple[str, str]:
    """Orden con una cotización inicial de $20,000 que espera al Gerente."""
    return cotizada(cliente, importes=("20000.00",))


def presentada(cliente: TestClient) -> tuple[str, str]:
    numero, id_cotizacion = cotizada(cliente)
    exigir(cliente.post(f"/api/cotizaciones/{id_cotizacion}/presentacion", headers=ASESOR), 200)
    return numero, id_cotizacion


def decision(lineas: list[int], flotilla: bool = False) -> dict[str, Any]:
    nombre, rol = AUTORIZANTE_DE_FLOTILLA if flotilla else AUTORIZANTE_PARTICULAR
    return {"lineas_autorizadas": lineas, "nombre_del_autorizante": nombre, "rol_del_autorizante": rol}


def decidir(
    cliente: TestClient, id_cotizacion: str, lineas: list[int], flotilla: bool = False
) -> dict[str, Any]:
    return exigir(
        cliente.post(
            f"/api/cotizaciones/{id_cotizacion}/decision",
            json=decision(lineas, flotilla),
            headers=ASESOR,
        ),
        200,
    )


def autorizada(
    cliente: TestClient, flotilla: bool = False, lineas: tuple[int, ...] = (1, 2)
) -> tuple[str, str]:
    numero, id_cotizacion = cotizada(cliente, flotilla)
    decidir(cliente, id_cotizacion, list(lineas), flotilla)
    return numero, id_cotizacion


def asignar(
    cliente: TestClient, numero: str, ids: tuple[int, ...] = (1, 2), tecnico: str = ID_TECNICO
) -> None:
    exigir(
        cliente.post(
            f"/api/ordenes/{numero}/asignacion-trabajos",
            json={"ids_trabajos": list(ids), "tecnico": tecnico},
            headers=ASESOR,
        ),
        200,
    )


def asignada(cliente: TestClient, flotilla: bool = False) -> str:
    """Orden «Autorizada» con los trabajos 1 y 2 asignados al técnico."""
    numero, _ = autorizada(cliente, flotilla)
    asignar(cliente, numero)
    return numero


def iniciar(cliente: TestClient, numero: str, id_trabajo: int = 1) -> None:
    exigir(cliente.post(f"/api/ordenes/{numero}/trabajos/{id_trabajo}/inicio", headers=TECNICO), 200)


def completar(cliente: TestClient, numero: str, id_trabajo: int = 1) -> None:
    exigir(
        cliente.post(f"/api/ordenes/{numero}/trabajos/{id_trabajo}/completado", headers=TECNICO),
        200,
    )


def en_reparacion(cliente: TestClient, flotilla: bool = False) -> str:
    """El trabajo 1 queda «En Progreso» y el 2 «Pendiente»."""
    numero = asignada(cliente, flotilla)
    iniciar(cliente, numero)
    return numero


def solicitar(cliente: TestClient, numero: str, id_trabajo: int = 2) -> int:
    respuesta = exigir(
        cliente.post(
            f"/api/ordenes/{numero}/solicitudes-de-compra",
            json={"id_trabajo": id_trabajo, "refaccion": "Balatas", "cantidad": 2},
            headers=TECNICO,
        ),
        201,
    )
    return respuesta["id_solicitud"]


def en_espera(cliente: TestClient) -> tuple[str, int]:
    """Orden «En Espera de Refacción» con una solicitud del trabajo 2."""
    numero = asignada(cliente)
    return numero, solicitar(cliente, numero)


def pausada(cliente: TestClient) -> tuple[str, int]:
    numero, id_solicitud = en_espera(cliente)
    exigir(cliente.post(f"/api/ordenes/{numero}/retiro", headers=ASESOR), 201)
    exigir(cliente.post(f"/api/ordenes/{numero}/retiro/firma", headers=ASESOR), 200)
    return numero, id_solicitud


def con_adicional(cliente: TestClient) -> tuple[str, str]:
    """Orden «En Reparación» con una cotización adicional v.2 de dos trabajos, sin decisión."""
    numero = en_reparacion(cliente)
    adicional = exigir(
        cliente.post(
            f"/api/ordenes/{numero}/cotizaciones-adicionales",
            json=trabajos("500.00", "700.00"),
            headers=ASESOR,
        ),
        201,
    )
    return numero, adicional["id"]


def revisar_plazos(cliente: TestClient) -> dict[str, Any]:
    return exigir(cliente.post("/api/revisiones/plazos", headers=SISTEMA), 200)
