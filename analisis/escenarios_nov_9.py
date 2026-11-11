# -*- coding: utf-8 -*-
"""Escenarios para cerrar noviembre y el riesgo de comprometerse (9-nov-2026).

OJO CON LO QUE SE PROMETE
-------------------------
El costo de 2.151 es el del 1 al 8. El CPM de Meta viene subiendo DENTRO del
mes (de 7.963 los dias 1-3 a 8.982 los dias 6-8, +12,8%). Si esa presion sigue,
el costo por solicitud sube y el mismo presupuesto rinde menos. Por eso cada
escenario se calcula tambien con el costo 10% mas alto.
"""
# La "Campana de formulario Copia 06/05/2026" NO entra en estas cuentas: el
# cliente gestiona esos contactos aparte y su presupuesto es independiente del
# que administramos. Se descuentan sus 80.425 del 1 al 8.
GASTADO = 2_559_593 + 719_600   # Meta (C1+C2+C4) + Google
HECHAS = 1_562
COSTO = GASTADO / HECHAS
META_MES = 255 * 30
DIAS = 22

falta = META_MES - HECHAS
print("Hechas al 8 de nov      {:>10,}".format(HECHAS))
print("Meta del mes            {:>10,}".format(META_MES))
print("Faltan en {} dias       {:>10,}   ({:.0f} por dia)".format(DIAS, falta, falta / DIAS))
print("Costo actual            {:>10,.0f}".format(COSTO))
print()
print("%-34s %13s %13s" % ("escenario", "costo 2.151", "costo +10%"))
print("-" * 62)
for etq, objetivo in (("Meta completa (7.650)", META_MES),
                      ("95% de la meta (7.268)", int(META_MES * .95)),
                      ("90% de la meta (6.885)", int(META_MES * .90)),
                      ("Sin tocar presupuesto (6.007)", 6007)):
    f = max(objetivo - HECHAS, 0)
    print("{:<34} {:>13,.0f} {:>13,.0f}".format(
        etq, GASTADO + f * COSTO, GASTADO + f * COSTO * 1.10))
print()
print("Lectura: comprometer la meta completa a 16,5 millones solo se sostiene")
print("si el costo se mantiene en 2.151. Si sube 10%, el mismo objetivo pide")
print("17,8 millones. Por eso el compromiso debe ser por costo, no por volumen.")
