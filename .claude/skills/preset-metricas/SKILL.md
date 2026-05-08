---
name: preset-metricas
description: Ingesta un Excel exportado del Administrador de Anuncios de Meta y guarda las columnas como un preset reutilizable de métricas (no catálogo) en presets/metricas/<nombre>.json. Activate cuando el usuario diga "subir preset", "cargar preset", "subir excel", "subir reporte de métricas", "nuevo preset", o cuando pida el reporte/métricas de una campaña/anuncio (en ese caso ofrece subir un preset primero).
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# preset-metricas

Recibe un Excel del Administrador de Anuncios de Meta, lee sus columnas (que ya son la "vista" deseada), las mapea a campos de la Marketing API y guarda el preset en `presets/metricas/<nombre>.json`.

**Solo métricas.** No catálogo, audiencias, creativos, ni nada más.

## Cuándo activar este skill

### Trigger directo
- "subir preset" / "cargar preset" / "nuevo preset"
- "subir excel" / "cargar excel" / "subir reporte" / "subir reporte de métricas"
- "guardar este preset"

### Trigger indirecto (ofrecer al usuario)
Cuando el usuario pida métricas/reporte de una campaña, anuncio o conjunto de anuncios sin haber configurado un preset todavía:

> "dame el reporte de la campaña X"
> "muéstrame las métricas de Y"
> "sácame los números de la campaña Z"

En ese caso, **antes de seguir**, pregunta con `AskUserQuestion`:
- "¿Quieres subir un preset (Excel) primero para definir qué columnas mostrar?"
- Opciones: "Sí, subir preset" / "No, usar uno existente" / "No, seguir sin preset"

Si dice "Sí" → corre este workflow. Si dice "No" → sale del skill y deja que Claude responda como siempre.

## Workflow

### Paso 0 — Verificar herramienta
```bash
.claude/skills/preset-metricas/bin/ingest --help
```
Si falla, el skill no está bien instalado. Avisar al usuario.

### Paso 1 — Obtener el path del Excel

Si el usuario ya pasó el path en su mensaje, úsalo. Si no, pregúntale con `AskUserQuestion` o pídele que pegue el path absoluto.

### Paso 2 — Leer y matchear headers

```bash
.claude/skills/preset-metricas/bin/ingest match "<path_al_xlsx>"
```

Devuelve JSON con:
- `level`: `ad`, `adset`, `campaign` o `unknown`
- `count`: total columnas
- `matched`: cuántas matchearon contra el diccionario
- `unmatched`: lista de columnas sin mapeo
- `columns`: cada una con `{pos, name, mapping|null, suggestions[]}`

Muestra al usuario un resumen breve:
> "Detecté nivel **<level>** con **N columnas** (M matchearon, K sin mapear)."

### Paso 3 — Resolver columnas no mapeadas

Para cada columna en `unmatched`:

1. Mostrar las `suggestions` que devolvió el script.
2. Usar `AskUserQuestion` con 3 opciones:
   - Las 2-3 sugerencias top (si las hay)
   - "Es una columna calculada" → pedir fórmula
   - "Saltar esta columna" → no incluir en el preset

Cuando el usuario elige una sugerencia, copia el mapping de esa entrada del diccionario para esta columna. Si elige "Es calculada", arma `{source: "calc", formula: "<lo que diga el usuario>"}`. Si "Saltar", omite la columna de `columns`.

**Importante:** las columnas resueltas que sean nuevas (no existentes en `known-mappings.json`) deben incluirse luego en `new_mappings` cuando se llame `write --learn-mappings` (ver Paso 6).

### Paso 4 — Pedir nombre del preset

Con `AskUserQuestion` (o input directo):
- Pregunta: "¿Cómo lo llamamos?"
- Validación: solo `[a-zA-Z0-9_-]+` (el script lo valida también).
- Si ya existe `presets/metricas/<name>.json`, ofrecer:
  - "Sobreescribir" → pasar flag `--overwrite`
  - "Cambiar nombre" → volver a preguntar

Sugerencias de nombre que puedes proponer al usuario en base al filename (ej: `Tepli-3-Campañas-...xlsx` → sugerir `tepli_campañas` o `tepli_whatsapp`).

### Paso 5 — Pedir descripción corta (opcional)

Una línea explicando qué tablero es. Si el usuario no quiere, dejar vacío.

### Paso 6 — Construir el JSON y guardar

Estructura del preset (espejo de `~/Downloads/meta_ads_presets.json` que ya existe):

```json
{
  "name": "<nombre>",
  "description": "<descripción opcional>",
  "level": "ad|adset|campaign",
  "api_fields": ["spend", "impressions", "..."],
  "extra_from_ad_node": ["effective_status"],
  "extra_from_adset_node": ["daily_budget", "lifetime_budget"],
  "extra_from_campaign_node": [],
  "calculated": ["Hook rate", "Hold rate", "..."],
  "columns": [
    {"pos": 1, "name": "Inicio del informe", "source": "api", "field": "date_start"},
    ...
  ]
}
```

Reglas para construir:
- **`api_fields`**: set único (sin duplicados) de todos los `field` de columnas con `source: "api"`. Excluir los que tengan ` OR ` en el nombre (van en `extra_from_*_node`).
- **`extra_from_ad_node` / `extra_from_adset_node` / `extra_from_campaign_node`**: campos de columnas con `source: "ad_node" | "adset_node" | "campaign_node"`. Si el `field` tiene ` OR `, separar y agregar ambos.
- **`calculated`**: lista de nombres de columnas con `source: "calc"`.
- **`columns`**: en orden de `pos`, copiar del match output. Si hay `filter_action_type` en el mapping, mantenerlo.

Pasarlo al script por stdin:

```bash
echo '{"preset": {...}, "new_mappings": {...}}' | \
  .claude/skills/preset-metricas/bin/ingest write [--overwrite] [--learn-mappings]
```

- `--overwrite`: si ya existe.
- `--learn-mappings`: si hay nuevas columnas que el usuario mapeó, se persisten en `known-mappings.json` para futuros presets.

### Paso 7 — Confirmar al usuario

Mostrar el resumen que devuelve `write`:

> ✅ Preset guardado: `presets/metricas/<nombre>.json`
> · Nivel: <level>
> · Columnas: N
> · Campos API: M
> · Aprendí K nuevos mapeos para futuros presets

## Comandos útiles del script

```bash
# Ver presets ya guardados
.claude/skills/preset-metricas/bin/ingest list

# Sugerir mapeos para un header suelto (debug)
.claude/skills/preset-metricas/bin/ingest suggest "Costo por compra (COP)"

# Solo leer headers sin matchear (debug)
.claude/skills/preset-metricas/bin/ingest read "<path>"
```

## Notas importantes

- **No instalar dependencias.** El script usa solo stdlib (zipfile, xml.etree, difflib).
- **Working directory.** El script resuelve el destino (`presets/metricas/`) relativo a su propia ubicación, así que funciona desde cualquier `pwd` mientras la estructura `.claude/skills/preset-metricas/bin/ingest` esté intacta.
- **Excel con celdas combinadas o múltiples sheets.** El script lee el primer sheet, primera fila. Si el reporte tiene un sheet distinto al primero o headers en otra fila, avisar al usuario.
- **Filtros de attribution.** No se cambian: el preset usa `7d_click + 1d_view` por convención (heredado del meta_ads_presets.json original). Si el usuario pide otra ventana, anotarlo en la `description` del preset.
