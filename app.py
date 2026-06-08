"""
India Money Journal — Streamlit App
Data stored in Google Sheets via Google Sheets API
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, date
import warnings
warnings.filterwarnings("ignore")

from data_layer import load_data, save_data, get_fy_for_month
from gsheets import get_gsheets_client

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India Money Journal",
    page_icon="₹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design tokens (mirror HTML tool) ──────────────────────────────────────────
INK       = "#1a1a18"
INK2      = "#4a4a44"
INK3      = "#8a8a80"
PAPER     = "#faf9f6"
PAPER2    = "#f2f0ea"
RULE      = "#dedad0"
ACCENT    = "#c8602a"
GREEN     = "#2a7a50"
GREEN_BG  = "#eaf4ee"
RED       = "#b03020"
RED_BG    = "#faecea"
GOLD      = "#a07020"
GOLD_BG   = "#faf0da"
BLUE      = "#2060a0"
BLUE_BG   = "#eaf0fa"

BANKS      = ["NRO Expense", "NRO Savings", "NRE AB", "NRE PT", "NRE Atharv"]
BANK_COLS  = ["nro_exp", "nro_sav", "nre_ab", "nre_pt", "nre_atharv"]
BANK_COLORS = ["#378ADD", "#1D9E75", "#D85A30", "#BA7517", "#D4537E"]
ALL_TAGS   = [
    "Income-Res", "Income-Com", "Income", "Expense", "TDS", "TDS Income",
    "Investment", "Cashflow", "Savings", "Gift", "Transfer", "Loan", "Balance", ""
]
INCOME_TAGS = ["Income", "Income-Res", "Income-Com", "TDS Income"]

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    color: {INK};
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: {INK} !important;
    border-right: none !important;
}}
[data-testid="stSidebar"] * {{
    color: rgba(255,255,255,0.75) !important;
}}
[data-testid="stSidebar"] .sidebar-logo {{
    font-family: 'DM Serif Display', serif !important;
    font-size: 20px !important;
    color: #fff !important;
    line-height: 1.3;
    padding: 8px 0 4px;
}}
[data-testid="stSidebar"] .sidebar-sub {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: rgba(255,255,255,0.35) !important;
    margin-top: 2px;
}}
[data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,0.1) !important;
    margin: 12px 0;
}}
[data-testid="stSidebar"] .stRadio label {{
    color: rgba(255,255,255,0.65) !important;
    font-size: 13px !important;
    padding: 4px 0;
}}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] {{
    background: transparent !important;
}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
    font-size: 11px !important;
    color: rgba(255,255,255,0.3) !important;
}}
[data-testid="stSidebar"] .stButton button {{
    background: rgba(255,255,255,0.07) !important;
    border: none !important;
    color: rgba(255,255,255,0.65) !important;
    font-size: 12px !important;
    border-radius: 6px !important;
    transition: background 0.15s !important;
}}
[data-testid="stSidebar"] .stButton button:hover {{
    background: rgba(255,255,255,0.14) !important;
}}

/* ── Main area ── */
.main {{
    background: {PAPER} !important;
}}
.block-container {{
    padding: 2rem 2.5rem 2rem !important;
    max-width: 1200px !important;
}}

/* ── Page title ── */
h1 {{
    font-family: 'DM Serif Display', serif !important;
    font-size: 28px !important;
    color: {INK} !important;
    font-weight: 400 !important;
    margin-bottom: 0.25rem !important;
}}
h2, h3 {{
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    color: {INK} !important;
}}
h2 {{ font-size: 17px !important; margin-top: 1.5rem !important; }}
h3 {{ font-size: 14px !important; }}

/* ── Metric cards ── */
[data-testid="stMetric"] {{
    background: #fff !important;
    border: 1px solid {RULE} !important;
    border-radius: 10px !important;
    padding: 16px 18px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}}
[data-testid="stMetric"] label {{
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: {INK3} !important;
    font-weight: 500 !important;
}}
[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    font-family: 'DM Mono', monospace !important;
    font-size: 20px !important;
    font-weight: 500 !important;
    color: {INK} !important;
}}
[data-testid="stMetric"] [data-testid="stMetricDelta"] {{
    font-size: 11px !important;
}}

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background: {PAPER2} !important;
    border-radius: 8px !important;
    padding: 4px !important;
    gap: 2px !important;
    border-bottom: none !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    background: transparent !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: {INK3} !important;
    padding: 8px 18px !important;
    border: none !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    background: #fff !important;
    color: {INK} !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border: 1px solid {RULE} !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    background: #fff !important;
}}

/* ── Inputs & selects ── */
[data-baseweb="input"] input,
[data-baseweb="select"] div,
[data-baseweb="textarea"] textarea {{
    background: #fff !important;
    border-color: {RULE} !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    color: {INK} !important;
}}
[data-baseweb="input"] input:focus,
[data-baseweb="select"] div:focus {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 2px rgba(200,96,42,0.12) !important;
}}

/* ── Buttons ── */
.stButton button {{
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    border: 1px solid {RULE} !important;
    background: #fff !important;
    color: {INK2} !important;
    transition: all 0.15s !important;
}}
.stButton button:hover {{
    border-color: {INK3} !important;
    color: {INK} !important;
}}
.stButton [kind="primary"] button,
.stButton button[kind="primary"] {{
    background: {ACCENT} !important;
    border-color: {ACCENT} !important;
    color: #fff !important;
}}

/* ── Section labels ── */
.section-label {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {INK3};
    font-weight: 500;
    margin-bottom: 10px;
    margin-top: 4px;
}}

/* ── Balance table ── */
.bal-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    background: #fff;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid {RULE};
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}
.bal-table th {{
    background: {PAPER2};
    padding: 10px 16px;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: {INK3};
    font-weight: 500;
    border-bottom: 1px solid {RULE};
    text-align: left;
}}
.bal-table td {{
    padding: 11px 16px;
    border-bottom: 1px solid {PAPER2};
    vertical-align: middle;
}}
.bal-table tr:last-child td {{ border-bottom: none; }}
.bal-table tr:hover td {{ background: {PAPER}; }}
.bal-acct {{ font-weight: 500; color: {INK2}; }}
.bal-amount {{ font-family: 'DM Mono', monospace; font-weight: 600; font-size: 15px; }}
.bal-pos {{ color: {GREEN}; }}
.bal-neg {{ color: {RED}; }}
.bal-mov {{ font-family: 'DM Mono', monospace; font-size: 12px; }}
.bal-mov-pos {{ color: {GREEN}; }}
.bal-mov-neg {{ color: {RED}; }}
.bal-muted {{ font-family: 'DM Mono', monospace; font-size: 12px; color: {INK3}; }}
.acct-dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:8px; }}

/* ── Tax table ── */
.tax-person-card {{
    background: #fff;
    border: 1px solid {RULE};
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}}
.tax-person-head {{
    background: {PAPER2};
    padding: 14px 18px;
    border-bottom: 1px solid {RULE};
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.tax-person-name {{ font-family: 'DM Serif Display', serif; font-size: 17px; }}
.tax-row {{ display:flex; justify-content:space-between; padding:9px 18px; border-bottom:1px solid {PAPER2}; font-size:13px; }}
.tax-row:last-child {{ border-bottom:none; }}
.tax-row-total {{ background:{PAPER2}; font-weight:600; }}
.tax-row-result {{ background:{INK}; color:#fff; font-weight:600; border-radius: 0 0 10px 10px; }}
.tax-label {{ color:{INK2}; }}
.tax-badge-pay {{ background:{RED_BG}; color:{RED}; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:500; }}
.tax-badge-ref {{ background:{GREEN_BG}; color:{GREEN}; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:500; }}

/* ── Divider ── */
.section-divider {{
    border: none;
    border-top: 1px solid {RULE};
    margin: 24px 0;
}}

/* ── Number input arrows ── */
input[type=number] {{ font-family: 'DM Mono', monospace !important; }}

/* ── Alerts ── */
[data-testid="stAlert"] {{ border-radius: 8px !important; font-size: 13px !important; }}

/* ── Success/info ── */
.stSuccess {{ background: {GREEN_BG} !important; color: {GREEN} !important; }}
</style>
""", unsafe_allow_html=True)


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner="Loading journal data…")
def get_data():
    client = get_gsheets_client()
    return load_data(client)


def refresh():
    st.cache_data.clear()
    st.rerun()


def save(df):
    client = get_gsheets_client()
    save_data(df, client)
    st.cache_data.clear()


# ── Balance calculation ────────────────────────────────────────────────────────
def compute_balances(df):
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


def get_fy_movement(df, fy, current, base_idx):
    bal_rows = df[
        (df["tag"] == "Balance") &
        (~df["remarks"].str.contains("Opening Balance", case=False, na=False))
    ]
    fy_bal = bal_rows[bal_rows["fy"] == fy]
    if not fy_bal.empty:
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
        fy_r = df[(df["fy"] == fy) & (df["tag"] != "Balance")]
        return {c: float(fy_r[c].fillna(0).sum()) for c in BANK_COLS}


# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt(v, compact=False):
    v = float(v or 0)
    sign = "-" if v < 0 else ""
    a = abs(v)
    if compact:
        if a >= 1e7: return f"{sign}₹{a/1e7:.2f}Cr"
        if a >= 1e5: return f"{sign}₹{a/1e5:.1f}L"
        if a >= 1e3: return f"{sign}₹{a/1e3:.0f}K"
        return f"{sign}₹{a:.0f}"
    return f"{sign}₹{a:,.0f}"


def fy_rows(df, fy):
    return df[df["fy"] == fy].copy()


def sum_tag(df, tags):
    return float(df[df["tag"].isin(tags)]["total"].fillna(0).sum())


def get_all_fys(df):
    return sorted(df["fy"].dropna().unique(), key=lambda x: x[2:4])


def tag_color(tag):
    if tag in ["Income","Income-Res","Income-Com","TDS Income"]: return GREEN
    if tag == "Expense": return RED
    if tag == "TDS": return GOLD
    if tag == "Investment": return BLUE
    return INK3


def tag_bg(tag):
    if tag in ["Income","Income-Res","Income-Com","TDS Income"]: return GREEN_BG
    if tag == "Expense": return RED_BG
    if tag == "TDS": return GOLD_BG
    if tag == "Investment": return BLUE_BG
    return PAPER2


def badge(tag):
    if not tag: return "—"
    return f'<span style="background:{tag_bg(tag)};color:{tag_color(tag)};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500">{tag}</span>'


def plotly_layout(fig, height=260):
    fig.update_layout(
        height=height,
        plot_bgcolor=PAPER,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color=INK2, size=11),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, font=dict(size=11)),
        xaxis=dict(gridcolor=RULE, linecolor=RULE, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=RULE, linecolor="rgba(0,0,0,0)",
                   tickfont=dict(size=10), tickformat=",.0f"),
    )
    return fig


# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">India Money<br>Journal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">AB · Family Ledger</div>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown('<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.09em;color:rgba(255,255,255,0.3);margin-bottom:8px">Overview</div>', unsafe_allow_html=True)
    page = st.radio(
        "nav",
        ["📊  Cashflow Summary", "📒  Cashflow Capture", "🧾  Tax Calculations"],
        label_visibility="collapsed"
    )
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("↻  Refresh data", use_container_width=True):
        refresh()
    st.markdown('<p style="margin-top:8px">Auto-synced · Google Sheets · Amounts in INR (₹)</p>', unsafe_allow_html=True)


# ── Load data ──────────────────────────────────────────────────────────────────
try:
    df = get_data()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.info("Check your Google Sheets credentials in Streamlit secrets.")
    st.stop()

all_fys = get_all_fys(df)
current_bal, base_idx = compute_balances(df)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — CASHFLOW SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊  Cashflow Summary":
    st.title("Cashflow Summary")

    # FY selector
    col_fy, _ = st.columns([2, 5])
    with col_fy:
        sel_fy = st.selectbox("Financial Year", list(reversed(all_fys)), index=0, key="sum_fy", label_visibility="collapsed")

    mov = get_fy_movement(df, sel_fy, current_bal, base_idx)

    # ── Account balance table ──────────────────────────────────────────────
    st.markdown('<div class="section-label">Account balances &amp; movement</div>', unsafe_allow_html=True)

    rows_html = ""
    for i, (bank, col) in enumerate(zip(BANKS, BANK_COLS)):
        bal  = current_bal[col]
        net  = mov[col]
        inf  = float(df[(df["fy"] == sel_fy) & (df[col] > 0)][col].sum())
        outf = float(df[(df["fy"] == sel_fy) & (df[col] < 0)][col].sum())
        bal_cls  = "bal-pos" if bal  >= 0 else "bal-neg"
        net_cls  = "bal-mov-pos" if net >= 0 else "bal-mov-neg"
        rows_html += f"""
        <tr>
          <td class="bal-acct">
            <span class="acct-dot" style="background:{BANK_COLORS[i]}"></span>{bank}
          </td>
          <td><span class="bal-amount {bal_cls}">{fmt(bal)}</span></td>
          <td><span class="bal-mov {net_cls}">{fmt(net, True)}</span></td>
          <td><span class="bal-muted">{'↑ '+fmt(inf, True) if inf else '—'}</span></td>
          <td><span class="bal-muted">{'↓ '+fmt(abs(outf), True) if outf else '—'}</span></td>
        </tr>"""

    st.markdown(f"""
    <table class="bal-table">
      <thead><tr>
        <th>Account</th>
        <th>Balance</th>
        <th>Net ({sel_fy})</th>
        <th>Inflow ↑</th>
        <th>Outflow ↓</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── FY metric tiles ────────────────────────────────────────────────────
    st.markdown(f'<div class="section-label">{sel_fy} summary</div>', unsafe_allow_html=True)
    rows = fy_rows(df, sel_fy)
    inc_res = sum_tag(rows, ["Income-Res"])
    inc_com = sum_tag(rows, ["Income-Com"])
    inc_oth = sum_tag(rows, ["Income"])
    expense = sum_tag(rows, ["Expense"])
    tds     = sum_tag(rows, ["TDS"])
    tds_ref = sum_tag(rows, ["TDS Income"])
    inv     = sum_tag(rows, ["Investment"])
    net     = inc_res + inc_com + inc_oth + expense

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("Res. Rent",    fmt(inc_res, True))
    c2.metric("Com. Rent",    fmt(inc_com, True))
    c3.metric("Other Income", fmt(inc_oth, True))
    c4.metric("Expenses",     fmt(abs(expense), True))
    c5.metric("TDS Deducted", fmt(abs(tds), True))
    c6.metric("TDS Refund",   fmt(tds_ref, True))
    c7.metric("Net Income",   fmt(net, True))

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Monthly bar chart ─────────────────────────────────────────────────
    st.markdown('<div class="section-label">Monthly income vs expenses</div>', unsafe_allow_html=True)
    monthly = []
    for m in sorted(rows["month"].dropna().unique()):
        mr = rows[rows["month"] == m]
        monthly.append({
            "m": m,
            "Income":  float(mr[mr["tag"].isin(["Income","Income-Res","Income-Com"])]["total"].sum()),
            "Expense": float(abs(mr[mr["tag"] == "Expense"]["total"].sum())),
            "TDS":     float(abs(mr[mr["tag"] == "TDS"]["total"].sum())),
        })
    if monthly:
        mdf = pd.DataFrame(monthly)
        fig = go.Figure()
        fig.add_bar(x=mdf["m"], y=mdf["Income"],  name="Income",  marker_color=GREEN,  marker_line_width=0, opacity=0.85)
        fig.add_bar(x=mdf["m"], y=mdf["Expense"], name="Expense", marker_color=RED,    marker_line_width=0, opacity=0.85)
        fig.add_bar(x=mdf["m"], y=mdf["TDS"],     name="TDS",     marker_color=GOLD,   marker_line_width=0, opacity=0.85)
        plotly_layout(fig, 280)
        fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.05)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Monthly breakdown table ───────────────────────────────────────────
    st.markdown('<div class="section-label">Monthly breakdown</div>', unsafe_allow_html=True)
    mb = []
    for m in sorted(rows["month"].dropna().unique()):
        mr = rows[rows["month"] == m]
        mb.append({
            "Month":       m,
            "Res Rent":    fmt(sum_tag(mr, ["Income-Res"])),
            "Com Rent":    fmt(sum_tag(mr, ["Income-Com"])),
            "Other":       fmt(sum_tag(mr, ["Income"])),
            "Expense":     fmt(sum_tag(mr, ["Expense"])),
            "TDS":         fmt(sum_tag(mr, ["TDS"])),
            "Investment":  fmt(sum_tag(mr, ["Investment"])),
            "Net":         fmt(sum_tag(mr, ["Income","Income-Res","Income-Com"]) + sum_tag(mr, ["Expense"])),
        })
    if mb:
        st.dataframe(pd.DataFrame(mb), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — CASHFLOW CAPTURE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📒  Cashflow Capture":
    st.title("Cashflow Capture")

    tab_ledger, tab_add, tab_clone = st.tabs(["  Ledger  ", "  Add / Edit  ", "  Clone Month  "])

    # ── LEDGER ────────────────────────────────────────────────────────────
    with tab_ledger:
        fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 3])
        with fc1: filt_fy   = st.selectbox("FY",      ["All"] + list(reversed(all_fys)), index=1, label_visibility="visible")
        with fc2: filt_tag  = st.selectbox("Tag",     ["All"] + [t for t in ALL_TAGS if t], label_visibility="visible")
        with fc3: filt_bank = st.selectbox("Account", ["All"] + BANKS, label_visibility="visible")
        with fc4: filt_q    = st.text_input("Search remarks", placeholder="e.g. Vatika, SIP…")

        filtered = df.copy()
        if filt_fy   != "All": filtered = filtered[filtered["fy"] == filt_fy]
        if filt_tag  != "All": filtered = filtered[filtered["tag"] == filt_tag]
        if filt_bank != "All":
            ck = BANK_COLS[BANKS.index(filt_bank)]
            filtered = filtered[filtered[ck].fillna(0) != 0]
        if filt_q: filtered = filtered[filtered["remarks"].str.contains(filt_q, case=False, na=False)]

        # Tiles
        t1, t2, t3, t4, t5 = st.columns(5)
        t1.metric("Income",      fmt(sum_tag(filtered, INCOME_TAGS), True))
        t2.metric("Expenses",    fmt(abs(sum_tag(filtered, ["Expense"])), True))
        t3.metric("TDS",         fmt(abs(sum_tag(filtered, ["TDS"])), True))
        t4.metric("Investments", fmt(abs(sum_tag(filtered, ["Investment"])), True))
        t5.metric("Entries",     str(len(filtered)))

        st.markdown("")

        if filtered.empty:
            st.info("No entries match your filters.")
        else:
            # Render as styled HTML table
            tbl_rows = ""
            for _, r in filtered.iterrows():
                bank_cells = ""
                for c in BANK_COLS:
                    v = float(r[c] or 0)
                    if v:
                        cls = f"color:{GREEN}" if v > 0 else f"color:{RED}"
                        bank_cells += f'<td style="font-family:DM Mono,monospace;font-size:12px;{cls};text-align:right">{fmt(v)}</td>'
                    else:
                        bank_cells += f'<td style="color:{INK3};text-align:right">—</td>'
                tot = float(r["total"] or 0)
                tot_cls = f"color:{GREEN}" if tot >= 0 else f"color:{RED}"
                tbl_rows += f"""<tr style="border-bottom:1px solid {PAPER2}">
                  <td style="color:{INK3};font-size:12px">{r['month'] or ''}</td>
                  <td style="color:{INK3};font-size:11px">{r['fy']}</td>
                  <td>{badge(r['tag'])}</td>
                  {bank_cells}
                  <td style="font-family:DM Mono,monospace;font-size:13px;font-weight:600;{tot_cls};text-align:right">{fmt(tot)}</td>
                  <td style="color:{INK3};font-size:12px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{r['remarks']}">{str(r['remarks'])[:45]}</td>
                </tr>"""

            th_style = f"padding:8px 12px;background:{PAPER2};font-size:10px;text-transform:uppercase;letter-spacing:0.06em;color:{INK3};font-weight:500;border-bottom:1px solid {RULE};white-space:nowrap"
            td_style = f"padding:8px 12px"
            st.markdown(f"""
            <div style="border:1px solid {RULE};border-radius:10px;overflow:auto;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.06)">
            <table style="width:100%;border-collapse:collapse;font-size:13px">
              <thead><tr>
                <th style="{th_style}">Month</th>
                <th style="{th_style}">FY</th>
                <th style="{th_style}">Tag</th>
                <th style="{th_style};text-align:right">NRO Exp</th>
                <th style="{th_style};text-align:right">NRO Sav</th>
                <th style="{th_style};text-align:right">NRE AB</th>
                <th style="{th_style};text-align:right">NRE PT</th>
                <th style="{th_style};text-align:right">NRE Atharv</th>
                <th style="{th_style};text-align:right">Total</th>
                <th style="{th_style}">Remarks</th>
              </tr></thead>
              <tbody style="font-family:DM Sans,sans-serif">{"".join(f'<tr style="">{r}</tr>' if False else tbl_rows)}</tbody>
            </table></div>
            """, unsafe_allow_html=True)

            # Bulk delete
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">Bulk delete</div>', unsafe_allow_html=True)
            del_idx = st.multiselect(
                "Select entries to delete",
                options=list(filtered.index),
                format_func=lambda i: f"{df.loc[i,'month']} · {df.loc[i,'fy']} · {df.loc[i,'tag']} · {fmt(df.loc[i,'total'])} · {str(df.loc[i,'remarks'])[:40]}"
            )
            if del_idx:
                if st.button(f"🗑  Delete {len(del_idx)} selected", type="primary"):
                    new_df = df.drop(index=del_idx).reset_index(drop=True)
                    with st.spinner("Saving…"):
                        save(new_df)
                    st.success(f"✓ Deleted {len(del_idx)} entries")
                    refresh()

    # ── ADD / EDIT ────────────────────────────────────────────────────────
    with tab_add:
        st.markdown('<div class="section-label">Add or edit an entry</div>', unsafe_allow_html=True)
        mode = st.radio("Mode", ["Add new entry", "Edit existing entry"], horizontal=True)

        edit_idx = None
        entry_data = {}

        if mode == "Edit existing entry":
            recent = df[df["tag"].notna() & (df["tag"] != "")].tail(60)
            edit_choice = st.selectbox(
                "Select entry",
                options=list(recent.index),
                format_func=lambda i: f"{df.loc[i,'month']}  ·  {df.loc[i,'fy']}  ·  {df.loc[i,'tag']}  ·  {fmt(df.loc[i,'total'])}  ·  {str(df.loc[i,'remarks'])[:45]}"
            )
            edit_idx = edit_choice
            entry_data = df.loc[edit_idx].to_dict()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            mv = entry_data.get("month", datetime.now().strftime("%Y-%m"))
            try:   md = datetime.strptime(str(mv)[:7], "%Y-%m").date().replace(day=1)
            except: md = date.today().replace(day=1)
            mp = st.date_input("Month", value=md, format="YYYY-MM-DD")
            month_str = mp.strftime("%Y-%m")
            auto_fy = get_fy_for_month(month_str)

        with col2:
            fy_val = entry_data.get("fy", auto_fy)
            fy_opts = sorted(set(list(reversed(all_fys)) + ["FY26-27","FY27-28"]), key=lambda x: x[2:4], reverse=True)
            if fy_val not in fy_opts: fy_opts.insert(0, fy_val)
            fy_picked = st.selectbox("Financial Year", fy_opts)

        with col3:
            tag_val = entry_data.get("tag", "Income-Res")
            tag_opts = [t for t in ALL_TAGS if t]
            tag_picked = st.selectbox("Tag", tag_opts,
                index=tag_opts.index(tag_val) if tag_val in tag_opts else 0)

        with col4:
            remarks_picked = st.text_input("Remarks", value=str(entry_data.get("remarks","") or ""))

        st.markdown('<div class="section-label" style="margin-top:16px">Bank account splits — total auto-calculated</div>', unsafe_allow_html=True)
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        splits = {}
        for cw, ck, bn in zip([sc1,sc2,sc3,sc4,sc5], BANK_COLS, BANKS):
            splits[ck] = cw.number_input(bn, value=float(entry_data.get(ck, 0) or 0),
                                          step=1000.0, format="%.0f")

        auto_total = sum(splits.values())
        total_col = GREEN if auto_total > 0 else RED if auto_total < 0 else INK3
        st.markdown(
            f'<div style="background:#fff;border:1px solid {RULE};border-radius:8px;padding:12px 16px;margin:8px 0 16px;display:inline-block">'
            f'<span style="font-size:10px;text-transform:uppercase;letter-spacing:0.07em;color:{INK3}">Total (auto)</span><br>'
            f'<span style="font-family:DM Mono,monospace;font-size:22px;font-weight:500;color:{total_col}">{fmt(auto_total)}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        if st.button("💾  Save entry", type="primary"):
            new_row = {
                "month": month_str, "fy": fy_picked, "tag": tag_picked,
                "total": auto_total, "remarks": remarks_picked,
                **splits
            }
            if mode == "Add new entry":
                new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            else:
                new_df = df.copy()
                for k, v in new_row.items():
                    new_df.at[edit_idx, k] = v
            with st.spinner("Saving to Google Sheets…"):
                save(new_df)
            st.success("✓ Saved")
            refresh()

    # ── CLONE MONTH ───────────────────────────────────────────────────────
    with tab_clone:
        st.markdown('<div class="section-label">Clone recurring entries to a future month</div>', unsafe_allow_html=True)
        cl1, cl2, arr, cl3, cl4 = st.columns([2, 2, 0.3, 2, 2])
        with cl1: src_fy    = st.selectbox("Source FY",    list(reversed(all_fys)), key="csf")
        with cl2:
            src_months = sorted(df[df["fy"] == src_fy]["month"].dropna().unique())
            src_month  = st.selectbox("Source Month", src_months,
                index=len(src_months)-1 if src_months else 0, key="csm")
        with arr: st.markdown("<br>→", unsafe_allow_html=True)
        with cl3: dst_fy    = st.selectbox("Target FY",    list(reversed(all_fys)) + ["FY26-27","FY27-28"], key="cdf")
        with cl4: dst_month = st.text_input("Target Month", value="2026-07", key="cdm")

        skip = ["Balance","Cashflow","Transfer"]
        clone_src = df[(df["fy"]==src_fy) & (df["month"]==src_month) & (~df["tag"].isin(skip))]

        if clone_src.empty:
            st.info("No cloneable entries for this month.")
        else:
            st.markdown(f'<div class="section-label">{len(clone_src)} entries from {src_month} — select and adjust</div>', unsafe_allow_html=True)
            to_clone = []
            for i, (idx, row) in enumerate(clone_src.iterrows()):
                cc1, cc2, cc3 = st.columns([0.4, 4, 2])
                with cc1: sel = st.checkbox("", value=True, key=f"cs_{i}")
                with cc2:
                    st.markdown(
                        f'<div style="padding:8px 0">{badge(row["tag"])} &nbsp;'
                        f'<span style="font-size:13px;color:{INK2}">{str(row["remarks"])[:55]}</span></div>',
                        unsafe_allow_html=True)
                with cc3:
                    amt = st.number_input("Amount", value=float(row["total"] or 0),
                        step=1000.0, format="%.0f", key=f"ca_{i}", label_visibility="collapsed")
                if sel:
                    to_clone.append((row, amt))

            if st.button(f"📋  Clone {len(to_clone)} entries → {dst_month}", type="primary", disabled=not to_clone):
                new_entries = []
                for row, new_total in to_clone:
                    ratio = new_total / row["total"] if row["total"] else 1
                    new_entries.append({
                        "month": dst_month, "fy": dst_fy,
                        "tag": row["tag"], "total": new_total, "remarks": row["remarks"],
                        "nro_exp":    round((row["nro_exp"]    or 0) * ratio),
                        "nro_sav":    round((row["nro_sav"]    or 0) * ratio),
                        "nre_ab":     round((row["nre_ab"]     or 0) * ratio),
                        "nre_pt":     round((row["nre_pt"]     or 0) * ratio),
                        "nre_atharv": round((row["nre_atharv"] or 0) * ratio),
                    })
                new_df = pd.concat([df, pd.DataFrame(new_entries)], ignore_index=True)
                with st.spinner("Saving…"):
                    save(new_df)
                st.success(f"✓ {len(new_entries)} entries cloned to {dst_month} ({dst_fy})")
                refresh()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — TAX CALCULATIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧾  Tax Calculations":
    st.title("Tax Calculations")
    st.markdown(f'<div style="font-size:13px;color:{INK3};margin-bottom:1.5rem">Old regime · Income attribution per family rules</div>', unsafe_allow_html=True)

    # Attribution rules table
    st.markdown('<div class="section-label">Income attribution rules</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <table class="bal-table" style="margin-bottom:24px">
      <thead><tr>
        <th>Income type</th><th>Abhishek</th><th>Praggya</th>
      </tr></thead>
      <tbody>
        <tr><td class="bal-acct">Residential rent — NRO Expense</td><td style="color:{GREEN};font-weight:500">✓ 100%</td><td style="color:{INK3}">—</td></tr>
        <tr><td class="bal-acct">Residential rent — NRO Savings</td><td style="color:{INK3}">—</td><td style="color:{GREEN};font-weight:500">✓ 100%</td></tr>
        <tr><td class="bal-acct">Commercial rent (Vatika)</td><td style="color:{ACCENT};font-weight:500">✓ 50%</td><td style="color:{ACCENT};font-weight:500">✓ 50%</td></tr>
        <tr><td class="bal-acct">Interest, dividends &amp; other income</td><td style="color:{GREEN};font-weight:500">✓ 100%</td><td style="color:{INK3}">—</td></tr>
        <tr><td class="bal-acct">Investments (80C deduction)</td><td style="color:{ACCENT};font-weight:500">✓ 50% share</td><td style="color:{ACCENT};font-weight:500">✓ 50% share</td></tr>
      </tbody>
    </table>
    """, unsafe_allow_html=True)

    # Controls
    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1: tax_fy    = st.selectbox("Financial Year", list(reversed(all_fys)), key="tax_fy")
    with ac2: ded_80c   = st.number_input("80C cap per person (₹)", value=150000, step=10000)
    with ac3: stat_ded  = st.selectbox("Statutory deduction", [0.30, 0.25, 0.40],
                            format_func=lambda x: f"{int(x*100)}% (commercial rent)")
    with ac4: tds_pct   = st.selectbox("TDS split (AB / PT)", [50,60,40,100,0],
                            format_func=lambda x: f"{x}% / {100-x}%")

    tds_split = tds_pct / 100
    rows = fy_rows(df, tax_fy)

    if rows.empty:
        st.warning(f"No data for {tax_fy}")
    else:
        res_rows  = rows[rows["tag"] == "Income-Res"]
        ab_res    = float(res_rows["nro_exp"].fillna(0).sum())
        pt_res    = float(res_rows["nro_sav"].fillna(0).sum())
        com_gross = sum_tag(rows, ["Income-Com"])
        ab_com    = com_gross * 0.5
        pt_com    = com_gross * 0.5
        ab_int    = sum_tag(rows, ["Income"])
        total_inv = abs(sum_tag(rows, ["Investment"]))
        ab_80c    = min(total_inv * 0.5, ded_80c)
        pt_80c    = min(total_inv * 0.5, ded_80c)
        tds_gross = abs(sum_tag(rows, ["TDS"]))
        tds_ref   = sum_tag(rows, ["TDS Income"])
        tds_net   = tds_gross - tds_ref
        ab_tds    = round(tds_net * tds_split)
        pt_tds    = round(tds_net * (1 - tds_split))
        ab_taxable = max(0, ab_res + ab_com*(1-stat_ded) - ab_80c + ab_int)
        pt_taxable = max(0, pt_res + pt_com*(1-stat_ded) - pt_80c)

        def calc_tax(inc):
            if inc <= 250000: return 0
            t = min(inc-250000, 250000) * 0.05
            if inc > 500000:  t += min(inc-500000,  500000) * 0.20
            if inc > 1000000: t += (inc - 1000000) * 0.30
            return round(t)

        ab_tax  = calc_tax(ab_taxable)
        pt_tax  = calc_tax(pt_taxable)
        ab_bal  = ab_tax - ab_tds
        pt_bal  = pt_tax - pt_tds

        def slab_row(label, income, low, high, rate):
            taxable = min(max(income - low, 0), high - low)
            amt = fmt(round(taxable * rate)) if taxable > 0 else "—"
            color = RED if taxable > 0 else INK3
            return f'<div class="tax-row"><span class="tax-label" style="padding-left:12px">{label}</span><span style="font-family:DM Mono,monospace;font-size:12px;color:{color}">{amt}</span></div>'

        def person_html(name, res, com, inv80c, interest, taxable, tax, tds_paid, balance, is_ab):
            badge_html = (f'<span class="tax-badge-pay">Payable: {fmt(balance)}</span>'
                          if balance > 0 else
                          f'<span class="tax-badge-ref">Refund: {fmt(abs(balance))}</span>')
            acct = "NRO Expense" if is_ab else "NRO Savings"
            rows_html = f"""
            <div class="tax-row"><span class="tax-label">Residential rent ({acct})</span><span style="color:{GREEN};font-family:DM Mono,monospace;font-size:12px">{fmt(res)}</span></div>
            <div class="tax-row"><span class="tax-label">Commercial rent — 50% share (gross)</span><span style="color:{GREEN};font-family:DM Mono,monospace;font-size:12px">{fmt(com)}</span></div>
            <div class="tax-row"><span class="tax-label">Less: {int(stat_ded*100)}% statutory deduction</span><span style="color:{RED};font-family:DM Mono,monospace;font-size:12px">-{fmt(round(com*stat_ded))}</span></div>
            <div class="tax-row"><span class="tax-label">Interest, dividends &amp; other income</span><span style="color:{GREEN if interest else INK3};font-family:DM Mono,monospace;font-size:12px">{fmt(interest) if interest else '—'}</span></div>
            <div class="tax-row"><span class="tax-label">Less: 80C (investments, capped)</span><span style="color:{RED};font-family:DM Mono,monospace;font-size:12px">-{fmt(inv80c)}</span></div>
            <div class="tax-row tax-row-total"><span>Taxable income</span><span style="font-family:DM Mono,monospace">{fmt(taxable)}</span></div>
            {slab_row("Up to ₹2.5L @ 0%",    taxable, 0,       250000,  0.00)}
            {slab_row("₹2.5L – ₹5L @ 5%",    taxable, 250000,  500000,  0.05)}
            {slab_row("₹5L – ₹10L @ 20%",    taxable, 500000,  1000000, 0.20)}
            {slab_row("Above ₹10L @ 30%",     taxable, 1000000, 9999999, 0.30)}
            <div class="tax-row tax-row-total"><span>Total tax liability</span><span style="font-family:DM Mono,monospace;color:{RED}">{fmt(tax)}</span></div>
            <div class="tax-row"><span class="tax-label">TDS deducted</span><span style="color:{RED};font-family:DM Mono,monospace;font-size:12px">-{fmt(tds_paid)}</span></div>
            <div class="tax-row tax-row-result" style="border-radius:0 0 10px 10px">
              <span>{"⚠ Tax payable" if balance > 0 else "✓ Refund due"}</span>
              <span style="font-family:DM Mono,monospace">{fmt(abs(balance))}</span>
            </div>"""
            return f"""
            <div class="tax-person-card">
              <div class="tax-person-head">
                <span class="tax-person-name">{name}</span>
                {badge_html}
              </div>
              {rows_html}
            </div>"""

        tc1, tc2 = st.columns(2)
        with tc1:
            st.markdown(person_html("Abhishek (AB)", ab_res, ab_com, ab_80c, ab_int,
                                    ab_taxable, ab_tax, ab_tds, ab_bal, True),
                        unsafe_allow_html=True)
        with tc2:
            st.markdown(person_html("Praggya (PT)", pt_res, pt_com, pt_80c, 0,
                                    pt_taxable, pt_tax, pt_tds, pt_bal, False),
                        unsafe_allow_html=True)

        # YoY TDS trend
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Year-on-year TDS trend</div>', unsafe_allow_html=True)
        trend = [{"FY": fy, "Net TDS": round(abs(sum_tag(fy_rows(df,fy),["TDS"])) - sum_tag(fy_rows(df,fy),["TDS Income"]))}
                 for fy in all_fys[1:]]
        if trend:
            tdf = pd.DataFrame(trend)
            fig = go.Figure(go.Bar(x=tdf["FY"], y=tdf["Net TDS"],
                                   marker_color=GOLD, marker_line_width=0, opacity=0.85))
            plotly_layout(fig, 220)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown(f'<div style="font-size:11px;color:{INK3};margin-top:8px">Consult your CA before filing. TDS split is an estimate — adjust above.</div>', unsafe_allow_html=True)
