"""
Meta Ads Manager
SDK: facebook-business (pip install facebook-business)
Cubre: campañas, métricas, creación/edición y audiencias.
"""

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.customaudience import CustomAudience
from facebook_business.adobjects.adsinsights import AdsInsights
import json

# ─────────────────────────────────────────
# CONFIGURACIÓN — rellena con tus datos
# ─────────────────────────────────────────
APP_ID       = "TU_APP_ID"
APP_SECRET   = "TU_APP_SECRET"
ACCESS_TOKEN = "TU_ACCESS_TOKEN"
AD_ACCOUNT_ID = "act_TU_AD_ACCOUNT_ID"   # Incluye el prefijo "act_"

# ─────────────────────────────────────────
# INICIALIZACIÓN
# ─────────────────────────────────────────
def init():
    FacebookAdsApi.init(APP_ID, APP_SECRET, ACCESS_TOKEN)
    return AdAccount(AD_ACCOUNT_ID)


# ════════════════════════════════════════════════════════════════
# 1. CAMPAÑAS — Listar
# ════════════════════════════════════════════════════════════════
def listar_campanas(account: AdAccount):
    """Lista todas las campañas con estado, presupuesto y objetivo."""
    print("\n═══ CAMPAÑAS ═══")
    campos = [
        Campaign.Field.id,
        Campaign.Field.name,
        Campaign.Field.status,
        Campaign.Field.objective,
        Campaign.Field.daily_budget,
        Campaign.Field.lifetime_budget,
        Campaign.Field.start_time,
        Campaign.Field.stop_time,
    ]
    campanas = account.get_campaigns(fields=campos)
    for c in campanas:
        presupuesto = (
            f"Diario: ${int(c.get('daily_budget', 0)) / 100:.2f}"
            if c.get('daily_budget')
            else f"Total: ${int(c.get('lifetime_budget', 0)) / 100:.2f}"
        )
        print(f"  [{c['status']}] {c['name']} (ID: {c['id']})")
        print(f"    Objetivo: {c.get('objective', 'N/A')} | {presupuesto}")
    return campanas


# ════════════════════════════════════════════════════════════════
# 2. MÉTRICAS / INSIGHTS
# ════════════════════════════════════════════════════════════════
def obtener_insights(account: AdAccount, fecha_inicio: str, fecha_fin: str, nivel: str = "campaign"):
    """
    Obtiene métricas para el rango de fechas indicado.
    nivel: 'account' | 'campaign' | 'adset' | 'ad'
    Fechas en formato YYYY-MM-DD.
    """
    print(f"\n═══ INSIGHTS ({nivel.upper()}) — {fecha_inicio} → {fecha_fin} ═══")
    campos = [
        AdsInsights.Field.campaign_name,
        AdsInsights.Field.adset_name,
        AdsInsights.Field.impressions,
        AdsInsights.Field.clicks,
        AdsInsights.Field.spend,
        AdsInsights.Field.cpc,
        AdsInsights.Field.cpm,
        AdsInsights.Field.ctr,
        AdsInsights.Field.reach,
        AdsInsights.Field.frequency,
        AdsInsights.Field.actions,          # conversiones, etc.
        AdsInsights.Field.purchase_roas,
    ]
    params = {
        "time_range": {"since": fecha_inicio, "until": fecha_fin},
        "level": nivel,
        "breakdowns": [],
    }
    insights = account.get_insights(fields=campos, params=params)
    for row in insights:
        nombre = row.get("campaign_name", "") or row.get("adset_name", "")
        gasto  = float(row.get("spend", 0))
        roas   = row.get("purchase_roas", [{}])
        roas_v = float(roas[0].get("value", 0)) if roas else 0.0
        print(f"\n  Campaña/AdSet: {nombre}")
        print(f"    Impresiones: {row.get('impressions', 0):>10}")
        print(f"    Clics:       {row.get('clicks', 0):>10}")
        print(f"    Alcance:     {row.get('reach', 0):>10}")
        print(f"    CTR:         {float(row.get('ctr', 0)):>9.2f}%")
        print(f"    CPM:         ${float(row.get('cpm', 0)):>9.2f}")
        print(f"    CPC:         ${float(row.get('cpc', 0)):>9.2f}")
        print(f"    Gasto:       ${gasto:>9.2f}")
        print(f"    ROAS:        {roas_v:>9.2f}x")
    return insights


# ════════════════════════════════════════════════════════════════
# 3. CREAR CAMPAÑA
# ════════════════════════════════════════════════════════════════
def crear_campana(account: AdAccount, nombre: str, objetivo: str = "OUTCOME_TRAFFIC",
                  presupuesto_diario_usd: float = 10.0, estado: str = "PAUSED"):
    """
    Crea una campaña nueva.
    objetivos comunes: OUTCOME_TRAFFIC | OUTCOME_LEADS | OUTCOME_SALES
                       OUTCOME_AWARENESS | OUTCOME_ENGAGEMENT | OUTCOME_APP_PROMOTION
    estado: PAUSED (recomendado para pruebas) | ACTIVE
    """
    print(f"\n═══ CREAR CAMPAÑA: {nombre} ═══")
    campana = account.create_campaign(
        fields=[Campaign.Field.id, Campaign.Field.name],
        params={
            Campaign.Field.name: nombre,
            Campaign.Field.objective: objetivo,
            Campaign.Field.status: estado,
            Campaign.Field.special_ad_categories: [],
            Campaign.Field.daily_budget: int(presupuesto_diario_usd * 100),  # en centavos
        }
    )
    print(f"  ✓ Campaña creada — ID: {campana['id']}")
    return campana


# ════════════════════════════════════════════════════════════════
# 4. CREAR CONJUNTO DE ANUNCIOS (Ad Set)
# ════════════════════════════════════════════════════════════════
def crear_conjunto(account: AdAccount, campana_id: str, nombre: str,
                   pais: str = "US", presupuesto_diario_usd: float = 5.0,
                   fecha_inicio: str = None, fecha_fin: str = None):
    """
    Crea un Ad Set dentro de una campaña.
    pais: código ISO-3166-1 alpha-2, ej. 'US', 'MX', 'ES', 'AR'
    Fechas: formato YYYY-MM-DD
    """
    from datetime import date
    inicio = fecha_inicio or str(date.today())

    print(f"\n═══ CREAR AD SET: {nombre} ═══")
    params = {
        AdSet.Field.name: nombre,
        AdSet.Field.campaign_id: campana_id,
        AdSet.Field.daily_budget: int(presupuesto_diario_usd * 100),
        AdSet.Field.billing_event: AdSet.BillingEvent.impressions,
        AdSet.Field.optimization_goal: AdSet.OptimizationGoal.link_clicks,
        AdSet.Field.bid_strategy: AdSet.BidStrategy.lowest_cost_without_cap,
        AdSet.Field.targeting: {
            "geo_locations": {"countries": [pais]},
            "age_min": 18,
            "age_max": 65,
        },
        AdSet.Field.status: AdSet.Status.paused,
        AdSet.Field.start_time: inicio,
    }
    if fecha_fin:
        params[AdSet.Field.end_time] = fecha_fin

    conjunto = account.create_ad_set(
        fields=[AdSet.Field.id, AdSet.Field.name],
        params=params
    )
    print(f"  ✓ Ad Set creado — ID: {conjunto['id']}")
    return conjunto


# ════════════════════════════════════════════════════════════════
# 5. EDITAR CAMPAÑA (pausar / activar / cambiar presupuesto)
# ════════════════════════════════════════════════════════════════
def editar_campana(campana_id: str, nuevo_estado: str = None,
                   nuevo_presupuesto_diario_usd: float = None):
    """
    Modifica una campaña existente.
    nuevo_estado: 'ACTIVE' | 'PAUSED' | 'DELETED'
    """
    print(f"\n═══ EDITAR CAMPAÑA ID: {campana_id} ═══")
    campana = Campaign(campana_id)
    params = {}
    if nuevo_estado:
        params[Campaign.Field.status] = nuevo_estado
    if nuevo_presupuesto_diario_usd:
        params[Campaign.Field.daily_budget] = int(nuevo_presupuesto_diario_usd * 100)

    campana.api_update(params=params)
    print(f"  ✓ Campaña actualizada: {params}")


# ════════════════════════════════════════════════════════════════
# 6. AUDIENCIAS — Listar
# ════════════════════════════════════════════════════════════════
def listar_audiencias(account: AdAccount):
    """Lista las audiencias personalizadas de la cuenta."""
    print("\n═══ AUDIENCIAS PERSONALIZADAS ═══")
    campos = [
        CustomAudience.Field.id,
        CustomAudience.Field.name,
        CustomAudience.Field.subtype,
        CustomAudience.Field.approximate_count_lower_bound,
        CustomAudience.Field.approximate_count_upper_bound,
        CustomAudience.Field.description,
    ]
    audiencias = account.get_custom_audiences(fields=campos)
    for a in audiencias:
        bajo  = a.get("approximate_count_lower_bound", 0)
        alto  = a.get("approximate_count_upper_bound", 0)
        print(f"  [{a.get('subtype')}] {a['name']} (ID: {a['id']})")
        print(f"    Tamaño estimado: {bajo:,} – {alto:,} personas")
    return audiencias


# ════════════════════════════════════════════════════════════════
# 7. AUDIENCIA PERSONALIZADA — Crear desde lista de emails
# ════════════════════════════════════════════════════════════════
def crear_audiencia_custom(account: AdAccount, nombre: str,
                           emails: list[str], descripcion: str = ""):
    """
    Crea una audiencia personalizada a partir de una lista de emails.
    Meta los hashea automáticamente (SHA-256) antes de subirlos.
    """
    import hashlib
    print(f"\n═══ CREAR AUDIENCIA: {nombre} ═══")

    # Crear la audiencia vacía
    audiencia = account.create_custom_audience(
        fields=[CustomAudience.Field.id],
        params={
            CustomAudience.Field.name: nombre,
            CustomAudience.Field.description: descripcion,
            CustomAudience.Field.subtype: CustomAudience.Subtype.custom,
            CustomAudience.Field.customer_file_source: "USER_PROVIDED_ONLY",
        }
    )

    # Hashear emails y subirlos
    hashed = [hashlib.sha256(e.strip().lower().encode()).hexdigest() for e in emails]
    audiencia.create_users_replace(
        params={
            "payload": {
                "schema": "EMAIL_SHA256",
                "data": hashed,
            }
        }
    )
    print(f"  ✓ Audiencia creada con {len(emails)} emails — ID: {audiencia['id']}")
    return audiencia


# ════════════════════════════════════════════════════════════════
# 8. AUDIENCIA SIMILAR (Lookalike)
# ════════════════════════════════════════════════════════════════
def crear_audiencia_lookalike(account: AdAccount, audiencia_origen_id: str,
                              pais: str = "US", ratio: float = 0.01):
    """
    Crea una audiencia Lookalike basada en una audiencia existente.
    ratio: 0.01 a 0.20 (1 % – 20 % de la población del país)
    """
    print(f"\n═══ CREAR LOOKALIKE desde audiencia {audiencia_origen_id} ═══")
    lookalike = account.create_custom_audience(
        fields=[CustomAudience.Field.id, CustomAudience.Field.name],
        params={
            CustomAudience.Field.subtype: "LOOKALIKE",
            CustomAudience.Field.origin_audience_id: audiencia_origen_id,
            CustomAudience.Field.lookalike_spec: {
                "type": "similarity",
                "ratio": ratio,
                "country": pais,
            },
        }
    )
    print(f"  ✓ Lookalike creada — ID: {lookalike['id']}")
    return lookalike


# ════════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL — ejemplo de uso
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    account = init()

    # ── 1. Ver campañas ──────────────────────────────────────────
    listar_campanas(account)

    # ── 2. Métricas de los últimos 7 días ────────────────────────
    obtener_insights(account, fecha_inicio="2025-05-01", fecha_fin="2025-05-24")

    # ── 3. Crear una campaña (en pausa para pruebas) ─────────────
    # nueva = crear_campana(account, nombre="Mi campaña de tráfico", presupuesto_diario_usd=20)

    # ── 4. Crear un Ad Set dentro de esa campaña ─────────────────
    # conjunto = crear_conjunto(account, campana_id=nueva["id"],
    #                           nombre="AdSet México", pais="MX",
    #                           presupuesto_diario_usd=10)

    # ── 5. Editar campaña existente ──────────────────────────────
    # editar_campana("123456789", nuevo_estado="ACTIVE", nuevo_presupuesto_diario_usd=50)

    # ── 6. Ver audiencias ────────────────────────────────────────
    listar_audiencias(account)

    # ── 7. Crear audiencia desde emails ──────────────────────────
    # crear_audiencia_custom(account, "Clientes VIP",
    #                        emails=["cliente1@ejemplo.com", "cliente2@ejemplo.com"],
    #                        descripcion="Compradores recurrentes")

    # ── 8. Crear Lookalike ───────────────────────────────────────
    # crear_audiencia_lookalike(account, audiencia_origen_id="987654321",
    #                           pais="MX", ratio=0.02)
