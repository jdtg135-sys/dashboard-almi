# -*- coding: utf-8 -*-
import sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE); os.chdir(BASE)
os.environ["ALMI_COTIZADOR"] = "nuevo"
import actualizar_dashboard as D
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (DateRange, Dimension, Metric,
    RunReportRequest, FilterExpression, Filter)
from google.analytics.admin import AnalyticsAdminServiceClient
import ga4_admin_auth as A
cli = BetaAnalyticsDataClient(credentials=D.get_credentials())
P = f"properties/{D.PROPERTY_ID}"
DR = [DateRange(start_date="2026-10-24", end_date="2026-10-26")]
for par, ev in [("selected_amount","loan_quote_calculated"),
                ("max_approved","loan_quote_calculated"),
                ("new_amount","loan_amount_adjusted"),
                ("max_amount","loan_amount_adjusted")]:
    try:
        r = cli.run_report(RunReportRequest(property=P,
            dimensions=[Dimension(name="eventName")],
            metrics=[Metric(name="eventCount"), Metric(name=f"customEvent:{par}")],
            date_ranges=DR,
            dimension_filter=FilterExpression(filter=Filter(field_name="eventName",
                string_filter=Filter.StringFilter(value=ev))), limit=5))
        for x in r.rows:
            n=int(x.metric_values[0].value); v=float(x.metric_values[1].value)/1000.0
            print(f"  {par:<16} en {ev:<24} n={n:>6,}  total={v:>16,.0f}  prom={v/n if n else 0:>12,.0f}")
    except Exception as e:
        print(f"  {par}: {str(e)[:100]}")
