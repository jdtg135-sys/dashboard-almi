# -*- coding: utf-8 -*-
"""Revisa si Meta esta recibiendo el valor de conversion y desde cuando.

Compara, por dia, las conversiones de pixel (Purchase) contra el valor que
Meta les asigna. Si hay conversiones y el valor es cero, el pixel esta
mandando value: 0.
"""
import os, json, datetime, requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH = "https://graph.facebook.com/v19.0"
cred = json.load(open(os.path.join(BASE, "meta_credentials.json"), encoding="utf-8"))
TOKEN = cred.get("access_token") or cred.get("token")
CUENTA = cred.get("account_id") or cred.get("ad_account_id")
if CUENTA and not str(CUENTA).startswith("act_"):
    CUENTA = "act_%s" % CUENTA
ACC = "offsite_conversion.fb_pixel_purchase"

hoy = datetime.date.today()
desde = hoy - datetime.timedelta(days=27)

r = requests.get("%s/%s/insights" % (GRAPH, CUENTA), params={
    "fields": "actions,action_values",
    "time_range": json.dumps({"since": str(desde), "until": str(hoy)}),
    "time_increment": 1,
    "access_token": TOKEN,
}, timeout=60)
r.raise_for_status()
filas = r.json().get("data", [])

print("Cuenta: %s" % CUENTA)
print()
print("%-12s %10s %18s %14s" % ("dia", "compras", "valor reportado", "valor/compra"))
print("-" * 58)
tot_n = tot_v = 0
for f in filas:
    n = v = 0.0
    for a in f.get("actions", []):
        if a.get("action_type") == ACC:
            n = float(a.get("value", 0))
    for a in f.get("action_values", []):
        if a.get("action_type") == ACC:
            v = float(a.get("value", 0))
    tot_n += n; tot_v += v
    prom = (v / n) if n else 0
    print("{:<12} {:>10,.0f} {:>18,.0f} {:>14,.0f}".format(f["date_start"], n, v, prom))
print("-" * 58)
print("{:<12} {:>10,.0f} {:>18,.0f} {:>14,.0f}".format(
    "TOTAL", tot_n, tot_v, (tot_v / tot_n) if tot_n else 0))
print()

# Que otros tipos de valor reporta la cuenta, por si el valor llega bajo otro nombre.
r2 = requests.get("%s/%s/insights" % (GRAPH, CUENTA), params={
    "fields": "action_values",
    "time_range": json.dumps({"since": str(desde), "until": str(hoy)}),
    "access_token": TOKEN,
}, timeout=60)
vals = (r2.json().get("data") or [{}])[0].get("action_values", [])
print("Todos los valores que reporta la cuenta en el periodo:")
if not vals:
    print("  (ninguno: Meta no esta recibiendo valor en ningun evento)")
for a in vals:
    print("  %-46s %s" % (a.get("action_type"), a.get("value")))
