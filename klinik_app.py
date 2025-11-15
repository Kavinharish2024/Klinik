# klinik_app.py (ISEF-style glow-up)
import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import colorsys
from typing import Tuple, Dict

# ---------- App Setup ----------
st.set_page_config(
    page_title="Klinik",
    page_icon="🧪",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": "Klinik helps users understand mucus color and hydration patterns.",
    },
)

# ---------- Color Palette ----------
PRIMARY = "#293241"
ACCENT = "#e0fbfc"
BACKGROUND = "#98c1d9"
TEXT_DARK = "#293241"

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
.stButton > button {{
  background: {ACCENT} !important;
  color: {TEXT_DARK} !important;
  border: 1px solid #c5e9ee !important;
  border-radius: 10px !important;
  padding: 0.6rem 1rem !important;
  font-weight: 700 !important;
  box-shadow: 0 1px 2px rgba(16,24,40,0.05) !important;
  cursor: pointer !important;
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
def init_state():
    if "route" not in st.session_state:
        st.session_state["route"] = "home"
    if "mucus_last" not in st.session_state:
        st.session_state["mucus_last"] = {}

init_state()

# ---------- Utils ----------
def rgb_to_hsv01(r: int, g: int, b: int) -> Tuple[float, float, float]:
    return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

def average_rgb(img: Image.Image) -> Tuple[int, int, int]:
    img = ImageOps.exif_transpose(img).convert("RGB")
    small = img.resize((96, 96))
    arr = np.asarray(small, dtype=np.uint8)
    center = arr[24:72, 24:72, :]
    med = np.median(center, axis=(0, 1))
    return tuple(int(x) for x in med)

def _hue_in_range(h_deg: float, lo: float, hi: float, eps: float = 0.8) -> bool:
    if lo <= hi:
        return (lo - eps) <= h_deg <= (hi + eps)
    return h_deg >= (lo - eps) or h_deg <= (hi + eps)

def classify_color(rgb: Tuple[int,int,int]) -> str:
    r,g,b = rgb
    h,s,v = rgb_to_hsv01(r,g,b)
    hue = h * 360.0
    if v < 0.16:
        return "black"
    if s < 0.07 and v > 0.80:
        return "clear"
    if s < 0.18 and v > 0.60:
        return "white"
    if v < 0.45 and s >= 0.25 and 15 < hue < 50:
        return "brown"
    if _hue_in_range(hue,25,75) and s >= 0.16 and v >= 0.50:
        return "yellow"
    if _hue_in_range(hue,75,170) and s >= 0.20:
        return "green"
    if (_hue_in_range(hue,342,360) or _hue_in_range(hue,0,18)) and s >= 0.20 and v > 0.25:
        return "red"
    return "uncertain"

# ---------- Full Detailed Explanations ----------
EXPLAINERS: Dict[str,str] = {
    "clear": """### Clear Mucus
**Color Description**  
The image provided most likely shows a clear mucus. Clear mucus is transparent and watery. It’s the most common and typically the healthiest type of mucus.

**The Science**  
Mucus is made of water, mucins, and salts. Clear mucus means your mucin-to-water ratio is balanced, allowing it to trap dust and microbes while keeping your nasal passages moist. Cilia, a hairlike structure in your cells, move this mucus and helps clean + protect the respiratory tract.

**Possible Causes**  
- Well-hydrated  
- Mild allergies or exposure to dust/pollen  
- Early stage of a cold  
- Temperature or humidity changes

**What to Do**  
- Maintain hydration  
- Use a humidifier if air is dry  
- Avoid smoke, perfumes, or strong odors  
- No concern unless color changes or thickens
""",
    "white": """### White or Gray Mucus
**Color Description**  
The image provided most likely shows a white or gray mucus. White or gray mucus looks cloudy or milky and feels thicker than clear mucus.

**The Science**  
As mucus becomes dehydrated, water content drops and mucins concentrate, giving it a cloudy appearance. White mucus can also indicate mild congestion, when airflow slows and mucus moves less efficiently.

**Possible Causes**  
- Mild nasal or sinus congestion  
- Early cold or minor irritation  
- Dehydration or dry air  
- Temporary airway inflammation

**What to Do**  
- Drink plenty of water  
- Use saline spray or humidifier  
- Rest and breathe warm, moist air
""",
    "yellow": """### Yellow Mucus
**Color Description**  
The image provided most likely shows a yellow mucus. Yellow mucus is thick and tinted from pale yellow color.

**The Science**  
Immune system sends neutrophils to fight irritants/pathogens. Their enzymes and iron proteins give mucus its yellow hue.

**Possible Causes**  
- Mild viral infection (cold)  
- Allergic reaction with inflammation  
- Healing stage of a recent infection  
- Daytime thickening from low hydration

**What to Do**  
- Rest and hydrate  
- Use steam or humid air  
- Avoid unnecessary antibiotics  
- Seek evaluation if fever or persistent congestion
""",
    "green": """### Green Mucus
**Color Description**  
The image provided most likely shows a green mucus. Dense, dark green or olive.

**The Science**  
Stronger immune response introduces more neutrophils. Enzymes (myeloperoxidase) give green color. Often shows inflammation, not necessarily infection.

**Possible Causes**  
- Ongoing sinus inflammation or infection  
- Allergic irritation lasting several days  
- Environmental exposure (pollution, dust, smoke)

**What to Do**  
- Hydrate and rest  
- Use nasal rinses or saline sprays  
- Avoid pollution/smoking  
- Seek care if >10 days
""",
    "brown": """### Brown Mucus
**Color Description**  
The image shows brown or rust-colored mucus, dry or grainy.

**The Science**  
Oxidized hemoglobin (old/dried blood) or inhaled particles darken mucus. Iron in hemoglobin turns brown after oxidation.

**Possible Causes**  
- Dried or old blood from irritation  
- Smoke or dust inhalation  
- Frequent nose blowing  
- Post-nasal drip mixing with old blood

**What to Do**  
- Avoid irritants/dry air  
- Use saline sprays  
- Consult clinician if frequent/heavy
""",
    "red": """### Red or Pink Mucus
**Color Description**  
Reddish/pink mucus with streaks/spots of blood.

**The Science**  
Tiny capillaries rupture, mixing blood with mucus before clotting.

**Possible Causes**  
- Dry air or dehydration  
- Forceful nose blowing  
- Irritation from allergens/infection

**What to Do**  
- Gently clear nose  
- Keep air humid  
- Saline spray  
- Seek help if bleeding is frequent/heavy
""",
    "black": """### Black or Very Dark Mucus
**Color Description**  
Black or gray-black mucus, thick, sometimes speckled.

**The Science**  
From inhaled particles (smoke, dust) or old blood oxidizing. Carbon/iron pigments trapped in mucins.

**Possible Causes**  
- Pollution/smoke exposure  
- Dusty environments  
- Chronic dryness  
- Rare fungal infections

**What to Do**  
- Move to clean, humid air  
- Saline rinses  
- Avoid smoke/polluted air  
- Consult professional if persistent
""",
    "uncertain": """### Uncertain or Mixed Color
**Color Description**  
Image cannot be classified; mixed tones or unclear color.

**The Science**  
Lighting, camera filters, tissue tint can alter perception. Mucus may be in transition between stages.

**Possible Causes**  
- Lighting/camera tint  
- Mixed immune response or healing  
- Varying hydration or irritation

**What to Do**  
- Retake photo in natural light with white background  
- Focus on symptoms  
- Track changes over time
"""
}

# ---------- Navigation ----------
def nav_to(route: str):
    st.session_state["route"] = route
    st.rerun()

# ---------- Pages ----------
def page_home():
    st.markdown(
        """
<div class="hero">
  <h1>Klinik</h1>
  <p>Try the Klinik Mucus Color Detector. Clear your throat mucus onto a white surface. Upload an image to find out its type and get detailed scientific info!</p>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("Get Started", use_container_width=True):
        nav_to("checkups")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)

def page_checkups():
    st.title("Checkups")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.subheader("Mucus Color")
    st.write("Find out what the color of your throat mucus means by uploading an image.")
    if st.button("Open Mucus Checkup ->", use_container_width=True):
        nav_to("mucus_detect")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    if st.button("Back to Home", use_container_width=True):
        nav_to("home")

def page_mucus_detect():
    st.title("Mucus Color Checkup")
    st.write("Upload a photo of mucus on a white background under natural light.")
    uploaded = st.file_uploader("Upload a photo", type=["jpg","jpeg","png","webp"])
    
    # Inline questionnaire
    st.subheader("Optional Questionnaire (improves accuracy)")
    fever = st.radio("Do you have a fever?", ["No","Yes"])
    congestion = st.radio("Do you have nasal congestion?", ["No","Yes"])
    allergy = st.radio("Any allergy symptoms?", ["No","Yes"])
    recent_cold = st.radio("Had a cold in the last few days?", ["No","Yes"])
    
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded image", use_container_width=True)
        if st.button("Analyze", use_container_width=True):
            rgb = average_rgb(img)
            key = classify_color(rgb)
            
            # Adjust with questionnaire heuristics
            if key in ["yellow","green"] and fever=="Yes":
                key += " (immune active)"
            if key=="clear" and congestion=="Yes":
                key += " (may indicate early irritation)"
            
            st.session_state["mucus_last"] = EXPLAINERS.get(key.split()[0], EXPLAINERS["uncertain"])
    
    if st.session_state.get("mucus_last"):
        st.markdown("<hr class='soft' />", unsafe_allow_html=True)
        st.markdown(st.session_state["mucus_last"])
    
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    if st.button("Back to Checkups", use_container_width=True):
        nav_to("checkups")

# ---------- Router ----------
route = st.session_state["route"]
if route == "home":
    page_home()
elif route == "checkups":
    page_checkups()
elif route == "mucus_detect":
    page_mucus_detect()
else:
    page_home()
