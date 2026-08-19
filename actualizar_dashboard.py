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
from datetime import timedelta
import calendar

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest, OrderBy,
    FilterExpression, Filter,
)
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "oauth_credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
DASHBOARD_FILE = os.path.join(BASE_DIR, "Dashboard_ALMI.html")
ADS_DATA_FILE = os.path.join(BASE_DIR, "ads_data.json")

PROPERTY_ID = "522022877"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

# Rango de fechas a consultar (ajustar segun necesidad)
#
# Las dos ventanas semanales tienen que medir la MISMA cantidad de dias, si no
# los porcentajes de variacion salen inflados. En GA4 "7daysAgo" a "today" son
# 8 dias (incluye hoy, que ademas esta incompleto) mientras la ventana previa
# eran 7: la comparativa semanal comparaba 8 contra 7. Ahora ambas son de 7
# dias completos, terminando ayer, igual que las de Meta y Google Ads.
DATE_RANGE = DateRange(start_date="7daysAgo", end_date="yesterday")
PREV_DATE_RANGE = DateRange(start_date="14daysAgo", end_date="8daysAgo")
ACCUM_DATE_RANGE = DateRange(start_date="2026-06-08", end_date="today")

MESES_ES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

# Eventos del cotizador que conforman el embudo (en orden)
FUNNEL_EVENTS = [
    ("1. Tipo de trabajador",   "worker_classification_selected"),
    ("2. Datos de empresa",     "company_selected"),
    ("3. Cotizacion calculada", "calculate_credit_clicked"),
    ("4. Terminos aceptados",   "terms_accepted"),
    ("5. Pre aprobacion",       "pre_approval_accepted"),
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
        refreshed = False
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                refreshed = True
            except RefreshError:
                # token revocado/expirado sin posibilidad de refresco: re-autorizar
                creds = None
        if not refreshed:
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


def aplicar_tope_monotono(valores):
    """Limita cada paso al minimo entre su valor y el del paso anterior.

    Antes el tope solo se aplicaba a los pasos 2 y 3, y los pasos 4-7 quedaban
    libres. Eso producia un embudo imposible: terms_accepted (15.803) salia por
    encima de calculate_credit_clicked (15.577) y el dashboard mostraba un
    "abandono de -1.5%", es decir mas gente aceptando terminos que calculando.

    La causa de fondo es que GA4 cuenta activeUsers por evento de forma
    independiente: no es un embudo secuencial real (no dice "usuarios que
    hicieron el paso 1 Y el paso 2"). Mientras se instrumenta un embudo
    secuencial de verdad, el tope evita mostrar un dato imposible.

    Vive en su propia funcion porque el embudo se calcula por dos caminos
    (fetch_funnel_users y fetch_funnel_users_fast) y si las reglas divergieran,
    el embudo estatico y el del filtro mostrarian numeros distintos.
    """
    capped = list(valores)
    for i in range(1, len(capped)):
        capped[i] = min(capped[i], capped[i - 1])
    return capped


def fetch_funnel_users(client, funnel_events, date_range=DATE_RANGE):
    """activeUsers por etapa del funnel, monotonamente decreciente.

    Delega en fetch_funnel_users_fast para que exista UNA sola forma de calcular
    el embudo.

    Antes esta funcion pedia cada evento por separado (una llamada por paso) y
    la del filtro los pedia con la dimension eventName (dos llamadas en total).
    Las dos consultas son validas, pero GA4 aproxima los conteos de usuarios
    unicos y cada camino daba un resultado ligeramente distinto: en el acumulado
    diferian 1-2 usuarios en los pasos 3, 4 y 5. Poco, pero suficiente para que
    el embudo estatico y el preset "Acumulado" no cuadraran entre si.
    """
    return fetch_funnel_users_fast(client, funnel_events, date_range)


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
                           event_names=("form_validation_error",)):
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


def fetch_users_by_event(client, event_names, date_range):
    """activeUsers por cada evento, en UNA sola llamada.

    Equivale a llamar fetch_users_for_event una vez por evento, pero pidiendo
    la dimension eventName. Se usa para armar los rangos del filtro sin
    disparar 7 llamadas por rango.
    """
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="eventName")],
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
    out = {row.dimension_values[0].value: int(row.metric_values[0].value)
           for row in response.rows}
    return {name: out.get(name, 0) for name in event_names}


def fetch_funnel_users_fast(client, funnel_events, date_range):
    """Igual que fetch_funnel_users pero con 2 llamadas en vez de 7.

    La union del paso 2 (company_selected + calculate_credit_clicked) necesita
    su propia llamada porque activeUsers deduplica: la union de dos eventos no
    es la suma de sus usuarios.
    """
    nombres = [ev for _, ev in funnel_events]
    por_evento = fetch_users_by_event(client, nombres, date_range)

    raw = []
    for label, event in funnel_events:
        if label.startswith("2."):
            raw.append(fetch_users_for_event(
                client, [event, "calculate_credit_clicked"], date_range))
        else:
            raw.append(por_evento.get(event, 0))

    return aplicar_tope_monotono(raw)


def fetch_error_breakdown_diario(client, date_range, limit=200,
                                 event_names=("form_validation_error",)):
    """Errores por (fecha, mensaje). eventCount es aditivo, asi que el navegador
    puede sumar cualquier subrango sin volver a consultar."""
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="date"),
                    Dimension(name="customEvent:error_message")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[date_range],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                in_list_filter=Filter.InListFilter(values=list(event_names)),
            )
        ),
        limit=100000,
    )
    response = client.run_report(request)
    filas = []
    for row in response.rows:
        f = row.dimension_values[0].value          # YYYYMMDD
        msg = row.dimension_values[1].value or "(sin especificar)"
        filas.append({
            "fecha": f"{f[0:4]}-{f[4:6]}-{f[6:8]}",
            "msg": msg,
            "n": int(row.metric_values[0].value),
        })
    return filas


def fetch_serie_diaria_eventos(client, date_range, event_names):
    """eventCount por (fecha, evento) para los graficos diarios y los KPIs
    aditivos. Una sola llamada cubre todo el historial."""
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="date"), Dimension(name="eventName")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[date_range],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                in_list_filter=Filter.InListFilter(values=list(event_names)),
            )
        ),
        limit=100000,
    )
    response = client.run_report(request)
    filas = []
    for row in response.rows:
        f = row.dimension_values[0].value
        filas.append({
            "fecha": f"{f[0:4]}-{f[4:6]}-{f[6:8]}",
            "ev": row.dimension_values[1].value,
            "n": int(row.metric_values[0].value),
        })
    return filas


def fetch_sesiones_diarias(client, date_range):
    """Sesiones por dia. sessions es practicamente aditiva (desvio medido
    < 1%), asi que sirve para recortar por rango en el navegador."""
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="sessions")],
        date_ranges=[date_range],
        limit=100000,
    )
    response = client.run_report(request)
    out = {}
    for row in response.rows:
        f = row.dimension_values[0].value
        out[f"{f[0:4]}-{f[4:6]}-{f[6:8]}"] = int(row.metric_values[0].value)
    return out


def rangos_preset(hoy, inicio_datos):
    """Define los rangos que ofrece el filtro.

    Se pre-descarga cada uno por separado en vez de sumar dias porque el embudo
    usa activeUsers, que esta deduplicada: sumar dias sobrecuenta (+16% medido
    a 30 dias). Con rangos fijos los usuarios unicos quedan exactos.
    """
    ayer = hoy - timedelta(days=1)
    presets = []

    for n in (7, 14, 30, 90):
        presets.append({
            "id": str(n),
            "label": f"{n} dias",
            "desde": (ayer - timedelta(days=n - 1)).isoformat(),
            "hasta": ayer.isoformat(),
        })

    ini_mes = hoy.replace(day=1)
    presets.append({
        "id": "mes",
        "label": "Mes actual",
        "desde": ini_mes.isoformat(),
        "hasta": hoy.isoformat(),
    })

    fin_mes_ant = ini_mes - timedelta(days=1)
    presets.append({
        "id": "mes-1",
        "label": "Mes anterior",
        "desde": fin_mes_ant.replace(day=1).isoformat(),
        "hasta": fin_mes_ant.isoformat(),
    })

    presets.append({
        "id": "acum",
        "label": "Acumulado",
        "desde": inicio_datos,
        "hasta": hoy.isoformat(),
    })

    # Un rango que empiece antes de que existieran los datos daria un total
    # incompleto leido como real.
    for p in presets:
        p["recortado"] = p["desde"] < inicio_datos
        if p["recortado"]:
            p["desde"] = inicio_datos
    return presets


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


def fetch_daily_errors(client, date_range, event_name="form_validation_error"):
    """Devuelve lista [(fecha 'YYYY-MM-DD', conteo), ...] del evento dado por dia."""
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[date_range],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value=event_name),
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


def construir_rangos(client, hoy, all_event_names):
    """Arma la estructura que consume el filtro global del dashboard.

    Estrategia mixta, decidida por como se comporta cada metrica en GA4:

      - activeUsers (embudo) NO es aditiva: esta deduplicada por rango, asi que
        sumar dias sobrecuenta (medido: +6.6% a 7 dias, +16.1% a 30). Por eso
        cada preset se descarga como su propio rango y queda exacto.

      - eventCount y sessions SI son aditivas (desvio medido 0.0% y -0.7%).
        Se bajan una sola vez como serie diaria y el navegador las recorta.
    """
    inicio_datos = ACCUM_DATE_RANGE.start_date
    presets = rangos_preset(hoy, inicio_datos)

    print("\n=== Descargando rangos del filtro global ===")
    datos = {}
    for p in presets:
        dr = DateRange(start_date=p["desde"], end_date=p["hasta"])
        embudo = fetch_funnel_users_fast(client, FUNNEL_EVENTS, dr)
        sesiones = fetch_sessions(client, dr)
        datos[p["id"]] = {
            "desde": p["desde"],
            "hasta": p["hasta"],
            "label": p["label"],
            "recortado": p["recortado"],
            "sesiones": sesiones,
            "embudo": embudo,
        }
        aviso = "  (recortado al inicio de datos)" if p["recortado"] else ""
        print(f"  {p['label']:<14} {p['desde']} -> {p['hasta']}  "
              f"sesiones={sesiones:>7,}  paso1={embudo[0]:>7,}  "
              f"paso7={embudo[-1]:>6,}{aviso}")

    rango_total = DateRange(start_date=inicio_datos, end_date=hoy.isoformat())
    print("  descargando series diarias (eventos, errores, sesiones)...")
    serie_eventos = fetch_serie_diaria_eventos(client, rango_total, all_event_names)
    serie_errores = fetch_error_breakdown_diario(
        client, rango_total, event_names=("form_validation_error",))
    serie_sesiones = fetch_sesiones_diarias(client, rango_total)
    print(f"  series: {len(serie_eventos)} filas evento-dia, "
          f"{len(serie_errores)} filas error-dia, {len(serie_sesiones)} dias de sesiones")

    return {
        "presets": [{"id": p["id"], "label": p["label"],
                     "desde": p["desde"], "hasta": p["hasta"]} for p in presets],
        "porRango": datos,
        "pasos": [label for label, _ in FUNNEL_EVENTS],
        "serieEventos": serie_eventos,
        "serieErrores": serie_errores,
        "serieSesiones": serie_sesiones,
        "inicioDatos": inicio_datos,
    }


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

    # Mismo rango que el contador "Errores de formulario" del resumen del embudo.
    # Antes el desglose salia a 7 dias (~2.809 errores) mientras el resumen mostraba
    # el acumulado (~20.236): el lector veia dos cifras que no cuadraban entre si.
    error_breakdown = fetch_error_breakdown(client, ACCUM_DATE_RANGE)
    print("\n=== Desglose de errores de formulario ===")
    for msg, cnt in error_breakdown:
        print(f"  - {msg}: {cnt}")

    # --- Acumulado desde implementacion (2026-06-08) ---
    sessions_accum = fetch_sessions(client, ACCUM_DATE_RANGE)
    counts_accum = fetch_event_counts(client, all_event_names, ACCUM_DATE_RANGE)
    funnel_accum = fetch_funnel_users(client, FUNNEL_EVENTS, ACCUM_DATE_RANGE)
    solicitudes_accum = funnel_accum[-1]
    pre_aprobaciones_accum = counts_accum["pre_approval_accepted"]
    errores_accum = counts_accum["form_validation_error"]
    cotizador_starts_accum = funnel_accum[0]

    print("\n=== Acumulado desde implementacion (2026-06-08) ===")
    print(f"Sesiones: {sessions_accum}")
    print(f"Iniciaron cotizacion: {cotizador_starts_accum}")
    print(f"Solicitudes enviadas: {solicitudes_accum}")
    print(f"Pre-aprobaciones: {pre_aprobaciones_accum}")
    print(f"Errores formulario: {errores_accum}")

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

    html = replace_stat_by_label(html, "Sesiones", sessions_accum)
    html = replace_stat_by_label(html, "Iniciaron cotizacion", cotizador_starts_accum)
    html = replace_stat_by_label(html, "Solicitudes enviadas", solicitudes_accum)
    html = replace_stat_by_label(html, "Pre-aprobaciones", pre_aprobaciones_accum)
    html = replace_stat_by_label(html, "Errores formulario", errores_accum)

    # Conversion % de sesiones que inician cotizacion (acumulado)
    pct_inicio = round(cotizador_starts_accum / sessions_accum * 100, 1) if sessions_accum else 0
    pct_conv = round(solicitudes_accum / sessions_accum * 100, 1) if sessions_accum else 0
    html = re.sub(r'\d+(\.\d+)?% de sesiones', f'{pct_inicio}% de sesiones', html, count=1)
    html = re.sub(r'\d+(\.\d+)?% tasa conversion', f'{pct_conv}% tasa conversion', html, count=1)

    # Frase de cierre. Antes solo se actualizaba el numero de sesiones y el
    # "Ahora sabemos que son X" quedaba fijo en 6, un valor viejo que no
    # correspondia a nada: con 12.730 sesiones las solicitudes eran 1.282.
    html = re.sub(r'(Teniamos )\d+( sesiones y no sabiamos)', rf'\g<1>{sessions}\g<2>', html, count=1)
    html = re.sub(r'(Ahora sabemos que son <em>)\d+(\.</em>)',
                  rf'\g<1>{funnel_values[-1]}\g<2>', html, count=1)
    html = re.sub(r'(<span id="closingFecha">)[^<]*(</span>)',
                  rf'\g<1>{MESES_ES[datetime.date.today().month - 1]} '
                  rf'{datetime.date.today().year}\g<2>', html, count=1)

    # --- Funnel stages (acumulado desde implementacion) ---
    base = funnel_accum[0] if funnel_accum[0] else 1
    for i, (label, event) in enumerate(FUNNEL_EVENTS):
        val = funnel_accum[i]
        pct = round(val / base * 100, 1)
        bar_pct = min(pct, 100.0)

        stage_pattern = re.compile(
            r'(<div class="f-label">' + re.escape(label) + r'</div>.*?data-pct=")[\d.]+("[^>]*></div></div>\s*<div class="f-value">)\d+(</div>\s*<div class="f-rate">)[\d.]+%(</div>)',
            re.DOTALL,
        )
        html = stage_pattern.sub(
            lambda m, bar_pct=bar_pct, pct=pct, val=val: f'{m.group(1)}{bar_pct}{m.group(2)}{val}{m.group(3)}{pct}%{m.group(4)}',
            html,
        )

    # Abandono entre etapas (funnel-connector, acumulado)
    for i in range(len(funnel_accum) - 1):
        a, b = funnel_accum[i], funnel_accum[i + 1]
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

    # Conversion total (paso 1 -> paso final, acumulado)
    conv_total = round(funnel_accum[-1] / base * 100, 1) if base else 0
    html = re.sub(r'(<div class="fsumm-num">)[\d.]+%(</div>\s*<div class="fsumm-label">Conversion total)', rf'\g<1>{conv_total}%\g<2>', html)

    # Mayor abandono: se calcula desde el embudo real en vez de dejarlo fijo.
    # Estaba hardcodeado en "66.5% — paso 1->2 (datos empresa)" cuando el paso
    # 1->2 real era 29.4% y la mayor caida estaba en otro paso. El numero no
    # correspondia a ningun dato de la tabla y contradecia la seccion de Insights.
    peor_i, peor_pct = 0, 0.0
    for i in range(len(funnel_accum) - 1):
        a, b = funnel_accum[i], funnel_accum[i + 1]
        pct = (a - b) / a * 100 if a else 0
        if pct > peor_pct:
            peor_i, peor_pct = i, pct
    peor_pct = round(peor_pct, 1)
    # "1. Tipo de trabajador" -> "Tipo de trabajador"
    origen = FUNNEL_EVENTS[peor_i][0].split(". ", 1)[-1]
    destino = FUNNEL_EVENTS[peor_i + 1][0].split(". ", 1)[-1]
    peor_label = f"Mayor abandono: paso {peor_i + 1}&#8594;{peor_i + 2} ({origen} &#8594; {destino})"
    html = re.sub(
        r'(<div class="fsumm-num" style="color:var\(--red\)">)[\d.]+%(</div>\s*<div class="fsumm-label">)'
        r'Mayor abandono[^<]*(</div>)',
        rf'\g<1>{peor_pct}%\g<2>{peor_label}\g<3>',
        html,
    )

    # Errores y fallos (acumulado)
    html = re.sub(
        r'(<div class="fsumm-num" style="color:var\(--amber\)">)\d+(</div>\s*<div class="fsumm-label">Errores de formulario)',
        rf'\g<1>{errores_accum}\g<2>',
        html,
    )

    fallos_accum = counts_accum["loan_request_failure"]
    html = re.sub(
        r'(<div class="fsumm-num" style="color:var\(--red\)">)\d+(</div>\s*<div class="fsumm-label">Fallos al enviar solicitud)',
        rf'\g<1>{fallos_accum}\g<2>',
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

    # Insight 1: mayor caida del funnel (acumulado)
    drops = []
    for i in range(len(funnel_accum) - 1):
        a, b = funnel_accum[i], funnel_accum[i + 1]
        if a > 0:
            drops.append((round((a - b) / a * 100, 1), i))
    if drops:
        drop_pct, idx = max(drops)
        label_a = FUNNEL_EVENTS[idx][0].split(". ", 1)[1]
        label_b = FUNNEL_EVENTS[idx + 1][0].split(". ", 1)[1]
        a, b = funnel_accum[idx], funnel_accum[idx + 1]
        html = replace_insight(
            html, 1, "Friccion critica",
            f'El <em>{drop_pct}%</em> abandona entre &quot;{label_a}&quot; y &quot;{label_b}&quot;',
            f'De {a} usuarios en el paso &quot;{label_a}&quot;, solo {b} llegan a &quot;{label_b}&quot; '
            f'({round(b / a * 100, 1) if a else 0}% de continuidad). Este es el mayor punto de fuga del '
            f'funnel acumulado — superar este paso deberia ser la prioridad de optimizacion '
            f'numero 1.'
        )

    # Insight 2: oportunidad de recuperacion (acumulado)
    #
    # Antes esto restaba counts_accum["pre_approval_accepted"] (eventCount) menos
    # funnel_accum[-1] (activeUsers): eventos menos personas. Daba ~14.350
    # "usuarios recuperables", una cifra que no significaba nada y que ademas
    # contradecia el embudo mostrado justo arriba. Ahora ambos lados salen del
    # mismo embudo, asi que la resta si son personas.
    idx_pre_ins = next(i for i, (l, _) in enumerate(FUNNEL_EVENTS) if l.startswith("5."))
    preap_users = funnel_accum[idx_pre_ins]
    enviadas_users = funnel_accum[-1]
    recuperables = max(preap_users - enviadas_users, 0)
    html = replace_insight(
        html, 2, "Oportunidad de recuperacion",
        f'<em>{recuperables} usuarios</em> llegaron a pre-aprobacion pero no enviaron',
        f'{preap_users} usuarios recibieron pre-aprobacion y {enviadas_users} enviaron la solicitud: '
        f'{recuperables} quedaron con luz verde sin completar. Son el segmento con mayor intencion '
        f'de compra disponible, y una campana de retargeting dirigida solo a ellos puede recuperar '
        f'parte de esas solicitudes.'
    )

    # Insight 3: tasa de conversion entre "Cotizacion calculada" -> "Pre aprobacion" (paso 5)
    #
    # Usa funnel_accum, no funnel_values: los insights 1 y 2 hablan del acumulado
    # y este salia de la ventana de 7 dias. Los tres aparecen juntos bajo el mismo
    # titulo, asi que mezclar periodos hacia que el porcentaje no cuadrara con el
    # embudo de arriba (decia 72.3% cuando el acumulado daba 70.1%).
    idx_calc = next(i for i, (l, _) in enumerate(FUNNEL_EVENTS) if l.startswith("3."))
    idx_pre = next(i for i, (l, _) in enumerate(FUNNEL_EVENTS) if l.startswith("5."))
    calc_val = funnel_accum[idx_calc]
    pre_val = funnel_accum[idx_pre]
    pct_calidad = round(pre_val / calc_val * 100, 1) if calc_val else 0
    html = replace_insight(
        html, 3, "Senal de calidad",
        f'El <em>{pct_calidad}%</em> de quienes calculan llegan a pre-aprobacion',
        f'Paso 3 -> Paso 5: {calc_val} cotizaciones calculadas, {pre_val} pre-aprobadas = {pct_calidad}% de '
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

    # --- Rangos del filtro global (embudo, KPIs, errores, graficos) ---
    rangos = construir_rangos(client, datetime.date.today(), all_event_names)
    nuevo_rangos = (
        "/* DATA_RANGOS_START */\n"
        "var DATA_RANGOS = "
        + json.dumps(rangos, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
        "/* DATA_RANGOS_END */"
    )
    html, n_rangos = re.subn(
        r"/\* DATA_RANGOS_START \*/.*?/\* DATA_RANGOS_END \*/",
        lambda _: nuevo_rangos,
        html, count=1, flags=re.DOTALL,
    )
    if not n_rangos:
        print("  AVISO: no se encontro el bloque DATA_RANGOS en el HTML")

    # --- Inversion en Medios Pagados (datos manuales desde ads_data.json) ---
    if os.path.exists(ADS_DATA_FILE):
        with open(ADS_DATA_FILE, "r", encoding="utf-8") as f:
            ads = json.load(f)

        m = ads.get("meta_ads", {})
        g = ads.get("google_ads", {})

        # --- Serie diaria para el filtro de rango de fechas del dashboard ---
        # El HTML agrega estos dias en el navegador, asi que el filtro funciona
        # sin volver a llamar a ninguna API. Los presupuestos y tipos van en
        # diccionarios aparte porque son atributos de la campana, no del dia.
        data_diario = {
            "periodo_desde": ads.get("periodo_desde", ""),
            "periodo_hasta": ads.get("periodo_hasta", ""),
            "actualizado": ads.get("actualizado", ""),
            "meta": {
                "diario": m.get("diario", []),
                "diario_campanas": m.get("diario_campanas", []),
                "presupuestos": {
                    c["nombre"]: c.get("presupuesto_dia", 0)
                    for c in m.get("campanas", [])
                },
            },
            "google": {
                "diario": g.get("diario", []),
                "diario_campanas": g.get("diario_campanas", []),
                "presupuestos": {
                    c["nombre"]: c.get("presupuesto_dia", 0)
                    for c in g.get("campanas", [])
                },
                "tipos": {
                    c["nombre"]: c.get("tipo", "")
                    for c in g.get("campanas", [])
                },
            },
        }
        nuevo_diario = (
            "/* DATA_DIARIO_START */\n"
            "var DATA_DIARIO = "
            + json.dumps(data_diario, ensure_ascii=False, separators=(",", ":"))
            + ";\n"
            "/* DATA_DIARIO_END */"
        )
        html = re.sub(
            r"/\* DATA_DIARIO_START \*/.*?/\* DATA_DIARIO_END \*/",
            lambda _: nuevo_diario,
            html, count=1, flags=re.DOTALL,
        )
        print(f"  Serie diaria inyectada: {len(data_diario['meta']['diario'])} dias Meta, "
              f"{len(data_diario['google']['diario'])} dias Google")

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

    # Los tres graficos diarios se bajan sobre TODO el historial, no sobre una
    # ventana fija de 30 dias. Antes, al elegir un rango anterior en el filtro,
    # el grafico se recortaba a la interseccion con esos 30 dias y mostraba
    # apenas unos pocos dias mientras el titulo seguia diciendo "ultimos 30".
    inicio_series = datetime.datetime.strptime(
        ACCUM_DATE_RANGE.start_date, "%Y-%m-%d").date()
    daily_errors = fetch_daily_errors(client, DateRange(
        start_date=inicio_series.strftime("%Y-%m-%d"), end_date=hoy.strftime("%Y-%m-%d")
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

    # Grafico de fallos al enviar solicitud (loan_request_failure) por dia: ultimos 30 dias
    daily_failures = fetch_daily_errors(client, DateRange(
        start_date=inicio_series.strftime("%Y-%m-%d"), end_date=hoy.strftime("%Y-%m-%d")
    ), event_name="loan_request_failure")
    items = [f"{{date:'{d}', val:{v}}}" for d, v in daily_failures]
    lines = []
    for i in range(0, len(items), 3):
        lines.append("  " + " ".join(x + "," if j != len(items) - 1 else x
                                       for j, x in enumerate(items[i:i + 3], start=i)))
    daily_failures_block = (
        "/* DAILY_FAILURES_START */\n"
        "var DATA_DAILY_FAILURES = [\n"
        + "\n".join(lines) + "\n"
        "];\n"
        "/* DAILY_FAILURES_END */"
    )
    html = re.sub(
        r"/\* DAILY_FAILURES_START \*/.*?/\* DAILY_FAILURES_END \*/",
        daily_failures_block,
        html,
        flags=re.S,
    )

    # Grafico agrupado cotizaciones vs solicitudes por dia: ultimos 30 dias
    daily_starts = dict(fetch_daily_errors(client, DateRange(
        start_date=inicio_series.strftime("%Y-%m-%d"), end_date=hoy.strftime("%Y-%m-%d")
    ), event_name="worker_classification_selected"))
    daily_subs = dict(fetch_daily_errors(client, DateRange(
        start_date=inicio_series.strftime("%Y-%m-%d"), end_date=hoy.strftime("%Y-%m-%d")
    ), event_name="purchase"))
    all_dates = sorted(set(daily_starts) | set(daily_subs))
    funnel_items = [f"{{date:'{d}', starts:{daily_starts.get(d,0)}, subs:{daily_subs.get(d,0)}}}" for d in all_dates]
    lines = []
    for i in range(0, len(funnel_items), 3):
        lines.append("  " + " ".join(x + "," if j != len(funnel_items) - 1 else x
                                      for j, x in enumerate(funnel_items[i:i + 3], start=i)))
    daily_funnel_block = (
        "/* DAILY_FUNNEL_START */\n"
        "var DATA_DAILY_FUNNEL = [\n"
        + "\n".join(lines) + "\n"
        "];\n"
        "/* DAILY_FUNNEL_END */"
    )
    html = re.sub(
        r"/\* DAILY_FUNNEL_START \*/.*?/\* DAILY_FUNNEL_END \*/",
        daily_funnel_block,
        html,
        flags=re.S,
    )

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print("\nDashboard_ALMI.html actualizado correctamente.")


if __name__ == "__main__":
    main()
