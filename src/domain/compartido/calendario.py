"""Domain Service: cálculo de días hábiles para el plazo de refacciones."""
from __future__ import annotations

from datetime import date, timedelta

_SABADO = 5


class CalendarioHabil:
    """Cuenta días de lunes a viernes, sin feriados."""

    def dias_habiles_entre(self, inicio: date, fin: date) -> int:
        """Cuenta los días hábiles después de `inicio` y hasta `fin`, inclusive."""
        dias = 0
        actual = inicio
        while actual < fin:
            actual += timedelta(days=1)
            if actual.weekday() < _SABADO:
                dias += 1
        return dias
