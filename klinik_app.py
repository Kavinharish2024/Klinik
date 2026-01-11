# klinik_app.py
import streamlit as st
from typing import List, Dict

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Klinik",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": "Klinik is a symptom organization framework. Not a medical diagnosis tool.",
    },
)

# ---------------- UI palette (green mock vibe) ----------------
PRIMARY = "#2AA8A1"        # teal-green
PRIMARY_DARK = "#1E8E88"
PRIMARY_SOFT = "#BFEFEA"
BG = "#F4F7F7"
CARD = "#FFFFFF"
TEXT = "#103B3A"
MUTED = "#6B7B7B"
BORDER = "rgba(17, 24, 39, 0.08)"

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
  padding-bottom: 2.2rem;
  max-width: 520px;
}}

.card {{
  background: {CARD};
  border: 1px solid {BORDER};
  border-radius: 18px;
  padding: 18px 16px;
  box-shadow: 0 10px 22px rgba(17, 24, 39, 0.06);
  margin: 12px 0;
}}
.subtle {{
  color: {MUTED};
  font-size: 14px;
  margin-top: 4px;
}}

.klinik-top {{
  display:flex;
  align-items:center;
  justify-content:center;
  gap:10px;
  margin-bottom: 14px;
}}
.klinik-badge {{
  width: 30px; height: 30px;
  border-radius: 9px;
  background: {PRIMARY};
  display:flex; align-items:center; justify-content:center;
  box-shadow: 0 10px 22px rgba(42,168,161,0.18);
}}
.klinik-badge span {{
  color: white; font-weight: 900; font-size: 18px; line-height: 1;
}}
.klinik-title {{
  font-weight: 800;
  font-size: 22px;
  letter-spacing: 0.2px;
}}

.hr {{
  height: 1px;
  background: rgba(17, 24, 39, 0.08);
  margin: 12px 0;
}}

.kbtn > button {{
  width: 100%;
  background: {PRIMARY} !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 0.72rem 1rem !important;
  font-weight: 800 !important;
  box-shadow: 0 10px 18px rgba(42,168,161,0.20) !important;
}}
.kbtn > button:hover {{ filter: brightness(0.98) !important; }}

.kbtn-secondary > button {{
  width: 100%;
  background: white !important;
  color: {TEXT} !important;
  border: 1px solid {BORDER} !important;
  border-radius: 12px !important;
  padding: 0.72rem 1rem !important;
  font-weight: 800 !important;
}}

.splash {{
  background: linear-gradient(180deg, rgba(42,168,161,0.95), rgba(42,168,161,0.70));
  border-radius: 22px;
  padding: 28px 18px;
  color: white;
  border: 1px solid rgba(255,255,255,0.20);
  box-shadow: 0 18px 40px rgba(42,168,161,0.28);
  text-align: center;
}}
.splash h1 {{
  margin: 6px 0 0 0;
  font-size: 26px;
  font-weight: 900;
}}
.splash p {{
  margin: 10px 0 0 0;
  opacity: 0.95;
  font-size: 14px;
}}
.splash-footer {{
  margin-top: 16px;
  font-size: 12px;
  opacity: 0.85;
}}

.module-grid {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}}
.module {{
  background: white;
  border: 1px solid {BORDER};
  border-radius: 16px;
  padding: 14px 14px;
}}
.module .name {{
  font-weight: 900;
  font-size: 16px;
}}
.module .desc {{
  margin-top: 4px;
  font-size: 13px;
  color: {MUTED};
}}
.pill {{
  display:inline-block;
  margin-top: 10px;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid {BORDER};
  color: {TEXT};
  background: #FBFEFE;
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------- State / Nav ----------------
def init_state():
    ss = st.session_state
    ss.setdefault("route", "home")

init_state()

def nav(route: str):
    st.session_state["route"] = route
    st.rerun()

def header():
    st.markdown(
        f"""
<div class="klinik-top">
  <div class="klinik-badge"><span>+</span></div>
  <div class="klinik-title">Klinik</div>
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------- Pages ----------------
def page_home():
    # All-green splash intro like your reference
    st.markdown(
        f"""
<div class="splash">
  <div style="display:flex; justify-content:center; gap:10px; align-items:center;">
    <div class="klinik-badge" style="background: rgba(255,255,255,0.22); box-shadow:none;">
      <span style="color:white;">+</span>
    </div>
    <div style="font-weight:900; font-size:22px;">Klinik</div>
  </div>

  <h1>Check Symptoms<br/> & Next Steps</h1>
  <p>A framework to organize symptoms and guide what to do next.</p>

  <div class="splash-footer">No personal information stored.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

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
    Klinik is a symptom organization tool and project framework. It does not diagnose.
  </div>
  <div class="hr"></div>
  <div class="subtle">
    • It may suggest general next steps (like “monitor” or “seek care”), but it is not medical advice.<br/>
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
    This is the framework hub. Modules will appear here as you build them.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Empty placeholders (you can rename these later)
    placeholders: List[Dict[str, str]] = [
        {"name": "Symptom Checker", "desc": "Coming soon. Structured Q&A + safe next-step guidance.", "tag": "Planned"},
        {"name": "Clinic Summary Export", "desc": "Coming soon. Clean printable summary for visits.", "tag": "Planned"},
        {"name": "Image-Based Checkups", "desc": "Coming soon. Separate modules (opt-in) for visual signals.", "tag": "Planned"},
    ]

    st.markdown("<div class='card'><div class='module-grid'>", unsafe_allow_html=True)
    for m in placeholders:
        st.markdown(
            f"""
<div class="module">
  <div class="name">{m['name']}</div>
  <div class="desc">{m['desc']}</div>
  <div class="pill">{m['tag']}</div>
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
