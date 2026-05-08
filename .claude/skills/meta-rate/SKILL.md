---
name: meta-rate
description: Trackea el rate-limit de Meta Marketing API en esta carpeta (dev tier 60 pts / 300s sliding window). Cada llamada a graph.facebook.com debe sumar puntos (GET=1, POST/PUT/DELETE=3) y dibujar la barra. Activate cuando hagas o vayas a hacer una llamada a la Marketing API desde esta carpeta.
---

# meta-rate

Tracker local del rate-limit de Marketing API a nivel cuenta de anuncios.

## Reglas (Meta dev tier)

- Max score: **60 puntos** en ventana deslizante de **300 segundos**
- GET / HEAD = **1 punto** (read)
- POST / PUT / DELETE / PATCH = **3 puntos** (write)
- Si llegas a 60 → bloqueo de 300s con error `17` o `613`

## Comandos

```bash
.claude/skills/meta-rate/bin/meta-rate add GET /act_xxx/campaigns
.claude/skills/meta-rate/bin/meta-rate add POST /act_xxx/campaigns
.claude/skills/meta-rate/bin/meta-rate show
.claude/skills/meta-rate/bin/meta-rate log
.claude/skills/meta-rate/bin/meta-rate reset
```

Estado: `.meta-api-points.log` en el cwd actual.

## Cómo usarlo (instrucciones para Claude)

Cada vez que hagas una llamada HTTP a `graph.facebook.com` desde esta carpeta:

1. **Antes de la llamada:** corre `bin/meta-rate show`. Si total ≥ 55, advierte al usuario antes de seguir.
2. **Si total ≥ 60:** parate. Decile al usuario cuántos segundos faltan para que decaiga.
3. **Después de cada llamada (exitosa o no):** corre `bin/meta-rate add <METHOD> <endpoint>` con el método HTTP que usaste. Imprime la barra que devuelve.
4. Si una sola operación lógica hace varias llamadas (ej: paginar, batch), suma cada llamada por separado.

## Plan de capacidad antes de operaciones grandes

**Antes de iniciar cualquier operación que vaya a hacer más de 1 llamada**, calcula los puntos totales que va a costar (GET=1, POST/PUT/DELETE=3) y compáralo con los puntos disponibles según `bin/meta-rate show`.

**Si la operación NO cabe en los puntos disponibles**, NO la ejecutes. Pregunta al usuario cuál de estas 3 opciones prefiere, mostrándole los números reales:

- **A) Esperar y crear todo desde 0:** dile cuántos segundos/minutos faltan para que la ventana decaiga lo suficiente (o se vacíe completa) y luego ejecutar la operación entera.
- **B) Parcial ahora + resto después:** cuántas llamadas alcanzas a hacer ahora hasta llegar a 60, pausa automática mientras la ventana decae, y luego completa el resto. Tú gestionas la pausa con `ScheduleWakeup` o equivalente.
- **C) Cancelar:** no hacer nada.

Ejemplo de cómo plantear la pregunta:
> "Esta operación cuesta 45 pts. Llevas 30/60, solo caben 30 pts (10 llamadas POST). Opciones:
> A) Esperar ~3 min y crearlo todo de una.
> B) Crear 10 ahora, esperar 3 min, crear las 5 restantes.
> C) Cancelar."

**Si el usuario ya autorizó parcial:** ejecuta hasta llegar a 58 pts (margen de 2), corre `bin/meta-rate show` para saber cuándo decae el primer paquete, espera ese tiempo + 5s extra, y reanuda con las llamadas faltantes. Mantén un registro mental de qué se creó y qué falta para no duplicar.

**Llamadas que no caben individualmente** (ej: 1 sola request POST cuando llevas 58/60): igual aplica, espera o cancela — no hay "parcial" para 1 sola llamada.

## Ejemplo de flujo

```bash
# Antes
$ .claude/skills/meta-rate/bin/meta-rate show
[████░░░░░░░░░░░░░░░░░░░░░░░░░░] 8/60 pts · decae en 180s

# Llamada
$ curl -G "https://graph.facebook.com/v21.0/act_xxx/campaigns" ...

# Después
$ .claude/skills/meta-rate/bin/meta-rate add GET /act_xxx/campaigns
[████▌░░░░░░░░░░░░░░░░░░░░░░░░░] 9/60 pts · decae en 180s
```

## Cuándo NO sumar

- Llamadas a otros dominios (no `graph.facebook.com`)
- Llamadas dentro de batch endpoint (cuentan como 1 sola)
- Endpoints que devuelvan `error.code: 17 / 613` (no se cobraron)
