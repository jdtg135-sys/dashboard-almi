# -*- coding: utf-8 -*-
"""Reparto de los 13 millones de noviembre entre Meta y Google (4-nov-2026).

DATOS REALES DEL 1 AL 4 DE NOVIEMBRE
------------------------------------
  Meta   458 solicitudes   1.152.673 invertidos   costo 2.517
  Google  72 conversiones    443.972 invertidos   costo 6.166

Google se encarecio: en octubre cerro en 3.752 y en lo que va de noviembre
esta en 6.166, un 64% mas. Meta mejoro: de 2.858 en octubre a 2.517.

El calculo usa el costo de NOVIEMBRE, no el de octubre, porque es el que
describe la subasta de hoy.
"""

TOTAL_MES = 13_000_000
GASTADO_META = 1_152_673
GASTADO_GOOGLE = 443_972
SOL_META = 458
SOL_GOOGLE = 72
DIAS_RESTANTES = 26          # del 5 al 30 de noviembre

COSTO_META = GASTADO_META / SOL_META
COSTO_GOOGLE = GASTADO_GOOGLE / SOL_GOOGLE

gastado = GASTADO_META + GASTADO_GOOGLE
queda = TOTAL_MES - gastado
diario = queda / DIAS_RESTANTES

print("=== Punto de partida ===")
print("  presupuesto del mes      {:>12,.0f}".format(TOTAL_MES))
print("  gastado 1 al 4 de nov    {:>12,.0f}   ({:.1f}%)".format(gastado, gastado / TOTAL_MES * 100))
print("  queda                    {:>12,.0f}   para {} dias".format(queda, DIAS_RESTANTES))
print("  disponible por dia       {:>12,.0f}".format(diario))
print()
print("  ritmo actual por dia     {:>12,.0f}   (Meta {:,.0f} + Google {:,.0f})".format(
    gastado / 4, GASTADO_META / 4, GASTADO_GOOGLE / 4))
print("  costo por solicitud      Meta {:,.0f}   Google {:,.0f}".format(COSTO_META, COSTO_GOOGLE))
print()

if diario < gastado / 4:
    print("  AVISO: el presupuesto disponible por dia ({:,.0f}) esta POR DEBAJO".format(diario))
    print("  del ritmo actual ({:,.0f}). Con 13 millones no se sostiene el ritmo de".format(gastado / 4))
    print("  los primeros cuatro dias: hay que bajar {:.0f}% o quedarse corto a fin de mes.".format(
        (1 - diario / (gastado / 4)) * 100))
print()

print("=== Escenarios de reparto para los {:,.0f} que quedan ===".format(queda))
print()
print("{:<34} {:>12} {:>12} {:>9} {:>9} {:>10}".format(
    "escenario", "Meta", "Google", "sol Meta", "sol Goo", "total mes"))
print("-" * 92)

escenarios = [
    ("Proporcion actual (72/28)", 0.722),
    ("Recomendado (85/15)", 0.85),
    ("Agresivo (92/8)", 0.92),
    ("Solo Meta (100/0)", 1.00),
]
for etq, pm in escenarios:
    m = queda * pm
    g = queda * (1 - pm)
    sm = m / COSTO_META
    sg = g / COSTO_GOOGLE if g else 0
    total = SOL_META + SOL_GOOGLE + sm + sg
    print("{:<34} {:>12,.0f} {:>12,.0f} {:>9,.0f} {:>9,.0f} {:>10,.0f}".format(
        etq, m, g, sm, sg, total))

print()
print("=== Contra la meta de noviembre ===")
META_DIARIA = 290
META_MES = META_DIARIA * 30
# Lo de arriba son solicitudes de pauta. La plataforma registra ~16% mas que
# lo que alcanzan a ver las plataformas, y ademas entra el trafico sin pauta,
# que en octubre fue el 31% del total.
AJUSTE_PLATAFORMA = 1.163
SIN_PAUTA_DIA = 58
mejor = queda * 0.85 / COSTO_META + queda * 0.15 / COSTO_GOOGLE + SOL_META + SOL_GOOGLE
en_plataforma = mejor * AJUSTE_PLATAFORMA + SIN_PAUTA_DIA * 30
print("  meta del mes                      {:>8,.0f}  ({}/dia)".format(META_MES, META_DIARIA))
print("  proyeccion con 13 millones        {:>8,.0f}  ({:.0f}/dia)".format(en_plataforma, en_plataforma / 30))
print("  diferencia                        {:>8,.0f}  ({:.0f}% de la meta)".format(
    en_plataforma - META_MES, en_plataforma / META_MES * 100))
print()
falta = META_MES - en_plataforma
extra = falta / AJUSTE_PLATAFORMA * COSTO_META
print("  para alcanzar la meta harian falta {:,.0f} solicitudes mas de pauta,".format(
    falta / AJUSTE_PLATAFORMA))
print("  que al costo de Meta son {:,.0f} adicionales: un presupuesto de {:,.0f}.".format(
    extra, TOTAL_MES + extra))
