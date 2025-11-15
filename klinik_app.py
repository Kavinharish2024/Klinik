# klinik_app.py
import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import colorsys
from typing import Tuple, Dict
import pandas as pd
import altair as alt
import os

# ---------- App Setup ----------
st.set_page_config(
    page_title="Klinik",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": "Klinik helps users understand mucus color and hydration patterns.",
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

def nav_to(route: str):
    st.session_state["route"] = route
    st.rerun()

# ---------- Utilities ----------
def average_rgb(img: Image.Image) -> Tuple[int, int, int]:
    img = ImageOps.exif_transpose(img).convert("RGB")
    small = img.resize((96, 96))
    arr = np.asarray(small, dtype=np.uint8)
    center = arr[24:72, 24:72, :]
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

# ---------- Explain Text ----------
EXPLAINERS = {
    "clear":"### Clear Mucus\nTransparent and watery. Stay hydrated.",
    "white":"### White Mucus\nThicker, can indicate minor congestion.",
    "yellow":"### Yellow Mucus\nImmune response; mild cold/allergy.",
    "green":"### Green Mucus\nStrong immune response; sinus pressure.",
    "brown":"### Brown Mucus\nDried blood/dust exposure.",
    "red":"### Red Mucus\nTiny blood vessels; dry air.",
    "black":"### Black Mucus\nSmoke/dust particles.",
    "uncertain":"### Uncertain\nLighting or mixed colors, try retaking."
}

# ---------- Home ----------
def page_home():
    st.markdown("<h1 style='text-align:center'>Klinik</h1>", unsafe_allow_html=True)
    st.markdown("Educational tool to check mucus color and hydration patterns.")
    if st.button("Start Checkup", use_container_width=True):
        nav_to("checkups")

# ---------- Checkups ----------
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

# ---------- Mucus Detect ----------
def page_mucus_detect():
    st.header("Mucus Color Detection")
    uploaded = st.file_uploader("Upload mucus image (white background, natural light)", type=["jpg","jpeg","png","webp"])
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded image", use_container_width=True)
        if st.button("Analyze"):
            # Segmentation placeholder (later replace with ML model)
            segmented = img # replace with segmentation output later
            rgb = average_rgb(segmented)
            color = classify_color(rgb)
            confidence = np.random.uniform(0.6, 0.95) # placeholder
            st.markdown(f"**Detected Color:** {color} ({confidence:.2f} confidence)")
            st.markdown(EXPLAINERS.get(color, EXPLAINERS["uncertain"]))
            # Save history
            st.session_state["history"].append({"color":color, "confidence":confidence})
    if st.button("Back", use_container_width=True):
        nav_to("checkups")

# ---------- Symptom Survey ----------
def page_symptoms():
    st.header("Symptom Survey")
    congestion = st.slider("Congestion (0-10)", 0,10)
    throat_dry = st.slider("Throat dryness (0-10)",0,10)
    fever = st.checkbox("Fever")
    smoke = st.checkbox("Recent smoke/dust exposure")
    if st.button("Submit"):
        st.success("Survey submitted! Correlating with mucus color next version.")
    if st.button("Back", use_container_width=True):
        nav_to("checkups")

# ---------- History ----------
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
if route == "home": page_home()
elif route == "checkups": page_checkups()
elif route == "mucus_detect": page_mucus_detect()
elif route == "symptoms": page_symptoms()
elif route == "history": page_history()
else: page_home()
