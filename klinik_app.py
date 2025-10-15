import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import colorsys
from typing import Tuple, Dict, Any

# ---------- App Setup ----------
st.set_page_config(
    page_title="Klinik",
    page_icon="",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": "Klinik is an educational demo. It is NOT a medical device.",
    }
)

APP_NAME = "Klinik"
ACCENT = "#4F46E5"  # indigo
BACKGROUND = "#DDEBFF"  # light blue background

# ---------- Styles ----------
CSS = f"""
<style>
body {{
  background-color: {BACKGROUND};
}}

.small-muted {{ color:#555; font-size:.9rem; }}
.badge {{
  display:inline-block; padding:.25rem .6rem; border-radius:9999px;
  background:{ACCENT}20; color:{ACCENT}; font-weight:600; font-size:.8rem;
}}
.codepill {{
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  background:#00000010; padding:.15rem .45rem; border-radius:.4rem;
}}
hr.soft {{ border:none; height:1px; background:#eaecef; margin:1.1rem 0; }}
footer {{ visibility:hidden; }}

.hero {{
  text-align:center; padding:2.2rem 1rem 1.2rem 1rem;
}}
.hero h1 {{ margin:0; font-size:2.2rem; }}
.hero p {{ margin:.5rem 0 0 0; color:#222; }}

.card {{
  border:1px solid #eaecef; border-radius:1rem; padding:1rem; background:white;
}}
</style>
"""
st.write(CSS, unsafe_allow_html=True)

# ---------- Session State ----------
def init_state():
    if "route" not in st.session_state:
        st.session_state["route"] = "home"
    if "mucus_last" not in st.session_state:
        st.session_state["mucus_last"] = {}

init_state()

# ---------- Utils ----------
def rgb_to_hsv01(r: int, g: int, b: int) -> Tuple[float, float, float]:
    return colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)

def average_rgb(img: Image.Image) -> Tuple[int, int, int]:
    img = ImageOps.exif_transpose(img).convert("RGB")
    small = img.resize((96, 96))
    arr = np.asarray(small, dtype=np.uint8)
    center = arr[24:72, 24:72, :]
    med = np.median(center, axis=(0, 1))
    return tuple(int(x) for x in med)

def hex_chip(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    hx = f"#{r:02x}{g:02x}{b:02x}".upper()
    return f"""
<div style="display:flex;gap:.6rem;align-items:center;">
  <div style="width:22px;height:22px;border-radius:.4rem;border:1px solid #00000022;background:{hx};"></div>
  <code class="codepill">{hx}</code>
  <span class="small-muted">(RGB {r}, {g}, {b})</span>
</div>
"""

def format_float(x: float, nd=3) -> str:
    return f"{x:.{nd}f}"

# ---------- Color Classifier ----------
def classify_color_with_trace(rgb: Tuple[int, int, int]) -> Dict[str, Any]:
    r, g, b = rgb
    h, s, v = rgb_to_hsv01(r, g, b)
    hue = h * 360.0

    rules = []

    def add_rule(name: str, cond: bool, detail: str):
        rules.append({"name": name, "passed": bool(cond), "detail": detail})

    category, explanation, key, picked_rule = "uncertain", "Hard to classify.", "uncertain", "none"

    add_rule("Very dark (black test)", v < 0.18, f"V={format_float(v)} < 0.18")
    if v < 0.18:
        category, explanation, key, picked_rule = "black/very dark", "Very low brightness.", "black", "Very dark"
    else:
        add_rule("Clear test", (s < 0.08 and v > 0.75),
                 f"S={format_float(s)} < 0.08 and V={format_float(v)} > 0.75")
        if s < 0.08 and v > 0.75:
            category, explanation, key, picked_rule = "clear", "Low saturation, high brightness.", "clear", "Clear"
        else:
            add_rule("White/gray test", (s < 0.15 and v > 0.55),
                     f"S={format_float(s)} < 0.15 and V={format_float(v)} > 0.55")
            if s < 0.15 and v > 0.55:
                category, explanation, key, picked_rule = "white/gray", "Low saturation + mid brightness.", "white", "White/Gray"
            else:
                add_rule("Yellow hue band", (35 <= hue <= 75 and s >= 0.18),
                         f"35° ≤ H={format_float(hue, 1)}° ≤ 75° and S={format_float(s)} ≥ 0.18")
                if 35 <= hue <= 75 and s >= 0.18:
                    category, explanation, key, picked_rule = "yellow", "Hue in yellow range.", "yellow", "Yellow band"
                else:
                    add_rule("Green hue band", (75 < hue <= 170 and s >= 0.18),
                             f"75° < H={format_float(hue, 1)}_
