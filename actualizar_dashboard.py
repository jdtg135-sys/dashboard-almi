"""
Actualizador automatico del Dashboard ALMI
--------------------------------------------
Conecta con la Google Analytics Data API (GA4) usando tu cuenta de Google
(OAuth), trae los datos mas recientes de la propiedad de ALMI Financiera
(522022877) y actualiza los numeros del archivo Dashboard_ALMI.html.

Como usarlo:
  1. Doble clic en "ejecutar_actualizacion.bat"
     (o ejecutar: python actualizar_dashboard.py)
  2. La primera vez se abrira el navegador pidiendo iniciar sesion con
     Google. Usa la cuenta que tiene acceso a Analytics de
     almifinanciera.com. Luego queda guardado en token.json y no
     volvera a pedirlo.
  3. El script reescribe Dashboard_ALMI.html con los datos actualizados.
"""

import os
import re
import json
import datetime
import calendar

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest, OrderBy,
    FilterExpression, Filter,
)
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "oauth_credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
DASHBOARD_FILE = os.path.join(BASE_DIR, "Dashboard_ALMI.html")
ADS_DATA_FILE = os.path.join(BASE_DIR, "ads_data.json")

PROPERTY_ID = "522022877"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

# Rango de fechas a consultar (ajustar segun necesidad)
DATE_RANGE = DateRange(start_date="7daysAgo", end_date="today")
PREV_DATE_RANGE = DateRange(start_date="14daysAgo", end_date="8daysAgo")

MESES_ES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

# Eventos del cotizador que conforman el embudo (en orden)
FUNNEL_EVENTS = [
    ("1. Tipo de trabajador",   "worker_classification_selected"),
    ("2. Datos de empresa",     "company_selected"),
    ("3. Cotizacion calculada", "calculate_credit_clicked"),
    ("4. Pre aprobacion",       "pre_approval_accepted"),
    ("5. Terminos aceptados",   "terms_accepted"),
    ("6. Solicitud iniciada",   "loan_request_initiated"),
    ("7. Solicitud enviada",    "purchase"),
]

# Eventos extra para los KPIs / chart
EXTRA_EVENTS = [
    "form_validation_error",
    "loan_request_success",
    "loan_request_failure",
]

# Eventos para el grafico "Eventos por frecuencia" (nombre GA4, etiqueta amigable)
CHART_EVENTS = [
    ("worker_classification_selected", "Tipo de trabajador"),
    ("company_selected", "Datos de empresa"),
    ("calculate_credit_clicked",       "Calcular credito"),
    ("loan_quote_calculated",          "Cotizacion calculada"),
    ("whatsapp_support_clicked",       "Contacto WhatsApp"),
    ("pre_approval_accepted",          "Pre-aprobacion"),
    ("purchase",                       "Solicitud enviada"),
    ("loan_request_initiated",         "Solicitud iniciada"),
    ("form_validation_error",          "Error formulario"),
]


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def fetch_users_for_event(client, event_names, date_range=DATE_RANGE):
    """Devuelve activeUsers que dispararon CUALQUIERA de los eventos dados (union)."""
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        metrics=[Metric(name="activeUsers")],
        date_ranges=[date_range],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                in_list_filter=Filter.InListFilter(values=list(event_names)),
            )
        ),
    )
    response = client.run_report(request)
    if response.rows:
        return int(response.rows[0].metric_values[0].value)
    return 0


def fetch_funnel_users(client, funnel_events, date_range=DATE_RANGE):
    """Devuelve lista de activeUsers por etapa del funnel, monotonamente decreciente
    (cada etapa se limita al minimo entre su propio valor y el de la etapa anterior,
    ya que un funnel lineal no puede crecer)."""
    raw = []
    for label, event in funnel_events:
        if label.startswith("2."):
            # Paso 2 (Datos de empresa): "company_selected" es el evento correcto pero
            # se implemento recientemente; se incluye tambien "calculate_credit_clicked"
            # (usado como proxy temporal) para no perder usuarios que ya pasaron por ahi.
            val = fetch_users_for_event(client, [event, "calculate_credit_clicked"], date_range)
        else:
            val = fetch_users_for_event(client, [event], date_range)
        raw.append(val)

    # Solo se limitan los pasos 2 y 3 (problema conocido: calculate_credit_clicked
    # se dispara mas veces que usuarios reales que seleccionan empresa). Los pasos
    # 4-7 se dejan con su valor real, aunque algun paso recien instrumentado
    # (ej. terms_accepted) pueda tener un conteo temporalmente bajo por ser
    # implementacion reciente con datos de pocos dias.
    capped = list(raw)
    for i in (1, 2):
        if i < len(capped):
            capped[i] = min(capped[i], capped[i - 1])
    return capped


def fetch_event_counts(client, event_names, date_range=DATE_RANGE):
    """Devuelve un dict {event_name: total_count} para los eventos dados."""
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="eventName")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[date_range],
    )
    response = client.run_report(request)
    counts = {row.dimension_values[0].value: int(row.metric_values[0].value) for row in response.rows}
    return {name: counts.get(name, 0) for name in event_names}


def fetch_error_breakdown(client, date_range=DATE_RANGE, limit=8,
                           event_names=("form_validation_error", "loan_request_failure")):
    """Devuelve lista [(mensaje_error, conteo), ...] ordenada de mayor a menor."""
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="customEvent:error_message")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[date_range],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                in_list_filter=Filter.InListFilter(values=list(event_names)),
            )
        ),
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventCount"), desc=True)],
        limit=limit,
    )
    response = client.run_report(request)
    result = []
    for row in response.rows:
        msg = row.dimension_values[0].value or "(sin especificar)"
        count = int(row.metric_values[0].value)
        result.append((msg, count))
    return result


def fetch_sessions(client, date_range=DATE_RANGE):
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        metrics=[Metric(name="sessions")],
        date_ranges=[date_range],
    )
    response = client.run_report(request)
    if response.rows:
        return int(response.rows[0].metric_values[0].value)
    return 0


def fetch_daily_errors(client, date_range):
    """Devuelve lista [(fecha 'YYYY-MM-DD', conteo), ...] de form_validation_error por dia."""
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[date_range],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value="form_validation_error"),
            )
        ),
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
    )
    response = client.run_report(request)
    counts = {row.dimension_values[0].value: int(row.metric_values[0].value) for row in response.rows}

    result = []
    start = date_range.start_date
    end = date_range.end_date
    cur = datetime.datetime.strptime(start, "%Y-%m-%d").date()
    last = datetime.datetime.strptime(end, "%Y-%m-%d").date()
    while cur <= last:
        key = cur.strftime("%Y%m%d")
        result.append((cur.strftime("%Y-%m-%d"), counts.get(key, 0)))
        cur += datetime.timedelta(days=1)
    return result


def fmt_money(v):
    return f"${v:,.0f} COP".replace(",", ".")


def fmt_num(v):
    return f"{v:,.0f}".replace(",", ".")


def fmt_pct_change(curr, prev):
    """Devuelve (texto, clase_css) para la variacion porcentual curr vs prev."""
    if prev == 0:
        if curr == 0:
            return "0%", "delta-neutral"
        return "+100%", "delta-up"
    pct = round((curr - prev) / prev * 100, 1)
    if pct > 0:
        return f"+{pct}%", "delta-up"
    if pct < 0:
        return f"{pct}%", "delta-down"
    return "0%", "delta-neutral"


def comp_row_simple_global(label, curr, prev, invertir=False, formatter=fmt_num):
    txt, css = fmt_pct_change(curr, prev)
    if invertir:
        css = {"delta-up": "delta-down", "delta-down": "delta-up"}.get(css, css)
    return (
        "<tr>"
        f"<td>{label}</td>"
        f"<td>{formatter(curr)}</td>"
        f"<td>{formatter(prev)}</td>"
        f'<td class="{css}">{txt}</td>'
        "</tr>"
    )


def replace_stat(html, target_value, new_value):
    """Reemplaza data-target="X" -> data-target="new_value" (primera ocurrencia)."""
    pattern = r'data-target="' + re.escape(str(target_value)) + r'"'
    return re.sub(pattern, f'data-target="{new_value}"', html, count=1)


def main():
    creds = get_credentials()
    client = BetaAnalyticsDataClient(credentials=creds)

    sessions = fetch_sessions(client)

    all_event_names = [e for _, e in FUNNEL_EVENTS] + EXTRA_EVENTS + [e for e, _ in CHART_EVENTS]
    counts = fetch_event_counts(client, all_event_names)

    funnel_values = fetch_funnel_users(client, FUNNEL_EVENTS)
    solicitudes = funnel_values[-1]  # purchase / step 6
    pre_aprobaciones = counts["pre_approval_accepted"]
    errores_form = counts["form_validation_error"]
    fallos_solicitud = counts["loan_request_failure"]
    cotizador_starts = funnel_values[0]

    print("=== Datos obtenidos de GA4 (ultimos 7 dias) ===")
    print(f"Sesiones: {sessions}")
    for (label, event), val in zip(FUNNEL_EVENTS, funnel_values):
        print(f"{label} [{event}]: {val}")
    print(f"Errores formulario [form_validation_error]: {errores_form}")
    print(f"Fallos al enviar solicitud [loan_request_failure]: {fallos_solicitud}")

    error_breakdown = fetch_error_breakdown(client)
    print("\n=== Desglose de errores de formulario ===")
    for msg, cnt in error_breakdown:
        print(f"  - {msg}: {cnt}")

    # --- Datos de la semana anterior (para comparativa) ---
    sessions_prev = fetch_sessions(client, PREV_DATE_RANGE)
    counts_prev = fetch_event_counts(client, all_event_names, PREV_DATE_RANGE)
    funnel_values_prev = fetch_funnel_users(client, FUNNEL_EVENTS, PREV_DATE_RANGE)
    solicitudes_prev = funnel_values_prev[-1]
    pre_aprobaciones_prev = counts_prev["pre_approval_accepted"]
    errores_form_prev = counts_prev["form_validation_error"]
    cotizador_starts_prev = funnel_values_prev[0]

    print("\n=== Semana anterior (comparativa) ===")
    print(f"Sesiones: {sessions_prev}")
    print(f"Iniciaron cotizacion: {cotizador_starts_prev}")
    print(f"Solicitudes enviadas: {solicitudes_prev}")
    print(f"Pre-aprobaciones: {pre_aprobaciones_prev}")
    print(f"Errores formulario: {errores_form_prev}")

    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # --- KPI scorecards (idempotente: reemplaza por contexto, no por valor viejo) ---
    def replace_stat_by_label(html, label, new_value):
        pattern = (r'(data-target=")\d+(">0</div>\s*<div class="stat-label">'
                   + re.escape(label) + r')')
        return re.sub(pattern, rf'\g<1>{new_value}\g<2>', html, count=1)

    html = replace_stat_by_label(html, "Sesiones", sessions)
    html = replace_stat_by_label(html, "Iniciaron cotizacion", cotizador_starts)
    html = replace_stat_by_label(html, "Solicitudes enviadas", solicitudes)
    html = replace_stat_by_label(html, "Pre-aprobaciones", pre_aprobaciones)
    html = replace_stat_by_label(html, "Errores formulario", errores_form)

    # Conversion % de sesiones que inician cotizacion
    pct_inicio = round(cotizador_starts / sessions * 100, 1) if sessions else 0
    pct_conv = round(solicitudes / sessions * 100, 1) if sessions else 0
    html = re.sub(r'\d+(\.\d+)?% de sesiones', f'{pct_inicio}% de sesiones', html, count=1)
    html = re.sub(r'\d+(\.\d+)?% tasa conversion', f'{pct_conv}% tasa conversion', html, count=1)

    # Frase de cierre: "Teniamos X sesiones..."
    html = re.sub(r'(Teniamos )\d+( sesiones y no sabiamos)', rf'\g<1>{sessions}\g<2>', html, count=1)

    # --- Funnel stages ---
    base = funnel_values[0] if funnel_values[0] else 1
    for i, (label, event) in enumerate(FUNNEL_EVENTS):
        val = funnel_values[i]
        pct = round(val / base * 100, 1)
        bar_pct = min(pct, 100.0)

        # f-value (numero del paso) - reemplazar el bloque de esa etapa
        stage_pattern = re.compile(
            r'(<div class="f-label">' + re.escape(label) + r'</div>.*?data-pct=")[\d.]+("[^>]*></div></div>\s*<div class="f-value">)\d+(</div>\s*<div class="f-rate">)[\d.]+%(</div>)',
            re.DOTALL,
        )
        html = stage_pattern.sub(
            lambda m, bar_pct=bar_pct, pct=pct, val=val: f'{m.group(1)}{bar_pct}{m.group(2)}{val}{m.group(3)}{pct}%{m.group(4)}',
            html,
        )

    # Abandono entre etapas (funnel-connector)
    for i in range(len(funnel_values) - 1):
        a, b = funnel_values[i], funnel_values[i + 1]
        drop_users = a - b
        drop_pct = round(drop_users / a * 100, 1) if a else 0
        drop_pct_str = str(int(drop_pct)) if drop_pct == int(drop_pct) else str(drop_pct)
        connector_pattern = re.compile(
            r'(<div class="f-label">' + re.escape(FUNNEL_EVENTS[i][0]) + r'</div>.*?</div>\s*'
            r'<div class="funnel-connector">\s*<div class="drop-label">↓ abandono )-?[\d.]+%( — )-?\d+( usuarios</div>)',
            re.DOTALL,
        )
        html = connector_pattern.sub(
            lambda m, p=drop_pct_str, u=drop_users: f'{m.group(1)}{p}%{m.group(2)}{u}{m.group(3)}',
            html,
        )

    # Conversion total (paso 1 -> paso 6)
    conv_total = round(funnel_values[-1] / base * 100, 1) if base else 0
    html = re.sub(r'(<div class="fsumm-num">)[\d.]+%(</div>\s*<div class="fsumm-label">Conversion total)', rf'\g<1>{conv_total}%\g<2>', html)

    # Errores de formulario (resumen del funnel)
    html = re.sub(
        r'(<div class="fsumm-num" style="color:var\(--amber\)">)\d+(</div>\s*<div class="fsumm-label">Errores de formulario)',
        rf'\g<1>{errores_form}\g<2>',
        html,
    )

    html = re.sub(
        r'(<div class="fsumm-num" style="color:var\(--red\)">)\d+(</div>\s*<div class="fsumm-label">Fallos al enviar solicitud)',
        rf'\g<1>{fallos_solicitud}\g<2>',
        html,
    )

    # Desglose de errores de formulario por tipo
    if error_breakdown:
        total_err = sum(c for _, c in error_breakdown) or 1
        rows_html = []
        for msg, cnt in error_breakdown:
            pct = round(cnt / total_err * 100, 1)
            rows_html.append(
                "<tr>"
                f"<td>{msg}</td>"
                f"<td>{fmt_num(cnt)}</td>"
                f"<td>{pct}%</td>"
                "</tr>"
            )
        new_error_rows = "\n          ".join(rows_html)
    else:
        new_error_rows = '<tr><td colspan="3">Sin errores registrados en el periodo</td></tr>'

    error_table_pattern = re.compile(
        r'(<!-- ERROR_BREAKDOWN_START -->)(?:(?!<!-- ERROR_BREAKDOWN_END -->).)*(<!-- ERROR_BREAKDOWN_END -->)',
        re.DOTALL,
    )
    html = error_table_pattern.sub(lambda m: m.group(1) + "\n          " + new_error_rows + "\n          " + m.group(2), html, count=1)

    # --- Insights dinamicos ---
    def replace_insight(html, n, tag, h3, p):
        pattern = re.compile(
            r'(<!-- INSIGHT_' + str(n) + r'_START -->\s*<div class="insight reveal">\s*'
            r'<div class="insight-tag">)[^<]*(</div>\s*<h3>)(?:(?!</h3>).)*(</h3>\s*<p>)(?:(?!</p>).)*(</p>)',
            re.DOTALL,
        )
        return pattern.sub(lambda m: m.group(1) + tag + m.group(2) + h3 + m.group(3) + p + m.group(4), html, count=1)

    # Insight 1: mayor caida del funnel (entre dos pasos consecutivos)
    drops = []
    for i in range(len(funnel_values) - 1):
        a, b = funnel_values[i], funnel_values[i + 1]
        if a > 0:
            drops.append((round((a - b) / a * 100, 1), i))
    if drops:
        drop_pct, idx = max(drops)
        label_a = FUNNEL_EVENTS[idx][0].split(". ", 1)[1]
        label_b = FUNNEL_EVENTS[idx + 1][0].split(". ", 1)[1]
        a, b = funnel_values[idx], funnel_values[idx + 1]
        html = replace_insight(
            html, 1, "Friccion critica",
            f'El <em>{drop_pct}%</em> abandona entre &quot;{label_a}&quot; y &quot;{label_b}&quot;',
            f'De {a} usuarios en el paso &quot;{label_a}&quot;, solo {b} llegan a &quot;{label_b}&quot; '
            f'({round(b / a * 100, 1) if a else 0}% de continuidad). Este es el mayor punto de fuga del '
            f'funnel en el periodo medido — superar este paso deberia ser la prioridad de optimizacion '
            f'numero 1.'
        )

    # Insight 2: oportunidad de recuperacion (pre-aprobados que no enviaron solicitud)
    recuperables = max(pre_aprobaciones - solicitudes, 0)
    html = replace_insight(
        html, 2, "Oportunidad de recuperacion",
        f'<em>{recuperables} usuarios</em> llegaron a pre-aprobacion pero no enviaron',
        f'{pre_aprobaciones} pre-aprobaciones vs {solicitudes} solicitudes enviadas = {recuperables} usuarios '
        f'que recibieron luz verde pero no completaron. Son el segmento de mayor intencion de compra '
        f'disponible. Una campana de retargeting especifica para este segmento puede recuperar parte de '
        f'estas solicitudes en las proximas semanas.'
    )

    # Insight 3: tasa de conversion entre "Cotizacion calculada" -> "Pre aprobacion"
    idx_calc = next(i for i, (l, _) in enumerate(FUNNEL_EVENTS) if l.startswith("3."))
    calc_val = funnel_values[idx_calc]
    pre_val = funnel_values[idx_calc + 1]
    pct_calidad = round(pre_val / calc_val * 100, 1) if calc_val else 0
    html = replace_insight(
        html, 3, "Senal de calidad",
        f'El <em>{pct_calidad}%</em> de quienes calculan llegan a pre-aprobacion',
        f'Paso 3 -> Paso 4: {calc_val} cotizaciones calculadas, {pre_val} pre-aprobadas = {pct_calidad}% de '
        f'conversion. {"Esto indica que el perfil de usuario que llega a calcular es de alta calidad y cumple criterios de aprobacion. El problema no es la calidad del trafico sino la perdida en los pasos iniciales del funnel." if pct_calidad >= 40 else "Esta tasa es baja y sugiere revisar los criterios de pre-aprobacion o la calidad del trafico que llega a este paso."}'
    )

    # --- Grafico "Eventos por frecuencia" (DATA_EVENTS) ---
    chart_lines = []
    for name, label in CHART_EVENTS:
        chart_lines.append(
            f"  {{name:'{name}', label:'{label}', val:{counts.get(name, 0)}}}"
        )
    new_data_events = "var DATA_EVENTS = [\n" + ",\n".join(chart_lines) + "\n];"
    html = re.sub(r'var DATA_EVENTS = \[.*?\];', new_data_events, html, count=1, flags=re.DOTALL)

    # --- Inversion en Medios Pagados (datos manuales desde ads_data.json) ---
    if os.path.exists(ADS_DATA_FILE):
        with open(ADS_DATA_FILE, "r", encoding="utf-8") as f:
            ads = json.load(f)

        m = ads.get("meta_ads", {})
        g = ads.get("google_ads", {})

        def replace_ads_row(html, data_id, value, is_money=False):
            new_val = fmt_money(value) if is_money else fmt_num(value)
            pattern = (r'(<div class="ads-row" data-id="' + re.escape(data_id)
                       + r'"><span>[^<]*</span><div class="ads-row-val"><strong>)[^<]*(</strong>)')
            return re.sub(pattern, lambda mo: mo.group(1) + new_val + mo.group(2), html, count=1)

        def replace_ads_delta(html, delta_id, curr, prev, invertir=False):
            if prev is None:
                txt, css = "", "delta-neutral"
            else:
                txt, css = fmt_pct_change(curr, prev)
                if invertir:
                    css = {"delta-up": "delta-down", "delta-down": "delta-up"}.get(css, css)
                txt = f"{txt} vs sem. anterior"
            pattern = (r'<small class="ads-delta(?: delta-\w+)?" data-delta="'
                       + re.escape(delta_id) + r'">[^<]*</small>')
            replacement = f'<small class="ads-delta {css}" data-delta="{delta_id}">{txt}</small>'
            return re.sub(pattern, replacement, html, count=1)

        html = replace_ads_row(html, "meta-inversion", m.get("inversion", 0), is_money=True)
        html = replace_ads_row(html, "meta-impresiones", m.get("impresiones", 0))
        html = replace_ads_row(html, "meta-clics", m.get("clics", 0))
        html = replace_ads_row(html, "meta-resultados", m.get("resultados", 0))
        html = replace_ads_row(html, "meta-costo", m.get("costo_por_resultado", 0), is_money=True)

        html = replace_ads_row(html, "google-inversion", g.get("inversion", 0), is_money=True)
        html = replace_ads_row(html, "google-impresiones", g.get("impresiones", 0))
        html = replace_ads_row(html, "google-clics", g.get("clics", 0))
        html = replace_ads_row(html, "google-conversiones", g.get("conversiones", 0))
        html = replace_ads_row(html, "google-costo", g.get("costo_por_conversion", 0), is_money=True)

        # --- Variaciones vs semana anterior (badges en las tarjetas) ---
        html = replace_ads_delta(html, "meta-inversion-delta", m.get("inversion", 0), m.get("inversion_prev"), invertir=True)
        html = replace_ads_delta(html, "meta-impresiones-delta", m.get("impresiones", 0), m.get("impresiones_prev"))
        html = replace_ads_delta(html, "meta-clics-delta", m.get("clics", 0), m.get("clics_prev"))
        html = replace_ads_delta(html, "meta-resultados-delta", m.get("resultados", 0), m.get("resultados_prev"))
        html = replace_ads_delta(html, "meta-costo-delta", m.get("costo_por_resultado", 0), m.get("costo_por_resultado_prev"), invertir=True)

        html = replace_ads_delta(html, "google-inversion-delta", g.get("inversion", 0), g.get("inversion_prev"), invertir=True)
        html = replace_ads_delta(html, "google-impresiones-delta", g.get("impresiones", 0), g.get("impresiones_prev"))
        html = replace_ads_delta(html, "google-clics-delta", g.get("clics", 0), g.get("clics_prev"))
        html = replace_ads_delta(html, "google-conversiones-delta", g.get("conversiones", 0), g.get("conversiones_prev"))
        html = replace_ads_delta(html, "google-costo-delta", g.get("costo_por_conversion", 0), g.get("costo_por_conversion_prev"), invertir=True)

        # Tabla de campanas activas de Google Ads
        campanas = g.get("campanas", [])
        if campanas:
            rows_html = []
            for c in campanas:
                rows_html.append(
                    "<tr>"
                    f"<td>{c['nombre']}</td>"
                    f"<td>{c['estado']}</td>"
                    f"<td>{c['tipo']}</td>"
                    f"<td>{fmt_num(c['impresiones'])}</td>"
                    f"<td>{fmt_num(c['clics'])}</td>"
                    f"<td>{c['ctr']}%</td>"
                    f"<td>{fmt_money(c['cpc_promedio'])}</td>"
                    f"<td>{fmt_money(c['presupuesto_dia'])}</td>"
                    f"<td>{fmt_money(c['gasto'])}</td>"
                    f"<td>{fmt_num(c['conversiones'])}</td>"
                    f"<td>{fmt_money(c['costo_por_conversion'])}</td>"
                    "</tr>"
                )
                prev = c.get("prev")
                if prev:
                    rows_html.append(
                        '<tr class="campaign-prev-row">'
                        '<td>↳ Sem. anterior</td>'
                        "<td></td>"
                        "<td></td>"
                        f"<td>{fmt_num(prev['impresiones'])}</td>"
                        f"<td>{fmt_num(prev['clics'])}</td>"
                        f"<td>{prev['ctr']}%</td>"
                        f"<td>{fmt_money(prev['cpc_promedio'])}</td>"
                        "<td></td>"
                        f"<td>{fmt_money(prev['gasto'])}</td>"
                        f"<td>{fmt_num(prev['conversiones'])}</td>"
                        f"<td>{fmt_money(prev['costo_por_conversion'])}</td>"
                        "</tr>"
                    )
            new_rows = "\n          ".join(rows_html)
        else:
            new_rows = '<tr><td colspan="11">Sin campanas activas en el periodo</td></tr>'

        table_pattern = re.compile(
            r'(<!-- GOOGLE_ADS_CAMPAIGNS_START -->)(?:(?!<!-- GOOGLE_ADS_CAMPAIGNS_END -->).)*(<!-- GOOGLE_ADS_CAMPAIGNS_END -->)',
            re.DOTALL,
        )
        html = table_pattern.sub(lambda m: m.group(1) + "\n          " + new_rows + "\n          " + m.group(2), html, count=1)

        print("\nInversion en medios pagados actualizada desde ads_data.json")

        # --- Google Ads: comparativa mensual y acumulado 3 meses ---
        g_meses = g.get("meses", [])
        if len(g_meses) >= 2:
            gcm, gpm = g_meses[0], g_meses[1]
            g_monthly_rows = [
                comp_row_simple_global("Inversion", gcm["inversion"], gpm["inversion"], formatter=fmt_money),
                comp_row_simple_global("Impresiones", gcm["impresiones"], gpm["impresiones"]),
                comp_row_simple_global("Clics", gcm["clics"], gpm["clics"]),
                comp_row_simple_global("Conversiones", gcm["conversiones"], gpm["conversiones"]),
                comp_row_simple_global("Costo x conversion", gcm["costo_por_conversion"], gpm["costo_por_conversion"], invertir=True, formatter=fmt_money),
            ]
            new_g_monthly = "\n          ".join(g_monthly_rows)
        else:
            new_g_monthly = '<tr><td colspan="4">Sin datos suficientes</td></tr>'

        g_monthly_pattern = re.compile(
            r'(<!-- GOOGLE_ADS_MENSUAL_START -->)(?:(?!<!-- GOOGLE_ADS_MENSUAL_END -->).)*(<!-- GOOGLE_ADS_MENSUAL_END -->)',
            re.DOTALL,
        )
        html = g_monthly_pattern.sub(lambda mo: mo.group(1) + "\n          " + new_g_monthly + "\n          " + mo.group(2), html, count=1)

        if g_meses:
            g_3m_rows = []
            for md in g_meses:
                g_3m_rows.append(
                    "<tr>"
                    f"<td>{md['label']}</td>"
                    f"<td>{fmt_money(md['inversion'])}</td>"
                    f"<td>{fmt_num(md['impresiones'])}</td>"
                    f"<td>{fmt_num(md['clics'])}</td>"
                    f"<td>{fmt_num(md['conversiones'])}</td>"
                    f"<td>{fmt_money(md['costo_por_conversion'])}</td>"
                    "</tr>"
                )
            new_g_3m = "\n          ".join(g_3m_rows)
        else:
            new_g_3m = '<tr><td colspan="6">Sin datos suficientes</td></tr>'

        g_3m_pattern = re.compile(
            r'(<!-- GOOGLE_ADS_3M_START -->)(?:(?!<!-- GOOGLE_ADS_3M_END -->).)*(<!-- GOOGLE_ADS_3M_END -->)',
            re.DOTALL,
        )
        html = g_3m_pattern.sub(lambda mo: mo.group(1) + "\n          " + new_g_3m + "\n          " + mo.group(2), html, count=1)

        print("Comparativas mensuales de Google Ads actualizadas")

        # --- Meta Ads: tabla de campanas (ultimos 7 dias) ---
        m_campanas = m.get("campanas", [])
        if m_campanas:
            m_camp_rows = []
            for c in m_campanas:
                m_camp_rows.append(
                    "<tr>"
                    f"<td>{c['nombre']}</td>"
                    f"<td>{c['estado']}</td>"
                    f"<td>{fmt_num(c['impresiones'])}</td>"
                    f"<td>{fmt_num(c['clics'])}</td>"
                    f"<td>{c['ctr']}%</td>"
                    f"<td>{fmt_money(c['cpc_promedio'])}</td>"
                    f"<td>{fmt_money(c['presupuesto_dia'])}</td>"
                    f"<td>{fmt_money(c['gasto'])}</td>"
                    f"<td>{fmt_num(c['resultados'])}</td>"
                    f"<td>{fmt_money(c['costo_por_resultado'])}</td>"
                    "</tr>"
                )
                prev = c.get("prev")
                if prev:
                    m_camp_rows.append(
                        '<tr class="campaign-prev-row">'
                        '<td>↳ Sem. anterior</td>'
                        "<td></td>"
                        f"<td>{fmt_num(prev['impresiones'])}</td>"
                        f"<td>{fmt_num(prev['clics'])}</td>"
                        f"<td>{prev['ctr']}%</td>"
                        f"<td>{fmt_money(prev['cpc_promedio'])}</td>"
                        "<td></td>"
                        f"<td>{fmt_money(prev['gasto'])}</td>"
                        f"<td>{fmt_num(prev['resultados'])}</td>"
                        f"<td>{fmt_money(prev['costo_por_resultado'])}</td>"
                        "</tr>"
                    )
            new_m_camp = "\n          ".join(m_camp_rows)
        else:
            new_m_camp = '<tr><td colspan="10">Sin campanas con actividad en el periodo</td></tr>'

        m_camp_pattern = re.compile(
            r'(<!-- META_ADS_CAMPAIGNS_START -->)(?:(?!<!-- META_ADS_CAMPAIGNS_END -->).)*(<!-- META_ADS_CAMPAIGNS_END -->)',
            re.DOTALL,
        )
        html = m_camp_pattern.sub(lambda mo: mo.group(1) + "\n          " + new_m_camp + "\n          " + mo.group(2), html, count=1)

        # --- Meta Ads: comparativa mensual y acumulado 3 meses ---
        m_meses = m.get("meses", [])
        if len(m_meses) >= 2:
            mcm, mpm = m_meses[0], m_meses[1]
            m_monthly_rows = [
                comp_row_simple_global("Inversion", mcm["inversion"], mpm["inversion"], formatter=fmt_money),
                comp_row_simple_global("Impresiones", mcm["impresiones"], mpm["impresiones"]),
                comp_row_simple_global("Clics", mcm["clics"], mpm["clics"]),
                comp_row_simple_global("Resultados", mcm["resultados"], mpm["resultados"]),
                comp_row_simple_global("Costo x resultado", mcm["costo_por_resultado"], mpm["costo_por_resultado"], invertir=True, formatter=fmt_money),
            ]
            new_m_monthly = "\n          ".join(m_monthly_rows)
        else:
            new_m_monthly = '<tr><td colspan="4">Sin datos suficientes</td></tr>'

        m_monthly_pattern = re.compile(
            r'(<!-- META_ADS_MENSUAL_START -->)(?:(?!<!-- META_ADS_MENSUAL_END -->).)*(<!-- META_ADS_MENSUAL_END -->)',
            re.DOTALL,
        )
        html = m_monthly_pattern.sub(lambda mo: mo.group(1) + "\n          " + new_m_monthly + "\n          " + mo.group(2), html, count=1)

        if m_meses:
            m_3m_rows = []
            for md in m_meses:
                m_3m_rows.append(
                    "<tr>"
                    f"<td>{md['label']}</td>"
                    f"<td>{fmt_money(md['inversion'])}</td>"
                    f"<td>{fmt_num(md['impresiones'])}</td>"
                    f"<td>{fmt_num(md['clics'])}</td>"
                    f"<td>{fmt_num(md['resultados'])}</td>"
                    f"<td>{fmt_money(md['costo_por_resultado'])}</td>"
                    "</tr>"
                )
            new_m_3m = "\n          ".join(m_3m_rows)
        else:
            new_m_3m = '<tr><td colspan="6">Sin datos suficientes</td></tr>'

        m_3m_pattern = re.compile(
            r'(<!-- META_ADS_3M_START -->)(?:(?!<!-- META_ADS_3M_END -->).)*(<!-- META_ADS_3M_END -->)',
            re.DOTALL,
        )
        html = m_3m_pattern.sub(lambda mo: mo.group(1) + "\n          " + new_m_3m + "\n          " + mo.group(2), html, count=1)

        print("Comparativas mensuales de Meta Ads actualizadas")

        # --- Comparativa semana actual vs anterior ---
        def comparativa_row(label, curr, prev, invertir=False, formatter=fmt_num):
            if prev is None:
                txt, css = "—", "delta-neutral"
            else:
                txt, css = fmt_pct_change(curr, prev)
                if invertir:
                    css = {"delta-up": "delta-down", "delta-down": "delta-up"}.get(css, css)
            prev_txt = formatter(prev) if prev is not None else "—"
            return (
                "<tr>"
                f"<td>{label}</td>"
                f"<td>{formatter(curr)}</td>"
                f"<td>{prev_txt}</td>"
                f'<td class="{css}">{txt}</td>'
                "</tr>"
            )

        comp_rows = [
            comparativa_row("Sesiones", sessions, sessions_prev),
            comparativa_row("Iniciaron cotizacion", cotizador_starts, cotizador_starts_prev),
            comparativa_row("Solicitudes enviadas", solicitudes, solicitudes_prev),
            comparativa_row("Pre-aprobaciones", pre_aprobaciones, pre_aprobaciones_prev),
            comparativa_row("Errores formulario", errores_form, errores_form_prev, invertir=True),
            comparativa_row("Inversion Google Ads", g.get("inversion", 0), g.get("inversion_prev"), formatter=fmt_money),
            comparativa_row("Conversiones Google Ads", g.get("conversiones", 0), g.get("conversiones_prev")),
            comparativa_row("Inversion Meta Ads", m.get("inversion", 0), m.get("inversion_prev"), formatter=fmt_money),
        ]
        new_comp_rows = "\n          ".join(comp_rows)

        comp_pattern = re.compile(
            r'(<!-- COMPARATIVA_SEMANAL_START -->)(?:(?!<!-- COMPARATIVA_SEMANAL_END -->).)*(<!-- COMPARATIVA_SEMANAL_END -->)',
            re.DOTALL,
        )
        html = comp_pattern.sub(lambda mo: mo.group(1) + "\n          " + new_comp_rows + "\n          " + mo.group(2), html, count=1)

        print("Comparativa semanal actualizada")

    # --- Comparativas mensuales (mes calendario) ---
    def month_range(months_back):
        """Devuelve (inicio, fin, etiqueta) del mes calendario `months_back` meses atras (0 = mes actual)."""
        today = datetime.date.today()
        y, mo = today.year, today.month
        for _ in range(months_back):
            mo -= 1
            if mo == 0:
                mo, y = 12, y - 1
        start = datetime.date(y, mo, 1)
        if months_back == 0:
            end = today
        else:
            end = datetime.date(y, mo, calendar.monthrange(y, mo)[1])
        return start, end, f"{MESES_ES[mo - 1]} {y}"

    month_data = []
    for mb in range(3):
        m_start, m_end, m_label = month_range(mb)
        m_dr = DateRange(start_date=m_start.isoformat(), end_date=m_end.isoformat())
        m_sessions = fetch_sessions(client, m_dr)
        m_counts = fetch_event_counts(client, all_event_names, m_dr)
        month_data.append({
            "label": m_label,
            "sessions": m_sessions,
            "starts": m_counts[FUNNEL_EVENTS[0][1]],
            "solicitudes": m_counts[FUNNEL_EVENTS[-1][1]],
            "pre_aprob": m_counts["pre_approval_accepted"],
            "errores": m_counts["form_validation_error"],
        })

    print("\n=== Comparativa mensual (mes calendario) ===")
    for md in month_data:
        print(f"  {md['label']}: sesiones={md['sessions']}, inicios={md['starts']}, "
              f"solicitudes={md['solicitudes']}, preaprob={md['pre_aprob']}, errores={md['errores']}")

    cm, pm = month_data[0], month_data[1]
    comp_row_simple = comp_row_simple_global

    monthly_rows = [
        comp_row_simple("Sesiones", cm["sessions"], pm["sessions"]),
        comp_row_simple("Iniciaron cotizacion", cm["starts"], pm["starts"]),
        comp_row_simple("Solicitudes enviadas", cm["solicitudes"], pm["solicitudes"]),
        comp_row_simple("Pre-aprobaciones", cm["pre_aprob"], pm["pre_aprob"]),
        comp_row_simple("Errores formulario", cm["errores"], pm["errores"], invertir=True),
    ]
    new_monthly_rows = "\n          ".join(monthly_rows)

    monthly_pattern = re.compile(
        r'(<!-- COMPARATIVA_MENSUAL_START -->)(?:(?!<!-- COMPARATIVA_MENSUAL_END -->).)*(<!-- COMPARATIVA_MENSUAL_END -->)',
        re.DOTALL,
    )
    html = monthly_pattern.sub(lambda mo: mo.group(1) + "\n          " + new_monthly_rows + "\n          " + mo.group(2), html, count=1)

    # --- Tabla acumulada ultimos 3 meses ---
    acumulado_rows = []
    for md in month_data:
        acumulado_rows.append(
            "<tr>"
            f"<td>{md['label']}</td>"
            f"<td>{fmt_num(md['sessions'])}</td>"
            f"<td>{fmt_num(md['starts'])}</td>"
            f"<td>{fmt_num(md['solicitudes'])}</td>"
            f"<td>{fmt_num(md['pre_aprob'])}</td>"
            f"<td>{fmt_num(md['errores'])}</td>"
            "</tr>"
        )
    new_acumulado_rows = "\n          ".join(acumulado_rows)

    acumulado_pattern = re.compile(
        r'(<!-- ACUMULADO_3M_START -->)(?:(?!<!-- ACUMULADO_3M_END -->).)*(<!-- ACUMULADO_3M_END -->)',
        re.DOTALL,
    )
    html = acumulado_pattern.sub(lambda mo: mo.group(1) + "\n          " + new_acumulado_rows + "\n          " + mo.group(2), html, count=1)

    print("Comparativas mensuales actualizadas")

    # Fecha del periodo medido
    hoy = datetime.date.today()
    hace_7 = hoy - datetime.timedelta(days=7)

    def fmt_dia_mes(d):
        return f"{d.day} {MESES_ES[d.month - 1]}"

    # section-sub: "periodo 02 Jun - 09 Jun"
    nuevo_periodo = f"{hace_7.strftime('%d')} {MESES_ES[hace_7.month - 1]} - {hoy.strftime('%d')} {MESES_ES[hoy.month - 1]}"
    html = re.sub(r'periodo \d{1,2} \w{3} - \d{1,2} \w{3}', f'periodo {nuevo_periodo}', html)

    # hero-badge: "Periodo: <span>8 — 9 Jun 2026</span>"
    if hace_7.month == hoy.month:
        badge_periodo = f"{hace_7.day} — {fmt_dia_mes(hoy)} {hoy.year}"
    else:
        badge_periodo = f"{fmt_dia_mes(hace_7)} — {fmt_dia_mes(hoy)} {hoy.year}"
    html = re.sub(
        r'(Periodo: <span>)[^<]*(</span>)',
        rf'\g<1>{badge_periodo}\g<2>',
        html,
    )

    # Grafico de errores diarios: solo mes en curso (1 al dia actual)
    inicio_mes = hoy.replace(day=1)
    daily_errors = fetch_daily_errors(client, DateRange(
        start_date=inicio_mes.strftime("%Y-%m-%d"), end_date=hoy.strftime("%Y-%m-%d")
    ))
    items = [f"{{date:'{d}', val:{v}}}" for d, v in daily_errors]
    lines = []
    for i in range(0, len(items), 3):
        lines.append("  " + " ".join(x + "," if j != len(items) - 1 else x
                                       for j, x in enumerate(items[i:i + 3], start=i)))
    daily_errors_block = (
        "/* DAILY_ERRORS_START */\n"
        "var DATA_DAILY_ERRORS = [\n"
        + "\n".join(lines) + "\n"
        "];\n"
        "/* DAILY_ERRORS_END */"
    )
    html = re.sub(
        r"/\* DAILY_ERRORS_START \*/.*?/\* DAILY_ERRORS_END \*/",
        daily_errors_block,
        html,
        flags=re.S,
    )

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print("\nDashboard_ALMI.html actualizado correctamente.")


if __name__ == "__main__":
    main()
