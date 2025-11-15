# klinik_ml_app.py
import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import colorsys
from typing import Tuple, Dict
import tensorflow as tf

# ---------- Load ML Model ----------
@st.cache_resource
def load_model():
    # You should train a small CNN or use a pre-trained model and save as 'klinik_cnn_model.h5'
    return tf.keras.models.load_model("klinik_cnn_model.h5")

model = load_model()
COLOR_CLASSES = ["clear","white","yellow","green","brown","red","black","uncertain"]

# ---------- App Setup ----------
st.set_page_config(page_title="Klinik 2.0", layout="centered")
st.markdown("<h1 style='text-align:center'>Klinik 2.0</h1>", unsafe_allow_html=True)
st.write("Upload your mucus image and answer a few quick questions for a detailed analysis.")

# ---------- Original EXPLAINERS (Rich Breakdown) ----------
EXPLAINERS: Dict[str, str] = {
    "clear": """### Clear Mucus
Clear mucus is transparent and watery — the most common and typically the healthiest kind.

**Why it happens**  
Your mucus is mostly water with just enough mucins and salts to stay fluid. This helps trap dust and microbes while keeping your airways moist.

**You might see it when:**  
- You’re well hydrated  
- You have mild allergies or dust exposure  
- Early in a cold before symptoms set in  
- The weather or humidity changes

**Try this:**  
Drink plenty of water, use a humidifier if needed, and avoid smoke or strong scents.
""",
    "white": """### White or Gray Mucus
White or gray mucus looks cloudy or milky and often feels thicker.

**Why it happens**  
As mucus loses water, mucins become more concentrated. This often signals mild congestion or slower airflow.

**You might see it when:**  
- You have a minor cold or sinus irritation  
- You’re dehydrated or the air is dry  
- Your nasal passages are inflamed

**Try this:**  
Stay hydrated, rest, and breathe warm, moist air to clear things up.
""",
    "yellow": """### Yellow Mucus
Yellow mucus has a pale to deeper tint and is thicker.

**Why it happens**  
Your immune system sends white blood cells to fight irritants. Their enzymes and proteins give mucus its yellow hue.

**You might see it when:**  
- Fighting a mild cold or allergy  
- Recovering from an infection  
- Slightly dehydrated

**Try this:**  
Rest, drink fluids, and use steam or a saline rinse to stay clear.
""",
    "green": """### Green Mucus
Green mucus is dense and darker, sometimes olive-toned.

**Why it happens**  
A strong immune response fills mucus with enzymes that deepen its color — it doesn’t always mean infection.

**You might see it when:**  
- You have sinus pressure or a lingering cold  
- You’ve been around smoke or pollution  

**Try this:**  
Rinse your nose with saline, rest, and hydrate. If it lasts long or worsens, check in with your doctor.
""",
    "brown": """### Brown Mucus
Brown or rust-colored mucus may look dry or grainy.

**Why it happens**  
It usually contains dried blood or small particles like dust or smoke. As blood oxidizes, it turns darker.

**You might see it when:**  
- Your nose is dry or irritated  
- You’ve been exposed to smoke or dust  

**Try this:**  
Avoid irritants and keep your airways moist with saline spray.
""",
    "red": """### Red or Pink Mucus
Red or pink streaks appear when tiny blood vessels break inside your nose.

**Why it happens**  
The blood mixes with mucus before clotting, creating a pink or red hue.

**You might see it when:**  
- You blow or wipe your nose often  
- The air is dry or cold  

**Try this:**  
Be gentle when cleaning your nose and keep the air humid.
""",
    "black": """### Black or Very Dark Mucus
Black or very dark mucus can look speckled or smoky.

**Why it happens**  
Tiny particles like soot, smoke, or dust stick to mucus. Sometimes old blood deep in the sinuses can darken it too.

**You might see it when:**  
- You’ve been around smoke, dust, or pollution  
- Your sinuses are very dry  

**Try this:**  
Rinse your nose, breathe clean air, and avoid pollutants.
""",
    "uncertain": """### Uncertain or Mixed Color
Sometimes mucus shows multiple tones or unclear colors.

**Why it happens**  
Lighting, filters, or tissue tint can alter the photo, and colors shift naturally as mucus thickens or dries.

**Try this:**  
Retake your photo in natural light with a white background and track any changes over time.
""",
}

# ---------- Image Preprocessing ----------
def preprocess_image(img: Image.Image) -> np.ndarray:
    img = ImageOps.exif_transpose(img).convert("RGB").resize((128,128))
    arr = np.array(img)/255.0
    return np.expand_dims(arr, axis=0)

# ---------- Questionnaire ----------
st.subheader("Symptom Check")
congestion = st.slider("Congestion (0-10)", 0, 10)
throat_dry = st.slider("Throat dryness (0-10)", 0, 10)
fever = st.checkbox("Fever")
smoke = st.checkbox("Recent smoke/dust exposure")

survey_features = np.array([[congestion, throat_dry, int(fever), int(smoke)]])

# ---------- Upload & Analyze ----------
uploaded = st.file_uploader("Upload mucus image (white background, natural light)", type=["jpg","jpeg","png","webp"])
if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Uploaded image", use_container_width=True)

    if st.button("Analyze"):
        # ML Prediction
        img_input = preprocess_image(img)
        preds = model.predict(img_input)[0]
        predicted_class = COLOR_CLASSES[np.argmax(preds)]
        confidence = float(np.max(preds))

        # Adjust confidence using survey (simple heuristic)
        if predicted_class in ["yellow","green"] and (congestion>5 or fever):
            confidence += 0.05
        if predicted_class=="clear" and (congestion>5 or fever):
            confidence -= 0.1
        confidence = min(confidence,1.0)

        # Output with original rich breakdown
        st.markdown(f"**Detected Color:** {predicted_class.capitalize()}  \n**Confidence:** {confidence*100:.1f}%")
        st.markdown(EXPLAINERS[predicted_class])
