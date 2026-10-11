# -*- coding: utf-8 -*-
import os
import sys, os
# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE); os.chdir(BASE)
import actualizar_google_ads as A
from google.ads.googleads.client import GoogleAdsClient
creds = A.get_credentials()
cli = GoogleAdsClient.load_from_dict({
    "developer_token": A.DEVELOPER_TOKEN, "login_customer_id": A.LOGIN_CUSTOMER_ID,
    "refresh_token": creds.refresh_token, "client_id": creds.client_id,
    "client_secret": creds.client_secret, "use_proto_plus": True})
svc = cli.get_service("GoogleAdsService"); CID = A.CUSTOMER_ID
def q(query, titulo):
    print("\n=== " + titulo + " ===")
    try:
        for b in svc.search_stream(customer_id=CID, query=query):
            for r in b.results: yield r
    except Exception as e:
        print("  ERROR:", str(e)[:200])

for r in q("""SELECT segments.conversion_action_name, metrics.all_conversions
 FROM campaign WHERE segments.date BETWEEN '2026-09-20' AND '2026-10-08'""",
 "Conversiones por accion (20-sep a 8-oct)"):
    if r.metrics.all_conversions:
        print(f"  {r.metrics.all_conversions:>8,.1f} | {r.segments.conversion_action_name[:60]}")

for r in q("""SELECT campaign.name, campaign.status, campaign.advertising_channel_type,
 campaign.bidding_strategy_type, campaign_budget.amount_micros
 FROM campaign WHERE campaign.status != 'REMOVED'""", "Campanas"):
    c = r.campaign
    print(f"  {c.status.name:<8} {c.advertising_channel_type.name[:14]:<15} "
          f"{c.bidding_strategy_type.name[:24]:<25} presup {r.campaign_budget.amount_micros/1e6:>8,.0f} | {c.name[:38]}")

for r in q("""SELECT asset.type, asset.name, asset.id FROM asset
 WHERE asset.type IN ('IMAGE','YOUTUBE_VIDEO','TEXT') LIMIT 200""", "Recursos en la biblioteca"):
    pass
import collections
tipos = collections.Counter()
for r in q("""SELECT asset.type FROM asset LIMIT 2000""", "Recursos por tipo"):
    tipos[r.asset.type_.name] += 1
for t, n in tipos.most_common():
    print(f"  {t:<22} {n}")
