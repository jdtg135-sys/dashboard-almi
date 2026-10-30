# -*- coding: utf-8 -*-
"""Presupuesto para 290 (noviembre) y 323 (diciembre) solicitudes diarias.

POR QUE HAY TRES BASES DE COSTO Y NO UNA
----------------------------------------
Alvaro cuenta 211 solicitudes diarias en la plataforma del 1 al 26 de octubre.
GA4 cuenta 156,6 en el cotizador. La diferencia es de 54,4 al dia, un 34,7%.
No sabemos repartirla con certeza: parte es subconteo de GA4 (bloqueadores,
consentimiento) y parte pueden ser solicitudes que no pasan por el cotizador
web. Como no se puede afirmar cual pesa mas, se calcula con las tres bases y
se recomienda comprometer presupuesto con la mas conservadora.

LO QUE SI ESTA MEDIDO
---------------------
  - Inversion del 1 al 26-oct: la de las plataformas, exacta.
  - Reparto de origen en GA4: 68,7% de las solicitudes vienen de pauta.
  - Solicitudes de pauta en GA4 en el periodo: 2.797.
"""

INV_DIA = 356_762          # inversion diaria actual (Meta + Google, 1-26 oct)
INV_PERIODO = 9_275_801
SOLIC_PAUTA_GA4 = 2_797
BASE_HOY = 211             # promedio diario en la plataforma, dato del cliente

COSTO = {
    "Conservadora (solo lo que GA4 ve)": INV_PERIODO / SOLIC_PAUTA_GA4,
    "Intermedia (+18%, medido el 21-oct)": INV_PERIODO / SOLIC_PAUTA_GA4 / 1.18,
    "Optimista (+34,7%, toda la brecha)": INV_PERIODO / SOLIC_PAUTA_GA4 / 1.347,
}

# Al subir el volumen el costo sube: se compite por subastas mas caras y se
# agota el publico que convierte barato. No es un supuesto libre: septiembre
# cerro en 1.409 y octubre en 2.861 con una inversion parecida. Se usa un
# recargo del 20% sobre el costo actual, que es moderado para un salto de
# casi el doble de volumen.
RECARGO = 1.20

print("=== Costo por solicitud segun la base ===")
for k, v in COSTO.items():
    print("  {:<38} ${:>8,.0f}   con recargo ${:>8,.0f}".format(k, v, v * RECARGO))

print()
print("=== Lo que falta sobre la base actual de {} diarias ===".format(BASE_HOY))
for mes, meta, dias in (("Noviembre", 290, 30), ("Diciembre", 323, 31)):
    falta = meta - BASE_HOY
    print()
    print("{}: meta {}/dia, {} dias. Hay que sumar {} solicitudes diarias (+{:.0f}%).".format(
        mes, meta, dias, falta, falta / BASE_HOY * 100))
    print("  {:<38} {:>14} {:>16}".format("base", "inversion/dia", "inversion/mes"))
    for k, v in COSTO.items():
        extra = falta * v * RECARGO
        dia = INV_DIA + extra
        print("  {:<38} ${:>13,.0f} ${:>15,.0f}".format(k, dia, dia * dias))

print()
print("=== Escalonado para no reiniciar el aprendizaje ===")
print("Subir de golpe ~80% reinicia la fase de aprendizaje de las campanas y")
print("el costo se dispara justo cuando mas volumen se necesita. Pasos del 25%")
print("cada 4 dias, con la base conservadora:")
inv = INV_DIA
objetivo = INV_DIA + (290 - BASE_HOY) * COSTO["Conservadora (solo lo que GA4 ve)"] * RECARGO
dia = 1
while inv < objetivo:
    inv = min(inv * 1.25, objetivo)
    print("  dia {:>2}:  ${:>9,.0f}/dia".format(dia, inv))
    dia += 4
