# Scripts de documentación y base de datos

Generan los documentos que deben coincidir entre sí, a partir de una sola fuente (`datos.py` y `rutas.py`):

| Script | Genera |
|---|---|
| `gen_historias.py docs` | `docs/user-stories.md` y `docs/gherkin/*.feature` |
| `gen_trazabilidad.py docs` | `docs/trazabilidad/matriz-trazabilidad.md` y `.xlsx`, `docs/api/README.md` |
| `gen_adr.py docs` | `docs/architecture/adr/*.md` |
| `gen_datos_profesor.py datos/profesor docs` | `docs/datos-profesor/` (README y oráculos CSV) |

Uso (desde la raíz del repositorio, requiere `openpyxl`):

```bash
python scripts/docs/gen_historias.py docs
python scripts/docs/gen_trazabilidad.py docs
python scripts/docs/gen_adr.py docs
python scripts/docs/gen_datos_profesor.py datos/profesor docs
```

Si cambia un criterio, una regla o una ruta, se edita `datos.py` o `rutas.py` y se vuelven a correr los scripts: cada uno valida que los conteos y las referencias cruzadas sigan cuadrando (por ejemplo, que cada criterio tenga necesidad, regla y ruta).

## Base de datos (`scripts/db/`)

| Script | Genera |
|---|---|
| `esquema.py .` | `database/01_esquema.sql`, `docs/architecture/modelo-de-datos.md` y `docs/architecture/diagramas/modelo-de-datos.puml` |
| `generar_datos_iniciales.py datos/profesor database` | `database/02_datos_iniciales.sql` y `database/03_verificacion.sql` |

```bash
python scripts/db/esquema.py .
python scripts/db/generar_datos_iniciales.py datos/profesor database
```

Si cambia una tabla, se edita `esquema.py` (no el SQL a mano), se regenera y se actualiza `src/infrastructure/base_de_datos/tablas.py` para que coincida.
