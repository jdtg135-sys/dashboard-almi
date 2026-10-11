# -*- coding: utf-8 -*-
"""Sube las piezas de Pauta Almi a la biblioteca de la cuenta publicitaria.

Guarda {ruta_relativa: image_hash} en hashes_imagenes.json. Es reanudable:
lo ya subido se omite.
"""
import json, os, requests

BASE = r"C:\Users\juanc\OneDrive\Documentos\Clientes\ALMI Financiera"
PIEZAS = os.path.join(BASE, "Pauta Almi")
cred = json.load(open(os.path.join(BASE, "Dashboard ALMI", "meta_credentials.json")))
TOKEN, ACT = cred["access_token"], cred["ad_account_id"]
SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hashes_imagenes.json")

hashes = json.load(open(SALIDA, encoding="utf-8")) if os.path.exists(SALIDA) else {}

archivos = []
for raiz, _, fs in os.walk(PIEZAS):
    for f in sorted(fs):
        if f.lower().endswith(".png"):
            archivos.append(os.path.relpath(os.path.join(raiz, f), PIEZAS))
archivos.sort()
print("piezas encontradas:", len(archivos), "| ya subidas:", len(hashes))

url = f"https://graph.facebook.com/v21.0/{ACT}/adimages"
nuevas = err = 0
for i, rel in enumerate(archivos, 1):
    if rel in hashes:
        continue
    ruta = os.path.join(PIEZAS, rel)
    with open(ruta, "rb") as fh:
        r = requests.post(url, data={"access_token": TOKEN}, files={"source": fh}, timeout=120)
    if r.status_code != 200:
        err += 1
        print(f"  ERROR {rel}: {r.json().get('error',{}).get('message','?')[:90]}")
        if err > 8:
            print("demasiados errores seguidos, se detiene")
            break
        continue
    img = list(r.json()["images"].values())[0]
    hashes[rel] = img["hash"]
    nuevas += 1
    if nuevas % 25 == 0:
        json.dump(hashes, open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  {i}/{len(archivos)} ... {nuevas} nuevas")

json.dump(hashes, open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nListo. {len(hashes)}/{len(archivos)} con hash. Nuevas en esta corrida: {nuevas}. Errores: {err}")
