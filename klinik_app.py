# klinik_app.py  (ASCII-safe, updated theme, tuned classifier, explainer-only output)
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
        "Get More Info": "https://www.cdc.gov/",
    },
)

# ---------- Color Palette (requested) ----------
# Background:  #98c1d9
# Buttons:     #e0fbfc
# Text:        #293241
PRIMARY = "#293241"     # headings/text
ACCENT = "#e0fbfc"      # buttons
BACKGROUND = "#98c1d9"  # page background
TEXT_DARK = "#293241"   # all text

# ---------- Styles ----------
CSS = f"""
<style>
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
hr.soft {{ border:none; height:1px; background:#e6edf3; margin:1.1rem 0; }}
footer {{ visibility:hidden; }}

.hero {{ text-align:center; padding:2.2rem 1rem 1.2rem 1rem; }}
.hero h1 {{ margin:0; font-size:2.2rem; }}
.hero p {{ margin:.5rem 0 0 0; color:{TEXT_DARK}; }}

.card {{ border:1px solid #e6edf3; border-radius:1rem; padding:1rem; background:white; color:{TEXT_DARK}; }}

/* Buttons: readable text at all times */
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

# ---------- Classifier (tuned: adds Yellow/Amber band, better ordering) ----------
def _hue_in_range(h_deg: float, lo: float, hi: float, eps: float = 0.8) -> bool:
    """Inclusive range with a small tolerance; supports wrap-around if lo > hi."""
    if lo <= hi:
        return (lo - eps) <= h_deg <= (hi + eps)
    return h_deg >= (lo - eps) or h_deg <= (hi + eps)

def classify_color(rgb: Tuple[int, int, int]) -> str:
    """
    Return a normalized key in: clear, white, yellow, green, brown, red, black, uncertain.
    (Internally we allow 'yellow/amber' but normalize to 'yellow' for display.)
    """
    r, g, b = rgb
    h, s, v = rgb_to_hsv01(r, g, b)
    hue = h * 360.0

    # Order: darkness -> low-sat neutrals -> brown (requires darkness) -> chromatic bands
    # Thresholds (empirically friendly for phone photos):
    # black: v < 0.16
    # clear: s < 0.07 and v > 0.80
    # white: s < 0.18 and v > 0.60
    # brown: v < 0.45 and s >= 0.25 and 15 < hue < 50
    # yellow/amber: 25..75 with s >= 0.16 and v >= 0.50
    # green: 75..170 with s >= 0.20
    # red: hue <= 18 or hue >= 342 with s >= 0.20 and v > 0.25

    if v < 0.16:
        return "black"
    if s < 0.07 and v > 0.80:
        return "clear"
    if s < 0.18 and v > 0.60:
        return "white"
    if v < 0.45 and s >= 0.25 and 15 < hue < 50:
        return "brown"
    if _hue_in_range(hue, 25, 75) and s >= 0.16 and v >= 0.50:
        return "yellow"  # normalize yellow/amber -> yellow
    if _hue_in_range(hue, 75, 170) and s >= 0.20:
        return "green"
    if (_hue_in_range(hue, 342, 360) or _hue_in_range(hue, 0, 18)) and s >= 0.20 and v > 0.25:
        return "red"

    return "uncertain"

# ---------- Explainers (render exactly one) ----------
EXPLAINERS: Dict[str, str] = {
    "clear": """
### Clear Mucus

**Color Description**  
The image provided most likely shows a clear mucus. Clear mucus is transparent and watery. It is the most common and typically the healthiest type of mucus.

**The Science**  
Mucus is made of water, mucins, and salts. Clear mucus means your mucin-to-water ratio is balanced, allowing it to trap dust and microbes while keeping your nasal passages moist. Cilia — tiny hairlike structures — move this mucus and help clean and protect the respiratory tract.

**Possible Causes**  
- When you are well-hydrated  
- Mild allergies or exposure to dust/pollen  
- Early stage of a cold, before immune cells thicken it  
- Temperature changes or increased humidity

**What to Do**  
- Maintain hydration with lots of fluids  
- Use a humidifier if air is dry  
- Avoid smoke, perfumes, or strong odors  
- No concern unless it changes color, thickens, or is accompanied by symptoms
""",
    "white": """
### White or Gray Mucus

**Color Description**  
The image provided most likely shows a white or gray mucus. It looks cloudy or milky and feels thicker than clear mucus.

**The Science**  
As mucus becomes dehydrated, water content drops and mucins become more concentrated, giving it a cloudy appearance. White mucus can also reflect mild congestion, when airflow slows and mucus moves less efficiently, trapping more dead cells and proteins.

**Possible Causes**  
- Mild nasal or sinus congestion  
- Early cold or minor irritation of nasal tissues  
- Dehydration or exposure to dry air  
- Temporary airway inflammation

**What to Do**  
- Drink plenty of water  
- Use a saline spray or humidifier  
- Rest and breathe warm, moist air (e.g., shower steam)  
- Usually resolves naturally unless symptoms persist or worsen
""",
    "yellow": """
### Yellow Mucus

**Color Description**  
The image provided most likely shows a yellow mucus. Yellow mucus is thicker with a pale-to-deeper yellow tint.

**The Science**  
When the immune system activates, white blood cells (neutrophils) move into mucus. Their enzymes and iron-containing proteins tint it yellow. This shows immune activity — not necessarily infection.

**Possible Causes**  
- Mild viral infection (like a cold)  
- Allergic reaction with inflammation  
- Healing stage of a recent infection  
- Normal daytime thickening from low hydration

**What to Do**  
- Rest and stay hydrated  
- Use steam or humid air to thin mucus  
- Avoid unnecessary antibiotics (color alone does not prove infection)  
- If fever or persistent congestion occurs, seek medical evaluation
""",
    "green": """
### Green Mucus

**Color Description**  
The image provided most likely shows a green mucus. It is dense and brightly colored, dark green or olive.

**The Science**  
A stronger immune response introduces more neutrophils. Their enzyme myeloperoxidase (green-tinted) deepens the color. Often linked to infection, but the color mainly reflects inflammation level.

**Possible Causes**  
- Ongoing sinus inflammation or infection  
- Allergic irritation lasting several days  
- Environmental exposure (polluted air, dust, smoke)

**What to Do**  
- Hydrate and rest  
- Try nasal rinses or gentle saline sprays  
- Avoid polluted environments or smoking  
- If green mucus extends beyond ~10 days, seek medical care
""",
    "brown": """
### Brown Mucus

**Color Description**  
The image provided most likely shows a brown mucus. Brown or rust-colored mucus has a reddish-brown tint and may appear dry or grainy.

**The Science**  
The color usually comes from oxidized hemoglobin — old or dried blood — or from inhaled particles. As small capillaries in nasal tissues break or as blood mixes with mucus and oxidizes, iron in hemoglobin darkens to brown.

**Possible Causes**  
- Dried or old blood from nose irritation or dryness  
- Smoke or dust inhalation  
- Frequent nose blowing or minor trauma  
- Post-nasal drip mixing with old blood

**What to Do**  
- Avoid irritants and dry air  
- Use saline sprays to keep nasal passages moist  
- If brown mucus is frequent or heavy, consult a clinician to rule out chronic irritation
""",
    "red": """
### Red or Pink Mucus

**Color Description**  
Reddish or pink mucus contains visible streaks or spots of fresh blood.

**The Science**  
This occurs when tiny blood vessels (capillaries) in the nasal passages rupture. The blood mixes with mucus before clotting, resulting in the reddish tint. It is usually benign if minimal, since nasal membranes are delicate and vascular.

**Possible Causes**  
- Dry air or dehydration  
- Forceful nose blowing or frequent wiping  
- Irritation from allergens or infection

**What to Do**  
- Gently clear the nose (avoid aggressive blowing)  
- Keep air moist with a humidifier  
- Apply gentle saline spray  
- If bleeding is frequent, heavy, or accompanied by other symptoms, seek medical attention
""",
    "black": """
### Black or Very Dark Mucus

**Color Description**  
Black or gray-black mucus looks dark and often thick, sometimes speckled.

**The Science**  
This appearance usually results from inhaled particles — smoke, soot, dust — sticking to mucus. Less commonly, dark mucus can occur if old blood oxidizes deep in the sinuses. The darkness comes from carbon or iron-based pigments trapped in mucins.

**Possible Causes**  
- Pollution or smoke exposure  
- Dusty environments (construction, fireplaces)  
- Chronic nasal dryness or irritation  
- Rarely, fungal infections

**What to Do**  
- Move to clean, humid air  
- Rinse nasal passages with sterile saline  
- Avoid smoking or polluted air  
- If persistent without a clear environmental cause, consult a healthcare professional
""",
    "uncertain": """
### Uncertain or Mixed Color

**Color Description**  
The image provided is hard to classify. Sometimes mucus shows mixed tones or unclear color.

**The Science**  
Lighting, camera filters, and tissue color can alter the perceived hue. Mixtures also happen when mucus is transitioning between immune stages or hydration levels (e.g., yellow when thick, white once it dries).

**Possible Causes**  
- Lighting issues or camera tint  
- Mixed immune response or healing phase  
- Varying hydration or mild irritation

**What to Do**  
- Retake the photo in natural light with a white background to get a clearer result  
- Focus on symptoms, not color alone  
- Track how it changes over time rather than one moment
""",
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
  <p>Try the <b>Mucus Color</b> Detector. We will show a single, plain-language explainer for the detected color — nothing else.</p>
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
        "- No diagnosis — just general, safe info.\n"
        "- Your image stays in this session.\n"
        "- Output is exactly one explainer block."
    )

def page_modules() -> None:
    st.title("Modules")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.markdown("#### Mucus Color")
    st.write("Quick read on how it works, then run the detector.")
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
        "We sample the center of the image, convert to HSV (hue, saturation, value), and check simple thresholds. "
        "Use neutral lighting and a plain white background for the cleanest result."
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
    st.title("Mucus Color Detector")
    st.caption("Educational only • Not a medical device • If you feel unwell, talk to a clinician.")
    st.write("Upload a photo on white tissue in neutral light. Avoid filters and colored backgrounds.")

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

            key = classify_color(rgb)
            # Store only the final markdown to display (one block)
            st.session_state["mucus_last"] = EXPLAINERS.get(key, EXPLAINERS["uncertain"])

    # ----- Explainer-only output -----
    if st.session_state.get("mucus_last"):
        st.markdown("<hr class='soft' />", unsafe_allow_html=True)
        st.markdown(st.session_state["mucus_last"])

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
    "Disclaimer: Klinik is an educational tool, not a medical device. "
    "It cannot diagnose or exclude any condition. If you feel unwell, seek professional care."
)
