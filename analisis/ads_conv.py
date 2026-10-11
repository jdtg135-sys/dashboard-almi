# -*- coding: utf-8 -*-
import os
import sys, os, collections
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
d = collections.defaultdict(lambda: collections.defaultdict(float))
for b in svc.search_stream(customer_id=CID, query="""
 SELECT segments.date, segments.conversion_action_name,
        metrics.all_conversions, metrics.all_conversions_value
 FROM campaign WHERE segments.date BETWEEN '2026-09-26' AND '2026-10-08'"""):
    for r in b.results:
        if r.metrics.all_conversions:
            n = r.segments.conversion_action_name
            d[r.segments.date][n] += r.metrics.all_conversions
nombres = sorted({n for v in d.values() for n in v})
print("fecha        " + "  ".join(f"{n[-26:]:>28}" for n in nombres))
for f in sorted(d):
    print(f"{f}  " + "  ".join(f"{d[f].get(n,0):>28,.0f}" for n in nombres))
