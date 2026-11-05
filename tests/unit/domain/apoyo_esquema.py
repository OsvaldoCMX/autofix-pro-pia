"""Lee los valores permitidos de `database/01_esquema.sql` para compararlos con los enums."""
from __future__ import annotations

import re
from pathlib import Path

ESQUEMA = Path(__file__).resolve().parents[3] / "database" / "01_esquema.sql"


def valores_del_check(tabla: str, columna: str) -> set[str]:
    """Devuelve los textos de `CHECK (columna IN (...))` de la tabla indicada."""
    sql = ESQUEMA.read_text(encoding="utf-8")
    definicion = re.search(rf"CREATE TABLE {tabla} \((.*?)\n\);", sql, re.DOTALL)
    assert definicion, f"No existe la tabla {tabla}"
    check = re.search(rf"CHECK \({columna}(?: IS NULL OR {columna})? IN \((.*?)\)\)", definicion[1])
    assert check, f"La tabla {tabla} no tiene CHECK para {columna}"
    return set(re.findall(r"'([^']*)'", check[1]))
