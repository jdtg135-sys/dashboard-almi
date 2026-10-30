# -*- coding: utf-8 -*-
"""Que anuncios estan rindiendo en las campanas activas, para decidir los
creativos nuevos a partir de datos y no de criterio.

Trae gasto, solicitudes y costo por solicitud a nivel de anuncio en los
ultimos 21 dias, mas el texto del creativo para poder leer QUE mensaje es el
que funciona, no solo cual identificador.
"""
import json, urllib.request, urllib.error, urllib.parse, collections, os, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN, ACT = cred["access_token"], cred["ad_account_id"]
PURCHASE = "offsite_conversion.fb_pixel_purchase"
HOY = datetime.date.today()
SINCE = (HOY - datetime.timedelta(days=21)).isoformat()
UNTIL = (HOY - datetime.timedelta(days=1)).isoformat()


def get(path, **params):
    params["access_token"] = TOKEN
    url = "https://graph.facebook.com/v21.0/%s?%s" % (path, urllib.parse.urlencode(params))
    out = []
    while url:
        try:
            d = json.load(urllib.request.urlopen(url))
        except urllib.error.HTTPError as e:
            print("ERROR:", json.loads(e.read()).get("error", {}).get("message", "?")[:160])
            return out
        out += d.get("data", [])
        url = d.get("paging", {}).get("next")
    return out


filas = get("%s/insights" % ACT, level="ad",
            fields="campaign_name,adset_name,ad_name,ad_id,spend,impressions,clicks,ctr,actions",
            time_range=json.dumps({"since": SINCE, "until": UNTIL}), limit=500)

print("Periodo %s a %s | anuncios con datos: %d\n" % (SINCE, UNTIL, len(filas)))

porcamp = collections.defaultdict(list)
for f in filas:
    camp = f.get("campaign_name", "")
    if not camp.startswith(("C1", "C2", "C3", "C4")):
        continue
    gasto = float(f.get("spend", 0))
    sol = 0
    for a in f.get("actions", []):
        if a.get("action_type") == PURCHASE:
            sol = int(float(a.get("value", 0)))
    porcamp[camp].append({
        "ad_id": f["ad_id"],
        "nombre": f.get("ad_name", ""),
        "gasto": gasto,
        "impresiones": int(f.get("impressions", 0)),
        "clics": int(f.get("clicks", 0)),
        "ctr": float(f.get("ctr", 0)),
        "sol": sol,
        "cps": gasto / sol if sol else None,
    })

todos = []
for camp in sorted(porcamp):
    ads = sorted(porcamp[camp], key=lambda a: (a["cps"] is None, a["cps"] or 0))
    gasto_c = sum(a["gasto"] for a in ads)
    sol_c = sum(a["sol"] for a in ads)
    print("=" * 96)
    print("%s   gasto $%,.0f".replace(",", ",") % (camp, gasto_c) if False else
          "{}   gasto ${:,.0f}   solicitudes {}   costo ${:,.0f}".format(
              camp, gasto_c, sol_c, gasto_c / sol_c if sol_c else 0))
    print("  {:<46} {:>9} {:>6} {:>6} {:>9}".format("anuncio", "gasto", "sol", "ctr", "costo"))
    for a in ads:
        todos.append((camp, a))
        print("  {:<46} {:>9,.0f} {:>6} {:>5.2f}% {:>9}".format(
            a["nombre"][:46], a["gasto"], a["sol"], a["ctr"],
            "{:,.0f}".format(a["cps"]) if a["cps"] else "sin sol."))
    print()

# --- Los mejores del conjunto, con texto ---
conv = [(c, a) for c, a in todos if a["sol"] >= 5]
conv.sort(key=lambda x: x[1]["cps"])
print("=" * 96)
print("LAS 12 MEJORES PIEZAS DEL CONJUNTO (minimo 5 solicitudes)")
print("=" * 96)
for camp, a in conv[:12]:
    cre = get("%s" % a["ad_id"], fields="creative{title,body,object_story_spec,asset_feed_spec}")
    print("\n[{}]  {}".format(camp[:14], a["nombre"][:60]))
    print("   {} solicitudes a ${:,.0f}   ctr {:.2f}%   gasto ${:,.0f}".format(
        a["sol"], a["cps"], a["ctr"], a["gasto"]))
