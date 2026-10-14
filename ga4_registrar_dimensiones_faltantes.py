# -*- coding: utf-8 -*-
"""Registra en GA4 los parametros que GTM espera y la propiedad no tenia.

Contexto (14-oct-2026): el valor de conversion llega en cero desde el 1-oct.
La etiqueta de GA4 y la de Meta SI mapean el valor; lo toma una variable de
GTM que busca `loan_amount` o `selectedAmount` en la capa de datos y exige que
sean numericos. Devuelve 0, asi que o el cotizador no los manda o los manda
como texto.

GA4 recoge los parametros aunque no esten registrados, pero no los muestra.
Al registrarlos, en unas horas sabremos cual de los dos escenarios es, sin
pedirle nada a desarrollo.

Se registran como DIMENSION y no como metrica a proposito: una dimension
muestra el valor literal sea numero o texto, que es justo lo que hay que
averiguar. Si resultan numericos se pueden convertir despues.

Uso:  python ga4_registrar_dimensiones_faltantes.py        -> simulacion
      python ga4_registrar_dimensiones_faltantes.py --go   -> registra
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ga4_admin_auth import get_admin_credentials
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.admin_v1beta.types import CustomDimension

PROPIEDAD = "properties/554405139"
DRY = "--go" not in sys.argv

# parametro -> nombre visible (sin parentesis: GA4 los rechaza)
FALTANTES = {
    "loan_amount":     "Monto del credito",
    "selectedAmount":  "Monto seleccionado",
    "maxApproved":     "Monto maximo aprobado",
    "salary":          "Salario reportado",
    "installments":    "Numero de cuotas",
    "from_step_index": "Paso de origen",
    "transaction_id":  "Id de transaccion",
}

cli = AnalyticsAdminServiceClient(credentials=get_admin_credentials())
existentes = {d.parameter_name: d for d in cli.list_custom_dimensions(parent=PROPIEDAD)}
print(f"La propiedad tiene {len(existentes)} dimensiones registradas\n")

for parametro, nombre in FALTANTES.items():
    if parametro in existentes:
        print(f"  ya existe   {parametro}")
        continue
    if DRY:
        print(f"  [simulacion] registraria {parametro:<18} como '{nombre}'")
        continue
    d = CustomDimension(
        parameter_name=parametro,
        display_name=nombre,
        description=f"Parametro {parametro} enviado por el cotizador. "
                    f"Registrado el 14-oct-2026 para diagnosticar el valor de conversion.",
        scope=CustomDimension.DimensionScope.EVENT,
    )
    try:
        r = cli.create_custom_dimension(parent=PROPIEDAD, custom_dimension=d)
        print(f"  registrada  {parametro:<18} -> {r.name}")
    except Exception as e:
        print(f"  ERROR       {parametro:<18} :: {str(e)[:130]}")

if DRY:
    print("\nSIMULACION. Ejecutar con --go para registrar.")
else:
    total = len(list(cli.list_custom_dimensions(parent=PROPIEDAD)))
    print(f"\nLISTO. La propiedad queda con {total} dimensiones.")
    print("Los datos aparecen desde ahora; GA4 no los aplica a lo ya recogido.")
