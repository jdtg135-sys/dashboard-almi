# -*- coding: utf-8 -*-
"""Modelo de escalado a 1.000 solicitudes diarias (11-nov-2026).

DE DONDE SALEN LOS NUMEROS
--------------------------
  base real hoy        195 solicitudes/dia (conteo de la plataforma, 1-10 nov)
  inversion hoy        430.000/dia
  costo hoy            2.099 por solicitud
  elasticidad b        0,29  (medida en las dos versiones del cotizador por
                       separado: 0,294 y 0,287, 15 y 6 semanas)
  conversion hoy       36,4% de punta a punta; el cotizador anterior hacia 45,0%

La elasticidad dice que el costo por solicitud crece con la inversion diaria
elevada a 0,29. Como las solicitudes son inversion/costo, se deduce que:

      solicitudes  ~  inversion ^ (1 - b)  =  inversion ^ 0,71

Esa sola formula es la que hace que escalar por volumen sea tan caro, y es el
hallazgo central del plan.
"""
import math

BASE_SOL = 195.0
BASE_INV = 430_000.0
B = 0.29
META = 1000.0
CONV_HOY = 0.364
CONV_ANTERIOR = 0.450


def inversion_para(mult_volumen):
    """Cuanta inversion diaria hace falta para multiplicar el volumen."""
    return BASE_INV * mult_volumen ** (1 / (1 - B))


print("=" * 72)
print("1. QUE CUESTA LLEGAR A 1.000 SOLO COMPRANDO MAS MEDIOS")
print("=" * 72)
mult = META / BASE_SOL
inv = inversion_para(mult)
print("  multiplicador necesario      x%.2f" % mult)
print("  inversion diaria necesaria   %s" % format(int(inv), ","))
print("  inversion mensual            %s" % format(int(inv * 30), ","))
print("  veces el presupuesto de hoy  x%.1f" % (inv / BASE_INV))
print("  costo por solicitud al final %s" % format(int(inv / META), ","))
print()
print("  Es inviable. 1.000 diarias comprando mas de lo mismo cuesta del orden")
print("  de %s millones al mes. El plan NO puede ser este." % int(inv * 30 / 1e6))

print()
print("=" * 72)
print("2. LAS PALANCAS QUE NO SON COMPRAR MAS")
print("=" * 72)
print()
print("  a) Recuperar la conversion del cotizador: 36,4%% -> 45,0%%")
f_conv = CONV_ANTERIOR / CONV_HOY
print("     multiplica el volumen por %.2f sin un peso mas de inversion" % f_conv)
print("     equivale a %+.0f solicitudes diarias sobre la base de hoy"
      % (BASE_SOL * (f_conv - 1)))
print("     La fuga esta en UNA pantalla: la de contacto, donde se piden")
print("     telefono, correo y cedula para el codigo. Alli se pierde el 26,6%%.")
print()
print("  b) Ganar posicion en busqueda de Google")
print("     Hoy aparecemos en el 10%% de las busquedas relevantes y perdemos")
print("     entre 60%% y 70%% de las impresiones POR RANKING, no por presupuesto.")
print("     Esa demanda ya existe y ya esta buscando: no hay que crearla.")
print()
print("  c) Mas convenios con empresas")
print("     El modelo es B2B2C. Cada convenio nuevo amplia la base de personas")
print("     elegibles sin competir en subasta. Es la unica palanca que mueve")
print("     la curva en lugar de moverse sobre ella.")
print()
print("  d) Canales nuevos (TikTok, YouTube, Demand Gen)")
print("     Cada canal trae su propia curva. Tres canales al 2x cuestan mucho")
print("     menos que un canal al 6x, justo por la elasticidad de arriba.")

print()
print("=" * 72)
print("3. ESCENARIOS COMBINADOS")
print("=" * 72)
print()
print("%-46s %12s %14s" % ("escenario", "inv/dia", "inv/mes"))
print("-" * 74)


def escenario(nombre, f_conversion, f_canales, objetivo=META):
    """f_canales: cuanto del volumen aportan canales nuevos y convenios,
    como multiplicador de la base, sin pasar por la curva de los actuales."""
    volumen_gratis = BASE_SOL * f_conversion * f_canales
    if volumen_gratis >= objetivo:
        inv_d = BASE_INV * f_canales      # aproximacion: canales nuevos a costo similar
    else:
        # lo que falta se compra sobre la curva de los canales actuales
        m = objetivo / (BASE_SOL * f_conversion * f_canales)
        inv_d = BASE_INV * f_canales * m ** (1 / (1 - B))
    print("%-46s %12s %14s" % (nombre, format(int(inv_d), ","),
                               format(int(inv_d * 30), ",")))
    return inv_d


escenario("Solo medios, todo igual", 1.0, 1.0)
escenario("Conversion recuperada a 45%", f_conv, 1.0)
escenario("Conversion + Google en posicion (x1,4)", f_conv, 1.4)
escenario("Conversion + Google + canales nuevos (x2,0)", f_conv, 2.0)
escenario("Todo lo anterior + convenios (x2,8)", f_conv, 2.8)

print()
print("  Leer la ultima fila: si entre conversion, posicion en Google, canales")
print("  nuevos y convenios se multiplica la capacidad por 2,8 veces, los 1.000")
print("  diarios se alcanzan con una inversion razonable. Si no, no se alcanzan")
print("  a ningun precio sensato.")

print()
print("=" * 72)
print("4. RAMPA TRIMESTRAL PROPUESTA PARA 2027")
print("=" * 72)
print()
TRIM = [
    ("Q1 2027", 320, 1.15, 1.00, "Arreglar la pantalla de contacto y el ranking de Google"),
    ("Q2 2027", 480, 1.24, 1.35, "Canales nuevos en prueba; primeros convenios del ano"),
    ("Q3 2027", 700, 1.24, 1.90, "Escalar lo que funciono; convenios en volumen"),
    ("Q4 2027", 1000, 1.24, 2.60, "Capacidad plena; temporada alta con presupuesto reforzado"),
]
print("%-9s %9s %9s %9s %13s %14s" % (
    "trimestre", "meta/dia", "f.conv", "f.canal", "inv/dia", "inv/mes"))
print("-" * 70)
for q, obj, fc, fk, _ in TRIM:
    m = obj / (BASE_SOL * fc * fk)
    inv_d = BASE_INV * fk * m ** (1 / (1 - B)) if m > 1 else BASE_INV * fk
    print("%-9s %9d %9.2f %9.2f %13s %14s" % (
        q, obj, fc, fk, format(int(inv_d), ","), format(int(inv_d * 30), ",")))
print()
for q, obj, fc, fk, nota in TRIM:
    print("  %-9s %s" % (q, nota))
