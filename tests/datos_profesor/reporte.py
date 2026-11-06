"""Escribe los resultados en `reportes/`, en el orden de los casos del profesor.

No lleva fechas: el mismo resultado siempre deja el mismo archivo. Solo se escribe si corrieron
todos los casos, para que un `pytest -k` no reemplace el reporte por uno parcial.
"""
from __future__ import annotations

import csv
from pathlib import Path


class Reporte:
    def __init__(self, ruta: Path, columnas: list[str], casos: list[str]) -> None:
        self._ruta = ruta
        self._columnas = columnas
        self._casos = casos
        self._filas: dict[str, dict[str, str]] = {}

    def anotar(self, caso_id: str, fila: dict[str, str]) -> None:
        self._filas[caso_id] = fila

    def escribir_si_esta_completo(self) -> None:
        if set(self._filas) != set(self._casos):
            return
        with self._ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
            escritor = csv.DictWriter(archivo, self._columnas, lineterminator="\n")
            escritor.writeheader()
            escritor.writerows(self._filas[caso] for caso in self._casos)
