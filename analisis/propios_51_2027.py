# Efecto de canales propios (CRM, referidos, correo, WhatsApp, alianzas) sobre el plan
import random, math, json, os
src = open('analisis/robustez_2027.py', encoding='utf-8').read()
exec(src[:src.index('import os\nN =')])
random.seed(7)
N = int(os.environ.get('N', '3000'))
# costo por solicitud de propios: primeras 100/dia (CRM 508 + referidos 1.144) ~ 830 ; siguientes 100 (correo, WhatsApp, alianzas) supuesto 1.500
def costo_propios(O):
    return (min(O, 100) * 830 + max(0, min(O, 200) - 100) * 1500 + max(0, O - 200) * 2200)
NIVELES = [0, 100, 200]
res = []
for _ in range(N):
    g = tri(1.0, 1.5, 2.35); b_int = tri(.10, .20, .35)
    fn = math.exp(random.gauss(0, .30)); ft = tri(.7, 1.0, 1.4)
    val = {n: (random.random() < p) for n, _, _, _, _, med, p in BASE if not med}
    k = tri(0.5, 1.0, 1.3)  # factor de cumplimiento de los propios
    res.append((armar(g, b_int, fn, ft, val), k, val))
def pc(v, p): v = sorted(v); return v[int(p * (len(v) - 1))]
out = {}
for O in NIVELES:
    row = {}
    for M in (51, 61):
        vols = []
        for can, k, val in res:
            Oe = O * k
            presu_paid = M * 1e6 / 30 - costo_propios(Oe)
            vols.append(volumen_con(presu_paid, can)[1] + Oe)
        row[M] = dict(p1000=sum(v >= 1000 for v in vols) / N, p850=sum(v >= 850 for v in vols) / N,
                      p700=sum(v >= 700 for v in vols) / N, med=pc(vols, .5), p10=pc(vols, .1), p90=pc(vols, .9))
    # sin TikTok (falla) a 61 M
    vols = []
    for can, k, val in res:
        can2 = [c if c[0] != 'TikTok' else (c[0], c[1], 0, c[3], c[4]) for c in can]
        Oe = O * k
        vols.append(volumen_con(51e6 / 30 - costo_propios(Oe), can2)[1] + Oe)
    row['sintiktok_p1000'] = sum(v >= 1000 for v in vols) / N
    row['sintiktok_med'] = pc(vols, .5)
    # presupuesto pagado necesario (central) para 1000-O
    g, b, fn, ft = 1.5, .20, 1.0, 1.0
    can = armar(g, b, fn, ft, {n: True for n, _, _, _, _, med, _ in BASE if not med})
    r = presupuesto_para(1000 - O, can)
    row['paid_central_M'] = r[0] * 30 / 1e6 if r else None
    row['propios_M'] = costo_propios(O) * 30 / 1e6
    out[O] = row
json.dump(out, open('analisis/propios_51_2027.json', 'w'), indent=1)
for O, r in out.items():
    print(O, json.dumps({k: (round(v, 2) if not isinstance(v, dict) else {a: round(b, 2) for a, b in v.items()}) for k, v in r.items()}))
