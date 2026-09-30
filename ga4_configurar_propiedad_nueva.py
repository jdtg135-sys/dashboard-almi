"""Configura la propiedad GA4 NUEVA (ALMI Financiera Cotizador nuevo, 554405139).

Crea dimensiones y metricas personalizadas a partir de los parametros reales
que envia el contenedor GTM-5GSLND8N, y marca loan_request_created como
evento clave. Es idempotente: lo que ya existe se omite.
"""
import sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from ga4_admin_auth import get_admin_credentials
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.admin_v1beta.types import CustomDimension, CustomMetric, KeyEvent

PROP = "properties/554405139"

# (parametro, nombre visible, descripcion)
DIMENSIONES = [
    ("step_slug",             "Paso slug",              "Identificador del paso del cotizador"),
    ("step_index",            "Paso numero",            "Posicion del paso en el wizard, para ordenar el embudo"),
    ("channel",               "Canal",                    "Canal de contacto o envio"),
    ("company_id",            "Empresa ID",             "Identificador de la empresa pagadora"),
    ("document_type",         "Tipo de documento",        "Tipo de documento de identidad"),
    ("bank_id",               "Banco ID",               "Banco seleccionado para el desembolso"),
    ("account_type",          "Tipo de cuenta",           "Ahorros o corriente"),
    ("error_type",            "Tipo de error",            "Clasificacion del error"),
    ("error_message",         "Mensaje de error",         "Texto del error devuelto"),
    ("error",                 "Error",                    "Detalle del error de cotizacion"),
    ("field_name",            "Campo",                    "Campo del formulario que fallo la validacion"),
    ("reason",                "Motivo",                   "Motivo reportado por el evento"),
    ("source",                "Origen",                   "Origen de la accion dentro del cotizador"),
    ("loan_request_number",   "Numero de solicitud",      "Consecutivo de la solicitud creada"),
    ("is_manual",             "Empresa manual",           "La empresa se escribio a mano"),
    ("has_referral_code",     "Tiene codigo de referido", "El usuario ingreso codigo de referido"),
    ("has_other_income",      "Tiene otros ingresos",     "Declara ingresos adicionales"),
    ("has_salary_discounts",  "Tiene descuentos",         "Declara descuentos de nomina"),
    ("has_credit_history",    "Tiene historial",          "Declara historial crediticio"),
    ("known_client_shortcut", "Atajo cliente conocido",   "Entro por el atajo de cliente ya registrado"),
    ("has_upload_url",        "Tiene URL de carga",       "La respuesta incluyo URL de carga de documentos"),
    ("has_recover_url",       "Tiene URL de retomar",     "La respuesta incluyo URL para retomar la solicitud"),
]

# (parametro, nombre visible, unidad, descripcion)
METRICAS = [
    ("loan_amount",      "Monto del credito",      "CURRENCY", "Monto en pesos de la solicitud"),
    ("selected_amount",  "Monto seleccionado",     "CURRENCY", "Monto elegido por el usuario, en pesos"),
    ("salary",           "Salario",                "CURRENCY", "Salario declarado, en pesos"),
    ("max_approved",     "Maximo preaprobado",     "CURRENCY", "Cupo maximo preaprobado, en pesos"),
    ("max_amount",       "Monto maximo",           "CURRENCY", "Tope del rango de monto, en pesos"),
    ("new_amount",       "Monto ajustado",         "CURRENCY", "Monto despues del ajuste, en pesos"),
    ("installments",     "Cuotas",                 "STANDARD", "Numero de cuotas"),
    ("new_installments", "Cuotas ajustadas",       "STANDARD", "Numero de cuotas despues del ajuste"),
    ("from_step_index",  "Paso de origen",         "STANDARD", "Paso desde el que se presiono atras"),
]

EVENTOS_CLAVE = ["loan_request_created"]


def main():
    c = AnalyticsAdminServiceClient(credentials=get_admin_credentials())

    existentes = {d.parameter_name for d in c.list_custom_dimensions(parent=PROP)}
    creadas = 0
    for param, nombre, desc in DIMENSIONES:
        if param in existentes:
            print(f"  = dimension ya existe: {param}")
            continue
        c.create_custom_dimension(parent=PROP, custom_dimension=CustomDimension(
            parameter_name=param, display_name=nombre, description=desc,
            scope=CustomDimension.DimensionScope.EVENT,
        ))
        print(f"  + dimension: {param}")
        creadas += 1

    existentes = {m.parameter_name for m in c.list_custom_metrics(parent=PROP)}
    creadas_m = 0
    for param, nombre, unidad, desc in METRICAS:
        if param in existentes:
            print(f"  = metrica ya existe: {param}")
            continue
        metrica = CustomMetric(
            parameter_name=param, display_name=nombre, description=desc,
            measurement_unit=getattr(CustomMetric.MeasurementUnit, unidad),
            scope=CustomMetric.MetricScope.EVENT,
        )
        # GA4 exige declarar el tipo restringido en las metricas de moneda.
        if unidad == "CURRENCY":
            metrica.restricted_metric_type = [
                CustomMetric.RestrictedMetricType.REVENUE_DATA
            ]
        c.create_custom_metric(parent=PROP, custom_metric=metrica)
        print(f"  + metrica: {param} ({unidad})")
        creadas_m += 1

    existentes = {k.event_name for k in c.list_key_events(parent=PROP)}
    creados_e = 0
    for nombre in EVENTOS_CLAVE:
        if nombre in existentes:
            print(f"  = evento clave ya existe: {nombre}")
            continue
        c.create_key_event(parent=PROP, key_event=KeyEvent(
            event_name=nombre,
            counting_method=KeyEvent.CountingMethod.ONCE_PER_EVENT,
        ))
        print(f"  + evento clave: {nombre}")
        creados_e += 1

    print(f"\nResumen: {creadas} dimensiones, {creadas_m} metricas, {creados_e} eventos clave.")


if __name__ == "__main__":
    main()
