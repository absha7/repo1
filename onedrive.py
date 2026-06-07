"""
onedrive.py — Microsoft Graph API client for OneDrive Excel access
Reads credentials from .streamlit/secrets.toml
"""

import streamlit as st
import requests
from functools import lru_cache


class OneDriveClient:
    """Thin wrapper around Microsoft Graph API for reading/writing a single Excel file."""

    GRAPH_BASE = "https://graph.microsoft.com/v1.0"
    TOKEN_URL  = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    def __init__(self, tenant_id: str, client_id: str, client_secret: str, file_path: str):
        self.tenant_id     = tenant_id
        self.client_id     = client_id
        self.client_secret = client_secret
        self.file_path     = file_path  # e.g. "/Documents/India_Money_Journal.xlsx"
        self._token        = None

    def _get_token(self) -> str:
        """Fetch access token using client credentials flow."""
        if self._token:
            return self._token
        url = self.TOKEN_URL.format(tenant_id=self.tenant_id)
        resp = requests.post(url, data={
            "grant_type":    "client_credentials",
            "client_id":     self.client_id,
            "client_secret": self.client_secret,
            "scope":         "https://graph.microsoft.com/.default",
        }, timeout=15)
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def download_excel(self) -> bytes:
        """Download the Excel file as bytes."""
        # Encode path for Graph API
        encoded = self.file_path.replace(" ", "%20")
        url = f"{self.GRAPH_BASE}/me/drive/root:{encoded}:/content"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.content

    def upload_excel(self, content: bytes) -> None:
        """Upload/overwrite the Excel file."""
        encoded = self.file_path.replace(" ", "%20")
        url = f"{self.GRAPH_BASE}/me/drive/root:{encoded}:/content"
        headers = {**self._headers(), "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        resp = requests.put(url, headers=headers, data=content, timeout=60)
        resp.raise_for_status()


@st.cache_resource
def get_onedrive_client() -> OneDriveClient:
    """Return a cached OneDrive client using credentials from secrets.toml"""
    try:
        cfg = st.secrets["onedrive"]
        return OneDriveClient(
            tenant_id     = cfg["tenant_id"],
            client_id     = cfg["client_id"],
            client_secret = cfg["client_secret"],
            file_path     = cfg["file_path"],
        )
    except KeyError as e:
        raise RuntimeError(
            f"Missing OneDrive credential: {e}. "
            "Add it to .streamlit/secrets.toml — see SETUP.md for instructions."
        )
