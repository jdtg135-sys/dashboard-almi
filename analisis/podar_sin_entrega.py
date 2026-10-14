# -*- coding: utf-8 -*-
"""Pausa los anuncios que Meta dejo de mostrar.

Por que: al 11-oct-2026 habia 133 anuncios activos y solo 43 recibian entrega
real. C1 llegaba a tener 44 anuncios en un conjunto con 14 entregando y 33 en
otro con 4. Repartir el aprendizaje entre tantos anuncios es una de las causas
de que dos conjuntos de C1 y C3 esten en "aprendizaje limitado".

Criterio: menos de 100 impresiones en 10 dias. Antes de pausar se comprueba
que el anuncio no haya recuperado entrega en los ultimos 3 dias (ninguno lo
hizo) y se respetan los que registren alguna conversion, por poca que sea.

Pausar un anuncio no esta en la lista de ediciones significativas de Meta
(segmentacion, objetivo, puja, presupuesto grande, creativo nuevo), asi que no
deberia reiniciar el aprendizaje del conjunto. Se aplica todo de una sola vez,
no goteado, para no repetir la perturbacion varios dias seguidos.

Uso:  python podar_sin_entrega.py        -> simulacion
      python podar_sin_entrega.py --go   -> aplica
"""
import json, os, sys, time, urllib.request, urllib.error, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AQUI = os.path.dirname(os.path.abspath(__file__))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN, ACT = cred["access_token"], cred["ad_account_id"]
G = "https://graph.facebook.com/v21.0/"
DRY = "--go" not in sys.argv
MIN_IMPR = 100
PURCHASE = "offsite_conversion.fb_pixel_purchase"


def get(path, **params):
    params["access_token"] = TOKEN
    url = G + path + "?" + urllib.parse.urlencode(params)
    out = []
    while url:
        try:
            d = json.load(urllib.request.urlopen(url))
        except urllib.error.HTTPError as e:
            raise SystemExit("error leyendo: " +
                             json.loads(e.read()).get("error", {}).get("message", "?")[:170])
        out += d.get("data", [])
        url = d.get("paging", {}).get("next")
    return out


activos = {}
for a in get(ACT + "/ads", fields="name,adset{name},campaign{name},effective_status", limit=500):
    camp = (a.get("campaign") or {}).get("name", "")
    if not camp.startswith(("C1", "C2", "C3", "C4")) or "Oct2026" not in camp:
        continue
    if a.get("effective_status") != "ACTIVE":
        continue
    activos[a["id"]] = (camp[:2], (a.get("adset") or {}).get("name", ""), a["name"])


def rendimiento(d1, d2):
    filas = get(ACT + "/insights", level="ad", limit=500,
                fields="ad_id,impressions,spend,actions",
                time_range=json.dumps({"since": d1, "until": d2}))
    out = {}
    for f in filas:
        acc = {x["action_type"]: float(x["value"]) for x in f.get("actions", [])}
        out[f["ad_id"]] = (int(f.get("impressions", 0)), float(f.get("spend", 0)),
                           acc.get(PURCHASE, 0))
    return out


todo = rendimiento("2026-10-02", "2026-10-11")
reciente = rendimiento("2026-10-09", "2026-10-11")

podar, salvados = [], []
for aid, (camp, conj, nom) in activos.items():
    im, gs, cv = todo.get(aid, (0, 0.0, 0))
    im_rec = reciente.get(aid, (0, 0, 0))[0]
    if im >= MIN_IMPR:
        continue
    if cv > 0:
        salvados.append((nom, im, cv, "tiene conversion")); continue
    if im_rec >= MIN_IMPR:
        salvados.append((nom, im, cv, "recupero entrega")); continue
    podar.append({"id": aid, "campana": camp, "conjunto": conj, "nombre": nom,
                  "impresiones": im, "gasto": gs})

porcamp = {}
for p in podar:
    porcamp.setdefault(p["campana"], []).append(p)
print(f"ANUNCIOS A PAUSAR: {len(podar)} de {len(activos)} activos\n")
for k in sorted(porcamp):
    v = porcamp[k]
    print(f"  {k}: {len(v)} anuncios | {sum(x['gasto'] for x in v):,.0f} COP gastados en 10 dias")
if salvados:
    print(f"\n  se respetan {len(salvados)}:")
    for nom, im, cv, por in salvados:
        print(f"      {nom[:46]:<48} {im:>5,} impr | {cv:.0f} conv | {por}")

if DRY:
    print("\nSIMULACION. Ejecutar con --go para aplicar.")
    raise SystemExit

ok = fallo = 0
fallos = []
for i in range(0, len(podar), 50):
    lote = podar[i:i + 50]
    batch = [{"method": "POST", "relative_url": p["id"], "body": "status=PAUSED"} for p in lote]
    for intento in range(5):
        r = urllib.request.Request(G, data=urllib.parse.urlencode(
            {"access_token": TOKEN, "batch": json.dumps(batch)}).encode())
        try:
            res = json.load(urllib.request.urlopen(r))
            break
        except urllib.error.HTTPError as e:
            err = json.loads(e.read()).get("error", {})
            if err.get("code") in (17, 4, 613):
                espera = 60 * (intento + 1)
                print(f"  limite de la API, esperando {espera}s...", flush=True)
                time.sleep(espera); continue
            raise SystemExit("batch -> " + str(err)[:200])
    for p, rr in zip(lote, res):
        if rr and rr.get("code") == 200:
            ok += 1
        else:
            fallo += 1; fallos.append((p["nombre"], str(rr)[:90]))
    print(f"  lote {i//50 + 1}: {ok} pausados, {fallo} fallidos", flush=True)
    time.sleep(3)

print(f"\nRESULTADO: {ok} pausados, {fallo} fallidos")
for n, m in fallos[:10]:
    print("   FALLA", n[:40], "::", m)
json.dump(podar, open(os.path.join(AQUI, "podados_11oct.json"), "w"),
          ensure_ascii=False, indent=1)
