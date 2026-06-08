"""
gsheets.py — Google Sheets client using a service account.
Credentials come from .streamlit/secrets.toml (never committed to GitHub).
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


@st.cache_resource
def get_gsheets_client() -> gspread.Client:
    """Return a cached gspread client authenticated via service account."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except KeyError as e:
        raise RuntimeError(
            f"Missing Google credential key: {e}. "
            "Add gcp_service_account to .streamlit/secrets.toml — see SETUP.md."
        )


def get_worksheet(client: gspread.Client, spreadsheet_id: str, sheet_name: str = "Bank Sheet") -> gspread.Worksheet:
    """Open the worksheet by spreadsheet ID and sheet name."""
    try:
        sh = client.open_by_key(spreadsheet_id)
        return sh.worksheet(sheet_name)
    except gspread.SpreadsheetNotFound:
        raise RuntimeError(
            f"Spreadsheet '{spreadsheet_id}' not found. "
            "Make sure you shared it with the service account email."
        )
    except gspread.WorksheetNotFound:
        raise RuntimeError(
            f"Sheet '{sheet_name}' not found in spreadsheet. "
            "Make sure the tab is named exactly 'Bank Sheet'."
        )
