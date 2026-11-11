# -*- coding: utf-8 -*-
"""Se apaga Performance Max y su presupuesto pasa a las dos de busqueda (11-nov-2026).

POR QUE SE APAGA
----------------
C7 Performance Max lleva dos ventanas con la atribucion ya cerrada y las dos
dan lo mismo:

                      costo por conversion
  1 al 8 de nov               8.722
  3 y 4 de nov (a 7 dias)    12.791
  9 y 10 de nov              13.392

Busqueda, en los mismos dias 9 y 10, esta en 3.174 y 3.246. PMax cuesta cuatro
veces mas. El 4 de noviembre se le recorto de 40.000 a 14.000 en vez de
apagarla, porque una lectura temprana puede estar inflada por el rezago con que
Google registra sus conversiones; ese rezago ya paso y el numero no se movio.

A DONDE VA EL DINERO
--------------------
A C6 y C5, que son las dos campanas con mejor costo de toda la cuenta y que
siguen TOPADAS: pierden 44,2% y 40,2% de impresiones por presupuesto. Es decir,
hay demanda buscando credito por libranza que no estamos atendiendo por plata,
al mejor precio que tenemos. C5 ademas acaba de mejorar de 5.912 a 3.246 con el
aumento del lunes, asi que responde.

El total diario de Google NO cambia: 86.000 antes y despues. Esto es una
redistribucion, no un aumento. El aumento va aparte, el lunes 16.

  C6  40.000 -> 48.000   (+20%)
  C5  32.000 -> 38.000   (+18,8%)
  C7  14.000 -> PAUSADA

Reversible: basta volver C7 a ENABLED y devolver los presupuestos.

Uso:  python apagar_pmax.py        -> simula
      python apagar_pmax.py --go   -> lo aplica
"""
import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
DRY = "--go" not in sys.argv

from actualizar_google_ads import (get_credentials, DEVELOPER_TOKEN,
                                   LOGIN_CUSTOMER_ID, CUSTOMER_ID,
                                   CLIENT_SECRET_FILE)
from google.ads.googleads.client import GoogleAdsClient
from google.api_core import protobuf_helpers

MICRO = 1_000_000
A_PAUSAR = "C7 - Performance Max - Libranza - Oct2026"
NUEVOS = {
    "C6 - Búsqueda - Reportados - Jun2026":      48_000,
    "C5 - Búsqueda - Libranza Nómina - Jun2026": 38_000,
}

creds = get_credentials()
sec = json.load(open(CLIENT_SECRET_FILE))["installed"]
cli = GoogleAdsClient.load_from_dict({
    "developer_token": DEVELOPER_TOKEN,
    "client_id": sec["client_id"], "client_secret": sec["client_secret"],
    "refresh_token": creds.refresh_token,
    "login_customer_id": LOGIN_CUSTOMER_ID, "use_proto_plus": True})
svc = cli.get_service("GoogleAdsService")

filas = list(svc.search(customer_id=CUSTOMER_ID, query="""
    SELECT campaign.resource_name, campaign.name, campaign.status,
           campaign_budget.resource_name, campaign_budget.amount_micros
    FROM campaign WHERE campaign.status = 'ENABLED'"""))

print("%-44s %9s %12s" % ("campana", "hoy", "queda"))
print("-" * 68)
ops_presu, op_pausa, total_antes, total_despues = [], None, 0, 0
for f in filas:
    n = f.campaign.name
    actual = f.campaign_budget.amount_micros / MICRO
    total_antes += actual
    if n == A_PAUSAR:
        op_pausa = f.campaign.resource_name
        print("%-44s %9s %12s" % (n[:44], format(int(actual), ","), "PAUSADA"))
        continue
    nuevo = NUEVOS.get(n)
    if nuevo is None:
        print("%-44s %9s %12s" % (n[:44], format(int(actual), ","), "sin cambio"))
        total_despues += actual
        continue
    print("%-44s %9s %12s  (%+.1f%%)" % (
        n[:44], format(int(actual), ","), format(nuevo, ","), (nuevo / actual - 1) * 100))
    ops_presu.append((f.campaign_budget.resource_name, n, nuevo))
    total_despues += nuevo

print("-" * 68)
print("%-44s %9s %12s" % ("TOTAL diario Google", format(int(total_antes), ","),
                          format(int(total_despues), ",")))
if op_pausa is None:
    raise SystemExit("\nNo encontre %s activa. No se aplica nada." % A_PAUSAR)
if len(ops_presu) != len(NUEVOS):
    raise SystemExit("\nNo encontre todas las campanas de busqueda. No se aplica nada.")

if DRY:
    print("\nSIMULACION. Ejecutar con --go para aplicarlo.")
    raise SystemExit

bsvc = cli.get_service("CampaignBudgetService")
ops = []
for rn, nombre, nuevo in ops_presu:
    op = cli.get_type("CampaignBudgetOperation")
    b = op.update
    b.resource_name = rn
    b.amount_micros = int(nuevo * MICRO)
    op.update_mask.CopyFrom(protobuf_helpers.field_mask(None, b._pb))
    ops.append(op)
res = bsvc.mutate_campaign_budgets(customer_id=CUSTOMER_ID, operations=ops)
print("presupuestos actualizados: %d" % len(res.results))

csvc = cli.get_service("CampaignService")
cop = cli.get_type("CampaignOperation")
c = cop.update
c.resource_name = op_pausa
c.status = cli.enums.CampaignStatusEnum.PAUSED
cop.update_mask.CopyFrom(protobuf_helpers.field_mask(None, c._pb))
r = csvc.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[cop])
print("Performance Max pausada: %s" % r.results[0].resource_name)
print("\nLISTO.")
