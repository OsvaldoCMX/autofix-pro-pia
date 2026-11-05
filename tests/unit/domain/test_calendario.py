"""CalendarioHabil: lunes a viernes, sin feriados. El umbral de 3 días se prueba con E7 (Fase 2)."""
from __future__ import annotations

from datetime import date

from domain.compartido.calendario import CalendarioHabil

LUNES = date(2026, 10, 12)
VIERNES = date(2026, 10, 16)
SABADO = date(2026, 10, 17)
LUNES_SIGUIENTE = date(2026, 10, 19)


def test_rn_11_calendario_no_cuenta_sabado_ni_domingo() -> None:
    assert CalendarioHabil().dias_habiles_entre(VIERNES, LUNES_SIGUIENTE) == 1


def test_rn_11_calendario_cuenta_desde_una_solicitud_en_fin_de_semana() -> None:
    assert CalendarioHabil().dias_habiles_entre(SABADO, LUNES_SIGUIENTE) == 1


def test_ca_021_dias_habiles_transcurridos_de_lunes_a_viernes() -> None:
    assert CalendarioHabil().dias_habiles_entre(LUNES, VIERNES) == 4


def test_calendario_mismo_dia_es_cero() -> None:
    assert CalendarioHabil().dias_habiles_entre(LUNES, LUNES) == 0


def test_calendario_fechas_invertidas_es_cero() -> None:
    assert CalendarioHabil().dias_habiles_entre(VIERNES, LUNES) == 0
