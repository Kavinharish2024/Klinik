# klinik_app.py  (ASCII-safe + Option B + fixed buttons)
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

# ---------- Color Palette: Natural Wellness (Option B) ----------
PRIMARY = "#2C7A7B"     # muted teal (buttons, headers)
ACCENT = "#68D391"      # soft green (badges, highlights)
BACKGROUND = "#F7FAFC"  # warm off-white background
TEXT_DARK = "#1A202C"   # slate gray

# ---------- Styles ----------
CSS = f"""
<style>
/* App background + text color */
.stApp {{
  background-color: {BACKGROUND};
  color: {TEXT_DARK};
  font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}}
h1, h2, h3, h4, h5, h6 {{ color: {PRIMARY}; }}
a {{ color: {PRIMARY}; }}

.badge {{
  display:inline-block; padding:.25rem .6rem; border-radius:9999px;
  background:{ACCENT}33; color:{PRIMARY}; font-weight:600; font-size:.8rem;
}}
.codepill {{
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  background:#00000010; padding:.15rem .45rem; border-radius:.4rem;
}}
hr.soft {{ border:none; height:1px; background:#CBD5E0; margin:1.1rem 0; }}
footer {{ visibility:hidden; }}

.hero {{ text-align:center; padding:2.2rem 1rem 1.2rem 1rem; }}
.hero h1 {{ margin:0; font-size:2.2rem; }}
.hero p {{ margin:.5rem 0 0 0; color:{TEXT_DARK}; }}

.card {{ border:1px solid #E2E8F0; border-radius:1rem; padding:1rem; background:white; }}

/* Force button style (works regardless of Streamlit theme) */
.stButton > button {{
  background: {PRIMARY} !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 0.6rem 1rem !important;
  font-weight: 600 !important;
  box-shadow: 0 1px 2px rgba(16,24,40,0.05) !important;
  cursor: pointer !important;
  opacity: 1 !important;
}}
.stButton > button:hover {{ filter: brightness(0.95) !important; }}
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

def hex_chip(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    hx = f"#{r:02x}{g:02x}{b:02x}".upper()
    return f"""
<div style="display:flex;gap:.6rem;align-items:center;">
  <div style="width:22px;height:22px;border-radius:.4rem;border:1px solid #00000022;background:{hx};"></div>
  <code class="codepill">{hx}</code>
  <span style="color:#4A5568;font-size:.9rem;">(RGB {r}, {g}, {b})</span>
</div>
"""

def format_float(x: float, nd: int = 3) -> str:
    return f"{x:.{nd}f}"

# ---------- Color Classifier ----------
def classify_color_with_trace(rgb: Tuple[int, int, int]) -> Dict[str, Any]:
    r, g, b = rgb
    h, s, v = rgb_to_hsv01(r, g, b)
    hue = h * 360.0

    rules = []
    def add_rule(name: str, cond: bool, detail: str) -> None:
        rules.append({"name": name, "passed": bool(cond), "detail": detail})

    category, explanation, key, picked_rule = "uncertain", "Hard to classify.", "uncertain", "none"

    # 1) Very dark -> black
    add_rule("Very dark (black test)", v < 0.18, f"V={format_float(v)} < 0.18")
    if v < 0.18:
        category, explanation, key, picked_rule = "black/very dark", "Very low brightness.", "black", "Very dark"
    else:
        # 2) Clear (low S, high V)
        add_rule("Clear test", (s < 0.08 and v > 0.75),
                 f"S={format_float(s)} < 0.08 and V={format_float(v)} > 0.75")
        if s < 0.08 and v > 0.75:
            category, explanation, key, picked_rule = "clear", "Low saturation, high brightness.", "clear", "Clear"
        else:
            # 3) White/gray (low S, mid+ V)
            add_rule("White/gray test", (s < 0.15 and v > 0.55),
                     f"S={format_float(s)} < 0.15 and V={format_float(v)} > 0.55")
            if s < 0.15 and v > 0.55:
                category, explanation, key, picked_rule = "white/gray", "Low saturation + mid brightness.", "white", "White/Gray"
            else:
                # 4) Yellow band
                add_rule("Yellow hue band", (35 <= hue <= 75 and s >= 0.18),
                         f"35 <= H={format_float(hue,1)} <= 75 and S={format_float(s)} >= 0.18")
                if 35 <= hue <= 75 and s >= 0.18:
                    category, explanation, key, picked_rule = "yellow", "Hue in yellow range.", "yellow", "Yellow band"
                else:
                    # 5) Green band
                    add_rule("Green hue band", (75 < hue <= 170 and s >= 0.18),
                             f"75 < H={format_float(hue,1)} <= 170 and S={format_float(s)} >= 0.18")
                    if 75 < hue <= 170 and s >= 0.18:
                        category, explanation, key, picked_rule = "green", "Hue in green range.", "green", "Green band"
                    else:
                        # 6) Red/pink band
                        add_rule("Red/pink hue band",
                                 ((hue <= 20 or hue >= 340) and s >= 0.2 and v > 0.2),
                                 f"(H <= 20 or H >= 340) with S={format_float(s)} >= 0.2 and V={format_float(v)} > 0.2")
                        if (hue <= 20 or hue >= 340) and s >= 0.2 and v > 0.2:
                            category, explanation, key, picked_rule = "red/pink", "Hue in red range.", "red", "Red/Pink band"
                        else:
                            # 7) Brown (dark warm)
                            add_rule("Brown warm/dark",
                                     (v < 0.4 and s >= 0.25 and 15 < hue < 50),
                                     f"V={format_float(v)} < 0.4 and S={format_float(s)} >= 0.25 and 15 < H={format_float(hue,1)} < 50")
                            if v < 0.4 and s >= 0.25 and 15 < hue < 50:
                                category, explanation, key, picked_rule = "brown", "Dark warm hue.", "brown", "Brown warm/dark"

    guidance = {
        "clear": ("Often normal hydration/irritation.",
                  ["Usually benign if you feel well.",
                   "Hydrate and monitor.",
                   "Seek care if symptoms persist or worsen."]),
        "white": ("Congestion common.",
                  ["Hydrate, humidify air.",
                   "If more than 10 days or worsening, see a clinician."]),
        "yellow": ("Inflammation, possibly infection.",
                  ["Rest, hydrate.",
                   "See doctor if fever or more than 10 days."]),
        "green": ("Inflammation or infection.",
                  ["Rest, avoid self-medicating.",
                   "Seek care if fever or shortness of breath."]),
        "brown": ("Old blood or irritants.",
                  ["Avoid smoke/dust.",
                   "See doctor if recurring."]),
        "red": ("Fresh blood.",
                ["Small streaks can be irritation.",
                 "Heavy or recurrent bleeding: urgent care."]),
        "black": ("Dark mucus (pollution/smoke/blood).",
                  ["Avoid irritants.",
                  "Persistent? Get medical help."]),
        "uncertain": ("Unclear result.",
                      ["Re-check under good light.",
                       "Focus on symptoms, not just color."]),
    }
    summary, actions = guidance.get(key, guidance["uncertain"])

    return {
        "rgb": rgb,
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
  <p>Explore simple wellness modules. Start with the <b>Mucus Color</b> demo to get a broad color estimate and general guidance.</p>
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
        "- No diagnosis. This provides general, safe information only.\n"
        "- Privacy. Images are processed locally in this session.\n"
        "- Clarity. We show a transparent breakdown of how the color category was chosen."
    )

def page_modules() -> None:
    st.title("Modules")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.markdown("#### Mucus Color")
    st.write("Learn how color estimation works and what the results mean, then try the detector.")
    if st.button("Open Mucus Module ->", use_container_width=True):
        nav_to("mucus_info")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    if st.button("Back to Home", use_container_width=True):
        nav_to("home")

def page_mucus_info() -> None:
    st.title("Mucus Color — Overview")
    st.caption("Read a quick primer, then proceed to the detector.")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)

    st.subheader("How this works")
    st.write(
        "We evaluate throat mucus color using HSV (hue, saturation, value) and compare to simple thresholds. "
        "Use good lighting and a white background for best results."
    )
    st.markdown(
        "**Best way to proceed:**\n"
        "- Use a plain white tissue or background.\n"
        "- Prefer natural/neutral light; avoid colored lights or filters.\n"
        "- Keep the camera in focus."
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
    st.caption("Educational only • Not a medical device • If unwell, seek a clinician.")
    st.write("Upload a photo on white tissue under natural/neutral light. Avoid filters and colored backgrounds.")

    uploaded = st.file_uploader(
        "Upload a photo (jpg, jpeg, png, webp)", type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded image", use_container_width=True)

        with st.expander("Advanced (optional)"):
            robust = st.checkbox(
                "Robust averaging (median pool center crop)",
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

    # Show last result (if any)
    if st.session_state.get("mucus_last"):
        res = st.session_state["mucus_last"]
        rgb = res["rgb"]
        h, s, v = res["hsv01"]
        hue = res["hue_deg"]

        st.markdown("<hr class='soft' />", unsafe_allow_html=True)
        st.subheader(f"Estimated: {res['category']}")
        st.write(f"*{res['explanation']}*")
        st.markdown(hex_chip(rgb), unsafe_allow_html=True)

        st.markdown(
            f"**Color metrics**  \n"
            f"Hue: {format_float(hue, 1)} deg  \n"
            f"Saturation: {format_float(s)}  \n"
            f"Value (brightness): {format_float(v)}"
        )

        st.markdown("**Decision breakdown (rule trace):**")
        for r in res["rules"]:
            status = "Passed" if r["passed"] else "—"
            st.markdown(f"- {status} — {r['name']}: {r['detail']}")
        st.caption(f"Picked rule: {res['picked_rule']}")

        st.markdown("<hr class='soft' />", unsafe_allow_html=True)
        st.markdown(f"**Summary:** {res['summary']}")
        st.markdown("**What you can do (general):**")
        for a in res["actions"]:
            st.markdown(f"- {a}")

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
