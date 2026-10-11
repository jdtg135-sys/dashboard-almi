# -*- coding: utf-8 -*-
"""Copys por campana. Hasta 5 textos y 5 titulares por anuncio.

Regla de armado: primero los ganadores propios de la campana (jul-sep 2026,
minimo 15 conversiones). Si no alcanzan para llenar 5, se completa con
ganadores de campanas hermanas antes que inventar texto nuevo. Los marcados
NUEVO no tienen historial y se construyeron sobre los patrones que si lo tienen:
mencionar la friccion del banco y prometer un tiempo concreto.

El conjunto de textos es IDENTICO en todos los anuncios de una misma campana,
asi la unica variable que cambia entre anuncios es la pieza.
"""

PAGE_ID = "732244117208789"
INSTAGRAM_ID = "17841401157769111"
PIXEL = "1749544856232374"
ENLACE = "https://cotizador.almifinanciera.com/"

COPY = {
    "C1": {
        "utm": "c1-convenio-sectores",
        "cta": "GET_QUOTE",
        "bodies": [
            "¿Cansado de que el banco te pida 50 documentos? En ALMI el proceso es diferente.",                          # 1.097
            "Crédito por libranza para empleados del sector privado. Cuota fija, 100% digital. Verifica tu convenio hoy.",  # 1.226
            "Tu empresa ya tiene convenio con ALMI. ¿Lo sabías? Crédito por nómina, aprobación rápida, 100% digital.",      # 1.305
            "Sin extractos bancarios. Sin cartas laborales. Sin ir a una sucursal. Aprobación el mismo día.",               # 1.388
            "Tu cuota queda fija y se descuenta de tu nómina. Sin sorpresas.",                                             # 1.418
        ],
        "titles": [
            "Sin trámites. Sin banco. Solo tu nómina",   # 1.245, unico titular con historial en C1
            "Simula tu crédito en 2 minutos",            # 980 en C2, el mejor titular de la cuenta
            "Solicita en 5 minutos",                     # 1.027 en C2
            "Aprobación el mismo día",                   # NUEVO, tiempo concreto
            "Sin papeleo, cuota fija",                   # NUEVO, friccion del banco
        ],
        "descriptions": [
            "Cuota fija descontada de tu nómina",
            "Aprobación el mismo día",
            "100% digital, sin ir a una sucursal",
        ],
    },
    "C2": {
        "utm": "c2-empleados-privado",
        "cta": "GET_QUOTE",
        "bodies": [
            "Llevas semanas pensando en ese préstamo que necesitas pero no sabes por dónde empezar.\nCon ALMI es diferente: si trabajas en empresa privada, nosotros te decimos SÍ.\nRápido, seguro y con cuota que cabe en tu salario.",   # 1.005
            "¿Necesitas dinero pero el banco te pone trabas?\nCon ALMI te prestamos rápido, sin papeleo y la cuota sale directo de tu nómina.\nAprobación en días. Sin fiador. Sin banco.",                                                  # 1.015
            "Tienes empleo. Eso es todo lo que necesitas.\nALMI te presta sobre tu nómina — cuota fija, sin sorpresas, sin trámites largos.\nSolicita en 2 minutos desde el celular.",                                                       # 1.200
            "¿Cansado de que el banco te pida 50 documentos? En ALMI el proceso es diferente.",                             # 1.097 en C1
            "Sin extractos bancarios. Sin cartas laborales. Sin ir a una sucursal. Aprobación el mismo día.",               # 1.388 en C1
        ],
        "titles": [
            "Simula tu crédito en 2 minutos",            # 980
            "Solicita en 5 minutos",                     # 1.027
            "Cotiza ahora sin compromiso",               # 1.603
            "Sin trámites. Sin banco. Solo tu nómina",   # 1.245 en C1
            "Aprobación el mismo día",                   # NUEVO
        ],
        "descriptions": [
            "Tu nómina es tu garantía",
            "Cuota fija, sin sorpresas",
            "Respuesta el mismo día",
        ],
    },
    "C3": {
        "utm": "c3-reportados",
        "cta": "GET_QUOTE",
        "bodies": [
            "¿Te han dicho que no en otros lados por estar reportado? Aquí sí te prestamos. Sin vueltas, sin excusas.",     # 2.102
            "No te vamos a juzgar por tu historial. Te vamos a ayudar a salir adelante. Solicita tu crédito con ALMI.",     # 2.123
            "Ya te dijeron que no en el banco. Ya te dijeron que no en otros lados. Nosotros sí te decimos que sí.",        # 2.190
            "Estar reportado no debería dejarte sin opciones cuando más lo necesitas. Solicita tu crédito hoy mismo.",      # 2.616
            "Estás reportado y necesitas el crédito ahora. Aquí sabes en minutos si calificas, sin ir a un banco.",         # NUEVO
        ],
        "titles": [
            "Aquí sí calificas",                         # 1.814, poco volumen: merece mas entrega
            "Sin importar tu historial, hablemos",       # 1.863
            "Reportado y aún así te prestamos",          # 2.138, el que sostiene el volumen
            "Tu historial no te cierra la puerta",       # NUEVO
            "Sabes en minutos si calificas",             # NUEVO, tiempo concreto
        ],
        "descriptions": [
            "Tu historial no nos detiene",
            "Solicita en 5 minutos",
            "Respuesta rápida, sin filas",
        ],
    },
    "C4": {
        "utm": "c4-retargeting",
        "cta": "GET_QUOTE",
        "bodies": [
            "Tu solicitud quedó a medias. No pierdas la oportunidad, termínala en menos de 5 minutos.",                     # 992
            "¿Te quedaste a mitad de camino? Vuelve, completa tu solicitud y recibe respuesta rápido.",                     # 1.084
            "Empezaste tu solicitud con nosotros pero no la terminaste. Faltan solo unos minutos para completarla.",        # 1.106
            "El crédito que buscabas sigue disponible. Vuelve y completa tu solicitud antes de que se te pase.",            # 1.126
            "Tu cupo sigue reservado. Termina la solicitud y recibe respuesta el mismo día.",                              # NUEVO
        ],
        "titles": [
            "Está a un paso de terminar",                # 1.161
            "Termina lo que empezaste",                  # 1.185
            "Tu solicitud te está esperando",            # 1.298
            "Vuelve y termina tu solicitud",             # 1.427
            "Termínala en 5 minutos",                    # NUEVO, tiempo concreto
        ],
        "descriptions": [
            "Tu solicitud sigue disponible",
            "Solo te toma unos minutos",
            "Rápido, fácil, desde tu celular",
        ],
    },
}

# --- Videos de la biblioteca -------------------------------------------------
# Van los 8 del lote de julio, cada uno como anuncio independiente, en las cuatro
# campanas. Historial conocido: 3.mp4 gana en C3 (CPA 1.527 contra 2.211 de imagen)
# y 4.mp4 rinde a la par del promedio en C2 (1.041).
VIDEOS = {
    "1":  "1351857243741559",
    "2":  "1076009458323183",
    "3":  "1025154430213482",
    "4":  "1040320635068675",
    "6":  "1533990968205286",
    "7":  "1327846089557736",
    "8":  "971765152563645",
    "10": "3971246113168390",
}
# conjunto donde entran los videos de cada campana (el mas amplio de cada una)
CONJUNTO_VIDEOS = {
    "C1": "sectores-alto-volumen",
    "C2": "advantage-frio",
    "C3": "reportados-advantage",
    "C4": "retargeting-general",
}

# --- Ubicaciones por formato -------------------------------------------------
# Solo aplica a las piezas de imagen, que tienen los 3 formatos. Los videos son
# verticales y entran sin personalizacion, con el recorte automatico apagado.
REGLAS_UBICACION = [
    ("vertical", {
        "publisher_platforms": ["facebook", "instagram", "messenger", "audience_network"],
        "facebook_positions": ["story", "facebook_reels"],
        "instagram_positions": ["story", "reels"],
        "messenger_positions": ["story"],
        "audience_network_positions": ["rewarded_video"],
    }),
    ("horizontal", {
        "publisher_platforms": ["facebook", "messenger", "audience_network"],
        "facebook_positions": ["right_hand_column"],
        "messenger_positions": ["messenger_home"],
        "audience_network_positions": ["classic"],
    }),
    ("cuadrado", {
        "publisher_platforms": ["facebook", "instagram"],
        "facebook_positions": ["feed", "marketplace", "video_feeds", "search", "profile_feed"],
        "instagram_positions": ["stream", "explore", "explore_home", "ig_search", "profile_feed"],
    }),
]

# --- Mejoras automaticas de Meta: TODAS desactivadas -------------------------
# Meta reescribe titulares y genera fondos con IA que rompen la tipografia y el
# logo de las piezas. Con creativos ya disenados, cualquier "mejora" empeora.
SIN_MEJORAS = {
    "creative_features_spec": {k: {"enroll_status": "OPT_OUT"} for k in [
        "advantage_plus_creative",
        "image_touchups",
        "image_templates",
        "text_optimizations",
        "enhance_cta",
        "image_background_gen",
        "text_generation",
        "video_auto_crop",
        "adapt_to_placement",
        "image_animation",
        "profile_card",
        "product_browsing",
        "text_overlay_translation",
        "ig_video_native_subtitle",
        "standard_enhancements_catalog",
        "product_metadata_automation",
    ]}
}
