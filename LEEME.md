# Dashboard ALMI — dónde vive y cómo se levanta

**Carpeta de trabajo: `C:\Users\juanc\Proyectos\ALMI Financiera\Dashboard ALMI`**

Fuera de OneDrive, a propósito. El 11-oct-2026 OneDrive vació la carpeta
anterior y se perdieron las credenciales, los scripts de análisis y la copia
local del repositorio. Lo que estaba en GitHub se recuperó completo; lo que no
estaba, hubo que reconstruirlo. No devolver el proyecto a OneDrive.

## Qué hay aquí

| Archivo | Para qué |
|---|---|
| `actualizar_dashboard.py` | Genera `Dashboard_ALMI.html` desde GA4 |
| `actualizar_google_ads.py` / `actualizar_meta_ads.py` | Llenan `ads_data.json` |
| `ejecutar_actualizacion.bat` | Corre los tres en orden y publica |
| `analisis/` | Barridos de campañas y scripts de escritura en Meta y Google |

Orden de ejecución: Google Ads, Meta Ads, dashboard. El `.bat` ya lo hace.

## Credenciales (ninguna está en Git)

| Archivo | Qué contiene | Si se pierde |
|---|---|---|
| `oauth_credentials.json` | Cliente OAuth de Google | Se reconstruye desde cualquier `token*.json`, que guardan `client_id` y `client_secret` |
| `token.json` | GA4 lectura | Se vuelve a autorizar solo al ejecutar |
| `token_ads.json` | Google Ads | Igual |
| `token_admin.json` | GA4 Admin API | Igual |
| `google_ads_config.json` | `developer_token`, MCC `2836788094`, cuenta `4143819923` | El token de desarrollador es el mismo de la agencia: está en `PALLOMARO\Dashboard\.env` |
| `meta_credentials.json` | Token de usuario de sistema y `act_1502138690491988` | Se regenera en Business Manager |

**Haz una copia de estos seis archivos fuera del proyecto.** Son lo único que
no se puede recuperar de GitHub.

## Sacar la foto de un mes cerrado

```
ALMI_COTIZADOR=viejo ALMI_DESDE=2026-08-01 ALMI_HASTA=2026-08-31 \
ALMI_SALIDA=Dashboard_ALMI_agosto2026.html python actualizar_dashboard.py
```

El tablero vivo no se toca. Hasta el 30-sep-2026 los datos están en la
propiedad GA4 `522022877` (cotizador anterior); desde el 1-oct, en `554405139`.

## Barridos

Desde `analisis/`:

```
python barrido.py 2026-10-02 2026-10-11      # Meta por campaña y por día
python barrido_google.py 2026-10-02 2026-10-11
python barrido_ga4.py 2026-10-01 2026-10-11  # embudo y solicitudes diarias
python poda.py 2026-10-02 2026-10-11         # candidatos a pausar
python pausar.py --go                        # aplica lo que dejó poda.py
```

Los scripts que escriben en las plataformas (`pausar.py`, `pmax.py`,
`crear_anuncios.py`, `webinar_campana.py`) **simulan por defecto** y solo
aplican con `--go`. Las campañas se crean siempre en pausa.
