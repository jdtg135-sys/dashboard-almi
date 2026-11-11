# -*- coding: utf-8 -*-
"""C1 pasa a un solo conjunto y un solo anuncio dinamico (4-nov-2026).

QUE CAMBIA Y POR QUE
--------------------
C1 venia armada por sectores: 85 anuncios con nombre de empresa, repartidos
en tres conjuntos. Se retiran las piezas con logos de otras marcas y se deja
UN anuncio dinamico con las piezas globales, en UN solo conjunto.

EL CONJUNTO QUE SE CONSERVA
---------------------------
`sectores-alto-volumen`. Dos razones: es el unico con fase de aprendizaje
superada y el que concentra el gasto (762.924 de 1.215.150 en 14 dias); y su
segmento ya es amplio de hecho, porque tiene el publico ampliado de Meta
activo (advantage_audience = 1), asi que los intereses que trae son solo una
sugerencia de arranque y Meta ya entrega por fuera de ellos. No se toca el
segmento: editarlo reiniciaria el aprendizaje sin ganar nada.

LOS 6 MESES
-----------
El requisito de antiguedad es de SEIS meses, confirmado por el cliente el
4-nov-2026. En el lote de creativos del 27-oct quedo escrito cuatro por error
mio; las piezas que llegaron de diseno dicen seis, que es lo correcto. Todo el
copy de aqui dice seis.

RIESGO CONOCIDO
---------------
Se apaga `c1-video-6`, que en 14 dias trajo 254 de las 508 solicitudes de la
campana a 2.421. Es decision del cliente dejar un solo anuncio. Si el volumen
cae, reactivarlo es inmediato: basta volver su estado a ACTIVE.

Uso:  python c1_anuncio_dinamico.py        -> muestra el plan
      python c1_anuncio_dinamico.py --go   -> lo ejecuta
"""
import json, os, sys, requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN = cred["access_token"]
ACT = cred["ad_account_id"]
if not str(ACT).startswith("act_"):
    ACT = "act_" + str(ACT)
G = "https://graph.facebook.com/v19.0"
DRY = "--go" not in sys.argv

CAMPANA = "120252908053710392"          # C1 - Convenio por sectores - Oct2026
CONJUNTO = "120252908055670392"         # sectores-alto-volumen (el que se conserva)
CONJUNTOS_A_PAUSAR = [
    "120252908054930392",               # sectores-especializados
    "120252908054170392",               # lookalike-solicitantes
]
PAGE = "732244117208789"
IG = "17841401157769111"
DESTINO = "https://cotizador.almifinanciera.com/"
UTM = ("utm_source=facebook&utm_medium=paid_social&utm_campaign=c1-convenio-general"
       "&utm_content={{ad.name}}&utm_term={{adset.name}}")
NOMBRE_ANUNCIO = "c1-dinamico-global-nov2026"
NOMBRE_CONJUNTO = "general-convenio"

HASHES = json.load(open(os.path.join(BASE, "analisis", "hashes_c1_nov.json")))

# Copy. Reglas de marca: sin promesa de aprobacion, sin plazos exactos,
# sin "sin importar tu historial". La antiguedad va como habilitador.
BODIES = [
    "Tu empresa puede tener convenio con ALMI y tu no saberlo. Verificalo en linea, "
    "sin compromiso. Con 6 meses en tu empresa ya puedes consultarlo.",
    "Credito por descuento de nomina, 100% en linea. Sin extractos bancarios, sin "
    "cartas laborales y sin fiador. Con 6 meses en tu empresa ya puedes solicitar.",
    "Mira tu cuota antes de pedir nada. Eliges el monto, ves lo que pagarias y "
    "decides con el numero en frente. Sin compromiso.",
    "La cuota sale directo de tu nomina: fija y sin sorpresas. Si llevas 6 meses en "
    "tu empresa, averigua si la tuya tiene convenio con ALMI.",
]
TITLES = [
    "Verifica tu convenio",
    "Tu nomina basta",
    "Sin fiador, sin papeleo",
    "Consulta sin compromiso",
]
DESCRIPTIONS = [
    "Descuento directo por nomina",
    "100% en linea, sin filas",
]


def get(path, **params):
    params["access_token"] = TOKEN
    r = requests.get("%s/%s" % (G, path), params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def post(path, data):
    data = dict(data)
    data["access_token"] = TOKEN
    r = requests.post("%s/%s" % (G, path), data=data, timeout=120)
    if r.status_code >= 400:
        raise SystemExit("ERROR en %s: %s" % (path, r.text[:500]))
    return r.json()


# --- Inventario de lo que se va a apagar ---
ads = get("%s/ads" % CAMPANA, fields="id,name,status,adset{id,name}", limit=300)["data"]
activos = [a for a in ads if a["status"] == "ACTIVE"]

print("C1 hoy: %d anuncios, %d activos, 3 conjuntos" % (len(ads), len(activos)))
print()
print("Se apagan estos %d anuncios activos:" % len(activos))
for a in sorted(activos, key=lambda a: a["name"]):
    print("   %-48s (%s)" % (a["name"][:48], a["adset"]["name"]))
print()
print("Se pausan los conjuntos: sectores-especializados, lookalike-solicitantes")
print("Se conserva y renombra: sectores-alto-volumen -> %s" % NOMBRE_CONJUNTO)
print()
print("Anuncio nuevo: %s" % NOMBRE_ANUNCIO)
print("   %d imagenes, %d textos, %d titulos, %d descripciones"
      % (len(HASHES), len(BODIES), len(TITLES), len(DESCRIPTIONS)))
print("   combinaciones posibles: %d" % (len(HASHES) * len(BODIES) * len(TITLES)))

if DRY:
    print()
    print("SIMULACION. Ejecutar con --go para aplicarlo.")
    raise SystemExit

# --- 1. Crear el creativo dinamico ---
asset_feed = {
    "images": [{"hash": h} for h in HASHES.values()],
    "bodies": [{"text": b} for b in BODIES],
    "titles": [{"text": t} for t in TITLES],
    "descriptions": [{"text": d} for d in DESCRIPTIONS],
    "link_urls": [{"website_url": DESTINO}],
    "call_to_action_types": ["GET_QUOTE"],
    "ad_formats": ["SINGLE_IMAGE"],
}
creativo = post("%s/adcreatives" % ACT, {
    "name": "c1-dinamico-global-nov2026",
    # La API v19 ya no acepta instagram_actor_id aqui: es instagram_user_id.
    "object_story_spec": json.dumps({"page_id": PAGE, "instagram_user_id": IG}),
    "asset_feed_spec": json.dumps(asset_feed),
    "url_tags": UTM,
    # `standard_enhancements` quedo obsoleto: hay que elegir funcion por funcion.
    # Se desactivan solo las que alteran la pieza y romperian la identidad de
    # marca (texto encima, recortes, retoques, fondos generados). El resto se
    # deja en el comportamiento por defecto de la cuenta.
    "degrees_of_freedom_spec": json.dumps({
        "creative_features_spec": {
            k: {"enroll_status": "OPT_OUT"} for k in (
                "add_text_overlay", "image_auto_crop", "image_uncrop",
                "image_enhancement", "image_brightness_and_contrast",
                "image_touchups", "image_background_gen", "image_animation",
                "image_templates", "text_generation",
            )
        }
    }),
})
print("Creativo creado: %s" % creativo["id"])

# --- 2. Crear el anuncio, ACTIVO, antes de apagar nada ---
anuncio = post("%s/ads" % ACT, {
    "name": NOMBRE_ANUNCIO,
    "adset_id": CONJUNTO,
    "creative": json.dumps({"creative_id": creativo["id"]}),
    "status": "ACTIVE",
})
print("Anuncio creado y activo: %s" % anuncio["id"])

# --- 3. Apagar los anuncios viejos ---
for a in activos:
    post(a["id"], {"status": "PAUSED"})
    print("   pausado: %s" % a["name"])

# --- 4. Pausar los otros dos conjuntos ---
for cj in CONJUNTOS_A_PAUSAR:
    post(cj, {"status": "PAUSED"})
    print("   conjunto pausado: %s" % cj)

# --- 5. Renombrar el conjunto que queda ---
post(CONJUNTO, {"name": NOMBRE_CONJUNTO})
print("Conjunto renombrado a %s" % NOMBRE_CONJUNTO)
print()
print("LISTO. C1 queda con un conjunto y un anuncio dinamico.")
