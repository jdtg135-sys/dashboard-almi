# -*- coding: utf-8 -*-
"""C1: el anuncio dinamico pasa a mezclar las 8 imagenes y los 6 videos (4-nov-2026).

POR QUE SE REEMPLAZA EL CREATIVO Y NO SE AGREGA UN ANUNCIO
----------------------------------------------------------
El conjunto `general-convenio` es dinamico (is_dynamic_creative = True) y Meta
no admite mas de un anuncio ahi. Para que los videos entren hay que cambiar el
creativo del anuncio que ya corre. Eso reinicia la fase de aprendizaje, que hoy
apenas arranco: el costo puede subir unos dias antes de estabilizarse. Es el
unico camino con un solo conjunto y un solo anuncio.

LOS DOS AJUSTES DE AUTOMATIZACION QUE SI SE DEJAN PRENDIDOS
-----------------------------------------------------------
`adapt_to_placement` y `video_auto_crop` van en OPT_IN. Los videos son 9:16 y
sin eso no se adaptan a las ubicaciones cuadradas (feed de Facebook e
Instagram): se verian con franjas o recortados mal. Todo lo que ALTERA la pieza
(texto encima, fondos generados, retoques, musica, voz) sigue en OPT_OUT.

Uso:  python c1_sumar_videos.py        -> simula
      python c1_sumar_videos.py --go   -> lo aplica
"""
import json, os, sys, requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN = cred["access_token"]
ACT = str(cred["ad_account_id"])
ACT = ACT if ACT.startswith("act_") else "act_" + ACT
G = "https://graph.facebook.com/v19.0"
DRY = "--go" not in sys.argv

ANUNCIO = "120253522650750392"          # c1-dinamico-global-nov2026
CREATIVO_VIEJO = "1996473534378906"
PAGE = "732244117208789"
IG = "17841401157769111"
DESTINO = "https://cotizador.almifinanciera.com/"
UTM = ("utm_source=facebook&utm_medium=paid_social&utm_campaign=c1-convenio-general"
       "&utm_content={{ad.name}}&utm_term={{adset.name}}")

VIDEOS = json.load(open(os.path.join(BASE, "analisis", "videos_c1_nov.json")))

# EL TOPE DE 10 PIEZAS
# --------------------
# Meta no admite mas de 10 imagenes y videos juntos en un creativo dinamico
# (error 1815983). Con 6 videos quedan 4 cupos de imagen y habia 8 estaticas.
# Las 8 son en realidad 4 disenos en dos relaciones: 1x1 y 4x5. Se conserva la
# version 4x5 de cada diseno (la que mas area ocupa en el feed) y se sueltan las
# 1x1, porque `adapt_to_placement` queda prendido y Meta recorta el 4x5 a
# cuadrado donde la ubicacion lo pida. No se pierde ningun diseno.
IMAGENES_QUE_QUEDAN = [
    "50bd9bcd7a61edf8750a30bd1c01012c",   # almi_c1_a_4x5_v1
    "1e0f021f68565c5e17ce7718f2921cb6",   # almi_c1_b_4x5_v1
    "d908a7cc959128af17f1db5dec278437",   # almi_c1_texto1_4x5_v1
    "783b3b2177c6f8d968b6ce813ec0d69a",   # almi_c1_texto2_4x5_v1
]

# Copy identico al que ya corre: no se toca para que el unico cambio medible
# sea la entrada de los videos.
viejo = requests.get("%s/%s" % (G, CREATIVO_VIEJO), params={
    "access_token": TOKEN, "fields": "asset_feed_spec"}).json()["asset_feed_spec"]

# Miniatura preferida de cada video
thumbs = {}
for n, vid in VIDEOS.items():
    d = requests.get("%s/%s/thumbnails" % (G, vid), params={
        "access_token": TOKEN, "fields": "uri,is_preferred"}).json().get("data", [])
    pref = [t for t in d if t.get("is_preferred")] or d
    if not pref:
        raise SystemExit("el video %s no tiene miniatura" % n)
    thumbs[n] = pref[0]["uri"]

FEED = {
    "images": [{"hash": h} for h in IMAGENES_QUE_QUEDAN],
    "videos": [{"video_id": VIDEOS[n], "thumbnail_url": thumbs[n]}
               for n in sorted(VIDEOS)],
    "bodies": viejo["bodies"],
    "titles": viejo["titles"],
    "descriptions": viejo["descriptions"],
    "link_urls": [{"website_url": DESTINO}],
    "call_to_action_types": ["GET_QUOTE"],
    "ad_formats": ["AUTOMATIC_FORMAT"],   # un solo formato: Meta rechaza la lista mixta (error 1885374)
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

print("Anuncio: c1-dinamico-global-nov2026 (%s)" % ANUNCIO)
print("  antes:  8 imagenes, 0 videos (tope de Meta: 10 piezas en total)")
print("  queda:  %d imagenes, %d videos" % (len(FEED["images"]), len(FEED["videos"])))
for n in sorted(VIDEOS):
    print("     %-12s %s" % (n, VIDEOS[n]))
print("  textos: %d cuerpos, %d titulos, %d descripciones"
      % (len(FEED["bodies"]), len(FEED["titles"]), len(FEED["descriptions"])))
print("  AVISO: cambiar el creativo reinicia el aprendizaje del conjunto.")

if DRY:
    print("\nSIMULACION. Ejecutar con --go para aplicarlo.")
    raise SystemExit

r = requests.post("%s/%s/adcreatives" % (G, ACT), data={
    "access_token": TOKEN,
    "name": "c1-dinamico-global-img-video-nov2026",
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
    "access_token": TOKEN,
    "creative": json.dumps({"creative_id": nuevo}),
}, timeout=120)
if r.status_code >= 400:
    raise SystemExit("ERROR cambiando el creativo del anuncio: %s" % r.text[:800])
print("anuncio actualizado. LISTO.")
