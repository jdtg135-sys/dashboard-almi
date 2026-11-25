# -*- coding: utf-8 -*-
"""Reparto optimo de presupuesto entre canales para 1.000 solicitudes diarias.

EL MODELO
---------
Cada canal tiene su propia curva de rendimientos decrecientes:

    costo(S) = CPA0 * (S / S0) ^ b        ->    volumen(S) = k * S^(1-b)
    con k = S0^b / CPA0

El reparto optimo NO es proporcional cuando las elasticidades difieren: hay que
igualar el RENDIMIENTO MARGINAL de cada canal, es decir la solicitud numero
siguiente debe costar lo mismo en todos. Se resuelve buscando el multiplicador
lambda tal que

    S_i = ( (1-b_i) * k_i / lambda ) ^ (1/b_i)

y se recorta cada canal en su tope de mercado. (Un primer intento uso reparto
proporcional y le asigno cero a busqueda: con b distintos esa formula no vale.)

LAS ELASTICIDADES
-----------------
  b = 0,29 en los canales de interrupcion. Medido en la cuenta, por separado en
  las dos versiones del cotizador: 0,294 y 0,287.

  b = 0,10 en busqueda. Ahi tomamos solo el 10% de las impresiones disponibles,
  asi que el presupuesto adicional compra inventario que hoy se nos escapa, no
  inventario peor. El costo sube mucho menos hasta que sature.

LOS CPA
-------
  Meta y busqueda: MEDIDOS del 1 al 11 de noviembre contra el conteo real de
  ALMI, no el atribuido (que subcuenta un 34%).
  El resto: SUPUESTOS. Cada uno lleva prueba presupuestada en el plan.
"""
import math

META_DIARIA = 1000
HOY_INV, HOY_SOL = 430_000, 195

#            nombre,                   CPA0,      S0,  tope/dia, medido, b
CANALES = [
    ("Meta · conversiones",           1_964,  330_000,  450, True,  0.29),
    ("Google · búsqueda",             3_222,   87_000,  160, True,  0.10),
    ("TikTok · conversiones",         2_750,  100_000,  200, False, 0.29),
    ("Google · Demand Gen",           2_950,  100_000,  150, False, 0.29),
    ("YouTube · acción en video",     3_200,  100_000,  120, False, 0.29),
]
# Fuera del plan por decision del cliente (11-nov-2026): CRM propio, correo,
# WhatsApp y referidos. El plan es solo de medios pagados. Eran los dos canales
# mas baratos (CPA 508 y 1.144) y aportaban 100 solicitudes diarias de techo,
# asi que sacarlos encarece el conjunto y acerca la meta al limite.
#   ("CRM propio · correo y WhatsApp",  450,   20_000,   60, False, 0.29),
#   ("Referidos",                       900,   20_000,   40, False, 0.29),

K = [(n, (s0 ** b) / cpa, tope, b, med, cpa) for n, cpa, s0, tope, med, b in CANALES]


def asignar(lmb):
    """Dado el costo marginal objetivo lambda, cuanto gasta y produce cada canal."""
    out = []
    for n, k, tope, b, med, cpa0 in K:
        s = ((1 - b) * k / lmb) ** (1 / b)
        q = k * s ** (1 - b)
        if q > tope:                      # el mercado se acaba antes
            q = tope
            s = (tope / k) ** (1 / (1 - b))
        out.append((n, s, q, (s / q if q else 0), tope))
    return out


# lambda alto = poco volumen. Se busca el lambda que da exactamente la meta.
lo, hi = 1e-9, 1.0
for _ in range(200):
    mid = math.sqrt(lo * hi)
    if sum(x[2] for x in asignar(mid)) > META_DIARIA:
        lo = mid
    else:
        hi = mid
plan = asignar(math.sqrt(lo * hi))
total_inv = sum(x[1] for x in plan)
total_sol = sum(x[2] for x in plan)

print("=" * 88)
print("SUPUESTOS DE PARTIDA")
print("=" * 88)
print("%-32s %9s %9s %9s %6s  %s" % ("canal", "CPA", "tope/día", "inv.ref", "b", "origen"))
for n, cpa, s0, tope, med, b in CANALES:
    print("%-32s %9s %9d %9s %6.2f  %s" % (
        n, format(cpa, ","), tope, format(s0, ","), b,
        "MEDIDO" if med else "supuesto · hay que probarlo"))
print()
print("  Suma de los topes: %d solicitudes diarias." % sum(c[3] for c in CANALES))
print("  La meta de 1.000 esta al %.0f%% del techo de este conjunto de canales."
      % (META_DIARIA / sum(c[3] for c in CANALES) * 100))

print()
print("=" * 88)
print("REPARTO ÓPTIMO PARA %d SOLICITUDES DIARIAS" % META_DIARIA)
print("=" * 88)
print("%-32s %12s %7s %10s %9s %6s" % (
    "canal", "inv/día", "share", "solic/día", "CPA", "tope"))
print("-" * 88)
for n, s, q, cpa, tope in sorted(plan, key=lambda x: -x[1]):
    print("%-32s %12s %6.1f%% %10.0f %9s %6s" % (
        n, format(int(s), ","), s / total_inv * 100, q,
        format(int(cpa), ",") if q else "-",
        "TOPE" if abs(q - tope) < 0.5 else ""))
print("-" * 88)
print("%-32s %12s %6.1f%% %10.0f %9s" % (
    "TOTAL", format(int(total_inv), ","), 100, total_sol,
    format(int(total_inv / total_sol), ",")))
print()
print("  inversión mensual      %s" % format(int(total_inv * 30), ","))
print("  hoy                    %s diarios para %d solicitudes"
      % (format(HOY_INV, ","), HOY_SOL))
print("  multiplicador          x%.1f en inversión para x%.1f en volumen"
      % (total_inv / HOY_INV, total_sol / HOY_SOL))

print()
print("=" * 88)
print("CUÁNTO AHORRA ABRIR CANALES")
print("=" * 88)
solo = 4_299_517     # calculado antes: todo sobre Meta y busqueda con b=0,29
print("  concentrado en los canales de hoy   %13s diarios" % format(solo, ","))
print("  repartido en los siete canales      %13s diarios" % format(int(total_inv), ","))
print("  ahorro                              %13s diarios · %s al mes"
      % (format(int(solo - total_inv), ","), format(int((solo - total_inv) * 30), ",")))


print()
print("=" * 88)
print("RAMPA TRIMESTRAL: que entrega cada nivel de inversion")
print("=" * 88)


def volumen_con(presupuesto):
    lo, hi = 1e-9, 1.0
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if sum(x[1] for x in asignar(mid)) > presupuesto:
            lo = mid
        else:
            hi = mid
    pl = asignar(math.sqrt(lo * hi))
    return pl, sum(x[2] for x in pl)


print("%-11s %13s %14s %11s %9s" % ("tramo", "inv/día", "inv/mes", "solic/día", "CPA"))
print("-" * 64)
for etq, inv in (("Hoy", 430_000), ("Q1 2027", 900_000), ("Q2 2027", 1_600_000),
                 ("Q3 2027", 2_400_000), ("Q4 2027", int(total_inv))):
    pl, q = volumen_con(inv)
    print("%-11s %13s %14s %11.0f %9s" % (
        etq, format(inv, ","), format(inv * 30, ","), q, format(int(inv / q), ",")))

print()
print("Detalle del reparto en cada tramo (inversión diaria por canal):")
print("%-32s %11s %11s %11s %11s" % ("canal", "Q1", "Q2", "Q3", "Q4"))
print("-" * 80)
tramos = [volumen_con(x)[0] for x in (900_000, 1_600_000, 2_400_000, int(total_inv))]
for i, (n, _, _, _, _) in enumerate(plan):
    fila = [next(x[1] for x in t if x[0] == n) for t in tramos]
    print("%-32s %11s %11s %11s %11s" % (
        n, *[format(int(v), ",") for v in fila]))
