# -*- coding: utf-8 -*-
"""Ajusta presupuestos de campana sin sacar los conjuntos de la fase de aprendizaje.

Meta reinicia el aprendizaje cuando una edicion es "significativa". Un cambio de
presupuesto grande cuenta como tal; la practica segura es no pasar del 20% por
cambio y espaciarlos. Aqui el tope es 15%, y el script se niega a aplicar
cualquier cambio que lo supere.

El presupuesto de estas campanas vive en la CAMPANA (presupuesto ventaja+),
no en el conjunto, asi que se edita ahi.

Uso:  python ajustar_presupuestos.py        -> simulacion
      python ajustar_presupuestos.py --go   -> aplica
"""
import json, os, sys, urllib.request, urllib.error, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN, ACT = cred["access_token"], cred["ad_account_id"]
G = "https://graph.facebook.com/v21.0/"
DRY = "--go" not in sys.argv
TOPE = 0.15

# Solo se suben las campanas que SI estan topadas por presupuesto.
# C2 y C4 quedan intactas: dejan ~18.000 diarios sin usar, asi que bajarles
# el presupuesto no libera nada y recortarlas les cortaria los dias buenos
# (C2 gasto 102.832 el 9 de octubre).
NUEVOS = {
    "C1 - Convenio por sectores - Oct2026": 69_000,   # desde 60.000, +15%
    "C3 - Reportados - Oct2026":            23_000,   # desde 20.000, +15%
}


def get(path, **params):
    params["access_token"] = TOKEN
    url = G + path + "?" + urllib.parse.urlencode(params)
    out = []
    while url:
        try:
            d = json.load(urllib.request.urlopen(url))
        except urllib.error.HTTPError as e:
            raise SystemExit("error leyendo: " +
                             json.loads(e.read()).get("error", {}).get("message", "?")[:160])
        out += d.get("data", [])
        url = d.get("paging", {}).get("next")
    return out


campanas = {c["name"]: c for c in get(ACT + "/campaigns",
            fields="name,daily_budget,effective_status", limit=100)}

# Antes de tocar nada: ningun conjunto puede estar en aprendizaje.
print("Fase de aprendizaje de los conjuntos afectados")
bloqueado = False
for a in get(ACT + "/adsets", fields="name,campaign{name},effective_status,learning_stage_info",
             limit=200):
    camp = (a.get("campaign") or {}).get("name", "")
    if camp not in NUEVOS or a.get("effective_status") != "ACTIVE":
        continue
    fase = (a.get("learning_stage_info") or {}).get("status", "SIN_DATO")
    print(f"   {camp[:34]:<36} / {a['name'][:22]:<24} {fase}")
    if fase == "LEARNING":
        print("      ESTA APRENDIENDO: tocarlo ahora reiniciaria el ciclo")
        bloqueado = True
if bloqueado:
    raise SystemExit("\nHay conjuntos en aprendizaje. No se aplica nada.")

print("\nCambios")
ops = []
for nombre, nuevo in NUEVOS.items():
    c = campanas.get(nombre)
    if not c:
        print(f"   NO ENCONTRADA: {nombre}")
        continue
    actual = int(c.get("daily_budget", 0) or 0)
    if not actual:
        print(f"   {nombre[:40]}: sin presupuesto de campana, se omite")
        continue
    var = (nuevo - actual) / actual
    marca = "OK" if abs(var) <= TOPE else "EXCEDE EL TOPE"
    print(f"   {nombre[:40]:<42} {actual:>7,} -> {nuevo:>7,}  ({var*100:+5.1f}%)  {marca}")
    if abs(var) > TOPE:
        print("      se omite para no reiniciar el aprendizaje")
        continue
    ops.append((c["id"], nombre, nuevo))

if DRY:
    print("\nSIMULACION. Ejecutar con --go para aplicar.")
    raise SystemExit

for cid, nombre, nuevo in ops:
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            G + cid, data=urllib.parse.urlencode(
                {"access_token": TOKEN, "daily_budget": nuevo}).encode()))
        json.load(r)
    except urllib.error.HTTPError as e:
        print("   ERROR", nombre[:34], "::",
              json.loads(e.read()).get("error", {}).get("message", "?")[:140])
        continue
    v = json.load(urllib.request.urlopen(
        G + cid + "?" + urllib.parse.urlencode(
            {"access_token": TOKEN, "fields": "name,daily_budget,effective_status"})))
    print(f"   aplicado: {v['name'][:40]:<42} {int(v['daily_budget']):>7,} | {v['effective_status']}")

print("\nLISTO")
