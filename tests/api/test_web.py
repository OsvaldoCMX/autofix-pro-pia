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
RUTA_NO_ENCONTRADA = {
    "error": "RutaNoEncontrada",
    "detalle": "No encontramos lo que busca. Revise la dirección e intente de nuevo.",
    "codigo": 404,
}


def _texto(nombre: str) -> str:
    return (CARPETA_WEB / nombre).read_text(encoding="utf-8")


def _claves_de_ejemplo() -> set[str]:
    ejemplo = (RAIZ / ".env.example").read_text(encoding="utf-8")
    return set(TOKENS.values()) | set(re.findall(r"^TOKEN_\w+=(\S+)", ejemplo, re.MULTILINE))


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


@pytest.mark.parametrize("nombre", ARCHIVOS)
def test_la_pagina_no_trae_claves_escritas(nombre: str) -> None:
    """Regla 5 de CLAUDE.md: la clave la escribe el empleado; nunca va en el código."""
    texto = _texto(nombre)

    assert "TOKEN_" not in texto
    assert [clave for clave in _claves_de_ejemplo() if clave in texto] == []


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
