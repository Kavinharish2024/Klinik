# klinik_app.py
import streamlit as st
from typing import Dict, Any, List

# ---------- Page config ----------
st.set_page_config(
    page_title="Klinik",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": "Klinik helps users organize symptoms and understand next steps. Not a medical diagnosis.",
    },
)

# ---------- Theme / UI palette (closer to your mock) ----------
PRIMARY = "#2AA8A1"       # teal
PRIMARY_DARK = "#1E8E88"
BG = "#F5F7F7"
CARD = "#FFFFFF"
TEXT = "#163A3A"
MUTED = "#6B7B7B"
BORDER = "rgba(17, 24, 39, 0.08)"
DANGER = "#D96565"
WARNING = "#F2C14E"
SUCCESS = "#50B37A"

CSS = f"""
<style>
.stApp {{
  background: {BG};
  color: {TEXT};
  font-family: -apple-system, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}}
header, footer {{ visibility: hidden; }}

.block-container {{
  padding-top: 1.6rem;
  padding-bottom: 2.2rem;
  max-width: 520px;
}}

.klinik-top {{
  display:flex;
  align-items:center;
  justify-content:center;
  gap:10px;
  margin-bottom: 10px;
}}
.klinik-badge {{
  width: 28px; height: 28px;
  border-radius: 8px;
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
.card {{
  background: {CARD};
  border: 1px solid {BORDER};
  border-radius: 16px;
  padding: 18px 16px;
  box-shadow: 0 10px 22px rgba(17, 24, 39, 0.06);
  margin: 12px 0;
}}
.card h2 {{
  margin: 0 0 6px 0;
  font-size: 20px;
}}
.subtle {{
  color: {MUTED};
  font-size: 14px;
  margin-top: 2px;
}}
.pillrow {{
  display:flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}}
.pill {{
  border: 1px solid {BORDER};
  border-radius: 999px;
  padding: 7px 10px;
  font-size: 13px;
  color: {TEXT};
  background: #FBFEFE;
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
  padding: 0.7rem 1rem !important;
  font-weight: 800 !important;
  box-shadow: 0 10px 18px rgba(42,168,161,0.20) !important;
}}
.kbtn > button:hover {{
  filter: brightness(0.97) !important;
}}
.kbtn-secondary > button {{
  width: 100%;
  background: white !important;
  color: {TEXT} !important;
  border: 1px solid {BORDER} !important;
  border-radius: 12px !important;
  padding: 0.7rem 1rem !important;
  font-weight: 800 !important;
}}
.kbtn-danger > button {{
  width: 100%;
  background: {DANGER} !important;
  color: white !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 0.7rem 1rem !important;
  font-weight: 900 !important;
}}
.tag {{
  display:inline-flex;
  align-items:center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid {BORDER};
  font-size: 13px;
  margin: 4px 6px 0 0;
  background: #FBFEFE;
}}
.tag b {{ font-weight: 800; }}
.warn {{
  border-left: 5px solid {WARNING};
  padding: 10px 12px;
  background: rgba(242,193,78,0.14);
  border-radius: 12px;
  margin-top: 10px;
}}
.danger {{
  border-left: 5px solid {DANGER};
  padding: 10px 12px;
  background: rgba(217,101,101,0.14);
  border-radius: 12px;
  margin-top: 10px;
}}
.ok {{
  border-left: 5px solid {SUCCESS};
  padding: 10px 12px;
  background: rgba(80,179,122,0.14);
  border-radius: 12px;
  margin-top: 10px;
}}
.small {{
  font-size: 13px;
  color: {MUTED};
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------- State ----------
def init_state():
    ss = st.session_state
    ss.setdefault("route", "start")
    ss.setdefault("lang", "English")
    ss.setdefault("symptoms", [])          # List[str]
    ss.setdefault("duration", "Today")
    ss.setdefault("severity", "Mild")
    ss.setdefault("risk", None)            # "Low" | "Moderate" | "High"
    ss.setdefault("summary", "")

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

# ---------- Simple risk logic (not diagnosis) ----------
RED_FLAGS = {
    "Trouble breathing",
    "Chest pain",
    "Fainting / Severe dizziness",
    "Severe allergic reaction",
    "Severe bleeding",
}

COMMON = ["Fever", "Cough", "Stomach pain", "Sore throat", "Headache", "Nausea", "Rash"]

def compute_risk(symptoms: List[str], duration: str, severity: str) -> str:
    # high if red-flag or severe + longer duration
    if any(s in RED_FLAGS for s in symptoms):
        return "High"
    if severity == "Severe":
        return "High" if duration in ["Over a Week"] else "Moderate"
    if severity == "Moderate":
        return "Moderate" if duration in ["2–3 Days", "Over a Week"] else "Low"
    # mild
    return "Low" if duration in ["Today"] else "Moderate"

def build_summary(ss: Dict[str, Any]) -> str:
    symptoms = ss["symptoms"] if ss["symptoms"] else ["(none selected)"]
    lines = []
    lines.append("KLINIK SYMPTOM SUMMARY")
    lines.append(f"Language: {ss['lang']}")
    lines.append("")
    lines.append("Reported:")
    for s in symptoms:
        lines.append(f"- {s}")
    lines.append("")
    lines.append(f"Duration: {ss['duration']}")
    lines.append(f"Severity: {ss['severity']}")
    lines.append("")
    lines.append(f"Suggested next step (non-diagnostic): {ss['risk']} risk")
    lines.append("")
    lines.append("Emergency warning signs:")
    lines.append("- Trouble breathing")
    lines.append("- Chest pain")
    lines.append("- Fainting / severe dizziness")
    return "\n".join(lines)

# ---------- Pages ----------
def page_start():
    header()
    st.markdown(
        f"""
<div class="card" style="background: linear-gradient(180deg, rgba(42,168,161,0.30), rgba(42,168,161,0.08));">
  <h2>Check Symptoms<br/>& Next Steps</h2>
  <div class="subtle">No personal information stored.</div>
  <div class="hr"></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="kbtn">', unsafe_allow_html=True)
    if st.button("Start"):
        nav("language")
    st.markdown("</div>", unsafe_allow_html=True)

def page_language():
    header()
    st.markdown(
        """
<div class="card">
  <h2>Select Your Language</h2>
  <div class="subtle">Choose the language you want to use.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="kbtn">', unsafe_allow_html=True)
        if st.button("🇺🇸 English"):
            st.session_state["lang"] = "English"
            nav("info")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="kbtn-secondary">', unsafe_allow_html=True)
        if st.button("🇪🇸 Español"):
            st.session_state["lang"] = "Español"
            nav("info")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="kbtn-secondary">', unsafe_allow_html=True)
    if st.button("Back"):
        nav("start")
    st.markdown("</div>", unsafe_allow_html=True)

def page_info():
    header()
    st.markdown(
        """
<div class="card">
  <h2>Important Information</h2>
  <div class="subtle">I will help you organize symptoms and suggest next steps.</div>
  <div class="hr"></div>
  <div class="small">
    • I am not a doctor and cannot diagnose medical conditions.<br/>
    • If you have severe symptoms, seek emergency help now.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="kbtn">', unsafe_allow_html=True)
    if st.button("I Understand, Continue"):
        nav("symptom_input")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="kbtn-danger">', unsafe_allow_html=True)
    if st.button("Get Emergency Help"):
        nav("emergency")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="kbtn-secondary">', unsafe_allow_html=True)
    if st.button("Back"):
        nav("language")
    st.markdown("</div>", unsafe_allow_html=True)

def page_symptom_input():
    header()
    st.markdown(
        """
<div class="card">
  <h2>What’s bringing you today?</h2>
  <div class="subtle">Type, tap, or select common symptoms.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    typed = st.text_input("Type a symptom (optional)", placeholder="e.g., fever, cough, stomach pain")
    if typed:
        if st.button("Add typed symptom"):
            st.session_state["symptoms"].append(typed.strip().title())
            st.session_state["symptoms"] = sorted(list(set(st.session_state["symptoms"])))
            st.rerun()

    st.markdown("<div class='card'><div class='subtle'>Quick picks</div><div class='pillrow'>", unsafe_allow_html=True)
    for s in COMMON:
        if st.button(s, key=f"pick_{s}"):
            st.session_state["symptoms"].append(s)
            st.session_state["symptoms"] = sorted(list(set(st.session_state["symptoms"])))
            st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)

    if st.session_state["symptoms"]:
        st.markdown("<div class='card'><h2>Your stages</h2>", unsafe_allow_html=True)
        for s in st.session_state["symptoms"]:
            st.markdown(f"<span class='tag'><b>•</b> {s}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="kbtn">', unsafe_allow_html=True)
    if st.button("Continue"):
        nav("learn_more")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="kbtn-secondary">', unsafe_allow_html=True)
    if st.button("Back"):
        nav("info")
    st.markdown("</div>", unsafe_allow_html=True)

def page_learn_more():
    header()
    st.markdown(
        """
<div class="card">
  <h2>Let’s learn more…</h2>
  <div class="subtle">A couple quick questions to guide next steps.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.session_state["duration"] = st.radio(
        "How long have you had this?",
        ["Today", "2–3 Days", "Over a Week"],
        index=["Today", "2–3 Days", "Over a Week"].index(st.session_state["duration"]),
        horizontal=True,
    )

    st.session_state["severity"] = st.radio(
        "How severe does it feel?",
        ["Mild", "Moderate", "Severe"],
        index=["Mild", "Moderate", "Severe"].index(st.session_state["severity"]),
        horizontal=True,
    )

    st.markdown('<div class="kbtn">', unsafe_allow_html=True)
    if st.button("Confirm & Get Next Steps  ›"):
        st.session_state["risk"] = compute_risk(
            st.session_state["symptoms"],
            st.session_state["duration"],
            st.session_state["severity"],
        )
        nav("next_steps")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="kbtn-secondary">', unsafe_allow_html=True)
    if st.button("Back"):
        nav("symptom_input")
    st.markdown("</div>", unsafe_allow_html=True)

def page_next_steps():
    header()
    risk = st.session_state.get("risk") or "Moderate"

    # banner tone
    if risk == "High":
        banner = f"<div class='danger'><b>High Risk</b><br/>Recommendation: Seek urgent care now.</div>"
    elif risk == "Moderate":
        banner = f"<div class='warn'><b>Moderate Risk</b><br/>Recommendation: Consider a clinic visit today.</div>"
    else:
        banner = f"<div class='ok'><b>Low Risk</b><br/>Recommendation: Home care and monitor symptoms.</div>"

    st.markdown(
        f"""
<div class="card">
  <h2>Next Steps for You</h2>
  {banner}
  <div class="hr"></div>
  <div class="small"><b>When to get urgent help</b></div>
  <div class="small">• Trouble breathing<br/>• Chest pain<br/>• Dizziness or fainting</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="kbtn">', unsafe_allow_html=True)
    if st.button("Continue to Summary"):
        st.session_state["summary"] = build_summary(st.session_state)
        nav("summary")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="kbtn-secondary">', unsafe_allow_html=True)
    if st.button("Back"):
        nav("learn_more")
    st.markdown("</div>", unsafe_allow_html=True)

def page_summary():
    header()
    st.markdown(
        """
<div class="card" style="background: linear-gradient(180deg, rgba(42,168,161,0.22), rgba(42,168,161,0.06));">
  <h2>Your Summary is Ready</h2>
  <div class="subtle">You can copy or download this to share with a clinic.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    summary = st.session_state.get("summary") or build_summary(st.session_state)
    st.text_area("Summary", value=summary, height=240)

    st.download_button(
        "Print Summary (Download .txt)",
        data=summary,
        file_name="klinik_summary.txt",
        mime="text/plain",
        use_container_width=True,
    )

    st.markdown('<div class="kbtn-secondary">', unsafe_allow_html=True)
    if st.button("Done"):
        # reset but keep language
        lang = st.session_state["lang"]
        st.session_state.clear()
        init_state()
        st.session_state["lang"] = lang
        nav("start")
    st.markdown("</div>", unsafe_allow_html=True)

def page_emergency():
    header()
    st.markdown(
        """
<div class="card">
  <h2>Get Emergency Help</h2>
  <div class="danger">
    If you think this is an emergency, call your local emergency number (US: 911) right now.
  </div>
  <div class="hr"></div>
  <div class="small">
    Emergency warning signs can include trouble breathing, chest pain, severe allergic reaction,
    fainting, or uncontrolled bleeding.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="kbtn-secondary">', unsafe_allow_html=True)
    if st.button("Back"):
        nav("info")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Router ----------
route = st.session_state["route"]
if route == "start":
    page_start()
elif route == "language":
    page_language()
elif route == "info":
    page_info()
elif route == "symptom_input":
    page_symptom_input()
elif route == "learn_more":
    page_learn_more()
elif route == "next_steps":
    page_next_steps()
elif route == "summary":
    page_summary()
elif route == "emergency":
    page_emergency()
else:
    nav("start")
