# -*- coding: utf-8 -*-
"""Campana de trafico para el webinar 'Navidad sin deudas' del 22-oct-2026.

Se crea EN PAUSA. El formulario de destino no tiene pixel, asi que se optimiza
por clics en el enlace (LINK_CLICKS); con pixel se podria optimizar por vistas
de pagina de destino, que rinde bastante mejor.
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

PAGE_ID = "732244117208789"
INSTAGRAM_ID = "17841401157769111"
ENLACE = "https://api.leadconnectorhq.com/widget/form/NZbsYM9mnEqP5JfNZWv0"
PRESUPUESTO = 10000
FIN = "2026-10-22T11:00:00-0500"      # el webinar arranca a las 12:00

TEXTOS = [
    "Diciembre llega con prima y con gastos. En este webinar gratuito aprendes a organizar tu plata para que enero no te sorprenda. Jueves 22 de octubre, 12:00 p.m.",
    "¿Tu prima se va completa en diciembre y no sabes bien en qué? Aprende a planearla antes de que llegue. Webinar gratuito, jueves 22 de octubre.",
    "Navidad sin deudas: cómo usar mejor tu prima y comprar con cabeza. Webinar gratuito el 22 de octubre, con sorteos en vivo.",
    "Llega diciembre y con él los gastos de fin de año. Inscríbete gratis al webinar del jueves 22 y aprende a llegar a enero sin deudas.",
    "Un webinar gratuito para preparar tu bolsillo para diciembre. Jueves 22 de octubre a las 12:00 p.m., en vivo por YouTube y con sorteos.",
]
TITULOS = [
    "Navidad sin deudas",
    "Webinar gratuito, 22 de octubre",
    "Prepara tu bolsillo para diciembre",
    "Inscríbete gratis, cupos limitados",
    "Aprovecha mejor tu prima",
]

REGLAS = [
    ("vertical", {"publisher_platforms": ["facebook", "instagram", "messenger"],
                  "facebook_positions": ["story", "facebook_reels"],
                  "instagram_positions": ["story", "reels"],
                  "messenger_positions": ["story"]}),
    ("horizontal", {"publisher_platforms": ["facebook", "audience_network"],
                    "facebook_positions": ["right_hand_column"],
                    "audience_network_positions": ["classic"]}),
    ("cuadrado", {"publisher_platforms": ["facebook", "instagram"],
                  "facebook_positions": ["feed", "marketplace", "video_feeds", "search", "profile_feed"],
                  "instagram_positions": ["stream", "explore", "explore_home", "ig_search", "profile_feed"]}),
]

SIN_MEJORAS = {"creative_features_spec": {k: {"enroll_status": "OPT_OUT"} for k in
               ["advantage_plus_creative", "image_touchups", "image_templates",
                "text_optimizations", "enhance_cta", "image_background_gen",
                "text_generation", "video_auto_crop", "adapt_to_placement",
                "image_animation", "profile_card"]}}

UTM = ("utm_source=facebook&utm_medium=paid_social&utm_campaign=webinar-navidad-sin-deudas"
       "&utm_content={{ad.name}}&utm_term={{adset.name}}")


def post(path, payload, etiqueta):
    if DRY:
        print("   [simulacion]", etiqueta)
        return {"id": "SIMULADO"}
    payload["access_token"] = TOKEN
    for i in range(4):
        r = requests.post(G + path, data=payload, timeout=180)
        if r.status_code == 200:
            return r.json()
        e = r.json().get("error", {})
        if e.get("code") in (17, 4, 613):
            time.sleep(60 * (i + 1)); continue
        print("   ERROR", etiqueta, "::", (e.get("error_user_msg") or e.get("message", ""))[:190])
        return None
    return None


hashes = json.load(open(os.path.join(AQUI, "webinar_hashes.json"), encoding="utf-8"))
video = json.load(open(os.path.join(AQUI, "webinar_video.json"), encoding="utf-8"))["video_id"]

print("CAMPANA: Webinar Navidad sin deudas 22/10/2026")
print("  objetivo trafico | optimiza por clics en el enlace")
print("  presupuesto {:,} COP/dia | termina {}".format(PRESUPUESTO, FIN))
print("  destino:", ENLACE)
print()

CAMPANA_EXISTENTE = "120252985917770392"
cam = {"id": CAMPANA_EXISTENTE} if CAMPANA_EXISTENTE else post(ACT + "/campaigns", {
    "name": "Webinar Navidad sin deudas 22/10/2026",
    "objective": "OUTCOME_TRAFFIC", "status": "PAUSED",
    "special_ad_categories": json.dumps([]),
    "buying_type": "AUCTION", "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
    "daily_budget": PRESUPUESTO,
}, "campana")
if not cam:
    raise SystemExit("no se creo la campana")
print("  campana:", cam["id"])

targeting = {
    "geo_locations": {"countries": ["CO"]},
    "age_min": 25, "age_max": 65,
    # con segmentacion ampliada la edad va como sugerencia, no como tope duro
    "targeting_automation": {"advantage_audience": 1, "individual_setting": {"age": 1}},
}
ads_ = post(ACT + "/adsets", {
    "name": "webinar-frio-colombia",
    "campaign_id": cam["id"], "status": "PAUSED",
    "billing_event": "IMPRESSIONS",
    "optimization_goal": "LINK_CLICKS",
    "destination_type": "WEBSITE",
    "targeting": json.dumps(targeting),
    "end_time": FIN,
}, "conjunto")
if not ads_:
    raise SystemExit("no se creo el conjunto")
print("  conjunto:", ads_["id"])

etiquetas = {"body_label": {"name": "txt"}, "title_label": {"name": "ttl"}}
bodies = [{"text": t, "adlabels": [{"name": "txt"}]} for t in TEXTOS]
titles = [{"text": t, "adlabels": [{"name": "ttl"}]} for t in TITULOS]

# --- anuncio de imagen, un formato por ubicacion ---
afs_img = {
    "ad_formats": ["SINGLE_IMAGE"],
    "images": [{"hash": h, "adlabels": [{"name": lab}]} for lab, h in hashes.items()],
    "bodies": bodies, "titles": titles,
    "link_urls": [{"website_url": ENLACE}],
    "call_to_action_types": ["SIGN_UP"],
    "asset_customization_rules": [dict(etiquetas, customization_spec=sp, image_label={"name": lab})
                                  for lab, sp in REGLAS],
}
cr = post(ACT + "/adcreatives", {
    "name": "cr-webinar-imagen",
    "object_story_spec": json.dumps({"page_id": PAGE_ID, "instagram_user_id": INSTAGRAM_ID}),
    "asset_feed_spec": json.dumps(afs_img),
    "degrees_of_freedom_spec": json.dumps(SIN_MEJORAS),
    "url_tags": UTM,
}, "creativo imagen")
if cr:
    a = post(ACT + "/ads", {"name": "webinar-imagen", "adset_id": ads_["id"],
                            "status": "PAUSED", "creative": json.dumps({"creative_id": cr["id"]})},
             "anuncio imagen")
    if a: print("  anuncio imagen:", a["id"])

# --- anuncio de video ---
th = requests.get(G + video + "/thumbnails",
                  params={"access_token": TOKEN, "fields": "uri,is_preferred"}, timeout=90)
ts = th.json().get("data", []) if th.status_code == 200 else []
pref = [t for t in ts if t.get("is_preferred")] or ts
vdata = {"video_id": video, "adlabels": [{"name": "vid"}]}
if pref:
    vdata["thumbnail_url"] = pref[0]["uri"]
afs_vid = {
    "ad_formats": ["SINGLE_VIDEO"], "videos": [vdata],
    "bodies": bodies, "titles": titles,
    "link_urls": [{"website_url": ENLACE}],
    "call_to_action_types": ["SIGN_UP"],
    "asset_customization_rules": [dict(etiquetas, customization_spec=sp, video_label={"name": "vid"})
                                  for _, sp in REGLAS],
}
cr2 = post(ACT + "/adcreatives", {
    "name": "cr-webinar-video",
    "object_story_spec": json.dumps({"page_id": PAGE_ID, "instagram_user_id": INSTAGRAM_ID}),
    "asset_feed_spec": json.dumps(afs_vid),
    "degrees_of_freedom_spec": json.dumps(SIN_MEJORAS),
    "url_tags": UTM,
}, "creativo video")
if cr2:
    a2 = post(ACT + "/ads", {"name": "webinar-video", "adset_id": ads_["id"],
                             "status": "PAUSED", "creative": json.dumps({"creative_id": cr2["id"]})},
              "anuncio video")
    if a2: print("  anuncio video:", a2["id"])

print("\n" + ("SIMULACION, ejecutar con --go" if DRY else "CREADA EN PAUSA"))
