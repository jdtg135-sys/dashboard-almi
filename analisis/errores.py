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
ERRS = ["loan_request_error","loan_quote_error","otp_failed",
        "duplicate_phone_detected","duplicate_email_detected","duplicate_document_detected"]
CANDS = ["customEvent:error_message","customEvent:error_code","customEvent:error_type",
         "customEvent:message","customEvent:reason","customEvent:step","customEvent:field",
         "customEvent:form_step","customEvent:error"]
for dim in CANDS:
    try:
        r = cli.run_report(RunReportRequest(
            property=f"properties/{D.PROPERTY_ID}",
            dimensions=[Dimension(name="eventName"), Dimension(name=dim)],
            metrics=[Metric(name="eventCount")], date_ranges=DR,
            dimension_filter=FilterExpression(filter=Filter(field_name="eventName",
                in_list_filter=Filter.InListFilter(values=ERRS))),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventCount"), desc=True)],
            limit=40))
    except Exception as e:
        print(f"-- {dim}: NO EXISTE"); continue
    vals = [(x.dimension_values[0].value, x.dimension_values[1].value,
             int(x.metric_values[0].value)) for x in r.rows]
    utiles = [v for v in vals if v[1] not in ("(not set)", "", "(not provided)")]
    print(f"-- {dim}: {len(r.rows)} filas, {len(utiles)} con valor")
    for ev, v, n in vals[:12]:
        print(f"     {ev:<28} {v[:52]:<54} {n:>6,}")
