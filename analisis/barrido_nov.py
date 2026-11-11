# -*- coding: utf-8 -*-
"""Barrido de Meta: 1 al 8 de noviembre contra octubre (9-nov-2026).

TRAMPA DE LA API (ya costo un error antes)
------------------------------------------
Si se pide `spend` junto con `actions` y `time_increment=1`, Meta devuelve
spend = 0. Hay que hacer DOS llamadas y cruzarlas por fecha.
"""
import json, os, requests
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
T = cred["access_token"]
A = str(cred["ad_account_id"]); A = A if A.startswith("act_") else "act_" + A
G = "https://graph.facebook.com/v19.0"

CONV = ("offsite_conversion.fb_pixel_purchase",)


def pedir(fields, since, until, nivel="account", extra=None):
    p = {"access_token": T, "fields": ",".join(fields), "level": nivel,
         "time_range": json.dumps({"since": since, "until": until}), "limit": 500}
    if extra:
        p.update(extra)
    out, url = [], "%s/%s/insights" % (G, A)
    while url:
        r = requests.get(url, params=p, timeout=120)
        r.raise_for_status()
        j = r.json()
        out += j.get("data", [])
        url = (j.get("paging") or {}).get("next")
        p = None
    return out


def conv_de(fila):
    tot = 0
    for a in fila.get("actions", []):
        if a["action_type"] in CONV:
            tot += float(a["value"])
    return tot


def bloque(titulo, since, until, diario=False):
    extra = {"time_increment": 1} if diario else None
    costos = pedir(["spend", "impressions", "reach", "frequency", "cpm", "cpc",
                    "ctr", "clicks", "inline_link_clicks"], since, until, extra=extra)
    acc = pedir(["actions"], since, until, extra=extra)
    ca = {f.get("date_start", "tot"): conv_de(f) for f in acc}
    print("\n=== %s (%s a %s) ===" % (titulo, since, until))
    if diario:
        print("%-11s %9s %7s %9s %7s %6s %6s %7s %8s" % (
            "fecha", "gasto", "conv", "costo", "CPM", "CTR", "frec", "clics", "CPC"))
    tg = tc = ti = tcl = 0
    for f in costos:
        d = f.get("date_start", "tot")
        g = float(f.get("spend", 0)); c = ca.get(d, 0)
        imp = float(f.get("impressions", 0)); cl = float(f.get("inline_link_clicks", 0) or 0)
        tg += g; tc += c; ti += imp; tcl += cl
        if diario:
            print("%-11s %9.0f %7.0f %9.0f %7.0f %6.2f %6.2f %7.0f %8.0f" % (
                d, g, c, (g / c if c else 0), float(f.get("cpm", 0)),
                float(f.get("ctr", 0) or 0), float(f.get("frequency", 0) or 0),
                cl, float(f.get("cpc", 0) or 0)))
    print("-" * 78)
    print("TOTAL      %9.0f %7.0f %9.0f  CPM %.0f  clics %.0f  conv/clic %.2f%%" % (
        tg, tc, (tg / tc if tc else 0), (tg / ti * 1000 if ti else 0), tcl,
        (tc / tcl * 100 if tcl else 0)))
    return tg, tc, ti, tcl


bloque("NOVIEMBRE dia a dia", "2026-11-01", "2026-11-08", diario=True)
bloque("OCTUBRE completo", "2026-10-01", "2026-10-31")
bloque("OCTUBRE 1-8 (mismo tramo)", "2026-10-01", "2026-10-08")
bloque("OCTUBRE ultima semana", "2026-10-23", "2026-10-31")

for titulo, s, u in (("NOVIEMBRE 1-8", "2026-11-01", "2026-11-08"),
                     ("OCTUBRE 23-31", "2026-10-23", "2026-10-31")):
    print("\n=== Por campana: %s ===" % titulo)
    costos = pedir(["campaign_name", "spend", "impressions", "cpm", "ctr",
                    "frequency", "inline_link_clicks"], s, u, nivel="campaign")
    acc = pedir(["campaign_name", "actions"], s, u, nivel="campaign")
    ca = {f["campaign_name"]: conv_de(f) for f in acc}
    print("%-44s %10s %7s %9s %7s %6s %6s" % (
        "campana", "gasto", "conv", "costo", "CPM", "CTR", "frec"))
    for f in sorted(costos, key=lambda x: -float(x.get("spend", 0))):
        n = f["campaign_name"]; g = float(f["spend"]); c = ca.get(n, 0)
        print("%-44s %10.0f %7.0f %9.0f %7.0f %6.2f %6.2f" % (
            n[:44], g, c, (g / c if c else 0), float(f.get("cpm", 0)),
            float(f.get("ctr", 0) or 0), float(f.get("frequency", 0) or 0)))
