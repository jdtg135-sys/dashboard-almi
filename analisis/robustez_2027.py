# -*- coding: utf-8 -*-
"""Robustez del plan 2027 (17-nov-2026): backtest, simulacion y plan por canal.

Tres bloques:
  1. BACKTEST: entrenar la curva costo-inversion con semanas de inversion baja y
     predecir las de inversion alta. Compara contra el ingenuo (costo constante).
  2. SIMULACION: mover a la vez eficiencia recuperada (g), elasticidad, CPA de los
     canales sin medir, techos de mercado y si cada canal nuevo pasa la validacion.
     Devuelve percentiles del presupuesto y probabilidad de llegar a 1.000.
  3. PLAN POR CANAL mes a mes (escenario base) con entrada escalonada de canales.

Se corre desde la carpeta del dashboard:  python analisis/robustez_2027.py
"""
import json, math, random, datetime, statistics
from collections import defaultdict

random.seed(2027)
d = json.load(open('ads_data.json', encoding='utf-8'))
meta = {x['fecha']: x for x in d['meta_ads']['diario']}
goo = {x['fecha']: x for x in d['google_ads']['diario']}

# ---------------------------------------------------------------- 1. BACKTEST
sem = defaultdict(lambda: [0, 0, 0])
for f in sorted(set(meta) | set(goo)):
    if f < '2026-06-09':
        continue
    iso = datetime.date.fromisoformat(f).isocalendar()
    k = (iso[0], iso[1])
    sem[k][0] += meta.get(f, {}).get('inversion', 0) + goo.get(f, {}).get('inversion', 0)
    sem[k][1] += meta.get(f, {}).get('resultados', 0) + goo.get(f, {}).get('conversiones', 0)
    sem[k][2] += 1
LIMPIAS = [(k[1], v[0] / 7, v[0] / v[1]) for k, v in sorted(sem.items())
           if v[2] == 7 and 26 <= k[1] <= 37 and v[1] > 0]       # S26-S37
entren = [x for x in LIMPIAS if x[1] < 300_000]
prueba = [x for x in LIMPIAS if x[1] >= 300_000]


def ajustar(pts):
    xs = [math.log(p[1]) for p in pts]; ys = [math.log(p[2]) for p in pts]
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return b, my - b * mx


b_bt, a_bt = ajustar(entren)
print("BACKTEST (semanas limpias S26-S37)")
print("  entrenamiento: %d semanas con inversion < 300.000/dia  -> b=%.2f" % (len(entren), b_bt))
print("  prueba: %d semanas con inversion >= 300.000/dia" % len(prueba))
cost_const = statistics.mean(p[2] for p in entren)
err_m, err_c = [], []
for s, inv, c in prueba:
    pred = math.exp(a_bt) * inv ** b_bt
    err_m.append(abs(pred - c) / c); err_c.append(abs(cost_const - c) / c)
    print("   S%02d inv/dia %7s  real %5d  curva %5d  constante %5d" % (
        s, format(int(inv), ","), c, pred, cost_const))
print("  error medio curva %.0f%%  |  error medio costo constante %.0f%%" % (
    100 * statistics.mean(err_m), 100 * statistics.mean(err_c)))
print("  rango de inversion en el que se valida: %s a %s por dia" % (
    format(int(min(p[1] for p in LIMPIAS)), ","), format(int(max(p[1] for p in LIMPIAS)), ",")))

# --------------------------------------------------------------- 2. SIMULACION
# canal: (nombre, CPA0 real, S0 referencia, techo/dia, b relativo, medido, p_validacion)
BASE = [
    ("Meta",               1964, 330_000, 450, 1.0, True,  1.0),
    ("Google búsqueda",    3222,  87_000, 160, 0.5, True,  1.0),
    ("TikTok",             2750, 100_000, 200, 1.0, False, 0.65),
    ("Demand Gen",         2950, 100_000, 150, 1.0, False, 0.60),
    ("YouTube",            3200, 100_000, 120, 1.0, False, 0.50),
    ("Otras plataformas",  3500,  60_000,  80, 1.0, False, 0.50),
]


# Piso: la busqueda de mayor intencion no se recorta por debajo de hoy (decision del plan)
PISO = {"Google búsqueda": 86_000}


def curva(cpa0, s0, b):
    return (s0 ** b) / cpa0


def asignar(lmb, canales):
    tot_s = tot_q = 0.0
    det = []
    for n, k, tope, b, piso in canales:
        if tope <= 0:
            det.append((n, 0.0, 0.0)); continue
        s = max(((1 - b) * k / lmb) ** (1 / b), piso)
        q = k * s ** (1 - b)
        if q > tope:
            q, s = tope, (tope / k) ** (1 / (1 - b))
        tot_s += s; tot_q += q; det.append((n, s, q))
    return tot_s, tot_q, det


def presupuesto_para(meta_q, canales):
    if sum(c[2] for c in canales) < meta_q:
        return None
    lo, hi = 1e-12, 10.0
    for _ in range(120):
        mid = math.sqrt(lo * hi)
        if asignar(mid, canales)[1] > meta_q: lo = mid
        else: hi = mid
    return asignar(math.sqrt(lo * hi), canales)


def volumen_con(presu, canales):
    lo, hi = 1e-12, 10.0
    for _ in range(120):
        mid = math.sqrt(lo * hi)
        if asignar(mid, canales)[0] > presu: lo = mid
        else: hi = mid
    return asignar(math.sqrt(lo * hi), canales)


def armar(g, b_int, f_nuevos, f_techo, valida):
    can = []
    for n, cpa, s0, tope, brel, med, p in BASE:
        b = max(0.05, b_int * brel)
        f = 1.0 if med else f_nuevos
        t = tope * f_techo * (1 if (med or valida.get(n, True)) else 0)
        can.append((n, curva(cpa * f / g, s0, b), t, b, PISO.get(n, 0)))
    return can


def tri(a, m, b):
    return random.triangular(a, b, m)


import os
N = int(os.environ.get('N', '4000'))
res = []
for _ in range(N):
    g = tri(1.0, 1.5, 2.35)
    b_int = tri(0.10, 0.20, 0.35)
    f_nuevos = math.exp(random.gauss(0, 0.30))
    f_techo = tri(0.7, 1.0, 1.4)
    valida = {n: (random.random() < p) for n, _, _, _, _, med, p in BASE if not med}
    can = armar(g, b_int, f_nuevos, f_techo, valida)
    r = presupuesto_para(1000, can)
    res.append((g, b_int, f_nuevos, f_techo, valida, can, r))

ok = [x for x in res if x[6]]
mens = sorted(x[6][0] * 30 / 1e6 for x in ok)


def pct(v, p):
    return v[int(p * (len(v) - 1))]


print()
print("SIMULACION (%d combinaciones de supuestos)" % N)
print("  llegan a 1.000 con los techos de mercado: %.0f%%" % (100 * len(ok) / N))
print("  inversion mensual necesaria en oct-2027 (solo las que llegan):")
for p in (0.10, 0.25, 0.50, 0.75, 0.90):
    print("    P%d  %6.1f M" % (p * 100, pct(mens, p)))
print()
print("  PROBABILIDAD DE LLEGAR A 1.000 SEGUN EL PRESUPUESTO MENSUAL DE OCTUBRE")
print("  %8s %12s %12s %12s" % ("M/mes", "P(>=1000)", "mediana", "P10-P90"))
salida_prob = {}
for M in (40, 60, 80, 100, 118, 140):
    vols = []
    for g, b_int, fn, ft, val, can, r in res:
        vols.append(volumen_con(M * 1e6 / 30, can)[1])
    vols.sort()
    p1000 = sum(1 for v in vols if v >= 1000) / N
    salida_prob[M] = (p1000, pct(vols, .5), pct(vols, .1), pct(vols, .9))
    print("  %8d %11.0f%% %12.0f %6.0f-%.0f" % (M, 100 * p1000, pct(vols, .5),
                                              pct(vols, .1), pct(vols, .9)))

print()
print("  SENSIBILIDAD: cuanto mueve cada supuesto el presupuesto (resto en su valor central)")
centro = dict(g=1.5, b_int=0.20, f_nuevos=1.0, f_techo=1.0)
todos_validan = {n: True for n, _, _, _, _, med, _ in BASE if not med}
ninguno = {n: False for n in todos_validan}


def mensual(**kw):
    c = dict(centro); c.update(kw)
    val = kw.pop('valida', todos_validan) if 'valida' in kw else todos_validan
    c.pop('valida', None)
    r = presupuesto_para(1000, armar(c['g'], c['b_int'], c['f_nuevos'], c['f_techo'], val))
    return None if not r else r[0] * 30 / 1e6


base_m = mensual()
print("  centro (g 1,5 · b 0,20 · todos validan): %.1f M" % base_m)
for etq, kw in (("g = 1,0 (nada se recupera)", dict(g=1.0)),
                ("g = 2,35 (vuelve a ago-sep)", dict(g=2.35)),
                ("elasticidad 0,35", dict(b_int=0.35)),
                ("elasticidad 0,10", dict(b_int=0.10)),
                ("canales nuevos 40% mas caros", dict(f_nuevos=1.4)),
                ("canales nuevos 30% mas baratos", dict(f_nuevos=0.7)),
                ("techos 30% menores", dict(f_techo=0.7)),
                ("techos 40% mayores", dict(f_techo=1.4))):
    m = mensual(**kw)
    print("   %-34s %s" % (etq, ("%.1f M" % m) if m else "no llega (techo)"))
for etq, v in (("solo Meta y Google (ningun canal nuevo valida)", ninguno),):
    m = mensual(valida=v)
    print("   %-34s %s" % (etq, ("%.1f M" % m) if m else "no llega (techo)"))

print()
print("  QUE PASA SI FALLAN CANALES NUEVOS (resto central)")
for etq, falla in (("falla TikTok", ["TikTok"]), ("falla Demand Gen", ["Demand Gen"]),
                   ("falla YouTube", ["YouTube"]), ("fallan Otras plataformas", ["Otras plataformas"]),
                   ("fallan TikTok y YouTube", ["TikTok", "YouTube"]),
                   ("fallan los tres de video/social", ["TikTok", "Demand Gen", "YouTube"])):
    v = {n: (n not in falla) for n in todos_validan}
    can = armar(1.5, 0.20, 1.0, 1.0, v)
    techo = sum(c[2] for c in can)
    m = mensual(valida=v)
    mx = volumen_con(1e12, can)[1]
    print("   %-34s techo %4.0f/dia  %s  (volumen maximo %.0f)" % (etq, techo, ("%.1f M" % m) if m else "no llega", mx))

print()
print("  FACTIBILIDAD SEGUN EL TECHO DE MERCADO (resto en valor central)")
for ft in (0.7, 0.8, 0.86, 0.9, 1.0, 1.2, 1.4):
    m = mensual(f_techo=ft)
    print("   techos x%.2f (suman %4.0f/dia)  %s" % (ft, ft * sum(b[3] for b in BASE),
          ("%.1f M" % m) if m else "no llega"))

# ----------------------------------------------------------- 3. PLAN POR CANAL
print()
print("PLAN POR CANAL, ESCENARIO BASE (g hasta 1,5 · b 0,20)")
MESES = ["Nov", "Dic", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct"]
SOL = [195, 230, 300, 380, 470, 560, 650, 740, 830, 900, 960, 1000]
G = [1.0, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5]
# mes de arranque de la prueba y rampa de techo (25/50/75/100%) tras validar
ENTRADA = {"TikTok": 3, "Demand Gen": 4, "YouTube": 5, "Otras plataformas": 7}
filas = []
print("%-4s %6s %9s | %s" % ("mes", "sol", "inv/mes", " ".join("%-8s" % n[:8] for n, *_ in BASE)))
for i, (m, q, g) in enumerate(zip(MESES, SOL, G)):
    can = []
    for n, cpa, s0, tope, brel, med, p in BASE:
        b = max(0.05, 0.20 * brel)
        if med:
            t = tope
        else:
            desde = ENTRADA[n]
            t = 0 if i < desde else tope * min(1.0, 0.25 * (i - desde + 1))
        can.append((n, curva(cpa / g, s0, b), t, b, PISO.get(n, 0)))
    if i == 0:
        r = (430_000, 195, [("Meta", 343_000, 168), ("Google búsqueda", 87_000, 27)] + [(n, 0, 0) for n, *_ in BASE[2:]])
    else:
        r = presupuesto_para(q, can)
    if r is None:
        # techo del mes: lo maximo que se puede producir
        r = volumen_con(1e12, can)
        etiqueta = "TECHO %.0f" % r[1]
    else:
        etiqueta = ""
    filas.append((m, q, r[0] * 30 / 1e6, r[2]))
    print("%-4s %6.0f %8.1fM | %s %s" % (m, r[1], r[0] * 30 / 1e6,
          " ".join("%8.0f" % (x[1] / 1000) for x in r[2]), etiqueta))
print("  (columnas por canal: inversion diaria en miles de pesos)")
tot = sum(f[2] for f in filas[1:])
print("  acumulado dic-oct: %.0f M" % tot)

json.dump({"prob": {str(k): v for k, v in salida_prob.items()},
           "p": {str(p): pct(mens, p) for p in (.1, .25, .5, .75, .9)},
           "factibles": len(ok) / N,
           "plan": [(m, q, round(i, 1), [(n, round(s), round(qq, 1)) for n, s, qq in det]) for m, q, i, det in filas]},
          open('analisis/robustez_2027.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
