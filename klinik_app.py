# klinik_app.py
import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import matplotlib.colors as mcolors
from typing import Tuple, Dict

# ---------- App Setup ----------
st.set_page_config(
    page_title="Klinik",
    page_icon="🧪",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": (
            "Klinik is an educational tool that helps users reflect on mucus color "
            "and symptom patterns. It does NOT provide medical diagnosis or treatment."
        ),
    },
)

# ---------- Color Palette / Styles ----------
PRIMARY = "#293241"
ACCENT = "#e0fbfc"
BACKGROUND = "#98c1d9"
TEXT_DARK = "#293241"

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
    if "last_report" not in st.session_state:
        st.session_state["last_report"] = None
    if "last_color" not in st.session_state:
        st.session_state["last_color"] = None

init_state()

# ---------- FULL EXPLAINERS (your exact breakdown) ----------
EXPLAINERS_FULL: Dict[str, str] = {
    "clear": """
### Clear Mucus
**Color Description**  
The image provided most likely shows a clear mucus. Clear mucus is transparent and watery. It’s the most common and typically the healthiest type of mucus.

**The Science**  
Mucus is made of water, mucins, and salts. Clear mucus means your mucin-to-water ratio is balanced, allowing it to trap dust and microbes while keeping your nasal passages moist.
Cilia, a hairlike structure in your cells, move this mucus and helps clean + protect the respiratory tract.

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
A stronger immune response introduces even more neutrophils. Their enzymes, especially myeloperoxidase (a green-tinted iron enzyme), give mucus this color. While often linked to infection, green mucus mainly shows inflammation, and not the invasion of bacteria.

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
This occurs when tiny blood vessels (capillaries) in the nasal passages rupture.
The blood mixes with mucus before clotting, resulting in the reddish tint.
It’s usually benign if minimal, since nasal membranes are delicate and vascular.

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
This appearance usually results from inhaled particles, such as smoke, soot, or dust, sticking to mucus. Less commonly, dark mucus can occur if old blood oxidizes deep in the sinuses.
The darkness comes from carbon or iron-based pigments trapped in mucins.

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
Lighting, camera filters, and tissue color can alter the perceived hue.
Mixtures also happen when mucus is transitioning between immune stages or hydration levels. For example, one’s mucus may be yellow as it thickens, but white when it dries.

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

# ---------- Color Engine (dominant HSV + prototypes) ----------
def dominant_hsv(pil_image: Image.Image) -> Tuple[float, float, float]:
    """
    Returns dominant HSV of the mucus region as (h_deg, s, v).
    h_deg in [0, 360), s,v in [0,1].
    """
    img = ImageOps.exif_transpose(pil_image).convert("RGB").resize((256, 256))
    arr = np.asarray(img, dtype=np.float32) / 255.0  # (H,W,3)

    hsv = mcolors.rgb_to_hsv(arr)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    # Ignore background: very bright & low saturation = likely tissue
    mask = (s > 0.10) & (v < 0.98)
    if not np.any(mask):
        mask = np.ones_like(s, dtype=bool)

    h_sel = h[mask]
    s_sel = s[mask]
    v_sel = v[mask]

    h_med = float(np.median(h_sel) * 360.0)
    s_med = float(np.median(s_sel))
    v_med = float(np.median(v_sel))

    return h_med, s_med, v_med


PROTOTYPES = {
    # hue (deg), sat, val – tweakable
    "clear":  (0.0,   0.02, 0.97),
    "white":  (0.0,   0.10, 0.85),
    "yellow": (50.0,  0.70, 0.80),
    "green":  (110.0, 0.70, 0.60),
    "brown":  (30.0,  0.60, 0.45),
    "red":    (5.0,   0.80, 0.70),
    "black":  (0.0,   0.05, 0.10),
}

def _circular_hue_distance(h1: float, h2: float) -> float:
    diff = abs(h1 - h2)
    diff = min(diff, 360.0 - diff)
    return diff / 180.0  # normalize to ~[0,1]

def classify_mucus_color(h_deg: float, s: float, v: float) -> Tuple[str, float]:
    """
    Returns (color_label, distance_score) by nearest prototype in HSV space.
    Lower distance_score = closer match.
    """
    best_label = None
    best_score = float("inf")

    for label, (ph, ps, pv) in PROTOTYPES.items():
        dh = _circular_hue_distance(h_deg, ph)
        ds = abs(s - ps)
        dv = abs(v - pv)
        score = 2.0 * dh + ds + dv  # hue weighted more

        if score < best_score:
            best_score = score
            best_label = label

    return best_label, best_score

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
  <p>Clear your throat mucus onto a white surface, take a photo, and upload it. Klinik estimates the mucus color and shows a detailed, science-based explanation plus a symptom summary. This is for education only, not diagnosis.</p>
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
    st.write(
        "Find out what the color of your throat mucus may suggest. "
        "Upload an image and answer a few quick questions."
    )
    if st.button("Open Mucus Checkup →", use_container_width=True):
        nav_to("mucus_detect")

    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    if st.button("Back to Home", use_container_width=True):
        nav_to("home")

def build_symptom_summary(answers: Dict[str, str]) -> str:
    lines = []
    lines.append("### Symptom Snapshot (self-reported)\n")
    lines.append(f"- **Duration of symptoms:** {answers.get('duration', 'Not specified')}")
    lines.append(f"- **Fever:** {answers.get('fever', 'Not specified')}")
    lines.append(f"- **Nasal congestion:** {answers.get('congestion', 'Not specified')}")
    lines.append(f"- **Cough:** {answers.get('cough', 'Not specified')}")
    lines.append(f"- **Sore throat:** {answers.get('sore_throat', 'Not specified')}")
    other = answers.get("other", "").strip()
    if other:
        lines.append(f"- **Other symptoms/notes:** {other}")
    lines.append(
        "\n_This information is self-reported and not reviewed by a clinician. "
        "Klinik does not diagnose or rule out any condition._"
    )
    return "\n".join(lines)

def page_mucus_detect() -> None:
    st.title("Mucus Color Checkup")
    st.write(
        "Upload a photo of mucus on a **white background** in **natural or neutral lighting**. "
        "Then answer a few questions so the report can reflect your context."
    )

    uploaded = st.file_uploader(
        "Upload a mucus photo", type=["jpg", "jpeg", "png", "webp"]
    )

    st.markdown("#### Symptom Questions (optional but recommended)")
    col1, col2 = st.columns(2)

    with col1:
        duration = st.selectbox(
            "How long have you had symptoms?",
            [
                "No symptoms",
                "< 1 day",
                "1–3 days",
                "4–7 days",
                "8–14 days",
                "> 14 days",
            ],
        )
        fever = st.selectbox("Fever?", ["No", "Yes", "Not sure"])
        congestion = st.selectbox(
            "Nasal congestion?", ["No", "Mild", "Moderate", "Severe"]
        )

    with col2:
        cough = st.selectbox("Cough?", ["No", "Mild", "Frequent", "Severe"])
        sore_throat = st.selectbox("Sore throat?", ["No", "Mild", "Moderate", "Severe"])
        other = st.text_input("Other symptoms or notes (optional)")

    answers = {
        "duration": duration,
        "fever": fever,
        "congestion": congestion,
        "cough": cough,
        "sore_throat": sore_throat,
        "other": other,
    }

    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded image", use_container_width=True)

        if st.button("Analyze", use_container_width=True):
            # 1. Extract dominant HSV for mucus region
            h_deg, s, v = dominant_hsv(img)

            # 2. Nearest-prototype classification
            base_label, distance = classify_mucus_color(h_deg, s, v)

            # 3. Simple heuristic tweak for display label
            display_label = base_label
            has_strong_symptoms = (
                fever == "Yes"
                or congestion in ["Moderate", "Severe"]
                or cough in ["Frequent", "Severe"]
                or sore_throat in ["Moderate", "Severe"]
            )

            if base_label in ["yellow", "green"] and has_strong_symptoms:
                display_label = f"{base_label} (immune response likely active)"
            elif base_label in ["clear", "white"] and has_strong_symptoms:
                display_label = f"{base_label} (color may lag behind symptoms)"

            # Save to session in case you want to use later
            st.session_state["last_color"] = base_label

            # 4. Result header
            st.markdown("<hr class='soft' />", unsafe_allow_html=True)
            st.markdown("### Analysis Summary")
            st.markdown(
                f"- **Estimated mucus color:** `{display_label}`  \n"
                f"- **Internal match score:** `{distance:.3f}` (lower = closer match)  \n"
                f"- **Dominant HSV (approx):** `{h_deg:.1f}° hue, {s:.2f} sat, {v:.2f} val`"
            )
            st.info(
                "This estimate is based on image color patterns and is meant for education only. "
                "It is not a medical diagnosis and should not replace professional care."
            )

            # 5. Color breakdown (your exact text)
            st.markdown(EXPLAINERS_FULL.get(base_label, EXPLAINERS_FULL["uncertain"]))

            # 6. Symptom snapshot using questionnaire
            st.markdown(build_symptom_summary(answers))

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
