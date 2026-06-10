"""
Actualizador de datos de Meta Ads para el Dashboard ALMI
------------------------------------------------------------
Usa el token del usuario de sistema "Informe Almi" (Graph API) para traer
metricas de la cuenta publicitaria de ALMI Financiera y guardarlas en
ads_data.json (seccion "meta_ads").

Luego ejecuta actualizar_dashboard.py (o ejecutar_actualizacion.bat) para
volcar esos valores al HTML.

Uso:
  python actualizar_meta_ads.py
"""

import os
import json
import datetime
import calendar

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "meta_credentials.json")
ADS_DATA_FILE = os.path.join(BASE_DIR, "ads_data.json")

GRAPH_URL = "https://graph.facebook.com/v19.0"
MESES_ES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]


def fetch_insights(account_id, token, since, until):
    """Devuelve dict {inversion, impresiones, clics, resultados, costo_por_resultado}
    para el rango de fechas dado (resultados = action_type 'lead')."""
    url = f"{GRAPH_URL}/{account_id}/insights"
    params = {
        "fields": "spend,impressions,clicks,actions",
        "time_range": json.dumps({"since": since, "until": until}),
        "access_token": token,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    rows = response.json().get("data", [])

    if not rows:
        return {"inversion": 0, "impresiones": 0, "clics": 0, "resultados": 0, "costo_por_resultado": 0}

    row = rows[0]
    inversion = float(row.get("spend", 0))
    impresiones = int(row.get("impressions", 0))
    clics = int(row.get("clicks", 0))
    resultados = 0
    for action in row.get("actions", []):
        if action.get("action_type") == "lead":
            resultados = int(float(action.get("value", 0)))
            break

    return {
        "inversion": round(inversion),
        "impresiones": impresiones,
        "clics": clics,
        "resultados": resultados,
        "costo_por_resultado": round(inversion / resultados) if resultados else 0,
    }


def month_range(months_back, today):
    y, mo = today.year, today.month
    for _ in range(months_back):
        mo -= 1
        if mo == 0:
            mo, y = 12, y - 1
    start = datetime.date(y, mo, 1)
    if months_back == 0:
        end = today
    else:
        end = datetime.date(y, mo, calendar.monthrange(y, mo)[1])
    return start, end, f"{MESES_ES[mo - 1]} {y}"


def main():
    creds = json.load(open(CREDENTIALS_FILE))
    account_id = creds["ad_account_id"]
    token = creds["access_token"]

    hoy = datetime.date.today()

    # --- Ultimos 7 dias ---
    actual = fetch_insights(account_id, token, (hoy - datetime.timedelta(days=7)).isoformat(), hoy.isoformat())
    print("=== Meta Ads (ultimos 7 dias) ===")
    print(f"Inversion: ${actual['inversion']:,.0f}")
    print(f"Impresiones: {actual['impresiones']}")
    print(f"Clics: {actual['clics']}")
    print(f"Resultados (leads): {actual['resultados']}")
    print(f"Costo por resultado: ${actual['costo_por_resultado']:,.0f}")

    # --- Semana anterior ---
    prev = fetch_insights(
        account_id, token,
        (hoy - datetime.timedelta(days=14)).isoformat(),
        (hoy - datetime.timedelta(days=8)).isoformat(),
    )
    print("\n=== Meta Ads (semana anterior) ===")
    print(f"Inversion: ${prev['inversion']:,.0f}")
    print(f"Resultados (leads): {prev['resultados']}")

    # --- Comparativas mensuales (mes calendario) ---
    meses = []
    for mb in range(3):
        m_start, m_end, m_label = month_range(mb, hoy)
        m_data = fetch_insights(account_id, token, m_start.isoformat(), m_end.isoformat())
        m_data["label"] = m_label
        meses.append(m_data)

    print("\n=== Meta Ads (comparativa mensual) ===")
    for md in meses:
        print(f"  {md['label']}: inversion=${md['inversion']:,.0f}, impresiones={md['impresiones']}, "
              f"clics={md['clics']}, resultados={md['resultados']}, costo_x_resultado=${md['costo_por_resultado']:,.0f}")

    # --- Actualizar ads_data.json ---
    if os.path.exists(ADS_DATA_FILE):
        with open(ADS_DATA_FILE, "r", encoding="utf-8") as f:
            ads = json.load(f)
    else:
        ads = {}

    ads["meta_ads"] = {
        "inversion": actual["inversion"],
        "impresiones": actual["impresiones"],
        "clics": actual["clics"],
        "resultados": actual["resultados"],
        "costo_por_resultado": actual["costo_por_resultado"],
        "inversion_prev": prev["inversion"],
        "impresiones_prev": prev["impresiones"],
        "clics_prev": prev["clics"],
        "resultados_prev": prev["resultados"],
        "costo_por_resultado_prev": prev["costo_por_resultado"],
        "meses": meses,
    }

    with open(ADS_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(ads, f, ensure_ascii=False, indent=2)

    print("\nads_data.json actualizado. Ejecuta actualizar_dashboard.py para reflejarlo en el HTML.")


if __name__ == "__main__":
    main()
