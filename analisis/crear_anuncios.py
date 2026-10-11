# -*- coding: utf-8 -*-
"""Crea los anuncios de C1..C4 EN PAUSA, con creativo por ubicacion y sin mejoras de Meta.

Reanudable: lo ya creado se registra en anuncios_creados.json y se omite.
Uso:  python crear_anuncios.py            -> simulacion
      python crear_anuncios.py --test     -> crea UN anuncio de prueba
      python crear_anuncios.py --go       -> crea todo lo que falte
"""
import json, os, re, sys, time, unicodedata, requests
from copys import (COPY, REGLAS_UBICACION, SIN_MEJORAS, PAGE_ID, INSTAGRAM_ID,
                   ENLACE, VIDEOS, CONJUNTO_VIDEOS)

RAIZ = r"C:\Users\juanc\OneDrive\Documentos\Clientes\ALMI Financiera"
PIEZAS = os.path.join(RAIZ, "Pauta Almi")
cred = json.load(open(os.path.join(RAIZ, "Dashboard ALMI", "meta_credentials.json")))
TOKEN, ACT = cred["access_token"], cred["ad_account_id"]
G = "https://graph.facebook.com/v21.0/"
AQUI = os.path.dirname(os.path.abspath(__file__))

HASHES = json.load(open(os.path.join(AQUI, "hashes_imagenes.json"), encoding="utf-8"))
ESTRUCTURA = json.load(open(os.path.join(AQUI, "estructura_nueva.json"), encoding="utf-8"))
REGISTRO = os.path.join(AQUI, "anuncios_creados.json")
creados = json.load(open(REGISTRO, encoding="utf-8")) if os.path.exists(REGISTRO) else {}

CARPETA_CAMPANA = {
    "C1 - Convenio por Sectores": "C1",
    "C2 - Empleados sector privado": "C2",
    "C3 - Reportados": "C3",
    "C4 - Retargeting caliente": "C4",
}
NOMBRE_CAMPANA = {
    "C1": "C1 - Convenio por sectores - Oct2026",
    "C2": "C2 - Empleados sector privado - Oct2026",
    "C3": "C3 - Reportados - Oct2026",
    "C4": "C4 - Retargeting caliente - Oct2026",
}
# C1: que sectores van en cada conjunto
CONJUNTO_POR_SECTOR = {
    "01 Seguridad y vigilancia": "sectores-alto-volumen",
    "02 Temporales y servicios": "sectores-alto-volumen",
    "03 Restaurantes y alimentos": "sectores-alto-volumen",
    "04 Retail y moda": "sectores-especializados",
    "05 Financiero y seguros": "sectores-especializados",
    "06 Salud y bienestar": "sectores-especializados",
    "07 BPO y tecnologia": "sectores-especializados",
    "08 Industria y automotriz": "sectores-especializados",
}
# marcas reconocibles que ademas van al conjunto de lookalike
LOOKALIKE = {"el-corral", "frisby", "postobon", "papa-johns", "davivienda",
             "tennis", "h-y-m", "smart-fit"}


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def bonito(s):
    """de 'banco-caja-social' a 'Banco Caja Social'"""
    especiales = {"h-y-m": "H&M", "axa-colpatria": "AXA Colpatria", "cifin": "CIFIN",
                  "abai": "ABAI", "atsa": "ATSA", "ava": "AVA", "iztech": "IZTech",
                  "cvs-colviseg": "CVS Colviseg", "sr-wok": "Sr. Wok"}
    if s in especiales:
        return especiales[s]
    return " ".join(p.capitalize() for p in s.split("-"))


def post(path, payload):
    payload["access_token"] = TOKEN
    for intento in range(5):
        r = requests.post(G + path, data=payload, timeout=120)
        if r.status_code == 200:
            return r.json()
        err = r.json().get("error", {})
        if err.get("code") in (17, 4, 613):          # limite de llamadas
            espera = 60 * (intento + 1)
            print(f"      limite de API, esperando {espera}s...")
            time.sleep(espera)
            continue
        print("      ERROR:", err.get("message", "?")[:200])
        return None
    return None


def construir_conceptos():
    """Devuelve [(campana, conjunto_slug, nombre_anuncio, marca, {label: hash})]"""
    fuera = []
    for carpeta_camp, camp in CARPETA_CAMPANA.items():
        base = os.path.join(PIEZAS, carpeta_camp)
        for raiz, dirs, fs in os.walk(base):
            pngs = [f for f in fs if f.lower().endswith(".png")]
            if len(pngs) != 3:
                continue
            concepto = os.path.basename(raiz)
            marca = re.sub(r"^\d+_", "", concepto)
            imgs = {}
            for f in pngs:
                lab = ("cuadrado" if "cuadrado" in f else
                       "vertical" if "vertical" in f else "horizontal")
                rel = os.path.relpath(os.path.join(raiz, f), PIEZAS)
                if rel not in HASHES:
                    imgs = {}
                    break
                imgs[lab] = HASHES[rel]
            if len(imgs) != 3:
                print("   faltan hashes, se omite:", concepto)
                continue

            if camp == "C1":
                sector = os.path.basename(os.path.dirname(raiz))
                conj = CONJUNTO_POR_SECTOR[sector]
                nombre = f"c1-{slug(sector)[3:]}-{marca}"
                fuera.append((camp, conj, nombre, marca, imgs))
                if marca in LOOKALIKE:
                    fuera.append((camp, "lookalike-solicitantes",
                                  f"c1-lookalike-{marca}", marca, imgs))
            else:
                conjuntos = list(ESTRUCTURA[NOMBRE_CAMPANA[camp]]["conjuntos"])
                for conj in conjuntos:
                    fuera.append((camp, conj, f"{camp.lower()}-{conj}-{marca}", marca, imgs))
    return fuera


def crear(camp, conj_slug, nombre, marca, imgs):
    cfg = COPY[camp]
    adset_id = ESTRUCTURA[NOMBRE_CAMPANA[camp]]["conjuntos"][conj_slug]

    # UNA sola pieza por anuncio (sus 3 formatos van por ubicacion, no rotando).
    # Hasta 5 textos y 5 titulares, que es lo que Meta permite optimizar dentro
    # del anuncio. El conjunto de textos es IDENTICO en todos los anuncios de la
    # campana, asi que la unica variable que cambia entre ellos sigue siendo la pieza.
    # Combinacion que Meta acepta: reglas de ubicacion para las 3 imagenes MAS
    # 5 textos y 5 titulares. La clave es que todos los textos compartan una
    # misma etiqueta y que cada regla apunte a esa etiqueta; si cada texto lleva
    # etiqueta propia, Meta exige uno por regla. No admite descripciones junto
    # con reglas, asi que el anuncio va sin descripcion de enlace.
    afs = {
        "ad_formats": ["SINGLE_IMAGE"],
        "images": [{"hash": h, "adlabels": [{"name": lab}]} for lab, h in imgs.items()],
        "bodies": [{"text": t, "adlabels": [{"name": "txt"}]} for t in cfg["bodies"][:5]],
        "titles": [{"text": t, "adlabels": [{"name": "ttl"}]} for t in cfg["titles"][:5]],
        "link_urls": [{"website_url": ENLACE}],
        "call_to_action_types": [cfg["cta"]],
        "asset_customization_rules": [
            {"customization_spec": spec,
             "image_label": {"name": lab},
             "body_label": {"name": "txt"},
             "title_label": {"name": "ttl"}}
            for lab, spec in REGLAS_UBICACION
        ],
    }
    utm = (f"utm_source=facebook&utm_medium=paid_social&utm_campaign={cfg['utm']}"
           f"&utm_content={{{{ad.name}}}}&utm_term={{{{adset.name}}}}")

    cr = post(ACT + "/adcreatives", {
        "name": "cr-" + nombre,
        "object_story_spec": json.dumps({"page_id": PAGE_ID,
                                         "instagram_user_id": INSTAGRAM_ID}),
        "asset_feed_spec": json.dumps(afs),
        "degrees_of_freedom_spec": json.dumps(SIN_MEJORAS),
        "url_tags": utm,
    })
    if not cr:
        return None
    ad = post(ACT + "/ads", {
        "name": nombre, "adset_id": adset_id, "status": "PAUSED",
        "creative": json.dumps({"creative_id": cr["id"]}),
    })
    return ad["id"] if ad else None


def miniatura(video_id):
    """Miniatura preferida del video. Reintenta: si devuelve vacio y se manda
    thumbnail_url en nulo, Meta rechaza el creativo con 'Invalid parameter'."""
    q = {"access_token": TOKEN, "fields": "uri,is_preferred"}
    for intento in range(4):
        r = requests.get(G + video_id + "/thumbnails", params=q, timeout=90)
        if r.status_code == 200:
            ts = r.json().get("data", [])
            pref = [t for t in ts if t.get("is_preferred")] or ts
            if pref:
                return pref[0]["uri"]
        time.sleep(20 * (intento + 1))
    return None


def crear_video(camp, clave, video_id, thumb):
    cfg = COPY[camp]
    conj_slug = CONJUNTO_VIDEOS[camp]
    adset_id = ESTRUCTURA[NOMBRE_CAMPANA[camp]]["conjuntos"][conj_slug]
    nombre = f"{camp.lower()}-video-{clave}"

    # Sin reglas de ubicacion: el video es vertical y entra igual en todas,
    # con el recorte automatico de Meta desactivado en SIN_MEJORAS.
    # Los conjuntos heredaron la configuracion de contenido dinamico, y Meta solo
    # admite UN anuncio por conjunto dinamico. Un creativo con reglas de
    # personalizacion deja de contar como dinamico, asi que el video tambien las
    # lleva: el mismo video para todas las ubicaciones, con las etiquetas de
    # texto compartidas igual que en las piezas de imagen.
    video = {"video_id": video_id, "adlabels": [{"name": "vid"}]}
    if thumb:                      # sin miniatura valida se omite la clave
        video["thumbnail_url"] = thumb
    etiquetas = {"body_label": {"name": "txt"}, "title_label": {"name": "ttl"},
                 "video_label": {"name": "vid"}}
    afs = {
        "ad_formats": ["SINGLE_VIDEO"],
        "videos": [video],
        "bodies": [{"text": t, "adlabels": [{"name": "txt"}]} for t in cfg["bodies"][:5]],
        "titles": [{"text": t, "adlabels": [{"name": "ttl"}]} for t in cfg["titles"][:5]],
        "link_urls": [{"website_url": ENLACE}],
        "call_to_action_types": [cfg["cta"]],
        "asset_customization_rules": [dict(etiquetas, customization_spec=spec)
                                      for _, spec in REGLAS_UBICACION],
    }
    utm = (f"utm_source=facebook&utm_medium=paid_social&utm_campaign={cfg['utm']}"
           f"&utm_content={{{{ad.name}}}}&utm_term={{{{adset.name}}}}")
    cr = post(ACT + "/adcreatives", {
        "name": "cr-" + nombre,
        "object_story_spec": json.dumps({"page_id": PAGE_ID,
                                         "instagram_user_id": INSTAGRAM_ID}),
        "asset_feed_spec": json.dumps(afs),
        "degrees_of_freedom_spec": json.dumps(SIN_MEJORAS),
        "url_tags": utm,
    })
    if not cr:
        return nombre, None
    ad = post(ACT + "/ads", {
        "name": nombre, "adset_id": adset_id, "status": "PAUSED",
        "creative": json.dumps({"creative_id": cr["id"]}),
    })
    return nombre, (ad["id"] if ad else None)


def crear_videos():
    """Los 8 videos del lote de julio, uno por anuncio, en las cuatro campanas."""
    print("\n--- videos ---")
    thumbs = {}
    ok = fallo = 0
    for camp in ("C1", "C2", "C3", "C4"):
        for clave, vid in VIDEOS.items():
            nombre = f"{camp.lower()}-video-{clave}"
            if nombre in creados:
                continue
            if vid not in thumbs:
                thumbs[vid] = miniatura(vid)
                time.sleep(0.4)
            n, aid = crear_video(camp, clave, vid, thumbs[vid])
            if aid:
                creados[n] = aid; ok += 1
                print(f"   OK {n} -> {aid}")
            else:
                fallo += 1
                print(f"   FALLO {n}")
                if fallo >= 3 and ok == 0:
                    print("   tres fallos sin exito, se detiene"); return ok, fallo
            time.sleep(1.2)
            json.dump(creados, open(REGISTRO, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
    return ok, fallo


def main():
    conceptos = construir_conceptos()
    print(f"anuncios a crear: {len(conceptos)} | ya creados: {len(creados)}")
    porcamp = {}
    for c, conj, n, m, i in conceptos:
        porcamp.setdefault((c, conj), 0)
        porcamp[(c, conj)] += 1
    for k in sorted(porcamp):
        print(f"   {k[0]} / {k[1]:26s} -> {porcamp[k]}")

    if "--go" not in sys.argv and "--test" not in sys.argv:
        print("\nSIMULACION. --test crea uno, --go crea todo.")
        return

    pendientes = [c for c in conceptos if c[2] not in creados]
    if "--test" in sys.argv:
        pendientes = pendientes[:1]
    print(f"\ncreando {len(pendientes)}...")
    ok = fallo = 0
    for camp, conj, nombre, marca, imgs in pendientes:
        aid = crear(camp, conj, nombre, marca, imgs)
        if aid:
            creados[nombre] = aid; ok += 1
            print(f"   OK {nombre} -> {aid}")
        else:
            fallo += 1
            print(f"   FALLO {nombre}")
            if fallo >= 3 and ok == 0:
                print("   tres fallos seguidos sin exito, se detiene")
                break
        if ok % 10 == 0:
            json.dump(creados, open(REGISTRO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(1.2)
    json.dump(creados, open(REGISTRO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    if "--go" in sys.argv:
        vok, vfallo = crear_videos()
        ok += vok; fallo += vfallo

    print(f"\ncreados {ok}, fallidos {fallo}. Registro en {REGISTRO}")


if __name__ == "__main__":
    main()
