# -*- coding: utf-8 -*-
"""Crea las campanas C1..C4 nuevas y sus conjuntos, TODO EN PAUSA.

Clona la segmentacion exacta de los conjuntos actuales. No toca nada existente.
Guarda los ids creados en estructura_nueva.json.
"""
import os
import json, os, sys, requests

# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN, ACT = cred["access_token"], cred["ad_account_id"]
G = "https://graph.facebook.com/v21.0/"
AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "estructura_nueva.json")
PIXEL = "1749544856232374"
DRY = "--go" not in sys.argv

# nombre viejo -> (nombre nuevo de campana, presupuesto diario COP)
CAMPANAS = {
    "C1 - Convenio por Sectores - Jun2026": ("C1 - Convenio por sectores - Oct2026", 60000),
    "C2 - Empleados sector privado":        ("C2 - Empleados sector privado - Oct2026", 95000),
    "C3 - Reportados":                      ("C3 - Reportados - Oct2026", 20000),
    "C4 - Retargeting caliente":            ("C4 - Retargeting caliente - Oct2026", 95000),
}

# nombres de conjunto en formato slug, para que las UTM salgan limpias
SLUG_CONJUNTO = {
    "Conjunto 1 - Sectores alto volumen":  "sectores-alto-volumen",
    "Conjunto 2 - Sectores especializados": "sectores-especializados",
    "Conjunto 3 - Lookalike Solicitantes":  "lookalike-solicitantes",
    "Segmentación LOOKALIKE  3% al 5%":     "lookalike-3-5",
    "Segmentación advantage + FRIO":        "advantage-frio",
    "reportados advantage+":                "reportados-advantage",
    "retargeting general":                  "retargeting-general",
}

# campos de targeting que la API devuelve pero no acepta al crear
QUITAR = {"brand_safety_content_filter_levels", "targeting_relaxation_types",
          "targeting_optimization", "is_whatsapp_destination_ad"}


def get(path, **q):
    q["access_token"] = TOKEN
    r = requests.get(G + path, params=q, timeout=60)
    if r.status_code != 200:
        raise SystemExit("GET " + path + " -> " + r.text[:300])
    return r.json()


def post(path, payload):
    payload["access_token"] = TOKEN
    r = requests.post(G + path, data=payload, timeout=120)
    if r.status_code != 200:
        print("   ERROR:", r.json().get("error", {}).get("message", "?")[:220])
        return None
    return r.json()


def limpiar(t):
    t = {k: v for k, v in t.items() if k not in QUITAR}
    for k in ("custom_audiences", "excluded_custom_audiences"):
        if t.get(k):
            t[k] = [{"id": a["id"]} for a in t[k]]
    return t


todas = get(ACT + "/campaigns", fields="name,status,objective", limit=200)["data"]
viejas = {c["name"]: c for c in todas
          if c["name"] in CAMPANAS and c["status"] == "ACTIVE"}

# idempotencia: si la campana nueva ya existe, no se vuelve a crear
YA_EXISTEN = {c["name"] for c in todas}

salida = {}
for viejo, (nuevo, presupuesto) in CAMPANAS.items():
    cv = viejas.get(viejo)
    if not cv:
        print("no encontrada:", viejo); continue
    if nuevo in YA_EXISTEN:
        print("=" * 80); print(nuevo, "YA EXISTE, se omite"); continue
    print("=" * 80)
    print(nuevo, f"| {presupuesto:,} COP/dia")

    conjuntos = [a for a in get(cv["id"] + "/adsets",
                                fields="name,status,billing_event,optimization_goal,"
                                       "attribution_spec,targeting,promoted_object,destination_type",
                                limit=50)["data"] if a["status"] == "ACTIVE"]

    if DRY:
        for a in conjuntos:
            print("   conjunto:", SLUG_CONJUNTO.get(a["name"], a["name"]))
        continue

    cr = post(ACT + "/campaigns", {
        "name": nuevo, "objective": "OUTCOME_SALES", "status": "PAUSED",
        "special_ad_categories": json.dumps([]),
        "buying_type": "AUCTION", "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "daily_budget": presupuesto,
    })
    if not cr:
        continue
    cid = cr["id"]
    print("   campana creada:", cid)
    salida[nuevo] = {"id": cid, "conjuntos": {}}

    for a in conjuntos:
        slug = SLUG_CONJUNTO.get(a["name"], a["name"])
        r = post(ACT + "/adsets", {
            "name": slug, "campaign_id": cid, "status": "PAUSED",
            "billing_event": a.get("billing_event", "IMPRESSIONS"),
            "optimization_goal": a.get("optimization_goal", "OFFSITE_CONVERSIONS"),
            "attribution_spec": json.dumps(a.get("attribution_spec")),
            "targeting": json.dumps(limpiar(a["targeting"])),
            "promoted_object": json.dumps(a.get("promoted_object") or
                                          {"pixel_id": PIXEL, "custom_event_type": "PURCHASE"}),
        })
        if r:
            print("   conjunto creado:", slug, r["id"])
            salida[nuevo]["conjuntos"][slug] = r["id"]

if DRY:
    print("\nSIMULACION. Ejecutar con --go para crear.")
elif salida:
    # se fusiona con lo que ya hubiera: si esta corrida no creo nada porque todo
    # existia, no se debe borrar el mapa de ids anterior
    previo = json.load(open(SALIDA, encoding="utf-8")) if os.path.exists(SALIDA) else {}
    previo.update(salida)
    json.dump(previo, open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nGuardado en", SALIDA)
else:
    print("\nNo se creo nada nuevo; se conserva", SALIDA)
