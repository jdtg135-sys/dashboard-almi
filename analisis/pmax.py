# -*- coding: utf-8 -*-
"""Crea la campana Performance Max de ALMI, EN PAUSA.

Se crea pausada a proposito: Performance Max reparte en YouTube, Display,
Discover, Gmail y Maps, asi que un error de configuracion se paga mucho mas
rapido que en Busqueda. Se revisa en la interfaz y se enciende a mano.

Uso:  python pmax.py           -> valida contra la API sin crear nada
      python pmax.py --go      -> crea
"""
import sys, os
from ads_cliente import cliente, CID

DRY = "--go" not in sys.argv
cli = cliente()
AQUI = os.path.dirname(os.path.abspath(__file__))

NOMBRE = "C7 - Performance Max - Libranza - Oct2026"
PRESUPUESTO = 20_000           # COP/dia
URL = "https://cotizador.almifinanciera.com/"
COLOMBIA = "2170"              # geo target constant
ESPANOL = "1003"               # language constant

TITULOS = [
    "Credito por Nomina | ALMI", "Aprobacion en el Dia",
    "Sin Banco. Solo tu Nomina", "Descuento Directo de Nomina",
    "Sin Tramites. Sin Fiador", "Solicita en 5 Minutos",
    "100% Online. Sin Filas", "Credito Aunque Estes Reportado",
    "Libranza Empresa Privada", "Credito Rapido. Cuota Fija",
    "Verifica tu Convenio ALMI", "Empleado Privado: Aplica Ya",
]
TITULOS_LARGOS = [
    "Credito por libranza para empleados: aprobacion rapida y cuota fija desde tu nomina",
    "Solicita tu credito por libranza 100% en linea, sin codeudor y sin extractos",
    "Reportado en Datacredito? En ALMI miramos tu empleo, no tu historial",
]
DESCRIPCIONES = [
    "Sin codeudor ni extractos. Solicita desde tu celular.",
    "Credito por libranza para empleados sector privado. Sin extractos, sin codeudor.",
    "Si eres empleado: aprobacion rapida y cuota fija descontada de tu nomina.",
    "Tu empresa no tiene convenio? Tambien puedes aplicar. Te ayudamos a verificarlo.",
]
NEGOCIO = "ALMI Financiera"

# Recursos que ya estan en la cuenta (ver inventario). Se reutilizan en vez de
# volver a subirlos: son los mismos que ya pasaron revision de politicas.
IMG_HORIZONTAL = [400609363093, 400609363108, 400609369477, 400609369492]  # 1200x628
IMG_CUADRADA = [354747002252, 354747145751, 354826689184, 354901560741]    # 1080x1080
IMG_VERTICAL = [350422025039, 350422025252, 350422025840]                  # 1080x1350
VIDEOS = [400610337700, 400610337709, 400680092961, 400680092967, 400680094488]


# --- validaciones de longitud antes de hablarle a la API ---
def revisar(lista, limite, etiqueta):
    malos = [(t, len(t)) for t in lista if len(t) > limite]
    for t, n in malos:
        print(f"  ERROR {etiqueta}: {n} caracteres (max {limite}) -> {t}")
    return not malos


ok = all([
    revisar(TITULOS, 30, "titulo"),
    revisar(TITULOS_LARGOS, 90, "titulo largo"),
    revisar(DESCRIPCIONES, 90, "descripcion"),
    revisar([NEGOCIO], 25, "nombre de negocio"),
])
if not any(len(d) <= 60 for d in DESCRIPCIONES):
    print("  ERROR: se necesita al menos una descripcion de 60 caracteres o menos")
    ok = False
if not ok:
    raise SystemExit("corregir los textos antes de continuar")
print(f"textos validados: {len(TITULOS)} titulos, {len(TITULOS_LARGOS)} largos, "
      f"{len(DESCRIPCIONES)} descripciones")

svc = cli.get_service("GoogleAdsService")
ops = []


def nueva(tipo):
    o = cli.get_type("MutateOperation")
    return o, getattr(o, tipo)


def rn(recurso, temp):
    return f"customers/{CID}/{recurso}/{temp}"


# --- 1. subir los dos logos (no habia ninguno cuadrado en la cuenta) ---
logos = {}
asset_svc = cli.get_service("AssetService")


def buscar_asset_por_nombre(nombre):
    salida = []
    for b in svc_busqueda.search_stream(customer_id=CID, query=f"""
      SELECT asset.resource_name FROM asset
      WHERE asset.name = '{nombre}' AND asset.type = 'IMAGE'"""):
        for r in b.results:
            salida.append(r.asset.resource_name)
    return salida


svc_busqueda = cli.get_service("GoogleAdsService")
for archivo, etiqueta in (("logo_1x1.png", "ALMI logo cuadrado 1200x1200"),
                          ("logo_4x1.png", "ALMI logo horizontal 1200x300")):
    ruta = os.path.join(AQUI, archivo)
    op = cli.get_type("AssetOperation")
    a = op.create
    a.name = etiqueta
    a.type_ = cli.enums.AssetTypeEnum.IMAGE
    a.image_asset.data = open(ruta, "rb").read()
    # Los logos se suben siempre, tambien al validar: un recurso de imagen
    # suelto en la biblioteca no hace nada, y el logo cuadrado tiene que
    # existir para poder validar el resto (lo exige Brand Guidelines).
    ya = [r for r in buscar_asset_por_nombre(etiqueta)]
    if ya:
        logos[archivo] = ya[0]
        print(f"  {archivo} ya estaba: {logos[archivo]}")
        continue
    res = asset_svc.mutate_assets(customer_id=CID, operations=[op])
    logos[archivo] = res.results[0].resource_name
    print(f"  subido {archivo} -> {logos[archivo]}")

# --- 2. presupuesto ---
o, b = nueva("campaign_budget_operation")
b.create.resource_name = rn("campaignBudgets", -1)
b.create.name = NOMBRE + " - presupuesto"
b.create.amount_micros = PRESUPUESTO * 1_000_000
b.create.delivery_method = cli.enums.BudgetDeliveryMethodEnum.STANDARD
b.create.explicitly_shared = False
ops.append(o)

# --- 3. campana ---
o, c = nueva("campaign_operation")
cc = c.create
cc.resource_name = rn("campaigns", -2)
cc.name = NOMBRE
cc.status = cli.enums.CampaignStatusEnum.PAUSED
cc.advertising_channel_type = cli.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
cc.campaign_budget = rn("campaignBudgets", -1)
cc.bidding_strategy_type = cli.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS
cc.maximize_conversions.target_cpa_micros = 0     # sin tope: que aprenda primero
# Declaracion obligatoria desde 2025, aunque la campana sea solo para Colombia.
cc.contains_eu_political_advertising = (
    cli.enums.EuPoliticalAdvertisingStatusEnum
       .DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING)
# La expansion de URL final no es un campo de la campana en esta version de la
# API; se desactiva a mano en la interfaz al revisar la campana. Con un solo
# destino (el cotizador) el riesgo es bajo, pero conviene apagarla igual.
ops.append(o)

# --- 4. pais e idioma ---
o, cr = nueva("campaign_criterion_operation")
cr.create.campaign = rn("campaigns", -2)
cr.create.location.geo_target_constant = f"geoTargetConstants/{COLOMBIA}"
ops.append(o)
o, cr = nueva("campaign_criterion_operation")
cr.create.campaign = rn("campaigns", -2)
cr.create.language.language_constant = f"languageConstants/{ESPANOL}"
ops.append(o)

# --- 5. grupo de recursos ---
o, ag = nueva("asset_group_operation")
ag.create.resource_name = rn("assetGroups", -3)
ag.create.name = "Libranza - empleados sector privado"
ag.create.campaign = rn("campaigns", -2)
ag.create.final_urls.append(URL)
ag.create.status = cli.enums.AssetGroupStatusEnum.ENABLED
ops.append(o)

# --- 6. textos ---
#
# Se crean en una llamada aparte y ANTES, no con identificadores temporales
# dentro del mismo lote. Google deduplica los textos contra los que ya existen
# en la cuenta, y con identificadores temporales la validacion del grupo no
# alcanzaba a contarlos: daba "Headline asset is not enough" teniendo doce.
F = cli.enums.AssetFieldTypeEnum


def crear_textos(valores):
    operaciones = []
    for v in valores:
        op = cli.get_type("AssetOperation")
        op.create.text_asset.text = v
        operaciones.append(op)
    res = asset_svc.mutate_assets(customer_id=CID, operations=operaciones)
    return [r.resource_name for r in res.results]


rn_titulos = crear_textos(TITULOS)
rn_largos = crear_textos(TITULOS_LARGOS)
rn_desc = crear_textos(DESCRIPCIONES)
rn_negocio = crear_textos([NEGOCIO])[0]
print(f"  recursos de texto listos: {len(rn_titulos)} + {len(rn_largos)} + "
      f"{len(rn_desc)} + 1")


def texto(recurso, campo):
    o, ga = nueva("asset_group_asset_operation")
    ga.create.asset = recurso
    ga.create.asset_group = rn("assetGroups", -3)
    ga.create.field_type = campo
    ops.append(o)


for t in rn_titulos:
    texto(t, F.HEADLINE)
for t in rn_largos:
    texto(t, F.LONG_HEADLINE)
for d in rn_desc:
    texto(d, F.DESCRIPTION)

# --- 6b. nombre de negocio y logo, a nivel de CAMPANA ---
#
# La cuenta tiene activado Brand Guidelines: con esa opcion el nombre y el
# logo dejan de ir en el grupo de recursos y pasan a la campana, para que sean
# los mismos en todos los grupos. Ponerlos en el grupo da error.
o, ca = nueva("campaign_asset_operation")
ca.create.asset = rn_negocio
ca.create.campaign = rn("campaigns", -2)
ca.create.field_type = F.BUSINESS_NAME
ops.append(o)

for archivo, campo in (("logo_1x1.png", F.LOGO),
                       ("logo_4x1.png", F.LANDSCAPE_LOGO)):
    o, ca = nueva("campaign_asset_operation")
    ca.create.asset = logos[archivo]
    ca.create.campaign = rn("campaigns", -2)
    ca.create.field_type = campo
    ops.append(o)


# --- 7. imagenes y videos que ya existen ---
def enlazar(asset_id, campo):
    o, ga = nueva("asset_group_asset_operation")
    ga.create.asset = f"customers/{CID}/assets/{asset_id}"
    ga.create.asset_group = rn("assetGroups", -3)
    ga.create.field_type = campo
    ops.append(o)


for i in IMG_HORIZONTAL:
    enlazar(i, F.MARKETING_IMAGE)
for i in IMG_CUADRADA:
    enlazar(i, F.SQUARE_MARKETING_IMAGE)
for i in IMG_VERTICAL:
    enlazar(i, F.PORTRAIT_MARKETING_IMAGE)
for v in VIDEOS:
    enlazar(v, F.YOUTUBE_VIDEO)

print()
print(NOMBRE)
print(f"  presupuesto {PRESUPUESTO:,} COP/dia | maximizar conversiones | EN PAUSA")
print(f"  destino {URL} | Colombia | espanol")
print(f"  {len(IMG_HORIZONTAL)} horizontales, {len(IMG_CUADRADA)} cuadradas, "
      f"{len(IMG_VERTICAL)} verticales, {len(VIDEOS)} videos, 2 logos")
print(f"  {len(ops)} operaciones")

req = cli.get_type("MutateGoogleAdsRequest")
req.customer_id = CID
req.mutate_operations.extend(ops)
req.validate_only = DRY

try:
    res = svc.mutate(request=req)
    if DRY:
        print()
        print("VALIDACION OK contra la API. Ejecutar con --go para crear.")
    else:
        print()
        print(f"CREADA. {len(res.mutate_operation_responses)} recursos.")
        for r in res.mutate_operation_responses:
            w = r._pb.WhichOneof("response")
            if w in ("campaign_result", "asset_group_result",
                     "campaign_budget_result"):
                print("   " + getattr(r, w).resource_name)
except Exception as e:
    print()
    print("ERROR de la API:")
    fallo = getattr(e, "failure", None)
    if fallo:
        vistos = set()
        for err in fallo.errors:
            campo = ".".join(str(x.field_name)
                             for x in err.location.field_path_elements)
            clave = (campo, err.message)
            if clave in vistos:
                continue
            vistos.add(clave)
            print(f"   [{campo}] {err.message}")
    else:
        print("   " + str(e)[:600])
    raise SystemExit(1)
