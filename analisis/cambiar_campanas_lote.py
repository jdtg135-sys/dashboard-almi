# -*- coding: utf-8 -*-
"""Corte de campanas usando la API por lotes de Meta.

Recorrer 134 anuncios con una llamada cada uno agota la cuota de la cuenta.
El endpoint /batch admite 50 operaciones por llamada, asi que todo el corte
cabe en 3 peticiones. Los ids salen de los archivos locales, de modo que no
hace falta ninguna lectura previa salvo la de las campanas viejas.

Uso:  python cambiar_campanas_lote.py          -> simulacion
      python cambiar_campanas_lote.py --go     -> aplica
"""
import os
import json, os, sys, time, requests

# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AQUI = os.path.dirname(os.path.abspath(__file__))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN, ACT = cred["access_token"], cred["ad_account_id"]
G = "https://graph.facebook.com/v21.0/"
DRY = "--go" not in sys.argv

VIEJAS = ("C1 - Convenio por Sectores - Jun2026", "C2 - Empleados sector privado",
          "C3 - Reportados", "C4 - Retargeting caliente")

estructura = json.load(open(os.path.join(AQUI, "estructura_nueva.json"), encoding="utf-8"))
anuncios = json.load(open(os.path.join(AQUI, "anuncios_creados.json"), encoding="utf-8"))

ops = []   # (id, estado, etiqueta)
for nombre, c in estructura.items():
    ops.append((c["id"], "ACTIVE", "campana " + nombre[:30]))
    for slug, aid in c["conjuntos"].items():
        ops.append((aid, "ACTIVE", "  conjunto " + slug))
for nombre, aid in sorted(anuncios.items()):
    ops.append((aid, "ACTIVE", "    anuncio " + nombre))

# las viejas se pausan: hace falta una lectura para sus ids
r = requests.get(G + ACT + "/campaigns",
                 params={"access_token": TOKEN, "fields": "name,status", "limit": 200}, timeout=90)
if r.status_code != 200:
    raise SystemExit("no se pudieron leer las campanas: " + r.text[:160])
viejas_ids = [(c["id"], c["name"]) for c in r.json()["data"] if c["name"] in VIEJAS]
for cid, n in viejas_ids:
    ops.append((cid, "PAUSED", "PAUSAR " + n[:34]))

print(f"operaciones: {len(ops)}  ({len(anuncios)} anuncios, {len(viejas_ids)} campanas a pausar)")
if DRY:
    for i, (_, e, et) in enumerate(ops[:6]):
        print(f"   {e:7s} {et}")
    print("   ...")
    print("\nSIMULACION. Ejecutar con --go para aplicar.")
    raise SystemExit

ok = fallo = 0
fallos = []
for i in range(0, len(ops), 50):
    lote = ops[i:i + 50]
    batch = [{"method": "POST", "relative_url": o[0], "body": "status=" + o[1]} for o in lote]
    for intento in range(5):
        rr = requests.post(G, data={"access_token": TOKEN, "batch": json.dumps(batch)}, timeout=180)
        if rr.status_code == 200:
            break
        e = rr.json().get("error", {})
        if e.get("code") in (17, 4, 613):
            espera = 90 * (intento + 1)
            print(f"  limite de API, esperando {espera}s...", flush=True)
            time.sleep(espera); continue
        raise SystemExit("batch -> " + rr.text[:200])
    for o, res in zip(lote, rr.json()):
        if res and res.get("code") == 200:
            ok += 1
        else:
            fallo += 1
            fallos.append((o[2], str(res)[:110]))
    print(f"  lote {i//50 + 1}: {ok} ok, {fallo} fallidos", flush=True)
    time.sleep(3)

print(f"\nRESULTADO: {ok} operaciones aplicadas, {fallo} fallidas")
for et, msg in fallos[:10]:
    print("   FALLA", et, "::", msg)
