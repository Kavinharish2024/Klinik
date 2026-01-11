# klinik_app.py
import streamlit as st
from typing import List, Dict

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Klinik",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": "Klinik is a health hub with multiple educational health modules. Not a medical diagnosis tool.",
    },
)

# ---------------- UI palette ----------------
PRIMARY = "#2AA8A1"
BG = "#F4F7F7"
CARD = "#FFFFFF"
TEXT = "#0F3636"
MUTED = "#6B7B7B"
BORDER = "rgba(17, 24, 39, 0.10)"

CSS = f"""
<style>
.stApp {{
  background: {BG};
  color: {TEXT};
  font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}}
header, footer {{ visibility: hidden; }}

.block-container {{
  padding-top: 1.4rem;
  padding-bottom: 2.4rem;
  max-width: 720px;
}}

.klinik-top {{
  display:flex;
  align-items:center;
  justify-content:center;
  gap:10px;
  margin-bottom: 16px;
}}
.klinik-badge {{
  width: 30px; height: 30px;
  border-radius: 10px;
  background: {PRIMARY};
  display:flex; align-items:center; justify-content:center;
  box-shadow: 0 12px 26px rgba(42,168,161,0.20);
}}
.klinik-badge span {{
  color: white; font-weight: 900; font-size: 18px;
}}
.klinik-title {{
  font-weight: 900;
  font-size: 22px;
}}

.card {{
  background: {CARD};
  border: 1px solid {BORDER};
  border-radius: 18px;
  padding: 18px 16px;
  box-shadow: 0 14px 30px rgba(17, 24, 39, 0.06);
  margin: 12px 0;
}}
.card h2 {{
  margin: 0 0 6px 0;
  font-size: 20px;
  font-weight: 900;
}}
.subtle {{
  color: {MUTED};
  font-size: 14px;
  line-height: 1.4;
}}
.hr {{
  height: 1px;
  background: rgba(17, 24, 39, 0.10);
  margin: 12px 0;
}}

.splash {{
  background: linear-gradient(180deg, rgba(42,168,161,0.95), rgba(42,168,161,0.75));
  border-radius: 22px;
  padding: 26px 20px;
  color: white;
  box-shadow: 0 22px 48px rgba(42,168,161,0.26);
}}
.splash h1 {{
  margin: 10px 0 0 0;
  font-size: 26px;
  font-weight: 950;
  line-height: 1.2;
}}
.splash p {{
  margin-top: 10px;
  font-size: 15px;
  opacity: 0.95;
}}
.splash-note {{
  margin-top: 14px;
  font-size: 12px;
  opacity: 0.9;
}}

.kbtn > button {{
  width: 100%;
  background: {PRIMARY} !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 0.75rem 1rem !important;
  font-weight: 900 !important;
  box-shadow: 0 12px 22px rgba(42,168,161,0.22) !important;
}}

.kbtn-secondary > button {{
  width: 100%;
  background: white !important;
  color: {TEXT} !important;
  border: 1px solid {BORDER} !important;
  border-radius: 12px !important;
  padding: 0.75rem 1rem !important;
  font-weight: 900 !important;
}}

.module {{
  background: white;
  border: 1px solid {BORDER};
  border-radius: 18px;
  padding: 16px;
}}
.module .name {{
  font-weight: 950;
  font-size: 16px;
}}
.module .desc {{
  margin-top: 6px;
  font-size: 13.5px;
  color: {MUTED};
  line-height: 1.4;
}}
.pill {{
  display:inline-block;
  margin-top: 10px;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid {BORDER};
  background: #FBFEFE;
}}
.grid {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------- State / Navigation ----------------
def init_state():
    st.session_state.setdefault("route", "home")

init_state()

def nav(route: str):
    st.session_state["route"] = route
    st.rerun()

def header():
    st.markdown(
        """
<div class="klinik-top">
  <div class="klinik-badge"><span>+</span></div>
  <div class="klinik-title">Klinik</div>
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------- Pages ----------------
def page_home():
    st.markdown(
        """
<div class="splash">
  <h1>Your Health Hub,<br/>All in One Place</h1>
  <p>
    Klinik is a growing collection of health-related modules.
    Some modules may use optional images to provide general, educational
    information and help you better understand patterns in your health.
  </p>
  <div class="splash-note">No personal information stored.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="card">
  <h2>What you’ll find here</h2>
  <div class="subtle">
    • Image-based health insights (educational)<br/>
    • Tools to organize observations before a clinic visit<br/>
    • Clear, non-diagnostic explanations
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="kbtn">', unsafe_allow_html=True)
    if st.button("Start"):
        nav("intro")
    st.markdown("</div>", unsafe_allow_html=True)

def page_intro():
    header()
    st.markdown(
        """
<div class="card">
  <h2>Important Information</h2>
  <div class="subtle">
    Klinik is a health hub for learning and organization. It does not diagnose
    medical conditions or replace professional care.
  </div>
  <div class="hr"></div>
  <div class="subtle">
    • Image-based modules can be affected by lighting and camera quality.<br/>
    • If you have severe symptoms or feel unsafe, seek urgent care immediately.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="kbtn">', unsafe_allow_html=True)
    if st.button("I Understand, Continue"):
        nav("modules")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="kbtn-secondary">', unsafe_allow_html=True)
    if st.button("Back"):
        nav("home")
    st.markdown("</div>", unsafe_allow_html=True)

def page_modules():
    header()
    st.markdown(
        """
<div class="card">
  <h2>Modules</h2>
  <div class="subtle">
    This is your health hub. Modules will appear here as they are developed.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    modules: List[Dict[str, str]] = [
        {
            "name": "Fingernail Check (Image)",
            "desc": "Upload a nail photo to get general educational notes about color, ridges, or visible patterns.",
        },
        {
            "name": "Mucus Color Check (Image)",
            "desc": "Provides basic, non-diagnostic information about common mucus color patterns.",
        },
        {
            "name": "Tongue & Lip Color (Image)",
            "desc": "Helps organize visual observations with short follow-up questions.",
        },
        {
            "name": "Bug Bite Check (Image)",
            "desc": "Educational categorization of bite-like patterns and when to consider next steps.",
        },
        {
            "name": "Wound Healing Tracker (Image)",
            "desc": "Helps document how healing appears over time and when to seek care.",
        },
        {
            "name": "Clinic Summary Export",
            "desc": "Turns your inputs into a clean, shareable summary for visits.",
        },
    ]

    st.markdown("<div class='card'><div class='grid'>", unsafe_allow_html=True)
    for m in modules:
        st.markdown(
            f"""
<div class="module">
  <div class="name">{m['name']}</div>
  <div class="desc">{m['desc']}</div>
  <div class="pill">Coming soon</div>
</div>
""",
            unsafe_allow_html=True,
        )
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown('<div class="kbtn-secondary">', unsafe_allow_html=True)
    if st.button("Back"):
        nav("intro")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Router ----------------
route = st.session_state["route"]
if route == "home":
    page_home()
elif route == "intro":
    page_intro()
elif route == "modules":
    page_modules()
else:
    nav("home")
