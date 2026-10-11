# -*- coding: utf-8 -*-
import os
import sys, os, json
# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
os.chdir(BASE)
import actualizar_google_ads as A
from google.ads.googleads.client import GoogleAdsClient

creds = A.get_credentials()
cli = GoogleAdsClient.load_from_dict({
    "developer_token": A.DEVELOPER_TOKEN,
    "login_customer_id": A.LOGIN_CUSTOMER_ID,
    "refresh_token": creds.refresh_token,
    "client_id": creds.client_id, "client_secret": creds.client_secret,
    "use_proto_plus": True,
})
svc = cli.get_service("GoogleAdsService")
SINCE, UNTIL = sys.argv[1], sys.argv[2]

q = f"""SELECT campaign.name, campaign.status, campaign_budget.amount_micros,
 metrics.impressions, metrics.clicks, metrics.ctr, metrics.cost_micros,
 metrics.conversions, metrics.cost_per_conversion
 FROM campaign WHERE segments.date BETWEEN '{SINCE}' AND '{UNTIL}'
 ORDER BY metrics.cost_micros DESC"""
print(f"=== GOOGLE ADS  {SINCE} a {UNTIL} ===")
tg = tc = 0.0
for b in svc.search_stream(customer_id=A.CUSTOMER_ID, query=q):
    for r in b.results:
        g = r.metrics.cost_micros / 1e6; c = r.metrics.conversions
        if g < 1 and c == 0: continue
        tg += g; tc += c
        print(f"  {r.campaign.name[:38]:<40} {r.campaign.status.name[:8]:<9}"
              f" presup {r.campaign_budget.amount_micros/1e6:>8,.0f} |"
              f" {g:>9,.0f} COP | {r.metrics.impressions:>7,} impr |"
              f" {r.metrics.clicks:>5,} clics | CTR {r.metrics.ctr*100:>4.2f}% |"
              f" {c:>5.1f} conv | CPA {(g/c if c else 0):>8,.0f}")
print(f"  {'TOTAL':<40} {tg:>9,.0f} COP | {tc:>5.1f} conv | CPA {(tg/tc if tc else 0):,.0f}")

q2 = f"""SELECT segments.date, metrics.cost_micros, metrics.clicks, metrics.conversions
 FROM customer WHERE segments.date BETWEEN '{SINCE}' AND '{UNTIL}' ORDER BY segments.date"""
print("\n=== GOOGLE por dia ===")
for b in svc.search_stream(customer_id=A.CUSTOMER_ID, query=q2):
    for r in b.results:
        g = r.metrics.cost_micros / 1e6; c = r.metrics.conversions
        print(f"  {r.segments.date}  {g:>8,.0f} COP | {r.metrics.clicks:>5,} clics |"
              f" {c:>5.1f} conv | CPA {(g/c if c else 0):>8,.0f}")
