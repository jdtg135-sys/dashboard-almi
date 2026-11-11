# -*- coding: utf-8 -*-
"""Proyeccion de noviembre con los datos reales del 1 al 8 (9-nov-2026).

Las solicitudes reales las entrega el cliente (conteo de la plataforma), no
Meta ni GA4. Son 8 dias, del domingo 1 al domingo 8.
"""
import datetime

REALES = {1: 146, 2: 203, 3: 258, 4: 218, 5: 211, 6: 203, 7: 173, 8: 150}
GASTO_META = 2_640_018
GASTO_GOOGLE = 719_600
META_DIARIA = 255
TOTAL_MES = 13_000_000
DIAS_MES = 30

gasto = GASTO_META + GASTO_GOOGLE
sol = sum(REALES.values())
print("=== 1 al 8 de noviembre, lo que de verdad paso ===")
print("  solicitudes            {:>10,}   ({:.1f} por dia)".format(sol, sol / 8))
print("  inversion              {:>10,}   (Meta {:,} + Google {:,})".format(
    gasto, GASTO_META, GASTO_GOOGLE))
print("  costo por solicitud    {:>10,.0f}".format(gasto / sol))
print("  meta diaria            {:>10,}   faltan {:.0f} por dia".format(
    META_DIARIA, META_DIARIA - sol / 8))
print("  presupuesto consumido  {:>9.1f}%   del mes va {:.1f}%".format(
    gasto / TOTAL_MES * 100, 8 / DIAS_MES * 100))

DIAS = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]
# Hay dos domingos en la muestra (el 1 y el 8): se promedian, no se pisa uno.
_acum = {}
for d, v in REALES.items():
    _acum.setdefault(datetime.date(2026, 11, d).weekday(), []).append(v)
por_dia = dict((w, sum(L) / len(L)) for w, L in _acum.items())
print("\n=== Por dia de semana (el 2 fue festivo) ===")
for i in range(7):
    print("  %s  %6.1f%s" % (DIAS[i], por_dia[i],
          "   (festivo)" if i == 0 else "   (promedio de los dos domingos)" if i == 6 else ""))

cuenta = {}
for d in range(1, DIAS_MES + 1):
    w = datetime.date(2026, 11, d).weekday()
    cuenta[w] = cuenta.get(w, 0) + 1
proy = sum(cuenta[w] * por_dia[w] for w in cuenta)
meta_mes = META_DIARIA * DIAS_MES
print("\n=== Proyeccion del mes al ritmo actual ===")
print("  (cada dia de semana se repite segun el calendario de noviembre)")
print("  proyeccion             {:>10,.0f}".format(proy))
print("  meta del mes           {:>10,}".format(meta_mes))
print("  diferencia             {:>10,.0f}   ({:.0f}% de la meta)".format(
    proy - meta_mes, proy / meta_mes * 100))

costo = gasto / sol
faltan = meta_mes - proy
print("\n  para cerrar la brecha hacen falta {:,.0f} solicitudes mas".format(faltan))
print("  al costo actual de {:,.0f} son {:,.0f} adicionales".format(costo, faltan * costo))
print("  presupuesto necesario {:,.0f}".format(TOTAL_MES + faltan * costo))

restante = TOTAL_MES - gasto
print("\n=== Lo que queda de los 13 millones ===")
print("  quedan {:,.0f} para {} dias = {:,.0f} por dia".format(
    restante, DIAS_MES - 8, restante / (DIAS_MES - 8)))
print("  ritmo actual {:,.0f} por dia -> sobran {:,.0f} por dia sin usar".format(
    gasto / 8, restante / (DIAS_MES - 8) - gasto / 8))
