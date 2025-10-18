# klinik_app.py  (ASCII-safe, updated theme, tuned classifier, trace-only output)
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
    },
)

# ---------- Color Palette (requested) ----------
# Background:  #98c1d9
# Buttons:     #e0fbfc
# Text:        #293241
PRIMARY = "#293241"     # headings and text emphasis
ACCENT = "#e0fbfc"      # buttons
BACKGROUND = "#98c1d9"  # page background
TEXT_DARK = "#293241"   # all text

# ---------- Styles ----------
CSS = f"""
<style>
/* App background + text color */
.stApp {{
  background-color: {BACKGROUND};
  color: {TEXT_DARK};
  font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}}
h1, h2, h3, h4, h5, h6 {{ color: {TEXT_DARK}; }}
a {{ color: {TEXT_DARK}; text-decoration: underline; }}

.badge {{
  display:inline-block; padding:.25rem .6rem; border-radius:9999px;
  background: rgba(224, 251, 252, 0.6); color:{TEXT_DARK}; font-weight:600; font-size:.8rem;
}}
.codepill {{
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  background:#00000010; padding:.15rem .45rem; border-radius:.4rem; color:{TEXT_DARK};
}}
hr.soft {{ border:none; height:1px; background:#e6edf3; margin:1.1rem 0; }}
footer {{ visibility:hidden; }}

.hero {{ text-align:center; padding:2.2rem 1rem 1.2rem 1rem; }}
.hero h1 {{ margin:0; font-size:2.2rem; }}
.hero p {{ margin:.5rem 0 0 0; color:{TEXT_DARK}; }}

.card {{ border:1px solid #e6edf3; border-radius:1rem; padding:1rem; background:white; color:{TEXT_DARK}; }}

/* Buttons - keep text visible at all times */
.stButton > button {{
  background: {ACCENT} !important;
  color: {TEXT_DARK} !important;
  border: 1px solid #c5e9ee !important;
  border-radius: 10px !important;
  padding: 0.6rem 1rem !important;
  font-weight: 700 !important;
  box-shadow: 0 1px 2px rgba(16,24,40,0.05) !important;
  cursor: pointer !important;
  opacity: 1 !important;
}}
.stButton > button:hover {{ filter: brightness(0.96) !important; }}
.stButton > button:disabled {{
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}}
</style>
"""
st.write(CSS, unsafe_allow_html=True)

# ---------- Session State ----------
def init_state() -> None:
    if "route" not in st.session_state:
        st.session_state["route"] = "home"
    if "mucus_last" not in st.session_state:
        st.session_state["mucus_last"] = {}

init_state()

# ---------- Utils ----------
def rgb_to_hsv01(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Return HSV in 0..1 from 8-bit RGB."""
    return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

def average_rgb(img: Image.Image) -> Tuple[int, int, int]:
    """Median of a center crop from a downsized image for robustness."""
    img = ImageOps.exif_transpose(img).convert("RGB")
    small = img.resize((96, 96))
    arr = np.asarray(small, dtype=np.uint8)
    center = arr[24:72, 24:72, :]  # 48x48 center
    med = np.median(center, axis=(0, 1))
    return tuple(int(x) for x in med)

def format_float(x: float, nd: int = 3) -> str:
    return f"{x:.{nd}f}"

# ---------- Color Classifier (tuned with tolerances and amber band) ----------
def _hue_in_range(h_deg: float, lo: float, hi: float, eps: float = 0.8) -> bool:
    """Inclusive range with tolerance; supports wrap-around if lo > hi."""
    if lo <= hi:
        return (lo - eps) <= h_deg <= (hi + eps)
    return h_deg >= (lo - eps) or h_deg <= (hi + eps)

def classify_color_with_trace(rgb: Tuple[int, int, int]) -> Dict[str, Any]:
    r, g, b = rgb
    h, s, v = rgb_to_hsv01(r, g, b)     # 0..1
    hue = h * 360.0

    rules = []
    def add_rule(name: str, cond: bool, detail: str) -> None:
        rules.append({"name": name, "passed": bool(cond), "detail": detail})

    category = "uncertain"
    explanation = "Hard to classify."
    key = "uncertain"
    picked_rule = "none"

    # Order: darkness -> low-sat neutrals -> brown (requires darkness) -> chromatic bands
    # Thresholds:
    # - black/very dark: v < 0.16
    # - clear: s < 0.07 and v > 0.80
    # - white/gray: s < 0.18 and v > 0.60
    # - brown (dark warm): v < 0.45 and s >= 0.25 and 15 < hue < 50
    # - yellow/amber: 25..75 with s >= 0.16 and v >= 0.50
    # - green: 75..170 with s >= 0.20
    # - red/pink: hue <= 18 or hue >= 342 with s >= 0.20 and v > 0.25

    # 1) Very dark -> black
    add_rule("Very dark (black test)", v < 0.16, f"V={format_float(v)} < 0.16")
    if v < 0.16:
        category, explanation, key, picked_rule = "black/very dark", "Very low brightness.", "black", "Very dark"
    else:
        # 2) Clear
        add_rule("Clear test", (s < 0.07 and v > 0.80),
                 f"S={format_float(s)} < 0.07 and V={format_float(v)} > 0.80")
        if s < 0.07 and v > 0.80:
            category, explanation, key, picked_rule = "clear", "Low saturation, high brightness.", "clear", "Clear"
        else:
            # 3) White/gray
            add_rule("White/gray test", (s < 0.18 and v > 0.60),
                     f"S={format_float(s)} < 0.18 and V={format_float(v)} > 0.60")
            if s < 0.18 and v > 0.60:
                category, explanation, key, picked_rule = "white/gray", "Low saturation + mid brightness.", "white", "White/Gray"
            else:
                # 4) Brown requires darkness; prevents bright ambers being tagged brown
                add_rule("Brown warm/dark",
                         (v < 0.45 and s >= 0.25 and 15 < hue < 50),
                         f"V={format_float(v)} < 0.45 and S={format_float(s)} >= 0.25 and 15 < H={format_float(hue,1)} < 50")
                if v < 0.45 and s >= 0.25 and 15 < hue < 50:
                    category, explanation, key, picked_rule = "brown", "Dark warm hue.", "brown", "Brown warm/dark"
                else:
                    # 5) Yellow / Amber (wider band, lower sat floor, min brightness)
                    add_rule("Yellow/Amber hue band",
                             (_hue_in_range(hue, 25, 75) and s >= 0.16 and v >= 0.50),
                             f"25 <= H={format_float(hue,1)} <= 75 and S={format_float(s)} >= 0.16 and V={format_float(v)} >= 0.50")
                    if _hue_in_range(hue, 25, 75) and s >= 0.16 and v >= 0.50:
                        category, explanation, key, picked_rule = "yellow/amber", "Hue in yellow/amber range.", "yellow", "Yellow/Amber band"
                    else:
                        # 6) Green
                        add_rule("Green hue band",
                                 (_hue_in_range(hue, 75, 170) and s >= 0.20),
                                 f"75 <= H={format_float(hue,1)} <= 170 and S={format_float(s)} >= 0.20")
                        if _hue_in_range(hue, 75, 170) and s >= 0.20:
                            category, explanation, key, picked_rule = "green", "Hue in green range.", "green", "Green band"
                        else:
                            # 7) Red/Pink (wrap-around)
                            add_rule("Red/pink hue band",
                                     ((_hue_in_range(hue, 342, 360) or _hue_in_range(hue, 0, 18)) and s >= 0.20 and v > 0.25),
                                     f"(H <= 18 or H >= 342) with S={format_float(s)} >= 0.20 and V={format_float(v)} > 0.25")
                            if ((_hue_in_range(hue, 342, 360) or _hue_in_range(hue, 0, 18)) and s >= 0.20 and v > 0.25):
                                category, explanation, key, picked_rule = "red/pink", "Hue in red range.", "red", "Red/Pink band"

    # Guidance retained for internal use; not displayed in trace-only UI
    guidance = {
        "clear": ("Often normal hydration/irritation.",
                  ["Usually benign if you feel well.",
                   "Hydrate and keep an eye on changes.",
                   "Seek care if symptoms persist or worsen."]),
        "white": ("Common with congestion or drier mucus.",
                  ["Drink water, humidify air.",
                   "If more than ~10 days or worsening, check in with a clinician."]),
        "yellow": ("Inflammation; immune system is active.",
                  ["Rest and hydrate.",
                   "Color alone is not infection; see a clinician if fever or >10 days."]),
        "green": ("Stronger inflammation; can be infection.",
                  ["Hydrate; saline or gentle rinses can help.",
                   "If lasting beyond ~10 days or with fever, seek care."]),
        "brown": ("Old/dry blood or inhaled particles.",
                  ["Avoid smoke/dust; use saline.",
                   "If frequent or heavy, see a clinician."]),
        "red": ("Fresh blood in mucus.",
                ["Small streaks can be from irritation.",
                 "Heavy or recurrent bleeding needs prompt care."]),
        "black": ("Dark from smoke/pollution or oxidized blood.",
                  ["Avoid irritants; use saline.",
                   "If persistent without a clear cause, seek care."]),
        "uncertain": ("Hard to read; lighting/background can mislead.",
                      ["Retake photo in neutral light on white background.",
                       "Track symptoms over time, not just color."]),
    }

    # Map yellow/amber to yellow guidance key (for any future UI use)
    if key in ("yellow/amber",):
        key = "yellow"

    summary, actions = guidance.get(key, guidance["uncertain"])

    return {
        "rgb": (int(r), int(g), int(b)),
        "hsv01": (h, s, v),
        "hue_deg": hue,
        "category": category,
        "explanation": explanation,
        "key": key,
        "summary": summary,
        "actions": actions,
        "rules": rules,
        "picked_rule": picked_rule,
    }

# ---------- Navigation ----------
def nav_to(route: str) -> None:
    st.session_state["route"] = route
    st.rerun()

# ---------- Pages ----------
def page_home() -> None:
    st.markdown(
        """
<div class="hero">
  <h1>Klinik</h1>
  <p>Explore simple, educational wellness modules. Start with the <b>Mucus Color</b> demo to see a rough color estimate and a transparent rule trace.</p>
  <div style="margin-top:1rem;">
    <span class="badge">Educational only — Not a medical device</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("Get Started", use_container_width=True):
        nav_to("modules")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.subheader("What to expect")
    st.markdown(
        "- No diagnosis. General information only.\n"
        "- Privacy. Images are processed in this session.\n"
        "- Transparency. You will see the rule trace used to decide color."
    )

def page_modules() -> None:
    st.title("Modules")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.markdown("#### Mucus Color")
    st.write("Learn how color estimation works, then try the detector.")
    if st.button("Open Mucus Module ->", use_container_width=True):
        nav_to("mucus_info")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    if st.button("Back to Home", use_container_width=True):
        nav_to("home")

def page_mucus_info() -> None:
    st.title("Mucus Color — Overview")
    st.caption("Read this first, then run the detector.")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)

    st.subheader("How the detector works")
    st.write(
        "We compute HSV color (hue, saturation, value) from a center crop and compare it to simple thresholds. "
        "For best results, use neutral lighting and a plain white background."
    )
    st.markdown(
        "**Tips**\n"
        "- Use a white tissue or background.\n"
        "- Prefer natural/neutral light; avoid colored bulbs/filters.\n"
        "- Keep the camera steady and in focus."
    )
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Proceed to Detector", use_container_width=True):
            nav_to("mucus_detect")
    with c2:
        if st.button("Back to Modules", use_container_width=True):
            nav_to("modules")

def page_mucus_detect() -> None:
    st.title("Mucus Color Detector (Demo)")
    st.caption("Educational only • Not a medical device • If you feel unwell, talk to a clinician.")
    st.write("Upload a photo on white tissue in natural/neutral light. Avoid filters and colored backgrounds.")

    uploaded = st.file_uploader(
        "Upload a photo (jpg, jpeg, png, webp)", type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded image", use_container_width=True)

        with st.expander("Advanced (optional)"):
            robust = st.checkbox(
                "Robust averaging (median of a center crop)",
                value=True,
                help="Helps reduce bias from highlights/shadows.",
            )

        if st.button("Analyze", use_container_width=True):
            if robust:
                rgb = average_rgb(img)
            else:
                arr = np.asarray(
                    ImageOps.exif_transpose(img).convert("RGB").resize((64, 64)),
                    dtype=np.float32,
                )
                rgb = tuple(int(x) for x in arr.mean(axis=(0, 1)))

            result = classify_color_with_trace(rgb)
            st.session_state["mucus_last"] = result

    # ----- Trace-only output (no estimate/hex/metrics/summary) -----
    if st.session_state.get("mucus_last"):
        res = st.session_state["mucus_last"]
        st.markdown("<hr class='soft' />", unsafe_allow_html=True)
        st.markdown("**Decision breakdown (rule trace):**")
        for r in res["rules"]:
            status = "Passed" if r["passed"] else "—"
            st.markdown(f"- {status} — {r['name']}: {r['detail']}")
        st.caption(f"Picked rule: {res.get('picked_rule', 'none')}")

    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back to Module Info", use_container_width=True):
            nav_to("mucus_info")
    with c2:
        if st.button("Back to Home", use_container_width=True):
            nav_to("home")

# ---------- Router ----------
route = st.session_state["route"]
if route == "home":
    page_home()
elif route == "modules":
    page_modules()
elif route == "mucus_info":
    page_mucus_info()
elif route == "mucus_detect":
    page_mucus_detect()
else:
    page_home()

# ---------- Footer ----------
st.markdown("<hr class='soft' />", unsafe_allow_html=True)
st.markdown(
    "Disclaimer: Klinik is an educational demo, not a medical device. "
    "It cannot diagnose or exclude any condition. If you feel unwell, seek professional care."
)
