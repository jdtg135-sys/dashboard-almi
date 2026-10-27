# -*- coding: utf-8 -*-
import sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE); os.chdir(BASE)
os.environ["ALMI_COTIZADOR"] = "nuevo"
import actualizar_dashboard as D
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (DateRange, Dimension, Metric,
    RunReportRequest, FilterExpression, Filter, OrderBy)
cli = BetaAnalyticsDataClient(credentials=D.get_credentials())
P = f"properties/{D.PROPERTY_ID}"
DR = [DateRange(start_date="2026-10-24", end_date="2026-10-26")]

print("=== loan_amount (metrica) por evento, 24-26 oct ===")
r = cli.run_report(RunReportRequest(property=P,
    dimensions=[Dimension(name="eventName")],
    metrics=[Metric(name="eventCount"), Metric(name="customEvent:loan_amount")],
    date_ranges=DR,
    order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventCount"), desc=True)],
    limit=60))
for x in r.rows:
    ev = x.dimension_values[0].value
    n = int(x.metric_values[0].value)
    v = float(x.metric_values[1].value)/1000.0
    if v > 0 or ev.startswith("loan") or ev.startswith("otp"):
        print(f"  {ev:<34} {n:>7,}  monto {v:>18,.0f}  prom {v/n if n else 0:>14,.0f}")

print()
print("=== parametro 'value' que recibe GA4 en loan_request_created ===")
for met in ["eventValue", "totalRevenue", "purchaseRevenue"]:
    try:
        r = cli.run_report(RunReportRequest(property=P,
            dimensions=[Dimension(name="eventName")],
            metrics=[Metric(name="eventCount"), Metric(name=met)],
            date_ranges=DR,
            dimension_filter=FilterExpression(filter=Filter(field_name="eventName",
                in_list_filter=Filter.InListFilter(values=["loan_request_created","loan_request_submitted"]))),
            limit=10))
        for x in r.rows:
            print(f"  {met:<16} {x.dimension_values[0].value:<26} n={int(x.metric_values[0].value):>6,} {met}={float(x.metric_values[1].value):,.2f}")
    except Exception as e:
        print(f"  {met}: {str(e)[:90]}")
