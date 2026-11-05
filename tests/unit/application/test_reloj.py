"""Reloj real del sistema."""
from __future__ import annotations

from datetime import UTC
from unittest.mock import patch
from zoneinfo import ZoneInfo

from infrastructure.reloj import RelojDelSistema
from tests.unit.application.escenarios import AHORA


def test_ahora_esta_en_utc() -> None:
    assert RelojDelSistema().ahora().tzinfo is UTC


def test_hora_del_taller_es_el_mismo_instante_en_la_zona_configurada() -> None:
    reloj = RelojDelSistema("America/Monterrey")

    with patch.object(RelojDelSistema, "ahora", return_value=AHORA):
        en_el_taller = reloj.ahora_en_el_taller()

    assert en_el_taller == AHORA
    assert en_el_taller.tzinfo == ZoneInfo("America/Monterrey")
    assert en_el_taller.hour == 9
