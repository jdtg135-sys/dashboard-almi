# -*- coding: utf-8 -*-
"""Control diario de la rampa de noviembre (desde el 9-nov-2026).

PARA QUE SIRVE
--------------
La rampa de presupuesto compromete al cliente con un costo por solicitud, no
con un volumen. Este script revisa SIEMPRE lo mismo y en el mismo orden, para
que la revision no dependa de que uno se acuerde de mirar algo. Imprime
alertas con umbrales fijos, decididos de antemano.

LO QUE REVISA, EN ORDEN DE GRAVEDAD
-----------------------------------
  1. Anuncios bloqueados o rechazados. Un anuncio rechazado no avisa y mata el
     volumen en silencio. Es lo primero que se mira.
  2. Costo por solicitud contra la linea base de 2.099 (el costo del 1 al 8,
     que es el que se le prometio al cliente).
  3. Entrega contra presupuesto. Si gastamos menos del 90% de lo presupuestado,
     el problema no es plata y subir mas no sirve.
  4. Fatiga de creativo: CTR y frecuencia por campana.
  5. Proyeccion del mes contra la meta de 7.650.

LA CIFRA QUE MANDA
------------------
El costo por solicitud se calcula con el conteo REAL de la plataforma, que
entrega el cliente y vive en `solicitudes_reales.json`. Meta y GA4 subcuentan
(GA4 solo ve web). Si falta el dato de ayer, el script lo dice y usa lo
atribuido, dejando claro que es una aproximacion.

NO ENTRA EN LAS CUENTAS
-----------------------
"Campana de formulario Copia 06/05/2026": presupuesto y contactos del cliente,
van aparte.

Uso:  python control_diario.py           -> revisa hasta ayer
      python control_diario.py 2026-11-13 -> revisa hasta esa fecha
"""
import datetime, json, os, sys, requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

# --- Parametros del compromiso con el cliente -------------------------------
COSTO_BASE = 2_099          # costo por solicitud del 1 al 8, la linea base
META_DIARIA = 255
DIAS_MES = 30
META_MES = META_DIARIA * DIAS_MES
PRESUPUESTO_MES = 16_060_068
FUERA_DE_CUENTAS = "Campaña de formulario"   # campana del cliente, va aparte
# Fecha del ultimo cambio de presupuesto. El punto 3 solo tiene sentido con un
# dia COMPLETO bajo el presupuesto vigente: antes de eso compara peras con
# manzanas y dispara una alerta falsa. Actualizar en cada tramo de la rampa.
ULTIMO_CAMBIO = datetime.date(2026, 11, 9)

# --- Umbrales de alerta, fijos ----------------------------------------------
U_COSTO_DIA = 1.20          # costo de un dia 20% sobre la base -> mirar
U_COSTO_3D = 1.10           # promedio de 3 dias 10% sobre la base -> frenar rampa
U_ENTREGA = 0.90            # gastar menos del 90% del presupuesto -> no es plata
U_FRECUENCIA = 2.0          # saturacion de audiencia
U_CTR_CAIDA = 0.15          # caida de CTR de 15% contra la semana previa

HOY = datetime.date.today()
HASTA = (datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1
         else HOY - datetime.timedelta(days=1))
DESDE = datetime.date(2026, 11, 1)

alertas = []


def alerta(nivel, texto):
    alertas.append((nivel, texto))


# ----------------------------------------------------------------- META -----
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
T = cred["access_token"]
ACT = str(cred["ad_account_id"])
ACT = ACT if ACT.startswith("act_") else "act_" + ACT
G = "https://graph.facebook.com/v19.0"
CONV = "offsite_conversion.fb_pixel_purchase"


def mget(path, **p):
    p["access_token"] = T
    out, url = [], "%s/%s" % (G, path)
    while url:
        j = requests.get(url, params=p, timeout=90).json()
        if "error" in j:
            raise SystemExit("Meta: " + j["error"].get("message", "?")[:200])
        out += j.get("data", [])
        url = (j.get("paging") or {}).get("next")
        p = None
    return out


def minsights(fields, desde, hasta, nivel="campaign", diario=False):
    p = {"fields": ",".join(fields), "level": nivel,
         "time_range": json.dumps({"since": str(desde), "until": str(hasta)}),
         "limit": 500}
    if diario:
        p["time_increment"] = 1
    return mget("%s/insights" % ACT, **p)


def conv(f):
    return sum(float(a["value"]) for a in f.get("actions", [])
               if a["action_type"] == CONV)


print("=" * 72)
print("CONTROL DIARIO ALMI  ·  del %s al %s" % (DESDE, HASTA))
print("=" * 72)

# --- 1. Anuncios bloqueados -------------------------------------------------
print("\n1 · ENTREGA DE LOS ANUNCIOS")
SANOS = {"ACTIVE", "CAMPAIGN_PAUSED", "ADSET_PAUSED", "PAUSED"}
problemas = 0
for a in mget("%s/ads" % ACT, limit=500,
              fields="name,status,effective_status,campaign{name}"):
    if a.get("status") != "ACTIVE":
        continue
    cam = (a.get("campaign") or {}).get("name", "")
    if cam.startswith(FUERA_DE_CUENTAS[:5]):
        continue
    ef = a.get("effective_status")
    if ef not in SANOS:
        problemas += 1
        print("   BLOQUEADO  %-34s %s" % (a["name"][:34], ef))
        alerta("GRAVE", "anuncio %s en estado %s: no esta entregando" % (a["name"], ef))
if not problemas:
    print("   Todos los anuncios activos estan entregando.")

# --- 2. Costo por solicitud -------------------------------------------------
reales = {k: v for k, v in json.load(open(
    os.path.join(BASE, "analisis", "solicitudes_reales.json"))).items()
    if not k.startswith("_")}

gasto_meta = {}
for f in minsights(["campaign_name", "spend"], DESDE, HASTA, diario=True):
    if f["campaign_name"].startswith(FUERA_DE_CUENTAS[:5]):
        continue
    gasto_meta[f["date_start"]] = gasto_meta.get(f["date_start"], 0) + float(f["spend"])

conv_meta = {}
for f in minsights(["campaign_name", "actions"], DESDE, HASTA, diario=True):
    if f["campaign_name"].startswith(FUERA_DE_CUENTAS[:5]):
        continue
    conv_meta[f["date_start"]] = conv_meta.get(f["date_start"], 0) + conv(f)

# --------------------------------------------------------------- GOOGLE -----
from actualizar_google_ads import (get_credentials, DEVELOPER_TOKEN,
                                   LOGIN_CUSTOMER_ID, CUSTOMER_ID,
                                   CLIENT_SECRET_FILE)
from google.ads.googleads.client import GoogleAdsClient

creds = get_credentials()
sec = json.load(open(CLIENT_SECRET_FILE))["installed"]
gcli = GoogleAdsClient.load_from_dict({
    "developer_token": DEVELOPER_TOKEN,
    "client_id": sec["client_id"], "client_secret": sec["client_secret"],
    "refresh_token": creds.refresh_token,
    "login_customer_id": LOGIN_CUSTOMER_ID, "use_proto_plus": True})
gsvc = gcli.get_service("GoogleAdsService")

gasto_goo, conv_goo = {}, {}
for f in gsvc.search(customer_id=CUSTOMER_ID, query="""
        SELECT segments.date, metrics.cost_micros, metrics.conversions
        FROM campaign WHERE segments.date BETWEEN '%s' AND '%s'
        AND metrics.impressions > 0""" % (DESDE, HASTA)):
    d = f.segments.date
    gasto_goo[d] = gasto_goo.get(d, 0) + f.metrics.cost_micros / 1_000_000
    conv_goo[d] = conv_goo.get(d, 0) + f.metrics.conversions

print("\n2 · COSTO POR SOLICITUD  (base comprometida: %s)" % format(COSTO_BASE, ","))
print("   %-11s %10s %8s %10s %s" % ("fecha", "inversion", "solic.", "costo", ""))
dias = sorted(set(gasto_meta) | set(gasto_goo))

# FACTOR DE SUBCONTEO. Meta y Google juntos atribuyen bastante menos de lo que
# la plataforma de ALMI registra: GA4 solo ve web y las plataformas solo ven lo
# que pueden atribuir a un clic suyo. Mezclar dias con conteo real y dias con
# conteo atribuido en la misma serie infla el costo de los dias recientes y
# dispara alertas falsas. Por eso los dias sin dato real se estiman escalando
# lo atribuido por la proporcion medida en los dias que SI tienen ambos.
_ra = _aa = 0.0
for d in dias:
    if d in reales:
        _ra += reales[d]
        _aa += conv_meta.get(d, 0) + conv_goo.get(d, 0)
FACTOR = (_ra / _aa) if _aa else 1.0

tot_g = tot_s = 0
serie = []
faltan_reales = []
for d in dias:
    g = gasto_meta.get(d, 0) + gasto_goo.get(d, 0)
    if d in reales:
        s, marca = reales[d], ""
    else:
        s = (conv_meta.get(d, 0) + conv_goo.get(d, 0)) * FACTOR
        marca = "  (estimado x%.2f, falta el real)" % FACTOR
        faltan_reales.append(d)
    c = g / s if s else 0
    serie.append((d, g, s, c))
    tot_g += g
    tot_s += s
    flag = ""
    if c > COSTO_BASE * U_COSTO_DIA:
        flag = "  <-- %.0f%% sobre la base" % ((c / COSTO_BASE - 1) * 100)
    print("   %-11s %10s %8.0f %10s%s%s" % (
        d, format(int(g), ","), s, format(int(c), ","), marca, flag))

costo_acum = tot_g / tot_s if tot_s else 0
print("   " + "-" * 60)
print("   %-11s %10s %8.0f %10s" % ("ACUMULADO", format(int(tot_g), ","),
                                    tot_s, format(int(costo_acum), ",")))

if faltan_reales:
    alerta("AVISO", "faltan los conteos reales de %s. Estan estimados escalando lo "
           "atribuido por %.2f, la proporcion medida en los dias con dato real. "
           "Pedirlos al cliente antes de decidir sobre la rampa."
           % (", ".join(faltan_reales), FACTOR))

ult3 = serie[-3:]
if len(ult3) == 3:
    g3 = sum(x[1] for x in ult3)
    s3 = sum(x[2] for x in ult3)
    c3 = g3 / s3 if s3 else 0
    print("   ultimos 3 dias: %s por solicitud (%+.1f%% contra la base)"
          % (format(int(c3), ","), (c3 / COSTO_BASE - 1) * 100))
    if c3 > COSTO_BASE * U_COSTO_3D:
        alerta("GRAVE", "el costo de los ultimos 3 dias (%s) supera la base en %.0f%%: "
               "NO aplicar el siguiente tramo de la rampa hasta entender por que"
               % (format(int(c3), ","), (c3 / COSTO_BASE - 1) * 100))

# --- 3. Entrega contra presupuesto ------------------------------------------
print("\n3 · ENTREGA CONTRA PRESUPUESTO")
camp = mget("%s/campaigns" % ACT, fields="name,daily_budget,status", limit=100)
presu_meta = sum(int(c.get("daily_budget") or 0) for c in camp
                 if c["status"] == "ACTIVE" and not c["name"].startswith(FUERA_DE_CUENTAS[:5]))
presu_goo = 0
for f in gsvc.search(customer_id=CUSTOMER_ID, query="""
        SELECT campaign.name, campaign_budget.amount_micros
        FROM campaign WHERE campaign.status = 'ENABLED'"""):
    presu_goo += f.campaign_budget.amount_micros / 1_000_000
presu = presu_meta + presu_goo
ayer = serie[-1] if serie else None
if ayer:
    uso = ayer[1] / presu if presu else 0
    print("   presupuesto diario hoy   %10s  (Meta %s + Google %s)" % (
        format(int(presu), ","), format(presu_meta, ","), format(int(presu_goo), ",")))
    print("   gastado el %s      %10s  (%.0f%% del presupuesto)" % (
        ayer[0], format(int(ayer[1]), ","), uso * 100))
    if datetime.date.fromisoformat(ayer[0]) < ULTIMO_CAMBIO:
        print("   (el presupuesto cambio el %s: esta comparacion sirve desde el %s)"
              % (ULTIMO_CAMBIO, ULTIMO_CAMBIO + datetime.timedelta(days=1)))
    elif uso < U_ENTREGA:
        alerta("AVISO", "solo se gasto el %.0f%% del presupuesto: la restriccion no es "
               "dinero, subirlo mas no traeria volumen" % (uso * 100))

# --- 4. Fatiga de creativo --------------------------------------------------
print("\n4 · FATIGA DE CREATIVO  (ultimos 3 dias contra los 7 previos)")
fin_a = HASTA
ini_a = HASTA - datetime.timedelta(days=2)
fin_b = ini_a - datetime.timedelta(days=1)
ini_b = fin_b - datetime.timedelta(days=6)


def por_campana(desde, hasta):
    out = {}
    for f in minsights(["campaign_name", "ctr", "frequency", "spend"], desde, hasta):
        if f["campaign_name"].startswith(FUERA_DE_CUENTAS[:5]):
            continue
        out[f["campaign_name"]] = (float(f.get("ctr") or 0),
                                   float(f.get("frequency") or 0))
    return out


a, b = por_campana(ini_a, fin_a), por_campana(ini_b, fin_b)
print("   %-42s %7s %7s %7s" % ("campana", "CTR ant", "CTR hoy", "frec"))
for n in sorted(a):
    ctr_a, frec = a[n]
    ctr_b = b.get(n, (0, 0))[0]
    print("   %-42s %7.2f %7.2f %7.2f" % (n[:42], ctr_b, ctr_a, frec))
    if ctr_b and ctr_a < ctr_b * (1 - U_CTR_CAIDA):
        alerta("AVISO", "%s: el CTR cayo %.0f%% (de %.2f a %.2f). Renovar creativo."
               % (n[:40], (1 - ctr_a / ctr_b) * 100, ctr_b, ctr_a))
    if frec > U_FRECUENCIA:
        alerta("AVISO", "%s: frecuencia en %.2f, la audiencia se esta saturando"
               % (n[:40], frec))

# --- 5. Proyeccion del mes --------------------------------------------------
print("\n5 · PROYECCION DEL MES")
dias_corridos = (HASTA - DESDE).days + 1
por_dia = tot_s / dias_corridos if dias_corridos else 0
# La proyeccion se pondera por dia de semana, no con el promedio plano. Los
# fines de semana rinden bastante menos, asi que un promedio simple sobre una
# muestra con mas domingos de la cuenta subestima el mes, y sobre una con menos
# lo infla. Se le da a cada dia que falta el promedio de SU dia de semana.
_por_wd = {}
for d, g, sol, c in serie:
    _por_wd.setdefault(datetime.date.fromisoformat(d).weekday(), []).append(sol)
_media_wd = dict((w, sum(L) / len(L)) for w, L in _por_wd.items())
proy = tot_s
for n_dia in range(dias_corridos + 1, DIAS_MES + 1):
    w = datetime.date(DESDE.year, DESDE.month, n_dia).weekday()
    proy += _media_wd.get(w, por_dia)
print("   solicitudes al %s   %8.0f  (%.0f por dia)" % (HASTA, tot_s, por_dia))
print("   proyeccion del mes          %8.0f  (ponderada por dia de semana)" % proy)
print("   meta del mes                %8s  (%.0f%% de la meta)" % (
    format(META_MES, ","), proy / META_MES * 100))
print("   presupuesto consumido       %8.1f%%  del mes va %.1f%%" % (
    tot_g / PRESUPUESTO_MES * 100, dias_corridos / DIAS_MES * 100))
if proy < META_MES * 0.95:
    alerta("AVISO", "la proyeccion va en %.0f%% de la meta: avisarle al cliente ahora, "
           "no a fin de mes" % (proy / META_MES * 100))

# --- Resumen ----------------------------------------------------------------
print("\n" + "=" * 72)
if not alertas:
    print("SIN ALERTAS. Todo dentro de los umbrales.")
else:
    for nivel, txt in sorted(alertas, key=lambda x: x[0] != "GRAVE"):
        print("[%s] %s" % (nivel, txt))
print("=" * 72)
