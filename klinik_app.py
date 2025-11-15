# klinik_app.py — improved classifier + integrated questionnaire + full breakdown

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
def init_state() -> None:
    if "route" not in st.session_state:
        st.session_state["route"] = "home"
    if "mucus_last" not in st.session_state:
        st.session_state["mucus_last"] = ""
    if "debug_last" not in st.session_state:
        st.session_state["debug_last"] = {}

init_state()

# ---------- Utils ----------
def dominant_color_features(img: Image.Image) -> Tuple[Tuple[int,int,int], Tuple[float,float,float]]:
    """
    1. Center-crop + downscale
    2. Ignore near-white background pixels
    3. Compute median RGB, then HSV
    """
    img = ImageOps.exif_transpose(img).convert("RGB")
    small = img.resize((96, 96))
    arr = np.asarray(small, dtype=np.uint8)

    # center crop
    center = arr[24:72, 24:72, :]  # (48,48,3)
    # flatten pixels
    pixels = center.reshape(-1, 3).astype(np.float32)

    # convert to HSV in [0,1] per pixel
    hsv_pixels = np.zeros_like(pixels, dtype=np.float32)
    for i, (r, g, b) in enumerate(pixels):
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        hsv_pixels[i] = [h, s, v]

    # filter out very bright / low-saturation pixels (likely white background)
    mask = ~((hsv_pixels[:, 1] < 0.08) & (hsv_pixels[:, 2] > 0.88))
    if mask.sum() < 50:
        # too few non-background pixels, just use entire center
        filtered_rgb = pixels
        filtered_hsv = hsv_pixels
    else:
        filtered_rgb = pixels[mask]
        filtered_hsv = hsv_pixels[mask]

    # median RGB & HSV
    med_rgb = np.median(filtered_rgb, axis=0)
    med_hsv = np.median(filtered_hsv, axis=0)

    rgb_tuple = tuple(int(x) for x in med_rgb)
    hsv_tuple = tuple(float(x) for x in med_hsv)  # (h,s,v) in [0,1]

    return rgb_tuple, hsv_tuple

def _hue_in_range(h_deg: float, lo: float, hi: float) -> bool:
    """Handle wrap-around if lo > hi (e.g., red)."""
    if lo <= hi:
        return lo <= h_deg <= hi
    return h_deg >= lo or h_deg <= hi

def classify_color_from_hsv(hsv: Tuple[float,float,float]) -> str:
    """
    Non-overlapping, more realistic HSV rules:

    - black: very low value
    - clear/white: low saturation, high value
    - brown: warm low-value region
    - yellow: 40–65°
    - green: 65–170°
    - red: around 0°/360°
    """
    h, s, v = hsv
    h_deg = h * 360.0

    # 1. extremes first
    if v < 0.12:
        return "black"

    # near-white / clear band
    if s < 0.09 and v > 0.80:
        return "clear"
    if s < 0.20 and v > 0.55:
        return "white"

    # reddish
    if _hue_in_range(h_deg, 345, 360) or _hue_in_range(h_deg, 0, 20):
        if s > 0.25 and v > 0.25:
            return "red"

    # brown: darker warm tones
    if _hue_in_range(h_deg, 10, 45) and v < 0.60 and s > 0.25:
        return "brown"

    # yellow: 40–65, fairly bright
    if _hue_in_range(h_deg, 40, 65) and s > 0.30 and v > 0.40:
        return "yellow"

    # green: 65–170, more saturated
    if _hue_in_range(h_deg, 65, 170) and s > 0.25 and v > 0.25:
        return "green"

    return "uncertain"

# ---------- Full Detailed Explanations (your text) ----------
EXPLAINERS: Dict[str, str] = {
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
The image provided most likely shows a green mucus. Green mucus is dense and brightly colored, dark green or almost an olive.

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
  <p>Try the Klinik Mucus Color Detector. Clear your throat mucus onto a white surface like a sink or tissue. Then, upload an image to see what the color may mean for your health.</p>
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
        "Klinik samples the central region of your mucus image and converts the colors into HSV "
        "(hue, saturation, value). Based on the dominant hue and saturation, it matches your sample "
        "to known mucus color ranges and combines that with your self-reported symptoms for a more "
        "context-aware interpretation. Use good lighting and a white background for accuracy."
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

    st.subheader("Symptom Snapshot (optional but helpful)")
    fever = st.radio("Do you have a fever?", ["No", "Yes"], horizontal=True)
    congestion = st.radio("Do you feel congested?", ["No", "Yes"], horizontal=True)
    allergy = st.radio("Are you having allergy symptoms (itchy eyes, sneezing)?", ["No", "Yes"], horizontal=True)
    recent_cold = st.radio("Have you had a cold in the last few days?", ["No", "Yes"], horizontal=True)

    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded image", use_container_width=True)

        if st.button("Analyze", use_container_width=True):
            rgb, hsv = dominant_color_features(img)
            color_key = classify_color_from_hsv(hsv)

            # dynamic label + symptom-based note (heuristic)
            label = color_key.capitalize()
            notes = []

            if color_key in ["yellow", "green"]:
                if fever == "Yes" or recent_cold == "Yes":
                    notes.append("Your symptoms and mucus color together suggest an active immune response.")
                if congestion == "Yes":
                    notes.append("Congestion plus yellow/green mucus is common in colds or sinus irritation.")
            if color_key == "clear" and (fever == "Yes" or congestion == "Yes"):
                notes.append("Clear mucus with symptoms may reflect an early-stage infection or non-color-based irritation.")
            if color_key == "white" and congestion == "Yes":
                notes.append("White mucus with congestion often reflects mild inflammation and slower mucus flow.")
            if color_key == "brown" and fever == "No" and recent_cold == "No":
                notes.append("Brown mucus without systemic symptoms often reflects dryness or old blood rather than infection.")
            if color_key == "red":
                notes.append("Red or pink streaks fit with minor capillary breakage, especially if you're blowing or wiping your nose often.")
            if color_key == "black" and allergy == "No" and fever == "No":
                notes.append("Dark mucus plus environmental exposure often points to smoke, dust, or pollution.")

            # build final report text
            symptom_block = (
                "**Your Symptom Snapshot (self-reported)**  \n"
                f"- Fever: {fever}  \n"
                f"- Congestion: {congestion}  \n"
                f"- Allergy symptoms: {allergy}  \n"
                f"- Recent cold: {recent_cold}  \n\n"
            )

            how_made = (
                "**How this analysis was made**  \n"
                "- The app sampled the central region of your image and converted pixel colors into HSV (hue, saturation, value).  \n"
                "- It ignored very bright, low-saturation pixels to reduce the impact of the white background.  \n"
                "- The dominant hue, saturation, and brightness were matched to pre-defined mucus color ranges.  \n"
                "- Your symptom answers were then used to add context about whether this color is likely linked to hydration, irritation, or a stronger immune response.  \n"
            )

            extra_notes = ""
            if notes:
                extra_notes = "**Context Notes (based on your symptoms)**  \n- " + "\n- ".join(notes) + "\n\n"

            full_text = (
                f"**Detected Color:** {label}  \n\n"
                + symptom_block
                + EXPLAINERS.get(color_key, EXPLAINERS["uncertain"])
                + "\n\n"
                + extra_notes
                + how_made
            )

            st.session_state["mucus_last"] = full_text
            # store debug info
            h, s, v = hsv
            st.session_state["debug_last"] = {
                "rgb": rgb,
                "hue_deg": h * 360.0,
                "saturation": s,
                "value": v,
            }

    if st.session_state.get("mucus_last"):
        st.markdown("<hr class='soft' />", unsafe_allow_html=True)
        st.markdown(st.session_state["mucus_last"])

        if st.session_state.get("debug_last"):
            with st.expander("View color analysis details (debug)"):
                dbg = st.session_state["debug_last"]
                st.write(f"Median RGB (center region, filtered): {dbg['rgb']}")
                st.write(
                    f"Median HSV: hue ≈ {dbg['hue_deg']:.1f}°, "
                    f"saturation ≈ {dbg['saturation']:.3f}, "
                    f"value ≈ {dbg['value']:.3f}"
                )

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
