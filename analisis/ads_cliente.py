# -*- coding: utf-8 -*-
"""Cliente de Google Ads reutilizable, con las credenciales del dashboard."""
import os
import sys, os
# La carpeta del tablero es la de arriba: el proyecto ya no vive en OneDrive.
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
_cwd = os.getcwd(); os.chdir(BASE)
import actualizar_google_ads as A
from google.ads.googleads.client import GoogleAdsClient
os.chdir(_cwd)

def cliente():
    creds = A.get_credentials()
    return GoogleAdsClient.load_from_dict({
        "developer_token": A.DEVELOPER_TOKEN,
        "login_customer_id": A.LOGIN_CUSTOMER_ID,
        "refresh_token": creds.refresh_token,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "use_proto_plus": True,
    })

CID = A.CUSTOMER_ID
