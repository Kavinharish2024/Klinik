# klinik_app_ml_ready_fullbreakdown.py
import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import colorsys

# ---------- App Setup ----------
st.set_page_config(page_title="Klinik Full Breakdown", layout="centered")
st.markdown("<h1 style='text-align:center'>Klinik ML-style Full Analysis</h1>", unsafe_allow_html=True)
st.write("Upload your mucus image and answer the questions inline for a detailed, science-backed analysis.")

# ---------- FULL EXPLAINERS ----------
EXPLAINERS_FULL = {
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
This occurs when tiny blood vessels (capillaries) in the nasal passages rupture. The blood mixes with mucus before clotting, resulting in the reddish tint. It’s usually benign if minimal.

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
Lighting, camera filters, and tissue color can alter the perceived hue. Mixtures also happen when mucus is transitioning between immune stages or hydration levels.

**Possible Causes**  
- Lighting issues or camera tint  
- Mixed immune response or healing phase  
- Varying hydration or mild irritation  

**What to Do**  
- Retake the photo in natural light with a white background  
- Focus on symptoms, not color alone  
- Track how it changes over time rather than at one moment
"""
}

# ---------- Utils ----------
def average_rgb(img: Image.Image):
    img = ImageOps.exif_transpose(img).convert("RGB")
    small = img.resize((96, 96))
    arr = np.asarray(small, dtype=np.uint8)
    center = arr[24:72, 24:72, :]
    med = np.median(center, axis=(0, 1))
    return tuple(int(x) for x in med)

def rgb_to_hsv01(r, g, b):
    return colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)

def _hue_in_range(h, lo, hi, eps=0.8):
    return (lo-eps <= h <= hi+eps) if lo <= hi else (h >= lo-eps or h <= hi+eps)

def classify_color(rgb):
    r, g, b = rgb
    h, s, v = rgb_to_hsv01(r, g, b)
    h_deg = h*360

    if v < 0.16: return "black"
    if s < 0.07 and v > 0.80: return "clear"
    if s < 0.18 and v > 0.60: return "white"
    if v < 0.45 and s >= 0.25 and 15 < h_deg < 50: return "brown"
    if _hue_in_range(h_deg, 25, 75) and s >= 0.16 and v >= 0.50: return "yellow"
    if _hue_in_range(h_deg, 75, 170) and s >= 0.20: return "green"
    if (_hue_in_range(h_deg, 342, 360) or _hue_in_range(h_deg, 0, 18)) and s >= 0.20 and v > 0.25:
        return "red"
    return "uncertain"

# ---------- Image + Questionnaire ----------
uploaded = st.file_uploader("Upload mucus image (white background, natural light)", type=["jpg","png","jpeg","webp"])
if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Uploaded image", use_container_width=True)

    st.subheader("Inline Questions")
    congestion = st.slider("Congestion (0-10)", 0, 10)
    throat_dry = st.slider("Throat dryness (0-10)", 0, 10)
    fever = st.checkbox("Fever?")
    smoke = st.checkbox("Recent smoke/dust exposure?")

    if st.button("Analyze"):
        rgb = average_rgb(img)
        color_key = classify_color(rgb)

        # Heuristic adjustment
        if color_key in ["yellow","green"] and (congestion>5 or fever):
            adjusted = f"{color_key} (immune response likely)"
        elif color_key == "clear" and (congestion>5 or fever):
            adjusted = f"{color_key} (possible dehydration or early infection)"
        else:
            adjusted = color_key

        st.markdown(f"**Detected Color:** {adjusted}")
        st.markdown(EXPLAINERS_FULL[color_key])
