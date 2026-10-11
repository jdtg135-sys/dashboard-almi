# -*- coding: utf-8 -*-
"""Solicitudes diarias: cotizador anterior (ago-sep) vs nuevo (oct).

Se comparan usuarios unicos POR DIA en los dos, que es la unica base valida:
el evento final cambio de nombre pero significa lo mismo, y los totales
mensuales de usuarios unicos no se pueden dividir entre 30 porque estan
deduplicados por rango.
"""
import os
import sys, os, statistics
# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE); os.chdir(BASE)
import actualizar_dashboard as D
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (DateRange, Dimension, Metric,
    RunReportRequest, FilterExpression, Filter)
cli = BetaAnalyticsDataClient(credentials=D.get_credentials())

def diario(prop, evento, desde, hasta):
    r = cli.run_report(RunReportRequest(
        property=f"properties/{prop}", metrics=[Metric(name="activeUsers")],
        dimensions=[Dimension(name="date")],
        date_ranges=[DateRange(start_date=desde, end_date=hasta)],
        dimension_filter=FilterExpression(filter=Filter(
            field_name="eventName", string_filter=Filter.StringFilter(value=evento)))))
    return {x.dimension_values[0].value: int(x.metric_values[0].value) for x in r.rows}

VIEJA, NUEVA = "522022877", "554405139"
tramos = [
    ("Agosto completo",        VIEJA, "purchase",             "2026-08-01", "2026-08-31"),
    ("Septiembre 1 al 15",     VIEJA, "purchase",             "2026-09-01", "2026-09-15"),
    ("Septiembre 16 al 30",    VIEJA, "purchase",             "2026-09-16", "2026-09-30"),
    ("Octubre 1 al 7",         NUEVA, "loan_request_created", "2026-10-01", "2026-10-07"),
]
print(f"{'tramo':<24} {'dias':>5} {'total':>8} {'media':>8} {'mediana':>8} {'min':>5} {'max':>5}")
for nombre, prop, ev, d1, d2 in tramos:
    v = list(diario(prop, ev, d1, d2).values())
    print(f"{nombre:<24} {len(v):>5} {sum(v):>8,} {statistics.mean(v):>8,.0f} "
          f"{statistics.median(v):>8,.0f} {min(v):>5} {max(v):>5}")

print("\n--- sesiones diarias, para saber si es trafico o conversion ---")
def ses(prop, d1, d2):
    r = cli.run_report(RunReportRequest(
        property=f"properties/{prop}", metrics=[Metric(name="sessions")],
        dimensions=[Dimension(name="date")],
        date_ranges=[DateRange(start_date=d1, end_date=d2)]))
    return [int(x.metric_values[0].value) for x in r.rows]
for nombre, prop, ev, d1, d2 in tramos:
    v = ses(prop, d1, d2)
    print(f"{nombre:<24} sesiones/dia media {statistics.mean(v):>8,.0f}")
