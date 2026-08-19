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

# Cuantos dias hacia atras se descarga la serie diaria que alimenta el filtro de
# fechas. Subir este numero permite consultar rangos mas antiguos en el dashboard.
DIAS_SERIE = 180


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


def fetch_campaign_insights(account_id, token, since, until):
    """Devuelve dict {campaign_id: {nombre, gasto, impresiones, clics, ctr, cpc_promedio, resultados, costo_por_resultado}}
    para todas las campanas con actividad en el rango (incluye pausadas/deshabilitadas)."""
    url = f"{GRAPH_URL}/{account_id}/insights"
    params = {
        "level": "campaign",
        "fields": "campaign_id,campaign_name,spend,impressions,clicks,actions",
        "time_range": json.dumps({"since": since, "until": until}),
        "limit": 200,
        "access_token": token,
    }
    out = {}
    while True:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        for row in data.get("data", []):
            spend = float(row.get("spend", 0))
            impresiones = int(row.get("impressions", 0))
            clics = int(row.get("clicks", 0))
            resultados = 0
            for action in row.get("actions", []):
                if action.get("action_type") == "lead":
                    resultados = int(float(action.get("value", 0)))
                    break
            out[row["campaign_id"]] = {
                "nombre": row.get("campaign_name", ""),
                "gasto": round(spend),
                "impresiones": impresiones,
                "clics": clics,
                "ctr": round(clics / impresiones * 100, 2) if impresiones else 0,
                "cpc_promedio": round(spend / clics, 2) if clics else 0,
                "resultados": resultados,
                "costo_por_resultado": round(spend / resultados) if resultados else 0,
            }
        next_url = data.get("paging", {}).get("next")
        if not next_url:
            break
        url, params = next_url, None
    return out


def fetch_campaign_info(account_id, token):
    """Devuelve dict {campaign_id: {estado, presupuesto_dia}} para todas las campanas de la cuenta."""
    url = f"{GRAPH_URL}/{account_id}/campaigns"
    params = {
        "fields": "id,name,effective_status,daily_budget",
        "limit": 200,
        "access_token": token,
    }
    out = {}
    while True:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        for row in data.get("data", []):
            daily_budget = row.get("daily_budget")
            out[row["id"]] = {
                "estado": row.get("effective_status", "").title(),
                # La cuenta esta en COP, moneda sin decimales: Graph API ya devuelve
                # el presupuesto en pesos enteros. Dividir entre 100 (como se hacia
                # antes) daba $800/dia cuando el real es $80.000/dia.
                "presupuesto_dia": int(daily_budget) if daily_budget else 0,
            }
        next_url = data.get("paging", {}).get("next")
        if not next_url:
            break
        url, params = next_url, None
    return out


def fetch_daily_series(account_id, token, since, until):
    """Devuelve una lista [{fecha, inversion, impresiones, clics, resultados}] con un
    registro por dia. Es la base del filtro de fechas del dashboard: el HTML agrega
    estos dias segun el rango que elija el usuario, sin volver a llamar la API."""
    url = f"{GRAPH_URL}/{account_id}/insights"
    params = {
        "fields": "spend,impressions,clicks,actions",
        "time_range": json.dumps({"since": since, "until": until}),
        "time_increment": 1,
        "limit": 500,
        "access_token": token,
    }
    dias = []
    while True:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        for row in data.get("data", []):
            spend = float(row.get("spend", 0))
            resultados = 0
            for action in row.get("actions", []):
                if action.get("action_type") == "lead":
                    resultados = int(float(action.get("value", 0)))
                    break
            dias.append({
                "fecha": row.get("date_start"),
                "inversion": round(spend),
                "impresiones": int(row.get("impressions", 0)),
                "clics": int(row.get("clicks", 0)),
                "resultados": resultados,
            })
        next_url = data.get("paging", {}).get("next")
        if not next_url:
            break
        url, params = next_url, None
    dias.sort(key=lambda d: d["fecha"])
    return dias


def fetch_daily_series_by_campaign(account_id, token, since, until):
    """Igual que fetch_daily_series pero desglosado por campana, para que el filtro
    de fechas tambien pueda recalcular la tabla de campanas."""
    url = f"{GRAPH_URL}/{account_id}/insights"
    params = {
        "level": "campaign",
        "fields": "campaign_id,campaign_name,spend,impressions,clicks,actions",
        "time_range": json.dumps({"since": since, "until": until}),
        "time_increment": 1,
        "limit": 500,
        "access_token": token,
    }
    dias = []
    while True:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        for row in data.get("data", []):
            spend = float(row.get("spend", 0))
            resultados = 0
            for action in row.get("actions", []):
                if action.get("action_type") == "lead":
                    resultados = int(float(action.get("value", 0)))
                    break
            dias.append({
                "fecha": row.get("date_start"),
                "campana": row.get("campaign_name", ""),
                "inversion": round(spend),
                "impresiones": int(row.get("impressions", 0)),
                "clics": int(row.get("clicks", 0)),
                "resultados": resultados,
            })
        next_url = data.get("paging", {}).get("next")
        if not next_url:
            break
        url, params = next_url, None
    dias.sort(key=lambda d: (d["fecha"], d["campana"]))
    return dias


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

    # Ventanas de 7 dias COMPLETOS, excluyendo hoy (dia parcial).
    # Antes el rango actual era (hoy-7 .. hoy) = 8 dias inclusive, mientras la
    # semana previa eran 7: comparar 8 contra 7 inflaba todos los deltas. Google
    # Ads ya usaba 7 dias, asi que ademas los dos paneles median periodos distintos.
    act_desde = (hoy - datetime.timedelta(days=7)).isoformat()
    act_hasta = (hoy - datetime.timedelta(days=1)).isoformat()
    prev_desde = (hoy - datetime.timedelta(days=14)).isoformat()
    prev_hasta = (hoy - datetime.timedelta(days=8)).isoformat()

    # --- Ultimos 7 dias ---
    actual = fetch_insights(account_id, token, act_desde, act_hasta)
    print(f"=== Meta Ads (7 dias completos: {act_desde} a {act_hasta}) ===")
    print(f"Inversion: ${actual['inversion']:,.0f}")
    print(f"Impresiones: {actual['impresiones']}")
    print(f"Clics: {actual['clics']}")
    print(f"Resultados (leads): {actual['resultados']}")
    print(f"Costo por resultado: ${actual['costo_por_resultado']:,.0f}")

    # --- Semana anterior ---
    prev = fetch_insights(account_id, token, prev_desde, prev_hasta)
    print("\n=== Meta Ads (semana anterior) ===")
    print(f"Inversion: ${prev['inversion']:,.0f}")
    print(f"Resultados (leads): {prev['resultados']}")

    # --- Campanas (ultimos 7 dias, incluye pausadas/deshabilitadas) ---
    actual_camp = fetch_campaign_insights(account_id, token, act_desde, act_hasta)
    prev_camp = fetch_campaign_insights(account_id, token, prev_desde, prev_hasta)
    info_camp = fetch_campaign_info(account_id, token)

    campaigns = []
    for cid, c in actual_camp.items():
        info = info_camp.get(cid, {})
        campaigns.append({
            "nombre": c["nombre"],
            "estado": info.get("estado", ""),
            "presupuesto_dia": info.get("presupuesto_dia", 0),
            "impresiones": c["impresiones"],
            "clics": c["clics"],
            "ctr": c["ctr"],
            "cpc_promedio": c["cpc_promedio"],
            "gasto": c["gasto"],
            "resultados": c["resultados"],
            "costo_por_resultado": c["costo_por_resultado"],
            "prev": prev_camp.get(cid),
        })
    campaigns.sort(key=lambda c: c["gasto"], reverse=True)

    print(f"\nCampanas Meta Ads (ultimos 7 dias): {len(campaigns)}")
    for c in campaigns:
        print(f"  - {c['nombre']} ({c['estado']}): gasto ${c['gasto']:,.0f}, {c['resultados']} resultados")

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

    # --- Serie diaria (alimenta el filtro de fechas del dashboard) ---
    serie_desde = (hoy - datetime.timedelta(days=DIAS_SERIE)).isoformat()
    diario = fetch_daily_series(account_id, token, serie_desde, hoy.isoformat())
    diario_camp = fetch_daily_series_by_campaign(account_id, token, serie_desde, hoy.isoformat())

    print(f"\n=== Serie diaria Meta ({DIAS_SERIE} dias) ===")
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
    ads["periodo_prev_desde"] = prev_desde
    ads["periodo_prev_hasta"] = prev_hasta
    ads["actualizado"] = datetime.datetime.now().isoformat(timespec="seconds")

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
        "campanas": campaigns,
        "meses": meses,
        "diario": diario,
        "diario_campanas": diario_camp,
    }

    with open(ADS_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(ads, f, ensure_ascii=False, indent=2)

    print("\nads_data.json actualizado. Ejecuta actualizar_dashboard.py para reflejarlo en el HTML.")


if __name__ == "__main__":
    main()
