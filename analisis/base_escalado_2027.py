# -*- coding: utf-8 -*-
"""Base de datos para el plan de escalado a 1.000 solicitudes diarias (11-nov-2026).

La medicion de conversion por solicitud arranco el 9 de junio de 2026, asi que
todo lo anterior se descarta: los resultados de mayo y de la primera semana de
junio no son comparables.
"""
import json, datetime
from collections import defaultdict

d = json.load(open('ads_data.json', encoding='utf-8'))
INICIO = '2026-06-09'

meta = {x['fecha']: x for x in d['meta_ads']['diario'] if x['fecha'] >= INICIO}
goo = {x['fecha']: x for x in d['google_ads']['diario'] if x['fecha'] >= INICIO}
dias = sorted(set(meta) | set(goo))
print("Ventana util: %s a %s  (%d dias)" % (dias[0], dias[-1], len(dias)))
print()

mes = defaultdict(lambda: [0, 0, 0, 0, 0])   # gasto_m, sol_m, gasto_g, sol_g, dias
for f in dias:
    m, g = meta.get(f, {}), goo.get(f, {})
    k = f[:7]
    mes[k][0] += m.get('inversion', 0)
    mes[k][1] += m.get('resultados', 0)
    mes[k][2] += g.get('inversion', 0)
    mes[k][3] += g.get('conversiones', 0)
    mes[k][4] += 1

print("=== Por mes (atribuido por las plataformas) ===")
print("%-9s %5s %12s %8s %9s %12s %7s %9s %12s %8s %9s" % (
    "mes", "dias", "inv Meta", "sol", "costo", "inv Google", "conv", "costo",
    "inv TOTAL", "sol/dia", "costo"))
hist = []
for k in sorted(mes):
    gm, sm, gg, sg, nd = mes[k]
    tot_g, tot_s = gm + gg, sm + sg
    hist.append((k, nd, gm, sm, gg, sg, tot_g, tot_s))
    print("%-9s %5d %12s %8.0f %9s %12s %7.0f %9s %12s %8.1f %9s" % (
        k, nd, format(int(gm), ","), sm, format(int(gm / sm) if sm else 0, ","),
        format(int(gg), ","), sg, format(int(gg / sg) if sg else 0, ","),
        format(int(tot_g), ","), tot_s / nd,
        format(int(tot_g / tot_s) if tot_s else 0, ",")))

print()
print("=== Elasticidad: que pasa con el costo cuando sube la inversion ===")
print("Cada punto es una semana completa. Si el costo sube con la inversion,")
print("escalar cuesta mas que proporcionalmente y hay que preverlo.")
print()
sem = defaultdict(lambda: [0, 0, 0])
for f in dias:
    iso = datetime.date.fromisoformat(f).isocalendar()
    k = "%d-S%02d" % (iso[0], iso[1])
    sem[k][0] += meta.get(f, {}).get('inversion', 0) + goo.get(f, {}).get('inversion', 0)
    sem[k][1] += meta.get(f, {}).get('resultados', 0) + goo.get(f, {}).get('conversiones', 0)
    sem[k][2] += 1
filas = [(k, v[0], v[1], v[0] / v[1] if v[1] else 0)
         for k, v in sorted(sem.items()) if v[2] == 7]
print("%-9s %12s %8s %9s %10s" % ("semana", "inversion", "solic.", "costo", "inv/dia"))
for k, g, s, c in filas:
    print("%-9s %12s %8.0f %9s %10s" % (
        k, format(int(g), ","), s, format(int(c), ","), format(int(g / 7), ",")))

# Regresion simple log-log: costo = a * inversion^b
import math
xs = [math.log(g / 7) for k, g, s, c in filas if c > 0]
ys = [math.log(c) for k, g, s, c in filas if c > 0]
n = len(xs)
mx, my = sum(xs) / n, sum(ys) / n
b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
a = my - b * mx
# correlacion
sx = math.sqrt(sum((x - mx) ** 2 for x in xs) / n)
sy = math.sqrt(sum((y - my) ** 2 for y in ys) / n)
r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (n * sx * sy)
print()
print("  semanas completas analizadas: %d" % n)
print("  elasticidad b = %.3f   (costo ~ inversion_diaria^b)" % b)
print("  correlacion r = %.3f" % r)
print("  lectura: al DOBLAR la inversion diaria, el costo por solicitud")
print("           se multiplica por %.3f (+%.0f%%)" % (2 ** b, (2 ** b - 1) * 100))
