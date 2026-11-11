# -*- coding: utf-8 -*-
"""Rampa de presupuesto de noviembre, paso 1 (9-nov-2026).

QUE SE APROBO
-------------
El cliente aprobo ampliar el presupuesto del mes a 16,1 millones, pero NO de
golpe: en incrementos. Este script aplica el primer tramo.

POR QUE EN TRAMOS Y NO DE UNA
-----------------------------
Meta trata un salto grande de presupuesto como una edicion significativa y
reinicia la fase de aprendizaje del conjunto. Durante ese reinicio el costo por
solicitud sube justo cuando mas volumen necesitamos. El tope seguro es 25% por
cambio, espaciados unos 4 dias. En Google no hay fase de aprendizaje que se
reinicie igual, pero subir de golpe una campana de busqueda la obliga a comprar
subastas mas caras antes de que el algoritmo ajuste.

LA CUENTA
---------
  gastado del 1 al 8      3.279.193   (Meta C1+C2+C4 2.559.593 + Google 719.600)
  objetivo del mes       16.060.068
  queda                  12.780.875   para 22 dias = 581.000 por dia
  ritmo actual              410.000 por dia

No se llega a 581.000 de un salto. La rampa, con TODOS los tramos en lunes:

  paso 1  lunes 9-nov    485.224 por dia   (+18% sobre el ritmo actual)
  paso 2  lunes 16-nov   ~606.500 por dia  (+25%)
  paso 3  lunes 23-nov   ~642.000 por dia  (+6%)

POR QUE TODOS LOS TRAMOS CAEN EN LUNES
--------------------------------------
Decision del 9-nov: no se toca el fin de semana. Baja de forma natural y no se
va a pelear con eso; lo que se busca es que los dias buenos cubran el deficit.
La forma barata de hacerlo, sin programacion por horario ni recortes de fin de
semana, es que cada aumento ENTRE EN LUNES: asi el dinero nuevo pasa cuatro
dias en el tramo barato de la semana antes de llegar al caro.

El dato que lo sustenta, y que se repite en octubre y en noviembre:

                  octubre   noviembre
  lunes a jueves    2.506       2.254   <- el tramo barato
  viernes a domingo 3.043       2.946   <- 31% mas caro

Un tramo que entrara un jueves o un viernes estrenaria presupuesto justo en los
dias peores. Entrando en lunes, no.

LO QUE HAY QUE LOGRAR, EN SOLICITUDES POR DIA
---------------------------------------------
Faltan 6.088 solicitudes en 22 dias. Manteniendo la proporcion observada entre
dias buenos y fin de semana (1,27 a 1), el mes cierra en la meta si:

  lunes a jueves    ~303 por dia   (hoy van en 222)
  viernes a domingo ~239 por dia   (hoy van en 175)

Ese es el numero contra el que hay que medir cada semana, no los 255 planos:
255 todos los dias no corresponde a como se comporta la demanda.

LO QUE NO SE TOCA
-----------------
  - "Campana de formulario Copia 06/05/2026": presupuesto del cliente, aparte.
  - Las dos campanas de webinar: activas pero sin entrega, no consumen.
  - C7 Performance Max: se sostiene en 14.000 hasta releerla el 16 con la
    atribucion cerrada. Su costo aparente cambia mucho segun cuando se mire.

POR QUE C1 SUBE SOLO 15% Y LAS OTRAS 25%
----------------------------------------
C1 tiene dos conjuntos activos: `sectores-alto-volumen` (con c1-video-6) en
fase SUCCESS, y `general-convenio` (el dinamico creado el 4-nov), que todavia
no reporta fase de aprendizaje. El presupuesto de C1 es de campana (CBO), asi
que un cambio afecta a los dos. Se sube menos para no arriesgar el conjunto que
aun no ha estabilizado.

POR QUE GOOGLE BUSQUEDA SUBE FUERTE
-----------------------------------
C6 y C5 estan perdiendo 31,2% y 25,2% de impresiones POR PRESUPUESTO, y del 5
al 8 de noviembre trajeron solicitudes a 3.118 y 3.021, mejor que su propio
octubre. Es el dinero incremental mas eficiente que hay hoy en la cuenta: el
nuevo presupuesto se calcula para cubrir justo esa perdida.

Uso:  python rampa_presupuesto_nov.py        -> simula
      python rampa_presupuesto_nov.py --go   -> aplica
"""
import json, os, sys, requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
DRY = "--go" not in sys.argv

# ----------------------------------------------------------------- META -----
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
T = cred["access_token"]
ACT = str(cred["ad_account_id"])
ACT = ACT if ACT.startswith("act_") else "act_" + ACT
G = "https://graph.facebook.com/v19.0"

META_NUEVOS = {
    "C1 - Convenio por sectores - Oct2026":    102_350,   # 89.000  +15%
    "C2 - Empleados sector privado - Oct2026": 148_437,   # 118.750 +25%
    "C4 - Retargeting caliente - Oct2026":     148_437,   # 118.750 +25%
}
TOPE_META = 0.25


def meta_get(path, **p):
    p["access_token"] = T
    out, url = [], "%s/%s" % (G, path)
    while url:
        j = requests.get(url, params=p, timeout=60).json()
        if "error" in j:
            raise SystemExit("Meta: " + j["error"].get("message", "?")[:200])
        out += j.get("data", [])
        url = (j.get("paging") or {}).get("next")
        p = None
    return out


campanas = {c["name"]: c for c in meta_get("%s/campaigns" % ACT,
            fields="id,name,daily_budget,effective_status", limit=100)}

print("=== META ===")
print("Fase de aprendizaje de los conjuntos afectados")
for a in meta_get("%s/adsets" % ACT, limit=200,
                  fields="name,campaign{name},effective_status,learning_stage_info"):
    cam = (a.get("campaign") or {}).get("name", "")
    if cam not in META_NUEVOS or a.get("effective_status") != "ACTIVE":
        continue
    fase = (a.get("learning_stage_info") or {}).get("status", "SIN_DATO")
    print("   %-42s %-24s %s" % (cam[:42], a["name"][:24], fase))
    if fase == "LEARNING":
        raise SystemExit("   %s esta APRENDIENDO: no se aplica nada." % a["name"])

print()
ops_meta = []
for nombre, nuevo in META_NUEVOS.items():
    c = campanas.get(nombre)
    if not c:
        raise SystemExit("no encuentro la campana %s" % nombre)
    viejo = int(c.get("daily_budget") or 0)
    if not viejo:
        raise SystemExit("%s no tiene presupuesto de campana" % nombre)
    salto = nuevo / viejo - 1
    if salto > TOPE_META + 1e-9:
        raise SystemExit("%s subiria %.1f%%, por encima del tope de %.0f%%"
                         % (nombre, salto * 100, TOPE_META * 100))
    print("  %-44s %9s -> %9s  (%+.1f%%)" % (nombre[:44], format(viejo, ","),
                                             format(nuevo, ","), salto * 100))
    ops_meta.append((c["id"], nombre, nuevo))

total_meta = sum(n for _, _, n in ops_meta)
print("  %-44s %9s -> %9s" % ("TOTAL diario Meta", format(
    sum(int(campanas[n].get("daily_budget") or 0) for n in META_NUEVOS), ","),
    format(total_meta, ",")))

# --------------------------------------------------------------- GOOGLE -----
from actualizar_google_ads import (get_credentials, DEVELOPER_TOKEN,
                                   LOGIN_CUSTOMER_ID, CUSTOMER_ID,
                                   CLIENT_SECRET_FILE)
from google.ads.googleads.client import GoogleAdsClient
from google.api_core import protobuf_helpers

GOOGLE_NUEVOS = {
    "C6 - Búsqueda - Reportados - Jun2026":      40_000,   # 28.000, cubre el 31,2% perdido
    "C5 - Búsqueda - Libranza Nómina - Jun2026": 32_000,   # 24.000, cubre el 25,2% perdido
    # C7 Performance Max se queda en 14.000 a proposito.
}
MICRO = 1_000_000

creds = get_credentials()
sec = json.load(open(CLIENT_SECRET_FILE))["installed"]
cli = GoogleAdsClient.load_from_dict({
    "developer_token": DEVELOPER_TOKEN,
    "client_id": sec["client_id"], "client_secret": sec["client_secret"],
    "refresh_token": creds.refresh_token,
    "login_customer_id": LOGIN_CUSTOMER_ID, "use_proto_plus": True})
svc = cli.get_service("GoogleAdsService")

filas = list(svc.search(customer_id=CUSTOMER_ID, query="""
    SELECT campaign.name, campaign.status, campaign_budget.resource_name,
           campaign_budget.amount_micros
    FROM campaign WHERE campaign.status = 'ENABLED'"""))

print("\n=== GOOGLE ===")
ops_google, total_google = [], 0
for f in filas:
    n = f.campaign.name
    actual = f.campaign_budget.amount_micros / MICRO
    nuevo = GOOGLE_NUEVOS.get(n)
    if nuevo is None:
        print("  %-44s %9s   (sin cambio)" % (n[:44], format(int(actual), ",")))
        total_google += actual
        continue
    print("  %-44s %9s -> %9s  (%+.1f%%)" % (
        n[:44], format(int(actual), ","), format(nuevo, ","), (nuevo / actual - 1) * 100))
    ops_google.append((f.campaign_budget.resource_name, n, nuevo))
    total_google += nuevo
print("  %-44s %9s" % ("TOTAL diario Google", format(int(total_google), ",")))

print("\n=== RESUMEN DEL PASO 1 ===")
print("  Meta   %10s por dia" % format(total_meta, ","))
print("  Google %10s por dia" % format(int(total_google), ","))
print("  TOTAL  %10s por dia" % format(int(total_meta + total_google), ","))
print("  (el paso 2, el lunes 16, va a ~606.500)")

if DRY:
    print("\nSIMULACION. Ejecutar con --go para aplicarlo.")
    raise SystemExit

for cid, nombre, nuevo in ops_meta:
    r = requests.post("%s/%s" % (G, cid),
                      data={"access_token": T, "daily_budget": nuevo}, timeout=60)
    if r.status_code >= 400:
        raise SystemExit("ERROR en %s: %s" % (nombre, r.text[:300]))
    print("Meta ok: %s -> %s" % (nombre, format(nuevo, ",")))

bsvc = cli.get_service("CampaignBudgetService")
ops = []
for rn, nombre, nuevo in ops_google:
    op = cli.get_type("CampaignBudgetOperation")
    b = op.update
    b.resource_name = rn
    b.amount_micros = int(nuevo * MICRO)
    # El cliente de v24 no expone un tipo FieldMask propio: se arma asi.
    op.update_mask.CopyFrom(protobuf_helpers.field_mask(None, b._pb))
    ops.append(op)
if ops:
    res = bsvc.mutate_campaign_budgets(customer_id=CUSTOMER_ID, operations=ops)
    print("Google ok: %d presupuestos actualizados" % len(res.results))

print("\nLISTO. Paso 1 aplicado. El paso 2 va el jueves 13.")
