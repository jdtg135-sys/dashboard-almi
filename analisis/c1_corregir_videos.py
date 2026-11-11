# -*- coding: utf-8 -*-
"""Correccion: a C1 solo le corresponden 3 de los 6 videos (4-nov-2026).

EL ERROR
--------
Se cargaron los 6 videos de la carpeta al anuncio dinamico de C1. Pero el
nombre de archivo trae la campana, igual que las estaticas (almi_c1_*,
almi_c2_*, almi_c4_*): `almi_v1-c1` es C1 y `almi_v1-c2` es C2. Lo confirma el
contenido de las piezas:

  v1-c1  "Tu empresa tiene convenio?"                -> C1, convenio
  v3-c1  "No te pedimos que alguien responda por ti" -> C1
  v5-c1  "Empiezas tu solicitud..."                  -> C1
  v1-c2  "Solicitalo con tu nomina. Sin fiador, sin sucursal." -> C2
  v2-c2  "Credito por nomina, 100% digital"          -> C2
  v4-c2  "Tu decides cuanto."                        -> C2

Los tres de C2 hablan de nomina sin mencionar convenio: es el mensaje de
empleados de sector privado, no el de C1.

QUE HACE ESTE SCRIPT
--------------------
Deja el anuncio de C1 con 3 videos y las 4 estaticas (una por diseno, en 4x5).
Son 7 piezas, debajo del tope de 10 de Meta. Los tres videos de C2 quedan
cargados en la cuenta pero fuera de este anuncio.

COSTO DE LA CORRECCION
----------------------
Es el segundo cambio de creativo del dia en el mismo anuncio, asi que el
aprendizaje vuelve a arrancar. Se hace igual: dejar corriendo piezas de otra
campana ensucia la lectura de C1 y gasta presupuesto en el mensaje equivocado.

Uso:  python c1_corregir_videos.py        -> simula
      python c1_corregir_videos.py --go   -> lo aplica
"""
import json, os, sys, requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN = cred["access_token"]
ACT = str(cred["ad_account_id"])
ACT = ACT if ACT.startswith("act_") else "act_" + ACT
G = "https://graph.facebook.com/v19.0"
DRY = "--go" not in sys.argv

ANUNCIO = "120253522650750392"
CREATIVO_ACTUAL = "3345447369178256"
PAGE = "732244117208789"
IG = "17841401157769111"
DESTINO = "https://cotizador.almifinanciera.com/"
UTM = ("utm_source=facebook&utm_medium=paid_social&utm_campaign=c1-convenio-general"
       "&utm_content={{ad.name}}&utm_term={{adset.name}}")

TODOS = json.load(open(os.path.join(BASE, "analisis", "videos_c1_nov.json")))
DE_C1 = [n for n in sorted(TODOS) if n.endswith("-c1")]
DE_C2 = [n for n in sorted(TODOS) if n.endswith("-c2")]

IMAGENES = [
    "50bd9bcd7a61edf8750a30bd1c01012c",   # almi_c1_a_4x5_v1
    "1e0f021f68565c5e17ce7718f2921cb6",   # almi_c1_b_4x5_v1
    "d908a7cc959128af17f1db5dec278437",   # almi_c1_texto1_4x5_v1
    "783b3b2177c6f8d968b6ce813ec0d69a",   # almi_c1_texto2_4x5_v1
]

actual = requests.get("%s/%s" % (G, CREATIVO_ACTUAL), params={
    "access_token": TOKEN, "fields": "asset_feed_spec"}).json()["asset_feed_spec"]

thumbs = {}
for n in DE_C1:
    d = requests.get("%s/%s/thumbnails" % (G, TODOS[n]), params={
        "access_token": TOKEN, "fields": "uri,is_preferred"}).json().get("data", [])
    pref = [t for t in d if t.get("is_preferred")] or d
    thumbs[n] = pref[0]["uri"]

FEED = {
    "images": [{"hash": h} for h in IMAGENES],
    "videos": [{"video_id": TODOS[n], "thumbnail_url": thumbs[n]} for n in DE_C1],
    "bodies": actual["bodies"],
    "titles": actual["titles"],
    "descriptions": actual["descriptions"],
    "link_urls": [{"website_url": DESTINO}],
    "call_to_action_types": ["GET_QUOTE"],
    "ad_formats": ["AUTOMATIC_FORMAT"],
    "optimization_type": "REGULAR",
}

ALTERAN_LA_PIEZA = (
    "add_text_overlay", "image_auto_crop", "image_uncrop", "image_enhancement",
    "image_brightness_and_contrast", "image_touchups", "image_background_gen",
    "image_animation", "image_templates", "text_generation", "music_generation",
    "video_voiceover", "translate_voiceover", "video_highlight", "video_to_image",
)
DOF = {"creative_features_spec": dict(
    [(k, {"enroll_status": "OPT_OUT"}) for k in ALTERAN_LA_PIEZA] +
    [("adapt_to_placement", {"enroll_status": "OPT_IN"}),
     ("video_auto_crop", {"enroll_status": "OPT_IN"})])}

print("Anuncio c1-dinamico-global-nov2026 (%s)" % ANUNCIO)
print("  se quedan en C1 : %s" % ", ".join(DE_C1))
print("  salen (son C2)  : %s" % ", ".join(DE_C2))
print("  queda con %d imagenes y %d videos" % (len(FEED["images"]), len(FEED["videos"])))

if DRY:
    print("\nSIMULACION. Ejecutar con --go para aplicarlo.")
    raise SystemExit

r = requests.post("%s/%s/adcreatives" % (G, ACT), data={
    "access_token": TOKEN,
    "name": "c1-dinamico-global-img-video-nov2026-v2",
    "object_story_spec": json.dumps({"page_id": PAGE, "instagram_user_id": IG}),
    "asset_feed_spec": json.dumps(FEED),
    "degrees_of_freedom_spec": json.dumps(DOF),
    "url_tags": UTM,
}, timeout=120)
if r.status_code >= 400:
    raise SystemExit("ERROR creando el creativo: %s" % r.text[:800])
nuevo = r.json()["id"]
print("creativo nuevo: %s" % nuevo)

r = requests.post("%s/%s" % (G, ANUNCIO), data={
    "access_token": TOKEN, "creative": json.dumps({"creative_id": nuevo})}, timeout=120)
if r.status_code >= 400:
    raise SystemExit("ERROR cambiando el creativo: %s" % r.text[:800])
print("anuncio actualizado. LISTO.")
