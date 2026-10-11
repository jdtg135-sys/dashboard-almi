# -*- coding: utf-8 -*-
import os
import sys, os
# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE); os.chdir(BASE)
os.environ["ALMI_COTIZADOR"] = "nuevo"
import actualizar_dashboard as D
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest, OrderBy

cli = BetaAnalyticsDataClient(credentials=D.get_credentials())
SINCE, UNTIL = sys.argv[1], sys.argv[2]
r = cli.run_report(RunReportRequest(
    property=f"properties/{D.PROPERTY_ID}",
    metrics=[Metric(name="eventCount"), Metric(name="activeUsers")],
    dimensions=[Dimension(name="eventName")],
    date_ranges=[DateRange(start_date=SINCE, end_date=UNTIL)],
    order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventCount"), desc=True)],
    limit=200))
print(f"=== Todos los eventos {SINCE} a {UNTIL} ===")
print(f"  {'evento':<42} {'eventos':>9} {'usuarios':>9}")
for row in r.rows:
    print(f"  {row.dimension_values[0].value:<42} "
          f"{int(row.metric_values[0].value):>9,} {int(row.metric_values[1].value):>9,}")
