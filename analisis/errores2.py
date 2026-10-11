# -*- coding: utf-8 -*-
import os
import sys, os
# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE); os.chdir(BASE)
os.environ["ALMI_COTIZADOR"] = "nuevo"
import actualizar_dashboard as D
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (DateRange, Dimension, Metric,
    RunReportRequest, OrderBy, FilterExpression, Filter)
cli = BetaAnalyticsDataClient(credentials=D.get_credentials())
DR = [DateRange(start_date="2026-10-01", end_date="2026-10-07")]
def rep(dims, metrics, evs=None, limit=100, order=None):
    f = None
    if evs: f = FilterExpression(filter=Filter(field_name="eventName",
            in_list_filter=Filter.InListFilter(values=evs)))
    return cli.run_report(RunReportRequest(property=f"properties/{D.PROPERTY_ID}",
        dimensions=[Dimension(name=d) for d in dims],
        metrics=[Metric(name=m) for m in metrics], date_ranges=DR,
        dimension_filter=f, limit=limit,
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order), desc=True)] if order else None))

ERRS = ["loan_quote_error","otp_failed","loan_request_error",
        "duplicate_phone_detected","duplicate_email_detected","duplicate_document_detected"]
print("=== Eventos de error: usuarios unicos y mensaje (1 al 7 de oct) ===")
r = rep(["eventName"], ["eventCount","activeUsers"], ERRS, order="eventCount")
tot = {}
for x in r.rows:
    tot[x.dimension_values[0].value] = (int(x.metric_values[0].value), int(x.metric_values[1].value))
for e in ERRS:
    c,u = tot.get(e,(0,0)); print(f"  {e:<30} {c:>6,} eventos | {u:>5,} usuarios")

print("\n=== Texto del error ===")
for dim in ("customEvent:error","customEvent:reason"):
    r = rep(["eventName", dim], ["eventCount","activeUsers"], ERRS, order="eventCount")
    for x in r.rows:
        ev, v = x.dimension_values[0].value, x.dimension_values[1].value
        if v in ("(not set)",""): continue
        print(f"  [{dim.split(':')[1]}] {ev:<24} {v[:46]:<48} "
              f"{int(x.metric_values[0].value):>5,} ev | {int(x.metric_values[1].value):>4,} usr")

print("\n=== Por dia (usuarios con error) ===")
r = rep(["date","eventName"], ["activeUsers"], ERRS, limit=500)
dd = {}
for x in r.rows:
    dd.setdefault(x.dimension_values[0].value, {})[x.dimension_values[1].value] = int(x.metric_values[0].value)
cols = ["loan_quote_error","otp_failed","loan_request_error"]
print("  fecha      cotiza  otp  solicitud")
for d in sorted(dd):
    print(f"  {d}   " + "  ".join(f"{dd[d].get(c,0):>5}" for c in cols))
