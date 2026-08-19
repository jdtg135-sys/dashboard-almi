"""
Actualizador de datos de Google Ads para el Dashboard ALMI
------------------------------------------------------------
Conecta con la Google Ads API usando tu cuenta de Google (OAuth),
trae las metricas de los ultimos 7 dias de la cuenta de ALMI Financiera
(via la cuenta MCC) y las guarda en ads_data.json (seccion "google_ads").

Luego ejecuta actualizar_dashboard.py (o ejecutar_actualizacion.bat) para
volcar esos valores al HTML.

Uso:
  python actualizar_google_ads.py
  (la primera vez abrira el navegador para iniciar sesion con Google)
"""

import os
import json
import datetime
import calendar

from google.ads.googleads.client import GoogleAdsClient
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "oauth_credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token_ads.json")
ADS_DATA_FILE = os.path.join(BASE_DIR, "ads_data.json")

SCOPES = ["https://www.googleapis.com/auth/adwords"]

# Cuantos dias hacia atras se descarga la serie diaria del filtro de fechas.
DIAS_SERIE = 180

# Credenciales de Google Ads.
#
# Antes estaban escritas aqui mismo, y este archivo se publica en un repositorio
# publico: el developer token quedaba a la vista de cualquiera. Ahora se leen de
# google_ads_config.json, que esta en .gitignore junto al resto de secretos.
#
# Si el archivo no existe, crearlo al lado de este script con esta forma:
#   {
#     "developer_token": "...",
#     "login_customer_id": "...",   // cuenta MCC
#     "customer_id": "..."          // cuenta del cliente
#   }
GOOGLE_ADS_CONFIG_FILE = os.path.join(BASE_DIR, "google_ads_config.json")


def cargar_config_ads():
    if not os.path.exists(GOOGLE_ADS_CONFIG_FILE):
        raise SystemExit(
            f"Falta {os.path.basename(GOOGLE_ADS_CONFIG_FILE)}.\n"
            "Crealo al lado de este script con las claves: "
            "developer_token, login_customer_id, customer_id."
        )
    with open(GOOGLE_ADS_CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    faltan = [k for k in ("developer_token", "login_customer_id", "customer_id")
              if not cfg.get(k)]
    if faltan:
        raise SystemExit(
            f"{os.path.basename(GOOGLE_ADS_CONFIG_FILE)} no tiene: {', '.join(faltan)}"
        )
    return cfg


_ads_cfg = cargar_config_ads()
DEVELOPER_TOKEN = _ads_cfg["developer_token"]
LOGIN_CUSTOMER_ID = _ads_cfg["login_customer_id"]   # MCC
CUSTOMER_ID = _ads_cfg["customer_id"]               # Cuenta del cliente


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        refreshed = False
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                refreshed = True
            except RefreshError:
                creds = None
        if not refreshed:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def main():
    creds = get_credentials()

    config = {
        "developer_token": DEVELOPER_TOKEN,
        "client_id": json.load(open(CLIENT_SECRET_FILE))["installed"]["client_id"],
        "client_secret": json.load(open(CLIENT_SECRET_FILE))["installed"]["client_secret"],
        "refresh_token": creds.refresh_token,
        "login_customer_id": LOGIN_CUSTOMER_ID,
        "use_proto_plus": True,
    }

    client = GoogleAdsClient.load_from_dict(config)
    ga_service = client.get_service("GoogleAdsService")

    # Ventanas explicitas de 7 dias completos, iguales a las de Meta, para que
    # ambos paneles del dashboard midan exactamente el mismo periodo.
    hoy = datetime.date.today()
    act_desde = (hoy - datetime.timedelta(days=7)).isoformat()
    act_hasta = (hoy - datetime.timedelta(days=1)).isoformat()
    prev_start = (hoy - datetime.timedelta(days=14)).isoformat()
    prev_end = (hoy - datetime.timedelta(days=8)).isoformat()

    query = f"""
        SELECT
          metrics.cost_micros,
          metrics.impressions,
          metrics.clicks,
          metrics.conversions
        FROM customer
        WHERE segments.date BETWEEN '{act_desde}' AND '{act_hasta}'
    """

    response = ga_service.search_stream(customer_id=CUSTOMER_ID, query=query)

    cost_micros = 0
    impressions = 0
    clicks = 0
    conversions = 0.0

    for batch in response:
        for row in batch.results:
            cost_micros += row.metrics.cost_micros
            impressions += row.metrics.impressions
            clicks += row.metrics.clicks
            conversions += row.metrics.conversions

    inversion = cost_micros / 1_000_000
    costo_por_conversion = round(inversion / conversions, 2) if conversions else 0

    print(f"=== Google Ads (7 dias completos: {act_desde} a {act_hasta}) ===")
    print(f"Inversion: ${inversion:,.0f}")
    print(f"Impresiones: {impressions}")
    print(f"Clics: {clicks}")
    print(f"Conversiones: {conversions}")
    print(f"Costo por conversion: ${costo_por_conversion:,.0f}")

    # --- Totales de la semana anterior (para comparativa) ---
    prev_query = f"""
        SELECT
          metrics.cost_micros,
          metrics.impressions,
          metrics.clicks,
          metrics.conversions
        FROM customer
        WHERE segments.date BETWEEN '{prev_start}' AND '{prev_end}'
    """

    prev_response = ga_service.search_stream(customer_id=CUSTOMER_ID, query=prev_query)

    cost_micros_prev = 0
    impressions_prev = 0
    clicks_prev = 0
    conversions_prev = 0.0

    for batch in prev_response:
        for row in batch.results:
            cost_micros_prev += row.metrics.cost_micros
            impressions_prev += row.metrics.impressions
            clicks_prev += row.metrics.clicks
            conversions_prev += row.metrics.conversions

    inversion_prev = cost_micros_prev / 1_000_000

    print("\n=== Google Ads (semana anterior) ===")
    print(f"Inversion: ${inversion_prev:,.0f}")
    print(f"Impresiones: {impressions_prev}")
    print(f"Clics: {clicks_prev}")
    print(f"Conversiones: {conversions_prev}")

    # --- Campanas activas (ultimos 7 dias) ---
    campaign_query = f"""
        SELECT
          campaign.name,
          campaign.status,
          campaign.advertising_channel_type,
          campaign_budget.amount_micros,
          metrics.impressions,
          metrics.clicks,
          metrics.ctr,
          metrics.average_cpc,
          metrics.cost_micros,
          metrics.conversions,
          metrics.cost_per_conversion
        FROM campaign
        WHERE segments.date BETWEEN '{act_desde}' AND '{act_hasta}'
          AND campaign.status = 'ENABLED'
        ORDER BY metrics.cost_micros DESC
    """

    CHANNEL_LABELS = {
        2: "Busqueda", 3: "Display", 5: "Video", 6: "Shopping",
        10: "Performance Max", 12: "Demand Gen", 13: "Local",
    }

    campaign_response = ga_service.search_stream(customer_id=CUSTOMER_ID, query=campaign_query)
    campaigns = []
    for batch in campaign_response:
        for row in batch.results:
            campaigns.append({
                "nombre": row.campaign.name,
                "estado": row.campaign.status.name.title(),
                "tipo": CHANNEL_LABELS.get(int(row.campaign.advertising_channel_type), "Otro"),
                "impresiones": row.metrics.impressions,
                "clics": row.metrics.clicks,
                "ctr": round(row.metrics.ctr * 100, 2),
                "cpc_promedio": round(row.metrics.average_cpc / 1_000_000, 2),
                "presupuesto_dia": round(row.campaign_budget.amount_micros / 1_000_000),
                "gasto": round(row.metrics.cost_micros / 1_000_000),
                "conversiones": round(row.metrics.conversions, 1),
                "costo_por_conversion": round(row.metrics.cost_per_conversion / 1_000_000, 2) if row.metrics.cost_per_conversion else 0,
            })

    print(f"\nCampanas activas: {len(campaigns)}")
    for c in campaigns:
        print(f"  - {c['nombre']} ({c['tipo']}): gasto ${c['gasto']:,.0f}, {c['conversiones']} conversiones")

    # --- Campanas: metricas de la semana anterior (para comparativa) ---
    campaign_prev_query = f"""
        SELECT
          campaign.name,
          metrics.impressions,
          metrics.clicks,
          metrics.ctr,
          metrics.average_cpc,
          metrics.cost_micros,
          metrics.conversions,
          metrics.cost_per_conversion
        FROM campaign
        WHERE segments.date BETWEEN '{prev_start}' AND '{prev_end}'
    """

    campaign_prev_response = ga_service.search_stream(customer_id=CUSTOMER_ID, query=campaign_prev_query)
    campanas_prev = {}
    for batch in campaign_prev_response:
        for row in batch.results:
            campanas_prev[row.campaign.name] = {
                "impresiones": row.metrics.impressions,
                "clics": row.metrics.clicks,
                "ctr": round(row.metrics.ctr * 100, 2),
                "cpc_promedio": round(row.metrics.average_cpc / 1_000_000, 2),
                "gasto": round(row.metrics.cost_micros / 1_000_000),
                "conversiones": round(row.metrics.conversions, 1),
                "costo_por_conversion": round(row.metrics.cost_per_conversion / 1_000_000, 2) if row.metrics.cost_per_conversion else 0,
            }

    for c in campaigns:
        c["prev"] = campanas_prev.get(c["nombre"])

    # --- Comparativas mensuales (mes calendario) ---
    MESES_ES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

    def month_range(months_back):
        y, mo = hoy.year, hoy.month
        for _ in range(months_back):
            mo -= 1
            if mo == 0:
                mo, y = 12, y - 1
        start = datetime.date(y, mo, 1)
        if months_back == 0:
            end = hoy
        else:
            end = datetime.date(y, mo, calendar.monthrange(y, mo)[1])
        return start, end, f"{MESES_ES[mo - 1]} {y}"

    meses = []
    for mb in range(3):
        m_start, m_end, m_label = month_range(mb)
        m_query = f"""
            SELECT
              metrics.cost_micros,
              metrics.impressions,
              metrics.clicks,
              metrics.conversions
            FROM customer
            WHERE segments.date BETWEEN '{m_start.isoformat()}' AND '{m_end.isoformat()}'
        """
        m_response = ga_service.search_stream(customer_id=CUSTOMER_ID, query=m_query)
        m_cost = m_imp = m_clicks = 0
        m_conv = 0.0
        for batch in m_response:
            for row in batch.results:
                m_cost += row.metrics.cost_micros
                m_imp += row.metrics.impressions
                m_clicks += row.metrics.clicks
                m_conv += row.metrics.conversions
        m_inversion = m_cost / 1_000_000
        meses.append({
            "label": m_label,
            "inversion": round(m_inversion),
            "impresiones": m_imp,
            "clics": m_clicks,
            "conversiones": round(m_conv, 1),
            "costo_por_conversion": round(m_inversion / m_conv, 2) if m_conv else 0,
        })

    print("\n=== Google Ads (comparativa mensual) ===")
    for md in meses:
        print(f"  {md['label']}: inversion=${md['inversion']:,.0f}, impresiones={md['impresiones']}, "
              f"clics={md['clics']}, conversiones={md['conversiones']}, costo_x_conv=${md['costo_por_conversion']:,.0f}")

    # --- Serie diaria (alimenta el filtro de fechas del dashboard) ---
    # El HTML agrega estos dias segun el rango que elija el usuario, sin volver
    # a llamar la API. Subir DIAS_SERIE permite consultar rangos mas antiguos.
    serie_desde = (hoy - datetime.timedelta(days=DIAS_SERIE)).isoformat()

    diario_query = f"""
        SELECT
          segments.date,
          metrics.cost_micros,
          metrics.impressions,
          metrics.clicks,
          metrics.conversions
        FROM customer
        WHERE segments.date BETWEEN '{serie_desde}' AND '{hoy.isoformat()}'
        ORDER BY segments.date
    """
    diario = []
    for batch in ga_service.search_stream(customer_id=CUSTOMER_ID, query=diario_query):
        for row in batch.results:
            diario.append({
                "fecha": row.segments.date,
                "inversion": round(row.metrics.cost_micros / 1_000_000),
                "impresiones": row.metrics.impressions,
                "clics": row.metrics.clicks,
                "conversiones": round(row.metrics.conversions, 1),
            })

    diario_camp_query = f"""
        SELECT
          segments.date,
          campaign.name,
          metrics.cost_micros,
          metrics.impressions,
          metrics.clicks,
          metrics.conversions
        FROM campaign
        WHERE segments.date BETWEEN '{serie_desde}' AND '{hoy.isoformat()}'
        ORDER BY segments.date
    """
    diario_camp = []
    for batch in ga_service.search_stream(customer_id=CUSTOMER_ID, query=diario_camp_query):
        for row in batch.results:
            diario_camp.append({
                "fecha": row.segments.date,
                "campana": row.campaign.name,
                "inversion": round(row.metrics.cost_micros / 1_000_000),
                "impresiones": row.metrics.impressions,
                "clics": row.metrics.clicks,
                "conversiones": round(row.metrics.conversions, 1),
            })

    print(f"\n=== Serie diaria Google ({DIAS_SERIE} dias) ===")
    print(f"  {len(diario)} dias con datos, {len(diario_camp)} filas por campana")
    if diario:
        print(f"  rango: {diario[0]['fecha']} -> {diario[-1]['fecha']}")

    # --- Actualizar ads_data.json ---
    if os.path.exists(ADS_DATA_FILE):
        with open(ADS_DATA_FILE, "r", encoding="utf-8") as f:
            ads = json.load(f)
    else:
        ads = {}

    ads["periodo"] = "7 dias completos"
    ads["periodo_desde"] = act_desde
    ads["periodo_hasta"] = act_hasta
    ads["periodo_prev_desde"] = prev_start
    ads["periodo_prev_hasta"] = prev_end
    ads["actualizado"] = datetime.datetime.now().isoformat(timespec="seconds")

    ads.setdefault("meta_ads", {
        "inversion": 0, "impresiones": 0, "clics": 0,
        "resultados": 0, "costo_por_resultado": 0
    })
    ads["google_ads"] = {
        "inversion": round(inversion),
        "impresiones": impressions,
        "clics": clicks,
        "conversiones": round(conversions, 1),
        "costo_por_conversion": costo_por_conversion,
        "campanas": campaigns,
        "inversion_prev": round(inversion_prev),
        "impresiones_prev": impressions_prev,
        "clics_prev": clicks_prev,
        "conversiones_prev": round(conversions_prev, 1),
        "costo_por_conversion_prev": round(inversion_prev / conversions_prev, 2) if conversions_prev else 0,
        "meses": meses,
        "diario": diario,
        "diario_campanas": diario_camp,
    }

    with open(ADS_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(ads, f, ensure_ascii=False, indent=2)

    print("\nads_data.json actualizado. Ejecuta actualizar_dashboard.py para reflejarlo en el HTML.")


if __name__ == "__main__":
    main()
