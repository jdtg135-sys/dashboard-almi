"""Autoriza el scope de EDICION de GA4 y guarda token_admin.json.

Se ejecuta una sola vez. Abre el navegador para que el usuario acepte.
"""
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

BASE = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(BASE, "oauth_credentials.json")
TOKEN_ADMIN_FILE = os.path.join(BASE, "token_admin.json")

SCOPES = [
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.readonly",
]


def get_admin_credentials():
    creds = None
    if os.path.exists(TOKEN_ADMIN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_ADMIN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0, prompt="consent")
        with open(TOKEN_ADMIN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


if __name__ == "__main__":
    c = get_admin_credentials()
    print("Autorizacion OK. Scopes:", c.scopes)
    print("Token guardado en", TOKEN_ADMIN_FILE)
