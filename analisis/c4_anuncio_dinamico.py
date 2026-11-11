# -*- coding: utf-8 -*-
"""C4 estrena lote: un conjunto dinamico con los 4 videos y las 4 graficas (11-nov-2026).

POR QUE HAY QUE CREAR UN CONJUNTO NUEVO
---------------------------------------
`retargeting-general` NO es dinamico, y un conjunto no se puede convertir en
dinamico despues de creado. Ademas Meta solo admite UN anuncio en un conjunto
dinamico, asi que el lote no cabe junto a `c4-video-6`. El conjunto nuevo
replica la segmentacion de `retargeting-general` tal cual, incluida la BBDD
GLOM que acabamos de refrescar.

Costo: el conjunto nuevo entra en aprendizaje. C4 viene haciendo ~53
conversiones diarias y el aprendizaje cierra con unas 50 en siete dias, asi que
deberia salir en uno o dos dias. `retargeting-general` NO se toca y sigue
corriendo con video-6, asi que la campana no se queda sin entrega mientras
tanto. Al ser presupuesto de campana (CBO), Meta reparte entre los dos.

EL TOPE DE 10 PIEZAS
--------------------
Un creativo dinamico admite como maximo 10 imagenes y videos juntos. Llegaron
16 archivos: 4 videos y 4 disenos en tres relaciones cada uno. Se usan los 4
videos (9:16, que cubren Reels e historias) y una sola relacion por diseno, la
4:5, que es la que mas area ocupa en el feed. Son 8 piezas. `adapt_to_placement`
queda prendido para que Meta recorte el 4:5 donde la ubicacion lo pida, asi que
no se pierde ningun diseno ni ninguna ubicacion.

Uso:  python c4_anuncio_dinamico.py        -> simula
      python c4_anuncio_dinamico.py --go   -> lo aplica
"""
import json, os, sys, time, requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN = cred["access_token"]
ACT = str(cred["ad_account_id"])
ACT = ACT if ACT.startswith("act_") else "act_" + ACT
G = "https://graph.facebook.com/v19.0"
DRY = "--go" not in sys.argv

CARPETA = r"C:\Users\juanc\Downloads\CAMPAÑA C4-20261111T140915Z-1-001\CAMPAÑA C4"
CAMPANA = "120252908058080392"          # C4 - Retargeting caliente - Oct2026
MODELO = "120252908058420392"           # retargeting-general, de donde se copia todo
PAGE = "732244117208789"
IG = "17841401157769111"
DESTINO = "https://cotizador.almifinanciera.com/"
UTM = ("utm_source=facebook&utm_medium=paid_social&utm_campaign=c4-retargeting"
       "&utm_content={{ad.name}}&utm_term={{adset.name}}")
NOMBRE_CONJUNTO = "retargeting-dinamico"
NOMBRE_ANUNCIO = "c4-dinamico-nov2026"

VIDEOS = ["almi_c4_v1_9x16_v1.mp4", "almi_c4_v2_9x16_v1.mp4",
          "almi_c4_v3_9x16_v1.mp4", "almi_c4_v4_9x16_v1.mp4"]
IMAGENES = ["almi_c4_e1_4x5_v1.png", "almi_c4_e2_4x5_v1.png",
            "almi_c4_e3_4x5_v1.png", "almi_c4_e4_4x5_v1.png"]

# Copy del documento de produccion, sin cambios.
BODIES = [
    "Tu solicitud sigue donde la dejaste. No tienes que empezar de nuevo: la "
    "retomas desde tu celular y la terminas cuando estes listo.",
    "La cuota que viste es la que pagas. Sale directo de tu nomina, fija y sin "
    "sorpresas. Con 6 meses en tu empresa ya puedes solicitar.",
    "Simular no te compromete a nada. Miras el numero, lo piensas y decides "
    "despues. Sin extractos bancarios, sin cartas laborales y sin fiador.",
    "Te pedimos pocos datos y te decimos para que: para confirmar que la cuota "
    "te cabe. Todo en linea, sin filas y sin papeleo.",
]
TITLES = ["Retoma tu solicitud", "Tu cuota te espera",
          "Decides tu, al final", "Sin filas, sin fiador"]
DESCRIPTIONS = ["Descuento directo por nomina", "100% en linea, desde tu celular"]

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


def get(path, **p):
    p["access_token"] = TOKEN
    r = requests.get("%s/%s" % (G, path), params=p, timeout=90)
    r.raise_for_status()
    return r.json()


def post(path, data, files=None):
    data = dict(data)
    data["access_token"] = TOKEN
    r = requests.post("%s/%s" % (G, path), data=data, files=files, timeout=600)
    if r.status_code >= 400:
        raise SystemExit("ERROR en %s: %s" % (path, r.text[:600]))
    return r.json()


modelo = get(MODELO, fields="targeting,promoted_object,optimization_goal,"
                            "billing_event,attribution_spec")

print("Campana  : C4 - Retargeting caliente")
print("Conjunto : %s  (copia la segmentacion de retargeting-general)" % NOMBRE_CONJUNTO)
print("Anuncio  : %s  (dinamico, uno solo)" % NOMBRE_ANUNCIO)
print()
print("  videos   : %d  -> %s" % (len(VIDEOS), ", ".join(v[:16] for v in VIDEOS)))
print("  imagenes : %d  -> %s  (solo 4:5; el tope de Meta son 10 piezas)"
      % (len(IMAGENES), ", ".join(i[:16] for i in IMAGENES)))
print("  total    : %d piezas" % (len(VIDEOS) + len(IMAGENES)))
print("  textos   : %d cuerpos, %d titulos, %d descripciones"
      % (len(BODIES), len(TITLES), len(DESCRIPTIONS)))
print()
print("  AVISO: el conjunto nuevo entra en aprendizaje (1-2 dias al ritmo de C4).")
print("         retargeting-general y c4-video-6 NO se tocan.")

faltan = [f for f in VIDEOS + IMAGENES
          if not os.path.exists(os.path.join(CARPETA, "VIDEOS" if f.endswith(".mp4") else "PIEZAS", f))]
if faltan:
    raise SystemExit("\nFaltan archivos: %s" % ", ".join(faltan))

if DRY:
    print("\nSIMULACION. Ejecutar con --go para aplicarlo.")
    raise SystemExit

# --- 1. Subir imagenes ---
hashes = []
for f in IMAGENES:
    with open(os.path.join(CARPETA, "PIEZAS", f), "rb") as fh:
        r = post("%s/adimages" % ACT, {}, files={f: fh})
    hashes.append(r["images"][f]["hash"])
    print("imagen subida: %s" % f)

# --- 2. Subir videos y esperar a que procesen ---
vids = []
for f in VIDEOS:
    with open(os.path.join(CARPETA, "VIDEOS", f), "rb") as fh:
        r = post("%s/advideos" % ACT, {"name": f.replace(".mp4", "")},
                 files={"source": (f, fh, "video/mp4")})
    vids.append(r["id"])
    print("video subido: %s -> %s" % (f, r["id"]))

for intento in range(30):
    pend = [v for v in vids
            if (get(v, fields="status").get("status") or {}).get("video_status") != "ready"]
    if not pend:
        print("todos los videos procesados")
        break
    print("  procesando %d video(s)..." % len(pend))
    time.sleep(20)
else:
    raise SystemExit("Los videos no terminaron de procesar. Reintentar mas tarde.")

thumbs = {}
for v in vids:
    d = get("%s/thumbnails" % v, fields="uri,is_preferred").get("data", [])
    pref = [t for t in d if t.get("is_preferred")] or d
    thumbs[v] = pref[0]["uri"]

# --- 3. Conjunto nuevo, dinamico, con la misma segmentacion ---
conjunto = post("%s/adsets" % ACT, {
    "name": NOMBRE_CONJUNTO,
    "campaign_id": CAMPANA,
    "is_dynamic_creative": "true",
    "optimization_goal": modelo["optimization_goal"],
    "billing_event": modelo["billing_event"],
    "promoted_object": json.dumps(modelo["promoted_object"]),
    "attribution_spec": json.dumps(modelo["attribution_spec"]),
    "targeting": json.dumps(modelo["targeting"]),
    "status": "ACTIVE",
})
print("conjunto creado: %s" % conjunto["id"])

# --- 4. Creativo dinamico ---
feed = {
    "images": [{"hash": h} for h in hashes],
    "videos": [{"video_id": v, "thumbnail_url": thumbs[v]} for v in vids],
    "bodies": [{"text": b} for b in BODIES],
    "titles": [{"text": t} for t in TITLES],
    "descriptions": [{"text": d} for d in DESCRIPTIONS],
    "link_urls": [{"website_url": DESTINO}],
    "call_to_action_types": ["GET_QUOTE"],
    # Un solo formato: Meta rechaza la lista mixta (error 1885374).
    "ad_formats": ["AUTOMATIC_FORMAT"],
    "optimization_type": "REGULAR",
}
creativo = post("%s/adcreatives" % ACT, {
    "name": NOMBRE_ANUNCIO,
    "object_story_spec": json.dumps({"page_id": PAGE, "instagram_user_id": IG}),
    "asset_feed_spec": json.dumps(feed),
    "degrees_of_freedom_spec": json.dumps(DOF),
    "url_tags": UTM,
})
print("creativo creado: %s" % creativo["id"])

anuncio = post("%s/ads" % ACT, {
    "name": NOMBRE_ANUNCIO,
    "adset_id": conjunto["id"],
    "creative": json.dumps({"creative_id": creativo["id"]}),
    "status": "ACTIVE",
})
print("anuncio creado y activo: %s" % anuncio["id"])
print("")
print("LISTO. C4 queda con dos conjuntos: retargeting-general (video-6) y")
print("%s (lote nuevo). Comparar en 3-4 dias." % NOMBRE_CONJUNTO)
