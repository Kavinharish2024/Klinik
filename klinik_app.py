# klinik_app.py

import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import colorsys
from typing import Tuple, Dict, Any

# ---------- App Setup ----------
st.set_page_config(
    page_title="Klinik",
    page_icon="🧪",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": "Klinik helps users understand mucus color and sinus patterns.",
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
    if "mucus_report" not in st.session_state:
        st.session_state["mucus_report"] = ""

init_state()

# ---------- Full Detailed Explainers ----------
EXPLAINERS_FULL: Dict[str, str] = {
    "clear": """
### Clear Mucus
**Color Description**  
The image provided most likely shows a clear mucus. Clear mucus is transparent and watery. It’s the most common and typically the healthiest type of mucus.

**The Science**  
Mucus is made of water, mucins, and salts. Clear mucus means your mucin-to-water ratio is balanced, allowing it to trap dust and microbes while keeping your nasal passages moist.  
Cilia, a hairlike structure in your cells, move this mucus and help clean + protect the respiratory tract.

**Possible Causes**  
- When you’re well-hydrated  
- During mild allergies or exposure to dust/pollen  
- In the early stage of a cold, before immune cells thicken it  
- From temperature changes or increased humidity  

**What to Do**  
- Maintain hydration with lots of fluids  
- Use a humidifier if air is dry  
- Avoid smoke, perfumes, or strong odors  
- No concern unless it changes color, thickens, or is accompanied by symptoms
""",
    "white": """
### White or Gray Mucus
**Color Description**  
The image provided most likely shows a white or gray mucus. White or gray mucus looks cloudy or milky and feels thicker than clear mucus.

**The Science**  
As mucus becomes dehydrated, water content drops and mucins become more concentrated, giving it a cloudy appearance. White mucus can also indicate mild congestion, when airflow slows and mucus moves less efficiently, trapping more dead cells and proteins.

**Possible Causes**  
- Mild nasal or sinus congestion  
- Early cold or minor irritation of nasal tissues  
- Dehydration or exposure to dry air  
- Temporary airway inflammation  

**What to Do**  
- Drink plenty of water  
- Use a saline spray or humidifier  
- Rest and breathe warm, moist air (like a shower)  
- Usually resolves naturally unless symptoms persist or worsen
""",
    "yellow": """
### Yellow Mucus
**Color Description**  
The image provided most likely shows a yellow mucus. Yellow mucus is thick and tinted from pale yellow color.

**The Science**  
When the immune system activates, white blood cells (neutrophils) move into mucus to fight irritants or pathogens. These cells release enzymes and iron-containing proteins that give the mucus a yellow hue. The color change shows an active immune response, not necessarily infection.

**Possible Causes**  
- Mild viral infection (like a cold)  
- Allergic reaction with inflammation  
- Healing stage of a recent infection  
- Normal daytime thickening from low hydration  

**What to Do**  
- Rest and stay hydrated  
- Use steam or humid air to thin mucus  
- Avoid unnecessary antibiotics (color alone does not mean you have an infection)  
- If fever or persistent congestion occurs, seek medical evaluation
""",
    "green": """
### Green Mucus
**Color Description**  
The image provided most likely shows a green mucus. Green mucus is dense and brightly colored, dark green or almost olive.

**The Science**  
A stronger immune response introduces even more neutrophils. Their enzymes, especially myeloperoxidase (a green-tinted iron enzyme), give mucus this color. While often linked to infection, green mucus mainly shows inflammation, not necessarily bacterial invasion.

**Possible Causes**  
- Ongoing sinus inflammation or infection  
- Allergic irritation lasting several days  
- Environmental exposure (polluted air, dust, smoke)  

**What to Do**  
- Hydrate and get rest  
- Use nasal rinses or gentle saline sprays  
- Avoid polluted environments or smoking  
- If green mucus extends beyond 10 days, seek medical care
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
This occurs when tiny blood vessels (capillaries) in the nasal passages rupture. The blood mixes with mucus before clotting, resulting in the reddish tint. It’s usually benign if minimal, since nasal membranes are delicate and vascular.

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
This appearance usually results from inhaled particles, such as smoke, soot, or dust, sticking to mucus. Less commonly, dark mucus can occur if old blood oxidizes deep in the sinuses. The darkness comes from carbon or iron-based pigments trapped in mucins.

**Possible Causes**  
- Pollution or smoke exposure  
- Dusty environments (construction, fireplaces)  
- Chronic nasal dryness or irritation  
- Rarely, fungal infections  

**What to Do**  
- Move to clean, humid air  
- Rinse nasal passages with sterile saline  
- Avoid smoking or polluted air  
- If persistent without clear environmental cause, consult a healthcare professional
""",
    "uncertain": """
### Uncertain or Mixed Color
**Color Description**  
The image provided is unable to be classified as a certain mucus color. Sometimes mucus shows mixed tones or unclear color.

**The Science**  
Lighting, camera filters, and tissue color can alter the perceived hue. Mixtures also happen when mucus is transitioning between immune stages or hydration levels. For example, one’s mucus may be yellow as it thickens, but white when it dries.

**Possible Causes**  
- Lighting issues or camera tint  
- Mixed immune response or healing phase  
- Varying hydration or mild irritation  

**What to Do**  
- Retake the photo in natural light with a white background and see if you are able to get a definitive result  
- Focus on symptoms, not color alone  
- Track how it changes over time rather than at one moment
"""
}

# ---------- Image / Color Utils ----------

def preprocess_center_crop(img: Image.Image, size: int = 192) -> np.ndarray:
    """
    Resize to a square and take a central crop as numpy array (H,W,3) uint8.
    """
    img = ImageOps.exif_transpose(img).convert("RGB")
    img = img.resize((size, size))
    arr = np.asarray(img, dtype=np.uint8)
    # central crop (keep same size here, but function kept for clarity)
    return arr


def rgb_array_to_hsv_array(arr: np.ndarray) -> np.ndarray:
    """
    Convert RGB uint8 array (H,W,3) in [0,255] to HSV float array (H,W,3) in [0,1].
    Uses colorsys for each pixel (no matplotlib).
    """
    h, w, _ = arr.shape
    hsv = np.zeros_like(arr, dtype=np.float32)
    for i in range(h):
        for j in range(w):
            r, g, b = arr[i, j] / 255.0
            hh, ss, vv = colorsys.rgb_to_hsv(float(r), float(g), float(b))
            hsv[i, j, 0] = hh
            hsv[i, j, 1] = ss
            hsv[i, j, 2] = vv
    return hsv


def classify_pixel(h: float, s: float, v: float) -> str:
    """
    Classify a single pixel's HSV (0–1 each) into a mucus color label.
    """
    hue_deg = h * 360.0

    # Black / very dark
    if v < 0.16:
        return "black"

    # Very low saturation: clear / white / uncertain
    if s < 0.07 and v > 0.80:
        return "clear"
    if s < 0.20 and v > 0.55:
        return "white"

    # Brown: dark-ish, warm hue
    if v < 0.55 and s >= 0.25 and 10.0 < hue_deg < 50.0:
        return "brown"

    # Yellow: 30–75 deg, decent saturation & brightness
    if 30.0 <= hue_deg <= 75.0 and s >= 0.18 and v >= 0.40:
        return "yellow"

    # Green: 75–170 deg, moderate saturation
    if 75.0 < hue_deg <= 170.0 and s >= 0.20 and v >= 0.25:
        return "green"

    # Red: 0–20 or 340–360, decent saturation/brightness
    if (0.0 <= hue_deg <= 20.0 or 340.0 <= hue_deg <= 360.0) and s >= 0.20 and v > 0.25:
        return "red"

    return "uncertain"


def analyze_mucus_image(img: Image.Image) -> Dict[str, Any]:
    """
    Do a more robust analysis:
    - Convert central crop to HSV
    - Ignore low-saturation/very-bright background (tissue)
    - Classify each remaining pixel
    - Return dominant color + distribution + basic stats
    """
    arr = preprocess_center_crop(img)           # (H,W,3) uint8
    hsv = rgb_array_to_hsv_array(arr)          # (H,W,3) float in [0,1]

    h = hsv[..., 0]
    s = hsv[..., 1]
    v = hsv[..., 2]

    # Mask: likely mucus pixels (not pure white tissue)
    mask = (s > 0.12) & (v > 0.15)  # tuneable

    if not np.any(mask):
        # Fallback: use all pixels if mask catches nothing
        mask = np.ones_like(s, dtype=bool)

    labels = {}
    total = int(mask.sum())

    for hi, si, vi in zip(h[mask], s[mask], v[mask]):
        lab = classify_pixel(hi, si, vi)
        labels[lab] = labels.get(lab, 0) + 1

    # Normalize to fractions
    fractions = {k: v_ / total for k, v_ in labels.items()}
    if not fractions:
        return {
            "primary": "uncertain",
            "fractions": {},
            "n_pixels": total,
            "median_hue_deg": float(np.median(h[mask]) * 360.0),
            "median_sat": float(np.median(s[mask])),
            "median_val": float(np.median(v[mask])),
        }

    # Pick dominant non-uncertain color
    sorted_colors = sorted(fractions.items(), key=lambda kv: kv[1], reverse=True)
    primary, primary_frac = sorted_colors[0]

    # If top color is uncertain or not dominant enough, mark as uncertain
    if primary == "uncertain" or primary_frac < 0.55:
        primary = "uncertain"

    median_h = float(np.median(h[mask]) * 360.0)
    median_s = float(np.median(s[mask]))
    median_v = float(np.median(v[mask]))

    return {
        "primary": primary,
        "fractions": fractions,
        "n_pixels": total,
        "median_hue_deg": median_h,
        "median_sat": median_s,
        "median_val": median_v,
    }


def build_report(
    analysis: Dict[str, Any],
    symptoms: Dict[str, Any],
) -> str:
    """
    Combine:
    - dominant color from image
    - distribution stats
    - symptom questionnaire
    into one markdown report with your detailed breakdown.
    """
    color_key = analysis["primary"]
    base_explainer = EXPLAINERS_FULL.get(color_key, EXPLAINERS_FULL["uncertain"])

    frac_text_lines = []
    for k, frac in sorted(analysis["fractions"].items(), key=lambda kv: kv[1], reverse=True):
        frac_text_lines.append(f"- **{k.capitalize()}**: {frac*100:.1f}% of detected mucus pixels")

    frac_block = "\n".join(frac_text_lines) if frac_text_lines else "Not enough colored pixels detected."

    stats_block = (
        f"**Image Analysis Summary**  \n"
        f"- Pixels analyzed (approx.): **{analysis['n_pixels']}**  \n"
        f"- Median hue: **{analysis['median_hue_deg']:.1f}°**  \n"
        f"- Median saturation: **{analysis['median_sat']:.2f}**  \n"
        f"- Median brightness (value): **{analysis['median_val']:.2f}**  \n\n"
        f"**Estimated Color Distribution**  \n{frac_block}\n"
    )

    # Symptoms section
    fever = symptoms.get("fever", "No")
    congestion = symptoms.get("congestion", "No")
    allergy = symptoms.get("allergy", "No")
    recent_cold = symptoms.get("recent_cold", "No")

    symptoms_block = (
        f"**Your Reported Symptoms**  \n"
        f"- Fever: **{fever}**  \n"
        f"- Nasal congestion: **{congestion}**  \n"
        f"- Allergy symptoms: **{allergy}**  \n"
        f"- Recent cold (last few days): **{recent_cold}**  \n"
    )

    # Simple interpretation tying symptoms + color together
    extra_notes = []

    if color_key in ["yellow", "green"]:
        if fever == "Yes" or congestion == "Yes":
            extra_notes.append(
                "- The combination of **yellow/green mucus** plus **fever or congestion** suggests an active immune response in your upper airways."
            )
        else:
            extra_notes.append(
                "- Yellow/green mucus without strong symptoms can appear during **mild viral infections, allergies, or healing**."
            )
    elif color_key == "clear":
        if congestion == "Yes":
            extra_notes.append(
                "- Clear mucus with congestion may reflect **early-stage irritation, allergies, or the beginning of a cold**."
            )
        else:
            extra_notes.append(
                "- Clear mucus with few symptoms is usually consistent with **healthy, well-hydrated airways**."
            )
    elif color_key == "white":
        extra_notes.append(
            "- White mucus and congestion often point to **mild swelling** or **slower mucus flow**, especially in dry environments."
        )
    elif color_key == "brown":
        extra_notes.append(
            "- Brown mucus plus any dryness/irritation could indicate **old blood** or **irritant exposure** like smoke or dust."
        )
    elif color_key == "red":
        extra_notes.append(
            "- Red or pink streaks usually reflect **tiny broken blood vessels**, especially if you blow or wipe your nose often."
        )
    elif color_key == "black":
        extra_notes.append(
            "- Very dark mucus is often linked to **smoke, dust, or pollution**. If you’re not exposed to these, consider talking to a clinician."
        )
    else:
        extra_notes.append(
            "- The system could not confidently pick a single color. Lighting, camera tint, or a mix of mucus types may be involved."
        )

    extra_block = "**How the App Interprets This Combination**  \n" + "\n".join(extra_notes) + "\n"

    return (
        f"**Detected Dominant Color (image-based):** **{color_key.capitalize()}**  \n\n"
        + stats_block
        + "\n"
        + symptoms_block
        + "\n"
        + extra_block
        + "\n---\n"
        + base_explainer
    )

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
  <p>Try the Klinik Mucus Color Detector. Clear your throat mucus onto a white surface like a tissue or sink, take a picture, and upload it to see what the color may mean for your respiratory health.</p>
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
    if st.button("Open Mucus Checkup →", use_container_width=True):
        nav_to("mucus_info")

    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    if st.button("Back to Home", use_container_width=True):
        nav_to("home")


def page_mucus_info() -> None:
    st.title("How It Works")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.write(
        "Klinik analyzes the color of your mucus using hundreds of pixels from the central region of your photo. "
        "It converts each pixel from RGB to HSV (hue, saturation, value) to estimate the underlying color tone, while ignoring most of the white tissue background. "
        "Then, it estimates what fraction of the mucus area matches each color category (clear, white, yellow, green, brown, red, black) and picks the dominant one. "
        "Finally, it combines this with a short symptom questionnaire to create a detailed, science-based explanation."
    )
    st.write(
        "For best results, use a **white background**, avoid heavy filters, and take the photo in **natural light**."
    )
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)

    if st.button("Proceed to Checkup", use_container_width=True):
        nav_to("mucus_detect")
    if st.button("Back to Checkups", use_container_width=True):
        nav_to("checkups")


def page_mucus_detect() -> None:
    st.title("Mucus Color Checkup")
    st.write("Upload a photo of mucus on a **white background** under **natural light** for the most accurate analysis.")
    uploaded = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png", "webp"])

    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.subheader("Quick Symptom Check (optional but recommended)")

    symptoms: Dict[str, Any] = {}
    symptoms["fever"] = st.radio("Do you currently have a fever?", ["No", "Yes"])
    symptoms["congestion"] = st.radio("Do you feel nasal congestion?", ["No", "Yes"])
    symptoms["allergy"] = st.radio("Do you have allergy symptoms (itchy eyes, sneezing, etc.)?", ["No", "Yes"])
    symptoms["recent_cold"] = st.radio("Have you had a cold in the last few days?", ["No", "Yes"])

    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded image", use_container_width=True)

        if st.button("Analyze", use_container_width=True):
            analysis = analyze_mucus_image(img)
            report = build_report(analysis, symptoms)
            st.session_state["mucus_report"] = report

    if st.session_state.get("mucus_report"):
        st.markdown("<hr class='soft' />", unsafe_allow_html=True)
        st.markdown(st.session_state["mucus_report"])

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
