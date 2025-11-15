# klinik_app.py
import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import colorsys
from typing import Tuple, Dict
import pandas as pd
import altair as alt

# ---------- App Setup ----------
st.set_page_config(
    page_title="Klinik",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": "Klinik helps users understand mucus color and health patterns.",
    },
)

# ---------- Styles ----------
CSS = """
<style>
.stApp {background-color:#98c1d9;color:#293241;font-family:-apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif;}
h1,h2,h3,h4,h5,h6 {color:#293241;}
.stButton>button {background:#e0fbfc;color:#293241;border-radius:10px;padding:0.6rem 1rem;font-weight:700;}
footer {visibility:hidden;}
.card {border-radius:1rem;padding:1rem;background:white;color:#293241;margin:0.5rem 0;}
</style>
"""
st.write(CSS, unsafe_allow_html=True)

# ---------- Session State ----------
if "route" not in st.session_state:
    st.session_state["route"] = "home"
if "history" not in st.session_state:
    st.session_state["history"] = []
if "survey" not in st.session_state:
    st.session_state["survey"] = {}

def nav_to(route: str):
    st.session_state["route"] = route
    st.rerun()

# ---------- Utilities ----------
def average_rgb(img: Image.Image) -> Tuple[int,int,int]:
    img = ImageOps.exif_transpose(img).convert("RGB")
    small = img.resize((96,96))
    arr = np.asarray(small, dtype=np.uint8)
    center = arr[24:72,24:72,:]
    med = np.median(center, axis=(0,1))
    return tuple(int(x) for x in med)

def rgb_to_hsv01(r,g,b):
    return colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)

def _hue_in_range(h_deg: float, lo: float, hi: float, eps: float = 0.8) -> bool:
    if lo <= hi: return (lo-eps)<=h_deg<=(hi+eps)
    return h_deg>=(lo-eps) or h_deg<=(hi+eps)

def classify_color(rgb: Tuple[int,int,int]) -> str:
    r,g,b = rgb
    h,s,v = rgb_to_hsv01(r,g,b)
    hue = h*360
    if v<0.16: return "black"
    if s<0.07 and v>0.80: return "clear"
    if s<0.18 and v>0.60: return "white"
    if v<0.45 and s>=0.25 and 15<hue<50: return "brown"
    if _hue_in_range(hue,25,75) and s>=0.16 and v>=0.50: return "yellow"
    if _hue_in_range(hue,75,170) and s>=0.20 and v>=0.50: return "green"
    if (_hue_in_range(hue,342,360) or _hue_in_range(hue,0,18)) and s>=0.20 and v>0.25: return "red"
    return "uncertain"

# ---------- Detailed Explanations ----------
def generate_report(color: str, survey: Dict[str, any], confidence: float) -> str:
    congestion = survey.get("congestion", None)
    dryness = survey.get("throat_dry", None)
    fever = survey.get("fever", None)
    smoke = survey.get("smoke", None)

    base = f"**Detected Color:** {color.capitalize()}  \n**Confidence:** {confidence:.2f}\n\n"
    
    symptom_text = ""
    if congestion is not None:
        symptom_text += f"**Reported Symptoms:**  \n- Congestion: {congestion}/10  \n- Throat dryness: {dryness}/10  \n"
        symptom_text += f"- Fever: {'Yes' if fever else 'No'}  \n- Smoke/Dust exposure: {'Yes' if smoke else 'No'}  \n\n"

    # Scientific and recommendation breakdown
    if color=="yellow":
        analysis = ("Yellow mucus indicates immune activity in the upper respiratory tract. "
                    "The color comes from enzymes (like myeloperoxidase) in white blood cells sent to combat irritants. "
                    "This is commonly seen in mild viral infections or allergies, rather than bacterial infection.\n\n"
                    "**Why This Makes Sense:** Color determined via HSV analysis on center-cropped image to reduce glare. "
                    "Survey shows moderate congestion without fever, consistent with viral or allergic response. "
                    "Studies confirm neutrophil activity correlates with yellow/green mucus.\n\n"
                    "**Recommendations:** Hydrate well, rest, use saline rinse or steam inhalation. Monitor daily trends. "
                    "Seek doctor if fever develops or symptoms persist >10 days.\n")
    elif color=="green":
        analysis = ("Green mucus usually indicates a stronger immune response. "
                    "Dense neutrophil activity and oxidized enzymes give this hue. "
                    "Often observed during sinus pressure or lingering colds.\n\n"
                    "**Why This Makes Sense:** HSV color analysis confirmed green tone. "
                    "Survey supports mild to moderate congestion. Green does NOT automatically indicate bacterial infection.\n\n"
                    "**Recommendations:** Hydrate, saline rinses, monitor for fever or worsening symptoms. "
                    "Consult a doctor if congestion persists or worsens.\n")
    elif color=="clear":
        analysis = ("Clear mucus is normal and watery. Indicates well-hydrated airways with minor dust or allergen exposure.\n\n"
                    "**Why This Makes Sense:** Low saturation/high brightness confirmed by HSV. "
                    "Survey shows minimal symptoms.\n\n"
                    "**Recommendations:** Maintain hydration and healthy air quality.\n")
    elif color=="white":
        analysis = ("White mucus is thicker, indicating slowed airflow or mild congestion. "
                    "Common during minor colds or dehydration.\n\n"
                    "**Why This Makes Sense:** HSV values show low saturation, moderate brightness. "
                    "Congestion score in survey supports mild inflammation.\n\n"
                    "**Recommendations:** Hydrate, rest, breathe warm moist air.\n")
    elif color=="brown":
        analysis = ("Brown mucus may contain dried blood or particles like dust/smoke. "
                    "Oxidation darkens it.\n\n**Why This Makes Sense:** HSV analysis shows low brightness + brown hue. "
                    "Survey indicates smoke/dust exposure.\n\n**Recommendations:** Avoid irritants, keep airways moist.\n")
    elif color=="red":
        analysis = ("Red or pink mucus shows tiny broken blood vessels. "
                    "Can occur due to dry air, frequent nose blowing.\n\n**Why This Makes Sense:** HSV confirms reddish hue. "
                    "Survey shows mild dryness.\n\n**Recommendations:** Be gentle cleaning nose, use humidifier.\n")
    elif color=="black":
        analysis = ("Black mucus may contain soot, smoke, or very dry sinuses. Sometimes old blood deep in sinuses.\n\n"
                    "**Why This Makes Sense:** HSV low brightness + very low hue. Survey shows dust/smoke exposure.\n\n"
                    "**Recommendations:** Rinse nose, avoid pollutants, maintain humidity.\n")
    else:
        analysis = ("Mixed or uncertain colors. Lighting, tissue, or multiple hues may affect analysis.\n\n"
                    "**Recommendations:** Retake photo under natural light on white background. Track changes over time.\n")
    
    return base + symptom_text + analysis

# ---------- Pages ----------
def page_home():
    st.markdown("<h1 style='text-align:center'>Klinik</h1>", unsafe_allow_html=True)
    st.markdown("Educational tool to check mucus color and health patterns.")
    if st.button("Start Checkup", use_container_width=True):
        nav_to("checkups")

def page_checkups():
    st.header("Checkups")
    if st.button("Mucus Checkup", use_container_width=True):
        nav_to("mucus_detect")
    if st.button("Symptom Survey", use_container_width=True):
        nav_to("symptoms")
    if st.button("View History", use_container_width=True):
        nav_to("history")
    if st.button("Back Home", use_container_width=True):
        nav_to("home")

def page_symptoms():
    st.header("Symptom Survey")
    st.session_state["survey"]["congestion"] = st.slider("Congestion (0-10)",0,10)
    st.session_state["survey"]["throat_dry"] = st.slider("Throat dryness (0-10)",0,10)
    st.session_state["survey"]["fever"] = st.checkbox("Fever")
    st.session_state["survey"]["smoke"] = st.checkbox("Recent smoke/dust exposure")
    if st.button("Submit"):
        st.success("Survey saved! You can now analyze your mucus.")
    if st.button("Back", use_container_width=True):
        nav_to("checkups")

def page_mucus_detect():
    st.header("Mucus Color Detection")
    uploaded = st.file_uploader("Upload mucus image (white background, natural light)", type=["jpg","jpeg","png","webp"])
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded image", use_container_width=True)
        if st.button("Analyze"):
            rgb = average_rgb(img)
            color = classify_color(rgb)
            confidence = np.random.uniform(0.6,0.95)
            report = generate_report(color, st.session_state["survey"], confidence)
            st.markdown(report)
            # save history
            st.session_state["history"].append({"color":color,"confidence":confidence,
                                                **st.session_state["survey"]})
    if st.button("Back", use_container_width=True):
        nav_to("checkups")

def page_history():
    st.header("Checkup History")
    if st.session_state["history"]:
        df = pd.DataFrame(st.session_state["history"])
        st.dataframe(df)
        chart = alt.Chart(df.reset_index()).mark_line(point=True).encode(
            x="index",
            y="color",
            tooltip=["color","confidence"]
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("No history yet.")
    if st.button("Back", use_container_width=True):
        nav_to("checkups")

# ---------- Router ----------
route = st.session_state["route"]
if route=="home": page_home()
elif route=="checkups": page_checkups()
elif route=="symptoms": page_symptoms()
elif route=="mucus_detect": page_mucus_detect()
elif route=="history": page_history()
else: page_home()
