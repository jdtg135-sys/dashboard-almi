# -*- coding: utf-8 -*-
"""Rendimiento a nivel de anuncio de las campanas C1..C4 de Meta."""
import os
import json, urllib.request, urllib.error, urllib.parse, collections, os

# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN, ACT = cred["access_token"], cred["ad_account_id"]
SINCE, UNTIL = "2026-07-01", "2026-09-29"
PURCHASE = "offsite_conversion.fb_pixel_purchase"
LEAD = "offsite_conversion.fb_pixel_lead"


def get(path, **params):
    params["access_token"] = TOKEN
    url = f"https://graph.facebook.com/v21.0/{path}?" + urllib.parse.urlencode(params)
    out = []
    while url:
        try:
            d = json.load(urllib.request.urlopen(url))
        except urllib.error.HTTPError as e:
            print("ERROR:", json.loads(e.read()).get("error", {}).get("message", "?")[:120])
            return out
        out += d.get("data", [])
        url = d.get("paging", {}).get("next")
    return out


filas = get(f"{ACT}/insights",
            level="ad",
            fields="campaign_name,adset_name,ad_name,ad_id,spend,impressions,clicks,ctr,actions",
            time_range=json.dumps({"since": SINCE, "until": UNTIL}),
            limit=500)

print(f"Periodo {SINCE} a {UNTIL} | filas: {len(filas)}\n")

porcamp = collections.defaultdict(list)
for f in filas:
    camp = f.get("campaign_name", "")
    if camp[:2] not in ("C1", "C2", "C3", "C4"):
        continue
    acc = {a["action_type"]: float(a["value"]) for a in f.get("actions", [])}
    compras = acc.get(PURCHASE, 0) or acc.get(LEAD, 0)
    gasto = float(f.get("spend", 0))
    impr = int(f.get("impressions", 0))
    porcamp[camp].append({
        "anuncio": f.get("ad_name", ""), "id": f.get("ad_id"),
        "conjunto": f.get("adset_name", ""), "gasto": gasto, "impr": impr,
        "clics": int(f.get("clicks", 0)), "ctr": float(f.get("ctr", 0) or 0),
        "compras": compras,
        "cpa": gasto / compras if compras else None,
    })

resumen = {}
for camp in sorted(porcamp):
    ads = porcamp[camp]
    g = sum(a["gasto"] for a in ads); c = sum(a["compras"] for a in ads)
    i = sum(a["impr"] for a in ads)
    print("=" * 96)
    print(f"{camp}   gasto {g:,.0f} COP | {i:,} impr | {c:.0f} conv | CPA promedio "
          f"{(g/c if c else 0):,.0f} COP | {len(ads)} anuncios")
    print("-" * 96)
    conv = [a for a in ads if a["compras"] > 0]
    conv.sort(key=lambda a: a["cpa"])
    for a in conv[:12]:
        print(f"  {a['cpa']:>9,.0f} CPA | {a['compras']:>4.0f} conv | {a['gasto']:>9,.0f} gasto |"
              f" {a['impr']:>8,} impr | CTR {a['ctr']:>5.2f}% | {a['anuncio'][:44]}")
    sinconv = [a for a in ads if a["compras"] == 0 and a["impr"] > 1000]
    if sinconv:
        sinconv.sort(key=lambda a: -a["gasto"])
        print(f"  --- sin conversiones con mas de 1.000 impresiones: {len(sinconv)} anuncios,"
              f" {sum(a['gasto'] for a in sinconv):,.0f} COP gastados")
        for a in sinconv[:5]:
            print(f"      {a['gasto']:>9,.0f} gasto | {a['impr']:>8,} impr | CTR {a['ctr']:>5.2f}% | {a['anuncio'][:44]}")
    resumen[camp] = conv

json.dump({k: v for k, v in resumen.items()},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ganadores.json"), "w"),
          ensure_ascii=False, indent=1)
