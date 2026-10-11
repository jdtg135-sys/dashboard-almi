# -*- coding: utf-8 -*-
import os
import sys, os
# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE); os.chdir(BASE)
os.environ["ALMI_COTIZADOR"] = "nuevo"
import actualizar_dashboard as D
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

cli = BetaAnalyticsDataClient(credentials=D.get_credentials())
SINCE, UNTIL = sys.argv[1], sys.argv[2]
PASOS = [("company_selected","1 empresa"),("calculate_credit_clicked","2 cotiza"),
         ("loan_quote_calculated","3 calculada"),("pre_approval_accepted","4 preaprob"),
         ("personal_info_submitted","5 datos"),("bank_info_submitted","6 banco"),
         ("loan_request_created","7 SOLICITUD")]

print(f"=== GA4 embudo (usuarios unicos) {SINCE} a {UNTIL} ===")
base = None
for ev, lab in PASOS:
    r = cli.run_report(RunReportRequest(
        property=f"properties/{D.PROPERTY_ID}", metrics=[Metric(name="activeUsers")],
        dimensions=[Dimension(name="eventName")],
        date_ranges=[DateRange(start_date=SINCE, end_date=UNTIL)],
        dimension_filter=D.FilterExpression(filter=D.Filter(
            field_name="eventName", string_filter=D.Filter.StringFilter(value=ev)))))
    v = int(r.rows[0].metric_values[0].value) if r.rows else 0
    base = base or v
    print(f"  {lab:<12} {v:>7,}  ({v/base*100:>5.1f}%)")

print(f"\n=== Solicitudes por dia ===")
r = cli.run_report(RunReportRequest(
    property=f"properties/{D.PROPERTY_ID}", metrics=[Metric(name="activeUsers")],
    dimensions=[Dimension(name="date"), Dimension(name="eventName")],
    date_ranges=[DateRange(start_date=SINCE, end_date=UNTIL)],
    dimension_filter=D.FilterExpression(filter=D.Filter(
        field_name="eventName", in_list_filter=D.Filter.InListFilter(
            values=["company_selected","loan_request_created"])))))
dd = {}
for row in r.rows:
    d, e = row.dimension_values[0].value, row.dimension_values[1].value
    dd.setdefault(d, {})[e] = int(row.metric_values[0].value)
for d in sorted(dd):
    a = dd[d].get("company_selected", 0); b = dd[d].get("loan_request_created", 0)
    print(f"  {d}  entran {a:>5,} | solicitudes {b:>4,} | conversion {(b/a*100 if a else 0):>5.1f}%")
