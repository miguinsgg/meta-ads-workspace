# Meta Ads Workspace

Workspace de [Claude Code](https://claude.com/claude-code) para operar tu cuenta
de anuncios de Meta directamente desde la terminal — listar campañas, sacar
métricas, crear presets de reportes — sin abrir Ads Manager.

Construido por [Ecom Circle](https://ecomcircle.com).

## ¿Qué incluye?

| Skill | Para qué sirve |
|---|---|
| `meta-rate` | Tracker local del rate-limit (60 pts / 300s en dev tier). Suma puntos por cada llamada y avisa antes de bloquearte. |
| `preset-metricas` | Subes un Excel exportado de Ads Manager y guarda las columnas como un preset reusable. Las próximas consultas salen con esa misma vista. |

## Requisitos

- [Claude Code](https://claude.com/claude-code) instalado
- Python 3 (incluido en macOS / Linux)
- Bash o zsh
- Token de acceso a Meta Marketing API ([cómo generarlo](#cómo-conseguir-el-access_token))

## Instalación

```bash
git clone <url-de-este-repo> meta-ads-workspace
cd meta-ads-workspace
cp .env.example .env
```

Editá `.env` con tus credenciales:

```
ACCESS_TOKEN=EAANeYY...
AD_ACCOUNT_ID=act_3282926935363592
```

Después abrí esta carpeta con Claude Code:

```bash
claude
```

Las skills se cargan solas desde `.claude/skills/`. Probá:

> "Listame todas mis campañas"

## Cómo conseguir el ACCESS_TOKEN

1. Ir a [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Seleccionar tu app (o crear una en [Meta for Developers](https://developers.facebook.com/apps/))
3. Permisos necesarios: `ads_read`, `ads_management`, `business_management`
4. Click en **Generate Access Token**
5. Copiar y pegar en `.env`

Tip: el token de la GUI dura ~1 hora. Para producción, intercambialo por uno de
larga duración (60 días) siguiendo
[esta guía](https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived).

## Cómo conseguir el AD_ACCOUNT_ID

En Ads Manager, arriba a la izquierda al lado del nombre de la cuenta — empieza
con `act_` seguido de 16 dígitos.

## Uso

Una vez configurado, escribile a Claude en lenguaje natural:

```
Listame todas mis campañas
Métricas de la campaña X últimos 7 días
Subir preset de métricas
Cuánto llevo gastado este mes
```

Claude invoca las skills automáticamente cuando hace falta.

### Crear un preset de métricas

1. En Ads Manager, exportá el reporte que querés replicar a Excel
2. Decile a Claude: **"subir preset"**
3. Pasale el path del `.xlsx`
4. Claude lee las columnas, mapea las que conoce, te pregunta por las desconocidas
5. Le ponés un nombre y queda guardado en `presets/metricas/<nombre>.json`

A partir de ahí, cuando pidas métricas de una campaña, Claude usa ese preset.

## Estructura

```
meta-ads-workspace/
├── .env                    ← tu config (gitignored)
├── .env.example            ← plantilla
├── .gitignore
├── README.md
├── .claude/
│   └── skills/
│       ├── meta-rate/      ← rate-limiter
│       └── preset-metricas/ ← ingesta de Excel
└── presets/
    └── metricas/           ← tus presets
```

## Compartir tus presets

Los presets son solo JSON. Si querés compartirlos con tu equipo o con la
comunidad, basta con que los commitees a tu fork del repo:

```bash
git add presets/metricas/mi_preset.json
git commit -m "preset: reporte WhatsApp Tepli"
git push
```

El `.env` está en `.gitignore` — tu token nunca se sube.

## Compatibilidad

- macOS / Linux: nativo
- Windows: requiere WSL o Git Bash (las skills usan bash)

## Seguridad

- **Nunca** commits tu `.env`. Si por accidente lo subiste, regenerá el token en
  Meta for Developers inmediatamente.
- El token tiene acceso a tu cuenta de anuncios — protegelo como una contraseña.

## Licencia

MIT
