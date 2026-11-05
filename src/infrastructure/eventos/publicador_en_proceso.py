"""Entrega los eventos confirmados a sus manejadores, en el mismo proceso (ADR-016)."""
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from application.puertos import PublicadorDeEventos
from domain.compartido.eventos import EventoDeDominio

_bitacora = logging.getLogger(__name__)

Manejador = Callable[[Any], None]


class PublicadorEnProceso(PublicadorDeEventos):
    def __init__(self) -> None:
        self._manejadores: defaultdict[type[EventoDeDominio], list[Manejador]] = defaultdict(list)

    def suscribir(self, tipo: type[EventoDeDominio], manejador: Manejador) -> None:
        self._manejadores[tipo].append(manejador)

    def publicar(self, eventos: list[EventoDeDominio]) -> None:
        """Si un manejador falla, el cambio de negocio ya quedó: se registra y se sigue."""
        for evento in eventos:
            for manejador in self._manejadores[type(evento)]:
                try:
                    manejador(evento)
                except Exception:
                    _bitacora.exception("Falló un manejador de %s", type(evento).__name__)
