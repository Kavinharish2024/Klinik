# klinik_app.py (clean version, "modules" -> "check-ups")
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
        "About": "Klinik helps users understand mucus color and hydration patterns.",
    },
)

# ---------- Color Palette ----------
PRIMARY = "#293241"     # headings/text
ACCENT = "#e0fbfc"      # buttons
BACKGROUND = "#98c1d9"  # background
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
def init_state() -> None:
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

# ---------- Classifier ----------
def _hue_in_range(h_deg: float, lo: float, hi: float, eps: float = 0.8) -> bool:
    if lo <= hi:
        return (lo - eps) <= h_deg <= (hi + eps)
    return h_deg >= (lo - eps) or h_deg <= (hi + eps)

def classify_color(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    h, s, v = rgb_to_hsv01(r, g, b)
    hue = h * 360.0

    if v < 0.16:
        return "black"
    if s < 0.07 and v > 0.80:
        return "clear"
    if s < 0.18 and v > 0.60:
        return "white"
    if v < 0.45 and s >= 0.25 and 15 < hue < 50:
        return "brown"
    if _hue_in_range(hue, 25, 75) and s >= 0.16 and v >= 0.50:
        return "yellow"
    if _hue_in_range(hue, 75, 170) and s >= 0.20:
        return "green"
    if (_hue_in_range(hue, 342, 360) or _hue_in_range(hue, 0, 18)) and s >= 0.20 and v > 0.25:
        return "red"
    return "uncertain"

# ---------- Explainers ----------
EXPLAINERS: Dict[str, str] = {
    "clear": """
### Clear Mucus
Clear mucus is transparent and watery — the most common and typically the healthiest kind.

**Why it happens**  
Your mucus is mostly water with just enough mucins and salts to stay fluid. This helps trap dust and microbes while keeping your airways moist.

**You might see it when:**  
- You’re well hydrated  
- You have mild allergies or dust exposure  
- Early in a cold before symptoms set in  
- The weather or humidity changes

**Try this:**  
Drink plenty of water, use a humidifier if needed, and avoid smoke or strong scents.
""",
    "white": """
### White or Gray Mucus
White or gray mucus looks cloudy or milky and often feels thicker.

**Why it happens**  
As mucus loses water, mucins become more concentrated. This often signals mild congestion or slower airflow.

**You might see it when:**  
- You have a minor cold or sinus irritation  
- You’re dehydrated or the air is dry  
- Your nasal passages are inflamed

**Try this:**  
Stay hydrated, rest, and breathe warm, moist air to clear things up.
""",
    "yellow": """
### Yellow Mucus
Yellow mucus has a pale to deeper tint and is thicker.

**Why it happens**  
Your immune system sends white blood cells to fight irritants. Their enzymes and proteins give mucus its yellow hue.

**You might see it when:**  
- Fighting a mild cold or allergy  
- Recovering from an infection  
- Slightly dehydrated

**Try this:**  
Rest, drink fluids, and use steam or a saline rinse to stay clear.
""",
    "green": """
### Green Mucus
Green mucus is dense and darker, sometimes olive-toned.

**Why it happens**  
A strong immune response fills mucus with enzymes that deepen its color — it doesn’t always mean infection.

**You might see it when:**  
- You have sinus pressure or a lingering cold  
- You’ve been around smoke or pollution  

**Try this:**  
Rinse your nose with saline, rest, and hydrate. If it lasts long or worsens, check in with your doctor.
""",
    "brown": """
### Brown Mucus
Brown or rust-colored mucus may look dry or grainy.

**Why it happens**  
It usually contains dried blood or small particles like dust or smoke. As blood oxidizes, it turns darker.

**You might see it when:**  
- Your nose is dry or irritated  
- You’ve been exposed to smoke or dust  

**Try this:**  
Avoid irritants and keep your airways moist with saline spray.
""",
    "red": """
### Red or Pink Mucus
Red or pink streaks appear when tiny blood vessels break inside your nose.

**Why it happens**  
The blood mixes with mucus before clotting, creating a pink or red hue.

**You might see it when:**  
- You blow or wipe your nose often  
- The air is dry or cold  

**Try this:**  
Be gentle when cleaning your nose and keep the air humid.
""",
    "black": """
### Black or Very Dark Mucus
Black or very dark mucus can look speckled or smoky.

**Why it happens**  
Tiny particles like soot, smoke, or dust stick to mucus. Sometimes old blood deep in the sinuses can darken it too.

**You might see it when:**  
- You’ve been around smoke, dust, or pollution  
- Your sinuses are very dry  

**Try this:**  
Rinse your nose, breathe clean air, and avoid pollutants.
""",
    "uncertain": """
### Uncertain or Mixed Color
Sometimes mucus shows multiple tones or unclear colors.

**Why it happens**  
Lighting, filters, or tissue tint can alter the photo, and colors shift naturally as mucus thickens or dries.

**Try this:**  
Retake your photo in natural light with a white background and track any changes over time.
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
  <p>Try the Klinik Mucus Color Detector. Clear your throat mucus onto a white surface like a sink or tissue. Then, take an image, upload it to the detector, and find out what the color of your mucus actually means!</p>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("Get Started", use_container_width=True):
        nav_to("checkups")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)

def page_checkups() -> None:
    st.title("Checkups")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.subheader("Mucus Color")
    st.write("Find out what the color of your throat mucus means by uploading an image.")
    if st.button("Open Mucus Checkup ->", use_container_width=True):
        nav_to("mucus_info")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    if st.button("Back to Home", use_container_width=True):
        nav_to("home")

def page_mucus_info() -> None:
    st.title("How It Works")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.write(
        "Klinik analyzes the average color of your mucus using three parameters: hue, saturation, and brightness. Based of this, we estimate its tone and give a break down of what it may mean. "
        "Use good lighting and a white background for accuracy."
    )
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    if st.button("Proceed to Checkup", use_container_width=True):
        nav_to("mucus_detect")
    if st.button("Back to Checkups", use_container_width=True):
        nav_to("checkups")

def page_mucus_detect() -> None:
    st.title("Mucus Color Checkup")
    st.write("Upload a photo of mucus on a white background under natural light.")
    uploaded = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png", "webp"])
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded image", use_container_width=True)
        if st.button("Analyze", use_container_width=True):
            rgb = average_rgb(img)
            key = classify_color(rgb)
            st.session_state["mucus_last"] = EXPLAINERS.get(key, EXPLAINERS["uncertain"])
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
elif route == "mucus_info":
    page_mucus_info()
elif route == "mucus_detect":
    page_mucus_detect()
else:
    page_home()
