import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import plotly.graph_objects as go
import textwrap
import json
import hashlib
import secrets

# =========================================================
# SONARA - app.py
# v0.9.0 con motor acústico WALLS portado desde MATLAB
# =========================================================

APP_VERSION = "BETA"

DATA_DIR = Path("data")
ASSETS_DIR = Path("assets")
USERS_CSV = DATA_DIR / "users.csv"
ACADEMY_CSV = DATA_DIR / "academy_users.csv"
PREMIUM_CSV = DATA_DIR / "premium_users.csv"
PROJECTS_JSON = DATA_DIR / "projects.json"
PROJECTS_DIR = DATA_DIR / "projects"
MATERIALS_CSV = DATA_DIR / "materiales_sonara.csv"
LOSCAA_CSV = DATA_DIR / "loscaa_validacion.csv"
SETTINGS_JSON = DATA_DIR / "settings.json"

SUPERUSERS = {"maaraos@gmail.com"}

TRIAL_MAX_PROJECTS = 2
TRIAL_MAX_SOLUTIONS = 20
TRIAL_DAYS = 3

SONARA_LOGO_B64 = ""


def bootstrap_sonara_assets():
    """
    Genera assets livianos de SONARA sin incrustar imágenes gigantes en app.py.
    """
    ASSETS_DIR.mkdir(exist_ok=True)
    logo_png = ASSETS_DIR / "logo_sonara.png"
    favicon_png = ASSETS_DIR / "favicon_sonara.png"

    if logo_png.exists() and favicon_png.exists():
        return logo_png, favicon_png

    try:
        from PIL import Image, ImageDraw, ImageFont

        def font(size, bold=False):
            candidates = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
            ]
            for c in candidates:
                try:
                    return ImageFont.truetype(c, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        W, H = 900, 430
        img = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(img)

        navy = (5, 24, 43)
        blue = (30, 144, 255)
        steel = (95, 110, 125)
        wool = (214, 188, 105)

        x0, y0 = 70, 85
        layer_w, layer_h = 170, 36
        gap = 38
        offsets = [0, 50, 10]
        for i, off in enumerate(offsets):
            y = y0 + i * (layer_h + gap)
            d.rounded_rectangle([x0 + off, y, x0 + off + layer_w, y + layer_h], radius=8, fill=(235, 238, 242), outline=steel, width=3)
            d.rounded_rectangle([x0 + off + 22, y + layer_h, x0 + off + layer_w - 18, y + layer_h + 28], radius=5, fill=wool if i != 1 else (40, 52, 64))
            d.line([x0 + off + layer_w, y + 8, x0 + off + layer_w + 48, y + 30], fill=steel, width=5)
            d.line([x0 + off + layer_w + 48, y + 30, x0 + off + layer_w + 48, y + layer_h + 54], fill=steel, width=5)

        d.text((310, 125), "SONARA", fill=navy, font=font(76, True))
        d.text((318, 215), "ACOUSTIC DESIGN ASSISTANT", fill=blue, font=font(25, True))

        labels = ["ANALIZA", "DISEÑA", "OPTIMIZA", "CUMPLE"]
        for j, lab in enumerate(labels):
            x = 315 + j * 130
            d.line([x, 300, x + 70, 300], fill=(210, 218, 228), width=2)
            d.text((x, 320), lab, fill=navy, font=font(16, True))

        img.save(logo_png, "PNG", optimize=True)

        fav = Image.new("RGB", (256, 256), "white")
        fd = ImageDraw.Draw(fav)
        fd.rounded_rectangle([24, 24, 232, 232], radius=44, fill=(5, 24, 43))
        fd.text((50, 58), "S", fill="white", font=font(126, True))
        fd.text((72, 182), "SONARA", fill=(30, 144, 255), font=font(24, True))
        fav.save(favicon_png, "PNG", optimize=True)

    except Exception:
        svg = """<svg xmlns='http://www.w3.org/2000/svg' width='900' height='430' viewBox='0 0 900 430'>
        <rect width='900' height='430' rx='30' fill='white'/>
        <text x='300' y='180' font-size='82' font-family='Arial' font-weight='700' fill='#05182b'>SONARA</text>
        <text x='307' y='230' font-size='26' font-family='Arial' font-weight='700' fill='#1e90ff'>ACOUSTIC DESIGN ASSISTANT</text>
        <text x='310' y='330' font-size='18' font-family='Arial' font-weight='700' fill='#05182b'>ANALIZA · DISEÑA · OPTIMIZA · CUMPLE</text>
        <rect x='80' y='100' width='150' height='30' fill='#e9eef5' stroke='#607080' stroke-width='4'/>
        <rect x='120' y='165' width='150' height='30' fill='#e9eef5' stroke='#607080' stroke-width='4'/>
        <rect x='80' y='230' width='150' height='30' fill='#e9eef5' stroke='#607080' stroke-width='4'/>
        </svg>"""
        logo_svg = ASSETS_DIR / "logo_sonara.svg"
        logo_svg.write_text(svg, encoding="utf-8")
        return logo_svg, logo_svg

    return logo_png, favicon_png


_BOOT_LOGO, _BOOT_FAVICON = bootstrap_sonara_assets()


st.set_page_config(
    page_title="SONARA",
    page_icon=str(_BOOT_FAVICON),
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
    --bg: #03070d;
    --panel: #07111d;
    --panel2: #0b1624;
    --blue: #0A84FF;
    --blue-dark: #0F4C81;
    --blue-deep: #06213D;
    --text: #F5F8FF;
    --muted: #AAB7C7;
    --line: rgba(79,166,255,.24);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 76% 14%, rgba(10,132,255,.18), transparent 30%),
        radial-gradient(circle at 26% 18%, rgba(0,87,184,.16), transparent 24%),
        linear-gradient(135deg, #010307 0%, #050910 45%, #07111d 100%);
    color: var(--text);
}

#MainMenu, footer { visibility: hidden; }
header { visibility: visible; }

.block-container {
    padding-top: 1.3rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

/* Sidebar */

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #02050a 0%, #06101b 52%, #010307 100%);
    border-right: 1px solid var(--line);
    box-shadow: 12px 0 40px rgba(0,0,0,.45);
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

[data-testid="stSidebar"] img {
    background: transparent;
    border-radius: 18px;
    padding: 4px;
    filter: drop-shadow(0 14px 30px rgba(0,132,255,.20));
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    height: 50px;
    justify-content: flex-start;
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    color: #EAF4FF !important;
    border-radius: 12px;
    box-shadow: none;
    padding-left: 14px;
    font-weight: 800;
    font-size: 15px;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(90deg, rgba(10,132,255,.95), rgba(0,63,133,.55));
    border: 1px solid rgba(128,196,255,.35);
    transform: translateX(2px);
}

.sidebar-license-card {
    margin-top: 22px;
    padding: 18px;
    border-radius: 16px;
    background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.025));
    border: 1px solid rgba(120,190,255,.22);
    box-shadow: 0 16px 35px rgba(0,0,0,.26);
}

.sidebar-title {
    font-size: 12px;
    text-transform: uppercase;
    color: #9FD4FF !important;
    font-weight: 800;
    letter-spacing: .06em;
}

.sidebar-badge {
    display: inline-block;
    margin-top: 10px;
    padding: 8px 14px;
    border-radius: 10px;
    background: rgba(10,132,255,.15);
    border: 1px solid rgba(10,132,255,.32);
    font-weight: 900;
}

.sidebar-days {
    font-size: 26px;
    font-weight: 900;
    color: #20A4FF !important;
    margin-top: 12px;
}

.sidebar-small {
    font-size: 12px;
    color: #AAB7C7 !important;
    margin-top: 8px;
}

/* Portada */

.hero-wrap {
    text-align: center;
    padding: 20px 0 6px;
}

.hero-title {
    font-size: 48px;
    letter-spacing: .22em;
    font-weight: 900;
    color: #fff;
    margin-top: 2px;
}

.hero-kicker {
    font-size: 15px;
    letter-spacing: .44em;
    color: #1DA1FF;
    font-weight: 800;
    margin-top: -8px;
}

.hero-line {
    width: 64px;
    height: 3px;
    background: var(--blue);
    border-radius: 10px;
    margin: 18px auto;
}

.hero-main {
    font-size: 24px;
    font-weight: 800;
    color: #fff;
}

.hero-sub {
    font-size: 16px;
    color: #B6C2D0;
    max-width: 760px;
    margin: 10px auto 18px;
    line-height: 1.6;
}

.hero-tags {
    color: #1DA1FF;
    font-size: 13px;
    font-weight: 900;
    letter-spacing: .18em;
    text-transform: uppercase;
    margin-top: 18px;
}

.card {
    background: linear-gradient(180deg, rgba(10,17,28,.92), rgba(5,10,18,.88));
    border: 1px solid rgba(124,190,255,.22);
    border-radius: 16px;
    padding: 26px;
    box-shadow: 0 18px 45px rgba(0,0,0,.32);
}

.card-title {
    font-size: 22px;
    font-weight: 900;
    color: #fff;
    margin-bottom: 14px;
}

.card-text {
    color: #B6C2D0;
    font-size: 14px;
    line-height: 1.55;
}

.plan {
    min-height: 170px;
    background: linear-gradient(180deg, rgba(8,18,32,.92), rgba(4,8,14,.92));
    border: 1px solid rgba(10,132,255,.28);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 16px 40px rgba(0,0,0,.28);
}

.plan.academy { border-color: rgba(0,220,130,.28); }
.plan.premium { border-color: rgba(255,178,0,.35); }

.plan-title {
    font-size: 18px;
    font-weight: 900;
    color: #26A8FF;
    text-transform: uppercase;
    letter-spacing: .06em;
}

.plan-title.academy { color: #00DE78; }
.plan-title.premium { color: #FFC02E; }

.plan-price {
    font-size: 18px;
    font-weight: 900;
    color: #fff;
    margin: 12px 0 8px;
}

.plan-text {
    font-size: 14px;
    color: #B6C2D0;
    line-height: 1.5;
}

.top-links {
    text-align: right;
    color: #EAF4FF;
    font-weight: 700;
    font-size: 14px;
    margin-right: 4px;
}

.top-links span {
    margin-left: 24px;
    color: #EAF4FF;
}

/* Formularios */

.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stRadio label,
.stCheckbox label {
    color: #F2F7FF !important;
    font-weight: 800 !important;
}

.stTextInput input,
.stNumberInput input {
    background: #0b1624 !important;
    border: 1px solid rgba(124,190,255,.45) !important;
    color: #fff !important;
    border-radius: 10px !important;
    height: 48px;
    font-weight: 800 !important;
}

div[role="radiogroup"] * {
    color: #FFFFFF !important;
    opacity: 1 !important;
    font-weight: 800 !important;
}

div[data-baseweb="select"] {
    background: linear-gradient(135deg, #06213D, #0F4C81) !important;
    border: 1px solid rgba(120,190,255,.55) !important;
    border-radius: 10px !important;
    min-height: 44px !important;
}

div[data-baseweb="select"] > div {
    background: transparent !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] div {
    color: #FFFFFF !important;
    font-weight: 900 !important;
}

div[data-baseweb="select"] svg { fill: #FFFFFF !important; }

div[data-baseweb="popover"] { background: #06213D !important; }

div[data-baseweb="popover"] ul {
    background: #06213D !important;
    border: 1px solid rgba(120,190,255,.55) !important;
    border-radius: 10px !important;
}

div[data-baseweb="popover"] li {
    background: #06213D !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
}

div[data-baseweb="popover"] li span,
div[data-baseweb="popover"] span {
    color: #FFFFFF !important;
    font-weight: 800 !important;
}

div[data-baseweb="popover"] li:hover {
    background: #0F4C81 !important;
    color: #FFFFFF !important;
}

div[data-baseweb="popover"] li[aria-selected="true"] {
    background: #0A63B8 !important;
    color: #FFFFFF !important;
}

/* Botones */

.stButton > button,
.stDownloadButton > button,
div[data-testid="stDownloadButton"] button {
    background: linear-gradient(90deg, #0A84FF, #0057B8) !important;
    color: white !important;
    border: 0 !important;
    border-radius: 12px !important;
    height: 58px !important;
    font-weight: 900 !important;
    font-size: 16px !important;
    box-shadow: 0 14px 30px rgba(10,132,255,.28) !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
div[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(90deg, #26A8FF, #0A63CA) !important;
    color: white !important;
}

/* Calculadora */

.sonara-card {
    background: linear-gradient(180deg, rgba(9,20,34,.96), rgba(4,9,16,.96));
    border: 1px solid rgba(71,166,255,.28);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 18px 42px rgba(0,0,0,.30);
}

.sonara-card-title {
    font-size: 24px;
    font-weight: 900;
    color: #FFFFFF;
    margin-bottom: 16px;
}

.result-note {
    background: rgba(10,132,255,.11);
    border-left: 4px solid #0A84FF;
    border-radius: 10px;
    padding: 12px 14px;
    color: #DDEEFF;
    font-size: 13px;
}

.layer-box {
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,.35);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 900;
    text-align: center;
    margin: 0 2px;
    min-height: 190px;
    box-shadow: inset 0 0 18px rgba(255,255,255,.06), 0 10px 24px rgba(0,0,0,.25);
    writing-mode: vertical-rl;
    transform: rotate(180deg);
}

.air-box {
    background: linear-gradient(180deg, rgba(34,154,255,.14), rgba(34,154,255,.04)) !important;
    border: 1px dashed rgba(90,185,255,.45);
    color: #9FD4FF;
}

.wool-lines {
    background: repeating-linear-gradient(
        75deg,
        rgba(212,178,74,.78),
        rgba(212,178,74,.78) 4px,
        rgba(60,45,15,.4) 5px,
        rgba(60,45,15,.4) 15px
    ) !important;
}

.result-card {
    background: linear-gradient(180deg, #081827, #03070d);
    border: 1px solid rgba(10,132,255,.45);
    border-radius: 14px;
    padding: 20px;
    min-height: 120px;
    box-shadow: 0 14px 32px rgba(0,0,0,.35);
}

.result-label {
    color: #8FD0FF;
    font-size: 18px;
    font-weight: 900;
    letter-spacing: .05em;
    text-transform: uppercase;
}

.result-value {
    color: #FFFFFF;
    font-size: 48px;
    font-weight: 900;
    margin-top: 8px;
    line-height: 1;
}

.result-unit {
    color: #8FD0FF;
    font-size: 15px;
    font-weight: 800;
    margin-top: 8px;
}

hr {
    border: 0;
    height: 1px;
    background: rgba(124,190,255,.16);
    margin: 28px 0;
}


/* Expander SONARA */
[data-testid="stExpander"] {
    background: linear-gradient(180deg, rgba(9,20,34,.90), rgba(4,9,16,.90)) !important;
    border: 1px solid rgba(71,166,255,.22) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] details { background: transparent !important; }
[data-testid="stExpander"] summary {
    background: rgba(8,18,32,.95) !important;
    color: #FFFFFF !important;
    font-weight: 900 !important;
    border-bottom: 1px solid rgba(124,190,255,.14) !important;
}
[data-testid="stExpander"] summary * {
    color: #FFFFFF !important;
    opacity: 1 !important;
    font-weight: 900 !important;
}
[data-testid="stExpander"] div[role="button"] {
    color: #FFFFFF !important;
    background: rgba(8,18,32,.95) !important;
}
[data-testid="stExpander"] p,
[data-testid="stExpander"] li,
[data-testid="stExpander"] span,
[data-testid="stExpander"] div {
    color: #EAF4FF !important;
}
.stCheckbox label, .stCheckbox label p, .stCheckbox span {
    color: #FFFFFF !important;
    opacity: 1 !important;
    font-weight: 800 !important;
}

h1, h2, h3, p, li, span, div { color: inherit; }

.project-panel {
    background: linear-gradient(145deg, rgba(9,28,48,.96), rgba(5,14,25,.98));
    border: 1px solid rgba(83,178,255,.38);
    box-shadow: 0 18px 60px rgba(0,0,0,.28);
    border-radius: 22px;
    padding: 24px 26px;
    margin: 14px 0 22px 0;
}
.project-panel-title {
    color: #FFFFFF;
    font-size: 24px;
    font-weight: 900;
    margin-bottom: 10px;
}
.project-panel-text {
    color: #DCEBFF;
    font-size: 15px;
    line-height: 1.75;
}
.project-pill {
    display:inline-block;
    padding: 7px 12px;
    margin: 5px 7px 5px 0;
    border-radius: 999px;
    background: rgba(35,137,255,.18);
    border: 1px solid rgba(83,178,255,.30);
    color: #EAF4FF;
    font-weight: 800;
    font-size: 12px;
}
.status-ok { color:#00E08A; font-weight:900; }
.status-bad { color:#FF6B6B; font-weight:900; }
.status-warn { color:#FFD166; font-weight:900; }


/* --- Ajuste visual SONARA v0.16.1 --- */
section[data-testid="stSidebar"] {
    width: 305px !important;
    min-width: 305px !important;
}

section[data-testid="stSidebar"] > div {
    padding-left: 14px !important;
    padding-right: 14px !important;
}

section[data-testid="stSidebar"] img {
    max-width: 188px !important;
    width: 188px !important;
    display: block !important;
    margin: 4px auto 18px auto !important;
    border-radius: 16px !important;
}

.hero-logo-wrap {
    width: 420px;
    max-width: 420px;
    margin: 0 0 18px 0;
}

.hero-logo-wrap img {
    width: 420px !important;
    max-width: 420px !important;
    border-radius: 18px !important;
    box-shadow: 0 14px 36px rgba(0,0,0,.22) !important;
}

.hero-wrap {
    max-width: 980px;
    overflow: hidden;
}

.hero-title {
    font-size: 50px !important;
    letter-spacing: .22em !important;
    line-height: 1.05 !important;
}

.hero-main {
    font-size: 24px !important;
    line-height: 1.3 !important;
    max-width: 840px !important;
}

.hero-sub {
    max-width: 860px !important;
}

@media (max-width: 900px) {
    .hero-title {
        font-size: 38px !important;
        letter-spacing: .14em !important;
    }
    .hero-main {
        font-size: 20px !important;
    }
}


section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    min-height: 54px !important;
    padding: 10px 14px !important;
    border-radius: 14px !important;
    font-size: 16px !important;
}


/* --- Tabs proyecto visibles v0.17 --- */
div[data-testid="stTabs"] button {
    color: #EAF4FF !important;
    font-weight: 900 !important;
    opacity: 1 !important;
}
div[data-testid="stTabs"] button p {
    color: #EAF4FF !important;
    font-weight: 900 !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #FFFFFF !important;
    border-bottom: 3px solid #1E90FF !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] p {
    color: #FFFFFF !important;
}
.project-flow-card {
    background: linear-gradient(145deg, rgba(7,23,40,.98), rgba(2,10,18,.98));
    border: 1px solid rgba(65,165,255,.42);
    border-radius: 20px;
    padding: 22px 24px;
    margin: 14px 0 20px 0;
    box-shadow: 0 14px 50px rgba(0,0,0,.24);
}
.project-flow-title {
    color:#FFFFFF;
    font-size:22px;
    font-weight:900;
    margin-bottom:8px;
}
.project-flow-text {
    color:#DCEBFF;
    line-height:1.7;
    font-size:15px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# ARCHIVOS Y LICENCIAS
# =========================================================


def ensure_sonara_logo():
    """
    Retorna el logo liviano generado al iniciar la app.
    """
    logo_file = ASSETS_DIR / "logo_sonara.png"
    favicon_file = ASSETS_DIR / "favicon_sonara.png"
    if not logo_file.exists() or not favicon_file.exists():
        logo_file, favicon_file = bootstrap_sonara_assets()
    return logo_file


def ensure_files():
    DATA_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)
    PROJECTS_DIR.mkdir(exist_ok=True)
    ensure_sonara_logo()

    if not USERS_CSV.exists():
        USERS_CSV.write_text(
            "email,password_hash,salt,nombre,empresa,cargo,first_login,last_login,license_type,estado,trial_start,trial_end\n",
            encoding="utf-8"
        )
    else:
        try:
            df_users = pd.read_csv(USERS_CSV)
            required_cols = ["email","password_hash","salt","nombre","empresa","cargo","first_login","last_login","license_type","estado","trial_start","trial_end"]
            changed = False
            for col in required_cols:
                if col not in df_users.columns:
                    df_users[col] = ""
                    changed = True
            if changed:
                df_users = df_users[required_cols]
                df_users.to_csv(USERS_CSV, index=False)
        except Exception:
            pass

    if not SETTINGS_JSON.exists():
        SETTINGS_JSON.write_text("{}", encoding="utf-8")

    if not ACADEMY_CSV.exists():
        ACADEMY_CSV.write_text(
            "email,nombre,licencia,vigencia\nmaaraos@gmail.com,Marco Araos,academy,2027-12-31\n",
            encoding="utf-8"
        )

    if not PREMIUM_CSV.exists():
        PREMIUM_CSV.write_text(
            "email,nombre,licencia,estado,precio_usd\nmaaraos@gmail.com,Marco Araos,premium,active,0\n",
            encoding="utf-8"
        )

    if not PROJECTS_JSON.exists():
        PROJECTS_JSON.write_text("{}", encoding="utf-8")

    ensure_materials_file()
    ensure_loscaa_file()



# =========================================================
# AUTENTICACIÓN Y CONFIGURACIÓN COMERCIAL
# =========================================================

def load_json_file(path, default=None):
    if default is None:
        default = {}
    try:
        if not path.exists():
            path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else default
    except Exception:
        return default


def save_json_file(path, data):
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    password = password or ""
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000
    ).hex()
    return digest, salt


def verify_password(password, stored_hash, salt):
    if not stored_hash or not salt:
        return False
    digest, _ = hash_password(password, salt)
    return secrets.compare_digest(digest, str(stored_hash))


def ensure_user_record(email, password, nombre="", empresa="", cargo=""):
    email = norm(email)
    now = datetime.now()
    users = read_csv(USERS_CSV)

    required_cols = ["email","password_hash","salt","nombre","empresa","cargo","first_login","last_login","license_type","estado","trial_start","trial_end"]
    for col in required_cols:
        if col not in users.columns:
            users[col] = ""

    exists = False if users.empty else email in users["email"].astype(str).str.lower().values
    if exists:
        return False, "Ese correo ya está registrado."

    end = now + timedelta(days=TRIAL_DAYS)
    pw_hash, salt = hash_password(password)

    new_user = pd.DataFrame([{
        "email": email,
        "password_hash": pw_hash,
        "salt": salt,
        "nombre": nombre or email,
        "empresa": empresa,
        "cargo": cargo,
        "first_login": now.isoformat(timespec="seconds"),
        "last_login": now.isoformat(timespec="seconds"),
        "license_type": "trial",
        "estado": "active",
        "trial_start": now.isoformat(timespec="seconds"),
        "trial_end": end.isoformat(timespec="seconds"),
    }])

    pd.concat([users, new_user], ignore_index=True).to_csv(USERS_CSV, index=False)
    return True, "Usuario creado correctamente."


def authenticate_user(email, password):
    email = norm(email)
    users = read_csv(USERS_CSV)

    if email in SUPERUSERS:
        # Primer acceso developer: si no está registrado, se crea con la contraseña ingresada.
        if users.empty or "email" not in users.columns or email not in users["email"].astype(str).str.lower().values:
            ok, msg = ensure_user_record(email, password, nombre="Marco Araos", empresa="SONARA / Akusoft", cargo="Developer")
            users = read_csv(USERS_CSV)
        # Si existe pero aún no tiene password, se activa con la clave ingresada.
        idxs = users[users["email"].astype(str).str.lower() == email].index
        if len(idxs):
            idx = idxs[0]
            if not str(users.loc[idx].get("password_hash", "")).strip():
                pw_hash, salt = hash_password(password)
                users.loc[idx, "password_hash"] = pw_hash
                users.loc[idx, "salt"] = salt
                users.to_csv(USERS_CSV, index=False)

    if users.empty or "email" not in users.columns:
        return False, "Usuario no registrado."

    match = users[users["email"].astype(str).str.lower() == email]
    if not len(match):
        return False, "Usuario no registrado."

    row = match.iloc[0]
    if not verify_password(password, row.get("password_hash", ""), row.get("salt", "")):
        return False, "Contraseña incorrecta."

    idx = match.index[0]
    users.loc[idx, "last_login"] = datetime.now().isoformat(timespec="seconds")
    users.to_csv(USERS_CSV, index=False)
    return True, "Acceso correcto."


def user_profile(email):
    email = norm(email)
    users = read_csv(USERS_CSV)
    if not users.empty and "email" in users.columns:
        match = users[users["email"].astype(str).str.lower() == email]
        if len(match):
            return match.iloc[0].to_dict()
    return {"email": email, "nombre": email, "empresa": "", "cargo": ""}


def update_user_profile(email, nombre, empresa, cargo):
    email = norm(email)
    users = read_csv(USERS_CSV)
    if users.empty or "email" not in users.columns:
        return False
    idxs = users[users["email"].astype(str).str.lower() == email].index
    if not len(idxs):
        return False
    idx = idxs[0]
    users.loc[idx, "nombre"] = nombre
    users.loc[idx, "empresa"] = empresa
    users.loc[idx, "cargo"] = cargo
    users.to_csv(USERS_CSV, index=False)
    return True


def load_settings():
    return load_json_file(SETTINGS_JSON, {})


def save_settings(data):
    save_json_file(SETTINGS_JSON, data)


def read_csv(path):
    ensure_files()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def norm(email):
    return (email or "").strip().lower()


def get_license(email):
    email = norm(email)
    now = datetime.now()

    if email in SUPERUSERS:
        return {
            "allowed": True,
            "type": "developer",
            "days_left": None,
            "expires": "ilimitada",
            "name": "Marco Araos"
        }

    academy = read_csv(ACADEMY_CSV)
    premium = read_csv(PREMIUM_CSV)
    users = read_csv(USERS_CSV)

    if not academy.empty and "email" in academy.columns:
        match = academy[academy["email"].astype(str).str.lower() == email]
        if len(match):
            row = match.iloc[0]
            return {
                "allowed": True,
                "type": "academy",
                "days_left": None,
                "expires": str(row.get("vigencia", "2099-12-31")),
                "name": row.get("nombre", email)
            }

    if not premium.empty and "email" in premium.columns:
        match = premium[premium["email"].astype(str).str.lower() == email]
        if len(match) and str(match.iloc[0].get("estado", "")).lower() == "active":
            return {
                "allowed": True,
                "type": "premium",
                "days_left": None,
                "expires": "activa",
                "name": match.iloc[0].get("nombre", email)
            }

    if users.empty or "email" not in users.columns or email not in users["email"].astype(str).str.lower().values:
        end = now + timedelta(days=TRIAL_DAYS)

        new_user = pd.DataFrame([{
            "email": email,
            "first_login": now.isoformat(timespec="seconds"),
            "last_login": now.isoformat(timespec="seconds"),
            "license_type": "trial",
            "trial_start": now.isoformat(timespec="seconds"),
            "trial_end": end.isoformat(timespec="seconds")
        }])

        pd.concat([users, new_user], ignore_index=True).to_csv(USERS_CSV, index=False)

        return {
            "allowed": True,
            "type": "trial",
            "days_left": TRIAL_DAYS,
            "expires": end.strftime("%d/%m/%Y"),
            "name": email
        }

    idx = users[users["email"].astype(str).str.lower() == email].index[0]
    users.loc[idx, "last_login"] = now.isoformat(timespec="seconds")
    users.to_csv(USERS_CSV, index=False)

    try:
        end = datetime.fromisoformat(str(users.loc[idx, "trial_end"]))
    except Exception:
        end = now - timedelta(days=1)

    if now <= end:
        return {
            "allowed": True,
            "type": "trial",
            "days_left": max(0, (end.date() - now.date()).days + 1),
            "expires": end.strftime("%d/%m/%Y"),
            "name": email
        }

    return {
        "allowed": False,
        "type": "expired",
        "days_left": 0,
        "expires": end.strftime("%d/%m/%Y"),
        "name": email
    }


# =========================================================
# SIDEBAR Y PORTADA
# =========================================================

def sidebar(license_info=None):
    logo = ensure_sonara_logo()

    if logo.exists():
        import base64
        _side_logo_b64 = base64.b64encode(logo.read_bytes()).decode("ascii")
        st.sidebar.markdown(
            f"<div style='text-align:center;margin:2px 0 18px 0;'>"
            f"<img src='data:image/png;base64,{_side_logo_b64}' style='width:165px;max-width:165px;border-radius:16px;'>"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown("## SONARA")

    if "page" not in st.session_state:
        st.session_state.page = "Proyecto"

    menu_items = [
        ("🏠", "Inicio"),
        ("📁", "Proyecto"),
        ("🧱", "Biblioteca de materiales"),
        ("📐", "Calculadora libre"),
        ("⚙️", "Configuración"),
        ("❓", "Ayuda"),
    ]


    for icon, label in menu_items:
        if st.sidebar.button(f"{icon}   {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.page = label
            st.rerun()

    if license_info:
        if st.sidebar.button("🚪   Cerrar sesión", key="nav_logout", use_container_width=True):
            for k in ["email", "license_info"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()


    if license_info:
        t = license_info["type"]

        if t == "trial":
            html = f"""
            <div class='sidebar-license-card'>
                <div class='sidebar-title'>Estado de licencia</div>
                <div class='sidebar-badge'>◷ TRIAL</div>
                <div class='sidebar-small'>Prueba gratuita activa</div>
                <div class='sidebar-days'>{license_info['days_left']} días restantes</div>
                <div style='height:8px;background:#172536;border-radius:10px;margin:10px 0;'>
                    <div style='height:8px;width:60%;background:#0A84FF;border-radius:10px;'></div>
                </div>
                <div class='sidebar-small'>Expira el {license_info['expires']}</div>
            </div>
            """
        elif t == "developer":
            html = """
            <div class='sidebar-license-card'>
                <div class='sidebar-title'>Estado de licencia</div>
                <div class='sidebar-badge'>👨‍💻 DEVELOPER</div>
                <div class='sidebar-small'>Marco Araos</div>
                <div class='sidebar-days'>Ilimitada</div>
                <div class='sidebar-small'>Todas las funciones habilitadas</div>
            </div>
            """
        elif t == "academy":
            html = f"""
            <div class='sidebar-license-card'>
                <div class='sidebar-title'>Estado de licencia</div>
                <div class='sidebar-badge'>🎓 ACADEMY</div>
                <div class='sidebar-small'>Alumno autorizado</div>
                <div class='sidebar-days'>Activa</div>
                <div class='sidebar-small'>Vigencia: {license_info['expires']}</div>
            </div>
            """
        elif t == "premium":
            html = """
            <div class='sidebar-license-card'>
                <div class='sidebar-title'>Estado de licencia</div>
                <div class='sidebar-badge'>★ PREMIUM</div>
                <div class='sidebar-small'>Suscripción profesional</div>
                <div class='sidebar-days'>Activa</div>
                <div class='sidebar-small'>USD 15/mes</div>
            </div>
            """
        else:
            html = """
            <div class='sidebar-license-card'>
                <div class='sidebar-title'>Estado de licencia</div>
                <div class='sidebar-badge'>EXPIRADO</div>
                <div class='sidebar-small'>Activa Premium para continuar</div>
            </div>
            """

        st.sidebar.markdown(html, unsafe_allow_html=True)

    st.sidebar.markdown(
        f"<div class='sidebar-small' style='margin-top:20px;'>© 2026 SONARA<br>Versión {APP_VERSION}</div>",
        unsafe_allow_html=True
    )

    return st.session_state.page


def hero():
    st.markdown(
        "<div class='top-links'><span>✉ Contacto</span><span>ⓘ Ayuda</span></div>",
        unsafe_allow_html=True
    )

    logo = ensure_sonara_logo()

    st.markdown("<div class='hero-wrap'>", unsafe_allow_html=True)

    if logo.exists():
        import base64
        _logo_b64 = base64.b64encode(logo.read_bytes()).decode("ascii")
        st.markdown(
            f"<div class='hero-logo-wrap'><img src='data:image/png;base64,{_logo_b64}'></div>",
            unsafe_allow_html=True
        )

    st.markdown("""
        <div class='hero-title'>SONARA</div>
        <div class='hero-kicker'>ACOUSTIC DESIGN ASSISTANT</div>
        <div class='hero-line'></div>
        <div class='hero-main'>Asistente de diseño acústico para especialistas y no especialistas</div>
        <div class='hero-sub'>
            Analiza soluciones constructivas, diseña alternativas, optimiza desempeño/costo y verifica cumplimiento con criterios normativos o referenciales.
        </div>
        <div class='hero-tags'>ANALIZA · DISEÑA · OPTIMIZA · CUMPLE</div>
    </div>
    """, unsafe_allow_html=True)


def login_page():
    hero()

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([0.95, 1.25], gap="large")

    with col1:
        st.markdown(
            "<div class='card'><div class='card-title'>ACCESO SONARA</div>"
            "<div class='card-text'>Ingresa con correo y contraseña para acceder a tus proyectos.</div>",
            unsafe_allow_html=True
        )

        auth_mode = st.radio("Modo", ["Ingresar", "Crear cuenta"], horizontal=True, key="auth_mode")

        email = st.text_input("Correo electrónico", placeholder="tu@email.com", key="auth_email")
        password = st.text_input("Contraseña", type="password", key="auth_password")

        if auth_mode == "Crear cuenta":
            nombre = st.text_input("Nombre profesional", key="reg_nombre")
            empresa = st.text_input("Empresa / institución", key="reg_empresa")
            cargo = st.text_input("Cargo", key="reg_cargo")
            password2 = st.text_input("Repetir contraseña", type="password", key="auth_password2")

            if st.button("Crear cuenta trial", use_container_width=True):
                e = norm(email)
                if not e or "@" not in e:
                    st.error("Ingresa un correo válido.")
                elif len(password) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                elif password != password2:
                    st.error("Las contraseñas no coinciden.")
                else:
                    ok, msg = ensure_user_record(e, password, nombre, empresa, cargo)
                    if ok:
                        st.session_state.email = e
                        st.session_state.license_info = get_license(e)
                        st.success("Cuenta creada. Accediendo...")
                        st.rerun()
                    else:
                        st.error(msg)

        else:
            if st.button("↪ Ingresar", use_container_width=True):
                e = norm(email)
                if not e or "@" not in e:
                    st.error("Ingresa un correo válido.")
                elif not password:
                    st.error("Ingresa tu contraseña.")
                else:
                    ok, msg = authenticate_user(e, password)
                    if ok:
                        st.session_state.email = e
                        st.session_state.license_info = get_license(e)
                        st.success("Acceso correcto.")
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown(
            "<div class='card-text' style='margin-top:16px;'>🔒 Las contraseñas se guardan con hash PBKDF2, no como texto plano.</div></div>",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("""
        <div class='card'>
            <div class='card-title'>SONARA VERSIÓN BETA</div>
            <div class='card-text'>
                Plataforma de diseño acústico por proyecto para especialistas, arquitectos y equipos técnicos.
            </div>
            <div style='margin-top:18px;'>
                <div class='card-text'>● Proyectos con recintos y matriz acústica</div>
                <div class='card-text'>● Calculadora integrada por requerimiento</div>
                <div class='card-text'>● Soluciones compuestas: tabique + ventana + puerta</div>
                <div class='card-text'>● Optimización IA, costos, cubicación e informe preliminar</div>
                <div class='card-text'>● Biblioteca normativa y materiales editables</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    SHOW_LICENSE_CARDS = False
    
    if SHOW_LICENSE_CARDS:
        st.markdown("<br>", unsafe_allow_html=True)
    
        p1, p2, p3 = st.columns(3, gap="large")
    
        p1.markdown("""
        <div class='plan'>
            <div class='plan-title'>TRIAL</div>
            <div class='plan-price'>3 días</div>
            <div class='plan-text'>Acceso completo para evaluar SONARA.</div>
        </div>
        """, unsafe_allow_html=True)
    
        p2.markdown("""
        <div class='plan academy'>
            <div class='plan-title academy'>ACADEMY</div>
            <div class='plan-price'>Docencia</div>
            <div class='plan-text'>Licencias para cursos, diplomados y talleres.</div>
        </div>
        """, unsafe_allow_html=True)
    
        p3.markdown("""
        <div class='plan premium'>
            <div class='plan-title premium'>PREMIUM</div>
            <div class='plan-price'>USD 15/mes</div>
            <div class='plan-text'>Uso profesional con proyectos e informes.</div>
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# MATERIALES
# =========================================================


def default_materials_dataframe():
    """
    Base de materiales original AKUZOFT/WALLS + campos de cubicación/costos.
    Se guarda en data/materiales_sonara.csv para edición desde SONARA.
    """

    nombres = [
        "Placa de yeso-cartón estándar",
        "Placa de yeso-cartón alta densidad",
        "Hormigón armado",
        "Albañilería / bloque pesado",
        "Acero",
        "Aluminio",
        "Plomo",
        "Cobre",
        "Madera pesada",
        "Madera liviana",
        "Vidrio monolítico",
        "Vidrio pesado",
        "Fibrocemento",
        "OSB / tablero madera",
        "Tablero liviano",
        "Tablero de madera",
        "Tablero yeso-madera",
        "Tablero compuesto",
        "Tablero liviano HD",
        "Tablero liviano MD",
        "Mármol / piedra delgada",
        "Vidrio float",
        "Vidrio laminado / compuesto",
        "Lana mineral 40 kg/m³",
        "Lana mineral 60 kg/m³",
        "Lana mineral 80 kg/m³",
        "Montante 60",
        "Montante 90",
        "Solera",
        "Tornillos",
        "Sellos / cinta / masilla",
        "Mano de obra referencial",
    ]

    # espesor_mm, densidad_kg_m3, modulo_young_Pa, eta
    datos = [
        [15, 735, 2550000000, 0.033],
        [15, 786, 2980000000, 0.052],
        [150, 2340, 11000000000, 0.006],
        [110, 1600, 8901000000, 0.003],
        [1, 6976, 157000000000, 0.033],
        [3, 2900, 85220000000, 0.010],
        [1, 11000, 15300000000, 0.050],
        [1, 8960, 140100000000, 0.010],
        [1.84, 1900, 265000000, 0.030],
        [4, 920, 30000000, 0.010],
        [10, 2200, 70000000000, 0.005],
        [20, 2600, 50000000000, 0.005],
        [8, 1327, 8320000000, 0.028],
        [2.4, 971, 3560000000, 0.058],
        [18, 619, 3060000000, 0.045],
        [18, 686, 3590000000, 0.040],
        [12, 635, 2980000000, 0.038],
        [11.1, 623, 4680000000, 0.030],
        [9, 545, 8230000000, 0.024],
        [12, 488, 5150000000, 0.024],
        [3.8, 1997, 31200000000, 0.012],
        [6, 2522, 66800000000, 0.014],
        [6, 2500, 50720000000, 0.060],
        [50, 40, 0, 0],
        [50, 60, 0, 0],
        [50, 80, 0, 0],
        [60, 0, 0, 0],
        [90, 0, 0, 0],
        [90, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]

    colores = [
        "#9CA3AF", "#B0B7C3", "#6B7280", "#9B5B3A",
        "#8E99A8", "#AAB7C7", "#5E6470", "#B87333",
        "#8B5A2B", "#A06A35", "#5DADE2", "#4FA3D1",
        "#7F8791", "#A06A35", "#C2A36B", "#B68A4C",
        "#B0B7C3", "#9CA3AF", "#A06A35", "#B68A4C",
        "#D6D3C4", "#5DADE2", "#6EC6FF",
        "#FACC15", "#FBBF24", "#F59E0B",
        "#94A3B8", "#64748B", "#475569",
        "#CBD5E1", "#60A5FA", "#22C55E",
    ]

    precios = {
        "Placa de yeso-cartón estándar": 4500,
        "Placa de yeso-cartón alta densidad": 6200,
        "Fibrocemento": 8500,
        "OSB / tablero madera": 7500,
        "Tablero liviano": 6500,
        "Tablero de madera": 7200,
        "Tablero yeso-madera": 7000,
        "Tablero compuesto": 9000,
        "Lana mineral 40 kg/m³": 5200,
        "Lana mineral 60 kg/m³": 6500,
        "Lana mineral 80 kg/m³": 8500,
        "Montante 60": 1400,
        "Montante 90": 1900,
        "Solera": 1300,
        "Tornillos": 18,
        "Sellos / cinta / masilla": 900,
        "Mano de obra referencial": 8500,
    }

    rows = []

    for nombre, fila, color in zip(nombres, datos, colores):
        espesor, densidad, young, eta = fila
        nlow = nombre.lower()

        if "vidrio" in nlow:
            tipo, grupo, unidad = "vidrio", "vidrio", "m²"
        elif "lana mineral" in nlow:
            tipo, grupo, unidad = "absorbente", "absorbente", "m²"
        elif "montante" in nlow or "solera" in nlow:
            tipo, grupo, unidad = "estructura", "estructura", "ml"
        elif "tornillo" in nlow:
            tipo, grupo, unidad = "fijacion", "fijacion", "un"
        elif "mano de obra" in nlow:
            tipo, grupo, unidad = "mano_obra", "mano_obra", "m²"
        elif "sellos" in nlow or "masilla" in nlow:
            tipo, grupo, unidad = "sello", "sello", "m²"
        else:
            tipo, grupo, unidad = "placa", "panel", "m²"

        rows.append({
            "nombre": nombre,
            "tipo": tipo,
            "grupo": grupo,
            "espesor": float(espesor),
            "dens": float(densidad),
            "E": float(young),
            "eta": float(eta),
            "color": color,
            "unidad": unidad,
            "precio": float(precios.get(nombre, 0)),
            "proveedor": "Personalizado",
            "activo": True,
        })

    return pd.DataFrame(rows)


def ensure_materials_file():
    DATA_DIR.mkdir(exist_ok=True)

    if not MATERIALS_CSV.exists():
        default_materials_dataframe().to_csv(MATERIALS_CSV, index=False, encoding="utf-8")

    try:
        df = pd.read_csv(MATERIALS_CSV)
    except Exception:
        df = default_materials_dataframe()
        df.to_csv(MATERIALS_CSV, index=False, encoding="utf-8")

    required = default_materials_dataframe().columns.tolist()
    changed = False

    for col in required:
        if col not in df.columns:
            df[col] = default_materials_dataframe()[col] if col in default_materials_dataframe().columns else ""
            changed = True

    if changed:
        df.to_csv(MATERIALS_CSV, index=False, encoding="utf-8")

    return df


def material_db():
    """
    Lee la biblioteca editable data/materiales_sonara.csv.
    La calculadora usa parámetros acústicos; cubicación/optimizador usan unidad y precio.
    """

    df = ensure_materials_file()

    if "activo" in df.columns:
        mask_active = df["activo"].astype(str).str.lower().isin(["true", "1", "sí", "si", "yes"])
        df = df[mask_active].copy()

    materiales = {}

    for _, row in df.iterrows():
        nombre = str(row.get("nombre", "")).strip()

        if not nombre:
            continue

        def fnum(col, default=0.0):
            try:
                val = row.get(col, default)
                if pd.isna(val):
                    return float(default)
                return float(val)
            except Exception:
                return float(default)

        materiales[nombre] = {
            "nombre": nombre,
            "tipo": str(row.get("tipo", "placa")),
            "grupo": str(row.get("grupo", "panel")),
            "espesor": fnum("espesor", 0.0),
            "dens": fnum("dens", 0.0),
            "E": fnum("E", 0.0),
            "eta": fnum("eta", 0.0),
            "color": str(row.get("color", "#9CA3AF")),
            "unidad": str(row.get("unidad", "m²")),
            "precio": fnum("precio", 0.0),
            "proveedor": str(row.get("proveedor", "Personalizado")),
            "activo": row.get("activo", True),
        }

    return materiales



# =========================================================
# MOTOR WALLS / AKUZOFT
# =========================================================

def _integral_walls_tl_from_m_b_eta(m, B, eta, freqs):
    """Integral angular original WALLS usando m, B y eta."""
    rho_air = 1.18
    c = 343.0

    theta = np.linspace(0.0, (4.0 / 9.0) * np.pi, 720)
    sin_t = np.sin(theta)
    cos_t = np.cos(theta)

    values = []

    for f in np.asarray(freqs, dtype=float):
        omega = 2.0 * np.pi * f
        a = (omega * m * cos_t) / (2.0 * rho_air * c)
        b = ((omega**2) * B * (sin_t**4)) / (m * c**4)

        denominator = (1.0 + eta * a * b) ** 2 + (a * (1.0 - b)) ** 2
        integrand = (1.0 / denominator) * cos_t * sin_t

        Q = float(np.trapezoid(integrand, theta))
        tau = max(Q * 2.0904, 1e-12)
        values.append(10.0 * np.log10(1.0 / tau))

    return np.asarray(values)


def layer_properties(material, espesor_mm, densidad_override=None):
    h = max(float(espesor_mm) * 1e-3, 1e-6)
    rho = float(densidad_override) if densidad_override else float(material["dens"])
    E = float(material["E"])
    eta = float(material["eta"])

    m = rho * h
    B = E * h**3 / 12.0
    fc = (343.0**2 / (2.0 * np.pi)) * np.sqrt(m / B)
    return m, B, eta, fc


def combine_layers(layers):
    """
    Combina capas adheridas según la lógica original WALLS:
    MT = suma(M_i), BT = suma(B_i), NT = suma(eta_i)
    """
    masses, rigidities, etas, fcs = [], [], [], []

    for layer in layers:
        m, B, eta, fc = layer_properties(
            layer["material"],
            layer["espesor"],
            layer.get("densidad")
        )
        masses.append(m)
        rigidities.append(B)
        etas.append(eta)
        fcs.append(fc)

    mt = float(np.sum(masses))
    bt = float(np.sum(rigidities))
    etat = float(np.sum(etas))
    fc_min = float(np.min(fcs)) if fcs else 0.0
    fc_eq = (343.0**2 / (2.0 * np.pi)) * np.sqrt(mt / bt) if bt > 0 else fc_min

    return mt, bt, etat, fc_min, fc_eq


def walls_multilayer_tl(layers, freqs):
    """Panel simple multicapa adherido, equivalente WALLS."""
    mt, bt, etat, fc_min, fc_eq = combine_layers(layers)
    tl = _integral_walls_tl_from_m_b_eta(mt, bt, etat, freqs)
    return tl, mt, bt, etat, fc_eq


def walls_panel_tl(material, espesor_mm, freqs, densidad_override=None):
    """Compatibilidad con el motor anterior: una capa."""
    layer = {
        "material": material,
        "espesor": espesor_mm,
        "densidad": densidad_override,
    }
    return walls_multilayer_tl([layer], freqs)


def walls_panel_equivalent_tl(m, B, eta, freqs):
    return _integral_walls_tl_from_m_b_eta(m, B, eta, freqs)


def absorbent_gain(absorbente_tipo):
    ganancias = {
        "Sin absorbente": 0.0,
        "Lana mineral 40 kg/m³": 1.5,
        "Lana mineral 60 kg/m³": 3.0,
        "Lana mineral 80 kg/m³": 4.5,
    }
    return ganancias.get(absorbente_tipo, 0.0)


def walls_double_multilayer_tl(
    layers_left,
    layers_right,
    camara_mm,
    freqs,
    configuracion="Montante simple",
    absorbente_tipo="Sin absorbente",
    distancia_fijaciones_mm=600.0,
):
    """
    Panel doble multicapa por lado.

    Configuración estructural en lenguaje de construcción:
    - Montante simple: unión mecánica más rígida.
    - Montantes independientes: mayor desacople.
    - Doble estructura: máximo desacople.

    Base WALLS:
    f0 = (1/(2*pi))*sqrt(rho_air*c^2)*sqrt((m1+m2)/(m1*m2*d))
    fl = c/(2*pi*d)
    """
    rho_air = 1.18
    c = 343.0
    d = max(float(camara_mm) * 1e-3, 1e-4)

    tl1, m1, B1, eta1, fc1 = walls_multilayer_tl(layers_left, freqs)
    tl2, m2, B2, eta2, fc2 = walls_multilayer_tl(layers_right, freqs)

    mt = m1 + m2
    bt = B1 + B2
    etat = eta1 + eta2

    f0 = (1.0 / (2.0 * np.pi)) * np.sqrt(rho_air * c**2) * np.sqrt((m1 + m2) / (m1 * m2 * d))
    fl = c / (2.0 * np.pi * d)

    tl_low = walls_panel_equivalent_tl(mt, bt, etat, freqs)
    gain_abs = absorbent_gain(absorbente_tipo)

    # Factores iniciales por configuración constructiva.
    # Se calibrarán con el r2/r3 original y/o ensayos.
    config_gain = {
        "Montante simple": -2.0,
        "Montantes independientes": 1.5,
        "Doble estructura": 3.0,
    }.get(configuracion, 0.0)

    # Efecto de fijaciones más próximas en montante simple.
    b = max(float(distancia_fijaciones_mm) * 1e-3, 0.1)
    fijacion_penalty = 0.0
    if configuracion == "Montante simple":
        fijacion_penalty = -max(0.0, 600.0 - distancia_fijaciones_mm) / 300.0

    tld = np.zeros_like(np.asarray(freqs, dtype=float))

    for i, f in enumerate(freqs):
        if f < f0:
            tld[i] = tl_low[i]
        elif f < fl:
            tld[i] = tl1[i] + tl2[i] + 20.0 * np.log10(max(f * d, 1e-12)) - 29.0
            tld[i] += gain_abs
        else:
            tld[i] = tl1[i] + tl2[i] + 6.0
            tld[i] += gain_abs * 0.35

        tld[i] += config_gain + fijacion_penalty

    return tld, mt, min(fc1, fc2), f0, fl


def walls_double_panel_tl(mat1, esp1_mm, mat2, esp2_mm, camara_mm, freqs, absorbente=True):
    """Compatibilidad con llamadas antiguas."""
    layers_left = [{"material": mat1, "espesor": esp1_mm}]
    layers_right = [{"material": mat2, "espesor": esp2_mm}]
    abs_tipo = "Lana mineral 60 kg/m³" if absorbente else "Sin absorbente"
    return walls_double_multilayer_tl(
        layers_left, layers_right, camara_mm, freqs,
        configuracion="Montante simple",
        absorbente_tipo=abs_tipo,
        distancia_fijaciones_mm=600.0,
    )



def walls_window_tl(mat1, esp1_mm, mat2, esp2_mm, camara_mm, freqs):
    """
    Motor de ventana / DVH basado en la rama r3 de WALLS.

    WALLS r3:
    FR = (1/(2*pi))*sqrt(rho_air*c^2)*sqrt((m1+m2)/(m1*m2*CA))
    F1 = c/(2*CA)

    Si f < FR:
        TLD = TLA, con TLA = panel equivalente.
    Si f >= FR:
        TLB = TL1 + TL2 - 10 + 10log10(CA) + 3.76 + 3
        TLD = max(TLA, TLB)

    Nota: CA está en metros, tal como en WALLS.
    """

    rho_air = 1.18
    c = 343.0

    ca = max(float(camara_mm) * 1e-3, 1e-4)

    tl1, m1, B1, eta1, fc1 = walls_panel_tl(mat1, esp1_mm, freqs)
    tl2, m2, B2, eta2, fc2 = walls_panel_tl(mat2, esp2_mm, freqs)

    mt = m1 + m2
    bt = B1 + B2
    etat = eta1 + eta2

    fr = (
        (1.0 / (2.0 * np.pi))
        * np.sqrt(rho_air * c**2)
        * np.sqrt((m1 + m2) / (m1 * m2 * ca))
    )

    f1 = c / (2.0 * ca)

    tla = walls_panel_equivalent_tl(mt, bt, etat, freqs)

    tld = np.zeros_like(np.asarray(freqs, dtype=float))

    for i, f in enumerate(freqs):
        if f < fr:
            tld[i] = tla[i]
        else:
            tlb = (
                tl1[i]
                + tl2[i]
                - 10.0
                + 10.0 * np.log10(ca)
                + 3.76
                + 3.0
            )
            tld[i] = max(tla[i], tlb)

    return tld, mt, min(fc1, fc2), fr, f1


def dvh_tl(vidrio_ext, esp_ext_mm, vidrio_int, esp_int_mm, camara_mm, freqs):
    """
    Compatibilidad: DVH usa el motor de ventana r3 de WALLS.
    """
    return walls_window_tl(
        vidrio_ext,
        esp_ext_mm,
        vidrio_int,
        esp_int_mm,
        camara_mm,
        freqs,
    )


def third_octave_from_fine(f_fine, tl_fine, bands=None):
    """Filtro de tercios como Panel1.m / Panel2.m / PARED.m."""
    if bands is None:
        bands = np.array([
            50, 63, 80, 100, 125, 160, 200, 250, 315,
            400, 500, 630, 800, 1000, 1250, 1600,
            2000, 2500, 3150, 4000, 5000,
        ])

    f_fine = np.asarray(f_fine, dtype=float)
    tl_fine = np.asarray(tl_fine, dtype=float)
    tl_bands = []

    for band in bands:
        fu = band / (2 ** (1 / 6))
        fo = fu * (2 ** (1 / 3))
        idx = (f_fine <= fo) & (f_fine > fu)

        if not np.any(idx):
            tl_bands.append(float(np.interp(band, f_fine, tl_fine)))
        else:
            tl_bands.append(float(10 * np.log10(np.mean(10 ** (tl_fine[idx] / 10)))))

    return bands, np.asarray(tl_bands)



def iso717_rw_simple(freqs, tl, return_curve=False):
    """
    Cálculo Rw, C y Ctr portado desde Panel1/Panel2/PARED.

    Si return_curve=True, retorna además la curva ISO 717 desplazada
    para mostrarla en el gráfico.
    """

    freqs = np.asarray(freqs, dtype=float)
    tl = np.asarray(tl, dtype=float)

    rw_freqs = np.array([
        100, 125, 160, 200, 250, 315, 400, 500,
        630, 800, 1000, 1250, 1600, 2000, 2500, 3150
    ])

    tl_rw = np.interp(rw_freqs, freqs, tl)

    ref_base = np.array([
        51, 54, 57, 60, 63, 66, 69, 70,
        71, 72, 73, 74, 74, 74, 74, 74
    ], dtype=float)

    ref = ref_base.copy()
    ref_shifted = ref.copy()
    rw = int(ref[7])

    for _ in range(52):
        desv = ref - tl_rw
        suma = np.sum(desv[desv > 0])

        if suma < 32:
            rw = int(round(ref[7]))
            ref_shifted = ref.copy()
            break

        ref = ref - 1

    c_ref = np.array([
        -29, -26, -23, -21, -19, -17, -15, -13,
        -12, -11, -10, -9, -9, -9, -9, -9
    ], dtype=float)

    ctr_ref = np.array([
        -20, -20, -18, -16, -15, -14, -13, -12,
        -11, -9, -8, -9, -10, -11, -13, -15
    ], dtype=float)

    c_val = -10 * np.log10(np.sum(10 ** ((c_ref - tl_rw) / 10)))
    ctr_val = -10 * np.log10(np.sum(10 ** ((ctr_ref - tl_rw) / 10)))

    c = int(round(c_val - rw))
    ctr = int(round(ctr_val - rw))

    if return_curve:
        return rw, c, ctr, rw_freqs, ref_shifted, tl_rw

    return rw, c, ctr


def octave_bands_from_third(freqs, values):
    """Agrupación 1/3 a octava por promedio energético."""
    octave_freqs = np.array([63, 125, 250, 500, 1000, 2000, 4000])
    grouped = []

    for fc in octave_freqs:
        low = fc / np.sqrt(2)
        high = fc * np.sqrt(2)
        mask = (freqs >= low) & (freqs <= high)

        if not np.any(mask):
            grouped.append(float(np.interp(fc, freqs, values)))
        else:
            grouped.append(float(10 * np.log10(np.mean(10 ** (values[mask] / 10)))))

    return octave_freqs, np.asarray(grouped)



def diagnostic_note(tipo, rw, c, ctr, fc, masa, extra=None):
    """
    Nota técnica referencial para transparentar sensibilidad del cálculo.
    """

    mensajes = []

    if fc < 1500:
        mensajes.append("Fc baja: posible zona crítica dentro del rango de uso")
    elif fc < 4000:
        mensajes.append("Fc media: revisar coincidencia en medias-altas frecuencias")
    else:
        mensajes.append("Fc alta: coincidencia desplazada hacia altas frecuencias")

    if masa < 15:
        mensajes.append("Elemento liviano: alta sensibilidad a montaje y uniones")
    elif masa < 40:
        mensajes.append("Elemento semipesado: revisar cámara, absorbente y fijaciones")
    else:
        mensajes.append("Elemento pesado: domina masa superficial y rigidez")

    if tipo == "Ventana":
        mensajes.append("En ventanas/DVH el sellado perimetral puede dominar el resultado real")

    if tipo == "Panel doble":
        mensajes.append("En paneles dobles la transmisión por montantes puede reducir el aislamiento real")

    if extra:
        mensajes.append(extra)

    return " · ".join(mensajes)



# =========================================================
# VISUAL CONSTRUCTIVO MULTICAPA
# =========================================================

def layer_html(label, width_px, color, extra_class=""):
    width_px = max(22, min(width_px, 145))
    return (
        f"<div class='layer-box {extra_class}' "
        f"style='width:{width_px}px;background:{color};'>{label}</div>"
    )


def layers_html(layers):
    html = ""
    for layer in layers:
        material = layer["material"]
        nombre = layer["nombre"]
        esp = layer["espesor"]
        color = material.get("color", "#9CA3AF")
        short = nombre.replace("Placa de ", "").replace(" / ", "<br>")
        html += layer_html(f"{short}<br>{esp:.1f} mm", esp * 3, color)
    return html


def structural_visual(
    tipo,
    mat1=None,
    esp1=None,
    mat2=None,
    esp2=None,
    camara=None,
    absorbente=False,
    layers_left=None,
    layers_right=None,
    configuracion=None,
    tipo_ventana=None,
    absorbente_tipo="Sin absorbente",
):
    html = "<div class='sonara-card'><div class='sonara-card-title'>Visual constructivo</div>"
    html += "<div style='display:flex;align-items:center;justify-content:center;min-height:230px;padding:12px;'>"

    if tipo == "Panel simple":
        html += layers_html(layers_left or [])

    elif tipo == "Panel doble":
        html += layers_html(layers_left or [])

        if configuracion == "Montante simple":
            html += layer_html("Montante<br>simple", 28, "#8E99A8")
        elif configuracion == "Montantes independientes":
            html += layer_html("Montante", 25, "#8E99A8")

        if absorbente_tipo != "Sin absorbente":
            html += layer_html(f"Lana<br>{camara:.0f} mm", camara * 1.3, "rgba(180,143,40,.35)", "wool-lines")
        else:
            html += layer_html(f"Aire<br>{camara:.0f} mm", camara * 1.3, "rgba(34,154,255,.06)", "air-box")

        if configuracion in ["Montantes independientes", "Doble estructura"]:
            html += layer_html("Montante", 25, "#8E99A8")

        html += layers_html(layers_right or [])

    else:
        if tipo_ventana == "DVH":
            html += layers_html(layers_left or [])
            html += layer_html(f"Aire<br>{camara:.0f} mm", camara * 1.6, "rgba(34,154,255,.08)", "air-box")
            html += layers_html(layers_right or [])
        else:
            html += layers_html(layers_left or [])

    html += "</div>"

    if tipo == "Panel doble":
        nota = f"Configuración: {configuracion}. Absorbente: {absorbente_tipo}."
    elif tipo == "Ventana":
        nota = f"Tipo de ventana: {tipo_ventana}."
    else:
        nota = "Panel simple multicapa: capas adheridas calculadas como elemento equivalente WALLS."

    html += f"<div class='result-note'>{nota}</div>"
    html += "</div>"
    return html


# =========================================================
# INPUTS MULTICAPA
# =========================================================

def layer_inputs(prefix, titulo, materiales, mats, default_count=1, max_layers=5):
    st.markdown(f"<div style='font-weight:900;color:#8FD0FF;margin-top:12px;margin-bottom:8px;'>{titulo}</div>", unsafe_allow_html=True)

    n_layers = st.number_input(
        f"Número de capas - {titulo}",
        min_value=1,
        max_value=max_layers,
        value=default_count,
        step=1,
        key=f"{prefix}_n_layers",
    )

    layers = []

    for i in range(int(n_layers)):
        mat_name = st.selectbox(
            f"Capa {i+1} - Material",
            materiales,
            index=0,
            key=f"{prefix}_mat_{i}",
        )

        esp = st.number_input(
            f"Capa {i+1} - Espesor [mm]",
            value=float(mats[mat_name]["espesor"]),
            min_value=0.1,
            step=0.1,
            key=f"{prefix}_esp_{i}",
        )

        layers.append({
            "nombre": mat_name,
            "material": mats[mat_name],
            "espesor": float(esp),
        })

    return layers


# =========================================================
# CALCULADORA FASE 2
# =========================================================


# =========================================================
# DESCRIPTORES DE EVALUACIÓN
# =========================================================

def stc_estimate_from_curve(third_freqs, tl_third, rw):
    """
    Estimación preliminar STC desde la curva 1/3 octava.
    STC usa ASTM E413 y no es idéntico a ISO 717-1.
    Para SONARA v1.1 se informa como estimación conservadora a partir de la curva calculada.
    """
    try:
        freqs = np.asarray(third_freqs, dtype=float)
        vals = np.asarray(tl_third, dtype=float)
        mask = (freqs >= 125) & (freqs <= 4000)
        if mask.sum() < 10:
            return int(round(rw))
        # Aproximación simple: limita el valor por el promedio en bandas medias y por Rw.
        mid = vals[mask]
        approx = min(float(rw), float(np.percentile(mid, 35)) + 2.0)
        return int(round(max(0, approx)))
    except Exception:
        return int(round(rw))


def airborne_descriptor_options():
    return [
        "ISO 717-1 · Rw",
        "ISO 717-1 · Rw + C",
        "ISO 717-1 · Rw + Ctr",
        "ANSI/ASTM · STC estimado",
        "ISO 16283/12354 · DnT,w estimado",
        "ISO 16283/12354 · DnT,A estimado",
        "ISO 16283/12354 · DnT,Atr estimado",
    ]


def descriptor_key(label):
    label = str(label)
    if "Rw + Ctr" in label:
        return "rw_ctr"
    if "Rw + C" in label:
        return "rw_c"
    if "STC" in label:
        return "stc"
    if "DnT,Atr" in label:
        return "dnt_atr"
    if "DnT,A" in label:
        return "dnt_a"
    if "DnT,w" in label:
        return "dntw"
    return "rw"


def descriptor_public_name(key):
    return {
        "rw": "Rw",
        "rw_c": "Rw + C",
        "rw_ctr": "Rw + Ctr",
        "stc": "STC estimado",
        "dntw": "DnT,w estimado",
        "dnt_a": "DnT,A estimado",
        "dnt_atr": "DnT,Atr estimado",
    }.get(str(key), str(key))


def calculate_airborne_descriptors(rw, c, ctr, stc, area_sep=10.0, vol_rec=35.0, t_rec=0.5):
    """
    Calcula/estima descriptores derivados de ruido aéreo.
    Rw/Rw+C/Rw+Ctr: desde ISO 717-1.
    STC: estimación ASTM.
    DnT: estimación preliminar desde R + 10log(V/(T*S)) usando T0=0.5 s.
    """
    rw = float(rw)
    c = float(c)
    ctr = float(ctr)
    stc = float(stc)
    area_sep = max(float(area_sep or 10.0), 0.1)
    vol_rec = max(float(vol_rec or 35.0), 0.1)
    t_rec = max(float(t_rec or 0.5), 0.1)

    dnt_correction = 10.0 * np.log10(vol_rec / (t_rec * area_sep))
    dntw = rw + dnt_correction

    return {
        "rw": rw,
        "c": c,
        "ctr": ctr,
        "rw_c": rw + c,
        "rw_ctr": rw + ctr,
        "stc": stc,
        "dntw": dntw,
        "dnt_a": dntw + c,
        "dnt_atr": dntw + ctr,
        "dnt_correction": dnt_correction,
        "area_sep": area_sep,
        "vol_rec": vol_rec,
        "t_rec": t_rec,
    }


def solution_descriptor_value(solution, indicador):
    """
    Obtiene desde una solución el valor que corresponde al descriptor normativo.
    """
    if not solution:
        return None
    ind = str(indicador or "Rw").replace(" ", "").lower()

    mapping = {
        "rw": "rw",
        "r'w": "rw",
        "ra": "rw_c",
        "r'a": "rw_c",
        "rw+c": "rw_c",
        "rw+ctr": "rw_ctr",
        "stc": "stc",
        "astc": "stc",
        "nic": "stc",
        "dnt,w": "dntw",
        "dntw": "dntw",
        "dnt,a": "dnt_a",
        "dnta": "dnt_a",
        "dnt,atr": "dnt_atr",
        "dntatr": "dnt_atr",
        "d2m,nt,w": "dntw",
        "d2mntw": "dntw",
        "d2m,nt,atr": "dnt_atr",
        "d2mntatr": "dnt_atr",
        "l'nt,w": "lntw",
        "lnt,w": "lntw",
        "lntw": "lntw",
        "ln,w": "lnw",
        "lnw": "lnw",
    }

    key = mapping.get(ind)
    if key:
        if key in solution and solution.get(key) is not None:
            return solution.get(key)
        descriptors = solution.get("descriptores", {})
        if isinstance(descriptors, dict) and key in descriptors:
            return descriptors.get(key)

    # fallback
    for k in ["valor", "rw", "dntw", "lntw", "lnw"]:
        if solution.get(k) is not None:
            return solution.get(k)
    return None


def solution_composition_text(sol):
    if not sol:
        return ""
    if sol.get("componentes"):
        return " + ".join([
            f"{c.get('nombre','Componente')} ({c.get('area','-')} m², R {c.get('r','-')} dB)"
            for c in sol.get("componentes", [])
        ])

    parts = []
    left = sol.get("layers_left", []) or []
    right = sol.get("layers_right", []) or []
    if left:
        parts.append("Lado 1: " + " + ".join([x.get("nombre", "") for x in left]))
    if right:
        parts.append("Lado 2: " + " + ".join([x.get("nombre", "") for x in right]))
    if sol.get("camara"):
        parts.append(f"Cámara: {sol.get('camara')} mm")
    if sol.get("absorbente"):
        parts.append(f"Absorbente: {sol.get('absorbente')}")
    if sol.get("configuracion"):
        parts.append(f"Configuración: {sol.get('configuracion')}")
    return " | ".join([p for p in parts if p])


def solution_cubicacion_summary(sol):
    cub = sol.get("cubicacion", {}) if isinstance(sol, dict) else {}
    if not isinstance(cub, dict) or not cub:
        return {"area_neta": "", "area_bruta": "", "area_vanos": "", "total": 0, "tipo": "", "items": ""}
    items = cub.get("items", [])
    items_txt = "; ".join([f"{i.get('Ítem','')}: {i.get('Cantidad','')} {i.get('Unidad','')}" for i in items[:5]]) if isinstance(items, list) else ""
    return {
        "area_neta": cub.get("area_neta", ""),
        "area_bruta": cub.get("area_bruta", ""),
        "area_vanos": cub.get("area_vanos", ""),
        "total": float(cub.get("total", 0) or 0),
        "tipo": cub.get("tipo_cubicacion", ""),
        "items": items_txt,
    }


def app_calculator():
    st.markdown(
        "<h2 style='color:#FFFFFF;margin-bottom:18px;'>Calculadora</h2>",
        unsafe_allow_html=True,
    )

    mats = material_db()

    materiales_panel = [k for k, v in mats.items() if v.get("grupo") == "panel"]
    materiales_vidrio = [k for k, v in mats.items() if v.get("grupo") == "vidrio"]
    materiales_panel_doble = materiales_panel + materiales_vidrio

    col_input, col_visual, col_results = st.columns([0.95, 0.95, 1.25], gap="large")

    with col_input:
        st.markdown("<div class='sonara-card-title'>Entrada del elemento</div>", unsafe_allow_html=True)

        tipo = st.radio(
            "Tipo de elemento",
            ["Panel simple", "Panel doble", "Ventana"],
            horizontal=True,
        )

        banda = st.radio(
            "Resolución de frecuencia",
            ["1/3 de octava", "Octava"],
            horizontal=True,
            key="banda_frecuencia",
        )

        descriptor_label = st.selectbox(
            "Método / descriptor de evaluación",
            airborne_descriptor_options(),
            index=0,
            key="airborne_descriptor_label",
            help="Rw, Rw+C y Rw+Ctr se obtienen desde ISO 717-1. STC y DnT se presentan como estimaciones preliminares."
        )

        descriptor_sel = descriptor_key(descriptor_label)

        area_sep = 10.0
        vol_rec = 35.0
        t_rec = 0.5
        if descriptor_sel in ["dntw", "dnt_a", "dnt_atr"]:
            st.markdown("<div class='result-note'>Para DnT se requiere geometría de recinto. Esta es una estimación preliminar de diseño.</div>", unsafe_allow_html=True)
            area_sep = st.number_input("Superficie del elemento separador S [m²]", value=10.0, min_value=0.5, step=0.5, key="dnt_area_sep")
            vol_rec = st.number_input("Volumen recinto receptor V [m³]", value=35.0, min_value=1.0, step=1.0, key="dnt_vol_rec")
            t_rec = st.number_input("Tiempo reverberación receptor T [s]", value=0.5, min_value=0.1, step=0.1, key="dnt_t_rec")

        configuracion = None
        tipo_ventana = None
        absorbente_tipo = "Sin absorbente"
        camara = None
        distancia_fijaciones = 600.0
        layers_left = []
        layers_right = []

        if tipo == "Panel simple":
            layers_left = layer_inputs(
                "ps",
                "Capas del panel",
                materiales_panel,
                mats,
                default_count=1,
                max_layers=5,
            )

        elif tipo == "Panel doble":
            configuracion = st.selectbox(
                "Configuración estructural",
                ["Montante simple", "Montantes independientes", "Doble estructura"],
                index=0,
            )

            layers_left = layer_inputs(
                "pd_ext",
                "Lado emisor / exterior",
                materiales_panel_doble,
                mats,
                default_count=1,
                max_layers=5,
            )

            camara = st.number_input(
                "Cámara [mm]",
                value=70.0,
                min_value=1.0,
                step=5.0,
            )

            absorbente_tipo = st.selectbox(
                "Material absorbente en cámara",
                ["Sin absorbente", "Lana mineral 40 kg/m³", "Lana mineral 60 kg/m³", "Lana mineral 80 kg/m³"],
                index=2,
            )

            if configuracion == "Montante simple":
                distancia_fijaciones = st.number_input(
                    "Distancia entre fijaciones [mm]",
                    value=600.0,
                    min_value=100.0,
                    step=50.0,
                )

            layers_right = layer_inputs(
                "pd_int",
                "Lado receptor / interior",
                materiales_panel_doble,
                mats,
                default_count=1,
                max_layers=5,
            )

        else:
            tipo_ventana = st.radio(
                "Tipo de ventana",
                ["Vidrio simple", "DVH"],
                horizontal=True,
            )

            if tipo_ventana == "Vidrio simple":
                layers_left = layer_inputs(
                    "vs",
                    "Vidrio",
                    materiales_vidrio,
                    mats,
                    default_count=1,
                    max_layers=1,
                )
            else:
                layers_left = layer_inputs(
                    "dvh_ext",
                    "Vidrio exterior",
                    materiales_vidrio,
                    mats,
                    default_count=1,
                    max_layers=1,
                )

                camara = st.number_input(
                    "Cámara DVH [mm]",
                    value=12.0,
                    min_value=1.0,
                    step=1.0,
                )

                layers_right = layer_inputs(
                    "dvh_int",
                    "Vidrio interior",
                    materiales_vidrio,
                    mats,
                    default_count=1,
                    max_layers=1,
                )

        st.button("Calcular", use_container_width=True)

    fine_freqs = np.linspace(45, 6000, 1191)

    if tipo == "Panel simple":
        tl_fine, masa, B, eta, fc = walls_multilayer_tl(layers_left, fine_freqs)

    elif tipo == "Panel doble":
        tl_fine, masa, fc, f0, fl = walls_double_multilayer_tl(
            layers_left,
            layers_right,
            camara,
            fine_freqs,
            configuracion=configuracion,
            absorbente_tipo=absorbente_tipo,
            distancia_fijaciones_mm=distancia_fijaciones,
        )

    else:
        if tipo_ventana == "Vidrio simple":
            tl_fine, masa, B, eta, fc = walls_multilayer_tl(layers_left, fine_freqs)
        else:
            tl_fine, masa, fc, f0, fl = dvh_tl(
                layers_left[0]["material"],
                layers_left[0]["espesor"],
                layers_right[0]["material"],
                layers_right[0]["espesor"],
                camara,
                fine_freqs,
            )

    third_freqs, tl_third = third_octave_from_fine(fine_freqs, tl_fine)

    if banda == "1/3 de octava":
        freqs = third_freqs
        tl = tl_third
    else:
        freqs, tl = octave_bands_from_third(third_freqs, tl_third)

    tickvals = np.array([63, 125, 250, 500, 1000, 2000, 4000])
    rw, c, ctr, iso_freqs, iso_curve, tl_rw_iso = iso717_rw_simple(third_freqs, tl_third, return_curve=True)
    stc = stc_estimate_from_curve(third_freqs, tl_third, rw)
    descriptores = calculate_airborne_descriptors(
        rw, c, ctr, stc,
        area_sep=area_sep,
        vol_rec=vol_rec,
        t_rec=t_rec,
    )
    descriptor_value = descriptores.get(descriptor_sel, rw)
    descriptor_name = descriptor_public_name(descriptor_sel)

    df = pd.DataFrame({
        "Frecuencia [Hz]": freqs.astype(int),
        "TL/R [dB]": np.round(tl, 1),
    })

    with col_visual:
        st.markdown(
            structural_visual(
                tipo,
                layers_left=layers_left,
                layers_right=layers_right,
                camara=camara,
                configuracion=configuracion,
                tipo_ventana=tipo_ventana,
                absorbente_tipo=absorbente_tipo,
            ),
            unsafe_allow_html=True,
        )

    with col_results:
        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;">
                <div class="result-card">
                    <div class="result-label">{descriptor_name}</div>
                    <div class="result-value">{descriptor_value:.0f}</div>
                    <div class="result-unit">dB</div>
                </div>
                <div class="result-card">
                    <div class="result-label">Rw / C / Ctr</div>
                    <div class="result-value" style="font-size:30px;">{rw}/{c}/{ctr}</div>
                    <div class="result-unit">dB</div>
                </div>
                <div class="result-card">
                    <div class="result-label">STC</div>
                    <div class="result-value">{stc}</div>
                    <div class="result-unit">estimado</div>
                </div>
                <div class="result-card">
                    <div class="result-label">Masa</div>
                    <div class="result-value">{masa:.1f}</div>
                    <div class="result-unit">kg/m²</div>
                </div>
                <div class="result-card">
                    <div class="result-label">Fc</div>
                    <div class="result-value">{fc:.0f}</div>
                    <div class="result-unit">Hz</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div class='result-note'>{diagnostic_note(tipo, rw, c, ctr, fc, masa)}<br><b>Descriptor seleccionado:</b> {descriptor_name} = {descriptor_value:.1f} dB.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    col_chart, col_table = st.columns([1.35, 0.65], gap="large")

    with col_chart:
        st.markdown(f"<div class='sonara-card-title'>Curva de aislamiento — {banda}</div>", unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=freqs,
                y=np.round(tl, 1),
                mode="lines+markers",
                name="TL/R WALLS",
                line=dict(width=3),
                marker=dict(size=7),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=iso_freqs,
                y=iso_curve,
                mode="lines",
                name="Curva ISO 717 desplazada",
                line=dict(width=2, dash="dash"),
            )
        )

        fig.update_xaxes(
            type="log",
            title="Frecuencia [Hz]",
            tickmode="array",
            tickvals=tickvals,
            ticktext=[str(int(f)) for f in tickvals],
            gridcolor="rgba(255,255,255,.10)",
            showline=True,
            linecolor="rgba(255,255,255,.25)",
            tickfont=dict(size=15, color="#FFFFFF"),
            title_font=dict(size=16, color="#FFFFFF"),
        )

        fig.update_yaxes(
            title="R [dB]",
            gridcolor="rgba(255,255,255,.10)",
            showline=True,
            linecolor="rgba(255,255,255,.25)",
            tickfont=dict(size=15, color="#FFFFFF"),
            title_font=dict(size=16, color="#FFFFFF"),
        )

        fig.update_layout(
            template="plotly_dark",
            height=490,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(8,18,32,.78)",
            font=dict(color="#FFFFFF", size=16),
            margin=dict(l=45, r=20, t=30, b=55),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=14, color="#FFFFFF")),
        )

        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown(f"<div class='sonara-card-title'>Tabla — {banda}</div>", unsafe_allow_html=True)

        table_fig = go.Figure(
            data=[
                go.Table(
                    columnwidth=[1.1, 1.0],
                    header=dict(
                        values=["<b>Frecuencia [Hz]</b>", "<b>TL/R [dB]</b>"],
                        fill_color="#0F4C81",
                        font=dict(color="white", size=15),
                        align=["left", "right"],
                        height=36,
                        line_color="rgba(255,255,255,.15)",
                    ),
                    cells=dict(
                        values=[df["Frecuencia [Hz]"], df["TL/R [dB]"]],
                        fill_color=[
                            ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df))],
                            ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df))],
                        ],
                        font=dict(color="#FFFFFF", size=14),
                        align=["left", "right"],
                        height=31,
                        line_color="rgba(255,255,255,.08)",
                    ),
                )
            ]
        )

        table_fig.update_layout(height=490, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(table_fig, use_container_width=True)

        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇ Descargar CSV",
            data=csv_data,
            file_name="sonara_resultados.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=False,
        )

        # Guardar solución de ruido aéreo/ventana en proyecto activo
        try:
            espesor_total = system_thickness_simple(layers_left) if tipo == "Panel simple" else system_thickness_double(layers_left, layers_right, camara or 0)
        except Exception:
            espesor_total = None

        descripcion = f"{tipo}"
        if tipo == "Panel doble":
            descripcion += f" · {configuracion} · cámara {camara} mm · {absorbente_tipo}"
        if tipo == "Ventana":
            descripcion += f" · {tipo_ventana}"

        solution_save_widget({
            "nombre": f"{tipo} {descriptor_name} {descriptor_value:.0f} dB",
            "tipo_calculo": "Ruido aéreo",
            "resultado_label": f"{descriptor_name} {descriptor_value:.0f} dB · Rw {rw} · C {c} · Ctr {ctr} · STC {stc}",
            "descriptor_seleccionado": descriptor_name,
            "descriptor_key": descriptor_sel,
            "valor": float(descriptor_value),
            "rw": float(rw),
            "c": float(c),
            "ctr": float(ctr),
            "rw_c": float(descriptores.get("rw_c")),
            "rw_ctr": float(descriptores.get("rw_ctr")),
            "stc": float(stc),
            "dntw": float(descriptores.get("dntw")),
            "dnt_a": float(descriptores.get("dnt_a")),
            "dnt_atr": float(descriptores.get("dnt_atr")),
            "descriptores": {k: float(v) for k, v in descriptores.items() if isinstance(v, (int, float, np.integer, np.floating))},
            "masa": round(float(masa), 1),
            "espesor": None if espesor_total is None else round(float(espesor_total), 1),
            "descripcion": descripcion,
            "composicion": solution_composition_text({
                "layers_left": layer_summary(layers_left),
                "layers_right": layer_summary(layers_right),
                "camara": camara,
                "configuracion": configuracion,
                "absorbente": absorbente_tipo,
            }),
            "layers_left": layer_summary(layers_left),
            "layers_right": layer_summary(layers_right),
            "camara": camara,
            "configuracion": configuracion,
            "absorbente": absorbente_tipo,
            "tipo_elemento": tipo,
            "tipo_ventana": tipo_ventana,
        }, key_prefix="save_airborne")




# =========================================================
# MÓDULO ISO 12354 - RECINTOS
# =========================================================

def _iso_reference_curve_from_rw(rw):
    """
    Curva de referencia con la misma forma usada en el cálculo WALLS/ISO 717.
    Se desplaza para que su valor a 500 Hz sea igual al Rw ingresado.
    """
    freqs = np.array([
        100, 125, 160, 200, 250, 315, 400, 500,
        630, 800, 1000, 1250, 1600, 2000, 2500, 3150
    ])

    ref = np.array([
        51, 54, 57, 60, 63, 66, 69, 70,
        71, 72, 73, 74, 74, 74, 74, 74
    ], dtype=float)

    curve = ref + (float(rw) - 70.0)
    return freqs, curve


def _iso12354_apparent_curve(freqs, r_direct, s_sep, flanks):
    """
    Estimación ISO 12354 simplificada por bandas.

    Mejora v0.9.9:
    - Si un flanco trae r_curve, se usa su curva R(f) calculada por WALLS.
    - Si no trae r_curve, se genera una curva de referencia desde Rw.
    - Kij se aplica por bandas como corrección energética simplificada.
    """

    freqs = np.asarray(freqs, dtype=float)
    r_direct = np.asarray(r_direct, dtype=float)

    s_sep = max(float(s_sep), 0.01)
    tau_total = 10 ** (-r_direct / 10.0)

    for flanco in flanks:
        if not flanco.get("activo", False):
            continue

        area_f = max(float(flanco.get("area", s_sep)), 0.01)
        kij = float(flanco.get("kij", 0.0))

        if flanco.get("r_curve") is not None:
            r_flanco = np.asarray(flanco["r_curve"], dtype=float)
            if len(r_flanco) != len(freqs):
                r_flanco = np.interp(freqs, np.asarray(flanco.get("freqs", freqs), dtype=float), r_flanco)
        else:
            rw_f = float(flanco.get("rw", 45.0))
            _, r_flanco = _iso_reference_curve_from_rw(rw_f)

        r_ij = r_flanco + kij
        tau_total += (area_f / s_sep) * 10 ** (-r_ij / 10.0)

    tau_total = np.maximum(tau_total, 1e-12)
    return -10.0 * np.log10(tau_total)


def kij_auto_value(tipo_union):
    """
    Kij referencial simplificado para uso preliminar.

    Valores orientativos:
    mientras mayor Kij, menor transmisión por la unión.
    En versión futura se puede reemplazar por tablas completas ISO 12354.
    """
    tabla = {
        "Manual": None,
        "Unión rígida pesada": 8.0,
        "Unión rígida liviana": 5.0,
        "Unión semi-rígida": 12.0,
        "Montante simple": 6.0,
        "Montantes independientes": 15.0,
        "Doble estructura": 20.0,
        "Junta elástica / resiliente": 25.0,
    }
    return tabla.get(tipo_union, None)


def _dnt_curve_from_rap(r_ap, volumen_receptor, tiempo_reverberacion, s_sep):
    """
    Conversión referencial a DnT por bandas.
    """
    v = max(float(volumen_receptor), 1.0)
    t = max(float(tiempo_reverberacion), 0.1)
    s = max(float(s_sep), 0.01)
    correction = 10.0 * np.log10(0.32 * v / (t * s))
    return np.asarray(r_ap, dtype=float) + correction


def app_iso12354():
    st.markdown(
        "<h2 style='color:#FFFFFF;margin-bottom:18px;'>ISO 12354 — Predicción entre recintos</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='result-note'>
        Módulo para estimar aislamiento acústico aéreo entre dos recintos. Permite ingresar los flancos manualmente
        o calcular su Rw usando el motor SONARA/WALLS. El esquema muestra solo los caminos de transmisión activados.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    mats = material_db()
    materiales_panel = [k for k, v in mats.items() if v.get("grupo") == "panel"]
    materiales_vidrio = [k for k, v in mats.items() if v.get("grupo") == "vidrio"]
    materiales_todos = materiales_panel + materiales_vidrio

    def calc_rw_from_layers(layers):
        fine_freqs = np.linspace(45, 6000, 1191)
        tl_fine, masa_calc, B_calc, eta_calc, fc_calc = walls_multilayer_tl(layers, fine_freqs)
        third_freqs_calc, tl_third_calc = third_octave_from_fine(fine_freqs, tl_fine)
        rw_calc, c_calc, ctr_calc = iso717_rw_simple(third_freqs_calc, tl_third_calc)
        return float(rw_calc), float(masa_calc), float(fc_calc), third_freqs_calc, tl_third_calc

    def active_flank_names(flanks_data):
        return [f["nombre"] for f in flanks_data if f.get("activo", False)]

    def transmission_scheme_html(flanks_data):
        active = active_flank_names(flanks_data)
        show_losa = "Losa horizontal" in active
        show_muro1 = "Muro lateral 1" in active
        show_muro2 = "Muro lateral 2" in active
        show_fachada = "Fachada / elemento lateral" in active

        losa_html = ""
        if show_losa:
            losa_html = """
            <div style="position:absolute;left:6%;top:4%;width:88%;height:7px;background:#22C55E;border-radius:10px;"></div>
            <div style="position:absolute;left:56%;top:7%;height:38%;border-left:4px dashed #22C55E;"></div>
            <div style="position:absolute;left:59%;top:8%;color:#00E08A;font-weight:900;">Fd losa</div>
            """

        muro1_html = ""
        if show_muro1:
            muro1_html = """
            <div style="position:absolute;left:4%;top:18%;height:64%;border-left:5px dashed #FF8A1F;"></div>
            <div style="position:absolute;left:6%;top:77%;width:47%;border-top:4px dashed #FF8A1F;"></div>
            <div style="position:absolute;left:28%;top:70%;color:#FF9F2E;font-weight:900;">Ff muro 1</div>
            """

        muro2_html = ""
        if show_muro2:
            muro2_html = """
            <div style="position:absolute;right:4%;top:18%;height:64%;border-right:5px dashed #A855F7;"></div>
            <div style="position:absolute;left:47%;top:23%;width:48%;border-top:4px dashed #A855F7;"></div>
            <div style="position:absolute;left:70%;top:16%;color:#C084FC;font-weight:900;">Df muro 2</div>
            """

        fachada_html = ""
        if show_fachada:
            fachada_html = """
            <div style="position:absolute;left:6%;bottom:8%;width:88%;height:7px;background:#38BDF8;border-radius:10px;"></div>
            <div style="position:absolute;left:48%;bottom:11%;height:29%;border-left:4px dashed #38BDF8;"></div>
            <div style="position:absolute;left:50%;bottom:18%;color:#7DD3FC;font-weight:900;">Fachada</div>
            """

        return textwrap.dedent(f"""
        <div class="sonara-card" style="margin-top:20px;">
            <div class="sonara-card-title">Esquema de caminos de transmisión</div>
            <div style="position:relative;height:330px;margin-top:10px;">

                <div style="position:absolute;left:8%;top:22%;width:34%;height:56%;
                    background:linear-gradient(135deg,#1b2735,#07111d);
                    border:7px solid #7f8791;border-radius:4px;
                    box-shadow:inset 0 0 28px rgba(0,0,0,.7);">
                </div>

                <div style="position:absolute;right:8%;top:22%;width:34%;height:56%;
                    background:linear-gradient(135deg,#1b2735,#07111d);
                    border:7px solid #7f8791;border-radius:4px;
                    box-shadow:inset 0 0 28px rgba(0,0,0,.7);">
                </div>

                <div style="position:absolute;left:44%;top:18%;width:12%;height:66%;
                    border-left:5px solid #a7adb5;border-right:5px solid #a7adb5;
                    background:rgba(160,170,180,.16);">
                </div>

                <div style="position:absolute;left:35%;top:49%;width:18%;height:4px;background:#0A84FF;"></div>
                <div style="position:absolute;left:52%;top:45%;width:0;height:0;
                    border-top:12px solid transparent;
                    border-bottom:12px solid transparent;
                    border-left:18px solid #0A84FF;">
                </div>
                <div style="position:absolute;left:33%;top:39%;color:#42A5FF;font-weight:900;">
                    Dd<br><span style="font-size:13px;color:#42A5FF;">directa</span>
                </div>

                {losa_html}
                {muro1_html}
                {muro2_html}
                {fachada_html}

                <div style="position:absolute;left:18%;bottom:0;color:#EAF4FF;font-weight:700;">Recinto emisor</div>
                <div style="position:absolute;right:16%;bottom:0;color:#EAF4FF;font-weight:700;">Recinto receptor</div>
            </div>
        </div>
        """)

    col_input, col_results = st.columns([1.05, 1.15], gap="large")

    with col_input:
        st.markdown("<div class='sonara-card-title'>Datos del recinto</div>", unsafe_allow_html=True)

        s_sep = st.number_input(
            "Superficie del elemento separador S [m²]",
            value=10.0,
            min_value=0.1,
            step=0.5
        )

        volumen_receptor = st.number_input(
            "Volumen recinto receptor V [m³]",
            value=35.0,
            min_value=1.0,
            step=1.0
        )

        t_receptor = st.number_input(
            "Tiempo de reverberación receptor T [s]",
            value=0.5,
            min_value=0.1,
            step=0.1
        )

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div class='sonara-card-title'>Elemento separador</div>", unsafe_allow_html=True)

        rw_direct = st.number_input(
            "Rw elemento separador [dB]",
            value=45.0,
            min_value=10.0,
            max_value=90.0,
            step=1.0
        )

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div class='sonara-card-title'>Flanqueos</div>", unsafe_allow_html=True)

        incluir_flanqueos = st.checkbox(
            "Incluir flanqueos",
            value=True
        )

        flanks = []

        flancos_base = [
            {"nombre": "Muro lateral 1", "rw": 45.0, "area": 10.0, "kij": 5.0, "activo": True, "key": "muro1"},
            {"nombre": "Muro lateral 2", "rw": 45.0, "area": 10.0, "kij": 5.0, "activo": True, "key": "muro2"},
            {"nombre": "Fachada / elemento lateral", "rw": 45.0, "area": 10.0, "kij": 5.0, "activo": False, "key": "fachada"},
            {"nombre": "Losa horizontal", "rw": 55.0, "area": 15.0, "kij": 8.0, "activo": False, "key": "losa"},
        ]

        if incluir_flanqueos:
            for i, fl in enumerate(flancos_base, start=1):
                with st.expander(f"{fl['nombre']}", expanded=fl["activo"]):
                    activo = st.checkbox(
                        "Activar este flanco",
                        value=fl["activo"],
                        key=f"iso12354_flank_active_{i}"
                    )

                    modo_r = st.radio(
                        "R del flanco",
                        ["Manual", "Calcular con SONARA/WALLS"],
                        horizontal=True,
                        key=f"iso12354_modo_r_{i}"
                    )

                    r_curve_f = None
                    freqs_f = None

                    if modo_r == "Manual":
                        rw_f = st.number_input(
                            "R flanco [dB]",
                            value=fl["rw"],
                            min_value=10.0,
                            max_value=90.0,
                            step=1.0,
                            key=f"iso12354_rw_f_{i}"
                        )
                        masa_f = None
                        fc_f = None
                    else:
                        capas_flanco = layer_inputs(
                            f"iso_flanco_{i}",
                            "Capas del flanco",
                            materiales_todos,
                            mats,
                            default_count=1,
                            max_layers=4
                        )

                        rw_f, masa_f, fc_f, freqs_f, r_curve_f = calc_rw_from_layers(capas_flanco)

                        st.markdown(
                            f"""
                            <div class='result-note'>
                            Rw calculado del flanco = <b>{rw_f:.0f} dB</b> · 
                            Masa = <b>{masa_f:.1f} kg/m²</b> · 
                            Fc = <b>{fc_f:.0f} Hz</b><br>
                            El módulo ISO 12354 usará la curva R(f) del flanco por bandas, no solo el Rw.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    area_f = st.number_input(
                        "Superficie equivalente del flanco S_eq [m²]",
                        value=fl["area"],
                        min_value=0.1,
                        step=0.5,
                        key=f"iso12354_area_f_{i}"
                    )

                    tipo_union = st.selectbox(
                        "Tipo de unión / desacople",
                        [
                            "Manual",
                            "Unión rígida pesada",
                            "Unión rígida liviana",
                            "Unión semi-rígida",
                            "Montante simple",
                            "Montantes independientes",
                            "Doble estructura",
                            "Junta elástica / resiliente",
                        ],
                        index=0,
                        key=f"iso12354_tipo_union_{i}"
                    )

                    kij_sugerido = kij_auto_value(tipo_union)

                    if kij_sugerido is None:
                        kij = st.number_input(
                            "Corrección de unión Kij [dB]",
                            value=fl["kij"],
                            min_value=-20.0,
                            max_value=40.0,
                            step=1.0,
                            key=f"iso12354_kij_{i}"
                        )
                    else:
                        kij = float(kij_sugerido)
                        st.markdown(
                            f"""
                            <div class='result-note'>
                            Kij aplicado automáticamente para <b>{tipo_union}</b>: <b>{kij:.1f} dB</b>.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    flanks.append({
                        "activo": activo,
                        "rw": float(rw_f),
                        "area": float(area_f),
                        "kij": float(kij),
                        "nombre": fl["nombre"],
                        "modo": modo_r,
                        "r_curve": r_curve_f,
                        "freqs": freqs_f
                    })

        with st.expander("¿Qué es R, S_eq y K_ij?"):
            st.markdown(
                """
                **R flanco:** aislamiento acústico propio del elemento lateral o flanqueante.  
                **S_eq:** superficie equivalente asociada al camino de transmisión flanqueante.  
                **K_ij:** corrección de unión. Mientras mayor sea, menor transmisión por esa unión.
                """
            )

        with st.expander("¿Cómo se estima R del flanqueo?"):
            st.markdown(
                """
                Puede ingresarse manualmente desde ensayos/fichas técnicas o calcularse con SONARA/WALLS.
                Si lo calculas con SONARA, el software usa las capas del flanco y obtiene su Rw automáticamente.
                """
            )

        with st.expander("¿Cómo se estima la corrección de unión K_ij?"):
            st.markdown(
                """
                SONARA ahora permite dos formas:
                - **Manual:** el usuario ingresa Kij.
                - **Automática referencial:** se asigna Kij según el tipo de unión/desacople.

                Criterio general: mientras mayor Kij, menor transmisión por la unión.
                Estos valores son orientativos y deben calibrarse con tablas normativas, ensayos o criterios de proyecto.
                """
            )

    freqs, r_direct = _iso_reference_curve_from_rw(rw_direct)

    if incluir_flanqueos:
        r_ap = _iso12354_apparent_curve(freqs, r_direct, s_sep, flanks)
    else:
        r_ap = np.asarray(r_direct, dtype=float)

    dnt = _dnt_curve_from_rap(r_ap, volumen_receptor, t_receptor, s_sep)

    rw_ap, c_ap, ctr_ap = iso717_rw_simple(freqs, r_ap)
    dntw, c_dnt, ctr_dnt = iso717_rw_simple(freqs, dnt)

    flanking_penalty = max(0.0, float(rw_direct - rw_ap))

    kij_values = [
        float(f.get("kij", 0.0))
        for f in flanks
        if f.get("activo", False)
    ]

    kij_eq = float(np.mean(kij_values)) if kij_values else 0.0

    flanking_curve = np.maximum(np.asarray(r_direct, dtype=float) - np.asarray(r_ap, dtype=float), 0.0)

    with col_results:
        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
                <div class="result-card">
                    <div class="result-label">R'ap,w</div>
                    <div class="result-value">{rw_ap}</div>
                    <div class="result-unit">dB</div>
                </div>
                <div class="result-card">
                    <div class="result-label">DnT,w</div>
                    <div class="result-value">{dntw}</div>
                    <div class="result-unit">dB</div>
                </div>
                <div class="result-card">
                    <div class="result-label">Flanqueo</div>
                    <div class="result-value">{flanking_penalty:.1f}</div>
                    <div class="result-unit">dB pérdida</div>
                </div>
                <div class="result-card">
                    <div class="result-label">Kij Eq.</div>
                    <div class="result-value">{kij_eq:.1f}</div>
                    <div class="result-unit">dB</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='result-note'>
            C = {c_ap} dB · Ctr = {ctr_ap} dB · DnT,w + Ctr = {dntw + ctr_dnt} dB
            </div>
            """,
            unsafe_allow_html=True
        )

        components.html(
            transmission_scheme_html(flanks if incluir_flanqueos else []),
            height=390,
            scrolling=False
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    col_chart, col_table = st.columns([1.35, 0.65], gap="large")

    with col_chart:
        st.markdown("<div class='sonara-card-title'>Curvas por bandas</div>", unsafe_allow_html=True)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=freqs,
            y=np.round(r_direct, 1),
            mode="lines+markers",
            name="R directo (Dd)",
            line=dict(color="#4F7CFF", width=3),
            marker=dict(size=6)
        ))

        fig.add_trace(go.Scatter(
            x=freqs,
            y=np.round(r_ap, 1),
            mode="lines+markers",
            name="R' aparente (con flanqueos)",
            line=dict(color="#00D4FF", width=3),
            marker=dict(size=6)
        ))

        fig.add_trace(go.Scatter(
            x=freqs,
            y=np.round(dnt, 1),
            mode="lines+markers",
            name="DnT",
            line=dict(color="#00E08A", width=3),
            marker=dict(size=6)
        ))

        fig.add_trace(go.Scatter(
            x=freqs,
            y=np.round(flanking_curve, 1),
            mode="lines",
            name="Pérdida por flanqueo",
            line=dict(color="#FF8A1F", width=2, dash="dash")
        ))

        iso_ref = np.asarray(r_direct, dtype=float) + 3.0

        fig.add_trace(go.Scatter(
            x=freqs,
            y=np.round(iso_ref, 1),
            mode="lines",
            name="Curva ISO 717 ref.",
            line=dict(color="#D7E3F4", width=2, dash="dot")
        ))

        fig.update_xaxes(
            type="log",
            title="Frecuencia [Hz]",
            tickmode="array",
            tickvals=[100, 125, 250, 500, 1000, 2000, 3150],
            ticktext=["100", "125", "250", "500", "1000", "2000", "3150"],
            gridcolor="rgba(255,255,255,.10)",
            tickfont=dict(size=15, color="#FFFFFF"),
            title_font=dict(size=16, color="#FFFFFF")
        )

        fig.update_yaxes(
            title="Aislamiento acústico R [dB]",
            gridcolor="rgba(255,255,255,.10)",
            tickfont=dict(size=15, color="#FFFFFF"),
            title_font=dict(size=16, color="#FFFFFF")
        )

        fig.update_layout(
            template="plotly_dark",
            height=540,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(8,18,32,.78)",
            font=dict(size=15, color="#EAF4FF"),
            margin=dict(l=60, r=20, t=90, b=60),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.12,
                xanchor="center",
                x=0.5,
                font=dict(size=13, color="#EAF4FF")
            )
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            """
            <div class='result-note'>
            La curva gris punteada se muestra como referencia visual. 
            Los resultados dependen de la calidad de los datos de entrada y de las hipótesis del modelo.
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_table:
        st.markdown("<div class='sonara-card-title'>Tabla ISO 12354 (por bandas)</div>", unsafe_allow_html=True)

        df_iso = pd.DataFrame({
            "Frecuencia [Hz]": freqs.astype(int),
            "R directo Dd [dB]": np.round(r_direct, 1),
            "R' aparente [dB]": np.round(r_ap, 1),
            "Flanqueo total [dB]": np.round(flanking_curve, 1),
            "DnT [dB]": np.round(dnt, 1),
        })

        table_fig = go.Figure(data=[go.Table(
            columnwidth=[0.8, 1.05, 1.1, 1.0, 1.0],
            header=dict(
                values=[
                    "<b>f [Hz]</b>",
                    "<b>R directo<br>Dd [dB]</b>",
                    "<b>R' aparente<br>[dB]</b>",
                    "<b>Flanqueo<br>[dB]</b>",
                    "<b>DnT<br>[dB]</b>"
                ],
                fill_color="#0F4C81",
                font=dict(color="white", size=14),
                align=["left", "right", "right", "right", "right"],
                height=42,
                line_color="rgba(255,255,255,.15)"
            ),
            cells=dict(
                values=[
                    df_iso["Frecuencia [Hz]"],
                    df_iso["R directo Dd [dB]"],
                    df_iso["R' aparente [dB]"],
                    df_iso["Flanqueo total [dB]"],
                    df_iso["DnT [dB]"]
                ],
                fill_color=[
                    ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df_iso))],
                    ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df_iso))],
                    ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df_iso))],
                    ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df_iso))],
                    ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df_iso))],
                ],
                font=dict(color="#FFFFFF", size=13),
                align=["left", "right", "right", "right", "right"],
                height=30,
                line_color="rgba(255,255,255,.08)"
            )
        )])

        table_fig.update_layout(
            height=540,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)"
        )

        st.plotly_chart(table_fig, use_container_width=True)

        st.download_button(
            label="⬇ Descargar CSV ISO 12354",
            data=df_iso.to_csv(index=False).encode("utf-8"),
            file_name="sonara_iso12354.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_notes, col_refs = st.columns(2, gap="large")

    with col_notes:
        st.markdown(
            """
            <div class='sonara-card'>
                <div class='sonara-card-title'>Notas</div>
                <ul style='color:#DCEBFF;line-height:1.7;'>
                    <li><b>Dd:</b> camino directo a través del elemento separador.</li>
                    <li><b>Fd:</b> camino por flanco que termina en el elemento separador.</li>
                    <li><b>Df:</b> camino directo que termina en un flanco.</li>
                    <li><b>Ff:</b> camino por flanco en ambos recintos.</li>
                    <li><b>R'_ap,w:</b> aislamiento aparente, incluyendo flanqueos.</li>
                    <li><b>DnT,w:</b> aislamiento acústico estandarizado entre recintos.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_refs:
        st.markdown(
            """
            <div class='sonara-card'>
                <div class='sonara-card-title'>Referencias bibliográficas actualizadas</div>
                <ul style='color:#DCEBFF;line-height:1.7;'>
                    <li><b>ISO 12354-1:2017</b> — Building acoustics — Estimation of acoustic performance of buildings from the performance of elements — Part 1: Airborne sound insulation between rooms.</li>
                    <li><b>ISO 717-1:2020</b> — Acoustics — Rating of sound insulation in buildings and of building elements — Part 1: Airborne sound insulation.</li>
                    <li><b>ISO 10140-2:2021</b> — Acoustics — Laboratory measurement of sound insulation of building elements — Part 2: Measurement of airborne sound insulation.</li>
                    <li><b>ISO 16283-1:2014</b> — Acoustics — Field measurement of sound insulation in buildings and of building elements — Part 1: Airborne sound insulation.</li>
                    <li><b>ISO 16283-3:2016</b> — Acoustics — Field measurement of sound insulation in buildings and of building elements — Part 3: Façade sound insulation.</li>
                    <li><b>ISO 12354-3:2017</b> — Building acoustics — Estimation of acoustic performance of buildings from the performance of elements — Part 3: Airborne sound insulation against outdoor sound.</li>
                    <li><b>Crocker & Price (1969)</b> — Sound transmission using statistical energy analysis.</li>
                    <li><b>Ljunggren (1991)</b> — Airborne sound insulation of thick walls.</li>
                    <li><b>Hoeller, Parzinger & Schanda (2025)</b> — Discussion and proposed changes to Annex B of ISO 12354-1 for homogeneous building elements.</li>
                </ul>
                <div class='result-note' style='margin-top:14px;'>
                    SONARA usa WALLS para elementos constructivos e ISO 12354-1 como base conceptual para recintos.
                    Las referencias deben revisarse frente a normas oficiales vigentes antes de uso contractual, certificación o informe formal.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def app_biblioteca():
    st.markdown(
        "<h2 style='color:#FFFFFF;margin-bottom:18px;'>Biblioteca técnica SONARA</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='sonara-card'>
            <div class='sonara-card-title'>Normas base de aislamiento acústico</div>
            <ul style='color:#DCEBFF;line-height:1.8;'>
                <li><b>ISO 12354-1:2017</b> — Estimación del aislamiento aéreo entre recintos desde el desempeño de elementos constructivos.</li>
                <li><b>ISO 717-1:2020</b> — Evaluación ponderada de aislamiento aéreo: Rw, C, Ctr, DnT,w.</li>
                <li><b>ISO 10140-2:2021</b> — Medición en laboratorio del aislamiento acústico aéreo de elementos de construcción.</li>
                <li><b>ISO 16283-1:2014</b> — Medición en terreno del aislamiento acústico aéreo entre recintos.</li>
                <li><b>ISO 16283-3:2016</b> — Medición en terreno del aislamiento acústico de fachadas.</li>
                <li><b>ISO 12354-3:2017</b> — Predicción del aislamiento frente a ruido exterior.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div class='sonara-card'>
                <div class='sonara-card-title'>Referencias científicas</div>
                <ul style='color:#DCEBFF;line-height:1.8;'>
                    <li><b>Crocker & Price (1969)</b> — Sound transmission using statistical energy analysis.</li>
                    <li><b>Ljunggren (1991)</b> — Airborne sound insulation of thick walls.</li>
                    <li><b>Hoeller, Parzinger & Schanda (2025)</b> — The Sound Reduction Index of Homogeneous Building Elements according to Annex B of ISO 12354-1: Discussion and proposal for changes.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class='sonara-card'>
                <div class='sonara-card-title'>Uso dentro de SONARA</div>
                <ul style='color:#DCEBFF;line-height:1.8;'>
                    <li><b>WALLS:</b> cálculo de R(f), Rw, C y Ctr de elementos constructivos.</li>
                    <li><b>ISO 717-1:</b> clasificación ponderada de curvas de aislamiento.</li>
                    <li><b>ISO 12354-1:</b> estimación entre recintos, transmisión directa, flanqueos y corrección de uniones Kij.</li>
                    <li><b>ISO 10140-2:</b> comparación con ensayos de laboratorio.</li>
                    <li><b>ISO 16283-1:</b> comparación con mediciones en terreno.</li>
                    <li><b>ISO 12354-2 / ISO 717-2:</b> predicción y evaluación de ruido de impacto.</li>
                </ul>
                <div class='result-note' style='margin-top:14px;'>
                    Esta bibliografía sirve como fuente técnica del software. Para documentos oficiales, verificar siempre la edición vigente y el texto normativo completo.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )



# =========================================================
# IMPACTO - ISO 12354-2 / ISO 717-2 NIVEL 1-2
# =========================================================

def impact_freqs():
    return np.array([100, 125, 160, 200, 250, 315, 400, 500,
                     630, 800, 1000, 1250, 1600, 2000, 2500, 3150])


def impact_ln0w_from_mass(masa_superficial):
    """
    Estimación referencial para losa homogénea pesada:
    Ln,0,w = 164 - 35 log10(m')
    m' en kg/m².
    """
    m = max(float(masa_superficial), 1.0)
    return float(164.0 - 35.0 * np.log10(m))


def impact_reference_curve_from_lnw(lnw):
    """
    Curva referencial de nivel de impacto por bandas.
    Es una forma típica decreciente con frecuencia, desplazada para que
    el valor ponderado sea cercano al Ln,w ingresado.
    """
    freqs = impact_freqs()
    shape = np.array([8, 7, 6, 5, 4, 3, 2, 1,
                      0, -1, -2, -3, -4, -5, -6, -7], dtype=float)
    return freqs, float(lnw) + shape


def delta_floor_curve(tipo_piso, freqs, f0=None):
    """
    Mejora ΔL(f) por revestimiento/piso.
    Para piso flotante físico usa una transición controlada por f0.
    """
    freqs = np.asarray(freqs, dtype=float)

    presets = {
        "Sin revestimiento": np.zeros_like(freqs),
        "Vinílico / piso delgado": np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 5, 5, 5], dtype=float),
        "Alfombra gruesa": np.array([2, 3, 4, 5, 7, 9, 12, 15, 18, 20, 22, 23, 24, 24, 24, 24], dtype=float),
        "Piso flotante básico": np.array([0, 1, 2, 3, 5, 7, 9, 11, 13, 14, 15, 16, 17, 17, 17, 17], dtype=float),
        "Sobrelosa flotante": np.array([1, 2, 4, 6, 9, 12, 16, 20, 23, 26, 29, 31, 33, 34, 35, 35], dtype=float),
    }

    if tipo_piso != "Piso flotante físico":
        return presets.get(tipo_piso, np.zeros_like(freqs))

    f0 = max(float(f0 or 80.0), 20.0)
    # Modelo físico simplificado: bajo f0 casi no mejora; sobre f0 aumenta ~30log(f/f0)
    delta = np.where(freqs <= f0, -3.0, 30.0 * np.log10(freqs / f0))
    delta = np.clip(delta, -3.0, 30.0)
    return delta


def ceiling_delta_curve(tipo_cielo, freqs):
    freqs = np.asarray(freqs, dtype=float)
    presets = {
        "Sin cielo": np.zeros_like(freqs),
        "Cielo yeso-cartón simple": np.array([0, 0, 0, 1, 1, 2, 2, 3, 3, 3, 4, 4, 4, 4, 4, 4], dtype=float),
        "Cielo suspendido con lana": np.array([1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 9, 9, 10, 10, 10, 10], dtype=float),
        "Cielo acústico desacoplado": np.array([2, 3, 4, 5, 7, 9, 11, 12, 13, 14, 15, 15, 16, 16, 16, 16], dtype=float),
    }
    return presets.get(tipo_cielo, np.zeros_like(freqs))


def iso717_impact_rating(freqs, ln_curve):
    """
    Evaluación preliminar Ln,w / CI.
    Para Nivel 1-2 se toma el máximo ajustado de una curva de referencia simplificada.
    CI se estima como diferencia energética de bajas frecuencias frente al valor ponderado.
    """
    freqs = np.asarray(freqs, dtype=float)
    ln_curve = np.asarray(ln_curve, dtype=float)
    lnw = int(round(np.interp(500, freqs, ln_curve)))

    low_mask = (freqs >= 100) & (freqs <= 2500)
    ci_val = 10 * np.log10(np.mean(10 ** (ln_curve[low_mask] / 10))) - lnw
    ci = int(round(ci_val))
    return lnw, ci


def energetic_sum_levels(levels):
    arr = np.vstack([np.asarray(x, dtype=float) for x in levels])
    return 10.0 * np.log10(np.sum(10 ** (arr / 10.0), axis=0))


def impact_transmission_scheme_html(flanks_active):
    """
    Esquema dinámico para caminos de impacto.
    """
    show_muro1 = "Muro lateral 1" in flanks_active
    show_muro2 = "Muro lateral 2" in flanks_active
    show_fachada = "Fachada / elemento lateral" in flanks_active
    show_tabique = "Tabique separador / elemento vertical" in flanks_active

    muro1 = """
        <div style="position:absolute;left:5%;top:20%;height:60%;border-left:5px dashed #FF8A1F;"></div>
        <div style="position:absolute;left:7%;top:74%;width:45%;border-top:4px dashed #FF8A1F;"></div>
        <div style="position:absolute;left:22%;top:66%;color:#FF9F2E;font-weight:900;">Flanco muro 1</div>
    """ if show_muro1 else ""

    muro2 = """
        <div style="position:absolute;right:5%;top:20%;height:60%;border-right:5px dashed #A855F7;"></div>
        <div style="position:absolute;left:50%;top:23%;width:45%;border-top:4px dashed #A855F7;"></div>
        <div style="position:absolute;left:68%;top:15%;color:#C084FC;font-weight:900;">Flanco muro 2</div>
    """ if show_muro2 else ""

    fachada = """
        <div style="position:absolute;left:8%;bottom:8%;width:84%;height:7px;background:#38BDF8;border-radius:10px;"></div>
        <div style="position:absolute;left:47%;bottom:11%;height:27%;border-left:4px dashed #38BDF8;"></div>
        <div style="position:absolute;left:50%;bottom:17%;color:#7DD3FC;font-weight:900;">Fachada</div>
    """ if show_fachada else ""

    tabique = """
        <div style="position:absolute;left:45%;top:12%;height:26%;border-left:4px dashed #22C55E;"></div>
        <div style="position:absolute;left:48%;top:10%;color:#00E08A;font-weight:900;">Tabique</div>
    """ if show_tabique else ""

    return textwrap.dedent(f"""
    <div class="sonara-card" style="margin-top:20px;">
        <div class="sonara-card-title">Esquema de caminos de impacto</div>
        <div style="position:relative;height:330px;margin-top:10px;">

            <div style="position:absolute;left:10%;top:12%;width:80%;height:9px;background:#94A3B8;border-radius:10px;"></div>
            <div style="position:absolute;left:10%;top:68%;width:80%;height:9px;background:#64748B;border-radius:10px;"></div>

            <div style="position:absolute;left:12%;top:21%;width:32%;height:42%;
                background:linear-gradient(135deg,#1b2735,#07111d);
                border:5px solid #7f8791;border-radius:4px;
                box-shadow:inset 0 0 22px rgba(0,0,0,.65);">
            </div>

            <div style="position:absolute;right:12%;top:21%;width:32%;height:42%;
                background:linear-gradient(135deg,#1b2735,#07111d);
                border:5px solid #7f8791;border-radius:4px;
                box-shadow:inset 0 0 22px rgba(0,0,0,.65);">
            </div>

            <div style="position:absolute;left:50%;top:13%;height:52%;border-left:5px solid #0A84FF;"></div>
            <div style="position:absolute;left:47%;top:56%;width:0;height:0;
                border-left:14px solid transparent;border-right:14px solid transparent;border-top:20px solid #0A84FF;">
            </div>
            <div style="position:absolute;left:52%;top:35%;color:#42A5FF;font-weight:900;">Directo<br><span style="font-size:13px;color:#42A5FF;">losa → recinto</span></div>

            {muro1}
            {muro2}
            {fachada}
            {tabique}

            <div style="position:absolute;left:16%;bottom:0;color:#EAF4FF;font-weight:700;">Recinto emisor / piso superior</div>
            <div style="position:absolute;right:13%;bottom:0;color:#EAF4FF;font-weight:700;">Recinto receptor</div>
        </div>
    </div>
    """)


def impact_kij_auto_value(tipo_union):
    tabla = {
        "Manual": None,
        "Unión rígida pesada": 5.0,
        "Unión rígida liviana": 3.0,
        "Unión semi-rígida": 8.0,
        "Montante simple": 5.0,
        "Montantes independientes": 12.0,
        "Doble estructura": 16.0,
        "Junta elástica / resiliente": 20.0,
    }
    return tabla.get(tipo_union, None)


def impact_flank_curve_from_lnw(freqs, lnw, kij=0.0):
    """
    Nivel de flanco por impacto referencial.
    Kij reduce el nivel transmitido por la unión.
    """
    _, curve = impact_reference_curve_from_lnw(lnw)
    return np.asarray(curve, dtype=float) - float(kij)


def impact_iso12354_2_sum(ln_direct, flanks):
    """
    Suma energética de camino directo + caminos flanqueantes de impacto.
    """
    levels = [np.asarray(ln_direct, dtype=float)]

    for f in flanks:
        if not f.get("activo", False):
            continue
        levels.append(np.asarray(f["curve"], dtype=float))

    return energetic_sum_levels(levels)


def app_impacto():
    st.markdown(
        "<h2 style='color:#FFFFFF;margin-bottom:18px;'>Impacto — Ruido de impacto entre recintos</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='result-note'>
        Módulo para estimación de ruido de impacto. Incluye modo simplificado y modo ISO 12354-2 preliminar,
        con piso flotante masa-resorte-masa, cielo inferior, normalización L'nT y flanqueos por bandas.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    modo_impacto = st.radio(
        "Método de cálculo",
        ["Simplificado", "ISO 12354-2"],
        horizontal=True
    )

    col_input, col_results = st.columns([1.0, 1.2], gap="large")

    with col_input:
        st.markdown("<div class='sonara-card-title'>Forjado / losa base</div>", unsafe_allow_html=True)

        modo_losa = st.radio(
            "Nivel base de impacto",
            ["Calcular por masa superficial", "Ingresar Ln,0,w manual"],
            horizontal=True
        )

        if modo_losa == "Calcular por masa superficial":
            esp_losa = st.number_input("Espesor losa hormigón [mm]", value=150.0, min_value=50.0, step=10.0)
            dens_losa = st.number_input("Densidad hormigón [kg/m³]", value=2400.0, min_value=500.0, step=50.0)
            masa_losa = esp_losa / 1000.0 * dens_losa
            ln0w = impact_ln0w_from_mass(masa_losa)
        else:
            ln0w = st.number_input("Ln,0,w losa desnuda [dB]", value=77.0, min_value=40.0, max_value=100.0, step=1.0)
            masa_losa = None

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div class='sonara-card-title'>Revestimiento superior</div>", unsafe_allow_html=True)

        tipo_piso = st.selectbox(
            "Tipo de piso / revestimiento",
            [
                "Sin revestimiento",
                "Vinílico / piso delgado",
                "Alfombra gruesa",
                "Piso flotante básico",
                "Sobrelosa flotante",
                "Piso flotante físico",
            ],
            index=0
        )

        f0_piso = None
        if tipo_piso == "Piso flotante físico":
            col_a, col_b = st.columns(2)
            with col_a:
                masa_sobrelosa = st.number_input("Masa superficial sobrelosa m' [kg/m²]", value=90.0, min_value=5.0, step=5.0)
            with col_b:
                rigidez_dinamica = st.number_input("Rigidez dinámica s' [MN/m³]", value=15.0, min_value=1.0, step=1.0)
            f0_piso = (1.0 / (2.0 * np.pi)) * np.sqrt((rigidez_dinamica * 1e6) / masa_sobrelosa)
            st.markdown(
                f"<div class='result-note'>Frecuencia propia estimada del piso flotante: <b>{f0_piso:.0f} Hz</b></div>",
                unsafe_allow_html=True
            )

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div class='sonara-card-title'>Cielo inferior</div>", unsafe_allow_html=True)

        tipo_cielo = st.selectbox(
            "Tipo de cielo",
            [
                "Sin cielo",
                "Cielo yeso-cartón simple",
                "Cielo suspendido con lana",
                "Cielo acústico desacoplado",
            ],
            index=0
        )

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div class='sonara-card-title'>Recinto receptor</div>", unsafe_allow_html=True)

        volumen_receptor = st.number_input("Volumen recinto receptor V [m³]", value=35.0, min_value=1.0, step=1.0)
        t_receptor = st.number_input("Tiempo reverberación receptor T [s]", value=0.5, min_value=0.1, step=0.1)

        flanks = []

        if modo_impacto == "Simplificado":
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("<div class='sonara-card-title'>Flanqueos equivalentes</div>", unsafe_allow_html=True)

            incluir_flancos = st.checkbox("Incluir flanqueos", value=False)
            flanco_nivel = st.slider("Nivel equivalente de flanqueos [dB]", min_value=35, max_value=85, value=60)
            n_flancos = st.number_input("Número de flancos equivalentes", value=1, min_value=0, max_value=6, step=1)

        else:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("<div class='sonara-card-title'>Flanqueos ISO 12354-2</div>", unsafe_allow_html=True)

            incluir_flancos = st.checkbox("Incluir flanqueos de impacto", value=True)

            flancos_base = [
                {"nombre": "Muro lateral 1", "lnw": 62.0, "kij": 5.0, "activo": True},
                {"nombre": "Muro lateral 2", "lnw": 62.0, "kij": 5.0, "activo": True},
                {"nombre": "Fachada / elemento lateral", "lnw": 65.0, "kij": 5.0, "activo": False},
                {"nombre": "Tabique separador / elemento vertical", "lnw": 60.0, "kij": 8.0, "activo": False},
            ]

            if incluir_flancos:
                for i, fl in enumerate(flancos_base, start=1):
                    with st.expander(fl["nombre"], expanded=fl["activo"]):
                        activo = st.checkbox("Activar este flanco", value=fl["activo"], key=f"imp_fl_active_{i}")

                        lnw_f = st.number_input(
                            "Nivel de impacto equivalente del flanco Ln,w [dB]",
                            value=fl["lnw"],
                            min_value=35.0,
                            max_value=95.0,
                            step=1.0,
                            key=f"imp_lnw_f_{i}"
                        )

                        tipo_union = st.selectbox(
                            "Tipo de unión / desacople",
                            [
                                "Manual",
                                "Unión rígida pesada",
                                "Unión rígida liviana",
                                "Unión semi-rígida",
                                "Montante simple",
                                "Montantes independientes",
                                "Doble estructura",
                                "Junta elástica / resiliente",
                            ],
                            index=0,
                            key=f"imp_tipo_union_{i}"
                        )

                        kij_sugerido = impact_kij_auto_value(tipo_union)

                        if kij_sugerido is None:
                            kij = st.number_input(
                                "Corrección de unión Kij [dB]",
                                value=fl["kij"],
                                min_value=-20.0,
                                max_value=40.0,
                                step=1.0,
                                key=f"imp_kij_{i}"
                            )
                        else:
                            kij = float(kij_sugerido)
                            st.markdown(
                                f"<div class='result-note'>Kij aplicado automáticamente: <b>{kij:.1f} dB</b></div>",
                                unsafe_allow_html=True
                            )

                        flanks.append({
                            "activo": activo,
                            "nombre": fl["nombre"],
                            "lnw": float(lnw_f),
                            "kij": float(kij),
                        })

            with st.expander("¿Qué calcula el modo ISO 12354-2?"):
                st.markdown(
                    """
                    El modo ISO 12354-2 suma energéticamente el camino directo de impacto y los caminos flanqueantes.
                    Cada flanco se representa por un nivel Ln,w equivalente y una corrección de unión Kij.
                    """
                )

    freqs, ln0_curve = impact_reference_curve_from_lnw(ln0w)
    delta_piso = delta_floor_curve(tipo_piso, freqs, f0_piso)
    delta_cielo = ceiling_delta_curve(tipo_cielo, freqs)

    ln_direct = ln0_curve - delta_piso - delta_cielo

    active_flank_names = []

    if modo_impacto == "Simplificado":
        levels = [ln_direct]
        if incluir_flancos and n_flancos > 0:
            _, fl_curve = impact_reference_curve_from_lnw(flanco_nivel)
            for _ in range(int(n_flancos)):
                levels.append(fl_curve)

        ln_total = energetic_sum_levels(levels)
    else:
        flanks_calc = []
        for fl in flanks:
            if not fl.get("activo", False):
                continue
            fl_curve = impact_flank_curve_from_lnw(freqs, fl["lnw"], fl["kij"])
            fl_new = dict(fl)
            fl_new["curve"] = fl_curve
            flanks_calc.append(fl_new)
            active_flank_names.append(fl["nombre"])

        ln_total = impact_iso12354_2_sum(ln_direct, flanks_calc)

    # Normalización a T0 = 0.5 s. Si T receptor > 0.5, L'nT disminuye.
    lnT = ln_total - 10.0 * np.log10(max(t_receptor, 0.1) / 0.5)

    lnw, ci = iso717_impact_rating(freqs, ln_total)
    lntw, ci_t = iso717_impact_rating(freqs, lnT)

    with col_results:
        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
                <div class="result-card">
                    <div class="result-label">Ln,w</div>
                    <div class="result-value">{lnw}</div>
                    <div class="result-unit">dB</div>
                </div>
                <div class="result-card">
                    <div class="result-label">L'nT,w</div>
                    <div class="result-value">{lntw}</div>
                    <div class="result-unit">dB</div>
                </div>
                <div class="result-card">
                    <div class="result-label">CI</div>
                    <div class="result-value">{ci_t}</div>
                    <div class="result-unit">dB</div>
                </div>
                <div class="result-card">
                    <div class="result-label">L'nT,w+CI</div>
                    <div class="result-value">{lntw + ci_t}</div>
                    <div class="result-unit">dB</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        masa_txt = f"Masa losa = {masa_losa:.1f} kg/m² · " if masa_losa is not None else ""
        st.markdown(
            f"""
            <div class='result-note'>
            Método: <b>{modo_impacto}</b> · {masa_txt}Ln,0,w = {ln0w:.1f} dB · 
            ΔLw piso aprox. = {np.mean(delta_piso):.1f} dB · 
            Mejora cielo aprox. = {np.mean(delta_cielo):.1f} dB. En ruido de impacto, <b>menor es mejor</b>.
            </div>
            """,
            unsafe_allow_html=True
        )

        if modo_impacto == "ISO 12354-2":
            components.html(
                impact_transmission_scheme_html(active_flank_names),
                height=390,
                scrolling=False
            )

    st.markdown("<hr>", unsafe_allow_html=True)

    col_chart, col_table = st.columns([1.35, 0.65], gap="large")

    with col_chart:
        st.markdown("<div class='sonara-card-title'>Curvas de impacto por bandas</div>", unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=freqs, y=np.round(ln0_curve, 1), mode="lines+markers",
                                 name="Losa desnuda Ln,0", line=dict(color="#4F7CFF", width=3), marker=dict(size=6)))
        fig.add_trace(go.Scatter(x=freqs, y=np.round(ln_direct, 1), mode="lines+markers",
                                 name="Directo con piso/cielo", line=dict(color="#00D4FF", width=3), marker=dict(size=6)))
        fig.add_trace(go.Scatter(x=freqs, y=np.round(lnT, 1), mode="lines+markers",
                                 name="L'nT", line=dict(color="#00E08A", width=3), marker=dict(size=6)))
        fig.add_trace(go.Scatter(x=freqs, y=np.round(delta_piso, 1), mode="lines",
                                 name="ΔL piso", line=dict(color="#FF8A1F", width=2, dash="dash")))

        if modo_impacto == "ISO 12354-2" and active_flank_names:
            fig.add_trace(go.Scatter(x=freqs, y=np.round(ln_total, 1), mode="lines",
                                     name="Total con flancos", line=dict(color="#C084FC", width=3, dash="dot")))

        fig.update_xaxes(
            type="log",
            title="Frecuencia [Hz]",
            tickmode="array",
            tickvals=[100, 125, 250, 500, 1000, 2000, 3150],
            ticktext=["100", "125", "250", "500", "1000", "2000", "3150"],
            gridcolor="rgba(255,255,255,.10)",
            tickfont=dict(size=15, color="#FFFFFF"),
            title_font=dict(size=16, color="#FFFFFF")
        )

        fig.update_yaxes(
            title="Nivel de impacto [dB]",
            gridcolor="rgba(255,255,255,.10)",
            tickfont=dict(size=15, color="#FFFFFF"),
            title_font=dict(size=16, color="#FFFFFF")
        )

        fig.update_layout(
            template="plotly_dark",
            height=540,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(8,18,32,.78)",
            font=dict(size=15, color="#EAF4FF"),
            margin=dict(l=60, r=20, t=90, b=60),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.12,
                xanchor="center",
                x=0.5,
                font=dict(size=13, color="#EAF4FF")
            )
        )

        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("<div class='sonara-card-title'>Tabla impacto</div>", unsafe_allow_html=True)

        df_imp = pd.DataFrame({
            "Frecuencia [Hz]": freqs.astype(int),
            "Ln,0 [dB]": np.round(ln0_curve, 1),
            "ΔL piso [dB]": np.round(delta_piso, 1),
            "ΔL cielo [dB]": np.round(delta_cielo, 1),
            "Ln total [dB]": np.round(ln_total, 1),
            "L'nT [dB]": np.round(lnT, 1),
        })

        table_fig = go.Figure(data=[go.Table(
            header=dict(
                values=["<b>f [Hz]</b>", "<b>Ln,0</b>", "<b>ΔL piso</b>", "<b>ΔL cielo</b>", "<b>Ln total</b>", "<b>L'nT</b>"],
                fill_color="#0F4C81",
                font=dict(color="white", size=14),
                align=["left", "right", "right", "right", "right", "right"],
                height=40,
                line_color="rgba(255,255,255,.15)"
            ),
            cells=dict(
                values=[
                    df_imp["Frecuencia [Hz]"],
                    df_imp["Ln,0 [dB]"],
                    df_imp["ΔL piso [dB]"],
                    df_imp["ΔL cielo [dB]"],
                    df_imp["Ln total [dB]"],
                    df_imp["L'nT [dB]"],
                ],
                fill_color=[
                    ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df_imp))],
                    ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df_imp))],
                    ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df_imp))],
                    ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df_imp))],
                    ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df_imp))],
                    ["#07111d" if i % 2 == 0 else "#0B1624" for i in range(len(df_imp))],
                ],
                font=dict(color="#FFFFFF", size=13),
                align=["left", "right", "right", "right", "right", "right"],
                height=30,
                line_color="rgba(255,255,255,.08)"
            )
        )])

        table_fig.update_layout(height=540, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(table_fig, use_container_width=True)

        st.download_button(
            label="⬇ Descargar CSV impacto",
            data=df_imp.to_csv(index=False).encode("utf-8"),
            file_name="sonara_impacto.csv",
            mime="text/csv",
            use_container_width=True
        )

        solution_save_widget({
            "nombre": f"Impacto L'nT,w {lntw} dB",
            "tipo_calculo": "Ruido de impacto",
            "resultado_label": f"L'nT,w {lntw} dB · CI {ci_t} · L'nT,w+CI {lntw + ci_t}",
            "lnw": float(lnw),
            "lntw": float(lntw),
            "ci": float(ci_t),
            "valor": float(lntw),
            "masa": None if masa_losa is None else round(float(masa_losa), 1),
            "espesor": None,
            "descripcion": f"{modo_impacto} · {tipo_piso} · {tipo_cielo}",
            "modo": modo_impacto,
            "tipo_piso": tipo_piso,
            "tipo_cielo": tipo_cielo,
            "ln0w": float(ln0w),
        }, key_prefix="save_impact")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class='sonara-card'>
            <div class='sonara-card-title'>Base técnica del módulo</div>
            <ul style='color:#DCEBFF;line-height:1.8;'>
                <li><b>ISO 12354-2:2017:</b> predicción de ruido de impacto entre recintos.</li>
                <li><b>ISO 717-2:2020:</b> evaluación ponderada Ln,w, L'nT,w y CI.</li>
                <li><b>ISO 16283-2:2020:</b> medición en terreno de ruido de impacto.</li>
                <li><b>ISO 10140-3:2021:</b> medición de laboratorio de aislamiento a ruido de impacto.</li>
                <li><b>Modelo físico:</b> piso flotante como sistema masa-resorte-masa mediante f0 = 1/(2π)√(s'/m').</li>
            </ul>
            <div class='result-note' style='margin-top:14px;'>
                Esta implementación es Nivel 1–2/ISO preliminar: útil para diseño preliminar y docencia.
                Para certificación o informe formal se requiere validar con datos de ensayo y norma completa.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# CUBICACIÓN Y OPTIMIZADOR IA
# =========================================================

def sonara_cost_db():
    """
    Costos desde el módulo Materiales.
    Fallback: si no existe un ítem, usa precio 0.
    """
    mats = material_db()
    costs = {}

    for nombre, data in mats.items():
        costs[nombre] = {
            "unidad": data.get("unidad", "m²"),
            "precio": float(data.get("precio", 0.0) or 0.0),
        }

    for nombre, unidad in [
        ("Lana mineral 40 kg/m³", "m²"),
        ("Lana mineral 60 kg/m³", "m²"),
        ("Lana mineral 80 kg/m³", "m²"),
        ("Montante 60", "ml"),
        ("Montante 90", "ml"),
        ("Solera", "ml"),
        ("Tornillos", "un"),
        ("Sellos / cinta / masilla", "m²"),
        ("Mano de obra referencial", "m²"),
    ]:
        costs.setdefault(nombre, {"unidad": unidad, "precio": 0.0})

    return costs


def layer_mass(layer):
    mat = layer["material"]
    esp = float(layer["espesor"]) / 1000.0
    return float(mat["dens"]) * esp


def system_mass(layers_left, layers_right=None):
    total = sum(layer_mass(x) for x in layers_left)
    if layers_right:
        total += sum(layer_mass(x) for x in layers_right)
    return total


def system_thickness_simple(layers):
    return sum(float(x["espesor"]) for x in layers)


def system_thickness_double(layers_left, layers_right, camara_mm):
    return system_thickness_simple(layers_left) + float(camara_mm) + system_thickness_simple(layers_right)


def layer_area_qty(area, n_couches=1, waste=0.10):
    return float(area) * int(n_couches) * (1.0 + float(waste))


def boards_qty(area_placas, board_w=1.2, board_h=2.4):
    board_area = max(board_w * board_h, 0.1)
    return int(np.ceil(float(area_placas) / board_area))


def studs_qty(largo, alto, separacion=0.6, config="Montante simple"):
    n = int(np.ceil(float(largo) / max(float(separacion), 0.1))) + 1
    factor = 2 if config in ["Montantes independientes", "Doble estructura"] else 1
    montantes_un = n * factor
    montantes_ml = montantes_un * float(alto)
    soleras_ml = 2.0 * float(largo) * factor
    return montantes_un, montantes_ml, soleras_ml


def estimate_cubicacion_tabique(
    layers_left,
    layers_right,
    area,
    largo,
    alto,
    camara,
    configuracion="Montante simple",
    absorbente_tipo="Sin absorbente",
    waste=0.10,
    separacion_montantes=0.6,
    incluir_mano_obra=True
):
    costs = sonara_cost_db()
    rows = []

    def add_row(item, unidad, cantidad, precio_unit):
        subtotal = float(cantidad) * float(precio_unit)
        rows.append({
            "Ítem": item,
            "Unidad": unidad,
            "Cantidad": round(float(cantidad), 2),
            "Precio unitario": round(float(precio_unit), 0),
            "Subtotal": round(subtotal, 0)
        })

    # Placas y capas
    all_layers = (layers_left or []) + (layers_right or [])
    for layer in all_layers:
        nombre = layer["nombre"]
        qty_area = layer_area_qty(area, 1, waste)
        precio = costs.get(nombre, {"precio": 6500})["precio"]
        add_row(nombre, "m²", qty_area, precio)

    # Planchas totales aproximadas
    area_placas = sum(layer_area_qty(area, 1, waste) for _ in all_layers)
    if area_placas > 0:
        add_row("Planchas 1,20 x 2,40 m", "un", boards_qty(area_placas), 0)

    # Montantes / soleras
    mont_un, mont_ml, sol_ml = studs_qty(largo, alto, separacion_montantes, configuracion)
    montante_tipo = "Montante 90" if camara >= 70 else "Montante 60"
    add_row(montante_tipo, "ml", mont_ml, costs[montante_tipo]["precio"])
    add_row("Solera", "ml", sol_ml, costs["Solera"]["precio"])

    # Lana
    if absorbente_tipo != "Sin absorbente":
        precio_lana = costs.get(absorbente_tipo, costs["Lana mineral 60 kg/m³"])["precio"]
        add_row(absorbente_tipo, "m²", layer_area_qty(area, 1, waste), precio_lana)

    # Tornillos / sellos
    add_row("Tornillos", "un", area * max(len(all_layers), 1) * 35, costs["Tornillos"]["precio"])
    add_row("Sellos / cinta / masilla", "m²", area, costs["Sellos / cinta / masilla"]["precio"])

    if incluir_mano_obra:
        add_row("Mano de obra referencial", "m²", area, costs["Mano de obra referencial"]["precio"])

    df = pd.DataFrame(rows)
    total = float(df["Subtotal"].sum()) if not df.empty else 0.0
    return df, total


def build_candidate_systems(mats, objetivo_rw, max_espesor, max_masa, area, prioridad):
    """
    Generador inicial de alternativas.
    Prueba combinaciones típicas de tabiques livianos con WALLS.
    """
    paneles = [
        k for k, v in mats.items()
        if v.get("grupo") == "panel"
        and not any(raw in k.lower() for raw in ["acero", "aluminio", "plomo", "cobre", "hormigón", "albañilería"])
    ]

    preferred = [
        "Placa de yeso-cartón estándar",
        "Placa de yeso-cartón alta densidad",
        "Fibrocemento",
        "OSB / tablero madera",
        "Tablero liviano",
    ]
    materials = [x for x in preferred if x in mats] + [x for x in paneles if x not in preferred][:3]

    camaras = [48, 70, 90]
    configs = ["Montante simple", "Montantes independientes", "Doble estructura"]
    absorbentes = ["Sin absorbente", "Lana mineral 40 kg/m³", "Lana mineral 60 kg/m³"]
    layer_counts = [1, 2]

    fine_freqs = np.linspace(45, 6000, 1191)
    results = []

    for mat_a in materials:
        for mat_b in materials:
            for n_left in layer_counts:
                for n_right in layer_counts:
                    for camara in camaras:
                        for config in configs:
                            for abs_tipo in absorbentes:
                                layers_left = [{
                                    "nombre": mat_a,
                                    "material": mats[mat_a],
                                    "espesor": float(mats[mat_a]["espesor"])
                                } for _ in range(n_left)]

                                layers_right = [{
                                    "nombre": mat_b,
                                    "material": mats[mat_b],
                                    "espesor": float(mats[mat_b]["espesor"])
                                } for _ in range(n_right)]

                                espesor_total = system_thickness_double(layers_left, layers_right, camara)
                                masa_total = system_mass(layers_left, layers_right)

                                if espesor_total > max_espesor or masa_total > max_masa:
                                    continue

                                try:
                                    tl_fine, masa_calc, fc, f0, fl = walls_double_multilayer_tl(
                                        layers_left,
                                        layers_right,
                                        camara,
                                        fine_freqs,
                                        configuracion=config,
                                        absorbente_tipo=abs_tipo,
                                        distancia_fijaciones_mm=600.0
                                    )
                                    third_freqs, tl_third = third_octave_from_fine(fine_freqs, tl_fine)
                                    rw, c, ctr = iso717_rw_simple(third_freqs, tl_third)
                                except Exception:
                                    continue

                                cub_df, costo = estimate_cubicacion_tabique(
                                    layers_left,
                                    layers_right,
                                    area=area,
                                    largo=max(area / 2.4, 1.0),
                                    alto=2.4,
                                    camara=camara,
                                    configuracion=config,
                                    absorbente_tipo=abs_tipo,
                                    waste=0.10,
                                    incluir_mano_obra=True
                                )

                                cumple = rw >= objetivo_rw

                                if prioridad == "Menor costo":
                                    score = costo + max(0, objetivo_rw - rw) * 1e7
                                elif prioridad == "Menor espesor":
                                    score = espesor_total * 1e6 + costo * 0.05 + max(0, objetivo_rw - rw) * 1e7
                                elif prioridad == "Menor peso":
                                    score = masa_total * 1e6 + costo * 0.05 + max(0, objetivo_rw - rw) * 1e7
                                else:
                                    score = -rw * 1e6 + costo * 0.05

                                name = f"{n_left}x {mat_a} + {camara} mm + {n_right}x {mat_b}"

                                results.append({
                                    "Solución": name,
                                    "Configuración": config,
                                    "Absorbente": abs_tipo,
                                    "Rw": int(rw),
                                    "C": int(c),
                                    "Ctr": int(ctr),
                                    "Espesor [mm]": round(espesor_total, 1),
                                    "Masa [kg/m²]": round(masa_total, 1),
                                    "Costo estimado": round(costo, 0),
                                    "Cumple": "Sí" if cumple else "No",
                                    "Score": score,
                                    "layers_left": layers_left,
                                    "layers_right": layers_right,
                                    "camara": camara,
                                    "cub_df": cub_df
                                })

    results = sorted(results, key=lambda x: x["Score"])
    return results


def ai_recommendation_text(best, objetivo_rw, prioridad):
    if not best:
        return "No se encontraron soluciones que cumplan las restricciones. Aumenta espesor máximo, masa máxima o reduce el Rw objetivo."

    cumple = best["Rw"] >= objetivo_rw
    margen = best["Rw"] - objetivo_rw

    if cumple:
        estado = f"cumple el objetivo con un margen de {margen:.0f} dB"
    else:
        estado = f"no alcanza el objetivo; faltan {abs(margen):.0f} dB"

    return (
        f"La alternativa recomendada es **{best['Solución']}**, con configuración **{best['Configuración']}** "
        f"y absorbente **{best['Absorbente']}**. Obtiene **Rw = {best['Rw']} dB**, por lo que {estado}. "
        f"Según la prioridad seleccionada (**{prioridad}**), esta solución presenta una buena relación entre desempeño, "
        f"espesor ({best['Espesor [mm]']} mm), masa ({best['Masa [kg/m²]']} kg/m²) y costo estimado."
    )




def is_massive_or_simple_solution(sol):
    """
    Define cuándo una solución NO debe cubicarse como tabique liviano con montantes/soleras.
    Ejemplos: hormigón, albañilería, acero, vidrio, panel simple masivo.
    """
    if not sol:
        return False

    desc = (str(sol.get("descripcion", "")) + " " + str(sol.get("tipo_elemento", "")) + " " + str(sol.get("tipo_calculo", ""))).lower()

    massive_terms = [
        "hormigón", "hormigon", "albañilería", "albanileria",
        "bloque", "ladrillo", "acero", "vidrio", "ventana"
    ]

    if any(t in desc for t in massive_terms):
        return True

    layers_right = sol.get("layers_right", []) or []
    layers_left = sol.get("layers_left", []) or []

    all_names = " ".join([str(x.get("nombre", "")) for x in layers_left + layers_right]).lower()
    if any(t in all_names for t in massive_terms):
        return True

    # Panel simple guardado: no debe agregar montantes/soleras si no hay segunda hoja.
    if layers_left and not layers_right:
        return True

    return False


def estimate_cubicacion_por_capas(layers_left, layers_right, area, waste=0.10, incluir_sellos=True, incluir_mano_obra=True):
    """
    Cubicación genérica por capas/materiales.
    No agrega montantes, soleras, tornillos ni placas tipo tabique liviano.
    Sirve para hormigón, albañilería, vidrio, acero, panel simple o soluciones masivas.
    """
    costs = sonara_cost_db()
    rows = []

    def add_row(item, unidad, cantidad, precio_unit):
        cantidad = float(cantidad)
        precio_unit = float(precio_unit or 0)
        rows.append({
            "Ítem": item,
            "Unidad": unidad,
            "Cantidad": round(cantidad, 2),
            "Precio unitario": round(precio_unit, 0),
            "Subtotal": round(cantidad * precio_unit, 0)
        })

    all_layers = (layers_left or []) + (layers_right or [])

    for layer in all_layers:
        nombre = layer.get("nombre", "Material")
        mat = layer.get("material", {})
        unidad = mat.get("unidad", "m²") or "m²"
        precio = costs.get(nombre, {"precio": mat.get("precio", 0)}).get("precio", mat.get("precio", 0))
        qty = layer_area_qty(area, 1, waste)

        if unidad.lower() in ["m2", "m²"]:
            add_row(nombre, "m²", qty, precio)
        else:
            add_row(nombre, unidad, qty, precio)

    if incluir_sellos:
        add_row("Sellos / tratamiento perimetral", "m", 0, 0)

    if incluir_mano_obra:
        precio_mo = costs.get("Mano de obra referencial", {"precio": 8500})["precio"]
        add_row("Mano de obra referencial", "m²", area, precio_mo)

    df = pd.DataFrame(rows)
    total = float(df["Subtotal"].sum()) if not df.empty else 0.0
    return df, total


def normalize_cubicacion_df(df):
    """
    Limpia y recalcula subtotal desde Cantidad x Precio unitario.
    Permite que el usuario agregue/edite ítems manualmente.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["Ítem", "Unidad", "Cantidad", "Precio unitario", "Subtotal"]), 0.0

    df = df.copy()
    for col in ["Ítem", "Unidad", "Cantidad", "Precio unitario", "Subtotal"]:
        if col not in df.columns:
            df[col] = ""

    df = df[["Ítem", "Unidad", "Cantidad", "Precio unitario", "Subtotal"]].copy()

    def num(x):
        try:
            if x == "" or pd.isna(x):
                return 0.0
            return float(x)
        except Exception:
            return 0.0

    df["Cantidad"] = df["Cantidad"].apply(num)
    df["Precio unitario"] = df["Precio unitario"].apply(num)
    df["Subtotal"] = (df["Cantidad"] * df["Precio unitario"]).round(0)

    # Permite mantener una fila manual con subtotal si cantidad/precio son 0 y subtotal fue ingresado.
    total = float(df["Subtotal"].sum()) if "Subtotal" in df.columns else 0.0
    return df, total


def update_solution_cubicacion_in_project(solution_id, requirement_id, cubicacion):
    """
    Persiste la cubicación dentro de la solución guardada del proyecto activo.
    """
    pid, p = active_project()
    if not pid or not p or not solution_id:
        return False

    projects = load_projects()
    if pid not in projects:
        return False

    reqs = project_requirements(projects[pid])
    updated = False

    for r in reqs:
        if requirement_id and r.get("id") != requirement_id:
            continue
        for s in r.get("soluciones", []):
            if s.get("id") == solution_id:
                s["cubicacion"] = cubicacion
                updated = True
                break

    if updated:
        projects[pid]["requerimientos"] = reqs
        projects[pid]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_projects(projects)

    return updated


def solution_cost(sol):
    try:
        cub = sol.get("cubicacion", {}) if isinstance(sol, dict) else {}
        return float(cub.get("total", 0) or 0)
    except Exception:
        return 0.0


def reconstruct_layers_from_solution(layer_list, mats):
    """
    Reconstruye capas guardadas en una solución.
    Usa el nombre del material para recuperar precio/parámetros desde la biblioteca actual.
    """
    layers = []
    for item in layer_list or []:
        nombre = str(item.get("nombre", "")).strip()
        mat = dict(mats.get(nombre, {}))
        if not mat:
            # fallback si el material no existe en la biblioteca
            dens = float(item.get("densidad", 0) or 0)
            esp = float(item.get("espesor_mm", 0) or 0)
            mat = {
                "tipo": "placa",
                "grupo": "panel",
                "espesor": esp,
                "dens": dens,
                "E": 0,
                "eta": 0,
                "color": "#9CA3AF",
                "unidad": "m²",
                "precio": 0,
                "proveedor": "No encontrado",
                "activo": True,
            }
        layers.append({
            "nombre": nombre or "Material no identificado",
            "material": mat,
            "espesor": float(item.get("espesor_mm", mat.get("espesor", 0)) or 0),
        })
    return layers


def selected_solution_label(sol, req=None):
    if not sol:
        return "Sin solución seleccionada"
    if req:
        em = req.get("recinto_emisor", "") or "Sin emisor"
        re_ = req.get("recinto_receptor", "") or "Sin receptor"
        elem = req.get("tipo_elemento", "")
        return f"{sol.get('nombre','Solución')} · {em} → {re_} · {elem}"
    return sol.get("nombre", "Solución")


def get_or_select_solution_for_cubicacion():
    """
    Devuelve solución y requerimiento para cubicación.
    Si no hay solución enviada desde Soluciones, permite elegir una desde el proyecto activo.
    """
    sol = st.session_state.get("selected_solution_for_cubicacion")
    req = st.session_state.get("selected_requirement_for_cubicacion")
    if sol:
        return sol, req

    pid, p = active_project()
    if not p:
        return None, None

    options = []
    for r in project_requirements(p):
        for s in r.get("soluciones", []):
            options.append((s, r, selected_solution_label(s, r)))

    if not options:
        return None, None

    labels = [x[2] for x in options]
    selected = st.selectbox(
        "Selecciona una solución guardada para cubicar",
        labels,
        key="cub_select_solution_from_project"
    )
    idx = labels.index(selected)
    sol, req, _ = options[idx]
    st.session_state["selected_solution_for_cubicacion"] = sol
    st.session_state["selected_requirement_for_cubicacion"] = req
    return sol, req


def component_cubicacion_table(sol, area_total, waste=0.10):
    """
    Cubicación simple de soluciones compuestas.
    Para ventanas/puertas se calcula por m²; para paramento opaco se informa como ítem.
    Los precios unitarios pueden completarse luego en biblioteca de componentes.
    """
    rows = []
    total = 0
    comps = sol.get("componentes", []) or []

    for c in comps:
        area = float(c.get("area", 0) or 0)
        nombre = c.get("nombre", "Componente")
        tipo = c.get("tipo", "Componente")
        r = c.get("r", "")
        qty = area * (1 + waste)
        unit_price = 0
        subtotal = qty * unit_price
        total += subtotal
        rows.append({
            "Ítem": f"{nombre} ({tipo}, R {r} dB)",
            "Unidad": "m²",
            "Cantidad": round(qty, 2),
            "Precio unitario": unit_price,
            "Subtotal": round(subtotal, 0),
        })

    if not rows:
        rows.append({
            "Ítem": "Solución compuesta sin componentes cubicables",
            "Unidad": "",
            "Cantidad": "",
            "Precio unitario": "",
            "Subtotal": 0,
        })

    return pd.DataFrame(rows), total



# =========================================================
# SONARA 1.2.2 - LIMPIEZA DE ÍTEMS DE CUBICACIÓN
# =========================================================

def sonara_fix_cubicacion_item_name(item, precio=0):
    """
    Corrige nombres heredados tipo 'Material no identificado'
    usando precio unitario referencial de biblioteca SONARA.
    """
    try:
        item_txt = str(item or "")
        precio = sonara_safe_float(precio, 0)

        if "Material no identificado" not in item_txt:
            return item_txt

        # Matches por precios base de materiales SONARA
        if abs(precio - 6500) < 1:
            return "Lana mineral 60 kg/m³"
        if abs(precio - 5200) < 1:
            return "Lana mineral 40 kg/m³"
        if abs(precio - 8500) < 1:
            return "Lana mineral 80 kg/m³"
        if abs(precio - 4500) < 1:
            return "Placa de yeso-cartón estándar"
        if abs(precio - 6200) < 1:
            return "Placa de yeso-cartón alta densidad"
        if abs(precio - 1900) < 1:
            return "Montante 90"
        if abs(precio - 1400) < 1:
            return "Montante 60"
        if abs(precio - 1300) < 1:
            return "Solera"
        if abs(precio - 900) < 1:
            return "Sellos / cinta / masilla"
        if abs(precio - 18) < 1:
            return "Tornillos"

        return item_txt
    except Exception:
        return str(item or "")


def sonara_clean_cubicacion_dataframe(df):
    """
    Limpia la tabla de cubicación antes de mostrarla/guardarla.
    También recalcula subtotales cuando existen Cantidad y Precio unitario.
    """
    try:
        if not isinstance(df, pd.DataFrame) or df.empty:
            return df

        df = df.copy()

        if "Ítem" in df.columns:
            if "Precio unitario" in df.columns:
                df["Ítem"] = df.apply(
                    lambda row: sonara_fix_cubicacion_item_name(
                        row.get("Ítem", ""),
                        row.get("Precio unitario", 0)
                    ),
                    axis=1
                )
            else:
                df["Ítem"] = df["Ítem"].astype(str)

        if all(c in df.columns for c in ["Cantidad", "Precio unitario", "Subtotal"]):
            df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0)
            df["Precio unitario"] = pd.to_numeric(df["Precio unitario"], errors="coerce").fillna(0)
            df["Subtotal"] = (df["Cantidad"] * df["Precio unitario"]).round(0)

        return df

    except Exception:
        return df


def app_cubicacion():
    st.markdown("<h2 style='color:#FFFFFF;margin-bottom:18px;'>Cubicación</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='result-note'>Cubicación asociada a la solución diseñada o seleccionada del proyecto. No vuelve a diseñar el tabique: usa la composición guardada en la solución.</div>",
        unsafe_allow_html=True
    )

    sol, req = get_or_select_solution_for_cubicacion()

    if not sol:
        st.warning("No hay solución seleccionada para cubicación. Ve a Proyecto → Soluciones, elige una solución y presiona 'Cubicar'.")
        return

    mats = material_db()
    tipo_calculo = str(sol.get("tipo_calculo", ""))
    nombre_solucion = sol.get("nombre", "Solución acústica")
    resultado = sol.get("resultado_label", "")
    req_label = ""
    if req:
        em = req.get("recinto_emisor", "") or "Sin emisor"
        rec = req.get("recinto_receptor", "") or "Sin receptor"
        elem = req.get("tipo_elemento", "")
        req_label = f"{em} → {rec} · {elem}"

    st.markdown(
        f"""
        <div class='project-flow-card'>
            <div class='project-flow-title'>Cubicando solución guardada</div>
            <div class='project-flow-text'>
            <b>{nombre_solucion}</b><br>
            {req_label}<br>
            Resultado de diseño: <b>{resultado}</b><br>
            Tipo de cálculo: <b>{tipo_calculo}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_in, col_out = st.columns([0.88, 1.35], gap="large")

    with col_in:
        st.markdown("<div class='sonara-card-title'>Geometría real de obra</div>", unsafe_allow_html=True)
        codigo_partida = st.text_input("Código / partida", value=req.get("elemento", "Partida acústica") if req else "Partida acústica", key="cub_codigo_partida")
        largo = st.number_input("Largo del elemento [m]", value=5.0, min_value=0.1, step=0.5, key="cub_largo_real")
        alto = st.number_input("Alto del elemento [m]", value=2.4, min_value=0.1, step=0.1, key="cub_alto_real")
        cantidad = st.number_input("Cantidad de elementos iguales", value=1, min_value=1, max_value=500, step=1, key="cub_cantidad_elementos")
        area_bruta = largo * alto * cantidad

        st.markdown("<div class='sonara-card-title'>Vanos a descontar</div>", unsafe_allow_html=True)
        incluir_vanos = st.checkbox("Descontar puertas/ventanas", value=False, key="cub_desc_vanos")
        area_vanos = 0.0

        if incluir_vanos:
            n_puertas = st.number_input("N° puertas", value=0, min_value=0, max_value=100, step=1, key="cub_n_puertas")
            ancho_puerta = st.number_input("Ancho puerta tipo [m]", value=0.8, min_value=0.1, step=0.1, key="cub_ancho_puerta")
            alto_puerta = st.number_input("Alto puerta tipo [m]", value=2.0, min_value=0.5, step=0.1, key="cub_alto_puerta")

            n_ventanas = st.number_input("N° ventanas", value=0, min_value=0, max_value=200, step=1, key="cub_n_ventanas")
            ancho_ventana = st.number_input("Ancho ventana tipo [m]", value=1.2, min_value=0.1, step=0.1, key="cub_ancho_ventana")
            alto_ventana = st.number_input("Alto ventana tipo [m]", value=1.0, min_value=0.1, step=0.1, key="cub_alto_ventana")

            area_vanos = (
                n_puertas * ancho_puerta * alto_puerta
                + n_ventanas * ancho_ventana * alto_ventana
            )

        area = max(area_bruta - area_vanos, 0.1)
        perdida = st.slider("Pérdida de material [%]", min_value=0, max_value=30, value=10, key="cub_perdida_solucion") / 100.0

    # Cubicación según tipo de solución guardada
    cubicacion_tipo = "Tabique liviano"
    if sol.get("componentes"):
        cubicacion_tipo = "Solución compuesta"
        df, total = component_cubicacion_table(sol, area, waste=perdida)
        masa = sol.get("masa")
        espesor = sol.get("espesor")
        masa_txt = "-" if masa is None else f"{float(masa):.1f}"
        esp_txt = "-" if espesor is None else f"{float(espesor):.0f}"
    else:
        layers_left = reconstruct_layers_from_solution(sol.get("layers_left", []), mats)
        layers_right = reconstruct_layers_from_solution(sol.get("layers_right", []), mats)

        if not layers_left and not layers_right:
            st.error("La solución seleccionada no tiene capas guardadas para cubicación. Vuelve a guardar la solución desde Diseñar.")
            return

        camara = float(sol.get("camara", 70) or 70)
        config = sol.get("configuracion", "Montante simple") or "Montante simple"
        absorbente = sol.get("absorbente", "Sin absorbente") or "Sin absorbente"

        if is_massive_or_simple_solution(sol):
            cubicacion_tipo = "Por capas / solución masiva"
            df, total = estimate_cubicacion_por_capas(
                layers_left,
                layers_right,
                area,
                waste=perdida,
                incluir_sellos=True,
                incluir_mano_obra=True
            )
        else:
            cubicacion_tipo = "Tabique liviano con estructura"
            df, total = estimate_cubicacion_tabique(
                layers_left,
                layers_right,
                area,
                largo * cantidad,
                alto,
                camara,
                config,
                absorbente,
                waste=perdida
            )

        masa = sol.get("masa")
        if masa is None:
            masa = system_mass(layers_left, layers_right)
        espesor = sol.get("espesor")
        if espesor is None:
            if is_massive_or_simple_solution(sol):
                espesor = sum(float(x.get("espesor", 0) or 0) for x in layers_left + layers_right)
            else:
                espesor = system_thickness_double(layers_left, layers_right, camara)

        masa_txt = f"{float(masa):.1f}"
        esp_txt = f"{float(espesor):.0f}"

    with col_out:
        # Placeholder permite que las tarjetas se muestren arriba, aunque el total se calcule desde la tabla editable.
        cards_placeholder = st.empty()

        st.markdown("<div class='sonara-card-title'>Tabla editable de cubicación</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='result-note'>Tipo de cubicación detectado: <b>{cubicacion_tipo}</b>. Edita cantidades/precios o agrega partidas faltantes. Las tarjetas se actualizan al aplicar los cambios.</div>",
            unsafe_allow_html=True
        )

        df = sonara_clean_cubicacion_dataframe(df)

        df = sonara_clean_cubicacion_dataframe(df)

        df_edit = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key=f"cub_editor_{sol.get('id','sin_id')}",
            height=430,
            column_config={
                "Ítem": st.column_config.TextColumn("Ítem"),
                "Unidad": st.column_config.TextColumn("Unidad"),
                "Cantidad": st.column_config.NumberColumn("Cantidad", step=0.01),
                "Precio unitario": st.column_config.NumberColumn("Precio unitario", step=100),
                "Subtotal": st.column_config.NumberColumn("Subtotal", disabled=True),
            }
        )

        df_calc, total = normalize_cubicacion_df(df_edit)

        # Tarjetas actualizadas a partir de la única tabla editable
        cards_placeholder.markdown(
            f"""
            <div class='sonara-card' style='margin-bottom:16px;'>
                <div class='sonara-card-title'>Cubicación de: {nombre_solucion}</div>
                <p style='color:#DCEBFF;margin:0;'>
                Partida: <b>{codigo_partida}</b><br>
                Requerimiento: <b>{req_label}</b><br>
                Tipo cubicación: <b>{cubicacion_tipo}</b><br>
                Área bruta: <b>{area_bruta:.1f} m²</b> · Vanos descontados: <b>{area_vanos:.1f} m²</b> · Área neta: <b>{area:.1f} m²</b>
                </p>
            </div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
                <div class="result-card"><div class="result-label">Área neta</div><div class="result-value">{area:.1f}</div><div class="result-unit">m²</div></div>
                <div class="result-card"><div class="result-label">Masa</div><div class="result-value">{masa_txt}</div><div class="result-unit">kg/m²</div></div>
                <div class="result-card"><div class="result-label">Espesor</div><div class="result-value">{esp_txt}</div><div class="result-unit">mm</div></div>
                <div class="result-card"><div class="result-label">TOTAL</div><div class="result-value" style="font-size:34px;">${total:,.0f}</div><div class="result-unit">CLP</div></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # CSV con fila TOTAL, pero no se muestra como segunda tabla.
        df_export = pd.concat([
            df_calc,
            pd.DataFrame([{
                "Ítem": "TOTAL",
                "Unidad": "",
                "Cantidad": "",
                "Precio unitario": "",
                "Subtotal": round(total, 0)
            }])
        ], ignore_index=True)

        st.download_button(
            "⬇ Descargar cubicación CSV",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name="sonara_cubicacion_solucion.csv",
            mime="text/csv",
            use_container_width=True
        )

        if st.button("💾 Asociar cubicación a la solución", use_container_width=True, key="cub_save_to_solution"):
            cubicacion_payload = {
                "codigo_partida": codigo_partida,
                "tipo_cubicacion": cubicacion_tipo,
                "area_bruta": float(area_bruta),
                "area_vanos": float(area_vanos),
                "area_neta": float(area),
                "total": float(total),
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "items": df_calc.to_dict(orient="records"),
            }
            sol["cubicacion"] = cubicacion_payload
            st.session_state["selected_solution_for_cubicacion"] = sol

            req_id = req.get("id") if isinstance(req, dict) else None
            ok = update_solution_cubicacion_in_project(sol.get("id"), req_id, cubicacion_payload)

            if ok:
                st.success("Cubicación guardada dentro de la solución del proyecto.")
            else:
                st.warning("Cubicación asociada en sesión, pero no se pudo persistir en el proyecto. Revisa que la solución tenga ID.")




# =========================================================
# SONARA 1.1.4 - OPTIMIZADOR PROGRESIVO RÁPIDO
# =========================================================

def sonara_layer_signature(layers):
    """Firma simple para cachear soluciones por capas."""
    sig = []
    try:
        for l in layers:
            mat = l.get("material", {})
            name = mat.get("nombre", "") if isinstance(mat, dict) else str(mat)
            esp = round(float(l.get("espesor", 0) or 0), 2)
            dens = l.get("densidad", "")
            sig.append(f"{name}:{esp}:{dens}")
    except Exception:
        pass
    return "|".join(sig)


def sonara_solution_signature(solution_dict):
    """Firma de una solución para evitar recalcular la misma variante."""
    try:
        return json.dumps(solution_dict, sort_keys=True, ensure_ascii=False, default=str)
    except Exception:
        return str(solution_dict)


@st.cache_data(show_spinner=False, max_entries=900)
def sonara_cached_score_variant(signature, variant_payload):
    """
    Cache liviano. El cálculo real se ejecuta fuera si no es posible serializar.
    Se mantiene para evitar repetir combinaciones exactas durante una sesión.
    """
    return signature


def sonara_estimate_mass_law_rw(masa_kg_m2):
    """
    Filtro rápido preliminar por ley de masa aproximada.
    No reemplaza WALLS; sirve para ordenar candidatos antes del cálculo preciso.
    """
    try:
        m = max(float(masa_kg_m2), 1.0)
        return 20.0 * np.log10(m) + 14.0
    except Exception:
        return 0.0


def sonara_get_material_by_keywords(materiales, keywords, fallback=None):
    """Busca un material en la biblioteca por palabras clave."""
    if not materiales:
        return fallback
    keys = list(materiales.keys())
    for kw in keywords:
        for k in keys:
            if kw.lower() in k.lower():
                return k
    return fallback or (keys[0] if keys else None)


def sonara_variant_cost_from_layers(layers, area_m2=1.0):
    """
    Estimación rápida de costo por capas, usando precio m² cuando exista.
    No incluye estructura fina salvo que esté en la capa.
    """
    total = 0.0
    try:
        for l in layers:
            mat = l.get("material", {})
            if isinstance(mat, dict):
                precio = float(mat.get("precio", 0) or 0)
            else:
                precio = 0.0
            total += precio * float(area_m2 or 1.0)
    except Exception:
        total = 0.0
    return float(total)


def sonara_layers_mass_thickness(layers):
    masa = 0.0
    esp = 0.0
    try:
        for l in layers:
            mat = l.get("material", {})
            e = float(l.get("espesor", 0) or 0)
            dens = float(l.get("densidad", mat.get("dens", 0) if isinstance(mat, dict) else 0) or 0)
            esp += e
            masa += dens * (e / 1000.0)
    except Exception:
        pass
    return float(masa), float(esp)


def sonara_build_variant_record(nombre, estrategia, layers_left, layers_right=None, camara_mm=0, absorbente_tipo="Sin absorbente", configuracion="Montante simple", area_m2=1.0):
    """Construye registro normalizado de variante candidata."""
    layers_left = [sonara_normalize_layer(l) for l in (layers_left or [])]
    layers_left = [l for l in layers_left if l]
    layers_right = [sonara_normalize_layer(l) for l in (layers_right or [])]
    layers_right = [l for l in layers_right if l]

    m1, e1 = sonara_layers_mass_thickness(layers_left)
    m2, e2 = sonara_layers_mass_thickness(layers_right)
    masa = m1 + m2
    espesor = e1 + e2 + sonara_safe_float(camara_mm, 0)
    costo = sonara_variant_cost_from_layers(layers_left, area_m2) + sonara_variant_cost_from_layers(layers_right, area_m2)

    return {
        "nombre": nombre,
        "estrategia": estrategia,
        "layers_left": layers_left,
        "layers_right": layers_right,
        "camara_mm": sonara_safe_float(camara_mm, 0),
        "absorbente_tipo": absorbente_tipo,
        "configuracion": configuracion,
        "masa": float(masa),
        "espesor": float(espesor),
        "costo_estimado": float(costo),
        "rw_preliminar": float(sonara_estimate_mass_law_rw(masa)),
    }


def sonara_safe_float(value, default=0.0):
    """Convierte números desde int/float/str con coma decimal, sin romper la app."""
    try:
        if value is None or value == "":
            return float(default)
        if isinstance(value, str):
            value = value.replace("$", "").replace("CLP", "").replace(" ", "").strip()
            if "," in value and "." in value:
                value = value.replace(".", "").replace(",", ".")
            elif "," in value:
                value = value.replace(",", ".")
        return float(value)
    except Exception:
        return float(default)


def sonara_first_material(materiales, keywords, fallback_keywords=None):
    """Devuelve (key, material) buscando por palabras clave."""
    materiales = materiales or {}
    all_keywords = list(keywords or []) + list(fallback_keywords or [])
    for kw in all_keywords:
        kwl = str(kw).lower()
        for k, v in materiales.items():
            if kwl in str(k).lower():
                return k, v
    if materiales:
        k = list(materiales.keys())[0]
        return k, materiales[k]
    return None, None


def sonara_normalize_layer(layer, materiales=None):
    """
    Normaliza una capa antigua/nueva a:
    {"material": dict, "espesor": mm, "densidad": kg/m3}
    """
    materiales = materiales or material_db()
    if not isinstance(layer, dict):
        return None

    mat = layer.get("material") or layer.get("mat") or layer.get("material_dict")
    if isinstance(mat, str):
        mat = materiales.get(mat, {"nombre": mat, "dens": 735, "E": 2550000000, "eta": 0.033, "precio": 0, "unidad": "m²"})
    elif isinstance(mat, dict):
        # asegurar nombre
        if "nombre" not in mat:
            mat = dict(mat)
            mat["nombre"] = mat.get("name", mat.get("material", "Material"))
    else:
        name = layer.get("nombre") or layer.get("name") or layer.get("material_nombre") or "Placa de yeso-cartón estándar"
        mat = materiales.get(str(name), None)
        if mat is None:
            _, mat = sonara_first_material(materiales, [str(name), "yeso", "hormig", "vidrio"])
        mat = dict(mat or {"nombre": str(name), "dens": 735, "E": 2550000000, "eta": 0.033, "precio": 0, "unidad": "m²"})
        mat.setdefault("nombre", str(name))

    esp = (
        layer.get("espesor")
        if layer.get("espesor") not in [None, ""]
        else layer.get("espesor_mm", layer.get("thickness", layer.get("e", mat.get("espesor", 15))))
    )
    dens = (
        layer.get("densidad")
        if layer.get("densidad") not in [None, ""]
        else layer.get("dens", mat.get("dens", 735))
    )

    esp = max(sonara_safe_float(esp, mat.get("espesor", 15)), 0.1)
    dens = max(sonara_safe_float(dens, mat.get("dens", 735)), 1.0)

    return {"material": mat, "espesor": esp, "densidad": dens}


def sonara_extract_layers_from_solution(solution, materiales=None):
    """
    Extrae capas desde cualquier estructura guardada por SONARA.
    Soporta: layers_left/right, layers, capas, capas_izq/der, composición textual.
    """
    materiales = materiales or material_db()
    if not isinstance(solution, dict):
        return [], []

    left_keys = ["layers_left", "capas_izq", "capas_left", "left_layers", "layers", "capas"]
    right_keys = ["layers_right", "capas_der", "capas_right", "right_layers"]

    left, right = [], []
    for k in left_keys:
        v = solution.get(k)
        if isinstance(v, list) and v:
            left = [sonara_normalize_layer(x, materiales) for x in v]
            left = [x for x in left if x]
            break

    for k in right_keys:
        v = solution.get(k)
        if isinstance(v, list) and v:
            right = [sonara_normalize_layer(x, materiales) for x in v]
            right = [x for x in right if x]
            break

    # Algunas soluciones guardan lista de dicts en composicion/capas_json como texto
    if not left:
        for k in ["capas_json", "layers_json"]:
            raw = solution.get(k)
            if isinstance(raw, str) and raw.strip().startswith("["):
                try:
                    arr = json.loads(raw)
                    left = [sonara_normalize_layer(x, materiales) for x in arr]
                    left = [x for x in left if x]
                    break
                except Exception:
                    pass

    return left, right


def sonara_solution_cost_for_report(sol):
    """
    Costo robusto para informe:
    1) cubicacion.total
    2) suma items de cubicación
    3) costo_estimado/costo
    """
    try:
        if not isinstance(sol, dict):
            return 0.0
        cub = sol.get("cubicacion", {})
        if isinstance(cub, dict) and cub:
            if cub.get("total") not in [None, ""]:
                return sonara_safe_float(cub.get("total"), 0)
            total = 0.0
            for it in cub.get("items", []) or []:
                subtotal = it.get("Subtotal", it.get("subtotal", None))
                if subtotal not in [None, ""]:
                    total += sonara_safe_float(subtotal, 0)
                else:
                    total += sonara_safe_float(it.get("Cantidad", it.get("cantidad", 0)), 0) * sonara_safe_float(it.get("Precio unitario", it.get("precio_unitario", 0)), 0)
            if total > 0:
                return float(total)
        return sonara_safe_float(sol.get("costo_estimado", sol.get("costo", 0)), 0)
    except Exception:
        return 0.0


def sonara_base_layers_from_context(solution=None, materiales=None):
    """
    Extrae o reconstruye las capas base de una solución guardada.

    Corrección clave:
    si la solución de proyecto no trae layers_left/layers_right, SONARA reconstruye
    una base desde nombre/tipo/composición/masa/espesor para evitar Rw=0.
    """
    materiales = materiales or material_db()

    left, right = sonara_extract_layers_from_solution(solution, materiales)
    if left:
        return left

    if isinstance(solution, dict):
        nombre = str(solution.get("nombre", solution.get("solution_name", "")))
        tipo = str(solution.get("tipo", solution.get("tipo_calculo", "")))
        comp = str(solution.get("composicion", solution.get("composition", "")))
        texto = f"{nombre} {tipo} {comp}".lower()
        espesor = sonara_safe_float(solution.get("espesor", solution.get("espesor_mm", 0)), 0)
        masa = sonara_safe_float(solution.get("masa", solution.get("masa_kg_m2", 0)), 0)
    else:
        texto = ""
        espesor = 0
        masa = 0

    # elegir material coherente
    if "hormig" in texto:
        _, mat = sonara_first_material(materiales, ["hormig"])
    elif "albañ" in texto or "alban" in texto or "ladrillo" in texto or "bloque" in texto:
        _, mat = sonara_first_material(materiales, ["alba", "bloque", "ladrillo"], ["hormig"])
    elif "vidrio" in texto or "ventana" in texto:
        _, mat = sonara_first_material(materiales, ["vidrio monolítico", "vidrio"])
    elif "madera" in texto or "osb" in texto:
        _, mat = sonara_first_material(materiales, ["osb", "madera"], ["yeso"])
    else:
        _, mat = sonara_first_material(materiales, ["yeso-cartón estándar", "yeso"], ["fibrocemento"])

    if mat is None:
        return []

    mat = dict(mat)
    mat.setdefault("nombre", "Material base")

    if espesor <= 0:
        espesor = sonara_safe_float(mat.get("espesor", 15), 15)

    dens = sonara_safe_float(mat.get("dens", 735), 735)
    if (dens <= 1 or dens == 735) and masa > 0 and espesor > 0:
        dens = masa / (espesor / 1000.0)

    return [{
        "material": mat,
        "espesor": max(float(espesor), 0.1),
        "densidad": max(float(dens), 1.0),
    }]


def sonara_generate_progressive_variants(base_solution=None, target_rw=45, max_espesor=150, max_masa=80, area_m2=1.0, modo="Rápido"):
    """
    Optimización progresiva rápida y robusta:
    1) aumentar masa/espesor;
    2) agregar capa;
    3) trasdosado con cámara + absorbente;
    4) desacople/doble estructura.
    """
    materiales = material_db()
    base_left = sonara_base_layers_from_context(base_solution, materiales)

    if not base_left:
        _, mat = sonara_first_material(materiales, ["yeso-cartón estándar", "yeso"])
        if mat:
            base_left = [{"material": mat, "espesor": sonara_safe_float(mat.get("espesor", 15), 15), "densidad": sonara_safe_float(mat.get("dens", 735), 735)}]

    if not base_left:
        return []

    mat_yeso_key = sonara_get_material_by_keywords(materiales, ["yeso-cartón estándar", "yeso"])
    mat_hd_key = sonara_get_material_by_keywords(materiales, ["alta densidad", "habito"], fallback=mat_yeso_key)
    mat_lana40_key = sonara_get_material_by_keywords(materiales, ["lana mineral 40"], fallback=None)
    mat_lana60_key = sonara_get_material_by_keywords(materiales, ["lana mineral 60", "lana"], fallback=mat_lana40_key)

    candidates = []

    candidates.append(sonara_build_variant_record(
        "Solución base recalculada", "Base existente", base_left, [], 0, "Sin absorbente", "Montante simple", area_m2
    ))

    # 1. Agregar masa / espesor
    factors = [1.10, 1.20, 1.35] if modo == "Rápido" else [1.05, 1.10, 1.20, 1.35, 1.50]
    for factor in factors:
        new_layers = []
        for l in base_left:
            nl = dict(l)
            nl["espesor"] = round(sonara_safe_float(l.get("espesor", 0), 0) * factor, 1)
            new_layers.append(nl)
        candidates.append(sonara_build_variant_record(
            f"+ masa / espesor x{factor:.2f}", "1. Agregar masa a capas existentes", new_layers, [], 0, "Sin absorbente", "Montante simple", area_m2
        ))

    # 2. Agregar capa
    if mat_hd_key:
        hd = materiales[mat_hd_key]
        for esp in ([12.5, 15] if modo == "Rápido" else [10, 12.5, 15, 18]):
            new_layers = list(base_left) + [{"material": hd, "espesor": float(esp), "densidad": hd.get("dens", 786)}]
            candidates.append(sonara_build_variant_record(
                f"+ capa alta densidad {esp} mm", "2. Agregar nueva capa", new_layers, [], 0, "Sin absorbente", "Montante simple", area_m2
            ))

    if mat_yeso_key:
        gy = materiales[mat_yeso_key]
        for esp in ([15] if modo == "Rápido" else [12.5, 15]):
            new_layers = list(base_left) + [{"material": gy, "espesor": float(esp), "densidad": gy.get("dens", 735)}]
            candidates.append(sonara_build_variant_record(
                f"+ placa estándar {esp} mm", "2. Agregar nueva capa", new_layers, [], 0, "Sin absorbente", "Montante simple", area_m2
            ))

    # 3. Cámara + absorbente
    if mat_yeso_key:
        gy = materiales[mat_yeso_key]
        right = [{"material": gy, "espesor": 15.0, "densidad": gy.get("dens", 735)}]
        cams = [50, 70] if modo == "Rápido" else [40, 50, 70, 90]
        abs_opts = ["Lana mineral 60 kg/m³"] if modo == "Rápido" else ["Lana mineral 40 kg/m³", "Lana mineral 60 kg/m³", "Lana mineral 80 kg/m³"]
        for cam in cams:
            for abs_tipo in abs_opts:
                candidates.append(sonara_build_variant_record(
                    f"+ trasdosado cámara {cam} mm + {abs_tipo}",
                    "3. Cámara + absorbente",
                    base_left,
                    right,
                    cam,
                    abs_tipo,
                    "Montante simple",
                    area_m2
                ))

    # 4. Desacople
    if mat_hd_key:
        hd = materiales[mat_hd_key]
        right = [{"material": hd, "espesor": 15.0, "densidad": hd.get("dens", 786)}]
        confs = ["Montantes independientes"] if modo == "Rápido" else ["Montantes independientes", "Doble estructura"]
        for conf in confs:
            candidates.append(sonara_build_variant_record(
                f"{conf} + placa alta densidad",
                "4. Desacople estructural",
                base_left,
                right,
                70.0,
                "Lana mineral 60 kg/m³",
                conf,
                area_m2
            ))

    # Filtrar, pero no dejar vacío si las restricciones son demasiado duras.
    max_e = sonara_safe_float(max_espesor, 9999)
    max_m = sonara_safe_float(max_masa, 9999)

    filtered = [c for c in candidates if c.get("espesor", 0) <= max_e and c.get("masa", 0) <= max_m]
    if not filtered:
        filtered = candidates[:]

    target = sonara_safe_float(target_rw, 0)
    filtered = sorted(
        filtered,
        key=lambda x: (
            0 if x.get("rw_preliminar", 0) >= target else 1,
            abs(target - x.get("rw_preliminar", 0)),
            x.get("costo_estimado", 0),
            x.get("espesor", 0),
        )
    )

    limit = 20 if modo == "Rápido" else 60
    return filtered[:limit]


def sonara_precise_score_variant(variant):
    """
    Cálculo WALLS preciso solo para candidatas prefiltradas.
    No devuelve Rw=0 silencioso salvo que realmente no existan capas.
    """
    freqs_fine = np.linspace(50, 5000, 700)
    bands = np.array([50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000])

    variant = dict(variant)
    try:
        left = [sonara_normalize_layer(l) for l in variant.get("layers_left", [])]
        left = [l for l in left if l]
        right = [sonara_normalize_layer(l) for l in variant.get("layers_right", [])]
        right = [l for l in right if l]
        cam = sonara_safe_float(variant.get("camara_mm", 0), 0)

        if not left:
            raise ValueError("Variante sin capas base")

        if right and cam > 0:
            tl_fine, mt, fc, f0, fl = walls_double_multilayer_tl(
                left, right, cam, freqs_fine,
                configuracion=variant.get("configuracion", "Montante simple"),
                absorbente_tipo=variant.get("absorbente_tipo", "Sin absorbente"),
                distancia_fijaciones_mm=600.0,
            )
        else:
            tl_fine, mt, bt, eta, fc = walls_multilayer_tl(left, freqs_fine)

        f_bands, tl_bands = third_octave_from_fine(freqs_fine, tl_fine, bands)
        rw, c, ctr = iso717_rw_simple(f_bands, tl_bands)

        masa, esp_layers = sonara_layers_mass_thickness(left + right)
        espesor = esp_layers + cam

        variant["layers_left"] = left
        variant["layers_right"] = right
        variant["Rw"] = float(rw)
        variant["C"] = float(c)
        variant["Ctr"] = float(ctr)
        variant["Rw+C"] = float(rw + c)
        variant["Rw+Ctr"] = float(rw + ctr)
        variant["masa"] = float(masa)
        variant["espesor"] = float(espesor)
        variant["resultado"] = f"Rw {rw:.0f} dB; C {c:+.0f}; Ctr {ctr:+.0f}"
        return variant

    except Exception as e:
        # fallback acústico aproximado para no bloquear la optimización comercial
        masa = sonara_safe_float(variant.get("masa", 0), 0)
        if masa <= 0:
            masa, esp = sonara_layers_mass_thickness(variant.get("layers_left", []) + variant.get("layers_right", []))
        rw_est = max(0.0, sonara_estimate_mass_law_rw(masa) - 5.0)
        variant["Rw"] = float(round(rw_est, 1))
        variant["C"] = 0.0
        variant["Ctr"] = -2.0 if rw_est > 0 else 0.0
        variant["Rw+C"] = variant["Rw"] + variant["C"]
        variant["Rw+Ctr"] = variant["Rw"] + variant["Ctr"]
        variant["resultado"] = f"Estimado preliminar: {e}"
        return variant


def sonara_run_fast_optimizer(base_solution=None, target_rw=45, max_espesor=150, max_masa=80, area_m2=1.0, prioridad="Menor costo", modo="Rápido"):
    """
    Orquestador de optimización rápida robusto.
    Reconstruye capas cuando la solución guardada no trae estructura interna.
    """
    if base_solution is None or not isinstance(base_solution, dict):
        base_solution = {}

    variants = sonara_generate_progressive_variants(
        base_solution=base_solution,
        target_rw=target_rw,
        max_espesor=max_espesor,
        max_masa=max_masa,
        area_m2=area_m2,
        modo=modo,
    )

    scored = []
    seen = set()
    for v in variants:
        sig = sonara_solution_signature({
            "left": sonara_layer_signature(v.get("layers_left", [])),
            "right": sonara_layer_signature(v.get("layers_right", [])),
            "cam": v.get("camara_mm", 0),
            "abs": v.get("absorbente_tipo", ""),
            "conf": v.get("configuracion", ""),
        })
        if sig in seen:
            continue
        seen.add(sig)
        scored.append(sonara_precise_score_variant(v))

    target = sonara_safe_float(target_rw, 0)
    for s in scored:
        s["cumple"] = s.get("Rw", 0) >= target
        s["margen"] = s.get("Rw", 0) - target

    if prioridad == "Mayor desempeño":
        key = lambda x: (0 if x["cumple"] else 1, -x.get("Rw", 0), x.get("costo_estimado", 0))
    elif prioridad == "Menor espesor":
        key = lambda x: (0 if x["cumple"] else 1, x.get("espesor", 999), x.get("costo_estimado", 0))
    elif prioridad == "Menor masa":
        key = lambda x: (0 if x["cumple"] else 1, x.get("masa", 999), x.get("costo_estimado", 0))
    else:
        key = lambda x: (0 if x["cumple"] else 1, x.get("costo_estimado", 0), x.get("espesor", 999))

    return sorted(scored, key=key)


def sonara_safe_float(x, default=0.0):
    try:
        if x is None or x == "":
            return float(default)
        if isinstance(x, str):
            x = x.replace("$", "").replace(".", "").replace(",", ".").strip()
        return float(x)
    except Exception:
        return float(default)


def sonara_material_nombre(mat):
    if isinstance(mat, dict):
        return str(mat.get("nombre", mat.get("name", "Material")))
    return str(mat) if mat is not None else "Material"


def sonara_material_precio(mat):
    if isinstance(mat, dict):
        return sonara_safe_float(mat.get("precio", mat.get("price", 0)), 0)
    return 0.0


def sonara_material_unidad(mat):
    if isinstance(mat, dict):
        return str(mat.get("unidad", "m²") or "m²")
    return "m²"



# =========================================================
# SONARA 1.2.0 - CAPAS, CUBICACIÓN Y ESQUEMA VISUAL
# =========================================================


def sonara_layer_material_name(layer):
    """
    Nombre robusto de material para capas antiguas/nuevas.
    Evita 'Material no identificado' cruzando por nombre, precio, densidad y espesor.
    """
    if not isinstance(layer, dict):
        return "Material no identificado"

    mat = layer.get("material", {})

    if isinstance(mat, str) and mat.strip():
        return mat.strip()

    if isinstance(mat, dict):
        for k in ["nombre", "name", "material", "tipo", "label"]:
            val = mat.get(k)
            if val not in [None, ""]:
                txt = str(val).strip()
                if txt and txt.lower() not in ["material", "none", "nan", "{}"]:
                    return txt

    for k in ["nombre", "name", "material_nombre", "material", "tipo", "label"]:
        val = layer.get(k)
        if val not in [None, ""]:
            txt = str(val).strip()
            if txt and txt.lower() not in ["material", "none", "nan", "{}"]:
                return txt

    try:
        mats = material_db()
        source = mat if isinstance(mat, dict) else layer
        dens = sonara_safe_float(source.get("dens", source.get("densidad", layer.get("densidad", 0))), 0)
        esp = sonara_safe_float(layer.get("espesor", layer.get("espesor_mm", source.get("espesor", 0))), 0)
        precio = sonara_safe_float(source.get("precio", layer.get("precio", 0)), 0)

        best_name = None
        best_score = 1e9

        for name, ref in mats.items():
            ref_dens = sonara_safe_float(ref.get("dens", 0), 0)
            ref_esp = sonara_safe_float(ref.get("espesor", 0), 0)
            ref_precio = sonara_safe_float(ref.get("precio", 0), 0)

            score = 0.0
            if precio > 0 and ref_precio > 0:
                score += abs(ref_precio - precio) / 100.0
            else:
                score += 50

            if esp > 0 and ref_esp > 0:
                score += abs(ref_esp - esp) / 2.0

            if dens > 0 and ref_dens > 0:
                score += abs(ref_dens - dens) / 20.0

            if score < best_score:
                best_score = score
                best_name = name

        if best_name is not None and best_score < 60:
            return str(best_name)

    except Exception:
        pass

    return "Material no identificado"


def sonara_layer_material_price(layer):
    """Precio robusto de material/capa."""
    if not isinstance(layer, dict):
        return 0.0

    mat = layer.get("material", {})

    if isinstance(mat, dict):
        for k in ["precio", "price", "costo", "precio_unitario"]:
            val = mat.get(k)
            if val not in [None, ""]:
                return sonara_safe_float(val, 0)

    for k in ["precio", "price", "costo", "precio_unitario"]:
        val = layer.get(k)
        if val not in [None, ""]:
            return sonara_safe_float(val, 0)

    # Si no trae precio pero se reconoce nombre, buscar en biblioteca.
    try:
        name = sonara_layer_material_name(layer)
        mats = material_db()
        if name in mats:
            return sonara_safe_float(mats[name].get("precio", 0), 0)
    except Exception:
        pass

    return 0.0


def sonara_layer_material_unit(layer):
    """Unidad robusta de material/capa."""
    if not isinstance(layer, dict):
        return "m²"
    mat = layer.get("material", {})
    if isinstance(mat, dict):
        val = mat.get("unidad")
        if val not in [None, ""]:
            return str(val)
    val = layer.get("unidad")
    if val not in [None, ""]:
        return str(val)
    return "m²"


def sonara_layer_color(layer):
    """Color de capa para esquema visual."""
    if not isinstance(layer, dict):
        return "#9CA3AF"
    mat = layer.get("material", {})
    if isinstance(mat, dict) and mat.get("color"):
        return str(mat.get("color"))
    return "#9CA3AF"


def sonara_html_escape(txt):
    import html
    return html.escape(str(txt))



def sonara_draw_solution_html(solution):
    """
    Esquema visual SVG de solución. Retorna SVG completo para st.markdown(..., unsafe_allow_html=True).
    """
    if not isinstance(solution, dict):
        return ""

    layers_left = (
        solution.get("layers_left", [])
        or solution.get("capas_izq", [])
        or solution.get("layers", [])
        or solution.get("capas", [])
    )
    layers_right = solution.get("layers_right", []) or solution.get("capas_der", [])
    camara = sonara_safe_float(solution.get("camara_mm", solution.get("camara", 0)), 0)
    absorbente = solution.get("absorbente_tipo", "")

    if not layers_left and not layers_right:
        return ""

    blocks = []

    def add_layer(layer):
        nombre = sonara_layer_material_name(layer)
        esp = sonara_safe_float(layer.get("espesor", layer.get("espesor_mm", 0)) if isinstance(layer, dict) else 0, 0)
        color = sonara_layer_color(layer)
        width = int(max(26, min(90, esp * 2.2 if esp > 0 else 32)))
        label = f"{nombre} {esp:g} mm" if esp > 0 else nombre
        blocks.append({
            "type": "layer",
            "label": label,
            "width": width,
            "color": color,
        })

    for l in layers_left or []:
        add_layer(l)

    if camara > 0:
        label = f"Cámara {camara:g} mm"
        if absorbente:
            label += f" + {absorbente}"
        blocks.append({
            "type": "air",
            "label": label,
            "width": int(max(44, min(120, camara))),
            "color": "#FACC15",
        })

    for l in layers_right or []:
        add_layer(l)

    total_w = sum(b["width"] + 8 for b in blocks) + 40
    total_w = max(total_w, 520)
    height = 270
    x = 20
    svg_parts = []

    svg_parts.append(f'<rect x="0" y="0" width="{total_w}" height="{height}" rx="14" fill="#07111d" stroke="#2f80ed" stroke-opacity=".35" />')

    for b in blocks:
        w = b["width"]
        if b["type"] == "air":
            svg_parts.append(f'<rect x="{x}" y="45" width="{w}" height="175" rx="8" fill="#172554" stroke="#60A5FA" stroke-dasharray="6 5" stroke-width="2"/>')
            for lx in range(int(x)+6, int(x+w), 12):
                svg_parts.append(f'<line x1="{lx}" y1="50" x2="{lx-28}" y2="220" stroke="#FACC15" stroke-width="4" opacity=".75"/>')
        else:
            color = b.get("color", "#9CA3AF")
            svg_parts.append(f'<rect x="{x}" y="45" width="{w}" height="175" rx="8" fill="{color}" stroke="#E5E7EB" stroke-width="2"/>')
            svg_parts.append(f'<rect x="{x+3}" y="48" width="{max(w-6,1)}" height="169" rx="6" fill="white" opacity=".10"/>')

        label = sonara_html_escape(b["label"])
        cx = x + w / 2
        cy = 132
        svg_parts.append(
            f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" '
            f'transform="rotate(-90 {cx} {cy})" font-size="12" font-weight="800" '
            f'font-family="Inter, Arial" fill="#FFFFFF">{label}</text>'
        )
        x += w + 8

    svg_inner = "".join(svg_parts)
    return f"""
    <div class="sonara-card" style="margin-top:18px;">
        <div class="sonara-card-title">Esquema constructivo de la solución</div>
        <div style="overflow-x:auto;padding:10px;background:#07111d;border:1px solid rgba(71,166,255,.25);border-radius:14px;">
            <svg width="{total_w}" height="{height}" viewBox="0 0 {total_w} {height}" xmlns="http://www.w3.org/2000/svg">
                {svg_inner}
            </svg>
        </div>
    </div>
    """



def sonara_cubicacion_from_optimized_solution(opt_solution, area_m2=1.0):
    """
    Genera cubicación inicial editable para una solución optimizada.
    Identifica materiales por nombre, precio, densidad o espesor.
    """
    area = sonara_safe_float(area_m2, 1.0)
    items = []

    layers_left = opt_solution.get("layers_left", []) or opt_solution.get("capas_izq", []) or opt_solution.get("layers", []) or opt_solution.get("capas", [])
    layers_right = opt_solution.get("layers_right", []) or opt_solution.get("capas_der", [])

    for lado, layers in [("Lado 1", layers_left), ("Lado 2", layers_right)]:
        for layer in layers or []:
            if not isinstance(layer, dict):
                continue

            nombre = sonara_layer_material_name(layer)
            unidad = sonara_layer_material_unit(layer)
            precio = sonara_layer_material_price(layer)
            esp = sonara_safe_float(layer.get("espesor", layer.get("espesor_mm", 0)), 0)

            if nombre == "Material no identificado":
                if abs(precio - 6500) < 1:
                    nombre = "Lana mineral 60 kg/m³"
                elif abs(precio - 5200) < 1:
                    nombre = "Lana mineral 40 kg/m³"
                elif abs(precio - 4500) < 1:
                    nombre = "Placa de yeso-cartón estándar"
                elif abs(precio - 6200) < 1:
                    nombre = "Placa de yeso-cartón alta densidad"
                elif abs(precio - 8500) < 1:
                    nombre = "Lana mineral 80 kg/m³ / Mano de obra ref."

            item_name = f"{lado}: {nombre}"
            if esp > 0 and "mm" not in item_name:
                item_name += f" {esp:g} mm"

            items.append({
                "Ítem": item_name,
                "Unidad": unidad,
                "Cantidad": area,
                "Precio unitario": precio,
                "Subtotal": round(area * precio, 0),
            })

    abs_tipo = opt_solution.get("absorbente_tipo", "")
    if abs_tipo and abs_tipo != "Sin absorbente":
        precio_abs = 0.0
        try:
            mats = material_db()
            for k, v in mats.items():
                if str(abs_tipo).lower() in str(k).lower() or str(k).lower() in str(abs_tipo).lower():
                    precio_abs = sonara_safe_float(v.get("precio", 0), 0)
                    break
        except Exception:
            precio_abs = 0.0

        if not any(str(abs_tipo).lower() in str(it.get("Ítem", "")).lower() for it in items):
            items.append({
                "Ítem": f"Absorbente: {abs_tipo}",
                "Unidad": "m²",
                "Cantidad": area,
                "Precio unitario": precio_abs,
                "Subtotal": round(area * precio_abs, 0),
            })

    configuracion = opt_solution.get("configuracion", "")
    if configuracion:
        items.append({
            "Ítem": f"Estructura / montaje: {configuracion}",
            "Unidad": "m²",
            "Cantidad": area,
            "Precio unitario": 0,
            "Subtotal": 0,
        })

    try:
        mats = material_db()
        if opt_solution.get("camara_mm", 0):
            if not any("montante" in str(it.get("Ítem", "")).lower() for it in items):
                precio = sonara_safe_float(mats.get("Montante 90", {}).get("precio", 0), 0)
                items.append({"Ítem": "Montante 90", "Unidad": "ml", "Cantidad": area * 2, "Precio unitario": precio, "Subtotal": round(area * 2 * precio, 0)})
            if not any("solera" in str(it.get("Ítem", "")).lower() for it in items):
                precio = sonara_safe_float(mats.get("Solera", {}).get("precio", 0), 0)
                items.append({"Ítem": "Solera", "Unidad": "ml", "Cantidad": max(area / 1.2, 0), "Precio unitario": precio, "Subtotal": round(max(area / 1.2, 0) * precio, 0)})
            if not any("tornillo" in str(it.get("Ítem", "")).lower() for it in items):
                precio = sonara_safe_float(mats.get("Tornillos", {}).get("precio", 0), 0)
                items.append({"Ítem": "Tornillos", "Unidad": "un", "Cantidad": area * 70, "Precio unitario": precio, "Subtotal": round(area * 70 * precio, 0)})
            if not any("sellos" in str(it.get("Ítem", "")).lower() or "masilla" in str(it.get("Ítem", "")).lower() for it in items):
                precio = sonara_safe_float(mats.get("Sellos / cinta / masilla", {}).get("precio", 0), 0)
                items.append({"Ítem": "Sellos / cinta / masilla", "Unidad": "m²", "Cantidad": area, "Precio unitario": precio, "Subtotal": round(area * precio, 0)})
    except Exception:
        pass

    try:
        mats = material_db()
        if not any("mano de obra" in str(it.get("Ítem", "")).lower() for it in items):
            precio_mo = sonara_safe_float(mats.get("Mano de obra referencial", {}).get("precio", 0), 0)
            if precio_mo > 0:
                items.append({
                    "Ítem": "Mano de obra referencial",
                    "Unidad": "m²",
                    "Cantidad": area,
                    "Precio unitario": precio_mo,
                    "Subtotal": round(area * precio_mo, 0),
                })
    except Exception:
        pass

    total = 0.0
    for item in items:
        cant = sonara_safe_float(item.get("Cantidad", 0), 0)
        precio = sonara_safe_float(item.get("Precio unitario", 0), 0)
        item["Ítem"] = sonara_fix_cubicacion_item_name(item.get("Ítem", ""), precio)
        item["Subtotal"] = round(cant * precio, 0)
        total += sonara_safe_float(item["Subtotal"], 0)

    return {
        "codigo_partida": opt_solution.get("nombre", "Solución optimizada"),
        "tipo_cubicacion": "Optimización IA",
        "area_bruta": area,
        "area_neta": area,
        "area_vanos": 0,
        "masa": sonara_safe_float(opt_solution.get("masa", 0), 0),
        "espesor": sonara_safe_float(opt_solution.get("espesor", 0), 0),
        "resultado_label": opt_solution.get("resultado_label", ""),
        "tipo_calculo": opt_solution.get("tipo_calculo", "Optimización IA"),
        "items": items,
        "total": float(total),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def sonara_solution_cost_for_report(sol):
    """
    Costo usado por Informe: primero cubicación.total, luego suma de partidas,
    y finalmente costo_estimado si no existe cubicación.
    """
    try:
        if not isinstance(sol, dict):
            return 0.0
        cub = sol.get("cubicacion", {})
        if isinstance(cub, dict) and cub:
            if cub.get("total") not in [None, ""]:
                return sonara_safe_float(cub.get("total"), 0)
            total = 0.0
            for item in cub.get("items", []) or []:
                subtotal = item.get("Subtotal", None)
                if subtotal not in [None, ""]:
                    total += sonara_safe_float(subtotal, 0)
                else:
                    total += sonara_safe_float(item.get("Cantidad", 0), 0) * sonara_safe_float(item.get("Precio unitario", 0), 0)
            if total > 0:
                return float(total)
        return sonara_safe_float(sol.get("costo_estimado", sol.get("costo", 0)), 0)
    except Exception:
        return 0.0

def app_optimizador():
    """
    Optimizador IA rápido y contextual.
    Trabaja sobre la solución/requerimiento seleccionado, no sobre un diseño nuevo desde cero.
    Estrategia:
    1) agregar masa / cambiar espesor,
    2) agregar capa,
    3) cámara + absorbente,
    4) desacople.
    """
    st.markdown("## Optimizador IA")
    st.markdown(
        "<div class='result-note'>Optimización contextual: SONARA parte desde la solución y requerimiento seleccionados, prueba mejoras progresivas y calcula WALLS solo en las mejores candidatas.</div>",
        unsafe_allow_html=True
    )

    # Contexto desde proyecto
    pid, project = active_project()
    if project is None:
        project = st.session_state.get("active_project", {})

    selected_req = (
        st.session_state.get("selected_requirement_for_optimizer")
        or st.session_state.get("selected_requirement")
        or st.session_state.get("active_requirement")
    )

    selected_sol = (
        st.session_state.get("selected_solution_for_optimizer")
        or st.session_state.get("selected_solution_for_optimization")
        or st.session_state.get("selected_solution")
    )

    # Buscar automáticamente una solución guardada si no hay selección explícita
    if selected_sol is None and isinstance(project, dict):
        for req in project_requirements(project):
            sols = req.get("soluciones", [])
            if sols:
                selected_req = req
                selected_sol = sols[0]
                break

    if selected_sol:
        sol_name = selected_sol.get("nombre", selected_sol.get("solution_name", selected_sol.get("tipo", "Solución seleccionada")))
    else:
        sol_name = "Solución base no seleccionada"

    req_label = ""
    if isinstance(selected_req, dict):
        req_label = selected_req.get("label", selected_req.get("nombre", selected_req.get("norma", "")))

    st.markdown(
        f"""
        <div class='sonara-card' style='margin-bottom:18px;'>
            <div class='sonara-card-title'>Contexto de optimización</div>
            <p style='color:#DCEBFF;margin:0;'>
            <b>Solución base:</b> {sol_name}<br>
            <b>Requerimiento:</b> {req_label or "No especificado"}<br>
            <b>Flujo técnico:</b> + masa → + capa → cámara/absorbente → desacople.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([0.9, 1.35], gap="large")

    with col1:
        st.markdown("### Objetivo de diseño")
        default_target = 45.0
        if isinstance(selected_req, dict):
            for k in ["objetivo", "target", "rw_objetivo", "valor"]:
                try:
                    if selected_req.get(k) not in [None, ""]:
                        default_target = float(selected_req.get(k))
                        break
                except Exception:
                    pass

        target_rw = st.number_input("Rw objetivo [dB]", min_value=20.0, max_value=90.0, value=float(default_target), step=1.0)
        max_espesor = st.number_input("Espesor máximo [mm]", min_value=20.0, max_value=500.0, value=150.0, step=5.0)
        max_masa = st.number_input("Masa máxima [kg/m²]", min_value=5.0, max_value=800.0, value=80.0, step=5.0)
        area_m2 = st.number_input("Superficie a construir [m²]", min_value=1.0, max_value=10000.0, value=20.0, step=1.0)
        prioridad = st.selectbox("Prioridad", ["Menor costo", "Menor espesor", "Menor masa", "Mayor desempeño"])
        modo = st.radio("Modo de búsqueda", ["Rápido", "Preciso"], horizontal=True, index=0)

        buscar = st.button("🧠 Buscar mejores soluciones", use_container_width=True)

    with col2:
        st.markdown(
            """
            <div class='sonara-card'>
                <div class='sonara-card-title'>Cómo funciona</div>
                <ul style='color:#DCEBFF;line-height:1.8;'>
                    <li>Parte desde la solución seleccionada del proyecto.</li>
                    <li>Primero prueba aumentar masa o espesor.</li>
                    <li>Luego agrega una capa adicional si no alcanza.</li>
                    <li>Después evalúa cámara con absorbente.</li>
                    <li>Finalmente prueba desacople estructural.</li>
                    <li>Calcula WALLS solo sobre candidatas filtradas para reducir tiempo.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    if buscar:
        with st.spinner("Optimizando con estrategia progresiva..."):
            results = sonara_run_fast_optimizer(
                base_solution=selected_sol,
                target_rw=target_rw,
                max_espesor=max_espesor,
                max_masa=max_masa,
                area_m2=area_m2,
                prioridad=prioridad,
                modo=modo,
            )

        if not results:
            st.warning("No se encontraron variantes. Revisa que exista una solución base o materiales activos.")
            return

        st.session_state["last_optimization_results"] = results
    else:
        results = st.session_state.get("last_optimization_results", [])

    if results:
        st.markdown("### Resultados optimizados")

        df = pd.DataFrame([{
            "Estrategia": r.get("estrategia", ""),
            "Solución": r.get("nombre", ""),
            "Rw": round(r.get("Rw", 0), 1),
            "C": round(r.get("C", 0), 1),
            "Ctr": round(r.get("Ctr", 0), 1),
            "Rw+Ctr": round(r.get("Rw+Ctr", 0), 1),
            "Margen": round(r.get("margen", 0), 1),
            "Masa kg/m²": round(r.get("masa", 0), 1),
            "Espesor mm": round(r.get("espesor", 0), 1),
            "Costo ref.": round(r.get("costo_estimado", 0), 0),
            "Estado": "Cumple" if r.get("cumple") else "No cumple",
        } for r in results])

        st.dataframe(df, use_container_width=True, hide_index=True, height=360)

        best = results[0]
        estado_color = "#00E08A" if best.get("cumple") else "#FFD166"
        st.markdown(
            f"""
            <div class='sonara-card' style='margin-top:18px;'>
                <div class='sonara-card-title'>Recomendación técnica</div>
                <p style='color:#DCEBFF;line-height:1.7;'>
                La mejor alternativa según <b>{prioridad}</b> es:<br>
                <b>{best.get("nombre","")}</b><br>
                Estrategia: <b>{best.get("estrategia","")}</b><br>
                Resultado: <b>Rw {best.get("Rw",0):.1f} dB; C {best.get("C",0):+.1f}; Ctr {best.get("Ctr",0):+.1f}</b><br>
                Masa: <b>{best.get("masa",0):.1f} kg/m²</b> · Espesor: <b>{best.get("espesor",0):.1f} mm</b> · Costo ref.: <b>${best.get("costo_estimado",0):,.0f}</b><br>
                Estado: <span style='color:{estado_color};font-weight:900;'>{'Cumple' if best.get("cumple") else 'No cumple'}</span>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(sonara_draw_solution_html(best), unsafe_allow_html=True)

        names = [f"{i+1}. {r.get('nombre','')}" for i, r in enumerate(results[:10])]
        idx = st.selectbox("Selecciona variante para guardar en el requerimiento", list(range(len(names))), format_func=lambda i: names[i])
        selected_variant = results[idx]

        if st.button("💾 Guardar variante optimizada en el requerimiento", use_container_width=True):
            resultado_rw = sonara_safe_float(selected_variant.get("Rw", 0), 0)
            c_val = sonara_safe_float(selected_variant.get("C", 0), 0)
            ctr_val = sonara_safe_float(selected_variant.get("Ctr", 0), 0)
            area = sonara_safe_float(area_m2, 1.0)

            opt_solution = {
                "id": f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "nombre": selected_variant.get("nombre", "Solución optimizada"),
                "tipo": "Optimización IA",
                "tipo_calculo": "Optimización IA",
                "es_solucion_vigente": True,
                "estrategia": selected_variant.get("estrategia", ""),
                "descriptor": "Rw",
                "resultado": resultado_rw,
                "resultado_label": f"Rw = {resultado_rw:.1f} dB",
                "C": c_val,
                "Ctr": ctr_val,
                "Rw+C": resultado_rw + c_val,
                "Rw+Ctr": resultado_rw + ctr_val,
                "masa": selected_variant.get("masa", 0),
                "espesor": selected_variant.get("espesor", 0),
                "costo_estimado": selected_variant.get("costo_estimado", 0),
                "layers_left": selected_variant.get("layers_left", []),
                "layers_right": selected_variant.get("layers_right", []),
                "camara_mm": selected_variant.get("camara_mm", 0),
                "absorbente_tipo": selected_variant.get("absorbente_tipo", ""),
                "configuracion": selected_variant.get("configuracion", ""),
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "fecha": datetime.now().isoformat(timespec="seconds"),
            }

            # Cubicación automática inicial de la optimización.
            opt_solution["cubicacion"] = sonara_cubicacion_from_optimized_solution(opt_solution, area_m2=area)
            opt_solution["costo_estimado"] = sonara_solution_cost_for_report(opt_solution)

            # Deja la variante seleccionada para el módulo Cubicación.
            st.session_state["selected_solution_for_cubicacion"] = opt_solution
            st.session_state["selected_requirement_for_cubicacion"] = selected_req
            st.session_state["selected_solution_for_optimizer"] = opt_solution
            st.session_state["selected_requirement_for_optimizer"] = selected_req

            saved = False

            if isinstance(project, dict) and isinstance(selected_req, dict):
                req_id = selected_req.get("id")

                for req in project_requirements(project):
                    if req.get("id") == req_id:
                        req.setdefault("soluciones", [])
                        req["soluciones"].append(opt_solution)
                        saved = True
                        break

                if saved:
                    st.session_state["active_project"] = project
                    try:
                        projects = load_projects()
                        if pid:
                            projects[pid] = project
                            save_projects(projects)
                        else:
                            save_active_project(project)
                    except Exception:
                        try:
                            save_active_project(project)
                        except Exception:
                            pass

            if not saved:
                st.session_state.setdefault("optimized_solutions", []).append(opt_solution)

            st.success("Variante optimizada guardada, cubicada y asociada al informe.")


def app_materiales():
    st.markdown(
        "<h2 style='color:#FFFFFF;margin-bottom:18px;'>Materiales</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='result-note'>
        Biblioteca editable de materiales SONARA. Aquí se guardan los parámetros acústicos del motor WALLS
        y los costos usados por Cubicación y Optimizador IA.
        </div>
        """,
        unsafe_allow_html=True
    )

    ensure_materials_file()
    df = pd.read_csv(MATERIALS_CSV)

    cols_order = [
        "nombre", "tipo", "grupo", "espesor", "dens", "E", "eta",
        "color", "unidad", "precio", "proveedor", "activo"
    ]

    for col in cols_order:
        if col not in df.columns:
            df[col] = ""

    df = df[cols_order].copy()

    col_actions1, col_actions2, col_actions3 = st.columns([1, 1, 1], gap="large")

    save_materials_clicked = False
    with col_actions1:
        save_materials_clicked = st.button("💾 Guardar cambios", use_container_width=True)

    with col_actions2:
        csv_export = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Exportar CSV",
            data=csv_export,
            file_name="materiales_sonara.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_actions3:
        if st.button("♻ Restaurar base WALLS", use_container_width=True):
            default_materials_dataframe().to_csv(MATERIALS_CSV, index=False, encoding="utf-8")
            st.success("Base WALLS restaurada. Recarga el módulo para ver los cambios.")

    uploaded = st.file_uploader(
        "Importar biblioteca CSV",
        type=["csv"],
        help="Debe contener columnas: nombre,tipo,grupo,espesor,dens,E,eta,color,unidad,precio,proveedor,activo"
    )

    if uploaded is not None:
        try:
            imported = pd.read_csv(uploaded)
            for col in cols_order:
                if col not in imported.columns:
                    imported[col] = ""
            imported = imported[cols_order]
            imported.to_csv(MATERIALS_CSV, index=False, encoding="utf-8")
            st.success("CSV importado correctamente. Recarga el módulo para editarlo.")
            df = imported.copy()
        except Exception as e:
            st.error(f"No se pudo importar el CSV: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<div class='sonara-card-title'>Editor de materiales y costos</div>", unsafe_allow_html=True)

    df = sonara_clean_cubicacion_dataframe(df)

    edited_df = st.data_editor(
        df,
        key="materiales_editor_v2",
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        height=520,
        column_config={
            "nombre": st.column_config.TextColumn("Nombre", required=True),
            "tipo": st.column_config.SelectboxColumn(
                "Tipo",
                options=["placa", "vidrio", "absorbente", "estructura", "fijacion", "sello", "mano_obra"],
                required=True
            ),
            "grupo": st.column_config.SelectboxColumn(
                "Grupo",
                options=["panel", "vidrio", "absorbente", "estructura", "fijacion", "sello", "mano_obra"],
                required=True
            ),
            "espesor": st.column_config.NumberColumn("Espesor [mm]", min_value=0.0, step=0.1),
            "dens": st.column_config.NumberColumn("Densidad [kg/m³]", min_value=0.0, step=1.0),
            "E": st.column_config.NumberColumn("Módulo Young E [Pa]", min_value=0.0, step=1000000.0),
            "eta": st.column_config.NumberColumn("η amortiguamiento", min_value=0.0, step=0.001, format="%.4f"),
            "color": st.column_config.TextColumn("Color HEX"),
            "unidad": st.column_config.SelectboxColumn("Unidad", options=["m²", "ml", "un", "kg", "m³"]),
            "precio": st.column_config.NumberColumn("Precio unitario [$]", min_value=0.0, step=100.0),
            "proveedor": st.column_config.TextColumn("Proveedor"),
            "activo": st.column_config.CheckboxColumn("Activo"),
        }
    )

    if save_materials_clicked:
        edited_df.to_csv(MATERIALS_CSV, index=False, encoding="utf-8")
        st.success("Biblioteca de materiales guardada.")

    st.markdown("<hr>", unsafe_allow_html=True)

    resumen = edited_df.copy()
    if "precio" in resumen.columns:
        resumen["precio"] = pd.to_numeric(resumen["precio"], errors="coerce").fillna(0)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"<div class='result-card'><div class='result-label'>Materiales</div><div class='result-value'>{len(resumen)}</div><div class='result-unit'>ítems</div></div>",
            unsafe_allow_html=True
        )

    with c2:
        activos = resumen["activo"].astype(str).str.lower().isin(["true", "1", "sí", "si", "yes"]).sum() if "activo" in resumen else len(resumen)
        st.markdown(
            f"<div class='result-card'><div class='result-label'>Activos</div><div class='result-value'>{activos}</div><div class='result-unit'>ítems</div></div>",
            unsafe_allow_html=True
        )

    with c3:
        con_precio = int((resumen["precio"] > 0).sum()) if "precio" in resumen else 0
        st.markdown(
            f"<div class='result-card'><div class='result-label'>Con precio</div><div class='result-value'>{con_precio}</div><div class='result-unit'>ítems</div></div>",
            unsafe_allow_html=True
        )

    with c4:
        precio_prom = resumen.loc[resumen["precio"] > 0, "precio"].mean() if "precio" in resumen and (resumen["precio"] > 0).any() else 0
        st.markdown(
            f"<div class='result-card'><div class='result-label'>Precio prom.</div><div class='result-value' style='font-size:34px;'>${precio_prom:,.0f}</div><div class='result-unit'>CLP</div></div>",
            unsafe_allow_html=True
        )

    st.markdown(
        """
        <div class='result-note' style='margin-top:18px;'>
        Recomendación: usa precios reales de tus proveedores y actualiza esta biblioteca antes de ejecutar cubicaciones u optimizaciones.
        Los parámetros densidad, E y η afectan directamente los cálculos WALLS.
        </div>
        """,
        unsafe_allow_html=True
    )




# =========================================================
# VALIDACIÓN LOSCAA MINVU E13 2024
# =========================================================

def default_loscaa_validation_dataframe():
    """
    Casos iniciales de validación contra LOSCAA MINVU E13 2024.
    Los valores oficiales deben ser revisados contra el documento original antes de uso formal.
    """
    rows = [
        {
            "codigo": "D.M.H.01.01",
            "nombre": "Muro H.A. e = 110 mm",
            "familia": "Aéreo - muro pesado",
            "tipo_sonara": "panel_simple_hormigon",
            "rw_oficial": 48,
            "c_oficial": 0,
            "ctr_oficial": -3,
            "lnw_oficial": "",
            "lnw_ci_oficial": "",
            "configuracion": "Panel simple: Hormigón armado, e=110 mm, densidad 2400 kg/m³.",
            "nota": "Solución vertical divisoria oficial LOSCAA.",
        },
        {
            "codigo": "D.M.H.01.02",
            "nombre": "Muro H.A. e = 110 mm + cerámica pulida e = 9 mm",
            "familia": "Aéreo - muro multicapa",
            "tipo_sonara": "panel_multicapa_hormigon_ceramica",
            "rw_oficial": 48,
            "c_oficial": 0,
            "ctr_oficial": -2,
            "lnw_oficial": "",
            "lnw_ci_oficial": "",
            "configuracion": "Panel multicapa: Hormigón armado 110 mm + cerámica 9 mm + adhesivo 3 mm.",
            "nota": "Modelo SONARA lo aproxima como multicapa rígida.",
        },
        {
            "codigo": "E.V.O.01.01",
            "nombre": "Vidrio simple 4 mm",
            "familia": "Aéreo - vidrio",
            "tipo_sonara": "vidrio_simple_4",
            "rw_oficial": 32,
            "c_oficial": -1,
            "ctr_oficial": -2,
            "lnw_oficial": "",
            "lnw_ci_oficial": "",
            "configuracion": "Ventana: vidrio simple monolítico 4 mm.",
            "nota": "Caso ideal para validar vidrio monolítico.",
        },
        {
            "codigo": "E.V.O.01.02",
            "nombre": "DVH 4-12-4 mm",
            "familia": "Aéreo - DVH",
            "tipo_sonara": "dvh_4_12_4",
            "rw_oficial": 32,
            "c_oficial": -1,
            "ctr_oficial": -3,
            "lnw_oficial": "",
            "lnw_ci_oficial": "",
            "configuracion": "Ventana: DVH 4 mm / cámara 12 mm / 4 mm.",
            "nota": "Caso para validar DVH fijo; no representa corredera con fugas.",
        },
        {
            "codigo": "E.V.Al.01.01",
            "nombre": "Ventana corredera aluminio vidrio simple 5 mm",
            "familia": "Aéreo - ventana real",
            "tipo_sonara": "ventana_corredera_5",
            "rw_oficial": 20,
            "c_oficial": -1,
            "ctr_oficial": -1,
            "lnw_oficial": "",
            "lnw_ci_oficial": "",
            "configuracion": "Ventana corredera aluminio AL5000, vidrio simple 5 mm. Incluye penalización por marco/sellos.",
            "nota": "Comparar con corrección de fugas/marco; no solo vidrio.",
        },
        {
            "codigo": "E.V.Al.01.03",
            "nombre": "Ventana corredera aluminio DVH 3-12-3",
            "familia": "Aéreo - ventana real",
            "tipo_sonara": "ventana_corredera_dvh_3_12_3",
            "rw_oficial": 20,
            "c_oficial": 0,
            "ctr_oficial": -1,
            "lnw_oficial": "",
            "lnw_ci_oficial": "",
            "configuracion": "Ventana corredera aluminio AL25, DVH 3-12-3. Incluye penalización por marco/sellos.",
            "nota": "Caso clave: el DVH solo no explica el resultado; domina la corredera.",
        },
        {
            "codigo": "D.EP.H.01.08",
            "nombre": "Losa H.A. 140 mm + sobrelosa 50 mm sobre lana vidrio 25 mm 80 kg/m³",
            "familia": "Impacto + aéreo",
            "tipo_sonara": "impacto_losa_sobrelosa_lana",
            "rw_oficial": 53,
            "c_oficial": -2,
            "ctr_oficial": -6,
            "lnw_oficial": 41,
            "lnw_ci_oficial": 40,
            "configuracion": "Impacto: losa HA 140 mm + sobrelosa 50 mm + lana vidrio 25 mm 80 kg/m³.",
            "nota": "Caso fuerte para calibrar piso flotante físico e impacto.",
        },
    ]
    return pd.DataFrame(rows)


def ensure_loscaa_file():
    DATA_DIR.mkdir(exist_ok=True)
    if not LOSCAA_CSV.exists():
        default_loscaa_validation_dataframe().to_csv(LOSCAA_CSV, index=False, encoding="utf-8")

    try:
        df = pd.read_csv(LOSCAA_CSV)
    except Exception:
        df = default_loscaa_validation_dataframe()
        df.to_csv(LOSCAA_CSV, index=False, encoding="utf-8")

    required = default_loscaa_validation_dataframe().columns.tolist()
    for col in required:
        if col not in df.columns:
            df[col] = ""
    df = df[required]
    return df


def loscaa_status(delta):
    try:
        d = abs(float(delta))
    except Exception:
        return "Sin dato"

    if d <= 1:
        return "Excelente"
    if d <= 2:
        return "Muy bueno"
    if d <= 3:
        return "Aceptable"
    return "Revisar modelo"


def loscaa_compute_case(row):
    """
    Ejecuta cálculo SONARA para los casos predefinidos de validación.
    Retorna dict con rw/c/ctr/lnw/lnw_ci y curvas cuando aplica.
    """
    mats = material_db()
    tipo = str(row.get("tipo_sonara", ""))
    result = {
        "rw": None,
        "c": None,
        "ctr": None,
        "lnw": None,
        "lnw_ci": None,
        "freqs": None,
        "curve": None,
        "metric": "Rw",
    }

    try:
        if tipo == "panel_simple_hormigon":
            material = dict(mats.get("Hormigón armado", {}))
            material["dens"] = 2400.0
            freqs = np.array([50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
                              800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000], dtype=float)
            tl, masa, B, eta, fc = walls_panel_tl(material, 110.0, freqs, densidad_override=2400.0)
            rw, c, ctr = iso717_rw_simple(freqs, tl)
            result.update({"rw": rw, "c": c, "ctr": ctr, "freqs": freqs, "curve": tl, "metric": "Rw"})

        elif tipo == "panel_multicapa_hormigon_ceramica":
            hormigon = dict(mats.get("Hormigón armado", {}))
            hormigon["dens"] = 2400.0
            ceramica = {"tipo": "placa", "grupo": "panel", "espesor": 9.0, "dens": 2100.0, "E": 30000000000.0, "eta": 0.012, "color": "#D6D3C4"}
            adhesivo = {"tipo": "placa", "grupo": "panel", "espesor": 3.0, "dens": 1600.0, "E": 8000000000.0, "eta": 0.02, "color": "#B0B7C3"}
            layers = [
                {"nombre": "Hormigón armado", "material": hormigon, "espesor": 110.0},
                {"nombre": "Adhesivo cerámica", "material": adhesivo, "espesor": 3.0},
                {"nombre": "Cerámica pulida", "material": ceramica, "espesor": 9.0},
            ]
            fine = np.linspace(45, 6000, 1191)
            tl_fine, masa_calc, B_calc, eta_calc, fc_calc = walls_multilayer_tl(layers, fine)
            freqs, tl = third_octave_from_fine(fine, tl_fine)
            rw, c, ctr = iso717_rw_simple(freqs, tl)
            result.update({"rw": rw, "c": c, "ctr": ctr, "freqs": freqs, "curve": tl, "metric": "Rw"})

        elif tipo == "vidrio_simple_4":
            material = dict(mats.get("Vidrio float", mats.get("Vidrio monolítico", {})))
            material["dens"] = 2600.0
            material["E"] = 70000000000.0
            material["eta"] = 0.014
            freqs = np.array([50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
                              800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000], dtype=float)
            tl, masa, B, eta, fc = walls_panel_tl(material, 4.0, freqs, densidad_override=2600.0)
            # Corrección menor por tamaño/marco fijo para aproximar ensayo de vidrio en marco.
            tl = np.asarray(tl) + 1.0
            rw, c, ctr = iso717_rw_simple(freqs, tl)
            result.update({"rw": rw, "c": c, "ctr": ctr, "freqs": freqs, "curve": tl, "metric": "Rw"})

        elif tipo == "dvh_4_12_4":
            glass = dict(mats.get("Vidrio float", mats.get("Vidrio monolítico", {})))
            glass["dens"] = 2600.0
            glass["E"] = 70000000000.0
            glass["eta"] = 0.014
            freqs = np.array([50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
                              800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000], dtype=float)
            tl, mt, fc_min, f0, fl = walls_double_panel_tl(glass, 4.0, glass, 4.0, 12.0, freqs, absorbente=False)
            rw, c, ctr = iso717_rw_simple(freqs, tl)
            result.update({"rw": rw, "c": c, "ctr": ctr, "freqs": freqs, "curve": tl, "metric": "Rw"})

        elif tipo == "ventana_corredera_5":
            glass = dict(mats.get("Vidrio float", mats.get("Vidrio monolítico", {})))
            glass["dens"] = 2500.0
            freqs = np.array([50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
                              800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000], dtype=float)
            tl, *_ = walls_panel_tl(glass, 5.0, freqs, densidad_override=2500.0)
            # Penalización de corredera/marco/fugas según diferencia típica vidrio vs ventana real.
            tl = np.asarray(tl) - 11.0
            rw, c, ctr = iso717_rw_simple(freqs, tl)
            result.update({"rw": rw, "c": c, "ctr": ctr, "freqs": freqs, "curve": tl, "metric": "Rw"})

        elif tipo == "ventana_corredera_dvh_3_12_3":
            glass = dict(mats.get("Vidrio float", mats.get("Vidrio monolítico", {})))
            glass["dens"] = 2500.0
            freqs = np.array([50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
                              800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000], dtype=float)
            tl, mt, fc_min, f0, fl = walls_double_panel_tl(glass, 3.0, glass, 3.0, 12.0, freqs, absorbente=False)
            tl = np.asarray(tl) - 10.0
            rw, c, ctr = iso717_rw_simple(freqs, tl)
            result.update({"rw": rw, "c": c, "ctr": ctr, "freqs": freqs, "curve": tl, "metric": "Rw"})

        elif tipo == "impacto_losa_sobrelosa_lana":
            freqs, ln0 = impact_reference_curve_from_lnw(impact_ln0w_from_mass(0.14 * 2400.0))
            f0 = (1.0 / (2.0 * np.pi)) * np.sqrt((12.0 * 1e6) / 120.0)
            delta_floor = delta_floor_curve("Piso flotante físico", freqs, f0=f0) + 4.0
            delta_ceiling = ceiling_delta_curve("Sin cielo", freqs)
            ln_direct = ln0 - delta_floor - delta_ceiling
            lnw, ci = iso717_impact_rating(freqs, ln_direct)
            result.update({"lnw": lnw, "lnw_ci": lnw + ci, "freqs": freqs, "curve": ln_direct, "metric": "Ln,w"})

    except Exception as e:
        result["error"] = str(e)

    return result



def loscaa_validation_results_dataframe(df=None):
    """
    Ejecuta todos los casos LOSCAA modelados y devuelve tabla con errores.
    Usa los casos existentes en data/loscaa_validacion.csv.
    """
    if df is None:
        df = ensure_loscaa_file()
    rows = []
    for _, row in df.iterrows():
        res = loscaa_compute_case(row)
        metric = res.get("metric", "Rw")
        rw_of = pd.to_numeric(row.get("rw_oficial", ""), errors="coerce")
        c_of = pd.to_numeric(row.get("c_oficial", ""), errors="coerce")
        ctr_of = pd.to_numeric(row.get("ctr_oficial", ""), errors="coerce")
        lnw_of = pd.to_numeric(row.get("lnw_oficial", ""), errors="coerce")
        lnwci_of = pd.to_numeric(row.get("lnw_ci_oficial", ""), errors="coerce")

        if metric == "Ln,w":
            sonara_main = res.get("lnw")
            oficial_main = None if pd.isna(lnw_of) else float(lnw_of)
            indicador = "Ln,w"
            sonara_comp = res.get("lnw_ci")
            oficial_comp = None if pd.isna(lnwci_of) else float(lnwci_of)
            indicador_comp = "Ln,w+CI"
        else:
            sonara_main = res.get("rw")
            oficial_main = None if pd.isna(rw_of) else float(rw_of)
            indicador = "Rw"
            sonara_comp = (res.get("rw") + res.get("ctr")) if res.get("rw") is not None and res.get("ctr") is not None else None
            oficial_comp = (float(rw_of) + float(ctr_of)) if not pd.isna(rw_of) and not pd.isna(ctr_of) else None
            indicador_comp = "Rw+Ctr"

        delta = None if sonara_main is None or oficial_main is None else float(sonara_main) - float(oficial_main)
        abs_delta = None if delta is None else abs(delta)
        delta_comp = None if sonara_comp is None or oficial_comp is None else float(sonara_comp) - float(oficial_comp)

        rows.append({
            "Código": row.get("codigo", ""),
            "Nombre": row.get("nombre", ""),
            "Familia": row.get("familia", ""),
            "Indicador": indicador,
            "LOSCAA": oficial_main,
            "SONARA": sonara_main,
            "Error": None if delta is None else round(delta, 2),
            "Abs error": None if abs_delta is None else round(abs_delta, 2),
            "Estado": loscaa_status(delta) if delta is not None else "Sin dato",
            "Indicador complementario": indicador_comp,
            "LOSCAA comp.": oficial_comp,
            "SONARA comp.": sonara_comp,
            "Error comp.": None if delta_comp is None else round(delta_comp, 2),
        })
    return pd.DataFrame(rows)


def loscaa_validation_stats(df_res):
    valid = df_res.dropna(subset=["LOSCAA", "SONARA", "Error"]).copy()
    if valid.empty:
        return {"n": 0, "mae": None, "rmse": None, "bias": None, "max_abs": None, "within3": None, "within5": None, "r2": None}
    err = valid["Error"].astype(float).to_numpy()
    y = valid["LOSCAA"].astype(float).to_numpy()
    yhat = valid["SONARA"].astype(float).to_numpy()
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    bias = float(np.mean(err))
    max_abs = float(np.max(np.abs(err)))
    within3 = float(np.mean(np.abs(err) <= 3) * 100)
    within5 = float(np.mean(np.abs(err) <= 5) * 100)
    if len(valid) > 1 and np.std(y) > 0 and np.std(yhat) > 0:
        r = float(np.corrcoef(y, yhat)[0, 1])
        r2 = r ** 2
    else:
        r2 = None
    return {"n": int(len(valid)), "mae": mae, "rmse": rmse, "bias": bias, "max_abs": max_abs, "within3": within3, "within5": within5, "r2": r2}


def _fmt_stat(v, suffix=""):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "-"
    if isinstance(v, (int, np.integer)):
        return f"{v}{suffix}"
    return f"{float(v):.2f}{suffix}"


def app_loscaa_validation():
    st.markdown(
        "<h2 style='color:#FFFFFF;margin-bottom:18px;'>Validación estadística LOSCAA — MINVU E13 2024</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='result-note'>
        Validación cuantitativa preliminar entre fichas LOSCAA MINVU ED13 2024 y el motor SONARA/WALLS.
        La comparación usa los casos actualmente modelados en SONARA; no reemplaza ensayos de laboratorio ni certificaciones.
        </div>
        """,
        unsafe_allow_html=True
    )

    df = ensure_loscaa_file()
    df_res = loscaa_validation_results_dataframe(df)
    stats = loscaa_validation_stats(df_res)

    st.markdown(
        f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
            <div class="result-card"><div class="result-label">Casos</div><div class="result-value">{stats['n']}</div><div class="result-unit">modelados</div></div>
            <div class="result-card"><div class="result-label">MAE</div><div class="result-value">{_fmt_stat(stats['mae'])}</div><div class="result-unit">dB</div></div>
            <div class="result-card"><div class="result-label">RMSE</div><div class="result-value">{_fmt_stat(stats['rmse'])}</div><div class="result-unit">dB</div></div>
            <div class="result-card"><div class="result-label">R²</div><div class="result-value">{_fmt_stat(stats['r2'])}</div><div class="result-unit">correlación</div></div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
            <div class="result-card"><div class="result-label">Sesgo</div><div class="result-value">{_fmt_stat(stats['bias'])}</div><div class="result-unit">dB</div></div>
            <div class="result-card"><div class="result-label">Error máx.</div><div class="result-value">{_fmt_stat(stats['max_abs'])}</div><div class="result-unit">dB</div></div>
            <div class="result-card"><div class="result-label">±3 dB</div><div class="result-value">{_fmt_stat(stats['within3'])}</div><div class="result-unit">%</div></div>
            <div class="result-card"><div class="result-label">±5 dB</div><div class="result-value">{_fmt_stat(stats['within5'])}</div><div class="result-unit">%</div></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_resumen, tab_caso, tab_biblioteca = st.tabs(["📊 Estadística", "🔎 Caso individual", "🧾 Biblioteca LOSCAA"])

    with tab_resumen:
        col_a, col_b = st.columns([1.2, 1], gap="large")
        with col_a:
            st.markdown("<div class='sonara-card-title'>Tabla comparativa global</div>", unsafe_allow_html=True)
            familias = sorted(df_res["Familia"].dropna().astype(str).unique().tolist())
            fam_sel = st.multiselect("Filtrar familias", familias, default=familias, key="loscaa_stats_fam")
            df_show = df_res[df_res["Familia"].astype(str).isin(fam_sel)].copy() if fam_sel else df_res.copy()
            st.dataframe(df_show, use_container_width=True, hide_index=True, height=440)
            st.download_button(
                "⬇ Descargar validación estadística CSV",
                data=df_res.to_csv(index=False).encode("utf-8"),
                file_name="sonara_validacion_estadistica_loscaa.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_b:
            valid = df_res.dropna(subset=["LOSCAA", "SONARA"]).copy()
            if not valid.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=valid["LOSCAA"],
                    y=valid["SONARA"],
                    mode="markers+text",
                    text=valid["Código"],
                    textposition="top center",
                    name="Casos LOSCAA",
                    marker=dict(size=12, color="#4F7CFF", line=dict(width=1, color="#FFFFFF"))
                ))
                minv = float(min(valid["LOSCAA"].min(), valid["SONARA"].min())) - 2
                maxv = float(max(valid["LOSCAA"].max(), valid["SONARA"].max())) + 2
                fig.add_trace(go.Scatter(x=[minv, maxv], y=[minv, maxv], mode="lines", name="Ideal 1:1", line=dict(color="#FF8A1F", dash="dash", width=2)))
                fig.update_layout(
                    title="SONARA vs LOSCAA",
                    template="plotly_dark",
                    height=440,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(8,18,32,.78)",
                    font=dict(size=14, color="#EAF4FF"),
                    margin=dict(l=60, r=20, t=60, b=60),
                    xaxis_title="LOSCAA [dB]",
                    yaxis_title="SONARA [dB]",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                fig.update_xaxes(gridcolor="rgba(255,255,255,.10)")
                fig.update_yaxes(gridcolor="rgba(255,255,255,.10)")
                st.plotly_chart(fig, use_container_width=True)
            st.markdown(
                """
                <div class='result-note'>
                Criterio sugerido: MAE ≤ 2 dB muy bueno para prediseño; error individual ≤ 3 dB aceptable;
                valores superiores deben usarse para calibrar el modelo o revisar la representación constructiva.
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_caso:
        col_left, col_right = st.columns([0.95, 1.25], gap="large")
        with col_left:
            familias = ["Todas"] + sorted(df["familia"].dropna().astype(str).unique().tolist())
            familia_sel = st.selectbox("Filtrar por familia", familias, key="loscaa_case_family")
            df_view = df.copy()
            if familia_sel != "Todas":
                df_view = df_view[df_view["familia"].astype(str) == familia_sel].copy()
            opciones = [f"{r['codigo']} — {r['nombre']}" for _, r in df_view.iterrows()]
            if not opciones:
                st.warning("No hay casos para esta familia.")
                return
            selected = st.selectbox("Seleccionar solución LOSCAA", opciones, key="loscaa_case_pick")
            selected_code = selected.split(" — ")[0]
            row = df[df["codigo"].astype(str) == selected_code].iloc[0]
            st.markdown(
                f"""
                <div class='sonara-card' style='margin-top:16px;'>
                    <div class='sonara-card-title'>{row['codigo']}</div>
                    <p style='color:#EAF4FF;line-height:1.65;'><b>{row['nombre']}</b></p>
                    <p style='color:#DCEBFF;line-height:1.65;'>{row['configuracion']}</p>
                    <div class='result-note'>{row['nota']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        result = loscaa_compute_case(row)
        rw_oficial = pd.to_numeric(row.get("rw_oficial", ""), errors="coerce")
        c_oficial = pd.to_numeric(row.get("c_oficial", ""), errors="coerce")
        ctr_oficial = pd.to_numeric(row.get("ctr_oficial", ""), errors="coerce")
        lnw_oficial = pd.to_numeric(row.get("lnw_oficial", ""), errors="coerce")
        lnwci_oficial = pd.to_numeric(row.get("lnw_ci_oficial", ""), errors="coerce")

        if result.get("metric") == "Ln,w":
            sonara_main = result.get("lnw")
            oficial_main = lnw_oficial if not pd.isna(lnw_oficial) else None
            delta_main = None if oficial_main is None or sonara_main is None else sonara_main - oficial_main
            main_label = "Ln,w"
            comp_plus_label = "Ln,w+CI"
            comp_plus_sonara = result.get("lnw_ci")
            comp_plus_oficial = lnwci_oficial if not pd.isna(lnwci_oficial) else None
        else:
            sonara_main = result.get("rw")
            oficial_main = rw_oficial if not pd.isna(rw_oficial) else None
            delta_main = None if oficial_main is None or sonara_main is None else sonara_main - oficial_main
            main_label = "Rw"
            comp_plus_label = "Rw+Ctr"
            comp_plus_sonara = (result.get("rw") + result.get("ctr")) if result.get("rw") is not None and result.get("ctr") is not None else None
            comp_plus_oficial = (rw_oficial + ctr_oficial) if not pd.isna(rw_oficial) and not pd.isna(ctr_oficial) else None

        status = loscaa_status(delta_main) if delta_main is not None else "Sin dato"
        with col_right:
            st.markdown(
                f"""
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
                    <div class="result-card"><div class="result-label">{main_label} LOSCAA</div><div class="result-value">{oficial_main if oficial_main is not None else '-'}</div><div class="result-unit">dB</div></div>
                    <div class="result-card"><div class="result-label">{main_label} SONARA</div><div class="result-value">{sonara_main if sonara_main is not None else '-'}</div><div class="result-unit">dB</div></div>
                    <div class="result-card"><div class="result-label">Δ</div><div class="result-value">{delta_main if delta_main is not None else '-'}</div><div class="result-unit">dB</div></div>
                    <div class="result-card"><div class="result-label">Estado</div><div class="result-value" style="font-size:24px;">{status}</div><div class="result-unit">validación</div></div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if result.get("metric") != "Ln,w":
                rwc_sonara = (result.get("rw") + result.get("c")) if result.get("rw") is not None and result.get("c") is not None else None
                rwctr_sonara = comp_plus_sonara
                rwc_oficial = (rw_oficial + c_oficial) if not pd.isna(rw_oficial) and not pd.isna(c_oficial) else None
                rwctr_oficial = comp_plus_oficial
                df_comp = pd.DataFrame([
                    {"Indicador": "Rw", "LOSCAA": oficial_main, "SONARA": sonara_main, "Δ": delta_main, "Estado": status},
                    {"Indicador": "Rw+C", "LOSCAA": rwc_oficial, "SONARA": rwc_sonara, "Δ": None if rwc_oficial is None or rwc_sonara is None else rwc_sonara - rwc_oficial, "Estado": loscaa_status(None if rwc_oficial is None or rwc_sonara is None else rwc_sonara - rwc_oficial)},
                    {"Indicador": "Rw+Ctr", "LOSCAA": rwctr_oficial, "SONARA": rwctr_sonara, "Δ": None if rwctr_oficial is None or rwctr_sonara is None else rwctr_sonara - rwctr_oficial, "Estado": loscaa_status(None if rwctr_oficial is None or rwctr_sonara is None else rwctr_sonara - rwctr_oficial)},
                ])
            else:
                df_comp = pd.DataFrame([
                    {"Indicador": "Ln,w", "LOSCAA": oficial_main, "SONARA": sonara_main, "Δ": delta_main, "Estado": status},
                    {"Indicador": comp_plus_label, "LOSCAA": comp_plus_oficial, "SONARA": comp_plus_sonara, "Δ": None if comp_plus_oficial is None or comp_plus_sonara is None else comp_plus_sonara - comp_plus_oficial, "Estado": loscaa_status(None if comp_plus_oficial is None or comp_plus_sonara is None else comp_plus_sonara - comp_plus_oficial)},
                ])
            st.dataframe(df_comp, use_container_width=True, hide_index=True, height=180)
            freqs = result.get("freqs")
            curve = result.get("curve")
            if freqs is not None and curve is not None:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=freqs, y=np.round(curve, 1), mode="lines+markers", name=f"SONARA {main_label}", line=dict(color="#4F7CFF", width=3), marker=dict(size=6)))
                if oficial_main is not None:
                    fig.add_trace(go.Scatter(x=freqs, y=np.ones_like(np.asarray(freqs, dtype=float)) * float(oficial_main), mode="lines", name=f"Referencia LOSCAA {main_label}", line=dict(color="#FF8A1F", width=2, dash="dash")))
                fig.update_xaxes(type="log", title="Frecuencia [Hz]", tickmode="array", tickvals=[100,125,250,500,1000,2000,3150], ticktext=["100","125","250","500","1000","2000","3150"], gridcolor="rgba(255,255,255,.10)")
                fig.update_yaxes(title=f"{main_label} / curva [dB]", gridcolor="rgba(255,255,255,.10)")
                fig.update_layout(template="plotly_dark", height=430, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,18,32,.78)", font=dict(size=15, color="#EAF4FF"), margin=dict(l=60, r=20, t=60, b=60), legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5))
                st.plotly_chart(fig, use_container_width=True)

    with tab_biblioteca:
        st.markdown("<div class='sonara-card-title'>Biblioteca editable de casos LOSCAA</div>", unsafe_allow_html=True)
        edited = st.data_editor(df, key="loscaa_editor", use_container_width=True, hide_index=True, num_rows="dynamic", height=460)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("💾 Guardar biblioteca", use_container_width=True):
                edited.to_csv(LOSCAA_CSV, index=False, encoding="utf-8")
                st.success("Biblioteca LOSCAA guardada.")
        with c2:
            st.download_button("⬇ Exportar CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="loscaa_validacion.csv", mime="text/csv", use_container_width=True)
        with c3:
            if st.button("♻ Restaurar", use_container_width=True):
                default_loscaa_validation_dataframe().to_csv(LOSCAA_CSV, index=False, encoding="utf-8")
                st.success("Biblioteca restaurada.")



def app_calculadora_master():
    st.markdown(
        "<h1 style='color:#FFFFFF;margin-bottom:8px;'>Calculadora</h1>",
        unsafe_allow_html=True
    )

    sub = st.radio(
        "Tipo de cálculo",
        [
            "Ruido aéreo",
            "Ruido de impacto",
            "Transmisión entre recintos (ISO 12354-1)"
        ],
        horizontal=True,
        key="calc_master_submodule"
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    if sub == "Ruido aéreo":
        app_calculator()
    elif sub == "Ruido de impacto":
        app_impacto()
    elif sub == "Transmisión entre recintos (ISO 12354-1)":
        app_iso12354()



# =========================================================
# PROYECTOS, SOLUCIONES Y BASE NORMATIVA
# =========================================================

def _json_default(value):
    try:
        if isinstance(value, (np.integer, np.floating)):
            return float(value)
        if isinstance(value, np.ndarray):
            return value.tolist()
    except Exception:
        pass
    return str(value)


def safe_user_id(email=None):
    """
    Convierte el correo activo en un nombre de archivo seguro.
    """
    email = norm(email or st.session_state.get("email", "anonimo"))
    if not email:
        email = "anonimo"
    safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in email)
    safe = "_".join([x for x in safe.split("_") if x])
    return safe or "anonimo"


def current_user_project_file(email=None):
    """
    Archivo de proyectos privado por usuario.
    Antes: data/projects.json
    Ahora: data/projects/<usuario>.json
    """
    PROJECTS_DIR.mkdir(exist_ok=True)
    return PROJECTS_DIR / f"{safe_user_id(email)}.json"


def migrate_legacy_projects_if_needed(email=None):
    """
    Migra el antiguo data/projects.json al archivo privado del usuario activo
    solo si el archivo privado aún no existe.
    """
    user_file = current_user_project_file(email)
    if user_file.exists():
        return

    if PROJECTS_JSON.exists():
        try:
            legacy = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
            if isinstance(legacy, dict) and legacy:
                user_file.write_text(
                    json.dumps(legacy, ensure_ascii=False, indent=2, default=_json_default),
                    encoding="utf-8"
                )
                return
        except Exception:
            pass

    user_file.write_text("{}", encoding="utf-8")


def load_projects():
    try:
        migrate_legacy_projects_if_needed()
        path = current_user_project_file()
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def save_projects(data):
    path = current_user_project_file()
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8"
    )


def list_user_project_files():
    PROJECTS_DIR.mkdir(exist_ok=True)
    return sorted(PROJECTS_DIR.glob("*.json"))



def current_license_type():
    lic = st.session_state.get("license_info", {})
    return str(lic.get("type", "")).lower()


def is_trial_user():
    return current_license_type() == "trial"


def project_solution_count(project):
    total = len(project.get("soluciones", []))
    for req in project_requirements(project):
        total += len(req.get("soluciones", []))
    return total


def total_user_solution_count(projects=None):
    if projects is None:
        projects = load_projects()
    return sum(project_solution_count(p) for p in projects.values())


def trial_limits_status(projects=None):
    if projects is None:
        projects = load_projects()
    return {
        "projects": len(projects),
        "solutions": total_user_solution_count(projects),
        "max_projects": TRIAL_MAX_PROJECTS,
        "max_solutions": TRIAL_MAX_SOLUTIONS,
    }


def can_create_project():
    if not is_trial_user():
        return True, ""
    status = trial_limits_status()
    if status["projects"] >= status["max_projects"]:
        return False, f"Tu plan Trial permite hasta {TRIAL_MAX_PROJECTS} proyectos. Actualiza a Premium para crear proyectos ilimitados."
    return True, ""


def can_save_solution():
    if not is_trial_user():
        return True, ""
    status = trial_limits_status()
    if status["solutions"] >= status["max_solutions"]:
        return False, f"Tu plan Trial permite hasta {TRIAL_MAX_SOLUTIONS} soluciones guardadas. Actualiza a Premium para guardar más soluciones."
    return True, ""


def trial_usage_banner():
    if not is_trial_user():
        return
    st_info = trial_limits_status()
    st.markdown(
        f"""
        <div class='result-note'>
        <b>Trial activo:</b> {st_info['projects']}/{st_info['max_projects']} proyectos · 
        {st_info['solutions']}/{st_info['max_solutions']} soluciones guardadas. 
        Premium libera proyectos y soluciones ilimitadas.
        </div>
        """,
        unsafe_allow_html=True
    )


def make_requirement_id(req):
    base = f"{req.get('recinto_emisor','')}_{req.get('recinto_receptor','')}_{req.get('tipo_elemento','')}_{req.get('elemento','')}"
    clean = "".join(ch.lower() if ch.isalnum() else "_" for ch in base)
    clean = "_".join([x for x in clean.split("_") if x])
    if not clean:
        clean = "requerimiento"
    return "req_" + clean[:70]


def project_requirements(project):
    """
    Devuelve solo los elementos/requerimientos creados explícitamente por el usuario.
    Antes se convertía el objetivo preliminar del proyecto en un requerimiento automático,
    lo que generaba un elemento fantasma en la matriz al crear un proyecto nuevo.
    """
    reqs = project.get("requerimientos", [])
    if not isinstance(reqs, list):
        return []

    clean = []
    for r in reqs:
        if not isinstance(r, dict):
            continue
        r.setdefault("soluciones", [])
        clean.append(r)
    return clean


def upsert_requirement(project_id, req):
    projects = load_projects()
    if project_id not in projects:
        return None

    req = dict(req)
    req_id = req.get("id") or make_requirement_id(req)
    req["id"] = req_id
    req.setdefault("soluciones", [])

    project = projects[project_id]
    reqs = project_requirements(project)

    found = False
    for i, existing in enumerate(reqs):
        if existing.get("id") == req_id:
            # Preserva soluciones ya guardadas
            req["soluciones"] = existing.get("soluciones", [])
            reqs[i] = req
            found = True
            break

    if not found:
        reqs.append(req)

    project["requerimientos"] = reqs
    project["requerimiento_activo"] = req
    project["objetivo"] = req
    project["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_projects(projects)
    st.session_state["active_requirement_id"] = req_id
    st.session_state["active_requirement"] = req
    return req_id


def active_requirement(project):
    req_id = st.session_state.get("active_requirement_id")
    reqs = project_requirements(project)

    for req in reqs:
        if req.get("id") == req_id:
            return req

    active = project.get("requerimiento_activo")
    if isinstance(active, dict):
        active_id = active.get("id")
        for req in reqs:
            if req.get("id") == active_id:
                return req

    if reqs:
        return reqs[-1]

    return None


def all_project_solutions(project):
    rows = []
    for req in project_requirements(project):
        for sol in req.get("soluciones", []):
            sol2 = dict(sol)
            sol2["_req_id"] = req.get("id")
            sol2["_req_label"] = f"{req.get('recinto_emisor','')} → {req.get('recinto_receptor','')} · {req.get('tipo_elemento','')}"
            sol2["_req_obj"] = req
            rows.append(sol2)
    # Compatibilidad con soluciones antiguas
    for sol in project.get("soluciones", []):
        sol2 = dict(sol)
        sol2["_req_id"] = ""
        sol2["_req_label"] = "Sin requerimiento asociado"
        sol2["_req_obj"] = project.get("objetivo", {})
        rows.append(sol2)
    return rows


def make_project_id(nombre):
    clean = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(nombre).strip())
    clean = "_".join([x for x in clean.split("_") if x])
    if not clean:
        clean = "proyecto"
    return clean[:50]


def upsert_project(nombre, tipo, norma, objetivo):
    projects = load_projects()
    pid = make_project_id(nombre)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if pid not in projects:
        allowed, msg = can_create_project()
        if not allowed:
            st.error(msg)
            return None

        projects[pid] = {
            "id": pid,
            "nombre": nombre,
            "tipo": tipo,
            "norma": norma,
            "objetivo": objetivo,
            "created_at": now,
            "updated_at": now,
            "soluciones": [],
            "requerimientos": [],
        }
    else:
        projects[pid].update({
            "nombre": nombre,
            "tipo": tipo,
            "norma": norma,
            "objetivo": objetivo,
            "updated_at": now,
        })
        projects[pid].setdefault("soluciones", [])
        projects[pid].setdefault("requerimientos", [])

    save_projects(projects)
    st.session_state["active_project_id"] = pid
    return pid


def active_project():
    projects = load_projects()
    pid = st.session_state.get("active_project_id")
    if pid in projects:
        return pid, projects[pid]
    if projects:
        pid = list(projects.keys())[-1]
        st.session_state["active_project_id"] = pid
        return pid, projects[pid]
    return None, None


def get_project_options():
    projects = load_projects()
    return [(pid, p.get("nombre", pid)) for pid, p in projects.items()]


def solution_status(solution, objetivo):
    indicador = str(objetivo.get("indicador", "Rw"))
    try:
        meta = float(objetivo.get("valor", 0))
    except Exception:
        meta = 0.0
    sentido = str(objetivo.get("sentido", ">="))

    value = solution_descriptor_value(solution, indicador)

    if value is None:
        return "Sin evaluación", None

    try:
        value = float(value)
        if sentido == "<=":
            ok = value <= meta
            delta = value - meta
        else:
            ok = value >= meta
            delta = value - meta
        return ("Cumple" if ok else "No cumple"), delta
    except Exception:
        return "Sin evaluación", None



def save_solution_to_project(project_id, solution):
    allowed, msg = can_save_solution()
    if not allowed:
        st.error(msg)
        return False

    projects = load_projects()
    if project_id not in projects:
        return False

    project = projects[project_id]
    solution = dict(solution)
    solution["id"] = f"sol_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    solution["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Guardado nuevo: dentro del requerimiento activo
    req = active_requirement(project)
    req_id = st.session_state.get("active_requirement_id") or (req or {}).get("id")

    if req:
        req = dict(req)
        req_id = req.get("id") or make_requirement_id(req)
        req["id"] = req_id

        reqs = project_requirements(project)
        if not reqs:
            reqs = [req]

        placed = False
        for r in reqs:
            if r.get("id") == req_id:
                r.setdefault("soluciones", [])
                r["soluciones"].append(solution)
                placed = True
                break

        if not placed:
            req["soluciones"] = [solution]
            reqs.append(req)

        project["requerimientos"] = reqs
        project["requerimiento_activo"] = req
        project["objetivo"] = req
    else:
        project.setdefault("soluciones", [])
        project["soluciones"].append(solution)

    project["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_projects(projects)
    return True


def layer_summary(layers):
    out = []
    for layer in layers or []:
        out.append({
            "nombre": layer.get("nombre", ""),
            "espesor_mm": float(layer.get("espesor", 0) or 0),
            "densidad": float(layer.get("material", {}).get("dens", 0) or 0),
        })
    return out


def solution_save_widget(solution, key_prefix="save_solution"):
    options = get_project_options()
    if not options:
        st.markdown(
            "<div class='result-note'>No hay proyecto creado. Crea uno en el módulo Proyecto para guardar esta solución.</div>",
            unsafe_allow_html=True
        )
        return

    with st.expander("💾 Guardar solución en proyecto", expanded=False):
        labels = [name for _, name in options]
        ids = [pid for pid, _ in options]
        default_idx = 0
        active_id = st.session_state.get("active_project_id")
        if active_id in ids:
            default_idx = ids.index(active_id)

        project_label = st.selectbox("Proyecto destino", labels, index=default_idx, key=f"{key_prefix}_project")
        project_id = ids[labels.index(project_label)]

        nombre_sol = st.text_input(
            "Nombre de la solución",
            value=solution.get("nombre", "Solución SONARA"),
            key=f"{key_prefix}_name"
        )

        solution["nombre"] = nombre_sol
        solution["proyecto"] = project_label

        if st.button("Guardar en proyecto", use_container_width=True, key=f"{key_prefix}_btn"):
            if save_solution_to_project(project_id, solution):
                st.success(f"Solución guardada en {project_label}.")
            else:
                st.error("No se pudo guardar la solución.")


def norm_target_rows():
    """
    Base normativa/referencial inicial SONARA.
    Valores resumidos para diseño preliminar; deben verificarse contra cada norma para informes formales.
    """
    return [
        # CHILE / vivienda
        {"sector":"Vivienda", "norma":"Chile OGUC art. 4.1.6", "elemento":"Elemento separador horizontal/vertical entre viviendas", "indicador":"Rw", "sentido":">=", "valor":45, "unidad":"dB", "fuente":"OGUC / reglamentación acústica vivienda"},
        {"sector":"Vivienda", "norma":"Chile OGUC art. 4.1.6", "elemento":"Entrepiso entre viviendas", "indicador":"L'nT,w", "sentido":"<=", "valor":75, "unidad":"dB", "fuente":"OGUC / reglamentación acústica vivienda"},
        {"sector":"Vivienda", "norma":"NCh352/2:2021", "elemento":"Clasificación residencial", "indicador":"Clasificación", "sentido":">=", "valor":0, "unidad":"clase", "fuente":"NCh352/2 clasificación acústica residencial"},

        # DB-HR / España
        {"sector":"Vivienda", "norma":"DB-HR España", "elemento":"Recinto protegido vs otra unidad de uso", "indicador":"DnT,A", "sentido":">=", "valor":50, "unidad":"dBA", "fuente":"DB-HR 2.1.1"},
        {"sector":"Vivienda", "norma":"DB-HR España", "elemento":"Recinto protegido vs instalaciones/actividad", "indicador":"DnT,A", "sentido":">=", "valor":55, "unidad":"dBA", "fuente":"DB-HR 2.1.1"},
        {"sector":"Vivienda", "norma":"DB-HR España", "elemento":"Tabiquería misma unidad residencial", "indicador":"RA", "sentido":">=", "valor":33, "unidad":"dBA", "fuente":"DB-HR 2.1.1"},

        # Hospital / HTM 08-01
        {"sector":"Hospital", "norma":"HTM 08-01", "elemento":"Habitación individual / noche", "indicador":"LAeq", "sentido":"<=", "valor":35, "unidad":"dBA", "fuente":"HTM 08-01 Table 1"},
        {"sector":"Hospital", "norma":"HTM 08-01", "elemento":"Habitación individual / día", "indicador":"LAeq", "sentido":"<=", "valor":40, "unidad":"dBA", "fuente":"HTM 08-01 Table 1"},
        {"sector":"Hospital", "norma":"HTM 08-01", "elemento":"Consulta / tratamiento / oficina pequeña", "indicador":"LAeq", "sentido":"<=", "valor":40, "unidad":"dBA", "fuente":"HTM 08-01 Table 1"},
        {"sector":"Hospital", "norma":"HTM 08-01", "elemento":"Consulta ↔ consulta / confidencial típico", "indicador":"DnT,w", "sentido":">=", "valor":47, "unidad":"dB", "fuente":"HTM 08-01 Tables 3-4"},
        {"sector":"Hospital", "norma":"HTM 08-01", "elemento":"Recinto sensible / alta privacidad", "indicador":"DnT,w", "sentido":">=", "valor":52, "unidad":"dB", "fuente":"HTM 08-01 Table 4"},
        {"sector":"Hospital", "norma":"HTM 08-01", "elemento":"Adjacencia crítica a evitar", "indicador":"DnT,w", "sentido":">=", "valor":57, "unidad":"dB", "fuente":"HTM 08-01 Table 4"},
        {"sector":"Hospital", "norma":"HTM 08-01", "elemento":"Habitaciones / áreas de sueño", "indicador":"NR", "sentido":"<=", "valor":30, "unidad":"NR", "fuente":"HTM 08-01 Table 2"},
        {"sector":"Hospital", "norma":"HTM 08-01", "elemento":"Consultas / oficinas pequeñas", "indicador":"NR", "sentido":"<=", "valor":35, "unidad":"NR", "fuente":"HTM 08-01 Table 2"},
        {"sector":"Hospital", "norma":"HTM 08-01", "elemento":"Urgencias / áreas clínicas abiertas", "indicador":"NR", "sentido":"<=", "valor":40, "unidad":"NR", "fuente":"HTM 08-01 Table 2"},

        # Educación / BB93 y ANSI
        {"sector":"Educación", "norma":"BB93", "elemento":"Aula / enseñanza general", "indicador":"LAeq", "sentido":"<=", "valor":35, "unidad":"dBA", "fuente":"BB93 Performance Standards"},
        {"sector":"Educación", "norma":"BB93", "elemento":"Aula / enseñanza general", "indicador":"T", "sentido":"<=", "valor":0.6, "unidad":"s", "fuente":"BB93 / Acoustics of Schools"},
        {"sector":"Educación", "norma":"BB93", "elemento":"Aula con necesidades auditivas especiales", "indicador":"T", "sentido":"<=", "valor":0.4, "unidad":"s", "fuente":"BB93 / Acoustics of Schools"},
        {"sector":"Educación", "norma":"BB93", "elemento":"Aula ↔ aula", "indicador":"DnT,w", "sentido":">=", "valor":45, "unidad":"dB", "fuente":"BB93"},
        {"sector":"Educación", "norma":"BB93", "elemento":"Aula ↔ música / actividad ruidosa", "indicador":"DnT,w", "sentido":">=", "valor":55, "unidad":"dB", "fuente":"BB93"},
        {"sector":"Educación", "norma":"ANSI/ASA S12.60", "elemento":"Aula permanente pequeña/mediana", "indicador":"LAeq", "sentido":"<=", "valor":35, "unidad":"dBA", "fuente":"ANSI/ASA S12.60 Part 1"},
        {"sector":"Educación", "norma":"ANSI/ASA S12.60", "elemento":"Aula permanente pequeña/mediana", "indicador":"T", "sentido":"<=", "valor":0.6, "unidad":"s", "fuente":"ANSI/ASA S12.60 Part 1"},

        # Oficinas / BS8233
        {"sector":"Oficina", "norma":"BS 8233", "elemento":"Oficina privada / privacidad", "indicador":"DnT,w", "sentido":">=", "valor":40, "unidad":"dB", "fuente":"BS 8233 guidance"},
        {"sector":"Oficina", "norma":"BS 8233", "elemento":"Sala de reuniones", "indicador":"DnT,w", "sentido":">=", "valor":45, "unidad":"dB", "fuente":"BS 8233 guidance"},
        {"sector":"Oficina", "norma":"BS 8233", "elemento":"Sala confidencial / dirección", "indicador":"DnT,w", "sentido":">=", "valor":50, "unidad":"dB", "fuente":"BS 8233 guidance"},

        # HVAC
        {"sector":"HVAC", "norma":"ASHRAE / CIBSE B5", "elemento":"Diseño HVAC general", "indicador":"NC/NR", "sentido":"<=", "valor":35, "unidad":"NC/NR", "fuente":"ASHRAE HVAC Applications / CIBSE B5"},
        {"sector":"HVAC", "norma":"ASHRAE / CIBSE B5", "elemento":"Espacio crítico / reunión / docencia", "indicador":"NC/NR", "sentido":"<=", "valor":30, "unidad":"NC/NR", "fuente":"ASHRAE HVAC Applications / CIBSE B5"},
    ]


def norm_targets_df():
    return pd.DataFrame(norm_target_rows())


def project_targets_db():
    """
    Mantiene compatibilidad con versiones previas, pero ahora se alimenta desde norm_targets_df().
    """
    df = norm_targets_df()
    out = {}
    for sector in sorted(df["sector"].unique()):
        out[sector] = {}
        for _, r in df[df["sector"] == sector].iterrows():
            out[str(r["elemento"])] = {
                "indicador": str(r["indicador"]),
                "objetivo": float(r["valor"]) if str(r["valor"]).replace(".", "", 1).isdigit() else r["valor"],
                "criterio": f"{r['sentido']} {r['unidad']}",
                "norma": str(r["norma"]),
                "fuente": str(r["fuente"]),
            }
    return out



def composite_r_from_parts(parts):
    """
    R compuesto por áreas:
    R_total = -10 log10( sum(Si * 10^(-Ri/10)) / sum(Si) )
    """
    total_area = sum(max(float(p.get("area", 0)), 0) for p in parts)
    if total_area <= 0:
        return None

    tau_area = 0.0
    for p in parts:
        s = max(float(p.get("area", 0)), 0)
        r = float(p.get("r", 0))
        tau_area += s * (10 ** (-r / 10.0))

    tau = max(tau_area / total_area, 1e-12)
    return -10.0 * np.log10(tau)


def composite_optimizer_suggestions(parts, target):
    """
    Sugerencias preliminares para mejorar una solución compuesta.
    Identifica el componente acústicamente dominante por transmisión energética.
    """
    total_area = sum(max(float(p.get("area", 0)), 0) for p in parts)
    if total_area <= 0:
        return [], None

    contribs = []
    for p in parts:
        s = max(float(p.get("area", 0)), 0)
        r = float(p.get("r", 0))
        tau_area = s * (10 ** (-r / 10.0))
        contribs.append((tau_area, p))

    contribs = sorted(contribs, key=lambda x: x[0], reverse=True)
    dominant = contribs[0][1] if contribs else None

    suggestions = []
    if dominant:
        name = dominant.get("nombre", "componente")
        tipo = dominant.get("tipo", "")
        r = float(dominant.get("r", 0))

        if "Ventana" in tipo or "ventana" in name.lower():
            suggestions.append(f"La ventana domina la transmisión. Subir de Rw {r:.0f} dB a una ventana/DVH de mejor prestación puede mejorar más que reforzar el tabique.")
            suggestions.append("Revisar hermeticidad, tipo de apertura y sellos. Una corredera puede limitar mucho el resultado aunque el DVH sea bueno.")
        elif "Puerta" in tipo or "puerta" in name.lower():
            suggestions.append("La puerta domina la transmisión. Usar puerta acústica de mayor Rw, burletes perimetrales, sello inferior automático o doble puerta/lobby.")
            suggestions.append("Evitar que el tabique tenga Rw mucho mayor que la puerta si no se especifica una puerta acústica equivalente.")
        else:
            suggestions.append("El paramento opaco domina la transmisión. Evaluar doble placa, mayor cámara, lana mineral o montantes independientes.")
            suggestions.append("Si hay exigencia alta, controlar flancos, cajas eléctricas, pasadas y encuentros perimetrales.")

    r_now = composite_r_from_parts(parts)
    if r_now is not None and target is not None:
        deficit = float(target) - r_now
        if deficit > 0:
            suggestions.append(f"Faltan aproximadamente {deficit:.1f} dB para cumplir. Priorizar la mejora del componente dominante antes de aumentar materiales en todos los elementos.")
        else:
            suggestions.append(f"La solución tiene un margen aproximado de {abs(deficit):.1f} dB sobre el objetivo.")

    return suggestions, dominant


def app_composite_solution(project=None, requirement=None):
    st.markdown(
        """
        <div class='project-flow-card'>
            <div class='project-flow-title'>Solución compuesta</div>
            <div class='project-flow-text'>
            Calcula el aislamiento global de un elemento compuesto: fachada con tabique opaco + ventana, o tabique interior con puerta.
            SONARA suma energéticamente las transmisiones por área.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    req = requirement or (project or {}).get("requerimiento_activo", {}) or (project or {}).get("objetivo", {})
    target = req.get("valor", None) if req else None
    indicador = req.get("indicador", "Rw") if req else "Rw"

    col_in, col_out = st.columns([1.05, 1.2], gap="large")

    with col_in:
        nombre = st.text_input("Nombre de la solución compuesta", value="Fachada / tabique compuesto", key="comp_nombre")
        area_total = st.number_input("Área total del elemento [m²]", value=12.0, min_value=0.5, step=0.5, key="comp_area_total")

        st.markdown("<div class='sonara-card-title'>Componentes</div>", unsafe_allow_html=True)

        n_comp = st.number_input("Número de componentes", value=3, min_value=2, max_value=8, step=1, key="comp_n")

        parts = []
        default_names = ["Tabique opaco", "Ventana", "Puerta", "Rejilla / ventilación"]
        default_areas = [9.0, 2.0, 1.0, 0.2]
        default_r = [52.0, 32.0, 30.0, 20.0]

        for i in range(int(n_comp)):
            with st.expander(f"Componente {i+1}", expanded=i < 3):
                tipo = st.selectbox(
                    "Tipo",
                    ["Paramento opaco", "Ventana", "Puerta", "Elemento débil", "Otro"],
                    index=min(i, 3),
                    key=f"comp_tipo_{i}"
                )
                comp_nombre = st.text_input("Nombre", value=default_names[i] if i < len(default_names) else f"Componente {i+1}", key=f"comp_name_{i}")
                area = st.number_input("Área [m²]", value=default_areas[i] if i < len(default_areas) else 1.0, min_value=0.0, step=0.1, key=f"comp_area_{i}")
                r = st.number_input("Rw / R del componente [dB]", value=default_r[i] if i < len(default_r) else 35.0, min_value=0.0, max_value=90.0, step=1.0, key=f"comp_r_{i}")
                parts.append({"tipo": tipo, "nombre": comp_nombre, "area": float(area), "r": float(r)})

        area_sum = sum(p["area"] for p in parts)
        if abs(area_sum - area_total) > 0.2:
            st.markdown(
                f"<div class='result-note'>Área total declarada: {area_total:.1f} m² · suma componentes: {area_sum:.1f} m². Revisa si hay diferencia importante.</div>",
                unsafe_allow_html=True
            )

    r_comp = composite_r_from_parts(parts)
    suggestions, dominant = composite_optimizer_suggestions(parts, target)

    with col_out:
        status = "Sin objetivo"
        delta = None
        if r_comp is not None and target is not None:
            delta = r_comp - float(target)
            if str(req.get("sentido", ">=")) == ">=":
                status = "Cumple" if r_comp >= float(target) else "No cumple"
            else:
                status = "Evaluar"

        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;">
                <div class="result-card"><div class="result-label">R compuesto</div><div class="result-value">{'-' if r_comp is None else round(r_comp,1)}</div><div class="result-unit">dB</div></div>
                <div class="result-card"><div class="result-label">Objetivo</div><div class="result-value">{target if target is not None else '-'}</div><div class="result-unit">{indicador}</div></div>
                <div class="result-card"><div class="result-label">Estado</div><div class="result-value" style="font-size:24px;">{status}</div><div class="result-unit">{'' if delta is None else f'Δ {delta:.1f} dB'}</div></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        df_parts = pd.DataFrame(parts)
        if r_comp is not None:
            total_tau_area = sum(p["area"] * 10 ** (-p["r"]/10.0) for p in parts)
            df_parts["Aporte transmisión [%]"] = [
                round((p["area"] * 10 ** (-p["r"]/10.0)) / max(total_tau_area, 1e-12) * 100, 1)
                for p in parts
            ]

        st.dataframe(df_parts, use_container_width=True, hide_index=True, height=260)

        st.markdown("<div class='sonara-card-title'>Recomendación del optimizador IA</div>", unsafe_allow_html=True)
        for s in suggestions:
            st.markdown(f"<div class='result-note' style='margin-bottom:8px;'>{s}</div>", unsafe_allow_html=True)

        solution_save_widget({
            "nombre": f"{nombre} Rw compuesto {0 if r_comp is None else round(r_comp,1)} dB",
            "tipo_calculo": "Solución compuesta",
            "resultado_label": f"Rw compuesto {0 if r_comp is None else round(r_comp,1)} dB",
            "rw": None if r_comp is None else float(r_comp),
            "valor": None if r_comp is None else float(r_comp),
            "masa": None,
            "espesor": None,
            "descripcion": " + ".join([f"{p['nombre']} ({p['area']} m², R {p['r']} dB)" for p in parts]),
            "componentes": parts,
            "objetivo": req,
        }, key_prefix="save_composite")



def project_rooms(project):
    rooms = project.get("recintos", [])
    if not isinstance(rooms, list):
        rooms = []
    return rooms


def upsert_room(project_id, room):
    projects = load_projects()
    if project_id not in projects:
        return False

    project = projects[project_id]
    rooms = project_rooms(project)
    room = dict(room)

    name = str(room.get("nombre", "")).strip()
    if not name:
        return False

    room_id = "room_" + "".join(ch.lower() if ch.isalnum() else "_" for ch in name)
    room_id = "_".join([x for x in room_id.split("_") if x])
    room["id"] = room_id
    room["nombre"] = name

    found = False
    for i, r in enumerate(rooms):
        if r.get("id") == room_id:
            rooms[i] = room
            found = True
            break

    if not found:
        rooms.append(room)

    project["recintos"] = rooms
    project["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_projects(projects)
    return True


def delete_room(project_id, room_id):
    projects = load_projects()
    if project_id not in projects:
        return False
    rooms = [r for r in project_rooms(projects[project_id]) if r.get("id") != room_id]
    projects[project_id]["recintos"] = rooms
    projects[project_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_projects(projects)
    return True



def delete_requirement(project_id, requirement_id):
    projects = load_projects()
    if project_id not in projects:
        return False

    reqs = [r for r in project_requirements(projects[project_id]) if r.get("id") != requirement_id]
    projects[project_id]["requerimientos"] = reqs

    active = projects[project_id].get("requerimiento_activo", {})
    if isinstance(active, dict) and active.get("id") == requirement_id:
        projects[project_id]["requerimiento_activo"] = reqs[-1] if reqs else {}

    projects[project_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_projects(projects)

    if st.session_state.get("active_requirement_id") == requirement_id:
        st.session_state.pop("active_requirement_id", None)
        st.session_state.pop("active_requirement", None)

    return True


def requirement_matrix_dataframe(project):
    reqs = project_requirements(project)
    rows = []
    for r in reqs:
        sols_all = r.get("soluciones", [])
        sols = sonara_select_report_solutions(sols_all)
        best = ""
        best_status = "Pendiente"
        if sols:
            scored = []
            for s in sols:
                estado, delta = solution_status(s, r)
                scored.append((estado, delta, s))
            # Prioriza cumple, luego menor déficit absoluto
            scored_sorted = sorted(
                scored,
                key=lambda x: (0 if x[0] == "Cumple" else 1, 999 if x[1] is None else abs(float(x[1])))
            )
            best_status, _, best_sol = scored_sorted[0]
            best = best_sol.get("nombre", "")
        rows.append({
            "Emisor": r.get("recinto_emisor", ""),
            "Receptor": r.get("recinto_receptor", ""),
            "Elemento": r.get("tipo_elemento", ""),
            "Objetivo": f"{r.get('indicador','')} {r.get('sentido','')} {r.get('valor','')} {r.get('unidad','')}",
            "Norma": r.get("norma", ""),
            "Soluciones": len(sols),
            "Mejor solución": best,
            "Estado": best_status,
        })
    return pd.DataFrame(rows)



# =========================================================
# SONARA 1.1.7 - HELPERS INFORME OPTIMIZADO
# =========================================================

def sonara_is_optimized_solution(sol):
    """Detecta si una solución corresponde a una optimización IA."""
    if not isinstance(sol, dict):
        return False
    txt = " ".join([
        str(sol.get("tipo", "")),
        str(sol.get("tipo_calculo", "")),
        str(sol.get("estrategia", "")),
        str(sol.get("nombre", "")),
    ]).lower()
    return (
        "optimización ia" in txt
        or "optimizacion ia" in txt
        or txt.startswith("opt_")
        or "+ trasdosado" in txt
        or "cámara" in txt
        or "camara" in txt
        or "desacople" in txt
    )


def sonara_solution_has_cubicacion(sol):
    """Detecta si una solución tiene cubicación usable."""
    if not isinstance(sol, dict):
        return False
    cub = sol.get("cubicacion", {})
    if not isinstance(cub, dict):
        return False
    if cub.get("total") not in [None, ""]:
        try:
            return float(cub.get("total") or 0) >= 0
        except Exception:
            return True
    return bool(cub.get("items"))


def sonara_select_report_solutions(sols_all):
    """
    Para el informe se muestra solo la solución vigente del requerimiento:
    1) última optimización IA,
    2) última solución cubicada,
    3) última solución guardada.
    Así no aparecen a la vez solución base + mejora.
    """
    if not isinstance(sols_all, list):
        return []

    sols_all = [s for s in sols_all if isinstance(s, dict)]
    if not sols_all:
        return []

    sols_vigentes = [s for s in sols_all if s.get("es_solucion_vigente") is True]
    if sols_vigentes:
        return [sols_vigentes[-1]]

    sols_opt = [s for s in sols_all if sonara_is_optimized_solution(s)]
    if sols_opt:
        return [sols_opt[-1]]

    sols_cub = [s for s in sols_all if sonara_solution_has_cubicacion(s)]
    if sols_cub:
        return [sols_cub[-1]]

    return [sols_all[-1]]


def sonara_solution_cost_for_report(sol):
    """
    Costo robusto para informe:
    1) total de cubicación,
    2) suma de subtotales de partidas,
    3) costo_estimado/costo.
    """
    try:
        if not isinstance(sol, dict):
            return 0.0

        cub = sol.get("cubicacion", {})
        if isinstance(cub, dict) and cub:
            if cub.get("total") not in [None, ""]:
                return float(cub.get("total") or 0)

            total = 0.0
            for item in cub.get("items", []) or []:
                if not isinstance(item, dict):
                    continue
                subtotal = item.get("Subtotal", item.get("subtotal", None))
                if subtotal not in [None, ""]:
                    total += float(subtotal or 0)
                else:
                    cant = float(item.get("Cantidad", item.get("cantidad", 0)) or 0)
                    precio = float(item.get("Precio unitario", item.get("precio_unitario", 0)) or 0)
                    total += cant * precio

            if total > 0:
                return float(total)

        return float(sol.get("costo_estimado", sol.get("costo", 0)) or 0)

    except Exception:
        return 0.0


def project_report_dataframe(project):
    rows = []
    total_general = 0.0

    for r in project_requirements(project):
        sols_all = r.get("soluciones", [])
        sols = sonara_select_report_solutions(sols_all)
        objetivo_txt = f"{r.get('indicador','')} {r.get('sentido','')} {r.get('valor','')} {r.get('unidad','')}"
        if not sols:
            rows.append({
                "Emisor": r.get("recinto_emisor", ""),
                "Receptor": r.get("recinto_receptor", ""),
                "Elemento": r.get("tipo_elemento", ""),
                "Objetivo": objetivo_txt,
                "Descriptor": r.get("indicador", ""),
                "Solución": "Sin solución",
                "Resultado": "",
                "Estado": "Pendiente",
                "Composición": "",
                "Área neta [m²]": "",
                "Área bruta [m²]": "",
                "Vanos [m²]": "",
                "Masa [kg/m²]": "",
                "Espesor [mm]": "",
                "Cubicación / partidas": "",
                "Costo solución [CLP]": 0,
            })
        else:
            for s in sols:
                estado, delta = solution_status(s, r)
                valor_eval = solution_descriptor_value(s, r.get("indicador", "Rw"))

                # Corrección para soluciones optimizadas:
                # si solution_status no logra evaluar, se usa el valor directo de la solución.
                try:
                    indicador_req = r.get("indicador", "Rw")
                    objetivo_req = float(r.get("valor", 0) or 0)
                    valor_directo = valor_eval
                    if valor_directo is None:
                        valor_directo = s.get(indicador_req, s.get("resultado", s.get("Rw", None)))
                    if valor_directo is not None:
                        valor_directo = float(valor_directo)
                        if objetivo_req > 0:
                            estado = "Cumple" if valor_directo >= objetivo_req else "No cumple"
                except Exception:
                    pass

                cub = solution_cubicacion_summary(s)
                costo = sonara_solution_cost_for_report(s)
                total_general += float(costo or 0)

                rows.append({
                    "Emisor": r.get("recinto_emisor", ""),
                    "Receptor": r.get("recinto_receptor", ""),
                    "Elemento": r.get("tipo_elemento", ""),
                    "Objetivo": objetivo_txt,
                    "Descriptor": r.get("indicador", ""),
                    "Solución": s.get("nombre", ""),
                    "Resultado": (
                        s.get("resultado_label", "")
                        if valor_eval is None
                        else f"{r.get('indicador','')} = {round(float(valor_eval), 1)} dB"
                    ),
                    "Estado": estado,
                    "Composición": s.get("composicion") or solution_composition_text(s),
                    "Área neta [m²]": cub.get("area_neta", ""),
                    "Área bruta [m²]": cub.get("area_bruta", ""),
                    "Vanos [m²]": cub.get("area_vanos", ""),
                    "Masa [kg/m²]": s.get("masa", ""),
                    "Espesor [mm]": s.get("espesor", ""),
                    "Cubicación / partidas": cub.get("items", ""),
                    "Costo solución [CLP]": round(float(costo or 0), 0),
                })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = pd.concat([
            df,
            pd.DataFrame([{
                "Emisor": "",
                "Receptor": "",
                "Elemento": "",
                "Objetivo": "",
                "Descriptor": "",
                "Solución": "TOTAL PROYECTO",
                "Resultado": "",
                "Estado": "",
                "Composición": "",
                "Área neta [m²]": "",
                "Área bruta [m²]": "",
                "Vanos [m²]": "",
                "Masa [kg/m²]": "",
                "Espesor [mm]": "",
                "Cubicación / partidas": "",
                "Costo solución [CLP]": round(total_general, 0),
            }])
        ], ignore_index=True)
    return df



def app_project_calculator_embedded(project, requirement):
    """
    Calculadora interna del proyecto.
    Mantiene el flujo del proyecto: requerimiento -> diseño -> cálculo -> guardar solución.
    """
    st.markdown(
        """
        <div class='project-flow-card'>
            <div class='project-flow-title'>Diseñar solución dentro del proyecto</div>
            <div class='project-flow-text'>
            Diseña el paramento según el requerimiento seleccionado. Al guardar, SONARA lo evalúa contra la meta activa del proyecto.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    objetivo = requirement or project.get("requerimiento_activo") or {}
    indicador = objetivo.get("indicador", "Rw")
    tipo_elemento_req = objetivo.get("tipo_elemento", "Paramento vertical")

    # Selector de calculadora según requerimiento
    if tipo_elemento_req in ["Paramento horizontal", "Entrepiso", "Impacto"]:
        calc_mode_default = "Ruido de impacto"
    elif indicador in ["L'nT,w", "Ln,w", "L'nT,w+CI"]:
        calc_mode_default = "Ruido de impacto"
    else:
        calc_mode_default = "Ruido aéreo"

    calc_mode = st.radio(
        "Calculadora del requerimiento",
        ["Solución compuesta", "Ruido aéreo", "Ruido de impacto", "ISO 12354-1"],
        index=0 if tipo_elemento_req in ["Fachada", "Puerta", "Ventana", "Paramento vertical"] else 2,
        horizontal=True,
        key="project_embedded_calc_mode"
    )

    st.markdown(
        f"""
        <div class='result-note'>
        Requerimiento activo: <b>{objetivo.get('elemento','')}</b> · 
        Meta: <b>{indicador} {objetivo.get('sentido','')} {objetivo.get('valor','')} {objetivo.get('unidad','')}</b>.
        </div>
        """,
        unsafe_allow_html=True
    )

    if calc_mode == "Solución compuesta":
        app_composite_solution(project, objetivo)
    elif calc_mode == "Ruido aéreo":
        app_calculator()
    elif calc_mode == "Ruido de impacto":
        app_impacto()
    else:
        app_iso12354()


def app_proyectos():
    st.markdown(
        "<h1 style='color:#FFFFFF;margin-bottom:8px;'>Proyecto</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='project-panel'>
            <div class='project-panel-title'>SONARA · Asistente de diseño acústico por proyecto</div>
            <div class='project-panel-text'>
            Flujo v1.0: crea el proyecto, define recintos, arma la matriz de elementos a diseñar,
            calcula cada solución dentro del proyecto, optimiza, cubica y prepara el informe.
            </div>
            <span class='project-pill'>1. Proyecto</span>
            <span class='project-pill'>2. Recintos</span>
            <span class='project-pill'>3. Matriz acústica</span>
            <span class='project-pill'>4. Diseñar</span>
            <span class='project-pill'>5. Informe</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    df_targets = norm_targets_df()
    trial_usage_banner()

    tab_datos, tab_recintos, tab_matriz, tab_diseno, tab_sol, tab_opt, tab_costos, tab_informe = st.tabs([
        "📌 Proyecto",
        "🏢 Recintos",
        "🧩 Elementos",
        "📐 Diseñar",
        "🧱 Soluciones",
        "🧠 Optimización IA",
        "📏 Cubicación",
        "📄 Informe"
    ])

    # 1. Proyecto
    with tab_datos:
        col1, col2 = st.columns([0.9, 1.3], gap="large")
        with col1:
            st.markdown("<div class='sonara-card-title'>Datos del proyecto</div>", unsafe_allow_html=True)
            nombre = st.text_input("Nombre del proyecto", value=st.session_state.get("project_nombre", "Proyecto SONARA"), key="project_v1_nombre")
            cliente = st.text_input("Cliente / mandante", value=st.session_state.get("project_cliente", ""), key="project_v1_cliente")
            sectores = sorted(df_targets["sector"].unique().tolist())
            tipo = st.selectbox("Tipo de proyecto", sectores, index=sectores.index(st.session_state.get("project_tipo", "Vivienda")) if st.session_state.get("project_tipo", "Vivienda") in sectores else 0, key="project_v1_tipo")
            normas = ["Todas"] + sorted(df_targets[df_targets["sector"] == tipo]["norma"].unique().tolist())
            norma = st.selectbox("Norma / referencia principal", normas, key="project_v1_norma")
            if st.button("💾 Crear / actualizar proyecto", use_container_width=True, key="project_v1_save"):
                df_base = df_targets[df_targets["sector"] == tipo].copy()
                if norma != "Todas":
                    df_base = df_base[df_base["norma"] == norma].copy()
                if df_base.empty:
                    df_base = df_targets[df_targets["sector"] == tipo].copy()
                r0 = df_base.iloc[0]
                objetivo_default = {
                    "sector": r0["sector"], "norma": r0["norma"], "elemento": r0["elemento"],
                    "indicador": r0["indicador"], "sentido": r0["sentido"], "valor": float(r0["valor"]),
                    "unidad": r0["unidad"], "fuente": r0["fuente"],
                    "recinto_emisor": "", "recinto_receptor": "", "tipo_elemento": "Paramento vertical",
                }
                pid = upsert_project(nombre, tipo, norma, objetivo_default)
                if pid:
                    projects = load_projects()
                    projects[pid]["cliente"] = cliente
                    projects[pid].setdefault("recintos", [])
                    projects[pid]["requerimientos"] = project_requirements(projects[pid])
                    projects[pid]["requerimiento_activo"] = {}
                    save_projects(projects)
                    st.session_state["project_nombre"] = nombre
                    st.session_state["project_cliente"] = cliente
                    st.session_state["project_tipo"] = tipo
                    st.success(f"Proyecto activo: {nombre}")

        with col2:
            pid, p = active_project()
            if p:
                reqs = project_requirements(p)
                rooms = project_rooms(p)
                df_matrix = requirement_matrix_dataframe(p)
                total_req = len(reqs)
                total_sol = sum(len(r.get("soluciones", [])) for r in reqs)
                cumple = 0
                for r in reqs:
                    for s in r.get("soluciones", []):
                        estado, _ = solution_status(s, r)
                        if estado == "Cumple":
                            cumple += 1
                st.markdown(
                    f"""
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
                        <div class="result-card"><div class="result-label">Proyecto</div><div class="result-value" style="font-size:21px;">{p.get('nombre')}</div><div class="result-unit">{p.get('tipo')}</div></div>
                        <div class="result-card"><div class="result-label">Recintos</div><div class="result-value">{len(rooms)}</div><div class="result-unit">creados</div></div>
                        <div class="result-card"><div class="result-label">Elementos</div><div class="result-value">{total_req}</div><div class="result-unit">a diseñar</div></div>
                        <div class="result-card"><div class="result-label">Soluciones</div><div class="result-value">{total_sol}</div><div class="result-unit">{cumple} cumplen</div></div>
                    </div>
                    <div class='project-flow-card'>
                        <div class='project-flow-title'>Estado del proyecto</div>
                        <div class='project-flow-text'>
                        Cliente: <b>{p.get('cliente','-')}</b><br>
                        Norma/referencia principal: <b>{p.get('norma','Todas')}</b><br>
                        Proyectos privados del usuario: <b>{current_user_project_file().name}</b><br>
                        Siguiente paso recomendado: crear recintos y luego generar la matriz acústica.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.info("Crea un proyecto para comenzar.")

    # 2. Recintos
    with tab_recintos:
        pid, p = active_project()
        if not p:
            st.warning("Primero crea un proyecto.")
        else:
            st.markdown("<div class='sonara-card-title'>Recintos del proyecto</div>", unsafe_allow_html=True)
            col1, col2 = st.columns([0.85, 1.2], gap="large")
            with col1:
                nombre_rec = st.text_input("Nombre recinto", value="Oficina 101", key="room_name")
                uso_rec = st.selectbox("Uso / tipo de recinto", ["Oficina", "Sala reunión", "Dormitorio", "Pasillo", "Consulta médica", "Aula", "Sala música", "Baño", "Exterior", "Sala máquinas", "Otro"], key="room_use")
                piso_rec = st.text_input("Nivel / piso", value="Nivel 1", key="room_level")
                area_rec = st.number_input("Área [m²]", value=12.0, min_value=0.0, step=0.5, key="room_area")
                volumen_rec = st.number_input("Volumen [m³]", value=35.0, min_value=0.0, step=1.0, key="room_volume")
                if st.button("➕ Agregar / actualizar recinto", use_container_width=True, key="room_add"):
                    ok = upsert_room(pid, {"nombre": nombre_rec, "uso": uso_rec, "nivel": piso_rec, "area": area_rec, "volumen": volumen_rec})
                    if ok:
                        st.success("Recinto guardado.")
                    else:
                        st.error("No se pudo guardar el recinto.")
            with col2:
                rooms = project_rooms(active_project()[1])
                if not rooms:
                    st.info("Aún no hay recintos.")
                else:
                    df_rooms = pd.DataFrame(rooms)
                    st.dataframe(df_rooms, use_container_width=True, hide_index=True, height=360)
                    room_names = [r.get("nombre") for r in rooms]
                    del_room = st.selectbox("Eliminar recinto", [""] + room_names, key="room_delete_select")
                    if del_room and st.button("🗑 Eliminar recinto seleccionado", use_container_width=True, key="room_delete_btn"):
                        rid = next((r.get("id") for r in rooms if r.get("nombre") == del_room), None)
                        if rid:
                            delete_room(pid, rid)
                            st.success("Recinto eliminado.")

    # 3. Matriz / Elementos a diseñar
    with tab_matriz:
        pid, p = active_project()
        if not p:
            st.warning("Primero crea un proyecto.")
        else:
            rooms = project_rooms(p)
            if len(rooms) < 1:
                st.warning("Crea al menos un recinto. Para fachadas puedes usar receptor 'Exterior'.")
            else:
                st.markdown("<div class='sonara-card-title'>Elemento a diseñar / matriz acústica</div>", unsafe_allow_html=True)
                room_names = [r.get("nombre") for r in rooms]
                if "Exterior" not in room_names:
                    room_names_ext = room_names + ["Exterior"]
                else:
                    room_names_ext = room_names

                col1, col2, col3 = st.columns(3, gap="large")
                with col1:
                    emisor = st.selectbox("Recinto emisor", room_names_ext, key="matrix_emisor")
                with col2:
                    receptor = st.selectbox("Recinto receptor", room_names_ext, index=min(1, len(room_names_ext)-1), key="matrix_receptor")
                with col3:
                    tipo_elemento = st.selectbox("Elemento", ["Paramento vertical", "Paramento horizontal", "Fachada", "Ventana", "Puerta", "Instalaciones / HVAC", "Reverberación"], key="matrix_tipo")

                df_sector = df_targets[df_targets["sector"] == p.get("tipo")].copy()
                if p.get("norma") != "Todas":
                    df_sector = df_sector[df_sector["norma"] == p.get("norma")].copy()
                if df_sector.empty:
                    df_sector = df_targets[df_targets["sector"] == p.get("tipo")].copy()

                df_req = df_sector.copy()
                if tipo_elemento == "Paramento horizontal":
                    df_req = df_req[df_req["indicador"].isin(["L'nT,w", "Ln,w", "L'nT,w+CI", "DnT,w", "Rw"])]
                elif tipo_elemento in ["Paramento vertical", "Puerta", "Ventana"]:
                    df_req = df_req[df_req["indicador"].isin(["Rw", "DnT,w", "DnT,A", "RA", "D2m,nT,Atr"])]
                elif tipo_elemento == "Fachada":
                    df_req = df_req[df_req["indicador"].isin(["D2m,nT,Atr", "Rw", "RA", "LAeq"])]
                elif tipo_elemento == "Instalaciones / HVAC":
                    df_req = df_req[df_req["indicador"].isin(["NR", "NC", "NC/NR", "LAeq"])]
                elif tipo_elemento == "Reverberación":
                    df_req = df_req[df_req["indicador"].isin(["T", "TR", "RT"])]

                if df_req.empty:
                    df_req = df_sector.copy()

                opciones = (
                    df_req["elemento"].astype(str) + " · " + df_req["indicador"].astype(str) + " " +
                    df_req["sentido"].astype(str) + " " + df_req["valor"].astype(str) + " " +
                    df_req["unidad"].astype(str) + " · " + df_req["norma"].astype(str)
                ).tolist()
                seleccion = st.selectbox("Requerimiento acústico", opciones, key="matrix_target")
                row = df_req.iloc[opciones.index(seleccion)]

                requerimiento = {
                    "sector": row["sector"], "norma": row["norma"], "elemento": row["elemento"],
                    "indicador": row["indicador"], "sentido": row["sentido"], "valor": float(row["valor"]),
                    "unidad": row["unidad"], "fuente": row["fuente"],
                    "recinto_emisor": emisor, "recinto_receptor": receptor, "tipo_elemento": tipo_elemento,
                }

                c1, c2 = st.columns([0.7, 0.3])
                with c1:
                    if st.button("➕ Agregar elemento a la matriz", use_container_width=True, key="matrix_add"):
                        req_id = upsert_requirement(pid, requerimiento)
                        st.success("Elemento agregado a la matriz y dejado como activo.")
                with c2:
                    if st.button("📐 Diseñar este elemento", use_container_width=True, key="matrix_design"):
                        req_id = upsert_requirement(pid, requerimiento)
                        st.success("Elemento activo. Ve a la pestaña Diseñar.")

                st.markdown("<hr>", unsafe_allow_html=True)
                df_matrix = requirement_matrix_dataframe(active_project()[1])
                if df_matrix.empty:
                    st.info("Aún no hay elementos en la matriz.")
                else:
                    st.dataframe(df_matrix, use_container_width=True, hide_index=True, height=380)

                    reqs_delete = project_requirements(active_project()[1])
                    labels_delete = [
                        f"{r.get('recinto_emisor','')} → {r.get('recinto_receptor','')} · {r.get('tipo_elemento','')} · {r.get('indicador','')} {r.get('sentido','')} {r.get('valor','')} {r.get('unidad','')}"
                        for r in reqs_delete
                    ]

                    with st.expander("🗑 Eliminar elemento de la matriz", expanded=False):
                        del_label = st.selectbox("Elemento a eliminar", [""] + labels_delete, key="matrix_delete_select")
                        if del_label:
                            idx_del = labels_delete.index(del_label)
                            req_del = reqs_delete[idx_del]
                            if st.button("Eliminar elemento seleccionado", use_container_width=True, key="matrix_delete_btn"):
                                delete_requirement(pid, req_del.get("id"))
                                st.success("Elemento eliminado de la matriz.")
                                st.rerun()

    # 4. Diseñar
    with tab_diseno:
        pid, p = active_project()
        if not p:
            st.warning("Primero crea un proyecto.")
        else:
            reqs = project_requirements(p)
            if not reqs:
                st.warning("Primero agrega un elemento a diseñar en la matriz acústica.")
            else:
                labels = [
                    f"{r.get('recinto_emisor','')} → {r.get('recinto_receptor','')} · {r.get('tipo_elemento','')} · {r.get('indicador','')} {r.get('sentido','')} {r.get('valor','')} {r.get('unidad','')}"
                    for r in reqs
                ]
                active_req = active_requirement(p)
                default_idx = 0
                for i, r in enumerate(reqs):
                    if active_req and r.get("id") == active_req.get("id"):
                        default_idx = i
                selected_label = st.selectbox("Elemento activo a diseñar", labels, index=default_idx, key="design_req_select")
                req = reqs[labels.index(selected_label)]
                st.session_state["active_requirement_id"] = req.get("id")
                st.session_state["active_requirement"] = req
                if req:
                    app_project_calculator_embedded(p, req)
                else:
                    st.warning("Primero agrega un elemento a diseñar en la matriz acústica.")

    # 5. Soluciones
    with tab_sol:
        pid, p = active_project()
        if not p:
            st.warning("Crea un proyecto.")
        else:
            reqs = project_requirements(p)
            df_matrix = requirement_matrix_dataframe(p)
            st.markdown("<div class='sonara-card-title'>Soluciones por elemento</div>", unsafe_allow_html=True)
            if df_matrix.empty:
                st.info("No hay elementos ni soluciones.")
            else:
                st.dataframe(df_matrix, use_container_width=True, hide_index=True, height=330)
                req_labels = [
                    f"{r.get('recinto_emisor','')} → {r.get('recinto_receptor','')} · {r.get('tipo_elemento','')}"
                    for r in reqs
                ]
                selected_req_label = st.selectbox("Ver soluciones de", req_labels, key="sol_req_v1")
                selected_req = reqs[req_labels.index(selected_req_label)]
                st.session_state["active_requirement_id"] = selected_req.get("id")
                sols = selected_req.get("soluciones", [])
                if not sols:
                    st.info("Este elemento no tiene soluciones guardadas.")
                else:
                    rows = []
                    for sol in sols:
                        estado, delta = solution_status(sol, selected_req)
                        rows.append({"Nombre": sol.get("nombre"), "Tipo": sol.get("tipo_calculo"), "Resultado": sol.get("resultado_label"), "Estado": estado, "Δ": delta, "Fecha": sol.get("created_at")})
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    sel = st.selectbox("Seleccionar solución", [r["Nombre"] for r in rows], key="sol_pick_v1")
                    sol = sols[[r["Nombre"] for r in rows].index(sel)]
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("🧠 Optimizar", use_container_width=True, key="opt_from_sol_v1"):
                            st.session_state["selected_solution_for_optimizer"] = sol
                            st.session_state["selected_requirement_for_optimizer"] = selected_req
                            st.success("Enviada a optimización.")
                    with c2:
                        if st.button("💰 Cubicar", use_container_width=True, key="cub_from_sol_v1"):
                            st.session_state["selected_solution_for_cubicacion"] = sol
                            st.session_state["selected_requirement_for_cubicacion"] = selected_req
                            st.success("Enviada a cubicación.")
                    with c3:
                        if st.button("🗑 Eliminar", use_container_width=True, key="del_from_sol_v1"):
                            projects = load_projects()
                            reqs2 = project_requirements(projects[pid])
                            for r in reqs2:
                                if r.get("id") == selected_req.get("id"):
                                    r["soluciones"] = [s for s in r.get("soluciones", []) if s.get("id") != sol.get("id")]
                            projects[pid]["requerimientos"] = reqs2
                            save_projects(projects)
                            st.success("Eliminada.")

    # 6. Optimización
    with tab_opt:
        sol = st.session_state.get("selected_solution_for_optimizer")
        req = st.session_state.get("selected_requirement_for_optimizer")
        if sol and req:
            st.markdown(f"<div class='result-note'>Optimizando: <b>{sol.get('nombre')}</b> para <b>{req.get('recinto_emisor')} → {req.get('recinto_receptor')}</b>.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='result-note'>Selecciona una solución guardada para optimizarla o usa el optimizador general.</div>", unsafe_allow_html=True)
        app_optimizador()

    # 7. Costos
    with tab_costos:
        sol = st.session_state.get("selected_solution_for_cubicacion")
        req = st.session_state.get("selected_requirement_for_cubicacion")
        if sol and req:
            em = req.get("recinto_emisor", "") or "Sin emisor"
            rec = req.get("recinto_receptor", "") or "Sin receptor"
            elem = req.get("tipo_elemento", "")
            st.markdown(
                f"<div class='result-note'>Cubicando solución guardada: <b>{sol.get('nombre')}</b> · <b>{em} → {rec}</b> · {elem}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown("<div class='result-note'>Selecciona una solución guardada en Proyecto → Soluciones y presiona Cubicar.</div>", unsafe_allow_html=True)
        app_cubicacion()

    # 8. Informe
    with tab_informe:
        pid, p = active_project()
        if not p:
            st.warning("Crea un proyecto.")
        else:
            df_report = project_report_dataframe(p)
            st.markdown(
                f"""
                <div class='project-flow-card'>
                    <div class='project-flow-title'>Informe preliminar · {p.get('nombre')}</div>
                    <div class='project-flow-text'>
                    Resumen por recintos, elementos evaluados, objetivos, soluciones y estado de cumplimiento.
                    Esta tabla será la base para la exportación PDF.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if df_report.empty:
                st.info("No hay información suficiente para informe.")
            else:
                total_costo = 0.0
                if "Costo solución [CLP]" in df_report.columns:
                    try:
                        total_costo = float(df_report[df_report["Solución"] == "TOTAL PROYECTO"]["Costo solución [CLP]"].iloc[0])
                    except Exception:
                        total_costo = float(pd.to_numeric(df_report["Costo solución [CLP]"], errors="coerce").fillna(0).sum())

                st.markdown(
                    f"""
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;">
                        <div class="result-card"><div class="result-label">Elementos</div><div class="result-value">{max(len(df_report)-1,0)}</div><div class="result-unit">filas</div></div>
                        <div class="result-card"><div class="result-label">Costo total</div><div class="result-value" style="font-size:32px;">${total_costo:,.0f}</div><div class="result-unit">CLP</div></div>
                        <div class="result-card"><div class="result-label">Estado</div><div class="result-value" style="font-size:24px;">Informe</div><div class="result-unit">preliminar</div></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.dataframe(df_report, use_container_width=True, hide_index=True, height=480)
                st.download_button("⬇ Descargar informe CSV", data=df_report.to_csv(index=False).encode("utf-8"), file_name="sonara_informe_preliminar.csv", mime="text/csv", use_container_width=True)

            with st.expander("📚 Base normativa usada por SONARA"):
                sector_filter = st.multiselect("Filtrar sector", sorted(df_targets["sector"].unique().tolist()), default=sorted(df_targets["sector"].unique().tolist()), key="targets_filter_report")
                df_show = df_targets[df_targets["sector"].isin(sector_filter)].copy()
                st.dataframe(df_show, use_container_width=True, hide_index=True, height=340)
                st.download_button("⬇ Descargar sonara_targets.csv", data=df_show.to_csv(index=False).encode("utf-8"), file_name="sonara_targets.csv", mime="text/csv", use_container_width=True)



def app_configuracion():
    st.markdown("<h1 style='color:#FFFFFF;margin-bottom:8px;'>Configuración</h1>", unsafe_allow_html=True)

    email = st.session_state.get("email", "")
    profile = user_profile(email)
    settings = load_settings()
    user_settings = settings.get(email, {})

    tabs = st.tabs(["👤 Perfil", "🔐 Licencia", "⚙️ Preferencias", "💰 Costos", "📦 Datos"])

    with tabs[0]:
        st.markdown("<div class='sonara-card-title'>Perfil profesional para informes</div>", unsafe_allow_html=True)
        nombre = st.text_input("Nombre", value=str(profile.get("nombre", email)), key="cfg_nombre")
        empresa = st.text_input("Empresa / institución", value=str(profile.get("empresa", "")), key="cfg_empresa")
        cargo = st.text_input("Cargo", value=str(profile.get("cargo", "")), key="cfg_cargo")
        firma = st.text_area("Firma / pie profesional", value=user_settings.get("firma", ""), key="cfg_firma")
        if st.button("💾 Guardar perfil", use_container_width=True):
            update_user_profile(email, nombre, empresa, cargo)
            settings.setdefault(email, {})
            settings[email]["firma"] = firma
            save_settings(settings)
            st.success("Perfil guardado.")

    with tabs[1]:
        lic = st.session_state.get("license_info", {})
        trial_usage_banner()
        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
                <div class="result-card"><div class="result-label">Usuario</div><div class="result-value" style="font-size:20px;">{email}</div><div class="result-unit">correo</div></div>
                <div class="result-card"><div class="result-label">Plan</div><div class="result-value" style="font-size:24px;">{lic.get('type','-')}</div><div class="result-unit">licencia</div></div>
                <div class="result-card"><div class="result-label">Vigencia</div><div class="result-value" style="font-size:20px;">{lic.get('expires','-')}</div><div class="result-unit">expira</div></div>
                <div class="result-card"><div class="result-label">Versión</div><div class="result-value" style="font-size:20px;">{APP_VERSION}</div><div class="result-unit">SONARA</div></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with tabs[2]:
        st.markdown("<div class='sonara-card-title'>Preferencias de cálculo</div>", unsafe_allow_html=True)
        modo = st.selectbox("Modo de usuario", ["Asistente", "Avanzado acústico"], index=0 if user_settings.get("modo", "Asistente") == "Asistente" else 1)
        mostrar_adv = st.checkbox("Mostrar advertencias normativas", value=user_settings.get("mostrar_adv", True))
        mostrar_inc = st.checkbox("Mostrar incertidumbre / notas de cautela", value=user_settings.get("mostrar_inc", True))
        flancos_default = st.checkbox("Considerar flancos por defecto", value=user_settings.get("flancos_default", True))
        if st.button("💾 Guardar preferencias", use_container_width=True):
            settings.setdefault(email, {})
            settings[email].update({
                "modo": modo,
                "mostrar_adv": mostrar_adv,
                "mostrar_inc": mostrar_inc,
                "flancos_default": flancos_default,
            })
            save_settings(settings)
            st.success("Preferencias guardadas.")

    with tabs[3]:
        st.markdown("<div class='sonara-card-title'>Costos y moneda</div>", unsafe_allow_html=True)
        moneda = st.selectbox("Moneda", ["CLP", "USD", "EUR"], index=["CLP", "USD", "EUR"].index(user_settings.get("moneda", "CLP")) if user_settings.get("moneda", "CLP") in ["CLP", "USD", "EUR"] else 0)
        iva = st.number_input("IVA / impuesto [%]", value=float(user_settings.get("iva", 19.0)), min_value=0.0, max_value=40.0, step=0.5)
        factor_mo = st.number_input("Factor mano de obra", value=float(user_settings.get("factor_mo", 1.0)), min_value=0.1, max_value=5.0, step=0.1)
        if st.button("💾 Guardar costos", use_container_width=True):
            settings.setdefault(email, {})
            settings[email].update({"moneda": moneda, "iva": iva, "factor_mo": factor_mo})
            save_settings(settings)
            st.success("Configuración de costos guardada.")

    with tabs[4]:
        st.markdown("<div class='sonara-card-title'>Datos locales</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class='result-note'>
            SONARA guarda localmente usuarios, materiales, configuración y proyectos en la carpeta <b>data/</b>.
            En una versión web productiva, esto debería migrar a una base de datos por usuario.
            </div>
            """,
            unsafe_allow_html=True
        )
        user_projects = current_user_project_file(email)
        files_to_download = [USERS_CSV, user_projects, MATERIALS_CSV, SETTINGS_JSON]
        for f in files_to_download:
            if f.exists():
                st.download_button(f"⬇ Descargar {f.name}", data=f.read_bytes(), file_name=f.name, use_container_width=True)

        st.markdown(
            f"<div class='result-note'>Archivo de proyectos del usuario activo: <b>{user_projects}</b></div>",
            unsafe_allow_html=True
        )


def app_ayuda():
    st.markdown("<h1 style='color:#FFFFFF;margin-bottom:8px;'>Ayuda</h1>", unsafe_allow_html=True)

    tabs = st.tabs(["🚀 Inicio rápido", "📘 Conceptos", "🏗️ Casos de uso", "📚 Referencias", "📊 Validación LOSCAA", "🛟 Soporte"])

    with tabs[0]:
        st.markdown(
            """
            <div class='project-flow-card'>
                <div class='project-flow-title'>Flujo recomendado SONARA</div>
                <div class='project-flow-text'>
                1. Crea un proyecto.<br>
                2. Agrega recintos: oficinas, dormitorios, aulas, consultas, pasillos o exterior.<br>
                3. Crea la matriz acústica: emisor → receptor + tipo de elemento.<br>
                4. Diseña la solución desde la calculadora integrada.<br>
                5. Guarda la solución en el requerimiento correspondiente.<br>
                6. Revisa cumplimiento, optimiza, cubica y genera informe preliminar.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with tabs[1]:
        conceptos = pd.DataFrame([
            {"Concepto": "Rw", "Uso": "Aislamiento de laboratorio de un elemento", "Interpretación": "Mayor es mejor"},
            {"Concepto": "DnT,w", "Uso": "Aislamiento medido/predicho entre recintos", "Interpretación": "Mayor es mejor"},
            {"Concepto": "D2m,nT,Atr", "Uso": "Aislamiento de fachada frente a ruido exterior", "Interpretación": "Mayor es mejor"},
            {"Concepto": "L'nT,w", "Uso": "Ruido de impacto normalizado en obra", "Interpretación": "Menor es mejor"},
            {"Concepto": "NC / NR", "Uso": "Ruido de instalaciones HVAC", "Interpretación": "Menor es mejor"},
            {"Concepto": "T / TR", "Uso": "Tiempo de reverberación", "Interpretación": "Depende del uso del recinto"},
        ])
        st.dataframe(conceptos, use_container_width=True, hide_index=True)
        st.markdown(
            "<div class='result-note'>Regla práctica: Rw 35 bajo · Rw 45 bueno · Rw 55 muy bueno · Rw 65 alto desempeño.</div>",
            unsafe_allow_html=True
        )

    with tabs[2]:
        st.markdown(
            """
            <div class='sonara-card'>
                <div class='sonara-card-title'>Casos típicos</div>
                <ul style='color:#DCEBFF;line-height:1.8;'>
                    <li><b>Vivienda:</b> medianeros, entrepisos, fachadas y recintos sensibles.</li>
                    <li><b>Oficinas:</b> oficina-oficina, salas de reunión, salas confidenciales y open space.</li>
                    <li><b>Hospital:</b> consultas, salas de tratamiento, habitaciones y ruido HVAC.</li>
                    <li><b>Educación:</b> aulas, música, gimnasios, bibliotecas y reverberación.</li>
                    <li><b>Fachadas:</b> tabique opaco + ventana + puerta/rejilla como solución compuesta.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    with tabs[3]:
        refs = pd.DataFrame([
            {"Área": "Vivienda Chile", "Referencia": "OGUC art. 4.1.6 / NCh352/2"},
            {"Área": "Aislamiento aéreo", "Referencia": "ISO 717-1, ISO 10140-2, ISO 16283-1"},
            {"Área": "Predicción edificios", "Referencia": "ISO 12354-1, ISO 12354-2, ISO 12354-3"},
            {"Área": "Hospitales", "Referencia": "HTM 08-01"},
            {"Área": "Educación", "Referencia": "BB93, ANSI/ASA S12.60"},
            {"Área": "HVAC", "Referencia": "ASHRAE Sound and Vibration, CIBSE Guide B5"},
            {"Área": "España / UK", "Referencia": "DB-HR, Approved Document E, BS8233"},
        ])
        st.dataframe(refs, use_container_width=True, hide_index=True)

    with tabs[4]:
        app_loscaa_validation()

    with tabs[5]:
        st.markdown(
            """
            <div class='project-flow-card'>
                <div class='project-flow-title'>Soporte y buenas prácticas</div>
                <div class='project-flow-text'>
                SONARA es una herramienta de diseño preliminar y apoyo técnico. Para informes contractuales o certificaciones,
                valida siempre contra ensayos, mediciones en terreno, normativa oficial vigente y juicio profesional del especialista.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def placeholder(title):
    st.markdown(
        f"<div class='card'><div class='card-title'>{title}</div>"
        f"<div class='card-text'>Módulo en desarrollo.</div></div>",
        unsafe_allow_html=True
    )


ensure_files()

if "license_info" not in st.session_state:
    login_page()
else:
    page = sidebar(st.session_state.license_info)
    lic = st.session_state.license_info

    # Alias para sesiones antiguas
    if page == "Proyectos":
        page = "Proyecto"
    elif page == "Calculadora":
        page = "Calculadora libre"
    elif page == "Materiales":
        page = "Biblioteca de materiales"

    if not lic.get("allowed"):
        placeholder("Tu prueba gratuita ha finalizado")
    elif page == "Inicio":
        hero()
    elif page == "Calculadora libre":
        app_calculadora_master()
    elif page == "Proyecto":
        app_proyectos()
    elif page == "Biblioteca de materiales":
        app_materiales()
    elif page == "Configuración":
        app_configuracion()
    elif page == "Ayuda":
        app_ayuda()
    else:
        placeholder(page)
