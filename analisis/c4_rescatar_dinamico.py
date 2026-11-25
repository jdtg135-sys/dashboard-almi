# -*- coding: utf-8 -*-
"""Rescata el conjunto dinamico de C4, que el presupuesto de campana ahogo (13-nov-2026).

EL PROBLEMA
-----------
Del 9 al 12 de noviembre, dentro de C4:

    retargeting-general       590.521 de gasto   196 conversiones
    retargeting-dinamico-v2     5.443 de gasto     1 conversion

Es el efecto conocido del presupuesto de campana (CBO): Meta reparte hacia el
conjunto con historial y no le da oportunidad al nuevo. Con 1.300 diarios, el
conjunto dinamico nunca va a juntar las 50 conversiones semanales que necesita
para salir de aprendizaje, asi que el lote nuevo de piezas NO se esta probando.

Ocurre lo mismo en C1: `general-convenio` lleva 24.085 contra 383.244 de
`sectores-alto-volumen`. Ese queda pendiente de decision aparte.

LA SOLUCION
-----------
`daily_min_spend_target` en el conjunto: un piso de gasto diario que CBO tiene
que respetar. Es lo que Meta ofrece justamente para esto, y no obliga a apagar
el presupuesto de campana ni a tocar el conjunto que ya funciona.

Se fija en 50.000, un tercio del presupuesto de C4. Al costo actual de C4 son
unas 17 conversiones diarias: supera las 50 semanales y en una semana habra una
comparacion real entre el lote nuevo y video-6.

El conjunto dinamico ya estaba en aprendizaje sin datos, asi que no hay fase que
perder. `retargeting-general` no se toca.

Uso:  python c4_rescatar_dinamico.py        -> simula
      python c4_rescatar_dinamico.py --go   -> lo aplica
"""
import json, os, sys, requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN = cred["access_token"]
G = "https://graph.facebook.com/v19.0"
DRY = "--go" not in sys.argv

# Mismo problema y misma solucion en C1: `general-convenio` llevaba 24.085 de
# gasto contra 383.244 de `sectores-alto-volumen` en los mismos cuatro dias.
# Se pasa el conjunto por argumento para no duplicar el script.
#   python c4_rescatar_dinamico.py c4 --go
#   python c4_rescatar_dinamico.py c1 --go
CUALES = {
    # clave: (id del conjunto,        piso,   presupuesto de la campana)
    "c4": ("120253640705050392",   50_000, 148_437),   # retargeting-dinamico-v2
    "c1": ("120253522650360392",   34_000, 102_350),   # general-convenio
}
_cual = next((x for x in sys.argv[1:] if x in CUALES), "c4")
CONJUNTO, PISO, PRESU_C4 = CUALES[_cual]

a = requests.get("%s/%s" % (G, CONJUNTO), params={
    "access_token": TOKEN,
    "fields": "name,status,effective_status,daily_min_spend_target,campaign{name,daily_budget}"
}).json()
if "error" in a:
    raise SystemExit("Meta: " + a["error"].get("message", "?")[:200])

print("Conjunto : %s  (%s)" % (a.get("name"), CONJUNTO))
print("Campaña  : %s" % (a.get("campaign") or {}).get("name"))
print("Presupuesto de campaña: %s diarios"
      % format(int((a.get("campaign") or {}).get("daily_budget") or PRESU_C4), ","))
print()
print("  piso de gasto actual : %s" % (a.get("daily_min_spend_target") or "sin piso"))
print("  piso que se fija     : %s  (%.0f%% del presupuesto de la campaña)"
      % (format(PISO, ","), PISO / PRESU_C4 * 100))
print()
print("  retargeting-general NO se toca.")

if DRY:
    print("\nSIMULACION. Ejecutar con --go para aplicarlo.")
    raise SystemExit

r = requests.post("%s/%s" % (G, CONJUNTO), data={
    "access_token": TOKEN,
    "daily_min_spend_target": PISO,
}, timeout=90)
if r.status_code >= 400:
    raise SystemExit("ERROR: %s" % r.text[:600])
print("aplicado: %s" % r.text[:200])

v = requests.get("%s/%s" % (G, CONJUNTO), params={
    "access_token": TOKEN, "fields": "name,daily_min_spend_target,effective_status"}).json()
print("verificado -> piso %s · estado %s"
      % (v.get("daily_min_spend_target"), v.get("effective_status")))
