"""Base de los Domain Events y de las raíces de Aggregate (ADR-016)."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime

import pytest

from domain.compartido.errores import ValorInvalido
from domain.compartido.eventos import EventoDeDominio, RaizDeAgregado

MOMENTO = datetime(2026, 10, 12, 15, 0, tzinfo=UTC)


@dataclass(frozen=True)
class _EventoDePrueba(EventoDeDominio):
    folio: str


class _RaizDePrueba(RaizDeAgregado):
    def hacer_algo(self, folio: str) -> None:
        self._registrar(_EventoDePrueba(MOMENTO, folio))


def test_evento_es_inmutable() -> None:
    evento = _EventoDePrueba(MOMENTO, "AUT-O001")

    with pytest.raises(FrozenInstanceError):
        evento.folio = "AUT-O002"


def test_evento_exige_fecha_con_zona_horaria() -> None:
    with pytest.raises(ValorInvalido, match="zona horaria"):
        _EventoDePrueba(datetime(2026, 10, 12, 15, 0), "AUT-O001")


def test_raiz_registra_eventos_en_orden() -> None:
    raiz = _RaizDePrueba()

    raiz.hacer_algo("AUT-O001")
    raiz.hacer_algo("AUT-O002")

    assert [evento.folio for evento in raiz.extraer_eventos()] == ["AUT-O001", "AUT-O002"]


def test_extraer_eventos_vacia_la_lista() -> None:
    raiz = _RaizDePrueba()
    raiz.hacer_algo("AUT-O001")

    raiz.extraer_eventos()

    assert raiz.extraer_eventos() == []
