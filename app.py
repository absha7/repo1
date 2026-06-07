"""
India Money Journal — Streamlit App
Data stored in OneDrive Excel file via Microsoft Graph API
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import warnings
warnings.filterwarnings("ignore")

from data_layer import load_data, save_data, get_fy_for_month
from onedrive import get_onedrive_client

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India Money Journal",
    page_icon="₹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ──────────────────────────────────────────────────────────────────
BANKS = ["NRO Expense", "NRO Savings", "NRE AB", "NRE PT", "NRE Atharv"]
BANK_COLS = ["nro_exp", "nro_sav", "nre_ab", "nre_pt", "nre_atharv"]
BANK_COLORS = ["#378ADD", "#1D9E75", "#D85A30", "#BA7517", "#D4537E"]
ALL_TAGS = [
    "Income-Res", "Income-Com", "Income", "Expense", "TDS", "TDS Income",
    "Investment", "Cashflow", "Savings", "Gift", "Transfer", "Loan", "Balance", ""
]
INCOME_TAGS = ["Income", "Income-Res", "Income-Com", "TDS Income"]

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main > div { padding-top: 1rem; }
    .stMetric { background: #f8f7f4; border-radius: 8px; padding: 12px 16px; border: 1px solid #e8e5dd; }
    .stMetric label { font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.05em; color: #8a8a80 !important; }
    .bal-positive { color: #2a7a50; font-weight: 600; }
    .bal-negative { color: #b03020; font-weight: 600; }
    .rule-table td { padding: 6px 12px; font-size: 13px; border-bottom: 1px solid #e8e5dd; }
    .rule-table th { padding: 6px 12px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #8a8a80; border-bottom: 1px solid #e8e5dd; }
    div[data-testid="stDataFrame"] { border: 1px solid #e8e5dd; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner="Loading journal data…")
def get_data():
    client = get_onedrive_client()
    return load_data(client)


def refresh():
    st.cache_data.clear()
    st.rerun()


def save(df):
    client = get_onedrive_client()
    save_data(client, df)
    st.cache_data.clear()


# ── Balance calculation (mirrors HTML computeBalances exactly) ─────────────────
def compute_balances(df: pd.DataFrame):
    """
    Base = last non-Opening Balance row values.
    Current = base + every row after it (all tags count).
    """
    bal_rows = df[
        (df["tag"] == "Balance") &
        (~df["remarks"].str.contains("Opening Balance", case=False, na=False))
    ]

    if bal_rows.empty:
        base_idx = -1
        base = {c: 0.0 for c in BANK_COLS}
    else:
        base_idx = bal_rows.index[-1]
        base = {c: float(df.loc[base_idx, c] or 0) for c in BANK_COLS}

    current = dict(base)
    after = df.loc[base_idx + 1:] if base_idx >= 0 else df
    after = after[after["tag"] != "Balance"]
    for c in BANK_COLS:
        current[c] += float(after[c].fillna(0).sum())

    return current, base_idx


def get_fy_movement(df: pd.DataFrame, fy: str, current: dict, base_idx: int):
    """Net movement per account for a given FY."""
    bal_rows = df[
        (df["tag"] == "Balance") &
        (~df["remarks"].str.contains("Opening Balance", case=False, na=False))
    ]
    fy_bal = bal_rows[bal_rows["fy"] == fy]

    if not fy_bal.empty:
        # Closed FY: movement = this closing - previous closing
        this_close_idx = fy_bal.index[-1]
        prev_bals = bal_rows[bal_rows.index < this_close_idx]
        if not prev_bals.empty:
            prev_idx = prev_bals.index[-1]
            open_vals = {c: float(df.loc[prev_idx, c] or 0) for c in BANK_COLS}
        else:
            ob = df[df["remarks"].str.contains("Opening Balance", case=False, na=False)]
            open_vals = {c: float(ob.iloc[0][c] or 0) for c in BANK_COLS} if not ob.empty else {c: 0.0 for c in BANK_COLS}
        close_vals = {c: float(df.loc[this_close_idx, c] or 0) for c in BANK_COLS}
        return {c: close_vals[c] - open_vals[c] for c in BANK_COLS}
    else:
        # Open FY: sum all non-Balance rows in this FY
        fy_rows = df[(df["fy"] == fy) & (df["tag"] != "Balance")]
        return {c: float(fy_rows[c].fillna(0).sum()) for c in BANK_COLS}


# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt_inr(v, compact=False):
    v = float(v or 0)
    sign = "-" if v < 0 else ""
    abs_v = abs(v)
    if compact:
        if abs_v >= 1e7: return f"{sign}₹{abs_v/1e7:.2f}Cr"
        if abs_v >= 1e5: return f"{sign}₹{abs_v/1e5:.1f}L"
        if abs_v >= 1e3: return f"{sign}₹{abs_v/1e3:.0f}K"
        return f"{sign}₹{abs_v:.0f}"
    return f"{sign}₹{abs_v:,.0f}"


def fy_rows(df, fy):
    return df[df["fy"] == fy].copy()


def sum_tag(df, tags):
    return float(df[df["tag"].isin(tags)]["total"].fillna(0).sum())


def get_all_fys(df):
    return sorted(df["fy"].dropna().unique(), key=lambda x: x[2:4])


# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ₹ India Money Journal")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["📊 Cashflow Summary", "📒 Cashflow Capture", "🧾 Tax Calculations"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    if st.button("🔄 Refresh data", use_container_width=True):
        refresh()
    st.caption("Data synced from OneDrive · Auto-saves on every change")


# ── Load data ──────────────────────────────────────────────────────────────────
try:
    df = get_data()
except Exception as e:
    st.error(f"Could not load data from OneDrive: {e}")
    st.info("Check your OneDrive credentials in `.streamlit/secrets.toml`")
    st.stop()

all_fys = get_all_fys(df)
current_bal, base_idx = compute_balances(df)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1: CASHFLOW SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Cashflow Summary":
    st.title("Cashflow Summary")

    # ── Account balances table ──────────────────────────────────────────────
    st.subheader("Account Balances & Movement")
    sel_fy = st.selectbox("FY for movement column", options=list(reversed(all_fys)), index=0, key="sum_fy")
    mov = get_fy_movement(df, sel_fy, current_bal, base_idx)

    bal_data = []
    for i, (bank, col) in enumerate(zip(BANKS, BANK_COLS)):
        bal = current_bal[col]
        net = mov[col]
        fy_rows_sel = df[(df["fy"] == sel_fy) & (df[col] > 0)]
        inflow = float(df[(df["fy"] == sel_fy) & (df[col] > 0)][col].sum())
        outflow = float(df[(df["fy"] == sel_fy) & (df[col] < 0)][col].sum())
        bal_data.append({
            "Account": bank,
            "Current Balance": fmt_inr(bal),
            f"Net ({sel_fy})": fmt_inr(net),
            "Inflow ↑": fmt_inr(inflow) if inflow else "—",
            "Outflow ↓": fmt_inr(abs(outflow)) if outflow else "—",
        })

    bal_df = pd.DataFrame(bal_data)
    st.dataframe(bal_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── FY summary tiles ────────────────────────────────────────────────────
    st.subheader(f"FY Summary — {sel_fy}")
    rows = fy_rows(df, sel_fy)
    inc_res = sum_tag(rows, ["Income-Res"])
    inc_com = sum_tag(rows, ["Income-Com"])
    inc_oth = sum_tag(rows, ["Income"])
    expense = sum_tag(rows, ["Expense"])
    tds     = sum_tag(rows, ["TDS"])
    tds_inc = sum_tag(rows, ["TDS Income"])
    inv     = sum_tag(rows, ["Investment"])
    net     = inc_res + inc_com + inc_oth + expense

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("Res. Rent",    fmt_inr(inc_res, True))
    c2.metric("Com. Rent",    fmt_inr(inc_com, True))
    c3.metric("Other Income", fmt_inr(inc_oth, True))
    c4.metric("Expenses",     fmt_inr(abs(expense), True), delta=fmt_inr(expense, True), delta_color="inverse")
    c5.metric("TDS Deducted", fmt_inr(abs(tds), True))
    c6.metric("Investments",  fmt_inr(abs(inv), True))
    c7.metric("Net Income",   fmt_inr(net, True), delta_color="normal")

    st.markdown("---")

    # ── Monthly bar chart ───────────────────────────────────────────────────
    st.subheader("Monthly Income vs Expenses")
    monthly = []
    for m in sorted(rows["month"].dropna().unique()):
        mr = rows[rows["month"] == m]
        inc = float(mr[mr["tag"].isin(["Income","Income-Res","Income-Com"])]["total"].sum())
        exp = float(abs(mr[mr["tag"] == "Expense"]["total"].sum()))
        tds_m = float(abs(mr[mr["tag"] == "TDS"]["total"].sum()))
        monthly.append({"Month": m, "Income": inc, "Expense": exp, "TDS": tds_m})

    if monthly:
        mdf = pd.DataFrame(monthly)
        fig = go.Figure()
        fig.add_bar(x=mdf["Month"], y=mdf["Income"],  name="Income",  marker_color="#2a7a50")
        fig.add_bar(x=mdf["Month"], y=mdf["Expense"], name="Expense", marker_color="#b03020")
        fig.add_bar(x=mdf["Month"], y=mdf["TDS"],     name="TDS",     marker_color="#a07020")
        fig.update_layout(
            barmode="group", height=300,
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=0,r=0,t=10,b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            yaxis=dict(tickformat=",.0f", gridcolor="#f0ede6"),
            xaxis=dict(gridcolor="#f0ede6"),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── Monthly breakdown table ──────────────────────────────────────────────
    st.subheader("Monthly Breakdown")
    mb_data = []
    for m in sorted(rows["month"].dropna().unique()):
        mr = rows[rows["month"] == m]
        mb_data.append({
            "Month": m,
            "Res Rent": fmt_inr(sum_tag(mr, ["Income-Res"])),
            "Com Rent":  fmt_inr(sum_tag(mr, ["Income-Com"])),
            "Other Inc": fmt_inr(sum_tag(mr, ["Income"])),
            "Expense":   fmt_inr(sum_tag(mr, ["Expense"])),
            "TDS":       fmt_inr(sum_tag(mr, ["TDS"])),
            "Investment":fmt_inr(sum_tag(mr, ["Investment"])),
            "Net":       fmt_inr(sum_tag(mr, ["Income","Income-Res","Income-Com"]) + sum_tag(mr, ["Expense"])),
        })
    if mb_data:
        st.dataframe(pd.DataFrame(mb_data), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2: CASHFLOW CAPTURE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📒 Cashflow Capture":
    st.title("Cashflow Capture")

    tab_ledger, tab_add, tab_clone = st.tabs(["📋 Ledger", "➕ Add / Edit Entry", "📋 Clone Month"])

    # ── TAB: LEDGER ─────────────────────────────────────────────────────────
    with tab_ledger:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filt_fy = st.selectbox("FY", ["All"] + list(reversed(all_fys)), index=1)
        with col2:
            filt_tag = st.selectbox("Tag", ["All"] + [t for t in ALL_TAGS if t])
        with col3:
            filt_bank = st.selectbox("Account", ["All"] + BANKS)
        with col4:
            filt_q = st.text_input("Search remarks", placeholder="e.g. Vatika")

        filtered = df.copy()
        if filt_fy != "All":
            filtered = filtered[filtered["fy"] == filt_fy]
        if filt_tag != "All":
            filtered = filtered[filtered["tag"] == filt_tag]
        if filt_bank != "All":
            col_key = BANK_COLS[BANKS.index(filt_bank)]
            filtered = filtered[filtered[col_key].fillna(0) != 0]
        if filt_q:
            filtered = filtered[filtered["remarks"].str.contains(filt_q, case=False, na=False)]

        # Summary tiles
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Income",      fmt_inr(sum_tag(filtered, INCOME_TAGS), True))
        c2.metric("Expenses",    fmt_inr(abs(sum_tag(filtered, ["Expense"])), True))
        c3.metric("TDS",         fmt_inr(abs(sum_tag(filtered, ["TDS"])), True))
        c4.metric("Investments", fmt_inr(abs(sum_tag(filtered, ["Investment"])), True))
        c5.metric("Entries",     len(filtered))

        st.markdown("")

        # Bulk actions
        selected_indices = []
        if len(filtered) > 0:
            display_cols = ["month", "fy", "tag"] + BANK_COLS + ["total", "remarks"]
            display = filtered[display_cols].copy()
            display.columns = ["Month", "FY", "Tag", "NRO Exp", "NRO Sav", "NRE AB", "NRE PT", "NRE Atharv", "Total", "Remarks"]

            st.dataframe(display, use_container_width=True, hide_index=True)

            # Bulk delete
            st.markdown("**Bulk actions**")
            col_a, col_b = st.columns([3,1])
            with col_a:
                del_idx = st.multiselect(
                    "Select rows to delete (by row number in full dataset)",
                    options=list(filtered.index),
                    format_func=lambda i: f"#{i} — {df.loc[i,'month']} | {df.loc[i,'tag']} | {df.loc[i,'remarks'][:40]}"
                )
            with col_b:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑 Delete selected", disabled=not del_idx):
                    new_df = df.drop(index=del_idx).reset_index(drop=True)
                    with st.spinner("Saving…"):
                        save(new_df)
                    st.success(f"Deleted {len(del_idx)} entries")
                    refresh()
        else:
            st.info("No entries match your filters.")

    # ── TAB: ADD / EDIT ──────────────────────────────────────────────────────
    with tab_add:
        st.subheader("Add or Edit Entry")

        mode = st.radio("Mode", ["Add new entry", "Edit existing entry"], horizontal=True)

        entry_data = {}
        edit_idx = None

        if mode == "Edit existing entry":
            recent = df[df["tag"].notna() & (df["tag"] != "")].tail(50)
            edit_choice = st.selectbox(
                "Select entry to edit",
                options=list(recent.index),
                format_func=lambda i: f"{df.loc[i,'month']} | {df.loc[i,'fy']} | {df.loc[i,'tag']} | ₹{df.loc[i,'total']:,.0f} | {str(df.loc[i,'remarks'])[:40]}"
            )
            edit_idx = edit_choice
            row = df.loc[edit_idx]
            entry_data = row.to_dict()

        col1, col2 = st.columns(2)
        with col1:
            month_val = entry_data.get("month", datetime.now().strftime("%Y-%m"))
            try:
                month_date = datetime.strptime(str(month_val)[:7], "%Y-%m").date().replace(day=1)
            except:
                month_date = date.today().replace(day=1)
            month_picked = st.date_input("Month", value=month_date, format="YYYY-MM-DD")
            month_str = month_picked.strftime("%Y-%m")
            auto_fy = get_fy_for_month(month_str)

        with col2:
            fy_val = entry_data.get("fy", auto_fy)
            all_fys_with_new = list(reversed(all_fys)) + ["FY27-28", "FY28-29"]
            fy_options = sorted(set(all_fys_with_new), key=lambda x: x[2:4])
            if fy_val not in fy_options:
                fy_options.append(fy_val)
            fy_picked = st.selectbox("Financial Year", options=list(reversed(fy_options)),
                                     index=0 if fy_val not in fy_options else list(reversed(fy_options)).index(fy_val))

        col3, col4 = st.columns(2)
        with col3:
            tag_val = entry_data.get("tag", "Income-Res")
            tag_picked = st.selectbox("Tag", [t for t in ALL_TAGS if t],
                                      index=max(0, [t for t in ALL_TAGS if t].index(tag_val) if tag_val in ALL_TAGS else 0))
        with col4:
            remarks_val = entry_data.get("remarks", "")
            remarks_picked = st.text_input("Remarks", value=str(remarks_val) if remarks_val else "")

        st.markdown("**Bank account splits** — Total is calculated automatically from splits")
        c1, c2, c3, c4, c5 = st.columns(5)
        splits = {}
        for col_w, col_k, bank in zip([c1,c2,c3,c4,c5], BANK_COLS, BANKS):
            default = float(entry_data.get(col_k, 0) or 0)
            splits[col_k] = col_w.number_input(bank, value=default, step=1000.0, format="%.0f", key=f"split_{col_k}")

        auto_total = sum(splits.values())
        st.metric("Total (auto-calculated)", fmt_inr(auto_total), delta=None)

        col_s1, col_s2 = st.columns([1, 4])
        with col_s1:
            label = "💾 Save entry" if mode == "Add new entry" else "💾 Update entry"
            if st.button(label, use_container_width=True):
                new_row = {
                    "month": month_str,
                    "fy": fy_picked,
                    "tag": tag_picked,
                    "total": auto_total,
                    "nro_exp": splits["nro_exp"],
                    "nro_sav": splits["nro_sav"],
                    "nre_ab": splits["nre_ab"],
                    "nre_pt": splits["nre_pt"],
                    "nre_atharv": splits["nre_atharv"],
                    "remarks": remarks_picked,
                }
                if mode == "Add new entry":
                    new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                else:
                    new_df = df.copy()
                    for k, v in new_row.items():
                        new_df.at[edit_idx, k] = v
                with st.spinner("Saving to OneDrive…"):
                    save(new_df)
                st.success("✓ Saved successfully")
                refresh()

    # ── TAB: CLONE MONTH ─────────────────────────────────────────────────────
    with tab_clone:
        st.subheader("Clone Month")
        st.caption("Carry forward recurring entries to a future month")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Source**")
            src_fy = st.selectbox("Source FY", list(reversed(all_fys)), key="clone_src_fy")
            src_months = sorted(df[df["fy"] == src_fy]["month"].dropna().unique())
            src_month = st.selectbox("Source Month", src_months, index=len(src_months)-1 if src_months else 0, key="clone_src_month")
        with col2:
            st.markdown("**Target**")
            dst_fy = st.selectbox("Target FY", list(reversed(all_fys)) + ["FY26-27","FY27-28"], key="clone_dst_fy")
            dst_month = st.text_input("Target Month (YYYY-MM)", value="2026-07", key="clone_dst_month")

        skip_tags = ["Balance", "Cashflow", "Transfer"]
        clone_src = df[(df["fy"] == src_fy) & (df["month"] == src_month) & (~df["tag"].isin(skip_tags))]

        if clone_src.empty:
            st.info("No cloneable entries for this month.")
        else:
            st.markdown(f"**{len(clone_src)} entries from {src_month}** — select and adjust amounts:")
            clone_rows = []
            for i, (idx, row) in enumerate(clone_src.iterrows()):
                c1, c2, c3 = st.columns([1, 3, 2])
                with c1:
                    selected = st.checkbox("", value=True, key=f"clone_sel_{i}")
                with c2:
                    st.markdown(f"`{row['tag']}` — {row['remarks'][:50]}")
                with c3:
                    amt = st.number_input("Amount", value=float(row["total"] or 0),
                                          step=1000.0, format="%.0f", key=f"clone_amt_{i}", label_visibility="collapsed")
                if selected:
                    clone_rows.append((row, amt))

            if st.button(f"📋 Clone {len(clone_rows)} selected entries → {dst_month}", disabled=not clone_rows):
                new_entries = []
                for row, new_total in clone_rows:
                    ratio = new_total / row["total"] if row["total"] else 1
                    new_entries.append({
                        "month": dst_month,
                        "fy": dst_fy,
                        "tag": row["tag"],
                        "total": new_total,
                        "nro_exp": round((row["nro_exp"] or 0) * ratio),
                        "nro_sav": round((row["nro_sav"] or 0) * ratio),
                        "nre_ab": round((row["nre_ab"] or 0) * ratio),
                        "nre_pt": round((row["nre_pt"] or 0) * ratio),
                        "nre_atharv": round((row["nre_atharv"] or 0) * ratio),
                        "remarks": row["remarks"],
                    })
                new_df = pd.concat([df, pd.DataFrame(new_entries)], ignore_index=True)
                with st.spinner("Saving to OneDrive…"):
                    save(new_df)
                st.success(f"✓ {len(new_entries)} entries cloned to {dst_month} ({dst_fy})")
                refresh()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3: TAX CALCULATIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧾 Tax Calculations":
    st.title("Tax Calculations")
    st.caption("Old regime · Income attribution per family rules")

    # Income attribution rules table
    st.markdown("""
| Income Type | Abhishek | Praggya |
|---|---|---|
| Residential rent — NRO Expense | ✅ 100% | — |
| Residential rent — NRO Savings | — | ✅ 100% |
| Commercial rent (Vatika) | ✅ 50% | ✅ 50% |
| Interest, dividends, other income | ✅ 100% | — |
| Investments (80C deduction) | ✅ 50% share | ✅ 50% share |
""")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        tax_fy = st.selectbox("Financial Year", list(reversed(all_fys)), key="tax_fy")
    with col2:
        ded_80c = st.number_input("80C cap per person (₹)", value=150000, step=10000)
    with col3:
        stat_ded = st.selectbox("Commercial rent statutory deduction", [0.30, 0.25, 0.40],
                                format_func=lambda x: f"{int(x*100)}%")

    tds_split_pct = st.selectbox("TDS attribution (AB / PT)", [50, 60, 40, 100, 0],
                                  format_func=lambda x: f"{x}% / {100-x}%")
    tds_split = tds_split_pct / 100

    rows = fy_rows(df, tax_fy)
    if rows.empty:
        st.warning(f"No data for {tax_fy}")
    else:
        # Income attribution
        res_rows = rows[rows["tag"] == "Income-Res"]
        ab_res   = float(res_rows["nro_exp"].fillna(0).sum())
        pt_res   = float(res_rows["nro_sav"].fillna(0).sum())

        com_gross = sum_tag(rows, ["Income-Com"])
        ab_com = com_gross * 0.5
        pt_com = com_gross * 0.5

        ab_interest = sum_tag(rows, ["Income"])
        pt_interest = 0.0

        total_inv    = abs(sum_tag(rows, ["Investment"]))
        ab_inv_80c   = min(total_inv * 0.5, ded_80c)
        pt_inv_80c   = min(total_inv * 0.5, ded_80c)

        tds_gross   = abs(sum_tag(rows, ["TDS"]))
        tds_refund  = sum_tag(rows, ["TDS Income"])
        tds_net     = tds_gross - tds_refund
        ab_tds      = round(tds_net * tds_split)
        pt_tds      = round(tds_net * (1 - tds_split))

        ab_com_net  = ab_com * (1 - stat_ded)
        pt_com_net  = pt_com * (1 - stat_ded)
        ab_taxable  = max(0, ab_res + ab_com_net - ab_inv_80c + ab_interest)
        pt_taxable  = max(0, pt_res + pt_com_net - pt_inv_80c + pt_interest)

        def calc_tax(income):
            if income <= 250000: return 0
            t = min(income - 250000, 250000) * 0.05
            if income > 500000:  t += min(income - 500000, 500000) * 0.20
            if income > 1000000: t += (income - 1000000) * 0.30
            return round(t)

        ab_tax  = calc_tax(ab_taxable)
        pt_tax  = calc_tax(pt_taxable)
        ab_bal  = ab_tax - ab_tds
        pt_bal  = pt_tax - pt_tds

        def person_card(name, res, com_gross, com_net, inv80c, interest, taxable, tax, tds_paid, balance):
            is_ab = "AB" in name
            status = "🔴 Payable" if balance > 0 else "🟢 Refund"
            st.markdown(f"### {name}")
            rows_data = [
                ("Residential rent (NRO {})".format("Expense" if is_ab else "Savings"), fmt_inr(res), "income"),
                ("Commercial rent — 50% share (gross)", fmt_inr(com_gross), "income"),
                (f"Less: {int(stat_ded*100)}% statutory deduction", f"-{fmt_inr(com_gross * stat_ded)}", "deduction"),
                ("Interest, dividends & other income", fmt_inr(interest) if interest else "—", "income"),
                (f"Less: 80C (investments — 50% share, capped)", f"-{fmt_inr(inv80c)}", "deduction"),
                ("**Taxable income**", f"**{fmt_inr(taxable)}**", "total"),
                ("Up to ₹2.5L @ 0%", "—", "slab"),
                ("₹2.5L–₹5L @ 5%", fmt_inr(min(max(taxable-250000,0),250000)*0.05) if taxable > 250000 else "—", "slab"),
                ("₹5L–₹10L @ 20%", fmt_inr(min(max(taxable-500000,0),500000)*0.20) if taxable > 500000 else "—", "slab"),
                ("Above ₹10L @ 30%", fmt_inr(max(taxable-1000000,0)*0.30) if taxable > 1000000 else "—", "slab"),
                ("**Total tax liability**", f"**{fmt_inr(tax)}**", "total"),
                ("TDS deducted", f"-{fmt_inr(tds_paid)}", "deduction"),
                (f"**{status}**", f"**{fmt_inr(abs(balance))}**", "result"),
            ]
            tbl_df = pd.DataFrame(rows_data, columns=["Item", "Amount", "_type"])
            st.table(tbl_df[["Item", "Amount"]])
            st.metric(f"{status}", fmt_inr(abs(balance)),
                      delta="Tax payable to ITD" if balance > 0 else "Refund expected from ITD",
                      delta_color="inverse" if balance > 0 else "normal")

        col_ab, col_pt = st.columns(2)
        with col_ab:
            person_card("Abhishek (AB)", ab_res, ab_com, ab_com_net,
                        ab_inv_80c, ab_interest, ab_taxable, ab_tax, ab_tds, ab_bal)
        with col_pt:
            person_card("Praggya (PT)", pt_res, pt_com, pt_com_net,
                        pt_inv_80c, pt_interest, pt_taxable, pt_tax, pt_tds, pt_bal)

        st.markdown("---")

        # YoY TDS chart
        st.subheader("Year-on-year TDS trend")
        trend_data = []
        for fy in all_fys[1:]:
            r = fy_rows(df, fy)
            net_tds = abs(sum_tag(r, ["TDS"])) - sum_tag(r, ["TDS Income"])
            trend_data.append({"FY": fy, "Net TDS": round(net_tds)})
        if trend_data:
            tdf = pd.DataFrame(trend_data)
            fig = px.bar(tdf, x="FY", y="Net TDS", color_discrete_sequence=["#a07020"],
                         labels={"Net TDS": "Net TDS Paid (₹)"})
            fig.update_layout(height=250, plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=0,r=0,t=10,b=0),
                              yaxis=dict(tickformat=",.0f", gridcolor="#f0ede6"))
            st.plotly_chart(fig, use_container_width=True)

        st.caption("Consult your CA before filing. TDS split is an estimate — adjust the selector above.")
