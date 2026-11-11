# -*- coding: utf-8 -*-
"""Detalle: patron por dia de semana y C1 antes/despues del 4-nov."""
import json, os, requests, datetime
from collections import defaultdict
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
T = cred["access_token"]; A = str(cred["ad_account_id"])
A = A if A.startswith("act_") else "act_" + A
G = "https://graph.facebook.com/v19.0"
CONV = "offsite_conversion.fb_pixel_purchase"
DIAS = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]


def ins(fields, since, until, nivel="account", inc=True):
    p = {"access_token": T, "fields": ",".join(fields), "level": nivel,
         "time_range": json.dumps({"since": since, "until": until}), "limit": 500}
    if inc:
        p["time_increment"] = 1
    out, url = [], "%s/%s/insights" % (G, A)
    while url:
        j = requests.get(url, params=p, timeout=120).json()
        out += j.get("data", []); url = (j.get("paging") or {}).get("next"); p = None
    return out


def conv(f):
    return sum(float(a["value"]) for a in f.get("actions", [])
               if a["action_type"] == CONV)


print("=== Meta: solicitudes por dia de semana ===")
for etq, s, u in (("octubre", "2026-10-01", "2026-10-31"),
                  ("1-8 nov", "2026-11-01", "2026-11-08")):
    acc = defaultdict(list)
    for f in ins(["actions"], s, u):
        d = datetime.date.fromisoformat(f["date_start"])
        acc[d.weekday()].append(conv(f))
    print(" %-9s %s" % (etq, "  ".join(
        "%s %5.0f" % (DIAS[i], sum(acc[i]) / len(acc[i])) for i in range(7) if acc[i])))

print("\n=== C1: antes y despues del cambio de creativo del 4-nov ===")
print("%-10s %10s %7s %9s %7s %6s %6s" % ("tramo", "gasto", "conv", "costo", "CPM", "CTR", "frec"))
for etq, s, u in (("1-3 nov", "2026-11-01", "2026-11-03"),
                  ("4 nov", "2026-11-04", "2026-11-04"),
                  ("5-8 nov", "2026-11-05", "2026-11-08")):
    c = ins(["campaign_name", "spend", "impressions", "cpm", "ctr", "frequency"],
            s, u, nivel="campaign", inc=False)
    a = ins(["campaign_name", "actions"], s, u, nivel="campaign", inc=False)
    ca = {x["campaign_name"]: conv(x) for x in a}
    for f in c:
        if f["campaign_name"].startswith("C1"):
            g = float(f["spend"]); n = ca.get(f["campaign_name"], 0)
            print("%-10s %10.0f %7.0f %9.0f %7.0f %6.2f %6.2f" % (
                etq, g, n, (g / n if n else 0), float(f["cpm"]),
                float(f["ctr"]), float(f["frequency"])))

print("\n=== Meta: todas las campanas, 1-4 nov contra 5-8 nov ===")
print("%-40s %9s %6s %8s %7s %6s" % ("campana", "gasto", "conv", "costo", "CPM", "CTR"))
for etq, s, u in (("1-4", "2026-11-01", "2026-11-04"), ("5-8", "2026-11-05", "2026-11-08")):
    c = ins(["campaign_name", "spend", "cpm", "ctr"], s, u, nivel="campaign", inc=False)
    a = ins(["campaign_name", "actions"], s, u, nivel="campaign", inc=False)
    ca = {x["campaign_name"]: conv(x) for x in a}
    print("-- %s nov" % etq)
    for f in sorted(c, key=lambda x: -float(x["spend"])):
        g = float(f["spend"]); n = ca.get(f["campaign_name"], 0)
        print("%-40s %9.0f %6.0f %8.0f %7.0f %6.2f" % (
            f["campaign_name"][:40], g, n, (g / n if n else 0),
            float(f["cpm"]), float(f["ctr"])))
