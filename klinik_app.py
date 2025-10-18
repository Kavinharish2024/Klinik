# klinik_app.py  (ASCII-safe, updated theme, humanized copy, post-detect explainer)
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
PRIMARY = "#293241"     # used for headings and text emphasis
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

def hex_chip(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    hx = f"#{r:02x}{g:02x}{b:02x}".upper()
    return f"""
<div style="display:flex;gap:.6rem;align-items:center;">
  <div style="width:22px;height:22px;border-radius:.4rem;border:1px solid #00000022;background:{hx};"></div>
  <code class="codepill">{hx}</code>
  <span style="color:{TEXT_DARK};font-size:.9rem;">(RGB {r}, {g}, {b})</span>
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

# ---------- Human-friendly explainers to show AFTER detection ----------
EXPLAINERS: Dict[str, str] = {
    "clear": """
### Clear Mucus
**Color snapshot.** Transparent and watery; the most common, usually healthy.

**The science.** Mucus is mostly water plus mucins and salts. Clear means that water-to-mucin balance is good. Tiny hairlike cilia move it along to trap dust and microbes and keep things moist.

**Possible causes**
- Normal hydration
- Mild allergies or light dust/pollen
- Early cold stage (before mucus thickens)
- Temperature or humidity changes

**What to do**
- Drink water
- Use a humidifier if air is dry
- Avoid smoke, strong perfumes
- No real concern unless it changes color, thickens, or new symptoms show up
""",
    "white": """
### White or Gray Mucus
**Color snapshot.** Cloudy, milky, and thicker than clear.

**The science.** As mucus loses water, mucins concentrate and look cloudy. Slower airflow with congestion traps more cells and proteins, adding to the pale look.

**Possible causes**
- Mild nasal/sinus congestion
- Early cold or minor irritation
- Dehydration or dry air
- Temporary airway inflammation

**What to do**
- Hydrate
- Saline spray or humidifier
- Warm showers/steam can help
- Usually clears on its own; check in if it lingers or worsens
""",
    "yellow": """
### Yellow Mucus
**Color snapshot.** Thicker with a pale to deeper yellow tint.

**The science.** When your immune system engages, white blood cells (like neutrophils) release enzymes and iron-containing proteins that tint the mucus yellow. It signals activity, not automatically infection.

**Possible causes**
- Mild viral cold
- Allergic flare with inflammation
- Healing stage after a recent bug
- Daytime thickening from low hydration

**What to do**
- Rest and fluids
- Steam or humid air to thin it
- Avoid unnecessary antibiotics (color alone is not proof)
- If fever or symptoms last >~10 days, get medical advice
""",
    "green": """
### Green Mucus
**Color snapshot.** Dense, vividly green; sometimes olive-toned.

**The science.** More neutrophils = more myeloperoxidase (a green iron enzyme), which deepens the color. Often linked with infection, but color mainly reflects inflammation level.

**Possible causes**
- Ongoing sinus inflammation or infection
- Allergic irritation lasting several days
- Pollution, smoke, or dusty air

**What to do**
- Hydrate, rest
- Gentle saline rinses
- Avoid polluted air or smoking
- If it sticks around >~10 days or comes with fever, seek care
""",
    "brown": """
### Brown (or Rust) Mucus
**Color snapshot.** Reddish-brown; may look dry or grainy.

**The science.** Usually oxidized hemoglobin (old or dried blood) or inhaled particles. As blood ages, iron darkens to brown.

**Possible causes**
- Minor nose irritation/dryness with tiny capillary breaks
- Smoke or dust exposure
- Frequent blowing or nose picking
- Post-nasal drip mixing with old blood

**What to do**
- Avoid irritants and dry air
- Use saline to keep passages moist
- If frequent or heavy, check with a clinician
""",
    "red": """
### Red or Pink Mucus
**Color snapshot.** Fresh blood streaks or pinkish tones.

**The science.** Delicate nasal capillaries can rupture; small amounts of fresh blood mix with mucus before clotting.

**Possible causes**
- Dry air or dehydration
- Forceful blowing or frequent wiping
- Irritation from allergens or infection

**What to do**
- Go easy when clearing the nose
- Humidifier + saline spray
- If bleeding is frequent, heavy, or with other symptoms, seek medical care
""",
    "black": """
### Black or Very Dark Mucus
**Color snapshot.** Dark gray to black; can look thick or speckled.

**The science.** Often from particles (smoke, soot, dust) sticking to mucus. Less commonly, oxidized blood deep in the sinuses.

**Possible causes**
- Pollution or smoke exposure
- Dusty environments (construction, fireplaces)
- Chronic nasal dryness or irritation
- Rarely, certain fungal infections

**What to do**
- Get to clean, humid air
- Sterile saline rinses
- Avoid smoking and polluted spaces
- If persistent without a clear cause, see a clinician
""",
    "uncertain": """
### Uncertain or Mixed Color
**Color snapshot.** Hard to classify; mixed tones or odd lighting.

**The science.** Lighting, camera filters, and tissue color can skew hue. Mixed colors can happen as your immune response shifts or hydration changes.

**Possible causes**
- Lighting or camera white balance
- Transition phase of an illness or recovery
- Varying hydration; mild irritation

**What to do**
- Retake the photo in natural light on plain white
- Focus more on symptoms and trend over time than a single color
"""
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
  <p>Explore simple, educational wellness modules. Start with the <b>Mucus Color</b> demo to see a rough color estimate and plain-language guidance.</p>
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
        "- Transparency. We show how the color guess was chosen."
    )

def page_modules() -> None:
    st.title("Modules")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.markdown("#### Mucus Color")
    st.write("Learn how color estimation works, what the results mean, then try the detector.")
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
        "We look at HSV color (hue, saturation, value) from a center crop and compare it to simple thresholds. "
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

        # ----- Post-detection explainer (full section) -----
        key = res.get("key", "uncertain")
        explainer_md = EXPLAINERS.get(key, EXPLAINERS["uncertain"])
        st.markdown("<hr class='soft' />", unsafe_allow_html=True)
        st.markdown(explainer_md)

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
