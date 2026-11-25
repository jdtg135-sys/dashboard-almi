# -*- coding: utf-8 -*-
"""Hay un quiebre estructural el 30 de septiembre: el cotizador nuevo.

La correlacion entre inversion y costo en la serie completa es 0,391: demasiado
baja para sacar una elasticidad de ahi. Casi toda la variacion la explica un
salto de nivel a finales de septiembre, no el tamano de la inversion. El
30-sep-2026 entro en produccion el cotizador nuevo en Next.js.
"""
import json, datetime, math
from collections import defaultdict

d = json.load(open('ads_data.json', encoding='utf-8'))
meta = {x['fecha']: x for x in d['meta_ads']['diario']}
goo = {x['fecha']: x for x in d['google_ads']['diario']}
dias = sorted(set(meta) | set(goo))
CORTE = '2026-09-30'


def agrega(desde, hasta):
    g = s = n = 0
    for f in dias:
        if not (desde <= f <= hasta):
            continue
        g += meta.get(f, {}).get('inversion', 0) + goo.get(f, {}).get('inversion', 0)
        s += meta.get(f, {}).get('resultados', 0) + goo.get(f, {}).get('conversiones', 0)
        n += 1
    return g, s, n


print("=== Antes y despues del cotizador nuevo (30-sep-2026) ===")
print("%-28s %13s %9s %10s %11s %9s" % (
    "periodo", "inversion", "solic.", "costo", "inv/dia", "sol/dia"))
for etq, a, b in (("Jun 9 - Sep 29 (viejo)", "2026-06-09", "2026-09-29"),
                  ("Oct 1 - Nov 11 (nuevo)", "2026-10-01", "2026-11-11")):
    g, s, n = agrega(a, b)
    print("%-28s %13s %9.0f %10s %11s %9.1f" % (
        etq, format(int(g), ","), s, format(int(g / s) if s else 0, ","),
        format(int(g / n), ","), s / n))

print()
print("  La inversion diaria casi no cambio. Las solicitudes atribuidas por dia")
print("  cayeron a menos de la mitad y el costo se duplico, en la misma semana")
print("  en que entro el cotizador nuevo.")
print()

print("=== Elasticidad DENTRO de cada regimen ===")
print("Separarlos es la unica forma de medir el efecto del tamano de la")
print("inversion sin que lo contamine el salto de nivel.")
print()
sem = defaultdict(lambda: [0, 0, 0, None])
for f in dias:
    if f < '2026-06-09':
        continue
    iso = datetime.date.fromisoformat(f).isocalendar()
    k = "%d-S%02d" % (iso[0], iso[1])
    sem[k][0] += meta.get(f, {}).get('inversion', 0) + goo.get(f, {}).get('inversion', 0)
    sem[k][1] += meta.get(f, {}).get('resultados', 0) + goo.get(f, {}).get('conversiones', 0)
    sem[k][2] += 1
    sem[k][3] = 'nuevo' if f > CORTE else ('viejo' if f < CORTE else sem[k][3] or 'mixto')

for regimen in ('viejo', 'nuevo'):
    pts = [(v[0] / 7, v[0] / v[1]) for k, v in sorted(sem.items())
           if v[2] == 7 and v[3] == regimen and v[1] > 0]
    if len(pts) < 4:
        print("  %s: solo %d semanas completas, insuficiente" % (regimen, len(pts)))
        continue
    xs = [math.log(p[0]) for p in pts]
    ys = [math.log(p[1]) for p in pts]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    sx = math.sqrt(den / n)
    sy = math.sqrt(sum((y - my) ** 2 for y in ys) / n)
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (n * sx * sy)
    print("  cotizador %-6s  %2d semanas  b = %+.3f   r = %+.3f   al doblar: %+.0f%%"
          % (regimen, n, b, r, (2 ** b - 1) * 100))
    print("                    rango de inversion diaria: %s a %s"
          % (format(int(min(p[0] for p in pts)), ","),
             format(int(max(p[0] for p in pts)), ",")))
