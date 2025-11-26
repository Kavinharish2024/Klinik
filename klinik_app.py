# klinik_app.py

import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import colorsys
from typing import Dict, Any

# basic Streamlit setup
st.set_page_config(
    page_title="Klinik",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": "Klinik helps users understand mucus color and sinus patterns.",
    },
)

# color palette for the UI
PRIMARY = "#293241"
ACCENT = "#e0fbfc"
BACKGROUND = "#98c1d9"
TEXT_DARK = "#293241"

# custom styles injected into the app
CSS = f"""
<style>
.stApp {{
  background-color: {BACKGROUND};
  color: {TEXT_DARK};
  font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}}
h1, h2, h3, h4, h5, h6 {{
  color: {TEXT_DARK};
}}
a {{
  color: {TEXT_DARK};
  text-decoration: underline;
}}
hr.soft {{
  border: none;
  height: 1px;
  background: #e6edf3;
  margin: 1.1rem 0;
}}
footer {{
  visibility: hidden;
}}
.hero {{
  text-align: center;
  padding: 2rem 1rem 1rem 1rem;
}}
.hero h1 {{
  margin: 0;
  font-size: 2.2rem;
}}
.stButton > button {{
  background: {ACCENT} !important;
  color: {TEXT_DARK} !important;
  border: 1px solid #c5e9ee !important;
  border-radius: 10px !important;
  padding: 0.6rem 1rem !important;
  font-weight: 700 !important;
  box-shadow: 0 1px 2px rgba(16,24,40,0.05) !important;
}}
.stButton > button:hover {{
  filter: brightness(0.96) !important;
}}
.stButton > button:disabled {{
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}}
</style>
"""
st.write(CSS, unsafe_allow_html=True)


# initialize session state for navigation and saved report
def init_state():
    if "route" not in st.session_state:
        st.session_state["route"] = "home"
    if "mucus_report" not in st.session_state:
        st.session_state["mucus_report"] = ""

init_state()


# full explainers for each color category
EXPLAINERS_FULL: Dict[str, str] = {
    "clear": """
### Clear Mucus
Clear mucus is usually thin and watery. This is the most common and generally healthy form.

**Why it looks this way**  
The balance of water and mucins is normal. This helps trap dust and keep the nose hydrated.

**Typical reasons**  
- Hydration  
- Allergies or dust  
- Early stages of a cold  
- Temperature changes  

**What helps**  
Stay hydrated, avoid irritants, use a humidifier if needed.
""",
    "white": """
### White or Gray Mucus
White mucus is thicker and looks cloudy. This often shows mild congestion.

**Why it looks this way**  
Low moisture and slower airflow make mucus thicker and cloudier.

**Typical reasons**  
- Mild congestion  
- Early cold  
- Dehydration  
- Dry air  

**What helps**  
Drink water, use saline spray, rest, and use humid air.
""",
    "yellow": """
### Yellow Mucus
Yellow mucus becomes discolored when immune cells collect in the mucus.

**Why it looks this way**  
White blood cells release enzymes that tint the mucus yellow.

**Typical reasons**  
- Mild viral infection  
- Allergies  
- Normal healing phase  

**What helps**  
Hydrate, rest, steam/humid air. Color alone does not mean bacterial infection.
""",
    "green": """
### Green Mucus
Green mucus is thick and vibrantly colored.

**Why it looks this way**  
A higher concentration of immune enzymes creates a darker green tone.

**Typical reasons**  
- Ongoing inflammation or infection  
- Allergies  
- Irritants in the environment  

**What helps**  
Hydration, nasal rinses, avoiding smoke or pollution.
""",
    "brown": """
### Brown Mucus
Brown mucus usually contains dried or older blood.

**Why it looks this way**  
Oxidized hemoglobin or dust mixes into mucus and darkens it.

**Typical reasons**  
- Dryness  
- Irritation  
- Nose blowing  
- Smoke or dust exposure  

**What helps**  
Avoid irritants, keep passages moist, use saline.
""",
    "red": """
### Red or Pink Mucus
Red or pink coloring typically indicates fresh blood in the mucus.

**Why it looks this way**  
Tiny blood vessels in the lining can break easily and mix with mucus.

**Typical reasons**  
- Dry air  
- Strong nose blowing  
- Irritation or inflammation  

**What helps**  
Gentle clearing, hydration, humid air.
""",
    "black": """
### Black or Very Dark Mucus
Dark mucus usually contains soot, smoke, or dust particles.

**Why it looks this way**  
Particles stick to mucus and darken the color.

**Typical reasons**  
- Pollution  
- Smoke exposure  
- Dryness  
- Rare fungal infection  

**What helps**  
Avoid irritants and rinse passages with sterile saline.
""",
    "uncertain": """
### Uncertain or Mixed Color
Sometimes the color is unclear due to lighting, mixtures, or camera issues.

Try retaking the photo in natural lighting on a white surface.
"""
}


# take and center-crop the image for analysis
def preprocess_center_crop(img: Image.Image, size: int = 192) -> np.ndarray:
    img = ImageOps.exif_transpose(img).convert("RGB")
    img = img.resize((size, size))
    return np.asarray(img, dtype=np.uint8)


# convert RGB numpy array to HSV
def rgb_array_to_hsv_array(arr: np.ndarray) -> np.ndarray:
    h, w, _ = arr.shape
    hsv = np.zeros_like(arr, dtype=np.float32)
    for i in range(h):
        for j in range(w):
            r, g, b = arr[i, j] / 255.0
            hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)
            hsv[i, j, 0] = hh
            hsv[i, j, 1] = ss
            hsv[i, j, 2] = vv
    return hsv


# classify an individual HSV pixel into a color label
def classify_pixel(h: float, s: float, v: float) -> str:
    hue_deg = h * 360.0

    if v < 0.16:
        return "black"
    if s < 0.07 and v > 0.80:
        return "clear"
    if s < 0.20 and v > 0.55:
        return "white"
    if v < 0.55 and s >= 0.25 and 10 < hue_deg < 50:
        return "brown"
    if 30 <= hue_deg <= 75 and s >= 0.18 and v >= 0.40:
        return "yellow"
    if 75 < hue_deg <= 170 and s >= 0.20 and v >= 0.25:
        return "green"
    if (0 <= hue_deg <= 20 or 340 <= hue_deg <= 360) and s >= 0.20 and v > 0.25:
        return "red"
    return "uncertain"


# analyze the mucus region and compute distribution + dominant color
def analyze_mucus_image(img: Image.Image) -> Dict[str, Any]:
    arr = preprocess_center_crop(img)
    hsv = rgb_array_to_hsv_array(arr)

    h = hsv[..., 0]
    s = hsv[..., 1]
    v = hsv[..., 2]

    mask = (s > 0.12) & (v > 0.15)
    if not np.any(mask):
        mask = np.ones_like(s, dtype=bool)

    counts = {}
    total = int(mask.sum())

    for hi, si, vi in zip(h[mask], s[mask], v[mask]):
        label = classify_pixel(hi, si, vi)
        counts[label] = counts.get(label, 0) + 1

    fractions = {k: v_ / total for k, v_ in counts.items()}
    if not fractions:
        return {
            "primary": "uncertain",
            "fractions": {},
            "n_pixels": total,
            "median_hue_deg": float(np.median(h[mask]) * 360),
            "median_sat": float(np.median(s[mask])),
            "median_val": float(np.median(v[mask])),
        }

    primary, primary_frac = sorted(fractions.items(), key=lambda kv: kv[1], reverse=True)[0]
    if primary == "uncertain" or primary_frac < 0.55:
        primary = "uncertain"

    return {
        "primary": primary,
        "fractions": fractions,
        "n_pixels": total,
        "median_hue_deg": float(np.median(h[mask]) * 360),
        "median_sat": float(np.median(s[mask])),
        "median_val": float(np.median(v[mask])),
    }


# build the final markdown report
def build_report(analysis: Dict[str, Any], symptoms: Dict[str, Any]) -> str:
    color_key = analysis["primary"]
    explainer = EXPLAINERS_FULL.get(color_key, EXPLAINERS_FULL["uncertain"])

    frac_lines = [
        f"- {k.capitalize()}: {frac * 100:.1f}%"
        for k, frac in sorted(analysis["fractions"].items(), key=lambda kv: kv[1], reverse=True)
    ]
    frac_text = "\n".join(frac_lines) if frac_lines else "No strong color signal detected."

    stats_block = (
        f"**Image Summary**  \n"
        f"- Pixels analyzed: {analysis['n_pixels']}  \n"
        f"- Median hue: {analysis['median_hue_deg']:.1f}°  \n"
        f"- Median saturation: {analysis['median_sat']:.2f}  \n"
        f"- Median brightness: {analysis['median_val']:.2f}  \n\n"
        f"**Color Distribution**  \n{frac_text}\n"
    )

    symptoms_block = (
        f"**Reported Symptoms**  \n"
        f"- Fever: {symptoms.get('fever')}  \n"
        f"- Nasal congestion: {symptoms.get('congestion')}  \n"
        f"- Allergy symptoms: {symptoms.get('allergy')}  \n"
        f"- Recent cold: {symptoms.get('recent_cold')}  \n"
    )

    notes = []
    if color_key in ["yellow", "green"]:
        if symptoms.get("fever") == "Yes" or symptoms.get("congestion") == "Yes":
            notes.append(
                "Yellow or green mucus with fever or congestion often reflects an active immune response."
            )
        else:
            notes.append("Yellow or green mucus without major symptoms can appear during minor viral issues.")
    elif color_key == "clear":
        if symptoms.get("congestion") == "Yes":
            notes.append("Clear mucus with congestion can be early irritation or the start of a cold.")
        else:
            notes.append("Clear mucus without symptoms often reflects normal hydration.")
    elif color_key == "white":
        notes.append("White mucus with congestion suggests mild swelling or dryness.")
    elif color_key == "brown":
        notes.append("Brown mucus often contains older blood or irritation-related residue.")
    elif color_key == "red":
        notes.append("Red or pink streaks usually come from small broken vessels.")
    elif color_key == "black":
        notes.append("Dark mucus often comes from smoke or dust exposure.")
    else:
        notes.append("Color could not be clearly identified.")

    interpretation = "**Interpretation**  \n" + "\n".join(f"- {n}" for n in notes)

    return (
        f"**Detected Color:** {color_key.capitalize()}\n\n"
        + stats_block
        + "\n"
        + symptoms_block
        + "\n"
        + interpretation
        + "\n\n"
        + explainer
    )


# basic routing
def nav_to(route: str):
    st.session_state["route"] = route
    st.rerun()


def page_home():
    st.markdown(
        """
<div class="hero">
  <h1>Klinik</h1>
  <p>Upload a mucus sample photo on a white background to see what the color might indicate.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("Get Started", use_container_width=True):
        nav_to("checkups")


def page_checkups():
    st.title("Checkups")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)

    st.subheader("Mucus Analysis")
    st.write("Upload a photo to check mucus color.")
    if st.button("Open Mucus Checkup", use_container_width=True):
        nav_to("mucus_info")

    if st.button("Back to Home", use_container_width=True):
        nav_to("home")


def page_mucus_info():
    st.title("How It Works")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.write(
        "Klinik examines hundreds of pixels from the central region of your photo. "
        "It converts the image to HSV color space to estimate color tones and ignore most of the white tissue background. "
        "Then it determines the dominant mucus color and combines this with a short symptom questionnaire."
    )
    st.write("For accuracy, use a white background and natural light.")

    if st.button("Proceed to Checkup", use_container_width=True):
        nav_to("mucus_detect")
    if st.button("Back to Checkups", use_container_width=True):
        nav_to("checkups")


def page_mucus_detect():
    st.title("Mucus Color Checkup")
    st.write("Upload a photo with mucus on a white background.")

    uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp"])

    st.subheader("Symptom Check (optional)")
    symptoms = {
        "fever": st.radio("Fever?", ["No", "Yes"]),
        "congestion": st.radio("Nasal congestion?", ["No", "Yes"]),
        "allergy": st.radio("Allergy symptoms?", ["No", "Yes"]),
        "recent_cold": st.radio("Cold in the last few days?", ["No", "Yes"]),
    }

    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded image", use_container_width=True)

        if st.button("Analyze", use_container_width=True):
            analysis = analyze_mucus_image(img)
            st.session_state["mucus_report"] = build_report(analysis, symptoms)

    if st.session_state.get("mucus_report"):
        st.markdown(st.session_state["mucus_report"], unsafe_allow_html=True)

    if st.button("Back to Checkups", use_container_width=True):
        nav_to("checkups")


# router
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
