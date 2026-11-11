"""La página del taller la sirve el mismo FastAPI sin cambiar la API (ADR-017, Fase 15).

Lo que solo se ve en el navegador se revisa a mano en la Fase 18; aquí se prueba que la página
llega completa, que sus módulos se encuentran entre sí y que no trae claves escritas.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.interfaz import CARPETA_WEB
from tests.api.pasos import TOKENS

RAIZ = Path(__file__).resolve().parents[2]
ARCHIVOS = sorted(archivo.name for archivo in CARPETA_WEB.iterdir() if archivo.is_file())
MODULOS = [nombre for nombre in ARCHIVOS if nombre.endswith(".js")]
PUESTOS = ["asesor.js", "tecnico.js", "gerente.js", "compras.js", "caja.js"]
TIPOS = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}
IMPORTACION = re.compile(r'import\s*\{([^}]*)\}\s*from\s*"\./([^"]+)"')
EXPORTACION = re.compile(r"export\s+(?:async\s+)?(?:function|const|let|class)\s+(\w+)")
LLAMADA = re.compile(r'pedir\(\s*"(GET|POST|PUT|DELETE)",\s*"(/api/[^"]+)"')
RUTA_NO_ENCONTRADA = {
    "error": "RutaNoEncontrada",
    "detalle": "No encontramos lo que busca. Revise la dirección e intente de nuevo.",
    "codigo": 404,
}


def _texto(nombre: str) -> str:
    return (CARPETA_WEB / nombre).read_text(encoding="utf-8")


def test_la_raiz_entrega_la_pagina(cliente: TestClient) -> None:
    respuesta = cliente.get("/")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert respuesta.headers["cache-control"] == "no-cache"
    assert "<title>AutoFix Pro</title>" in respuesta.text


def test_la_pagina_carga_sus_estilos_y_su_modulo_principal() -> None:
    referencias = re.findall(r'(?:href|src)="/web/([^"]+)"', _texto("index.html"))

    assert set(referencias) == {"estilos.css", "principal.js"}


@pytest.mark.parametrize("nombre", ARCHIVOS)
def test_cada_archivo_de_la_pagina_se_sirve_con_su_tipo(cliente: TestClient, nombre: str) -> None:
    respuesta = cliente.get(f"/web/{nombre}")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith(TIPOS[Path(nombre).suffix])
    assert respuesta.headers["cache-control"] == "no-cache"


@pytest.mark.parametrize("nombre", MODULOS)
def test_cada_modulo_importa_modulos_que_existen(nombre: str) -> None:
    importados = re.findall(r'from\s*"\./([^"]+)"', _texto(nombre))

    assert [modulo for modulo in importados if modulo not in MODULOS] == []


@pytest.mark.parametrize("nombre", MODULOS)
def test_cada_modulo_importa_lo_que_otro_modulo_exporta(nombre: str) -> None:
    for nombres, modulo in IMPORTACION.findall(_texto(nombre)):
        exportados = set(EXPORTACION.findall(_texto(modulo)))
        importados = {parte.strip() for parte in nombres.split(",") if parte.strip()}
        assert importados <= exportados, f"{nombre} importa de {modulo}: {importados - exportados}"


@pytest.mark.parametrize("nombre", PUESTOS)
def test_cada_puesto_tiene_menu_con_direcciones_documentadas(nombre: str) -> None:
    texto = _texto(nombre)
    documentadas = set(re.findall(r"`(#/[^`]+)`", _seccion_de_navegacion()))
    direcciones = re.findall(r'direccion:\s*"([^"]+)"', texto)

    assert {"MENU", "mostrar"} <= set(EXPORTACION.findall(texto))
    assert direcciones, f"{nombre} no tiene menú"
    assert set(direcciones) <= documentadas


def _seccion_de_navegacion() -> str:
    texto = (RAIZ / "docs/interfaz-web.md").read_text(encoding="utf-8")
    return texto.split("## 3. Sesión y navegación")[1].split("## 4.")[0]


def _rutas_que_usa(nombre: str) -> set[tuple[str, str]]:
    """Las llamadas `pedir("POST", "/api/ordenes/{numero}/entrega", …)` de un módulo."""
    return set(LLAMADA.findall(_texto(nombre)))


@pytest.mark.parametrize("nombre", MODULOS)
def test_la_pagina_solo_llama_rutas_que_existen_en_la_api(
    cliente: TestClient, nombre: str
) -> None:
    contrato = cliente.get("/openapi.json").json()["paths"]
    llamadas = _rutas_que_usa(nombre)

    faltantes = {
        (metodo, ruta)
        for metodo, ruta in llamadas
        if metodo.lower() not in contrato.get(ruta, {})
    }
    assert faltantes == set()


@pytest.mark.parametrize(
    ("nombre", "seccion_inicial", "seccion_final"),
    [
        ("asesor.js", "### 4.2 Asesor de Servicio", "### 4.3"),
        ("expediente.js", "### 4.2 Asesor de Servicio", "### 4.3"),
        ("tecnico.js", "### 4.3 Técnico", "### 4.4"),
        ("gerente.js", "### 4.4 Gerente de Taller", "### 4.5"),
        ("compras.js", "### 4.5 Personal de Compras", "### 4.6"),
        ("caja.js", "### 4.6 Personal de Caja", "### 4.7"),
        ("alertas.js", "### 4.1 Públicas y comunes", "### 4.2"),
    ],
)
def test_las_rutas_de_cada_puesto_estan_en_interfaz_web(
    nombre: str, seccion_inicial: str, seccion_final: str
) -> None:
    """Regla 1 de CLAUDE.md: cada botón de un puesto usa una ruta de la tabla de su sección."""
    texto = (RAIZ / "docs/interfaz-web.md").read_text(encoding="utf-8")
    seccion = texto.split(seccion_inicial)[1].split(seccion_final)[0]
    llamadas = _rutas_que_usa(nombre)

    # La tabla escribe algunas rutas con sus parámetros: `GET /api/clientes?tipo=Flotilla&empresa=`.
    documentadas = {
        f"{metodo} {ruta}"
        for metodo, ruta in llamadas
        if f"`{metodo} {ruta}`" in seccion or f"`{metodo} {ruta}?" in seccion
    }

    assert llamadas, f"{nombre} no llama a la API"
    assert {f"{metodo} {ruta}" for metodo, ruta in llamadas} - documentadas == set()


@pytest.mark.parametrize("nombre", ARCHIVOS)
def test_la_pagina_no_trae_claves_escritas(nombre: str) -> None:
    """Regla 5 de CLAUDE.md: la clave la escribe el empleado; nunca va en el código."""
    texto = _texto(nombre)

    assert "TOKEN_" not in texto
    assert [clave for clave in TOKENS.values() if clave in texto] == []
    # La única clave que va después de «Bearer» es la que escribió el empleado: `${clave}`.
    assert re.findall(r"Bearer\s+(?!\$\{)\S+", texto) == []


@pytest.mark.parametrize("direccion", ["/web/no-existe.js", "/api/no-existe", "/no-existe"])
def test_una_direccion_que_no_existe_responde_el_error_de_siempre(
    cliente: TestClient, direccion: str
) -> None:
    respuesta = cliente.get(direccion)

    assert respuesta.status_code == 404
    assert respuesta.json() == RUTA_NO_ENCONTRADA


def test_docs_openapi_y_health_siguen_respondiendo(cliente: TestClient) -> None:
    assert cliente.get("/docs").status_code == 200
    assert cliente.get("/openapi.json").status_code == 200
    assert cliente.get("/health").json() == {"estado": "ok"}


def test_la_pagina_no_aparece_en_swagger(cliente: TestClient) -> None:
    rutas = cliente.get("/openapi.json").json()["paths"]

    assert [ruta for ruta in rutas if ruta == "/" or ruta.startswith("/web")] == []
