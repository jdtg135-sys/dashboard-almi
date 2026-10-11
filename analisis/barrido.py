# -*- coding: utf-8 -*-
"""Barrido de campanas Meta: campana y dia, periodo del cotizador nuevo."""
import os
import json, urllib.request, urllib.error, urllib.parse, collections, os, sys

# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN, ACT = cred["access_token"], cred["ad_account_id"]
SINCE, UNTIL = sys.argv[1], sys.argv[2]
PURCHASE = "offsite_conversion.fb_pixel_purchase"
LEAD = "offsite_conversion.fb_pixel_lead"

def get(path, **p):
    p["access_token"] = TOKEN
    url = f"https://graph.facebook.com/v21.0/{path}?" + urllib.parse.urlencode(p)
    out = []
    while url:
        try:
            d = json.load(urllib.request.urlopen(url))
        except urllib.error.HTTPError as e:
            print("ERROR:", json.loads(e.read()).get("error", {}).get("message", "?")[:160]); return out
        out += d.get("data", []); url = d.get("paging", {}).get("next")
    return out

def conv(f):
    acc = {a["action_type"]: float(a["value"]) for a in f.get("actions", [])}
    return acc.get(PURCHASE, 0) or acc.get(LEAD, 0), acc

flds = "campaign_name,spend,impressions,clicks,ctr,actions,reach,frequency"
rows = get(f"{ACT}/insights", level="campaign", fields=flds,
           time_range=json.dumps({"since": SINCE, "until": UNTIL}), limit=200)
print(f"=== META  {SINCE} a {UNTIL} ===")
tg = tc = 0
for f in sorted(rows, key=lambda x: -float(x.get("spend", 0))):
    c, _ = conv(f); g = float(f.get("spend", 0))
    if g < 1: continue
    tg += g; tc += c
    print(f"  {f['campaign_name'][:40]:<42} {g:>10,.0f} COP | {int(f.get('impressions',0)):>8,} impr |"
          f" {int(f.get('clicks',0)):>6,} clics | CTR {float(f.get('ctr',0) or 0):>4.2f}% |"
          f" {c:>5.0f} conv | CPA {(g/c if c else 0):>8,.0f}")
print(f"  {'TOTAL':<42} {tg:>10,.0f} COP | {tc:>5.0f} conv | CPA {(tg/tc if tc else 0):,.0f}")

print(f"\n=== META por dia ===")
d = get(f"{ACT}/insights", level="account", fields="spend,impressions,clicks,actions",
        time_range=json.dumps({"since": SINCE, "until": UNTIL}),
        time_increment="1", limit=100)
for f in d:
    c, _ = conv(f); g = float(f.get("spend", 0))
    print(f"  {f['date_start']}  {g:>9,.0f} COP | {int(f.get('clicks',0)):>6,} clics |"
          f" {c:>4.0f} conv | CPA {(g/c if c else 0):>8,.0f}")
