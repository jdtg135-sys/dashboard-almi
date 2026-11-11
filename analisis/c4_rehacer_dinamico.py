# -*- coding: utf-8 -*-
"""Rehace el conjunto y el anuncio dinamico de C4 (11-nov-2026).

El primer intento (conjunto 120253639897120392, anuncio 120253639907320392)
quedo con error y el usuario lo archivo. Meta no dejo registrado ni
ad_review_feedback ni issues_info, y el anuncio dinamico equivalente de C1
sigue activo sin problema, asi que la estructura no parece ser la causa.

Se reutiliza el creativo 1111913591468202, que ya tiene las 8 piezas cargadas:
no hace falta volver a subir 23 MB ni dejar activos duplicados en la cuenta.

Al final se consulta el estado varias veces, para ver el error en vivo si
vuelve a aparecer en lugar de reportar "en revision" y dejarlo.
"""
import json, os, sys, time, requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN = cred["access_token"]
ACT = str(cred["ad_account_id"])
ACT = ACT if ACT.startswith("act_") else "act_" + ACT
G = "https://graph.facebook.com/v19.0"

CAMPANA = "120252908058080392"
MODELO = "120252908058420392"          # retargeting-general
CREATIVO = "1111913591468202"
NOMBRE_CONJUNTO = "retargeting-dinamico-v2"
NOMBRE_ANUNCIO = "c4-dinamico-nov2026-v2"


def get(path, **p):
    p["access_token"] = TOKEN
    r = requests.get("%s/%s" % (G, path), params=p, timeout=90)
    r.raise_for_status()
    return r.json()


def post(path, data):
    data = dict(data)
    data["access_token"] = TOKEN
    r = requests.post("%s/%s" % (G, path), data=data, timeout=180)
    if r.status_code >= 400:
        raise SystemExit("ERROR en %s: %s" % (path, r.text[:700]))
    return r.json()


m = get(MODELO, fields="targeting,promoted_object,optimization_goal,"
                       "billing_event,attribution_spec")

conjunto = post("%s/adsets" % ACT, {
    "name": NOMBRE_CONJUNTO,
    "campaign_id": CAMPANA,
    "is_dynamic_creative": "true",
    "optimization_goal": m["optimization_goal"],
    "billing_event": m["billing_event"],
    "promoted_object": json.dumps(m["promoted_object"]),
    "attribution_spec": json.dumps(m["attribution_spec"]),
    "targeting": json.dumps(m["targeting"]),
    "status": "ACTIVE",
})
print("conjunto creado: %s" % conjunto["id"])

anuncio = post("%s/ads" % ACT, {
    "name": NOMBRE_ANUNCIO,
    "adset_id": conjunto["id"],
    "creative": json.dumps({"creative_id": CREATIVO}),
    "status": "ACTIVE",
})
print("anuncio creado:  %s" % anuncio["id"])
print()

for intento in range(10):
    time.sleep(15)
    a = get(anuncio["id"], fields="effective_status,issues_info")
    cj = get(conjunto["id"], fields="effective_status,issues_info")
    print("  [%2d] anuncio %-22s conjunto %s"
          % (intento + 1, a.get("effective_status"), cj.get("effective_status")))
    for quien, obj in (("anuncio", a), ("conjunto", cj)):
        for i in obj.get("issues_info", []) or []:
            print("       %s -> %s | %s" % (quien, i.get("error_summary"),
                                            i.get("error_message")))
    if a.get("effective_status") not in ("PENDING_REVIEW", "IN_PROCESS"):
        break

print()
print("ESTADO FINAL  anuncio: %s" % a.get("effective_status"))
print("              conjunto: %s" % cj.get("effective_status"))
