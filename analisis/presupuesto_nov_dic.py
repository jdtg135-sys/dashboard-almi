# -*- coding: utf-8 -*-
"""Cuanto presupuesto hace falta para 290 solicitudes diarias en noviembre
y 323 en diciembre, partiendo del costo por solicitud de hoy.

La pregunta del cliente mezcla dos cosas que hay que separar antes de
responder: el promedio diario de la plataforma incluye TODAS las solicitudes,
vengan o no de pauta. El presupuesto solo mueve la parte que viene de pauta.
Este script mide ese reparto en vez de suponerlo.
"""
import sys, os, json
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE); os.chdir(BASE)
os.environ["ALMI_COTIZADOR"] = "nuevo"
import actualizar_dashboard as D
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (DateRange, Dimension, Metric,
    RunReportRequest, FilterExpression, Filter, OrderBy)

cli = BetaAnalyticsDataClient(credentials=D.get_credentials())
P = "properties/%s" % D.PROPERTY_ID
DESDE, HASTA = "2026-10-01", "2026-10-26"
DIAS = 26

print("=== Solicitudes por canal en GA4, %s al %s ===" % (DESDE, HASTA))
r = cli.run_report(RunReportRequest(property=P,
    dimensions=[Dimension(name="sessionDefaultChannelGroup")],
    metrics=[Metric(name="eventCount")],
    date_ranges=[DateRange(start_date=DESDE, end_date=HASTA)],
    dimension_filter=FilterExpression(filter=Filter(field_name="eventName",
        string_filter=Filter.StringFilter(value="loan_request_created"))),
    order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventCount"), desc=True)],
    limit=30))
total = 0
canales = []
for x in r.rows:
    n = int(x.metric_values[0].value)
    canales.append((x.dimension_values[0].value, n))
    total += n
PAGO = ("Paid Search", "Paid Social", "Paid Video", "Paid Other",
        "Paid Shopping", "Display", "Cross-network")
de_pauta = sum(n for c, n in canales if c in PAGO)
for c, n in canales:
    marca = "pauta" if c in PAGO else ""
    print("  %-26s %7,d  %5.1f%%  %s".replace(",", ",") % (c, n, n / total * 100, marca)
          if False else "  {:<26} {:>7,}  {:>5.1f}%  {}".format(c, n, n / total * 100, marca))
print("  {:<26} {:>7,}".format("TOTAL GA4", total))
print()
print("  De pauta: {:,} ({:.1f}%)   Sin pauta: {:,} ({:.1f}%)".format(
    de_pauta, de_pauta / total * 100, total - de_pauta, (total - de_pauta) / total * 100))
print("  Promedio diario GA4: {:.1f}   de pauta: {:.1f}   sin pauta: {:.1f}".format(
    total / DIAS, de_pauta / DIAS, (total - de_pauta) / DIAS))

# --- Inversion del periodo ---
ads = json.load(open(os.path.join(BASE, "ads_data.json"), encoding="utf-8"))
meta_mes = next((m for m in ads["meta_ads"]["meses"] if "Oct" in m["label"]), {})
goog_mes = next((m for m in ads["google_ads"]["meses"] if "Oct" in m["label"]), {})

# La serie diaria permite recortar al mismo rango exacto que GA4.
def gasto_rango(serie, desde, hasta):
    return sum(float(d.get("gasto", d.get("inversion", 0)))
               for d in serie if desde <= d["fecha"] <= hasta)

gm = gasto_rango(ads["meta_ads"]["diario"], DESDE, HASTA)
gg = gasto_rango(ads["google_ads"]["diario"], DESDE, HASTA)
inv = gm + gg
print()
print("=== Inversion del mismo rango ===")
print("  Meta:   ${:>12,.0f}".format(gm))
print("  Google: ${:>12,.0f}".format(gg))
print("  TOTAL:  ${:>12,.0f}   ({:,.0f} por dia)".format(inv, inv / DIAS))

costo = inv / de_pauta if de_pauta else 0
print()
print("=== Costo por solicitud de pauta (base GA4) ===")
print("  ${:,.0f}".format(costo))

# La plataforma recibe mas solicitudes que las que GA4 alcanza a registrar.
# Medido el 21-oct-2026: 2.037 contra 1.727, un 18% mas. Se deja explicito
# como supuesto para poder cambiarlo sin tocar el resto del calculo.
AJUSTE = 1.18
costo_real = costo / AJUSTE
print("  ${:,.0f}  ajustado por el +{:.0f}% que la plataforma registra de mas".format(
    costo_real, (AJUSTE - 1) * 100))

print()
print("=== Presupuesto necesario ===")
base_sin_pauta = (total - de_pauta) / DIAS * AJUSTE
for mes, meta_diaria, dias_mes in (("Noviembre", 290, 30), ("Diciembre", 323, 31)):
    falta = meta_diaria - base_sin_pauta
    dia = falta * costo_real
    print("  {}: meta {}/dia, {} dias".format(mes, meta_diaria, dias_mes))
    print("      sin pauta aportan ~{:.0f}/dia -> la pauta debe traer {:.0f}/dia".format(
        base_sin_pauta, falta))
    print("      inversion diaria ${:,.0f}   mensual ${:,.0f}".format(dia, dia * dias_mes))
    hoy_dia = inv / DIAS
    print("      hoy se invierten ${:,.0f}/dia  ->  x{:.2f}".format(hoy_dia, dia / hoy_dia))
    print()
