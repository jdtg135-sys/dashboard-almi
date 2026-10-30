# -*- coding: utf-8 -*-
"""Presupuesto para noviembre y diciembre, con las solicitudes REALES de la
plataforma (dato del cliente, 1 al 26 de octubre de 2026).

QUE CAMBIO FRENTE AL CALCULO ANTERIOR
-------------------------------------
Antes habia tres bases de costo porque no se sabia repartir la diferencia
entre lo que cuenta GA4 y lo que cuenta la plataforma. Con el detalle diario
real esa diferencia queda medida y deja de ser un supuesto: ya no hacen falta
escenarios.
"""

DIARIAS = [163, 150, 169, 135, 216, 199, 196, 167, 171, 137, 112, 160, 209,
           217, 208, 189, 158, 155, 261, 212, 222, 206, 181, 123, 173, 245]

INV_DIA = 356_762        # inversion diaria actual (Meta + Google, 1-26 oct)
INV_PERIODO = 9_275_801
GA4_TOTAL = 4_071        # loan_request_created en GA4, mismo rango
GA4_PAUTA = 2_797        # de esas, las que vienen de pauta (68,7%)
RECARGO = 1.20           # al subir volumen el costo sube

n = len(DIARIAS)
total = sum(DIARIAS)
prom = total / n
print("=== Solicitudes reales de la plataforma ===")
print("  {} dias, {:,} solicitudes, promedio {:.1f} por dia".format(n, total, prom))
print("  mejor dia {}, peor dia {}".format(max(DIARIAS), min(DIARIAS)))

brecha = total / GA4_TOTAL
print()
print("=== La brecha con GA4 queda medida ===")
print("  GA4: {:,}   plataforma: {:,}   la plataforma registra {:+.1f}% mas".format(
    GA4_TOTAL, total, (brecha - 1) * 100))
print("  El 21-oct habiamos medido +18% por otra via. Coincide, asi que la")
print("  base deja de ser un supuesto.")

pauta_real = GA4_PAUTA * brecha
costo = INV_PERIODO / pauta_real
print()
print("=== Costo por solicitud de pauta ===")
print("  solicitudes de pauta en la plataforma: {:,.0f}".format(pauta_real))
print("  costo real:        ${:,.0f}".format(costo))
print("  con recargo 20%:   ${:,.0f}".format(costo * RECARGO))

print()
print("=== Presupuesto ===")
plan = {}
for mes, meta, dias in (("Noviembre", 290, 30), ("Diciembre", 323, 31)):
    falta = meta - prom
    extra = falta * costo * RECARGO
    dia = INV_DIA + extra
    plan[mes] = dia
    print()
    print("{}: meta {}/dia durante {} dias".format(mes, meta, dias))
    print("  faltan {:.0f} solicitudes diarias sobre las {:.0f} de hoy (+{:.0f}%)".format(
        falta, prom, falta / prom * 100))
    print("  inversion diaria  ${:>10,.0f}   (hoy ${:,.0f}, es x{:.2f})".format(
        dia, INV_DIA, dia / INV_DIA))
    print("  inversion del mes ${:>10,.0f}".format(dia * dias))

print()
print("=== Escalonado hasta la meta de noviembre ===")
print("Pasos del 25% cada 4 dias para no reiniciar el aprendizaje:")
inv, dia_n = INV_DIA, 1
while inv < plan["Noviembre"] - 1:
    inv = min(inv * 1.25, plan["Noviembre"])
    print("  dia {:>2}:  ${:>9,.0f}/dia".format(dia_n, inv))
    dia_n += 4
