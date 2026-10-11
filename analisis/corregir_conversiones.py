# -*- coding: utf-8 -*-
"""Deja una sola accion de conversion principal y pone a C5/C6 a maximizar
conversiones en vez de valor.

La accion "www.almifinanciera.com (web) purchase" dejo de recibir datos el
30-sep (es la propiedad GA4 del cotizador anterior) pero seguia marcada como
principal con un valor de 25.000 COP. La nueva, loan_request_created, llega
con valor 1. Con las campanas en MAXIMIZE_CONVERSION_VALUE el resultado era
pujar por un valor que ya no existe.
"""
import sys
from ads_cliente import cliente, CID
from google.api_core import protobuf_helpers

DRY = "--go" not in sys.argv
cli = cliente()
svc = cli.get_service("GoogleAdsService")

VIEJA = "www.almifinanciera.com (web) purchase"
CAMPANAS = ("C5 - Búsqueda - Libranza Nómina - Jun2026",
            "C6 - Búsqueda - Reportados - Jun2026")

# --- 1. quitar la accion vieja como principal ---
acc = None
for b in svc.search_stream(customer_id=CID, query=f"""
  SELECT conversion_action.resource_name, conversion_action.name,
         conversion_action.primary_for_goal
  FROM conversion_action WHERE conversion_action.name = '{VIEJA}'"""):
    for r in b.results:
        acc = r.conversion_action
print(f"accion vieja: {acc.name} | principal={acc.primary_for_goal}")

if acc.primary_for_goal:
    ca_svc = cli.get_service("ConversionActionService")
    op = cli.get_type("ConversionActionOperation")
    up = op.update
    up.resource_name = acc.resource_name
    up.primary_for_goal = False
    cli.copy_from(op.update_mask, protobuf_helpers.field_mask(None, up._pb))
    if DRY:
        print("  [simulacion] dejaria de ser principal")
    else:
        ca_svc.mutate_conversion_actions(customer_id=CID, operations=[op])
        print("  -> ya no es principal")
else:
    print("  ya no era principal, nada que hacer")

# --- 2. C5 y C6 a maximizar conversiones ---
ops = []
for b in svc.search_stream(customer_id=CID, query="""
  SELECT campaign.resource_name, campaign.name, campaign.status,
         campaign.bidding_strategy_type
  FROM campaign WHERE campaign.status = 'ENABLED'"""):
    for r in b.results:
        c = r.campaign
        if not c.name.startswith(("C5", "C6")):
            continue
        print(f"{c.name[:38]:<40} {c.bidding_strategy_type.name}")
        if c.bidding_strategy_type.name == "MAXIMIZE_CONVERSIONS":
            print("   ya estaba, nada que hacer"); continue
        op = cli.get_type("CampaignOperation")
        up = op.update
        up.resource_name = c.resource_name
        up.maximize_conversions.target_cpa_micros = 0   # sin tope de CPA
        cli.copy_from(op.update_mask, protobuf_helpers.field_mask(None, up._pb))
        ops.append((c.name, op))

for nombre, _ in ops:
    print(f"  {'[simulacion] ' if DRY else ''}-> maximizar conversiones: {nombre[:38]}")
if ops and not DRY:
    cli.get_service("CampaignService").mutate_campaigns(
        customer_id=CID, operations=[o for _, o in ops])
    print("  aplicado")

print("\n" + ("SIMULACION. Ejecutar con --go" if DRY else "LISTO"))
