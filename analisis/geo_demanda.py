# -*- coding: utf-8 -*-
"""Hay demanda por ciudad que las campanas no estan capturando? (11-nov-2026)

Meta no desglosa las conversiones del pixel por region, asi que el embudo por
ciudad se saca de GA4, que si tiene geografia y el evento de solicitud. El
gasto por region si sale de Meta, y cruzando ambos se ve donde invertimos de
mas y donde de menos respecto de lo que cada ciudad produce.
"""
import os, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE); os.chdir(BASE)
os.environ["ALMI_COTIZADOR"] = "nuevo"
import actualizar_dashboard as D
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (DateRange, Dimension, Metric,
                                                RunReportRequest, Filter, FilterExpression)

cli = BetaAnalyticsDataClient(credentials=D.get_credentials())
DR = [DateRange(start_date="2026-10-15", end_date="2026-11-11")]


def por_ciudad(evento):
    r = cli.run_report(RunReportRequest(
        property=f"properties/{D.PROPERTY_ID}",
        dimensions=[Dimension(name="city")],
        metrics=[Metric(name="activeUsers")],
        date_ranges=DR, limit=400,
        dimension_filter=FilterExpression(filter=Filter(
            field_name="eventName", string_filter=Filter.StringFilter(value=evento)))))
    return {x.dimension_values[0].value: int(x.metric_values[0].value) for x in r.rows}


entran = por_ciudad("company_selected")
solic = por_ciudad("loan_request_created")

tot_e = sum(entran.values())
tot_s = sum(solic.values())
print("GA4 · 15-oct al 11-nov · %s entran · %s solicitudes · conversion global %.1f%%"
      % (format(tot_e, ","), format(tot_s, ","), tot_s / tot_e * 100))
print()
print("%-26s %9s %9s %8s %7s %7s" % (
    "ciudad", "entran", "solicit.", "conv", "%entran", "%solic"))
print("-" * 74)
filas = []
for c, e in entran.items():
    s = solic.get(c, 0)
    filas.append((c, e, s, s / e * 100 if e else 0))
for c, e, s, cv in sorted(filas, key=lambda x: -x[1])[:20]:
    print("%-26s %9s %9s %7.1f%% %6.1f%% %6.1f%%" % (
        c[:26], format(e, ","), format(s, ","), cv, e / tot_e * 100,
        s / tot_s * 100 if tot_s else 0))

print()
print("=" * 74)
print("DONDE CONVIERTE MEJOR QUE EL PROMEDIO  (minimo 150 entradas)")
print("=" * 74)
prom = tot_s / tot_e * 100
mejores = [x for x in filas if x[1] >= 150 and x[3] > prom]
print("%-26s %9s %9s %8s  %s" % ("ciudad", "entran", "solicit.", "conv", "vs promedio"))
for c, e, s, cv in sorted(mejores, key=lambda x: -x[3])[:14]:
    print("%-26s %9s %9s %7.1f%%  %+.0f%%" % (
        c[:26], format(e, ","), format(s, ","), cv, (cv / prom - 1) * 100))

print()
print("=" * 74)
print("DONDE CONVIERTE PEOR  (minimo 150 entradas)")
print("=" * 74)
peores = [x for x in filas if x[1] >= 150 and x[3] < prom]
for c, e, s, cv in sorted(peores, key=lambda x: x[3])[:10]:
    print("%-26s %9s %9s %7.1f%%  %+.0f%%" % (
        c[:26], format(e, ","), format(s, ","), cv, (cv / prom - 1) * 100))

print()
print("=" * 74)
print("CONCENTRACION")
print("=" * 74)
orden = sorted(filas, key=lambda x: -x[2])
acum = 0
for i, (c, e, s, cv) in enumerate(orden, 1):
    acum += s
    if i in (1, 3, 5, 10, 20):
        print("  las %2d ciudades con mas solicitudes concentran %5.1f%% del total"
              % (i, acum / tot_s * 100))
print("  ciudades con al menos una solicitud: %d"
      % sum(1 for x in filas if x[2] > 0))
