"""
data_layer.py — Read and write the journal Excel file via OneDrive.

Excel sheet structure (Bank Sheet):
  Row 1: empty
  Row 2: dashboard totals
  Row 3: column headers → Month | FY | Total | Tags | NRO Expense | NRO Savings | NRE AB | NRE PT | NRE Atharv | Remarks
  Row 4+: data rows
"""

import io
import pandas as pd
import numpy as np
from datetime import datetime
from onedrive import OneDriveClient

# Column mapping: Excel header → internal snake_case name
EXCEL_COLS = {
    "Month":       "month",
    "FY":          "fy",
    "Total":       "total",
    "Tags":        "tag",
    "NRO Expense": "nro_exp",
    "NRO Savings": "nro_sav",
    "NRE AB":      "nre_ab",
    "NRE PT":      "nre_pt",
    "NRE Atharv":  "nre_atharv",
    "Remarks":     "remarks",
}
REVERSE_COLS = {v: k for k, v in EXCEL_COLS.items()}
SHEET_NAME = "Bank Sheet"


def _parse_month(val) -> str | None:
    """Convert Excel date or string to YYYY-MM string."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m")
    s = str(val).strip()
    if len(s) >= 7 and s[4] == "-":
        return s[:7]
    return None


def load_data(client: OneDriveClient) -> pd.DataFrame:
    """
    Download and parse the Excel Bank Sheet into a clean DataFrame.
    Returns one row per journal entry with standardised column names.
    """
    raw = client.download_excel()
    xl = pd.ExcelFile(io.BytesIO(raw))
    df_raw = xl.parse(SHEET_NAME, header=2)  # row index 2 = Excel row 3 = headers

    # Keep only the columns we care about
    keep = [c for c in EXCEL_COLS.keys() if c in df_raw.columns]
    df = df_raw[keep].copy()
    df.rename(columns=EXCEL_COLS, inplace=True)

    # Coerce numeric columns
    num_cols = ["total", "nro_exp", "nro_sav", "nre_ab", "nre_pt", "nre_atharv"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Clean string columns
    df["month"]   = df["month"].apply(_parse_month)
    df["fy"]      = df["fy"].fillna("").astype(str).str.strip()
    df["tag"]     = df["tag"].fillna("").astype(str).str.strip()
    df["remarks"] = df["remarks"].fillna("").astype(str).str.strip()

    # Drop completely empty rows
    df = df[~(
        (df["fy"] == "") &
        (df["tag"] == "") &
        (df["total"] == 0) &
        (df["remarks"] == "")
    )].reset_index(drop=True)

    return df


def save_data(client: OneDriveClient, df: pd.DataFrame) -> None:
    """
    Write the DataFrame back to the Excel Bank Sheet, preserving the
    dashboard header rows (rows 1–2) and re-writing from row 3 onwards.
    """
    raw = client.download_excel()
    xl = pd.ExcelFile(io.BytesIO(raw))

    # Read all sheets so we can preserve non-Bank-Sheet content
    all_sheets = {}
    for sheet in xl.sheet_names:
        if sheet != SHEET_NAME:
            all_sheets[sheet] = xl.parse(sheet, header=None)

    # Build the output Bank Sheet
    # Row 1: empty
    # Row 2: dashboard (we will recalculate the SUM row here)
    # Row 3: headers
    # Row 4+: data

    # Prepare data rows in Excel column order
    out_cols_ordered = list(EXCEL_COLS.keys())
    out_data = pd.DataFrame(index=range(len(df)), columns=out_cols_ordered)

    for excel_col, internal_col in EXCEL_COLS.items():
        if internal_col == "month":
            out_data[excel_col] = df["month"].apply(
                lambda m: pd.Timestamp(m + "-01") if m else None
            )
        elif internal_col in df.columns:
            out_data[excel_col] = df[internal_col].values
        else:
            out_data[excel_col] = None

    # Dashboard summary row (row 2): sum of bank columns across all data
    bank_sums = {
        "NRO Expense": float(df["nro_exp"].sum()),
        "NRO Savings": float(df["nro_sav"].sum()),
        "NRE AB":      float(df["nre_ab"].sum()),
        "NRE PT":      float(df["nre_pt"].sum()),
        "NRE Atharv":  float(df["nre_atharv"].sum()),
    }

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl", datetime_format="YYYY-MM-DD") as writer:
        # Write Bank Sheet
        # Empty row 1
        pd.DataFrame([{}]).to_excel(writer, sheet_name=SHEET_NAME, index=False, header=False, startrow=0)
        # Dashboard row 2
        dash = pd.DataFrame([bank_sums])
        dash.to_excel(writer, sheet_name=SHEET_NAME, index=False, startrow=1)
        # Headers + data from row 3
        out_data.to_excel(writer, sheet_name=SHEET_NAME, index=False, startrow=3)

        # Restore other sheets
        for sheet_name, sheet_df in all_sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

    output.seek(0)
    client.upload_excel(output.read())


def get_fy_for_month(month_str: str) -> str:
    """Derive Indian FY from a YYYY-MM string. e.g. '2026-05' → 'FY26-27'"""
    try:
        y, m = int(month_str[:4]), int(month_str[5:7])
        fy_start = y if m >= 4 else y - 1
        return f"FY{str(fy_start)[2:]}-{str(fy_start+1)[2:]}"
    except:
        return ""
