# -*- coding: utf-8 -*-
"""Organiza las piezas de pauta de ALMI en carpetas por concepto.

Cada concepto son 3 archivos consecutivos: n=cuadrado, n+1=vertical, n+2=horizontal.
Estructura destino:  <Sector>/<NNN_slug>/<NNN_formato_WxH>.png
Escribe un manifiesto CSV que permite revertir el movimiento exactamente.
"""
import os, shutil, csv, sys

BASE = r"C:\Users\juanc\OneDrive\Documentos\Clientes\ALMI Financiera\Pauta Almi"

GEN = "00 Genericas"
SEG = "01 Seguridad y vigilancia"
TEM = "02 Temporales y servicios"
RES = "03 Restaurantes y alimentos"
RET = "04 Retail y moda"
FIN = "05 Financiero y seguros"
SAL = "06 Salud y bienestar"
BPO = "07 BPO y tecnologia"
IND = "08 Industria y automotriz"

# n -> (sector, slug)   slug con prefijo REVISAR_ = incumple el brief (voseo)
C = {
    4:   (GEN, "ya-reclamaste-tu-cupo"),
    7:   (GEN, "miles-lo-pidieron-6-meses"),
    10:  (GEN, "el-banco-demora-nosotros-dias"),
    13:  (GEN, "el-banco-te-pidio-demasiado"),
    16:  (GEN, "tu-trabajo-es-tu-garantia"),
    19:  (GEN, "REVISAR_para-que-queres-tu-plata"),
    22:  (GEN, "credito-si-almi-tiene-el-tuyo"),
    25:  (GEN, "tu-empresa-ya-tiene-convenio"),
    28:  (GEN, "miles-de-privados-ya-lo-tienen"),
    31:  (GEN, "REVISAR_empresa-privada-calificas"),
    34:  (GEN, "credito-sin-banco-lo-sabias"),
    37:  (GEN, "REVISAR_trabajas-tu-nomina-trabaja"),
    40:  (GEN, "todo-lo-pide-el-banco-almi-lo-hace-facil"),
    43:  (GEN, "REVISAR_trabajas-y-quieres-un-empujon"),
    46:  (GEN, "sin-banco-solo-trabajar"),
    49:  (GEN, "REVISAR_queres-credito-sin-tanto-complique"),
    52:  (GEN, "por-que-el-banco-pide-tanto"),
    55:  (GEN, "REVISAR_tu-trabajo-habla-por-vos"),

    97:  (SEG, "delthac-seguridad"),
    100: (SEG, "atlantica-seguridad"),
    103: (SEG, "serviconfor"),
    106: (SEG, "alpha-seguridad-privada"),
    109: (SEG, "servigpoder"),
    112: (SEG, "andina-seguridad"),
    115: (SEG, "avizor-seguridad"),
    118: (SEG, "cvs-colviseg"),
    121: (SEG, "nueva-era-seguridad"),
    124: (SEG, "fortox-security-group"),
    127: (SEG, "sevicol"),
    130: (SEG, "andiseg"),

    247: (TEM, "summar-productividad"),
    250: (TEM, "brillaseo"),
    253: (TEM, "casalimpia"),
    256: (TEM, "tu-temporal"),
    259: (TEM, "temporizar"),
    262: (TEM, "temporales-plus"),
    268: (TEM, "asservi"),
    271: (TEM, "interaseo"),
    277: (TEM, "listos"),

    169: (RES, "el-corral"),
    172: (RES, "ramo"),
    175: (RES, "frisby"),
    178: (RES, "citadino-gastro-bar"),
    181: (RES, "el-corral-gourmet"),
    184: (RES, "martin-birrieria"),
    187: (RES, "penelope-martini"),
    190: (RES, "papa-johns"),
    193: (RES, "raca-man-dapa"),
    196: (RES, "sr-wok"),
    202: (RES, "anttoninas-cocina-natural"),
    205: (RES, "gios-pizza"),
    208: (RES, "natura-foods"),
    211: (RES, "el-gringo-american-kitchen"),
    229: (RES, "postobon"),

    58:  (RET, "tennis"),
    61:  (RET, "h-y-m"),
    64:  (RET, "calzatodo"),
    67:  (RET, "pricesmart"),
    73:  (RET, "beauty-studio"),
    199: (RET, "ava"),

    70:  (FIN, "acertemos"),
    76:  (FIN, "banco-caja-social"),
    79:  (FIN, "coomeva"),
    82:  (FIN, "mundo-mujer"),
    85:  (FIN, "davivienda"),
    160: (FIN, "cifin"),
    226: (FIN, "axa-colpatria"),

    88:  (SAL, "farmatodo"),
    91:  (SAL, "cruz-verde"),
    94:  (SAL, "smart-fit"),
    232: (SAL, "christus-sinergia-salud"),

    148: (BPO, "groupcos"),
    151: (BPO, "foundever"),
    154: (BPO, "siigo"),
    157: (BPO, "bold"),
    163: (BPO, "grupo-cinte"),
    166: (BPO, "ciber-c"),
    223: (BPO, "abai"),
    265: (BPO, "iztech"),

    214: (IND, "autopacifico-chevrolet"),
    217: (IND, "almotores-kia"),
    220: (IND, "ladrillera-el-ajizal"),
    235: (IND, "altipal"),
    238: (IND, "aritex"),
    241: (IND, "atsa"),
    244: (IND, "plastypetco"),
    274: (IND, "lineas-del-valle"),
}

FORMATOS = [(0, "cuadrado", "1080x1080"), (1, "vertical", "1080x1920"), (2, "horizontal", "1200x628")]

DRY = "--go" not in sys.argv


def main():
    existentes = {int(os.path.splitext(f)[0]) for f in os.listdir(BASE)
                  if f.lower().endswith(".png") and os.path.splitext(f)[0].isdigit()}

    faltan = [n for n in C for off, _, _ in FORMATOS if n + off not in existentes]
    if faltan:
        print("ATENCION, faltan archivos para:", sorted(set(faltan)))
    sin_mapear = existentes - {n + off for n in C for off, _, _ in FORMATOS}
    if sin_mapear:
        print("ATENCION, archivos sin mapear:", sorted(sin_mapear))

    filas = []
    for n in sorted(C):
        sector, slug = C[n]
        carpeta = os.path.join(BASE, sector, f"{n:03d}_{slug}")
        for off, nombre, dim in FORMATOS:
            src = os.path.join(BASE, f"{n + off}.png")
            dst = os.path.join(carpeta, f"{n + off:03d}_{nombre}_{dim}.png")
            filas.append((f"{n + off}.png", os.path.relpath(dst, BASE)))
            if DRY:
                continue
            os.makedirs(carpeta, exist_ok=True)
            if os.path.exists(dst):
                print("  ya existe, se omite:", dst)
                continue
            shutil.move(src, dst)

    if DRY:
        print(f"\nSIMULACION: {len(C)} conceptos, {len(filas)} archivos.")
        for f in filas[:6]:
            print("   ", f[0], "->", f[1])
        print("    ...")
        print("Ejecutar con --go para aplicar.")
        return

    man = os.path.join(BASE, "_manifiesto_organizacion.csv")
    with open(man, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["origen_plano", "destino_relativo"])
        w.writerows(filas)
    print(f"\nListo: {len(C)} conceptos, {len(filas)} archivos movidos.")
    print("Manifiesto:", man)


if __name__ == "__main__":
    main()
