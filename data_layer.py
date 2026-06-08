"""
data_layer.py — Read and write the journal Google Sheet.

Sheet structure (tab named "Bank Sheet"):
  Row 1: column headers → month | fy | tag | total | nro_exp | nro_sav | nre_ab | nre_pt | nre_atharv | remarks
  Row 2+: data rows

This is simpler than the Excel structure — no dashboard row, no merged cells.
The Google Sheet is the single source of truth.
"""

import pandas as pd
import numpy as np
import streamlit as st
import gspread
from gsheets import get_gsheets_client, get_worksheet

# Column order in the Google Sheet (must match exactly)
SHEET_COLS = ["month", "fy", "tag", "total", "nro_exp", "nro_sav", "nre_ab", "nre_pt", "nre_atharv", "remarks"]
NUM_COLS   = ["total", "nro_exp", "nro_sav", "nre_ab", "nre_pt", "nre_atharv"]


def get_spreadsheet_id() -> str:
    try:
        return st.secrets["google"]["spreadsheet_id"]
    except KeyError:
        raise RuntimeError("Missing google.spreadsheet_id in secrets.toml — see SETUP.md.")


def load_data(client: gspread.Client = None) -> pd.DataFrame:
    """Download all rows from the Bank Sheet and return a clean DataFrame."""
    if client is None:
        client = get_gsheets_client()
    sid = get_spreadsheet_id()
    ws  = get_worksheet(client, sid)

    records = ws.get_all_records(expected_headers=SHEET_COLS, default_blank="")
    if not records:
        # Sheet exists but has no data rows — return empty frame
        return pd.DataFrame(columns=SHEET_COLS)

    df = pd.DataFrame(records)

    # Coerce types
    for c in NUM_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["month"]   = df["month"].astype(str).str.strip().replace("", None)
    df["fy"]      = df["fy"].astype(str).str.strip()
    df["tag"]     = df["tag"].astype(str).str.strip()
    df["remarks"] = df["remarks"].astype(str).str.strip()

    # Drop fully empty rows
    df = df[~(
        (df["fy"] == "") & (df["tag"] == "") &
        (df["total"] == 0) & (df["remarks"] == "")
    )].reset_index(drop=True)

    return df


def save_data(df: pd.DataFrame, client: gspread.Client = None) -> None:
    """
    Overwrite the entire Bank Sheet with the current DataFrame.
    Writes headers on row 1, then all data rows.
    """
    if client is None:
        client = get_gsheets_client()
    sid = get_spreadsheet_id()
    ws  = get_worksheet(client, sid)

    # Build the values list: header row + data rows
    rows = [SHEET_COLS]  # header
    for _, row in df[SHEET_COLS].iterrows():
        out_row = []
        for c in SHEET_COLS:
            v = row[c]
            if c in NUM_COLS:
                out_row.append(float(v) if v and not (isinstance(v, float) and np.isnan(v)) else 0)
            else:
                out_row.append(str(v) if v is not None and str(v) != "nan" else "")
        rows.append(out_row)

    # Clear and rewrite
    ws.clear()
    ws.update(rows, value_input_option="USER_ENTERED")


def get_fy_for_month(month_str: str) -> str:
    """Derive Indian FY from YYYY-MM. e.g. '2026-05' → 'FY26-27'"""
    try:
        y, m = int(month_str[:4]), int(month_str[5:7])
        fy_start = y if m >= 4 else y - 1
        return f"FY{str(fy_start)[2:]}-{str(fy_start+1)[2:]}"
    except Exception:
        return ""
