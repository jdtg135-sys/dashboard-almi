# -*- coding: utf-8 -*-
"""Inventario completo de textos y titulares con su rendimiento real.

Recorre TODOS los anuncios de C1..C4 y agrega por texto, no por anuncio, para
quedarse con los 5 mejores de cada tipo por campana.
"""
import os
import json, os, time, collections, requests

# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN, ACT = cred["access_token"], cred["ad_account_id"]
G = "https://graph.facebook.com/v21.0/"
AQUI = os.path.dirname(os.path.abspath(__file__))
RANGO = json.dumps({"since": "2026-07-01", "until": "2026-09-29"})
PUR, LEAD = "offsite_conversion.fb_pixel_purchase", "offsite_conversion.fb_pixel_lead"
MIN_CONV = 20          # por debajo de esto el dato no es concluyente


def get(path, **q):
    q["access_token"] = TOKEN
    for intento in range(6):
        r = requests.get(G + path, params=q, timeout=90)
        if r.status_code == 200:
            return r.json()
        if r.json().get("error", {}).get("code") in (17, 4, 613):
            espera = 90 * (intento + 1)
            print(f"   limite de API, esperando {espera}s...")
            time.sleep(espera)
            continue
        print("   ERROR:", r.json().get("error", {}).get("message", "?")[:140])
        return {}
    return {}


ads = get(ACT + "/insights", level="ad",
          fields="campaign_name,ad_id,spend", time_range=RANGO, limit=500).get("data", [])
porcamp = collections.defaultdict(list)
for a in ads:
    c = a.get("campaign_name", "")
    if c[:2] in ("C1", "C2", "C3", "C4") and float(a.get("spend", 0)) > 0:
        porcamp[c[:2]].append(a["ad_id"])

resultado = {}
for camp in sorted(porcamp):
    print("=" * 84)
    print(camp, f"({len(porcamp[camp])} anuncios con gasto)")
    for tipo, br in (("textos", "body_asset"), ("titulares", "title_asset")):
        acum = collections.defaultdict(lambda: [0.0, 0.0])   # texto -> [gasto, conv]
        for aid in porcamp[camp]:
            d = get(aid + "/insights", fields="spend,actions",
                    breakdowns=br, time_range=RANGO, limit=60)
            for f in d.get("data", []):
                txt = (f.get(br) or {}).get("text", "").strip()
                if not txt:
                    continue
                acc = {x["action_type"]: float(x["value"]) for x in f.get("actions", [])}
                acum[txt][0] += float(f.get("spend", 0))
                acum[txt][1] += acc.get(PUR, 0) or acc.get(LEAD, 0)
            time.sleep(0.4)
        filas = [(g / c, c, g, t) for t, (g, c) in acum.items() if c >= MIN_CONV]
        filas.sort()
        print(f"  -- {tipo}: {len(acum)} distintos, {len(filas)} con {MIN_CONV}+ conversiones")
        for cpa, c, g, t in filas[:8]:
            print(f"     CPA {cpa:>8,.0f} | {c:>5.0f} conv | {t[:96]}")
        resultado.setdefault(camp, {})[tipo] = [
            {"texto": t, "cpa": round(cpa), "conv": c} for cpa, c, g, t in filas]

json.dump(resultado, open(os.path.join(AQUI, "inventario_copys.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nGuardado en inventario_copys.json")
