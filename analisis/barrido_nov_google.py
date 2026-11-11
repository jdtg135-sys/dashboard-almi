# -*- coding: utf-8 -*-
"""Barrido de Google Ads: 1 al 8 de noviembre contra octubre (9-nov-2026)."""
import datetime, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from actualizar_google_ads import (get_credentials, DEVELOPER_TOKEN,
                                   LOGIN_CUSTOMER_ID, CUSTOMER_ID,
                                   CLIENT_SECRET_FILE)
from google.ads.googleads.client import GoogleAdsClient

creds = get_credentials()
sec = json.load(open(CLIENT_SECRET_FILE))["installed"]
cli = GoogleAdsClient.load_from_dict({
    "developer_token": DEVELOPER_TOKEN,
    "client_id": sec["client_id"], "client_secret": sec["client_secret"],
    "refresh_token": creds.refresh_token,
    "login_customer_id": LOGIN_CUSTOMER_ID, "use_proto_plus": True})
svc = cli.get_service("GoogleAdsService")
M = 1_000_000


def q(sel, desde, hasta, extra=""):
    s = ("SELECT %s FROM campaign WHERE segments.date BETWEEN '%s' AND '%s' "
         "AND metrics.impressions > 0 %s" % (sel, desde, hasta, extra))
    return list(svc.search(customer_id=CUSTOMER_ID, query=s))


def dia_a_dia(desde, hasta):
    filas = q("segments.date, metrics.cost_micros, metrics.conversions, "
              "metrics.impressions, metrics.clicks, metrics.average_cpc", desde, hasta)
    acc = {}
    for f in filas:
        d = f.segments.date
        a = acc.setdefault(d, [0, 0, 0, 0])
        a[0] += f.metrics.cost_micros / M
        a[1] += f.metrics.conversions
        a[2] += f.metrics.impressions
        a[3] += f.metrics.clicks
    print("%-11s %9s %7s %9s %8s %7s" % ("fecha", "gasto", "conv", "costo", "impr", "clics"))
    tg = tc = 0
    for d in sorted(acc):
        g, c, i, cl = acc[d]
        tg += g; tc += c
        print("%-11s %9.0f %7.1f %9.0f %8.0f %7.0f" % (d, g, c, (g / c if c else 0), i, cl))
    print("-" * 56)
    print("TOTAL       %9.0f %7.1f %9.0f" % (tg, tc, (tg / tc if tc else 0)))
    return tg, tc


def por_campana(titulo, desde, hasta):
    filas = q("campaign.name, campaign.advertising_channel_type, campaign.status, "
              "metrics.cost_micros, metrics.conversions, metrics.impressions, "
              "metrics.clicks, metrics.search_impression_share, "
              "metrics.search_budget_lost_impression_share, "
              "metrics.search_rank_lost_impression_share, metrics.average_cpc",
              desde, hasta)
    acc = {}
    for f in filas:
        k = (f.campaign.name, f.campaign.advertising_channel_type.name, f.campaign.status.name)
        a = acc.setdefault(k, [0, 0, 0, 0, [], [], []])
        a[0] += f.metrics.cost_micros / M
        a[1] += f.metrics.conversions
        a[2] += f.metrics.impressions
        a[3] += f.metrics.clicks
        if f.metrics.search_impression_share:
            a[4].append(f.metrics.search_impression_share)
        if f.metrics.search_budget_lost_impression_share:
            a[5].append(f.metrics.search_budget_lost_impression_share)
        if f.metrics.search_rank_lost_impression_share:
            a[6].append(f.metrics.search_rank_lost_impression_share)
    print("\n=== Google por campana: %s ===" % titulo)
    print("%-40s %-10s %9s %7s %9s %7s %7s %7s" % (
        "campana", "tipo", "gasto", "conv", "costo", "IS%", "perdIS$", "perdISr"))
    for k in sorted(acc, key=lambda x: -acc[x][0]):
        g, c, i, cl, isa, bl, rl = acc[k]
        prom = lambda L: (sum(L) / len(L) * 100) if L else 0
        print("%-40s %-10s %9.0f %7.1f %9.0f %7.1f %7.1f %7.1f" % (
            k[0][:40], k[1][:10], g, c, (g / c if c else 0),
            prom(isa), prom(bl), prom(rl)))


print("=== Google dia a dia: NOVIEMBRE ===")
dia_a_dia("2026-11-01", "2026-11-08")
print("\n=== Google dia a dia: OCTUBRE 23-31 ===")
dia_a_dia("2026-10-23", "2026-10-31")
por_campana("NOVIEMBRE 1-8", "2026-11-01", "2026-11-08")
por_campana("OCTUBRE 23-31", "2026-10-23", "2026-10-31")
por_campana("NOVIEMBRE 5-8 (despues del recorte)", "2026-11-05", "2026-11-08")
