# -*- coding: utf-8 -*-
import os
import json, urllib.request, urllib.parse, urllib.error, os
# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
c = json.load(open(os.path.join(BASE, "meta_credentials.json")))
T, ACT = c["access_token"], c["ad_account_id"]
def get(p, **q):
    q["access_token"] = T
    u = f"https://graph.facebook.com/v21.0/{p}?" + urllib.parse.urlencode(q)
    try: return json.load(urllib.request.urlopen(u))
    except urllib.error.HTTPError as e: return {"error": json.loads(e.read())}

d = get(f"{ACT}/campaigns", fields="name,status,effective_status,daily_budget,objective", limit=100)
print("=== Campanas con gasto o activas ===")
for x in d.get("data", []):
    if x.get("effective_status") in ("ACTIVE",) or "Copia" in x["name"]:
        print(f"  {x['effective_status']:<10} presup {int(x.get('daily_budget',0) or 0):>7,} | {x['objective'][:22]:<24} | {x['name'][:50]}")

print("\n=== Webinar: desglose de acciones 2-6 oct ===")
ins = get(f"{ACT}/insights", level="campaign", fields="campaign_name,spend,clicks,actions,cost_per_action_type",
          time_range=json.dumps({"since":"2026-10-02","until":"2026-10-06"}), limit=200)
for f in ins.get("data", []):
    if "Webinar" not in f.get("campaign_name",""): continue
    print("  gasto", f["spend"], "| clics", f.get("clicks"))
    for a in f.get("actions", []):
        print(f"    {a['action_type']:<42} {a['value']}")
