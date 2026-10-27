"""
app.py — Decentralized Multi-Agent University Scheduling Simulator.

Architecture & Interface:
  • Enterprise dark obsidian aesthetic (zero AI-cliché gradients or emojis)
  • Clean typographic status badges and monospace protocol telemetry
  • Live message bus replay (agent offers and bids + backtracking)
  • Dynamic agent resource cards and weekly master timetable matrix
  • Independent verification engine for Hard Constraints H1–H6
"""

from __future__ import annotations

import time
from collections import Counter
import pandas as pd
import streamlit as st

import importlib
from models import Day, MsgType, Period, RoomType, ALL_DAYS, ALL_PERIODS
import demo_data
importlib.reload(demo_data)
from demo_data import (
    build_demo_scenario,
    build_department_scale_scenario,
    get_autofill_five_teachers_dept,
    build_custom_scenario,
)
from scheduler import (
    Scheduler, SimulationState,
    build_unsatisfiable_scenario, build_conflict_scenario,
)

# ─── Page configuration ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Multi-Agent Timetabling Protocol",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Light / Dark theme palette (the toggle lives in the sidebar) ────────────
# Colours are driven by CSS variables so switching themes is just a value swap.
_DARK = st.session_state.get("dark_mode", False)
_PALETTE = {
    "light": {
        "--bg": "#F8FAFC", "--surface": "#FFFFFF", "--surface-2": "#F1F5F9",
        "--surface-3": "#E2E8F0", "--border": "#E2E8F0", "--chip": "#EEF2FF",
        "--text": "#0F172A", "--text-soft": "#1E293B", "--muted": "#64748B",
        "--primary": "#4F46E5", "--primary-2": "#6366F1",
        "--primary-3": "#818CF8", "--primary-strong": "#3730A3",
    },
    "dark": {
        "--bg": "#0B1120", "--surface": "#131C2E", "--surface-2": "#1B2740",
        "--surface-3": "#26324C", "--border": "#2B3A57", "--chip": "#1E2A4A",
        "--text": "#E7EEF9", "--text-soft": "#CBD5E1", "--muted": "#93A3BC",
        "--primary": "#818CF8", "--primary-2": "#6366F1",
        "--primary-3": "#A5B4FC", "--primary-strong": "#4F46E5",
    },
}
_active = _PALETTE["dark" if _DARK else "light"]
st.markdown(
    "<style>:root{" + "".join(f"{k}:{v};" for k, v in _active.items()) + "}"
    # a couple of extra nudges so Streamlit's own widgets follow the theme
    ".stApp,[data-testid='stHeader']{background:var(--bg);}"
    "[data-testid='stMetricValue'],[data-testid='stMetricLabel']{color:var(--text)!important;}"
    "</style>",
    unsafe_allow_html=True,
)

# ─── Design System (violet brand, clean neutrals, lime accent) ───────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-soft);
}

.stApp {
    background-color: var(--bg);
    min-height: 100vh;
}

/* ── Academic Top Navigation Bar ── */
.academic-navbar {
    background: linear-gradient(130deg, #4F46E5 0%, #4338CA 52%, #312E81 100%);
    border: none;
    border-radius: 18px;
    padding: 24px 28px;
    margin-bottom: 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 16px 40px rgba(49, 46, 129, 0.34), 0 2px 6px rgba(0,0,0,0.08);
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

/* soft sky glow accent */
.academic-navbar::after {
    content: "";
    position: absolute;
    top: -70px; right: -30px;
    width: 220px; height: 220px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #38BDF8, transparent 70%);
    opacity: 0.35;
    pointer-events: none;
}

.academic-navbar:hover {
    box-shadow: 0 20px 48px rgba(49, 46, 129, 0.44);
}

.navbar-left {
    display: flex;
    align-items: center;
    gap: 16px;
    position: relative;
    z-index: 1;
}

.navbar-crest {
    width: 46px;
    height: 46px;
    background: rgba(255, 255, 255, 0.16);
    border: 1.5px solid rgba(255, 255, 255, 0.28);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF;
    font-weight: 800;
    box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.14), 0 4px 14px rgba(0,0,0,0.18);
}

.navbar-super {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #C7D2FE;
    text-transform: uppercase;
    margin-bottom: 3px;
}

.navbar-title {
    font-family: 'DM Sans', 'Plus Jakarta Sans', sans-serif;
    font-size: 1.62rem;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.02em;
    line-height: 1.15;
}

.navbar-sub {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.72);
    margin-top: 2px;
}

.navbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
    position: relative;
    z-index: 1;
}

.navbar-badge-scenario {
    background: var(--chip);
    color: var(--primary);
    border: 1px solid var(--border);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}

.navbar-status-pill {
    background: #EBF7EE;
    color: #166534;
    border: 1px solid #BBF7D0;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.76rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 8px;
}

.nav-pulse-dot {
    width: 8px;
    height: 8px;
    background-color: #166534;
    border-radius: 50%;
    display: inline-block;
    animation: dotPulse 2s infinite;
}

@keyframes dotPulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(22, 101, 52, 0.6); }
    70% { transform: scale(1.15); box-shadow: 0 0 0 6px rgba(22, 101, 52, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(22, 101, 52, 0); }
}

/* ── Animation Flows & Keyframes ── */
@keyframes slideUpFade {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes softBreathing {
    0%, 100% { border-color: var(--border); box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04); }
    50% { border-color: var(--primary-2); box-shadow: 0 4px 16px rgba(15, 23, 42, 0.14); }
}

@keyframes ribbonPulse {
    0%, 100% { border-left-color: var(--primary); }
    50% { border-left-color: var(--primary-3); }
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--surface-2) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] hr {
    border-color: var(--border) !important;
    margin: 16px 0 !important;
}

.sidebar-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--primary-2);
    text-transform: uppercase;
    margin-bottom: 6px;
}

.sidebar-brand {
    font-family: 'DM Sans', 'Plus Jakarta Sans', sans-serif;
    font-size: 1.18rem;
    font-weight: 700;
    color: var(--primary-strong);
    letter-spacing: -0.01em;
    margin-bottom: 2px;
}

.sidebar-sub {
    font-size: 0.75rem;
    color: var(--muted);
    margin-bottom: 16px;
}

/* Sidebar Buttons */
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: var(--surface);
    color: var(--text-soft);
    border: 1px solid var(--surface-3);
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 9px 14px;
    letter-spacing: 0.01em;
    transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    margin-bottom: 6px;
    text-align: left;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--primary) !important;
    color: #FFFFFF !important;
    border-color: var(--primary) !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.22) !important;
}

[data-testid="stSidebar"] .stButton > button:active {
    transform: translateY(0);
}

/* ── Section Titles ── */
.sec-header {
    font-family: 'DM Sans', 'Plus Jakarta Sans', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--primary-strong);
    margin: 18px 0 12px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.sec-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--surface-2);
}

/* ── Agent Cards ── */
.agent-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 12px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
    position: relative;
}

.agent-card:hover {
    transform: translateY(-2px);
    border-color: var(--primary-2);
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.09);
}

.agent-card.active {
    border-color: var(--primary-2);
    background: var(--surface);
    animation: softBreathing 3s infinite;
}

.agent-card.committed {
    border-color: #A7F3D0;
    background: #F8FCF9;
}

.agent-card.failed {
    border-color: #FECACA;
    background: var(--chip);
}

.agent-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}

.agent-type {
    font-size: 0.68rem;
    font-weight: 700;
    color: var(--primary-2);
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.agent-name {
    font-family: 'DM Sans', 'Plus Jakarta Sans', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.3;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.pill-idle        { background: var(--surface-2); color: var(--muted); border: 1px solid var(--border); }
.pill-negotiating { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
.pill-committed   { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
.pill-failed      { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }

/* ── Protocol Message Feed (Pastel & Cream) ── */
.msg-bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 11px 14px;
    margin-bottom: 8px;
    font-size: 0.83rem;
    transition: all 0.2s ease;
    box-shadow: 0 1px 4px rgba(0,0,0,0.02);
    animation: slideUpFade 0.25s ease-out;
}

.msg-bubble:hover {
    border-color: var(--primary-2);
    background: var(--surface);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
}

.msg-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 5px;
    font-size: 0.74rem;
}

.badge-tag {
    font-size: 0.66rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 5px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* Pastel Badge Palette */
.badge-CFP       { background: #EEF2FF; color: #3730A3; border: 1px solid #C7D2FE; }
.badge-BID       { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
.badge-REJECT    { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
.badge-AWARD     { background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
.badge-RELEASE   { background: #F8FAFC; color: #475569; border: 1px solid #CBD5E1; }
.badge-VALIDATE  { background: #FAF5FF; color: #6B21A8; border: 1px solid #E9D5FF; }
.badge-ACCEPT    { background: #F0FDF4; color: #166534; border: 1px solid #BBF7D0; }
.badge-NOGOOD    { background: #FFF7ED; color: #9A3412; border: 1px solid #FED7AA; }
.badge-BACKTRACK { background: #FDF4FF; color: #86198F; border: 1px solid #F5D0FE; }
.badge-COMMIT    { background: var(--chip); color: var(--primary); border: 1px solid var(--border); }

.msg-actors {
    color: var(--muted);
    font-weight: 500;
}

.msg-actors strong {
    color: var(--text);
}

.msg-details {
    color: var(--text-soft);
    font-size: 0.8rem;
    line-height: 1.45;
    font-family: 'JetBrains Mono', monospace;
    background: var(--bg);
    padding: 6px 10px;
    border-radius: 6px;
    border: 1px solid var(--surface-2);
    margin-top: 4px;
}

/* ── Banner ── */
.telemetry-banner {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--primary);
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 16px;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
    animation: ribbonPulse 4s infinite ease-in-out;
}

/* ── Constraint Badges ── */
.badge-pass {
    background: #ECFDF5;
    color: #065F46;
    border: 1px solid #A7F3D0;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 6px;
    text-transform: uppercase;
}

.badge-fail {
    background: #FEF2F2;
    color: #991B1B;
    border: 1px solid #FECACA;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 6px;
    text-transform: uppercase;
}

/* ── Boxes ── */
.status-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 0.85rem;
    margin-bottom: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}

.status-box.success {
    border-left: 4px solid #10B981;
    background: #F6FCF8;
    color: #065F46;
}

.status-box.error {
    border-left: 4px solid #EF4444;
    background: var(--chip);
    color: #991B1B;
}

.status-box.info {
    border-left: 4px solid var(--primary);
    background: var(--chip);
    color: var(--primary-strong);
}

/* ── Typography & Tables ── */
p, span, li, div {
    color: var(--text-soft);
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'DM Sans', 'Plus Jakarta Sans', sans-serif;
    color: var(--text) !important;
}

strong, b {
    color: var(--text) !important;
}

/* Streamlit Tabs */
[data-baseweb="tab-list"] {
    gap: 12px !important;
    border-bottom: 1.5px solid var(--border) !important;
    background: transparent !important;
}

[data-baseweb="tab"] {
    color: var(--muted) !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    background: transparent !important;
    border: none !important;
    padding: 10px 18px !important;
    transition: all 0.2s ease !important;
}

[data-baseweb="tab"]:hover {
    color: var(--primary) !important;
}

[data-baseweb="tab"][aria-selected="true"] {
    color: var(--primary) !important;
    font-weight: 700 !important;
    border-bottom: 2.5px solid var(--primary) !important;
}

/* Streamlit Metrics */
[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
    transition: all 0.2s ease;
}

[data-testid="stMetric"]:hover {
    border-color: var(--primary-2);
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
}

[data-testid="stMetricLabel"] {
    color: var(--primary-2) !important;
    font-size: 0.73rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

[data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-weight: 700 !important;
    font-size: 1.7rem !important;
    font-family: 'DM Sans', 'Plus Jakarta Sans', sans-serif !important;
}

/* Streamlit Expanders */
[data-testid="stExpander"] {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.02) !important;
}

[data-testid="stExpander"] summary {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}

[data-testid="stExpander"] summary:hover {
    background-color: var(--surface-2) !important;
    color: var(--primary) !important;
}

[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: var(--text) !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background-color: var(--surface) !important;
    border-top: 1px solid var(--border) !important;
    padding: 16px 20px !important;
}

/* Tables High-Contrast Cream & Burgundy */
table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 16px 0 !important;
    font-size: 0.85rem !important;
    background: var(--surface) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
}

table th {
    background-color: var(--chip) !important;
    color: var(--primary-strong) !important;
    font-weight: 700 !important;
    border: 1px solid var(--chip) !important;
    padding: 11px 15px !important;
    text-align: left !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}

table td {
    background-color: var(--surface) !important;
    color: var(--text-soft) !important;
    border: 1px solid var(--surface-2) !important;
    padding: 10px 15px !important;
    line-height: 1.55 !important;
}

table tr:nth-child(even) td {
    background-color: var(--bg) !important;
}

table tr:hover td {
    background-color: var(--chip) !important;
    color: var(--text) !important;
}

/* Captions and Code blocks */
.stCaption, [data-testid="stCaptionContainer"], p.stCaption {
    color: var(--muted) !important;
    font-size: 0.82rem !important;
}

pre {
    background-color: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 14px 16px !important;
    color: var(--text) !important;
}

code:not(pre code) {
    background-color: var(--chip) !important;
    color: var(--primary) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    border: 1px solid var(--border) !important;
}

/* ══════════════════════════════════════════════════════════════════
   STREAMLIT FORM WIDGETS & BASEWEB CONTROLS (CREAM & BURGUNDY THEME)
   ══════════════════════════════════════════════════════════════════ */

/* Labels above form controls */
label[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span {
    color: var(--primary-strong) !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
}

/* All Text & Number Inputs - Main Area & Sidebar */
div[data-baseweb="input"],
div[data-baseweb="base-input"],
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
input[type="text"],
input[type="number"],
.stTextInput input,
.stNumberInput input {
    background-color: var(--surface) !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    transition: all 0.2s ease !important;
}

/* Inner input container wrapper */
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"] > div,
div[data-testid="stTextInput"] > div > div,
div[data-testid="stNumberInput"] > div > div {
    background-color: var(--surface) !important;
    background: var(--surface) !important;
    border-color: var(--border) !important;
}

div[data-baseweb="input"]:focus-within,
div[data-baseweb="base-input"]:focus-within,
div[data-testid="stTextInput"] > div > div:focus-within,
div[data-testid="stNumberInput"] > div > div:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(15, 23, 42, 0.12) !important;
}

/* Number input increment / decrement buttons */
div[data-testid="stNumberInput"] button,
div[data-testid="stNumberInputContainer"] button,
div[data-testid="stNumberInput"] div button {
    background-color: var(--surface-2) !important;
    background: var(--surface-2) !important;
    color: var(--primary) !important;
    border: 1px solid var(--surface-3) !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stNumberInput"] button:hover,
div[data-testid="stNumberInputContainer"] button:hover,
div[data-testid="stNumberInput"] div button:hover {
    background-color: var(--primary) !important;
    background: var(--primary) !important;
    color: #FFFFFF !important;
    border-color: var(--primary) !important;
}

div[data-testid="stNumberInput"] button svg {
    fill: currentColor !important;
}

/* All Selectboxes & Dropdowns */
div[data-baseweb="select"],
div[data-baseweb="select"] > div,
div[data-testid="stSelectbox"] > div > div {
    background-color: var(--surface) !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}

div[data-baseweb="select"]:focus-within > div,
div[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(15, 23, 42, 0.12) !important;
}

div[data-baseweb="select"] *,
div[data-testid="stSelectbox"] * {
    color: var(--text) !important;
}

/* Select dropdown arrow icon */
div[data-baseweb="select"] svg,
div[data-testid="stSelectbox"] svg {
    fill: var(--primary) !important;
}

/* Dropdown popover menu list */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
ul[data-baseweb="menu"],
div[data-baseweb="popover"] ul {
    background-color: var(--surface) !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08) !important;
}

li[data-baseweb="menu-item"],
div[data-baseweb="popover"] li {
    background-color: var(--surface) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
    padding: 8px 14px !important;
    font-size: 0.84rem !important;
    transition: all 0.15s ease !important;
}

li[data-baseweb="menu-item"]:hover,
li[data-baseweb="menu-item"][aria-selected="true"] {
    background-color: var(--chip) !important;
    color: var(--primary) !important;
    font-weight: 600 !important;
}

/* Checkbox */
[data-testid="stCheckbox"] span {
    color: var(--text) !important;
    font-size: 0.86rem !important;
}

/* ══════════════════════════════════════════════════════════════════
   STREAMLIT BUTTONS (PRIMARY & SECONDARY LIGHT THEMING)
   ══════════════════════════════════════════════════════════════════ */

/* General / Secondary buttons across whole app */
button,
button[kind="secondary"],
button[data-testid="baseButton-secondary"],
button[data-testid="stBaseButton-secondary"],
.stButton > button {
    background-color: var(--surface) !important;
    background: var(--surface) !important;
    color: var(--primary-strong) !important;
    border: 1.5px solid var(--surface-3) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    padding: 8px 16px !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
}

button:hover,
button[kind="secondary"]:hover,
button[data-testid="baseButton-secondary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover,
.stButton > button:hover {
    background-color: var(--bg) !important;
    background: var(--bg) !important;
    color: var(--primary) !important;
    border-color: var(--primary-2) !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12) !important;
}

/* Primary buttons (e.g. Active Workspace, Deploy Council) */
button[kind="primary"],
button[data-testid="baseButton-primary"],
button[data-testid="stBaseButton-primary"],
.stButton > button[kind="primary"] {
    background-color: var(--primary) !important;
    background: var(--primary) !important;
    color: #FFFFFF !important;
    border: 1.5px solid var(--primary-strong) !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 0.84rem !important;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.25) !important;
}

button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {
    background-color: var(--primary-2) !important;
    background: var(--primary-2) !important;
    color: #FFFFFF !important;
    border-color: var(--primary) !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.35) !important;
}

button[kind="primary"] p,
button[kind="primary"] span,
button[data-testid="baseButton-primary"] p,
button[data-testid="baseButton-primary"] span {
    color: #FFFFFF !important;
}

button[kind="secondary"] p,
button[kind="secondary"] span,
button[data-testid="baseButton-secondary"] p,
button[data-testid="baseButton-secondary"] span {
    color: var(--primary-strong) !important;
}

button:hover p,
button:hover span {
    color: var(--primary) !important;
}

button[kind="primary"]:hover p,
button[kind="primary"]:hover span {
    color: #FFFFFF !important;
}

/* Sidebar Specific Buttons */
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] .stButton > button {
    text-align: left !important;
    margin-bottom: 6px !important;
}

[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background-color: var(--primary) !important;
    background: var(--primary) !important;
    color: #FFFFFF !important;
    border-color: var(--primary-strong) !important;
    text-align: center !important;
}

[data-testid="stSidebar"] button[kind="secondary"],
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background-color: var(--surface) !important;
    background: var(--surface) !important;
    color: var(--text-soft) !important;
    border-color: var(--surface-3) !important;
}

/* Streamlit Header & Toolbar */
header[data-testid="stHeader"],
[data-testid="stHeader"],
header,
.stAppHeader {
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
    border-bottom: none !important;
}

/* trim the big default top padding above the main content */
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"],
section.main > div.block-container,
.block-container {
    padding-top: 0.6rem !important;
}
[data-testid="stAppViewContainer"] { padding-top: 0 !important; }
/* collapse the sidebar's own top header bar (the empty strip above the menu) */
[data-testid="stSidebarHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
}
[data-testid="stSidebarUserContent"] {
    padding-top: 0.4rem !important;
}

.stDeployButton,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu,
footer {
    display: none !important;
    visibility: hidden !important;
}

/* ── Force Sidebar Always Visible & Expanded ── */
[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    transform: none !important;
    min-width: 270px !important;
    max-width: 300px !important;
    position: relative !important;
    height: auto !important;
}

[data-testid="stSidebar"][aria-expanded="false"] {
    display: block !important;
    margin-left: 0 !important;
    transform: translateX(0) !important;
    width: 270px !important;
    min-width: 270px !important;
}

/* Hide the sidebar collapse/expand toggle arrow button */
[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarNavCollapseButton"],
[data-testid="collapsedControl"] {
    display: none !important;
}

/* ── Real-Time Scenario Studio ── */
.studio-banner {
    background: linear-gradient(135deg, #FFFFFF 0%, var(--bg) 100%);
    border: 1px solid var(--border);
    border-left: 5px solid var(--primary);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 18px rgba(15, 23, 42, 0.04);
}

.studio-title {
    font-family: 'DM Sans', 'Plus Jakarta Sans', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 4px;
}

.studio-subtitle {
    font-size: 0.85rem;
    color: var(--muted);
    line-height: 1.5;
}

.studio-tag {
    display: inline-block;
    font-size: 0.70rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--primary-2);
    background: var(--chip);
    padding: 3px 10px;
    border-radius: 14px;
    border: 1px solid var(--border);
    margin-bottom: 8px;
}

.studio-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.02);
}
</style>
""", unsafe_allow_html=True)


# ─── State Management ────────────────────────────────────────────────────────

def _init():
    defaults = {
        "sim":           None,
        "replay_idx":    0,
        "is_playing":    False,
        "anim_speed":    1.2,
        "scenario_name": "",
        "current_view":  "dashboard",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "studio_data" not in st.session_state:
        st.session_state.studio_data = get_autofill_five_teachers_dept()
    if st.session_state.sim is None:
        _load(build_demo_scenario(), "Demo (with a clash)")

def sim() -> SimulationState | None:
    return st.session_state.sim


def _load(scenario: dict, name: str):
    state = Scheduler.build_from_scenario(scenario)
    Scheduler.run_full(state)
    Scheduler.validate(state)
    st.session_state.sim = state
    st.session_state.replay_idx = len(state.message_log) if ("Studio" in name or "Real-Time" in name) else 0
    st.session_state.is_playing = False
    st.session_state.scenario_name = name

_init()


# ─── Sidebar Navigation ──────────────────────────────────────────────────────

with st.sidebar:
    # Light / Dark theme toggle (drives the CSS variables at the top of the script)
    st.toggle("🌙 Dark mode", key="dark_mode")

    # Workspace Mode Switcher
    st.markdown('<div class="sidebar-title">View</div>', unsafe_allow_html=True)
    c_w1, c_w2 = st.columns(2)
    with c_w1:
        dash_active = (st.session_state.get("current_view", "dashboard") == "dashboard")
        dash_type = "primary" if dash_active else "secondary"
        if st.button("Timetable", type=dash_type, use_container_width=True, help="View the timetable, live steps and stats"):
            st.session_state.current_view = "dashboard"
            st.rerun()
    with c_w2:
        stud_active = (st.session_state.get("current_view") == "studio")
        stud_type = "primary" if stud_active else "secondary"
        if st.button("Studio", type=stud_type, use_container_width=True, help="Enter/Customize Teachers, Rooms, Courses & Students"):
            st.session_state.current_view = "studio"
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="sidebar-title">Examples</div>', unsafe_allow_html=True)

    if st.button("Demo (with a clash)"):
        _load(build_demo_scenario(), "Demo (with a clash)")
        st.session_state.current_view = "dashboard"
        st.rerun()

    if st.button("Clash Example"):
        _load(build_conflict_scenario(), "Clash Example")
        st.session_state.current_view = "dashboard"
        st.rerun()

    if st.button("Hard Case (no answer)"):
        _load(build_unsatisfiable_scenario(), "Hard Case (no answer)")
        st.session_state.current_view = "dashboard"
        st.rerun()

    if st.button("Big Timetable"):
        _load(build_department_scale_scenario(), "Big Timetable")
        st.session_state.current_view = "dashboard"
        st.rerun()

    st.markdown("---")
    st.markdown('<div class="sidebar-title">Real-Time Studio</div>', unsafe_allow_html=True)

    if st.button("Build Your Own"):
        st.session_state.current_view = "studio"
        st.rerun()

    if st.button("Reset"):
        if st.session_state.sim is not None:
            if "no answer" in st.session_state.scenario_name:
                _load(build_unsatisfiable_scenario(), "Hard Case (no answer)")
            elif "Big" in st.session_state.scenario_name:
                _load(build_department_scale_scenario(), "Big Timetable")
            else:
                _load(build_demo_scenario(), "Demo (with a clash)")
        st.session_state.current_view = "dashboard"
        st.rerun()

    st.markdown("---")
    st.markdown('<div class="sidebar-title">Playback Controls</div>', unsafe_allow_html=True)

    s = sim()
    total_msgs = len(s.message_log) if s else 0
    idx = st.session_state.replay_idx

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("Back Step", disabled=(idx == 0 or s is None)):
            st.session_state.replay_idx = max(0, idx - 1)
            st.rerun()
    with col_b2:
        if st.button("Next Step", disabled=(s is None or idx >= total_msgs)):
            st.session_state.replay_idx = min(total_msgs, idx + 1)
            st.rerun()

    if s:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("Reset Stream"):
                st.session_state.replay_idx = 0
                st.session_state.is_playing = False
                st.rerun()
        with col_c2:
            if st.button("Skip to End"):
                st.session_state.replay_idx = total_msgs
                st.session_state.is_playing = False
                st.rerun()

        play_label = "Pause" if st.session_state.is_playing else "Auto Play"
        if st.button(play_label):
            st.session_state.is_playing = not st.session_state.is_playing
            st.rerun()

        pct = int((idx / total_msgs * 100)) if total_msgs else 0
        st.markdown(f"""
<div style="margin-top:12px; font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#64748b;">
  Stream Index: {idx}/{total_msgs} ({pct}%)
</div>
""", unsafe_allow_html=True)
        st.progress(pct / 100)

    st.markdown("---")
    st.markdown("""
<div style="font-size:0.75rem; color:var(--muted); line-height:1.65; background:var(--bg); padding:12px 14px; border-radius:8px; border:1px solid var(--border);">
  <strong style="color:var(--primary); letter-spacing:0.04em;">THEORETICAL FOUNDATIONS:</strong><br/>
  &bull; Agents make offers and bids<br/>
  &bull; Clashes are fixed by stepping back<br/>
  &bull; Domain Nogood Filtering<br/>
  &bull; Hard Constraints H1–H6
</div>
""", unsafe_allow_html=True)


# ─── Academic Top Navigation Bar ─────────────────────────────────────────────

active_scen = st.session_state.scenario_name or "Demo (with a clash)"
s_state = sim()
if s_state is not None:
    if s_state.validation_report and s_state.validation_report.is_fully_valid:
        status_label = "NO CLASHES"
        status_pill_style = "background:#EBF7EE; color:#166534; border:1px solid #BBF7D0;"
        dot_color = "#166534"
    elif any(sess.failed for sess in s_state.sessions):
        status_label = "DOMAIN EXHAUSTED"
        status_pill_style = "background:#FEF2F2; color:#991B1B; border:1px solid #FECACA;"
        dot_color = "#991B1B"
    else:
        status_label = "COUNCIL ACTIVE"
        status_pill_style = "background:#FEF3C7; color:#92400E; border:1px solid #FCD34D;"
        dot_color = "#92400E"
else:
    status_label = "PICK AN EXAMPLE"
    status_pill_style = "background:var(--bg); color:var(--muted); border:1px solid var(--border);"
    dot_color = "var(--muted)"

st.markdown(f"""
<div class="academic-navbar">
  <div class="navbar-left">
    <div class="navbar-crest">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
        <path d="M6 12v5c3 3 9 3 12 0v-5"/>
      </svg>
    </div>
    <div>
      <div class="navbar-super">DEMO &bull; TIMETABLE BUILDER</div>
      <div class="navbar-title">Automatic Timetable Builder</div>
      <div class="navbar-sub">Teachers, rooms and student groups agree on a clash-free timetable</div>
    </div>
  </div>
  <div class="navbar-right">
    <div class="navbar-badge-scenario">{active_scen}</div>
    <div class="navbar-status-pill" style="{status_pill_style}">
      <span class="nav-pulse-dot" style="background-color: {dot_color};"></span>
      <span>{status_label}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

if sim() is None:
    st.markdown("""
<div class="status-box info" style="padding: 34px; text-align: center; border-left-color: var(--primary);">
  <div style="font-family:'DM Sans',Georgia,serif; font-size: 1.25rem; font-weight: 700; color: var(--primary-strong); margin-bottom: 6px;">
    System Initialization Required
  </div>
  <div style="color: var(--muted); font-size: 0.88rem; max-width: 600px; margin: 0 auto; line-height: 1.55;">
    Select <strong>Demo (with a clash)</strong> or any benchmark in the sidebar to initialize the multi-agent system.
  </div>
</div>
""", unsafe_allow_html=True)
    st.stop()


def render_scenario_studio():
    col_t_title, col_t_back = st.columns([3.5, 1.5])
    with col_t_title:
        st.markdown("""
<div class="studio-banner" style="margin-bottom:12px;">
  <div class="studio-tag">Build Your Own</div>
  <div class="studio-title">Build Your Own Timetable</div>
  <div class="studio-subtitle">
    Add your own teachers, rooms, courses and student groups, or click <strong>Auto-Fill</strong>. The agents will work out a clash-free timetable that follows all 6 rules.
  </div>
</div>
""", unsafe_allow_html=True)
    with col_t_back:
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        if st.button("View Timetable Dashboard ➜", use_container_width=True):
            st.session_state.current_view = "dashboard"
            st.rerun()

    if "studio_data" not in st.session_state:
        st.session_state.studio_data = get_autofill_five_teachers_dept()

    s_data = st.session_state.studio_data

    # Preset Quick Action Bar
    c_btn1, c_btn2, c_btn3 = st.columns([1.6, 1.4, 1.0])
    with c_btn1:
        if st.button("Auto-Fill: 5 Teachers, 8 Courses", use_container_width=True, help="Fill in a bigger example"):
            st.session_state.studio_data = get_autofill_five_teachers_dept()
            st.toast("Loaded 5-Teacher & 8-Course Department Preset!")
            st.rerun()
    with c_btn2:
        if st.button("Auto-Fill: 3 Teachers, 5 Courses", use_container_width=True, help="Fill in the basic example"):
            st.session_state.studio_data = {
                "teachers": [
                    {"id": "T1", "name": "Teacher Alpha", "priority": 3, "pref_day": "MONDAY", "pref_period": "P2"},
                    {"id": "T2", "name": "Teacher Bravo",   "priority": 2, "pref_day": "TUESDAY", "pref_period": "P2"},
                    {"id": "T3", "name": "Teacher Charlie",  "priority": 1, "pref_day": "WEDNESDAY", "pref_period": "P2"},
                ],
                "rooms": [
                    {"id": "R101", "capacity": 50, "type": "LECTURE", "building": "Block-A"},
                    {"id": "R204", "capacity": 70, "type": "LECTURE", "building": "Block-B"},
                    {"id": "R305", "capacity": 40, "type": "LECTURE", "building": "Block-A"},
                    {"id": "LAB1", "capacity": 35, "type": "LAB",     "building": "Block-C"},
                ],
                "students": [
                    {"id": "S1", "name": "Cohort-A (CS Core)", "courses": "CSE401, CSE330"},
                    {"id": "S2", "name": "Cohort-B (AI Major)", "courses": "CSE501, CSE401"},
                    {"id": "S3", "name": "Cohort-C (Math)",     "courses": "MAT101L, CSE202"},
                ],
                "sessions": [
                    {"code": "CSE401",  "name": "Advanced Algorithms",  "teacher_id": "T1", "enrollment": 45, "type": "LECTURE"},
                    {"code": "CSE330",  "name": "Operating Systems",    "teacher_id": "T2", "enrollment": 48, "type": "LECTURE"},
                    {"code": "CSE501",  "name": "Machine Learning",     "teacher_id": "T1", "enrollment": 40, "type": "LECTURE"},
                    {"code": "CSE202",  "name": "Data Structures",      "teacher_id": "T3", "enrollment": 38, "type": "LECTURE"},
                    {"code": "MAT101L", "name": "Discrete Math Lab",    "teacher_id": "T3", "enrollment": 30, "type": "LAB"},
                ],
                "pre_committed": [
                    {"session_id": "SES_CSE330", "day": "MONDAY", "period": "P2", "room_id": "R101"}
                ]
            }
            st.toast("Loaded 3-Teacher Demo Preset!")
            st.rerun()
    with c_btn3:
        if st.button("Clear Custom Fields", use_container_width=True, help="Clear to minimal customizable template"):
            st.session_state.studio_data = {
                "teachers": [{"id": "T1", "name": "Prof. Primary", "priority": 1, "pref_day": "MONDAY", "pref_period": "P1"}],
                "rooms": [{"id": "R101", "capacity": 50, "type": "LECTURE", "building": "Block-A"}],
                "students": [{"id": "S1", "name": "Group-1", "courses": "CSE101"}],
                "sessions": [{"code": "CSE101", "name": "Intro to Computing", "teacher_id": "T1", "enrollment": 40, "type": "LECTURE"}],
                "pre_committed": []
            }
            st.toast("Reset to minimal blank template")
            st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # 5 Sub-Tabs for clean category inputs
    st_t1, st_t2, st_t3, st_t4, st_t5 = st.tabs([
        "Faculty Members",
        "Rooms & Facilities",
        "Course Offerings",
        "Student Groups",
        "Pre-Booked Obstacle (Optional)"
    ])

    days_opts = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    periods_opts = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
    room_types = ["LECTURE", "LAB"]

    # 1. Teachers Tab
    with st_t1:
        st.markdown('<div class="sec-header">Teacher Agent Parameters (Priority & Preferences)</div>', unsafe_allow_html=True)
        cur_t_count = len(s_data.get("teachers", []))
        t_count = st.number_input("Number of Teachers", min_value=1, max_value=8, value=cur_t_count, step=1, key="num_teachers_input")
        
        teachers_list = list(s_data.get("teachers", []))
        while len(teachers_list) < t_count:
            idx_new = len(teachers_list) + 1
            teachers_list.append({
                "id": f"T{idx_new}",
                "name": f"Faculty {idx_new}",
                "priority": max(1, 6 - idx_new),
                "pref_day": days_opts[(idx_new - 1) % len(days_opts)],
                "pref_period": "P2"
            })
        teachers_list = teachers_list[:t_count]

        for i, t in enumerate(teachers_list):
            c1, c2, c3, c4, c5 = st.columns([1.2, 2.5, 1.5, 1.5, 1.5])
            with c1:
                t["id"] = st.text_input("Teacher ID", value=t.get("id", f"T{i+1}"), key=f"t_id_{i}")
            with c2:
                t["name"] = st.text_input("Full Name", value=t.get("name", f"Faculty {i+1}"), key=f"t_name_{i}")
            with c3:
                t["priority"] = st.number_input("Priority (ABT)", min_value=1, max_value=10, value=int(t.get("priority", 1)), key=f"t_prio_{i}")
            with c4:
                cur_day = t.get("pref_day", "MONDAY").upper()
                day_idx = days_opts.index(cur_day) if cur_day in days_opts else 0
                t["pref_day"] = st.selectbox("Preferred Day", days_opts, index=day_idx, key=f"t_pday_{i}")
            with c5:
                cur_per = t.get("pref_period", "P2").upper()
                per_idx = periods_opts.index(cur_per) if cur_per in periods_opts else 1
                t["pref_period"] = st.selectbox("Preferred Period", periods_opts, index=per_idx, key=f"t_pper_{i}")

        s_data["teachers"] = teachers_list

    # 2. Rooms Tab
    with st_t2:
        st.markdown('<div class="sec-header">Rooms</div>', unsafe_allow_html=True)
        cur_r_count = len(s_data.get("rooms", []))
        r_count = st.number_input("Number of Rooms / Labs", min_value=1, max_value=8, value=cur_r_count, step=1, key="num_rooms_input")
        
        rooms_list = list(s_data.get("rooms", []))
        while len(rooms_list) < r_count:
            idx_new = len(rooms_list) + 1
            rooms_list.append({
                "id": f"R{100 + idx_new*10}",
                "capacity": 50,
                "type": "LECTURE",
                "building": "Block-A"
            })
        rooms_list = rooms_list[:r_count]

        for i, r in enumerate(rooms_list):
            c1, c2, c3, c4 = st.columns([1.5, 1.8, 1.8, 2.0])
            with c1:
                r["id"] = st.text_input("Room ID", value=r.get("id", f"R{i+1}"), key=f"r_id_{i}")
            with c2:
                r["capacity"] = st.number_input("Capacity (Seats)", min_value=10, max_value=250, value=int(r.get("capacity", 40)), step=5, key=f"r_cap_{i}")
            with c3:
                cur_rtype = r.get("type", "LECTURE").upper()
                rtype_idx = 1 if cur_rtype == "LAB" else 0
                r["type"] = st.selectbox("Facility Type", room_types, index=rtype_idx, key=f"r_type_{i}")
            with c4:
                r["building"] = st.text_input("Building / Wing", value=r.get("building", "Main Block"), key=f"r_bld_{i}")

        s_data["rooms"] = rooms_list

    # 3. Sessions Tab
    with st_t3:
        st.markdown('<div class="sec-header">Course Sessions to Schedule (Requirements)</div>', unsafe_allow_html=True)
        cur_s_count = len(s_data.get("sessions", []))
        sess_count = st.number_input("Number of Sessions", min_value=1, max_value=12, value=cur_s_count, step=1, key="num_sessions_input")
        
        teacher_ids = [t["id"] for t in s_data.get("teachers", [])] or ["T1"]
        sessions_list = list(s_data.get("sessions", []))
        while len(sessions_list) < sess_count:
            idx_new = len(sessions_list) + 1
            sessions_list.append({
                "code": f"CSE{200 + idx_new*20}",
                "name": f"Core Subject {idx_new}",
                "teacher_id": teacher_ids[0],
                "enrollment": 40,
                "type": "LECTURE"
            })
        sessions_list = sessions_list[:sess_count]

        for i, sess in enumerate(sessions_list):
            c1, c2, c3, c4, c5 = st.columns([1.4, 2.5, 1.5, 1.4, 1.4])
            with c1:
                sess["code"] = st.text_input("Course Code", value=sess.get("code", f"CRS{i+1}"), key=f"sess_code_{i}")
            with c2:
                sess["name"] = st.text_input("Course Title", value=sess.get("name", f"Course {i+1}"), key=f"sess_name_{i}")
            with c3:
                cur_t = sess.get("teacher_id", teacher_ids[0])
                t_idx = teacher_ids.index(cur_t) if cur_t in teacher_ids else 0
                sess["teacher_id"] = st.selectbox("Assigned Faculty", teacher_ids, index=t_idx, key=f"sess_t_{i}")
            with c4:
                sess["enrollment"] = st.number_input("Enrollment", min_value=10, max_value=250, value=int(sess.get("enrollment", 35)), step=5, key=f"sess_cap_{i}")
            with c5:
                cur_stype = sess.get("type", "LECTURE").upper()
                stype_idx = 1 if cur_stype == "LAB" else 0
                sess["type"] = st.selectbox("Format", room_types, index=stype_idx, key=f"sess_type_{i}")

        s_data["sessions"] = sessions_list

    # 4. Students Tab
    with st_t4:
        st.markdown('<div class="sec-header">Student Groups</div>', unsafe_allow_html=True)
        cur_c_count = len(s_data.get("students", []))
        cohort_count = st.number_input("Number of Student Groups", min_value=1, max_value=6, value=cur_c_count, step=1, key="num_cohorts_input")

        students_list = list(s_data.get("students", []))
        while len(students_list) < cohort_count:
            idx_new = len(students_list) + 1
            students_list.append({
                "id": f"S{idx_new}",
                "name": f"Cohort-{idx_new}",
                "courses": s_data["sessions"][0]["code"] if s_data.get("sessions") else "CSE101"
            })
        students_list = students_list[:cohort_count]

        for i, std in enumerate(students_list):
            c1, c2, c3 = st.columns([1.2, 2.2, 3.5])
            with c1:
                std["id"] = st.text_input("Cohort ID", value=std.get("id", f"S{i+1}"), key=f"std_id_{i}")
            with c2:
                std["name"] = st.text_input("Cohort Label", value=std.get("name", f"Cohort {i+1}"), key=f"std_name_{i}")
            with c3:
                std["courses"] = st.text_input("Enrolled Courses (comma-separated)", value=std.get("courses", ""), key=f"std_crs_{i}", help="Example: CSE401, CSE330, CSE410L")

        s_data["students"] = students_list

    # 5. Obstacles Tab
    with st_t5:
        st.markdown('<div class="sec-header">Blocked Room (already booked)</div>', unsafe_allow_html=True)
        st.write("Simulate a room already being occupied during a specific time slot to observe autonomous agent backtracking and conflict resolution.")
        
        has_obs = len(s_data.get("pre_committed", [])) > 0
        inject_obstacle = st.checkbox("Add a room that's already booked", value=has_obs, key="inject_obs_chk")
        
        if inject_obstacle:
            obs_r_opts = [r["id"] for r in s_data.get("rooms", [])] or ["R101"]
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                obs_rid = st.selectbox("Occupied Room", obs_r_opts, index=0, key="obs_rid")
            with c2:
                obs_day = st.selectbox("Day", days_opts, index=0, key="obs_day")
            with c3:
                obs_per = st.selectbox("Period", periods_opts, index=1, key="obs_per")
            with c4:
                obs_desc = st.text_input("Reason / External Event", value="University Seminar", key="obs_desc")
            
            s_data["pre_committed"] = [{
                "session_id": "SES_EXTERNAL_OBS",
                "day": obs_day,
                "period": obs_per,
                "room_id": obs_rid
            }]
        else:
            s_data["pre_committed"] = []

    st.session_state.studio_data = s_data

    # Deploy Multi-Agent Council
    st.markdown("---")
    deploy_btn = st.button("Run Multi-Agent Council & Generate Timetable", type="primary", use_container_width=True)

    if deploy_btn:
        errs = []
        r_ids = [r["id"] for r in s_data["rooms"]]
        t_ids = [t["id"] for t in s_data["teachers"]]
        
        if len(r_ids) != len(set(r_ids)):
            errs.append("Duplicate Room IDs detected. Each room must have a unique identifier.")
        if len(t_ids) != len(set(t_ids)):
            errs.append("Duplicate Teacher IDs detected. Each teacher must have a unique identifier.")
        
        for sess in s_data["sessions"]:
            if sess["teacher_id"] not in t_ids:
                errs.append(f"Session {sess['code']} is assigned to unknown teacher {sess['teacher_id']}.")
        
        if errs:
            for e in errs:
                st.error(e)
        else:
            with st.spinner("Agents are building a clash-free timetable..."):
                custom_scen = build_custom_scenario(
                    teachers_raw=s_data["teachers"],
                    rooms_raw=s_data["rooms"],
                    students_raw=s_data["students"],
                    sessions_raw=s_data["sessions"],
                    pre_committed_raw=s_data.get("pre_committed", [])
                )
                scen_name = f"Real-Time Studio ({len(s_data['teachers'])} Faculty, {len(s_data['sessions'])} Sessions)"
                _load(custom_scen, scen_name)
                st.session_state.current_view = "dashboard"
                st.toast("Timetable successfully generated by autonomous agent council!")
                st.rerun()


# ─── Main View Routing (Dashboard vs Studio) ─────────────────────────────────

if st.session_state.get("current_view") == "studio":
    render_scenario_studio()
    st.stop()

# ─── Timetable Dashboard Navigation Header ───────────────────────────────────

col_dash_info, col_dash_studio = st.columns([3.8, 1.2])
with col_dash_info:
    st.markdown("<div style='font-size:0.83rem; color:var(--muted); padding:6px 0 10px;'>Dashboard — the timetable, the live steps, and the rule checks</div>", unsafe_allow_html=True)
with col_dash_studio:
    if st.button("Build Your Own ➜", use_container_width=True, help="Enter/Customize your own teachers, rooms, and courses"):
        st.session_state.current_view = "studio"
        st.rerun()

# ─── Dashboard Tabs ──────────────────────────────────────────────────────────

tab_stream, tab_matrix, tab_verify, tab_metrics, tab_arch = st.tabs([
    "Live Steps",
    "Timetable",
    "Rule Checks",
    "Stats",
    "How It Works",
])

s          = sim()
idx        = st.session_state.replay_idx
all_msgs   = s.message_log
shown_msgs = all_msgs[:idx]
total_msgs = len(all_msgs)

# Reconstruct agent states up to the current replay index
active_teachers = set()
active_rooms    = set()
active_students = set()
committed_sessions: dict[str, tuple] = {}

for m in shown_msgs:
    if m.msg_type == MsgType.CFP:
        active_teachers.add(m.sender_id)
    elif m.msg_type == MsgType.BID:
        active_rooms.add(m.sender_id)
    elif m.msg_type in (MsgType.NOGOOD, MsgType.ACCEPT):
        active_students.add(m.sender_id)
    elif m.msg_type == MsgType.COMMIT and m.receiver_id == "SYSTEM":
        committed_sessions[m.session_id] = (
            m.payload.get("slot"), m.payload.get("room_id")
        )

last_msg = shown_msgs[-1] if shown_msgs else None


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 1: PROTOCOL STREAM (LIVE NEGOTIATION)
# ═════════════════════════════════════════════════════════════════════════════

with tab_stream:

    # Top Status Bar
    if last_msg is None:
        st.markdown("""
<div class="telemetry-banner" style="border-left-color: var(--primary);">
  <span style="font-family:'DM Sans',Georgia,serif; font-size:0.88rem; color:var(--primary); font-weight:700;">
    READY &nbsp;&bull;&nbsp; PRESS NEXT STEP
  </span><br/>
  <span style="font-size:0.86rem; color:var(--text-soft);">
    Press <strong>Next Step</strong> (or <strong>Auto Play</strong>) to watch the teachers, rooms and groups build a clash-free timetable.
  </span>
</div>
""", unsafe_allow_html=True)
    else:
        t = last_msg.msg_type.value
        border_colors = {
            "CFP": "#4F46E5", "BID": "#059669", "REJECT": "#DC2626", "AWARD": "#D97706",
            "RELEASE": "#475569", "ACCEPT": "#16A34A", "NOGOOD": "#EA580C",
            "BACKTRACK": "#9333EA", "COMMIT": "var(--primary)", "VALIDATE": "var(--primary-2)",
        }
        bcolor = border_colors.get(t, "var(--primary)")

        desc_map = {
            "CFP":       f"Teacher <strong>{last_msg.sender_id}</strong> asks for a room for class <strong>{last_msg.session_id}</strong> at time <strong>{last_msg.payload.get('slot','?')}</strong>",
            "BID":       f"Room <strong>{last_msg.sender_id}</strong> offers itself (cost <strong>{last_msg.payload.get('cost','?')}</strong>, size and type OK)",
            "REJECT":    f"Room <strong>{last_msg.sender_id}</strong> says no — reason: <em>{last_msg.payload.get('reason','')[:120]}</em>",
            "AWARD":     f"Teacher <strong>{last_msg.sender_id}</strong> picks room <strong>{last_msg.payload.get('room_id','?')}</strong> (best offer, held for now)",
            "RELEASE":   f"Teacher <strong>{last_msg.sender_id}</strong> lets go of room <strong>{last_msg.payload.get('room_id', last_msg.receiver_id)}</strong>",
            "VALIDATE":  f"Teacher <strong>{last_msg.sender_id}</strong> checks time <strong>{last_msg.payload.get('slot','?')}</strong> with group <strong>{last_msg.receiver_id}</strong> for clashes",
            "ACCEPT":    f"Group <strong>{last_msg.sender_id}</strong> accepts the time — no clash",
            "NOGOOD":    f"Group <strong>{last_msg.sender_id}</strong> reports a clash: <em>{last_msg.payload.get('reason','')[:120]}</em>",
            "BACKTRACK": f"Teacher <strong>{last_msg.sender_id}</strong> steps back and tries another time",
            "COMMIT":    f"Final: <strong>{last_msg.session_id}</strong> → <strong>{last_msg.payload.get('slot','?')}</strong> in room <strong>{last_msg.payload.get('room_id','?')}</strong>",
        }
        detail_desc = desc_map.get(t, f"{t}: {last_msg.sender_id} → {last_msg.receiver_id}")

        st.markdown(f"""
<div class="telemetry-banner" style="border-left-color: {bcolor};">
  <div style="font-family:'DM Sans',Georgia,serif; font-size:0.8rem; color:{bcolor}; font-weight:700; margin-bottom:3px;">
    STREAM STEP {idx} OF {total_msgs} &nbsp;&bull;&nbsp; ROUND {last_msg.round_num} &nbsp;&bull;&nbsp; [{t}]
  </div>
  <div style="font-size:0.88rem; color:var(--text); line-height:1.5;">
    {detail_desc}
  </div>
</div>
""", unsafe_allow_html=True)

    # 3-Column Grid: Teachers | Message Bus | Rooms & Students
    col_t, col_bus, col_rs = st.columns([1, 1.4, 1.1])

    # 1. Teachers Column
    with col_t:
        st.markdown('<div class="sec-header">Teachers</div>', unsafe_allow_html=True)
        for tid, ta in s.teacher_agents.items():
            t_active = tid in active_teachers
            t_committed = [sess for sess in ta.sessions if sess.session_id in committed_sessions]
            t_failed    = [sess for sess in ta.sessions if sess.failed]

            if t_committed and len(t_committed) == len(ta.sessions):
                state_str, pill_cls, card_cls = "Committed", "pill-committed", "committed"
            elif t_active:
                state_str, pill_cls, card_cls = "Negotiating", "pill-negotiating", "active"
            elif t_failed:
                state_str, pill_cls, card_cls = "Exhausted", "pill-failed", "failed"
            else:
                state_str, pill_cls, card_cls = "Idle", "pill-idle", ""

            committed_lines = ""
            for sess in t_committed:
                slot_info, room_info = committed_sessions.get(sess.session_id, ("?", "?"))
                committed_lines += f"<div style='color:#059669; font-size:0.74rem; font-family:\"JetBrains Mono\",monospace;'>✓ [{sess.course_id}] {slot_info} | {room_info}</div>"

            active_notice = ""
            if last_msg and last_msg.sender_id == tid:
                active_notice = f"<div style='color:var(--primary-2); font-size:0.73rem; font-family:\"JetBrains Mono\",monospace; margin-top:4px;'>Active Session: {last_msg.session_id}</div>"

            nogood_total = sum(len(v) for v in ta._nogoods.values())

            st.markdown(f"""
<div class="agent-card {card_cls}">
  <div class="agent-header">
    <span class="agent-type">PRIORITY {ta.priority}</span>
    <span class="status-pill {pill_cls}">{state_str}</span>
  </div>
  <div class="agent-name">{ta.name}</div>
  <div style="font-size:0.73rem; color:var(--muted); font-family:'JetBrains Mono',monospace; margin:4px 0 6px;">
    Teaches: {', '.join(x.course_id for x in ta.sessions)}
  </div>
  {committed_lines}
  {active_notice}
  <div style="margin-top:6px; font-size:0.72rem; color:var(--muted); font-family:'JetBrains Mono',monospace;">
    Clashes found: {nogood_total}
  </div>
</div>
""", unsafe_allow_html=True)

    # 2. Message Bus Feed Column
    with col_bus:
        st.markdown('<div class="sec-header">Messages</div>', unsafe_allow_html=True)

        if not shown_msgs:
            st.markdown("""
<div style="border: 1.5px dashed var(--surface-3); background: var(--bg); border-radius: 8px; padding: 26px; text-align: center; color: var(--muted); font-size:0.8rem;">
  <strong>NO MESSAGES YET</strong><br/>
  Use the controls on the left to start
</div>
""", unsafe_allow_html=True)
        else:
            visible_window = list(reversed(shown_msgs[-35:]))
            feed_html = ""
            for m in visible_window:
                m_type = m.msg_type.value
                slot_val = m.payload.get("slot", "")
                room_val = m.payload.get("room_id", "")
                cost_val = m.payload.get("cost", "")
                crs_val  = m.payload.get("course_id", "")
                rsn_val  = m.payload.get("reason", "")

                details = []
                if slot_val: details.append(f"slot: {slot_val}")
                if room_val: details.append(f"room: {room_val}")
                if crs_val:  details.append(f"course: {crs_val}")
                if cost_val != "": details.append(f"cost: {cost_val}")
                if rsn_val:  details.append(f"reason: {rsn_val[:85]}")

                detail_text = " • ".join(details)

                feed_html += f"""
<div class="msg-bubble">
  <div class="msg-meta">
    <span class="badge-tag badge-{m_type}">{m_type}</span>
    <span class="msg-actors"><strong>{m.sender_id}</strong> &rarr; <strong>{m.receiver_id}</strong></span>
    <span style="color:var(--muted); margin-left:auto; font-size:0.7rem;">R{m.round_num}</span>
  </div>
  <div class="msg-details">{detail_text}</div>
</div>
"""
            st.markdown(feed_html, unsafe_allow_html=True)

    # 3. Rooms and Students Column
    with col_rs:
        st.markdown('<div class="sec-header">Rooms</div>', unsafe_allow_html=True)
        for rid, ra in s.room_agents.items():
            r_committed = {}
            r_tentative = {}
            for m in shown_msgs:
                if m.msg_type == MsgType.COMMIT and m.receiver_id == rid:
                    r_committed[str(m.payload.get("slot",""))] = m.session_id
                elif m.msg_type == MsgType.AWARD and m.receiver_id == rid:
                    r_tentative[str(m.payload.get("slot",""))] = m.session_id
                elif m.msg_type == MsgType.RELEASE and m.receiver_id == rid:
                    r_tentative.pop(str(m.payload.get("slot","")), None)

            if r_committed:
                state_str, pill_cls, card_cls = "Committed", "pill-committed", "committed"
            elif r_tentative or (rid in active_rooms):
                state_str, pill_cls, card_cls = "Holding", "pill-negotiating", "active"
            else:
                state_str, pill_cls, card_cls = "Idle", "pill-idle", ""

            hold_html = ""
            for sl, sid in r_committed.items():
                hold_html += f"<div style='color:#059669; font-size:0.73rem; font-family:\"JetBrains Mono\",monospace;'>✓ {sid} @ {sl}</div>"
            for sl, sid in r_tentative.items():
                hold_html += f"<div style='color:#B45309; font-size:0.73rem; font-family:\"JetBrains Mono\",monospace;'>[HOLD] {sid} @ {sl}</div>"

            st.markdown(f"""
<div class="agent-card {card_cls}">
  <div class="agent-header">
    <span class="agent-type">{ra.room_type} // CAP {ra.capacity}</span>
    <span class="status-pill {pill_cls}">{state_str}</span>
  </div>
  <div class="agent-name">{ra.room_id}</div>
  <div style="font-size:0.72rem; color:var(--muted); font-family:'JetBrains Mono',monospace; margin-bottom:4px;">
    {ra.building}
  </div>
  {hold_html}
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="sec-header" style="margin-top:16px;">Student Groups</div>', unsafe_allow_html=True)
        if not s.student_agents:
            st.markdown("""
<div style="color:var(--muted); font-size:0.76rem; font-family:'JetBrains Mono',monospace; padding:6px 0;">
  [No cohort constraints in this scenario]
</div>
""", unsafe_allow_html=True)
        for sid_key, sa in s.student_agents.items():
            stud_schedule = {}
            stud_nogoods  = 0
            for m in shown_msgs:
                if m.msg_type == MsgType.COMMIT and m.receiver_id == sid_key:
                    stud_schedule[m.payload.get("course_id","")] = str(m.payload.get("slot",""))
                elif m.msg_type == MsgType.NOGOOD and m.sender_id == sid_key:
                    stud_nogoods += 1

            if stud_schedule:
                state_str, pill_cls, card_cls = "Committed", "pill-committed", "committed"
            elif sid_key in active_students:
                state_str, pill_cls, card_cls = "Validating", "pill-negotiating", "active"
            else:
                state_str, pill_cls, card_cls = "Idle", "pill-idle", ""

            sched_lines = ""
            for crs, sl in stud_schedule.items():
                sched_lines += f"<div style='color:#059669; font-size:0.73rem; font-family:\"JetBrains Mono\",monospace;'>✓ {crs} @ {sl}</div>"

            st.markdown(f"""
<div class="agent-card {card_cls}">
  <div class="agent-header">
    <span class="agent-type">COHORT</span>
    <span class="status-pill {pill_cls}">{state_str}</span>
  </div>
  <div class="agent-name">{sa.name}</div>
  <div style="font-size:0.72rem; color:var(--muted); font-family:'JetBrains Mono',monospace; margin:2px 0 4px;">
    Takes: {', '.join(sa.enrolled_courses)}
  </div>
  {sched_lines}
  <div style="margin-top:4px; font-size:0.72rem; color:var(--muted); font-family:'JetBrains Mono',monospace;">
    Clashes avoided: {stud_nogoods}
  </div>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 2: MASTER MATRIX (TIMETABLE)
# ═════════════════════════════════════════════════════════════════════════════

with tab_matrix:
    st.markdown('<div class="sec-header">Weekly Timetable</div>', unsafe_allow_html=True)

    committed_at_idx = {sid for sid, _ in committed_sessions.items()}
    grid = {p.value: {d.value: "" for d in ALL_DAYS} for p in ALL_PERIODS}

    for sess in s.sessions:
        if sess.session_id in committed_at_idx and sess.assigned_slot:
            slot = sess.assigned_slot
            day_k = slot.day.value
            per_k = slot.period.value
            grid[per_k][day_k] = (
                f"{sess.course_id}\n"
                f"{sess.teacher_id} | {sess.assigned_room} ({sess.enrollment} seats)"
            )

    if not any(any(v for v in row.values()) for row in grid.values()):
        st.markdown("""
<div class="status-box info">
  No classes placed yet. Press Next Step to fill the timetable.
</div>
""", unsafe_allow_html=True)
    else:
        df_tt = pd.DataFrame(grid).T
        df_tt.index.name = "Period"
        ordered_cols = [d.value for d in ALL_DAYS if d.value in df_tt.columns]
        df_tt = df_tt[ordered_cols]
        st.dataframe(df_tt, use_container_width=True, height=420)

    unscheduled = [sess for sess in s.sessions if not sess.is_committed and sess.session_id not in committed_at_idx]
    if unscheduled:
        st.markdown('<div class="sec-header">Unallocated Sessions</div>', unsafe_allow_html=True)
        for sess in unscheduled:
            tag = "DOMAIN EXHAUSTED" if sess.failed else "PENDING ALLOCATION"
            st.markdown(f"""
<div class="status-box error" style="margin-bottom:6px;">
  <strong>[{tag}]</strong> {sess.session_id} ({sess.course_name}) &nbsp;•&nbsp; 
  Teacher: {sess.teacher_id} &nbsp;•&nbsp; Required: {sess.room_type} (Cap {sess.enrollment})
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 3: CONSTRAINT VERIFICATION (H1–H6)
# ═════════════════════════════════════════════════════════════════════════════

with tab_verify:
    st.markdown('<div class="sec-header">Rule Checks (6 basic rules)</div>', unsafe_allow_html=True)

    if s.validation_report is None:
        st.markdown('<div class="status-box info">Validator uninitialized.</div>', unsafe_allow_html=True)
    else:
        report = s.validation_report
        if report.is_fully_valid:
            st.markdown("""
<div class="status-box success">
  <strong>MATHEMATICAL PROOF VERIFIED:</strong> All formal hard constraints H1–H6 pass with zero violations across all committed sessions.
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="status-box error">
  <strong>VIOLATIONS DETECTED:</strong> {report.total_violations} constraint violation(s) present.
</div>
""", unsafe_allow_html=True)

        for r in report.results:
            badge_markup = f'<span class="{"badge-pass" if r.passed else "badge-fail"}">{"PASS" if r.passed else "FAIL"}</span>'
            with st.expander(f"{r.constraint_id}: {r.constraint_name}"):
                st.markdown(badge_markup, unsafe_allow_html=True)
                desc_map = {
                    "H1": "Teacher Non-Overlap: An instructor cannot be assigned to multiple sessions during the same period.",
                    "H2": "Room Non-Overlap: A classroom/lab cannot host multiple sessions concurrently.",
                    "H3": "Cohort Non-Overlap: A student group cannot have overlapping scheduled sessions.",
                    "H4": "Room Capacity: Venue seating capacity must be greater than or equal to course enrollment.",
                    "H5": "Room Type Compatibility: Specialized courses (e.g. Computer Labs) require matching facility classification.",
                    "H6": "Instructor Availability: Assigned slots must adhere to stated instructor working hours.",
                }
                st.markdown(f'<div style="color:#cbd5e1; font-size:0.83rem; margin:8px 0 10px; line-height:1.5;">{desc_map.get(r.constraint_id, "")}</div>', unsafe_allow_html=True)
                if r.passed:
                    st.markdown("<span style='color:#34d399; font-size:0.8rem; font-family:\"JetBrains Mono\",monospace;'>Status: Verified compliant (0 violations)</span>", unsafe_allow_html=True)
                else:
                    for v in r.violations:
                        st.error(v)

        st.markdown('<div class="sec-header">Final Session Assignment Registry</div>', unsafe_allow_html=True)
        registry = [
            {"Session": ss.session_id, "Course": ss.course_name,
             "Teacher": ss.teacher_id, "Slot": str(ss.assigned_slot),
             "Room": ss.assigned_room, "Enrollment": ss.enrollment,
             "RoomType": str(ss.room_type), "Outcome": "COMMITTED"}
            for ss in s.sessions if ss.is_committed
        ] + [
            {"Session": ss.session_id, "Course": ss.course_name,
             "Teacher": ss.teacher_id, "Slot": "—", "Room": "—",
             "Enrollment": ss.enrollment, "RoomType": str(ss.room_type),
             "Outcome": "FAILED (UNSATISFIABLE)"}
            for ss in s.sessions if ss.failed
        ]
        if registry:
            st.dataframe(pd.DataFrame(registry), use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 4: TELEMETRY & ANALYTICS
# ═════════════════════════════════════════════════════════════════════════════

with tab_metrics:
    st.markdown('<div class="sec-header">Stats</div>', unsafe_allow_html=True)

    stats = s.stats
    c1, c2, c3, c4 = st.columns(4)

    sched_count   = sum(1 for ss in s.sessions if ss.is_committed)
    failed_count  = sum(1 for ss in s.sessions if ss.failed)
    unsched_count = sum(1 for ss in s.sessions if not ss.is_committed)

    c1.metric("Classes Placed", sched_count)
    c2.metric("Not Placed", unsched_count)
    c3.metric("Rounds", stats.negotiation_rounds)
    c4.metric("Messages Sent", len(s.message_log))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Clash Checks OK", stats.proposals_accepted)
    c6.metric("Rooms Said No", stats.proposals_rejected)
    c7.metric("Clashes Found", stats.nogoods_generated)
    viol_total = s.validation_report.total_violations if s.validation_report else 0
    c8.metric("Rule Breaks", viol_total)

    st.markdown("---")

    type_counts = Counter(m.msg_type.value for m in s.message_log)
    df_types = pd.DataFrame([{"Type": k, "Count": v} for k, v in type_counts.most_common()])

    try:
        import plotly.express as px
        col_ch1, col_ch2 = st.columns(2)
        with col_ch1:
            st.markdown('<div class="sec-header">Message Distribution by Protocol Type</div>', unsafe_allow_html=True)
            fig1 = px.bar(
                df_types, x="Type", y="Count", color="Type",
                color_discrete_map={
                    "CFP":"#6366F1","BID":"#10B981","REJECT":"#EF4444",
                    "AWARD":"#F59E0B","RELEASE":"#94A3B8","ACCEPT":"#059669",
                    "NOGOOD":"#EA580C","BACKTRACK":"#A855F7",
                    "COMMIT":"var(--primary)","VALIDATE":"var(--primary-3)",
                },
                template="plotly_white"
            )
            fig1.update_layout(
                showlegend=False, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                font=dict(color="var(--text)", family="Plus Jakarta Sans, sans-serif")
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col_ch2:
            st.markdown('<div class="sec-header">Instructor Pedagogical Utility per Session</div>', unsafe_allow_html=True)
            util_data = []
            for sess in s.sessions:
                if sess.is_committed:
                    ta = s.teacher_agents.get(sess.teacher_id)
                    if ta and sess.assigned_slot:
                        u = ta._utility(sess.assigned_slot, sess)
                        util_data.append({"Session": sess.course_id, "Utility": round(u, 2)})
            if util_data:
                fig2 = px.bar(
                    pd.DataFrame(util_data), x="Session", y="Utility",
                    color="Utility",
                    color_continuous_scale=[[0, "var(--chip)"], [0.5, "var(--primary-2)"], [1, "var(--primary)"]],
                    template="plotly_white"
                )
                fig2.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                    font=dict(color="var(--text)", family="Plus Jakarta Sans, sans-serif")
                )
                st.plotly_chart(fig2, use_container_width=True)
    except ImportError:
        st.dataframe(df_types, use_container_width=True)

    st.markdown('<div class="sec-header">Agent Summary</div>', unsafe_allow_html=True)
    agent_rows = []
    for tid, ta in s.teacher_agents.items():
        agent_rows.append({
            "Agent": ta.name, "Classification": "Teacher",
            "Priority": str(ta.priority), "Total Sessions": len(ta.sessions),
            "Committed": sum(1 for sess in ta.sessions if sess.is_committed),
            "Clashes found": ta.nogood_count(),
            "Outbound Messages": ta.msgs_sent, "Inbound Messages": ta.msgs_received,
        })
    for rid, ra in s.room_agents.items():
        agent_rows.append({
            "Agent": ra.room_id, "Classification": f"Room ({ra.room_type})",
            "Priority": "—", "Total Sessions": "—",
            "Committed": len(ra._committed),
            "Clashes found": "—",
            "Outbound Messages": ra.msgs_sent, "Inbound Messages": ra.msgs_received,
        })
    st.dataframe(pd.DataFrame(agent_rows), use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
#  TAB 5: SYSTEM ARCHITECTURE
# ═════════════════════════════════════════════════════════════════════════════

with tab_arch:
    st.markdown(r"""
### Multi-Agent Protocol Specification

#### 1. How agents agree (offers and bids)
```
Teacher (Manager)                Room (Contractor)           Student (Cohort)
       |                                |                            |
       |--- CFP(session, slot) -------->|                            |
       |<-- BID(cost) / REJECT ---------|                            |
       |                                |                            |
       |--- AWARD (tentative hold) ---->|                            |
       |                                |                            |
       |--- VALIDATE(cohort, slot) --------------------------------->|
       |<-- ACCEPT / NOGOOD(conflict) ------------------------------|
       |                                |                            |
[ACCEPT]-- COMMIT --------------------->|--------------------------->|
[NOGOOD]-- RELEASE (clear hold) ------->|                            |
       (Teacher learns Nogood, backtracks to next candidate slot)
```

---

#### 2. Protocol Primitives

| Message Type | Semantics & Pre-Conditions | Post-Conditions |
|:---|:---|:---|
| **CFP** | Teacher initiates negotiation for slot $T$ | Rooms evaluate local constraints H2, H4, H5 |
| **BID** | Room verifies capacity, type, and availability | Computes resource efficiency cost ($C = \text{cap} - \text{enroll}$) |
| **REJECT** | Room fails H2, H4, or H5 constraint check | Informs teacher of failure reason; teacher prunes room |
| **AWARD** | Teacher selects room with $\min(\text{cost})$ | Room places tentative hold on slot $T$ |
| **VALIDATE** | Teacher checks cohort availability | Student agent inspects personal schedule |
| **ACCEPT** | Cohort has no conflicting commitments (H3 satisfied) | Ready for final commitment |
| **NOGOOD** | Cohort detects schedule collision | Teacher logs $(T, \text{reason})$ in nogood set |
| **RELEASE** | Cohort rejected tentative assignment | Room releases tentative hold; slot becomes available |
| **BACKTRACK** | Teacher advances search pointer to next ranked slot | Re-initiates CFP round with pruned domain |
| **COMMIT** | Both room and students agree | Immutable assignment logged in all agent databases |
""")





# ─── Bottom Auto-Play Ticker (Renders AFTER UI is drawn) ─────────────────────

if st.session_state.is_playing and sim() is not None:
    total = len(sim().message_log)
    if st.session_state.replay_idx < total:
        time.sleep(st.session_state.anim_speed)
        st.session_state.replay_idx += 1
        st.rerun()
    else:
        st.session_state.is_playing = False
        st.rerun()
