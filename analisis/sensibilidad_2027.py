# -*- coding: utf-8 -*-
"""Que tan confiable es el 118 millones mensuales (11-nov-2026).

LA DEBILIDAD PRINCIPAL DEL MODELO
---------------------------------
La elasticidad se midio con inversiones diarias entre 154.000 y 470.000. El
plan la extrapola hasta 3,9 millones: ocho veces por encima del rango observado.
Fuera del rango, una elasticidad con correlacion de 0,23 a 0,40 deja de ser una
medicion y pasa a ser una conjetura.

Este script muestra cuanto cambia el resultado al mover los tres supuestos que
mas pesan, para saber si el numero es solido o fragil.
"""
import math

META = 1000
HOY_INV, HOY_SOL = 430_000, 195


def plan(b_interrup, factor_cpa, tope_meta, tope_tiktok):
    canales = [
        ("Meta",        1_964 * factor_cpa, 330_000, tope_meta,    b_interrup),
        ("Búsqueda",    3_222 * factor_cpa,  87_000, 160,          0.10),
        ("TikTok",      2_750 * factor_cpa, 100_000, tope_tiktok,  b_interrup),
        ("Demand Gen",  2_950 * factor_cpa, 100_000, 150,          b_interrup),
        ("YouTube",     3_200 * factor_cpa, 100_000, 120,          b_interrup),
    ]
    K = [(n, (s0 ** b) / cpa, tope, b) for n, cpa, s0, tope, b in canales]

    def asignar(l):
        tot_s = tot_q = 0
        for n, k, tope, b in K:
            s = ((1 - b) * k / l) ** (1 / b)
            q = k * s ** (1 - b)
            if q > tope:
                q, s = tope, (tope / k) ** (1 / (1 - b))
            tot_s += s; tot_q += q
        return tot_s, tot_q

    techo = sum(c[3] for c in canales)
    if techo < META:
        return None, techo
    lo, hi = 1e-12, 1.0
    for _ in range(250):
        mid = math.sqrt(lo * hi)
        if asignar(mid)[1] > META:
            lo = mid
        else:
            hi = mid
    s, q = asignar(math.sqrt(lo * hi))
    return s, techo


print("=" * 80)
print("EL PROBLEMA DE FONDO")
print("=" * 80)
print("  rango de inversion diaria con el que se midio:  154.000 a 470.000")
print("  inversion diaria que propone el plan:           3.934.099")
print("  extrapolacion:                                  8,4 veces fuera del rango")
print("  correlacion de la medicion:                     0,23 y 0,40")
print()
print("  Traduccion: el 118 millones no es una prediccion, es el extremo caro")
print("  de un abanico. Estos son los otros extremos.")

print()
print("=" * 80)
print("1. SI LA ELASTICIDAD ES MENOR DE LO MEDIDO")
print("=" * 80)
print("%-38s %14s %14s" % ("supuesto", "inv/día", "inv/mes"))
for b in (0.29, 0.25, 0.20, 0.15):
    s, _ = plan(b, 1.0, 450, 200)
    etq = "b = %.2f%s" % (b, "   (lo medido)" if b == 0.29 else "")
    print("%-38s %14s %14s" % (etq, format(int(s), ","), format(int(s * 30), ",")))

print()
print("=" * 80)
print("2. SI SE RECUPERA LA CONVERSIÓN DEL COTIZADOR")
print("=" * 80)
print("  Hoy convierte 36,4% de punta a punta; el cotizador anterior hacia 45,0%.")
print("  Eso NO es un canal: es un multiplicador sobre TODOS los canales.")
print("  Recuperarlo baja el costo por solicitud un 19% en los cinco a la vez.")
print()
print("%-38s %14s %14s" % ("supuesto", "inv/día", "inv/mes"))
for f, etq in ((1.0, "conversión como hoy"), (0.81, "conversión recuperada a 45%")):
    s, _ = plan(0.29, f, 450, 200)
    print("%-38s %14s %14s" % (etq, format(int(s), ","), format(int(s * 30), ",")))

print()
print("=" * 80)
print("3. SI LOS TECHOS SON MÁS ALTOS")
print("=" * 80)
print("  Los topes por canal son supuestos mios, no mediciones. Con la meta al")
print("  93%% del techo, moverlos cambia mucho el resultado.")
print()
print("%-38s %14s %14s %9s" % ("supuesto", "inv/día", "inv/mes", "techo"))
for tm, tt, etq in ((450, 200, "topes del plan"),
                    (550, 250, "Meta 550 · TikTok 250"),
                    (650, 300, "Meta 650 · TikTok 300")):
    s, techo = plan(0.29, 1.0, tm, tt)
    print("%-38s %14s %14s %9d" % (etq, format(int(s), ","), format(int(s * 30), ","), techo))

print()
print("=" * 80)
print("ESCENARIO RAZONABLE: las tres cosas a la vez, sin exagerar ninguna")
print("=" * 80)
s, techo = plan(0.22, 0.81, 550, 250)
print("  elasticidad 0,22 (dentro del margen de error de lo medido)")
print("  conversión del cotizador recuperada")
print("  techos de Meta y TikTok algo más altos")
print()
print("  inversión diaria   %s" % format(int(s), ","))
print("  inversión mensual  %s" % format(int(s * 30), ","))
print("  costo por solicitud %s" % format(int(s / META), ","))
print()
print("  contra los %s mensuales del plan: %.0f%% menos"
      % (format(118_022_970, ","), (1 - s * 30 / 118_022_970) * 100))
