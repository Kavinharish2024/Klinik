# klinik_app.py
import streamlit as st
from typing import List, Dict

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Klinik",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": "Klinik is a health hub with multiple modules that help users learn patterns and prepare information for care visits. Not a medical diagnosis tool.",
    },
)

# ---------------- UI palette (green/teal mock vibe) ----------------
PRIMARY = "#2AA8A1"
PRIMARY_DARK = "#1E8E88"
BG = "#F4F7F7"
CARD = "#FFFFFF"
TEXT = "#0F3636"
MUTED = "#6B7B7B"
BORDER = "rgba(17, 24, 39, 0.10)"

# ---------------- CSS: iPhone-like 9:16 frame + cards ----------------
CSS = f"""
<style>
/* Base */
.stApp {{
  background: {BG};
  color: {TEXT};
  font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}}
header, footer {{ visibility: hidden; }}
.block-container {{
  padding-top: 1.0rem;
  padding-bottom: 2.2rem;
  max-width: 980px; /* allow the centered phone to sit nicely */
}}

/* Phone frame (rough iPhone 13/14 size: 390 x 844) */
.phone-wrap {{
  display: flex;
  justify-content: center;
}}
.phone {{
  width: 390px;
  height: 844px;
  background: #F8FAFA;
  border-radius: 26px;
  border: 1px solid rgba(17,24,39,0.14);
  box-shadow: 0 24px 70px rgba(17,24,39,0.14);
  overflow: hidden;
  position: relative;
}}
.phone-inner {{
  height: 100%;
  overflow-y: auto;
  padding: 18px 16px 22px 16px;
}}

/* nice subtle scrollbar */
.phone-inner::-webkit-scrollbar {{
  width: 8px;
}}
.phone-inner::-webkit-scrollbar-thumb {{
  background: rgba(17,24,39,0.12);
  border-radius: 999px;
}}

/* Klinik header */
.klinik-top {{
  display:flex;
  align-items:center;
  justify-content:center;
  gap:10px;
  margin: 6px 0 14px 0;
}}
.klinik-badge {{
  width: 30px; height: 30px;
  border-radius: 10px;
  background: {PRIMARY};
  display:flex; align-items:center; justify-content:center;
  box-shadow: 0 12px 26px rgba(42,168,161,0.20);
}}
.klinik-badge span {{
  color: white; font-weight: 950; font-size: 18px; line-height: 1;
}}
.klinik-title {{
  font-weight: 900;
  font-size: 22px;
  letter-spacing: 0.2px;
}}

/* Cards */
.card {{
  background: {CARD};
  border: 1px solid {BORDER};
  border-radius: 18px;
  padding: 16px 14px;
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
  line-height: 1.35;
}}
.hr {{
  height: 1px;
  background: rgba(17, 24, 39, 0.10);
  margin: 12px 0;
}}

/* Splash (home screen) */
.splash {{
  background: linear-gradient(180deg, rgba(42,168,161,0.98), rgba(42,168,161,0.70));
  border-radius: 22px;
  padding: 22px 16px;
  color: white;
  border: 1px solid rgba(255,255,255,0.20);
  box-shadow: 0 22px 48px rgba(42,168,161,0.26);
  text-align: left;
}}
.splash-top {{
  display:flex;
  align-items:center;
  gap:10px;
}}
.splash h1 {{
  margin: 12px 0 0 0;
  font-size: 24px;
  font-weight: 950;
  line-height: 1.15;
}}
.splash p {{
  margin: 10px 0 0 0;
  opacity: 0.95;
  font-size: 14px;
  line-height: 1.35;
}}
.splash-note {{
  margin-top: 14px;
  font-size: 12px;
  opacity: 0.9;
}}

/* Buttons */
.kbtn > button {{
  width: 100%;
  background: {PRIMARY} !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 0.74rem 1rem !important;
  font-weight: 900 !important;
  box-shadow: 0 12px 22px rgba(42,168,161,0.22) !important;
}}
.kbtn > button:hover {{ filter: brightness(0.98) !important; }}

.kbtn-secondary > button {{
  width: 100%;
  background: white !important;
  color: {TEXT} !important;
  border: 1px solid {BORDER} !important;
  border-radius: 12px !important;
  padding: 0.74rem 1rem !important;
  font-weight: 900 !important;
}}

/* Module tiles */
.module {{
  background: white;
  border: 1px solid {BORDER};
  border-radius: 18px;
  padding: 14px 14px;
}}
.module .name {{
  font-weight: 950;
  font-size: 16px;
}}
.module .desc {{
  margin-top: 4px;
  font-size: 13px;
  color: {MUTED};
  line-height: 1.35;
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
.grid {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}}
.small {{
  font-size: 12.5px;
  color: {MUTED};
  line-height: 1.35;
}}

/* Make Streamlit widgets feel less "desktop" */
div[data-baseweb="input"] input {{
  border-radius: 14px !important;
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

def phone_start():
    st.markdown('<div class="phone-wrap"><div class="phone"><div class="phone-inner">', unsafe_allow_html=True)

def phone_end():
    st.markdown("</div></div></div>", unsafe_allow_html=True)

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
    phone_start()

    # Home = all-green, simpler, higher contrast, easy to read
    st.markdown(
        f"""
<div class="splash">
  <div class="splash-top">
    <div class="klinik-badge" style="background: rgba(255,255,255,0.22); box-shadow:none;">
      <span style="color:white;">+</span>
    </div>
    <div style="font-weight:950; font-size:20px;">Klinik</div>
  </div>

  <h1>Your Health Hub<br/>in One Place</h1>
  <p>
    Klinik is a growing set of health-related modules.
    Some modules can use optional images (like fingernails or mucus) to provide
    general, educational information and help you prepare for care.
  </p>
  <div class="splash-note">No personal information stored.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        """
<h2>How it works</h2>
<div class="subtle">
1) Read a quick safety note<br/>
2) Browse modules<br/>
3) (Later) Use modules as you build them
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="kbtn">', unsafe_allow_html=True)
    if st.button("Start"):
        nav("intro")
    st.markdown("</div>", unsafe_allow_html=True)

    phone_end()

def page_intro():
    phone_start()
    header()

    st.markdown(
        """
<div class="card">
  <h2>Important Information</h2>
  <div class="subtle">
    Klinik is a health hub. It can show general, educational guidance and help you organize what you notice,
    but it does not diagnose conditions.
  </div>
  <div class="hr"></div>
  <div class="subtle">
    • Image-based modules (when added) are optional and can be affected by lighting and camera quality.<br/>
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

    phone_end()

def page_modules():
    phone_start()
    header()

    st.markdown(
        """
<div class="card">
  <h2>Modules</h2>
  <div class="subtle">
    This is your hub. Modules will show up here as you build them.
    For now, everything is “Coming soon”.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Placeholders based on your examples (NOT diagnostic wording)
    placeholders: List[Dict[str, str]] = [
        {
            "name": "Fingernail Check (Image)",
            "desc": "Upload a nail photo to get general educational notes (ex: discoloration, vertical ridges).",
            "tag": "Coming soon",
        },
        {
            "name": "Mucus Color Check (Image)",
            "desc": "Upload a photo to get basic, non-diagnostic info about common mucus color patterns.",
            "tag": "Coming soon",
        },
        {
            "name": "Tongue & Lip Color (Image)",
            "desc": "Educational notes from photos plus a short questionnaire to organize observations.",
            "tag": "Coming soon",
        },
        {
            "name": "Bug Bite Check (Image)",
            "desc": "Helps categorize bite-like patterns and suggests general next steps (monitor vs. get checked).",
            "tag": "Coming soon",
        },
        {
            "name": "Wound Healing Stage (Image)",
            "desc": "Helps document how healing looks over time and when to consider getting help.",
            "tag": "Coming soon",
        },
        {
            "name": "Clinic Summary Export",
            "desc": "Turns your inputs into a clean summary you can share at a visit.",
            "tag": "Coming soon",
        },
    ]

    st.markdown("<div class='card'><div class='grid'>", unsafe_allow_html=True)
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

    st.markdown(
        """
<div class="card">
  <div class="small">
    Tip: When you start adding modules, keep each one focused:
    one input type, one goal, one safe output.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="kbtn-secondary">', unsafe_allow_html=True)
    if st.button("Back"):
        nav("intro")
    st.markdown("</div>", unsafe_allow_html=True)

    phone_end()

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
