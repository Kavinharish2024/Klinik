# app.py
# ---------------------------------------------------------
# KLINIK — Educational Wellness Demo (Non-diagnostic)
# ---------------------------------------------------------
# Flow:
#   🏠 Home  ->  ▶️ Get Started  ->  🧩 Modules (choose Mucus Color)
#   ->  📘 Mucus Info  ->  🔬 Detector (upload, analyze, breakdown)
#
# Not a medical device. If you feel unwell, seek professional care.

import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import colorsys
from typing import Tuple, Dict, Any

# ---------- App Setup ----------
st.set_page_config(
    page_title="Klinik",
    page_icon="🩺",
    layout="centered",
    menu_items={
        "Get Help": "https://www.cdc.gov/",
        "About": "Klinik is an educational demo. It is NOT a medical device.",
    }
)

APP_NAME = "Klinik"
ACCENT = "#4F46E5"  # indigo

# ---------- Styles ----------
CSS = f"""
<style>
.small-muted {{ color:#666; font-size:.9rem; }}
.badge {{
  display:inline-block; padding:.25rem .6rem; border-radius:9999px;
  background:{ACCENT}20; color:{ACCENT}; font-weight:600; font-size:.8rem;
}}
.codepill {{
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  background:#00000010; padding:.15rem .45rem; border-radius:.4rem;
}}
hr.soft {{ border:none; height:1px; background:#eaecef; margin:1.1rem 0; }}
footer {{ visibility:hidden; }}

.hero {{
  text-align:center; padding:2.2rem 1rem 1.2rem 1rem;
}}
.hero h1 {{ margin:0; font-size:2.2rem; }}
.hero p {{ margin:.5rem 0 0 0; color:#444; }}

.card {{
  border:1px solid #eaecef; border-radius:1rem; padding:1rem; background:white;
}}
</style>
"""
st.write(CSS, unsafe_allow_html=True)

# ---------- Session State ----------


def init_state():
    if "route" not in st.session_state:
        # home -> modules -> mucus_info -> mucus_detect
        st.session_state["route"] = "home"
    if "mucus_last" not in st.session_state:
        st.session_state["mucus_last"] = {}  # store last analysis


init_state()

# ---------- Utils ----------


def rgb_to_hsv01(r: int, g: int, b: int) -> Tuple[float, float, float]:
    return colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)


def average_rgb(img: Image.Image) -> Tuple[int, int, int]:
    """Median-pool a center crop for robust color sampling."""
    img = ImageOps.exif_transpose(img).convert("RGB")
    small = img.resize((96, 96))
    arr = np.asarray(small, dtype=np.uint8)
    center = arr[24:72, 24:72, :]
    med = np.median(center, axis=(0, 1))
    return tuple(int(x) for x in med)


def hex_chip(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    hx = f"#{r:02x}{g:02x}{b:02x}".upper()
    return f"""
<div style="display:flex;gap:.6rem;align-items:center;">
  <div style="width:22px;height:22px;border-radius:.4rem;border:1px solid #00000022;background:{hx};"></div>
  <code class="codepill">{hx}</code>
  <span class="small-muted">(RGB {r}, {g}, {b})</span>
</div>
"""


def format_float(x: float, nd=3) -> str:
    return f"{x:.{nd}f}"

# ---------- Color Classifier with Rule Trace ----------


def classify_color_with_trace(rgb: Tuple[int, int, int]) -> Dict[str, Any]:
    """Return category + human-readable rule trace explaining the decision."""
    r, g, b = rgb
    h, s, v = rgb_to_hsv01(r, g, b)  # h,s,v in 0..1
    hue = h * 360.0

    rules = []  # collect comparisons for a user-facing breakdown

    def add_rule(name: str, cond: bool, detail: str):
        rules.append({"name": name, "passed": bool(cond), "detail": detail})

    # Threshold checks (ordered)
    category, explanation, key, picked_rule = "uncertain", "Hard to classify.", "uncertain", "none"

    # 1) Very dark -> black
    add_rule("Very dark (black test)", v < 0.18, f"V={format_float(v)} < 0.18")
    if v < 0.18:
        category, explanation, key, picked_rule = "black/very dark", "Very low brightness.", "black", "Very dark"
    else:
        # 2) Clear (very low saturation, high brightness)
        add_rule("Clear test", (s < 0.08 and v > 0.75),
                 f"S={format_float(s)} < 0.08 and V={format_float(v)} > 0.75")
        if s < 0.08 and v > 0.75:
            category, explanation, key, picked_rule = "clear", "Low saturation, high brightness.", "clear", "Clear"
        else:
            # 3) White/gray (low saturation, mid+ brightness)
            add_rule("White/gray test", (s < 0.15 and v > 0.55),
                     f"S={format_float(s)} < 0.15 and V={format_float(v)} > 0.55")
            if s < 0.15 and v > 0.55:
                category, explanation, key, picked_rule = "white/gray", "Low saturation + mid brightness.", "white", "White/Gray"
            else:
                # 4) Yellow band
                add_rule("Yellow hue band", (35 <= hue <= 75 and s >= 0.18),
                         f"35° ≤ H={format_float(hue, 1)}° ≤ 75° and S={format_float(s)} ≥ 0.18")
                if 35 <= hue <= 75 and s >= 0.18:
                    category, explanation, key, picked_rule = "yellow", "Hue in yellow range.", "yellow", "Yellow band"
                else:
                    # 5) Green band
                    add_rule("Green hue band", (75 < hue <= 170 and s >= 0.18),
                             f"75° < H={format_float(hue, 1)}° ≤ 170° and S={format_float(s)} ≥ 0.18")
                    if 75 < hue <= 170 and s >= 0.18:
                        category, explanation, key, picked_rule = "green", "Hue in green range.", "green", "Green band"
                    else:
                        # 6) Red/pink band
                        add_rule("Red/pink hue band",
                                 ((hue <= 20 or hue >= 340)
                                  and s >= 0.2 and v > 0.2),
                                 f"(H≤20° or H≥340°) with S={format_float(s)} ≥ 0.2 and V={format_float(v)} > 0.2")
                        if (hue <= 20 or hue >= 340) and s >= 0.2 and v > 0.2:
                            category, explanation, key, picked_rule = "red/pink", "Hue in red range.", "red", "Red/Pink band"
                        else:
                            # 7) Brown (dark warm)
                            add_rule("Brown warm/dark", (v < 0.4 and s >= 0.25 and 15 < hue < 50),
                                     f"V={format_float(v)} < 0.4 and S={format_float(s)} ≥ 0.25 and 15°<H={format_float(hue, 1)}°<50°")
                            if v < 0.4 and s >= 0.25 and 15 < hue < 50:
                                category, explanation, key, picked_rule = "brown", "Dark warm hue.", "brown", "Brown warm/dark"

    guidance = {
        "clear": ("Often normal hydration/irritation.",
                  ["Usually benign if you feel well.",
                   "Hydrate and monitor.",
                   "Seek care if symptoms persist or worsen."]),
        "white": ("Congestion common.",
                  ["Hydrate, humidify air.",
                   "If >10 days or worsening → see clinician."]),
        "yellow": ("Inflammation, possibly infection.",
                   ["Rest, hydrate.",
                    "See doctor if fever or >10 days."]),
        "green": ("Inflammation or infection.",
                  ["Rest, avoid self-medicating.",
                   "Seek care if fever/shortness of breath."]),
        "brown": ("Old blood or irritants.",
                  ["Avoid smoke/dust.",
                   "See doctor if recurring."]),
        "red": ("Fresh blood.",
                ["Small streaks can be irritation.",
                 "Heavy/recurrent bleeding → urgent care."]),
        "black": ("Dark mucus (pollution/smoke/blood).",
                  ["Avoid irritants.",
                   "Persistent? Get medical help."]),
        "uncertain": ("Unclear result.",
                      ["Re-check under good light.",
                       "Focus on symptoms, not just color."])
    }
    summary, actions = guidance.get(key, guidance["uncertain"])

    return {
        "rgb": rgb,
        "hsv01": (h, s, v),
        "hue_deg": hue,
        "category": category,
        "explanation": explanation,
        "key": key,
        "summary": summary,
        "actions": actions,
        "rules": rules,
        "picked_rule": picked_rule
    }

# ---------- Navigation Helpers ----------


def nav_to(route: str):
    st.session_state["route"] = route
    st.rerun()

# ---------- Pages ----------


def page_home():
    st.markdown(
        f"""
<div class="hero">
  <h1>🩺 {APP_NAME}</h1>
  <p>Explore simple wellness modules. Start with our <b>Mucus Color</b> demo to get a broad color estimate and general guidance.</p>
  <div style="margin-top:1rem;">
    <span class="badge">Educational only — Not a medical device</span>
  </div>
</div>
""",
        unsafe_allow_html=True
    )
    col = st.columns([1, 1, 1])
    with col[1]:
        if st.button("🚀 Get Started", use_container_width=True):
            nav_to("modules")

    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    st.subheader("What to expect")
    st.markdown("""
- **No diagnosis.** These modules provide general, safe information only.
- **Privacy.** Images are processed locally in this session.
- **Clarity.** We show a **transparent breakdown** of how the color category was chosen.
""")


def page_modules():
    st.title("🧩 Modules")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)

    with st.container():
        st.markdown("### 🧪 Mucus Color")
        st.write(
            "Learn how color estimation works and what the results mean, then try the detector."
        )
        if st.button("Open Mucus Module →"):
            nav_to("mucus_info")

    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    if st.button("← Back to Home"):
        nav_to("home")


def page_mucus_info():
    st.title("🧪 Mucus Color — Overview")
    st.caption("Read a quick primer, then proceed to the detector.")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)

    st.subheader("How this works")
    st.write("""
We compute a robust average color from the **center** of your uploaded image,
convert that to **HSV** (hue–saturation–value), then map it to broad categories using threshold rules.
This is **not** a clinical color chart. Lighting and background can strongly affect results.
""")
    st.markdown("""
**Good practice before you proceed:**
- Use a **plain white tissue** or background.
- Prefer **natural/neutral light**; avoid colored bulbs and filters.
- Keep the camera steady and in focus.
""")
    st.markdown("<hr class='soft' />", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔬 Proceed to Detector"):
            nav_to("mucus_detect")
    with c2:
        if st.button("← Back to Modules"):
            nav_to("modules")


def page_mucus_detect():
    st.title("🔬 Mucus Color Detector (Demo)")
    st.caption(
        "Educational only • Not a medical device • If unwell, seek a clinician.")
    st.markdown(
        "Upload a photo on **white tissue** under **natural/neutral light**. Avoid filters and colored backgrounds."
    )

    uploaded = st.file_uploader(
        "Upload a photo (jpg, jpeg, png, webp)", type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded image", width='stretch')

        with st.expander("Advanced (optional)"):
            robust = st.checkbox(
                "Robust averaging (median pool center crop)",
                value=True,
                help="Helps reduce bias from highlights/shadows."
            )

        if st.button("🔍 Analyze"):
            rgb = average_rgb(img) if robust else tuple(
                int(x) for x in np.asarray(
                    ImageOps.exif_transpose(img).convert(
                        "RGB").resize((64, 64)),
                    dtype=np.float32
                ).mean(axis=(0, 1))
            )

            result = classify_color_with_trace(rgb)
            st.session_state["mucus_last"] = result

    # If we have a previous result, show it
    if st.session_state["mucus_last"]:
        res = st.session_state["mucus_last"]
        rgb = res["rgb"]
        h, s, v = res["hsv01"]
        hue = res["hue_deg"]

        st.markdown("<hr class='soft' />", unsafe_allow_html=True)
        st.subheader(f"Estimated: **{res['category']}**")
        st.write(f"*{res['explanation']}*")

        st.markdown(hex_chip(rgb), unsafe_allow_html=True)
        st.markdown(
            f"""
**Color metrics**
- Hue: **{format_float(hue, 1)}°**
- Saturation: **{format_float(s)}**
- Value (brightness): **{format_float(v)}**
""")

        st.markdown("**Decision breakdown (rule trace):**")
        for r in res["rules"]:
            status = "✅" if r["passed"] else "—"
            st.markdown(f"- {status} **{r['name']}** — {r['detail']}")
        st.caption(f"Picked rule: **{res['picked_rule']}**")

        st.markdown("<hr class='soft' />", unsafe_allow_html=True)
        st.markdown(f"**Summary:** {res['summary']}")
        st.markdown("**What you can do (general):**")
        for a in res["actions"]:
            st.markdown(f"- {a}")

        with st.expander("What this means & next steps"):
            st.write("""
- **Color ≠ diagnosis.** Hydration, lighting, and background strongly affect appearance.
- **Track symptoms:** fever, chest pain, shortness of breath, worsening cough, duration >10 days.
- **Seek prompt care** for: heavy/recurrent bleeding, severe breathing issues, high fever, or if you’re immunocompromised/pregnant/very young/older adult.
- **Home care basics:** rest, fluids, humidified air, avoid smoke/dust.
""")

    st.markdown("<hr class='soft' />", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back to Module Info"):
            nav_to("mucus_info")
    with c2:
        if st.button("🏠 Back to Home"):
            nav_to("home")


# ---------- Router ----------
route = st.session_state["route"]
if route == "home":
    page_home()
elif route == "modules":
    page_modules()
elif route == "mucus_info":
    page_mucus_info()
elif route == "mucus_detect":
    page_mucus_detect()
else:
    page_home()

# ---------- Global Footer ----------
st.markdown("<hr class='soft' />", unsafe_allow_html=True)
st.markdown(
    "⚠️ **Disclaimer:** Klinik is an educational demo, not a medical device. "
    "It cannot diagnose or exclude any condition. If you feel unwell, seek professional care."
)
