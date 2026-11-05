"""Reloj real del sistema."""
from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from application.puertos import Reloj


class RelojDelSistema(Reloj):
    def __init__(self, zona: str = "America/Monterrey") -> None:
        self._zona = ZoneInfo(zona)

    def ahora(self) -> datetime:
        return datetime.now(UTC)

    def ahora_en_el_taller(self) -> datetime:
        return self.ahora().astimezone(self._zona)
