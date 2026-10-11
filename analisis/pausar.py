# -*- coding: utf-8 -*-
"""Pausa los anuncios listados en a_podar.json. Verifica el estado despues."""
import os
import json, os, sys, urllib.request, urllib.parse, urllib.error
# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AQUI = os.path.dirname(os.path.abspath(__file__))
c = json.load(open(os.path.join(BASE, "meta_credentials.json")))
T = c["access_token"]
G = "https://graph.facebook.com/v21.0/"
DRY = "--go" not in sys.argv
podar = json.load(open(os.path.join(AQUI, "a_podar.json"), encoding="utf-8"))

for a in podar:
    print(f"{'[simulacion] ' if DRY else ''}PAUSAR {a['nombre']} "
          f"({a['gasto']:,.0f} COP, {a['conv']:.0f} conv)")
    if DRY:
        continue
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            G + a["id"], data=urllib.parse.urlencode(
                {"access_token": T, "status": "PAUSED"}).encode()))
        print("   ->", json.load(r))
    except urllib.error.HTTPError as e:
        print("   ERROR:", json.loads(e.read()).get("error", {}).get("message", "?")[:160])
        continue
    v = json.load(urllib.request.urlopen(
        G + a["id"] + "?" + urllib.parse.urlencode(
            {"access_token": T, "fields": "name,status,effective_status"})))
    print(f"   verificado: {v['status']} / {v['effective_status']}")

print("\n" + ("SIMULACION. Ejecutar con --go" if DRY else "LISTO"))
