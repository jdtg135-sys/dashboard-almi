# -*- coding: utf-8 -*-
"""Refresca el publico BBDD GLOM con la base nueva de 67.221 contactos (11-nov-2026).

POR QUE SE ACTUALIZA EL PUBLICO EXISTENTE Y NO SE CREA UNO NUEVO
----------------------------------------------------------------
Crear un publico nuevo obliga a editar la segmentacion del conjunto para
meterlo, y eso Meta lo trata como edicion significativa: reinicia el
aprendizaje. Actualizar los miembros del publico que YA esta en la
segmentacion no toca el conjunto, asi que no hay reinicio. El ID sigue siendo
el mismo y la campana ni se entera.

Matiz honesto: la bandera de Meta no se mueve, pero pasar de ~20.000 a ~67.000
personas cambia a quien le entrega. El rendimiento se va a mover unos dias de
todas formas.

SE AGREGA, NO SE REEMPLAZA
--------------------------
Se hace POST de los contactos nuevos. Meta deduplica por hash, asi que los que
ya estaban no se duplican. No se borra a nadie: un DELETE masivo es
irreversible y los contactos de julio que no esten en la lista nueva no hacen
dano, solo envejecen. Si algun dia se quiere limpiar, se hace aparte y a
conciencia.

PRIVACIDAD
----------
Los datos personales NO salen en claro. Se normalizan y se cifran con SHA-256
en este equipo, como exige Meta, y solo viajan los hashes. El archivo original
no se copia al repositorio.

LO QUE ESTE SCRIPT NO ARREGLA
-----------------------------
La lista es "All Contacts" y no distingue quien ya es cliente. Mientras no
llegue el listado de clientes con credito vigente para cargarlo como
EXCLUSION, C4 le sigue mostrando anuncios de "solicita tu credito" a gente que
ya lo tiene. Eso es lo siguiente, junto con la division C1 / C2.

Uso:  python refrescar_bbdd_glom.py <ruta_csv>        -> simula
      python refrescar_bbdd_glom.py <ruta_csv> --go   -> lo aplica
"""
import csv, hashlib, json, os, re, sys, time, unicodedata, requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred = json.load(open(os.path.join(BASE, "meta_credentials.json")))
TOKEN = cred["access_token"]
G = "https://graph.facebook.com/v19.0"

PUBLICO = "120250780395030392"          # BBDD GLOM 01/07/2026
LOTE = 5_000

# REANUDABLE. Meta corta con el error 613 ("Daily limit for this API has been
# exceeded") cuando se le mandan muchos contactos seguidos; el 11-nov-2026 nos
# paro despues del primer lote de 5.000. El progreso queda en este archivo para
# poder continuar mas tarde sin reenviar lo ya cargado. Reenviar no duplicaria
# (Meta deduplica por hash) pero si quemaria cuota.
PROGRESO = os.path.join(BASE, "analisis", "refresco_bbdd_glom_progreso.json")
DRY = "--go" not in sys.argv
RUTA = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
if not RUTA:
    raise SystemExit("Falta la ruta del CSV.")


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def norm_nombre(s):
    # Meta pide minusculas, sin tildes, sin puntuacion ni espacios de sobra.
    s = sin_tildes(s.lower().strip())
    return re.sub(r"[^a-z]", "", s)


def norm_mail(s):
    s = s.strip().lower()
    return s if re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", s) else None


def norm_tel(s):
    # Solo digitos. Colombia: debe quedar 57 + celular de 10 digitos.
    d = re.sub(r"\D", "", s)
    if d.startswith("57") and len(d) == 12:
        return d
    if len(d) == 10 and d.startswith("3"):
        return "57" + d
    return None


filas, con_algo, descartados = 0, 0, {"sin_contacto": 0, "tel_malo": 0, "mail_malo": 0}
datos = []
with open(RUTA, encoding="utf-8-sig", errors="replace", newline="") as fh:
    r = csv.reader(fh, delimiter=";")
    next(r, None)
    for x in r:
        if len(x) < 6:
            continue
        emp, filtro, nom, ape, tel, mail = [y.strip() for y in x[:6]]
        if not (nom or tel or mail):
            continue
        filas += 1
        m, t = norm_mail(mail), norm_tel(tel)
        if mail and not m:
            descartados["mail_malo"] += 1
        if tel and not t:
            descartados["tel_malo"] += 1
        if not m and not t:
            descartados["sin_contacto"] += 1
            continue
        con_algo += 1
        datos.append([
            sha(m) if m else "",
            sha(t) if t else "",
            sha(norm_nombre(nom)) if norm_nombre(nom) else "",
            sha(norm_nombre(ape)) if norm_nombre(ape) else "",
            sha("co"),
        ])

ESQUEMA = ["EMAIL", "PHONE", "FN", "LN", "COUNTRY"]

info = requests.get("%s/%s" % (G, PUBLICO), params={
    "access_token": TOKEN,
    "fields": "name,subtype,approximate_count_lower_bound,time_updated"}).json()

print("Publico destino : %s  (%s)" % (info.get("name"), PUBLICO))
print("Archivo         : %s" % os.path.basename(RUTA))
print()
print("  contactos en el archivo      %8d" % filas)
print("  se envian                    %8d" % con_algo)
print("  descartados por no tener ni correo ni telefono usable: %d"
      % descartados["sin_contacto"])
print("     telefonos con formato invalido: %d" % descartados["tel_malo"])
print("     correos con formato invalido:   %d" % descartados["mail_malo"])
print()
print("  esquema enviado : %s" % ", ".join(ESQUEMA))
print("  cifrado         : SHA-256 en este equipo; no viaja ningun dato en claro")
print("  lotes           : %d de hasta %s" % (
    (len(datos) + LOTE - 1) // LOTE, format(LOTE, ",")))
print("  modo            : se AGREGA, no se reemplaza. No se borra a nadie.")

desde = 0
if os.path.exists(PROGRESO):
    desde = json.load(open(PROGRESO)).get("enviados", 0)
for a in sys.argv[1:]:
    if a.startswith("--desde="):
        desde = int(a.split("=", 1)[1])
if desde:
    print("  REANUDANDO: ya van %s, faltan %s"
          % (format(desde, ","), format(max(len(datos) - desde, 0), ",")))

if DRY:
    print("")
    print("SIMULACION. Ejecutar con --go para enviarlo.")
    raise SystemExit

i = desde
while i < len(datos):
    trozo = datos[i:i + LOTE]
    r = requests.post("%s/%s/users" % (G, PUBLICO), data={
        "access_token": TOKEN,
        "payload": json.dumps({"schema": ESQUEMA, "data": trozo}),
    }, timeout=180)
    if r.status_code >= 400:
        try:
            cod = r.json().get("error", {}).get("code")
        except Exception:
            cod = None
        json.dump({"enviados": i, "archivo": os.path.basename(RUTA)},
                  open(PROGRESO, "w"), indent=2)
        if cod == 613:
            print("")
            print("  Meta corto por limite diario de la API (613).")
            print("  Van %s de %s. El progreso quedo guardado."
                  % (format(i, ","), format(len(datos), ",")))
            print("  Volver a correr el mismo comando mas tarde: sigue donde quedo.")
            raise SystemExit
        raise SystemExit("ERROR enviando desde %d: %s" % (i, r.text[:400]))
    i += len(trozo)
    json.dump({"enviados": i, "archivo": os.path.basename(RUTA)},
              open(PROGRESO, "w"), indent=2)
    print("  enviados %s de %s" % (format(i, ","), format(len(datos), ",")))
    time.sleep(2)

print("")
print("LISTO. %s contactos enviados a %s." % (format(i, ","), info.get("name")))
print("Meta tarda entre varios minutos y unas horas en procesarlos y reflejar el tamano.")
