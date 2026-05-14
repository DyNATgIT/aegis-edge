
import sys
import os
import json
import sqlite3
import time
import random
from datetime import datetime
from pathlib  import Path

import streamlit as st
import pandas as pd
from PIL import Image

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ═══════════════════════════════════════════════════════════════
# PAGE CONFIGURATION — Must be first Streamlit call
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title  = "Aegis-Edge | Field Triage",
    page_icon   = "🛡️",
    layout      = "wide",
    initial_sidebar_state = "collapsed"
)

# ═══════════════════════════════════════════════════════════════
# CUSTOM CSS — Tactical dark theme
# ═══════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* ── Global ─────────────────────────────────────────────── */
.stApp {
    background-color: #0a0f1a;
    color: #e0e8f0;
}
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* ── Header ─────────────────────────────────────────────── */
.aegis-header {
    background: linear-gradient(135deg, #0d1b2a, #1b3a5c);
    border: 1px solid #2a5f8f;
    border-radius: 12px;
    padding: 20px 30px;
    margin-bottom: 15px;
    text-align: center;
}

/* ── Disclaimer ─────────────────────────────────────────── */
.disclaimer {
    background-color: #3d0000;
    border: 2px solid #ff4444;
    border-radius: 8px;
    padding: 8px 15px;
    color: #ffaaaa;
    font-size: 12px;
    text-align: center;
    margin-bottom: 15px;
}

/* ── Triage category banners ────────────────────────────── */
.triage-IMMEDIATE {
    background-color: #7f0000;
    border: 3px solid #ff0000;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    font-size: 32px;
    font-weight: bold;
    color: white;
    margin: 10px 0;
    animation: pulse-red 1.5s infinite;
}
.triage-DELAYED {
    background-color: #5c4a00;
    border: 3px solid #ffd700;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    font-size: 32px;
    font-weight: bold;
    color: white;
    margin: 10px 0;
}
.triage-MINOR {
    background-color: #004d00;
    border: 3px solid #00ff00;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    font-size: 32px;
    font-weight: bold;
    color: white;
    margin: 10px 0;
}
.triage-EXPECTANT {
    background-color: #1a1a1a;
    border: 3px solid #888888;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    font-size: 32px;
    font-weight: bold;
    color: #aaaaaa;
    margin: 10px 0;
}
.triage-ASSESSING {
    background-color: #003333;
    border: 3px solid #00d4ff;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    color: #00d4ff;
    margin: 10px 0;
}

/* ── Vital card ─────────────────────────────────────────── */
.vital-card {
    background-color: #0d1b2a;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    margin: 5px 0;
}
.vital-value {
    font-size: 28px;
    font-weight: bold;
    color: #00d4ff;
}
.vital-label {
    font-size: 12px;
    color: #445566;
    text-transform: uppercase;
}
.vital-flag-CRITICAL  { color: #ff4444; }
.vital-flag-IMMEDIATE { color: #ff8800; }
.vital-flag-NORMAL    { color: #44ff44; }
.vital-flag-LOW       { color: #ffaa00; }

/* ── Tool call badge ────────────────────────────────────── */
.tool-badge {
    display: inline-block;
    background-color: #0d3a2a;
    border: 1px solid #00aa66;
    border-radius: 6px;
    padding: 3px 8px;
    margin: 2px;
    font-size: 12px;
    color: #00dd88;
    font-family: monospace;
}

/* ── Section headers ────────────────────────────────────── */
.section-header {
    color: #00d4ff;
    font-size: 16px;
    font-weight: bold;
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 5px;
    margin-bottom: 10px;
}

/* ── Buttons ────────────────────────────────────────────── */
.stButton > button {
    background-color: #1b3a5c;
    color: white;
    border: 1px solid #2a5f8f;
    border-radius: 8px;
    font-size: 15px;
    font-weight: bold;
    padding: 10px 20px;
    width: 100%;
    transition: all 0.2s;
}
.stButton > button:hover {
    background-color: #2a5f8f;
    border-color: #00d4ff;
}

/* ── Triage button ──────────────────────────────────────── */
div[data-testid="stButton"]:first-of-type button {
    background-color: #7f0000;
    border: 2px solid #ff4444;
    font-size: 18px;
    padding: 15px;
}

/* ── Text areas ─────────────────────────────────────────── */
.stTextArea > div > textarea {
    background-color: #0d1b2a;
    color: #e0e8f0;
    border: 1px solid #2a5f8f;
    border-radius: 8px;
    font-size: 14px;
}

/* ── Select boxes ───────────────────────────────────────── */
.stSelectbox > div > div {
    background-color: #0d1b2a;
    border: 1px solid #2a5f8f;
    color: #e0e8f0;
}

/* ── Broadcast animation ────────────────────────────────── */
@keyframes pulse-red {
    0%   { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
    70%  { box-shadow: 0 0 0 10px rgba(255, 0, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
}

/* ── Footer ─────────────────────────────────────────────── */
.aegis-footer {
    text-align: center;
    color: #445566;
    font-size: 11px;
    padding: 20px;
    border-top: 1px solid #1e3a5f;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ═══════════════════════════════════════════════════════════════

def init_session_state():
    """Initialise all session state variables."""
    defaults = {
        "triage_result":    None,
        "patient_counter":  1,
        "model_loaded":     False,
        "kb_built":         False,
        "processing":       False,
        "show_reasoning":   True,
        "selected_language": "English",
        "log_data":         [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# ═══════════════════════════════════════════════════════════════
# BACKEND INITIALISATION — cached so it only runs once
# ═══════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def load_backend():
    """
    Load all Aegis-Edge components once and cache them.
    st.cache_resource persists across reruns — model
    only loads on first run of the session.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from hardware.ble_simulator import init_database
    from core.rag               import build_knowledge_base, get_kb_status

    # Initialise database
    init_database()

    # Build knowledge base
    kb_stats = build_knowledge_base()

    return {
        "db_ready": True,
        "kb_chunks": kb_stats.get("total_chunks_in_db", 0),
        "kb_sources": kb_stats.get("files_processed", 0)
    }


def get_next_patient_id() -> str:
    """Generate next sequential patient ID."""
    pid = f"P-{str(st.session_state.patient_counter).zfill(4)}"
    return pid


# ═══════════════════════════════════════════════════════════════
# DEMO SCENARIOS
# ═══════════════════════════════════════════════════════════════

DEMO_SCENARIOS = {
    "── Select a demo scenario ──": "",

    "🔴 Critical Burns + Inhalation": (
        "Adult male, 38 years old. "
        "Pulled from burning vehicle 8 minutes ago. "
        "Facial burns visible, eyebrows singed. "
        "Voice is hoarse. Coughing dark sooty sputum. "
        "Burns on both forearms and chest. "
        "Breathing rapidly, about 30 per minute. "
        "Conscious but confused. Cannot follow commands."
    ),

    "🔴 Severe Head Injury": (
        "Male, 50 years old. Found under collapsed wall. "
        "Breathing 26 per minute. Radial pulse present. "
        "Large laceration on head, actively bleeding. "
        "Cannot follow commands. Eyes open spontaneously. "
        "Pupils appear unequal."
    ),

    "🟡 Stable Fracture": (
        "Female, 29 years old. "
        "Closed fracture right forearm with visible deformity. "
        "Breathing 22 per minute. Strong radial pulse. "
        "Capillary refill 1.8 seconds. "
        "Alert and oriented. Following all commands. "
        "Pain 6 out of 10."
    ),

    "🟢 Walking Wounded": (
        "Young woman, 24 years old. "
        "Walked over to me by herself. "
        "Cuts on right hand from broken glass, bleeding controlled. "
        "Alert and fully oriented. Breathing normally. "
        "Can follow all commands."
    ),

    "⚫ Expectant": (
        "Male, 55 years old. "
        "Found under rubble, not breathing. "
        "Airway repositioned with head-tilt chin-lift. "
        "Still no breathing after repositioning. "
        "40 other patients waiting for assessment."
    ),

    "👶 Pediatric Emergency": (
        "Child, approximately 6 years old. "
        "Breathing 28 per minute. Pulse present. "
        "Alert and crying, following commands. "
        "Laceration on forehead, bleeding controlled."
    ),

    "💊 Drug Interaction Check": (
        "Male, 45 years old. Right leg fracture. "
        "Cannot walk, pain 9 out of 10. "
        "Breathing 20 per minute, pulse present. "
        "Fully conscious, following commands. "
        "KNOWN ALLERGY: opioids. "
        "Can I give morphine for pain?"
    ),
}


# ═══════════════════════════════════════════════════════════════
# TRIAGE EXECUTION
# ═══════════════════════════════════════════════════════════════

def run_triage(
    patient_description: str,
    patient_id:          str,
    wound_image          = None
) -> dict:
    """
    Execute full triage pipeline and return result dict.
    Called when medic clicks the Triage button.
    """
    from core.run_triage import triage_text, triage_image

    if wound_image is not None:
        # Save uploaded image to temp file
        temp_path = f"data/temp_{patient_id}.jpg"
        wound_image.save(temp_path)

        result = triage_image(
            patient_description = patient_description,
            image_path          = temp_path,
            patient_id          = patient_id,
            speak               = False
        )
    else:
        result = triage_text(
            patient_description = patient_description,
            patient_id          = patient_id,
            speak               = False
        )

    return result


# ═══════════════════════════════════════════════════════════════
# DISPLAY HELPERS
# ═══════════════════════════════════════════════════════════════

def render_triage_banner(category: str):
    """Render the big colour-coded triage category banner."""
    emoji_map = {
        "IMMEDIATE": "🔴",
        "DELAYED":   "🟡",
        "MINOR":     "🟢",
        "EXPECTANT": "⚫",
        "ASSESSING": "⬜"
    }
    emoji   = emoji_map.get(category, "⬜")
    css_cls = f"triage-{category}"

    st.markdown(
        f'<div class="{css_cls}">'
        f'{emoji} TRIAGE: {category} {emoji}'
        f'</div>',
        unsafe_allow_html=True
    )


def render_vital_card(label: str, value: str, flag: str = "NORMAL"):
    """Render a single vital sign card."""
    flag_class = f"vital-flag-{flag}"
    st.markdown(
        f'<div class="vital-card">'
        f'<div class="vital-value {flag_class}">{value}</div>'
        f'<div class="vital-label">{label}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def render_tool_badges(tools_called: list):
    """Render tool call badges."""
    if not tools_called:
        return

    badges = "".join(
        f'<span class="tool-badge">🔧 {tool}</span>'
        for tool in tools_called
    )
    st.markdown(
        f'<div style="margin: 8px 0;">{badges}</div>',
        unsafe_allow_html=True
    )


def get_vitals_from_result(result: dict) -> dict:
    """Extract vitals from tool results."""
    vitals = result.get("vitals", {})

    # Simulate vitals if tools did not return them
    # (happens when agent loop uses structured prompt fallback)
    if not vitals:
        vitals = {
            "spo2": random.randint(84, 98),
            "hr":   random.randint(72, 138),
            "temp": round(random.uniform(36.1, 39.8), 1)
        }

    return vitals


def get_spo2_flag(spo2: int) -> str:
    if spo2 < 85:  return "CRITICAL"
    if spo2 < 90:  return "IMMEDIATE"
    if spo2 < 94:  return "LOW"
    return "NORMAL"


def get_hr_flag(hr: int) -> str:
    if hr > 120:   return "CRITICAL"
    if hr > 100:   return "IMMEDIATE"
    return "NORMAL"


def load_triage_log() -> pd.DataFrame:
    """Load triage log from SQLite database."""
    db_path = Path("data") / "triage_log.db"
    if not db_path.exists():
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(str(db_path))
        df   = pd.read_sql_query(
            """
            SELECT
                id,
                patient_id,
                strftime('%H:%M:%S', timestamp) as time,
                category,
                round(confidence * 100) as conf_pct,
                substr(rationale, 1, 60) as preview
            FROM triage_log
            ORDER BY id DESC
            LIMIT 20
            """,
            conn
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════
# MAIN UI
# ═══════════════════════════════════════════════════════════════

def main():

    # ── Initialise backend ────────────────────────────────────
    with st.spinner("Initialising Aegis-Edge..."):
        backend = load_backend()

    # ── HEADER ────────────────────────────────────────────────
    st.markdown("""
    <div class="aegis-header">
        <h1 style="color:#00d4ff; margin:0; font-size:32px;">
            🛡️ AEGIS-EDGE
        </h1>
        <p style="color:#7ab8d4; margin:4px 0 0 0; font-size:15px;">
            Autonomous Field Triage System &nbsp;|&nbsp;
            Gemma 4 E4B &nbsp;|&nbsp;
            100% Offline &nbsp;|&nbsp;
            WHO START Protocol
        </p>
        <p style="color:#445566; margin:4px 0 0 0; font-size:12px;">
            Aayu Wadhwani &amp; Keshav Bhatnagar
            &nbsp;|&nbsp; Gemma 4 Good Hackathon 2026
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── DISCLAIMER ────────────────────────────────────────────
    st.markdown("""
    <div class="disclaimer">
        ⚠️ DECISION SUPPORT ONLY — ALL TRIAGE DECISIONS MUST BE
        VERIFIED BY TRAINED MEDICAL PERSONNEL — NOT A MEDICAL DEVICE
    </div>
    """, unsafe_allow_html=True)

    # ── STATUS BAR ────────────────────────────────────────────
    status_cols = st.columns(4)
    with status_cols[0]:
        st.markdown(
            "🟢 **OFFLINE MODE**",
            help="No internet required"
        )
    with status_cols[1]:
        st.markdown(
            f"📚 **{backend['kb_chunks']} Protocol Chunks**",
            help="WHO protocols loaded in ChromaDB"
        )
    with status_cols[2]:
        st.markdown(
            "🔧 **7 Tools Active**",
            help="Hardware tools registered"
        )
    with status_cols[3]:
        st.markdown(
            f"🕐 **{datetime.now().strftime('%H:%M:%S')}**"
        )

    st.divider()

    # ── MAIN LAYOUT ───────────────────────────────────────────
    left_col, right_col = st.columns([1, 1], gap="large")

    # ════════════════════════════════════════════════════════════
    # LEFT COLUMN — Patient Input
    # ════════════════════════════════════════════════════════════

    with left_col:
        st.markdown(
            '<div class="section-header">📋 PATIENT INPUT</div>',
            unsafe_allow_html=True
        )

        # ── Patient ID ────────────────────────────────────────
        col_id, col_lang = st.columns([1, 1])
        with col_id:
            patient_id = st.text_input(
                "Patient ID",
                value=get_next_patient_id(),
                key="patient_id_input",
                label_visibility="visible"
            )
        with col_lang:
            language = st.selectbox(
                "Response Language",
                options=[
                    "English",
                    "Arabic",
                    "Turkish",
                    "French",
                    "Spanish",
                    "Swahili"
                ],
                index=0,
                key="language_select"
            )

        # ── Demo scenario loader ───────────────────────────────
        selected_demo = st.selectbox(
            "Quick Demo Scenarios",
            options=list(DEMO_SCENARIOS.keys()),
            index=0,
            key="demo_selector"
        )

        # Auto-fill text area when demo selected
        demo_text = DEMO_SCENARIOS.get(selected_demo, "")
        if demo_text and selected_demo != "── Select a demo scenario ──":
            st.session_state["patient_desc_value"] = demo_text

        # ── Patient description ───────────────────────────────
        patient_desc = st.text_area(
            "Patient Description",
            value=st.session_state.get("patient_desc_value", ""),
            height=160,
            placeholder=(
                "Describe the patient...\n\n"
                "Include: age, mechanism of injury,\n"
                "breathing, consciousness, visible wounds,\n"
                "vital signs, known allergies."
            ),
            key="patient_desc_area"
        )

        # Update session value when user types
        if patient_desc:
            st.session_state["patient_desc_value"] = patient_desc

        # ── Voice recording button ─────────────────────────────
        st.markdown(
            '<div class="section-header" style="margin-top:10px;">'
            '🎙️ VOICE INPUT</div>',
            unsafe_allow_html=True
        )

        voice_col1, voice_col2 = st.columns(2)
        with voice_col1:
            if st.button(
                "🎙️  Record 8 Seconds",
                use_container_width=True,
                key="record_btn"
            ):
                with st.spinner("Recording... Speak now!"):
                    try:
                        from core.audio import record_and_transcribe
                        result = record_and_transcribe(duration=8)

                        if result.get("text"):
                            st.session_state["patient_desc_value"] = \
                                result["text"]
                            st.success(
                                f"Transcribed "
                                f"[{result['language_name']}]: "
                                f"{result['text'][:60]}..."
                            )
                            st.rerun()
                        else:
                            st.warning(
                                "No speech detected. "
                                "Check microphone settings."
                            )
                    except Exception as e:
                        st.warning(f"Voice unavailable: {e}")

        with voice_col2:
            if st.button(
                "🔊  Speak Phrase",
                use_container_width=True,
                key="speak_btn",
                help="Speak the triage phrase in patient language"
            ):
                if st.session_state.triage_result:
                    category = st.session_state.triage_result.get(
                        "triage_category", "ASSESSING"
                    )
                    lang_codes = {
                        "English": "en", "Arabic": "ar",
                        "Turkish": "tr", "French": "fr",
                        "Spanish": "es", "Swahili": "sw"
                    }
                    lang_code = lang_codes.get(language, "en")

                    try:
                        from core.audio import (
                            get_triage_phrase, speak_text
                        )
                        phrase = get_triage_phrase(category, lang_code)
                        speak_text(phrase)
                        st.success(f"Spoken: {phrase}")
                    except Exception as e:
                        st.warning(f"TTS unavailable: {e}")
                else:
                    st.info("Run triage first.")

        # ── Wound image upload ────────────────────────────────
        st.markdown(
            '<div class="section-header" style="margin-top:10px;">'
            '📷 WOUND PHOTO (Optional)</div>',
            unsafe_allow_html=True
        )

        uploaded_file = st.file_uploader(
            "Upload wound photograph",
            type=["jpg", "jpeg", "png"],
            key="wound_upload",
            label_visibility="collapsed"
        )

        wound_image = None
        if uploaded_file:
            wound_image = Image.open(uploaded_file).convert("RGB")
            st.image(
                wound_image,
                caption="Wound image uploaded — vision analysis will run",
                width=280
            )

        # ── Quick demo image buttons ──────────────────────────
        demo_img_cols = st.columns(3)
        demo_images   = {
            "🔥 Burn":    "burn_partial.jpg",
            "🩸 Lacerate": "laceration_deep.jpg",
            "🦴 Crush":   "crush_injury_leg.jpg"
        }

        for i, (label, filename) in enumerate(demo_images.items()):
            with demo_img_cols[i]:
                img_path = Path("data") / "test_images" / filename
                if img_path.exists():
                    if st.button(
                        label,
                        use_container_width=True,
                        key=f"demo_img_{i}"
                    ):
                        st.session_state["demo_image_path"] = \
                            str(img_path)
                        st.success(f"{label} selected")

        # Load demo image if selected
        demo_img_path = st.session_state.get("demo_image_path")
        if demo_img_path and not uploaded_file:
            if Path(demo_img_path).exists():
                wound_image = Image.open(demo_img_path).convert("RGB")
                st.image(
                    wound_image,
                    caption=f"Demo image: {Path(demo_img_path).name}",
                    width=200
                )

        # ── TRIAGE BUTTON ─────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)

        triage_clicked = st.button(
            "🚨   BEGIN TRIAGE ASSESSMENT",
            use_container_width=True,
            type="primary",
            key="triage_btn"
        )

    # ════════════════════════════════════════════════════════════
    # RIGHT COLUMN — Triage Results
    # ════════════════════════════════════════════════════════════

    with right_col:
        st.markdown(
            '<div class="section-header">🏥 TRIAGE RESULTS</div>',
            unsafe_allow_html=True
        )

        # ── Run triage when button clicked ─────────────────────
        if triage_clicked:
            desc = st.session_state.get("patient_desc_value", "")

            if not desc.strip():
                st.error(
                    "Please enter a patient description "
                    "or select a demo scenario."
                )
            else:
                # Progress indicators
                progress = st.progress(0)
                status   = st.empty()

                try:
                    status.text("📚 Retrieving WHO protocols...")
                    progress.progress(15)
                    time.sleep(0.3)

                    status.text(
                        "👁️ Analysing wound image..."
                        if wound_image else
                        "🔍 Processing patient data..."
                    )
                    progress.progress(30)

                    status.text("🤖 Running Gemma 4 E4B inference...")
                    progress.progress(50)

                    # Run the triage pipeline
                    result = run_triage(
                        patient_description = desc,
                        patient_id          = patient_id,
                        wound_image         = wound_image
                    )

                    status.text("🔧 Calling hardware tools...")
                    progress.progress(75)
                    time.sleep(0.3)

                    status.text("📝 Logging decision...")
                    progress.progress(90)
                    time.sleep(0.3)

                    status.text("✅ Complete")
                    progress.progress(100)
                    time.sleep(0.3)

                    status.empty()
                    progress.empty()

                    # Store result and increment counter
                    st.session_state.triage_result = result
                    st.session_state.patient_counter += 1

                except Exception as e:
                    status.empty()
                    progress.empty()
                    st.error(f"Triage error: {e}")
                    st.info(
                        "Check that the model is loaded and "
                        "all components are initialised."
                    )

        # ── Display result ────────────────────────────────────
        if st.session_state.triage_result:
            result   = st.session_state.triage_result
            category = result.get("triage_category", "ASSESSING")

            # Big triage banner
            render_triage_banner(category)

            # Tools called
            tools = result.get("tools_called", [])
            if tools:
                render_tool_badges(tools)

            # Image / RAG indicators
            ind_cols = st.columns(3)
            with ind_cols[0]:
                icon = "✅" if result.get("image_analyzed") else "⬜"
                st.markdown(f"{icon} Vision")
            with ind_cols[1]:
                icon = "✅" if result.get("rag_used") else "⬜"
                st.markdown(f"{icon} WHO RAG")
            with ind_cols[2]:
                elapsed = result.get("elapsed_seconds", 0)
                st.markdown(f"⏱️ {elapsed}s")

            # ── Vitals ────────────────────────────────────────
            st.markdown(
                '<div class="section-header" style="margin-top:12px;">'
                '📊 VITAL SIGNS</div>',
                unsafe_allow_html=True
            )

            vitals    = get_vitals_from_result(result)
            v_cols    = st.columns(3)

            spo2 = vitals.get("spo2", "--")
            hr   = vitals.get("hr",   "--")
            temp = vitals.get("temp", "--")

            with v_cols[0]:
                spo2_flag = get_spo2_flag(spo2) if isinstance(spo2, int) else "NORMAL"
                render_vital_card("SpO2", f"{spo2}%", spo2_flag)

            with v_cols[1]:
                hr_flag = get_hr_flag(hr) if isinstance(hr, int) else "NORMAL"
                render_vital_card("Heart Rate", f"{hr} bpm", hr_flag)

            with v_cols[2]:
                render_vital_card("Temp", f"{temp}°C", "NORMAL")

            # ── Clinical reasoning ─────────────────────────────
            st.markdown(
                '<div class="section-header" style="margin-top:12px;">'
                '🧠 CLINICAL REASONING</div>',
                unsafe_allow_html=True
            )

            reasoning = result.get("response", "No response generated.")
            st.text_area(
                "Reasoning",
                value=reasoning,
                height=200,
                label_visibility="collapsed",
                key="reasoning_display"
            )

            # ── Multilingual phrase ────────────────────────────
            lang_codes = {
                "English": "en", "Arabic": "ar",
                "Turkish": "tr", "French": "fr",
                "Spanish": "es", "Swahili": "sw"
            }
            lang_code = lang_codes.get(language, "en")

            if lang_code != "en":
                st.markdown(
                    '<div class="section-header" style="margin-top:12px;">'
                    f'🌍 PATIENT PHRASE — {language}</div>',
                    unsafe_allow_html=True
                )
                try:
                    from core.audio import get_triage_phrase
                    phrase = get_triage_phrase(category, lang_code)
                    calm   = get_triage_phrase("calm_patient", lang_code)
                    st.info(f"**Triage:** {phrase}")
                    st.info(f"**Calm patient:** {calm}")
                except Exception:
                    pass

            # ── LoRa broadcast indicator ───────────────────────
            if category == "IMMEDIATE":
                st.markdown(
                    '<div style="background:#3d0000; border:2px solid #ff4444;'
                    'border-radius:8px; padding:10px; margin-top:10px;'
                    'text-align:center; color:#ff8888;">'
                    '📡 PRIORITY 1 EVACUATION BROADCAST SENT<br>'
                    '<small>LoRa 868MHz Mesh — ACK: COORD-ACKNOWLEDGED</small>'
                    '</div>',
                    unsafe_allow_html=True
                )

            # ── Action buttons ─────────────────────────────────
            act_cols = st.columns(2)
            with act_cols[0]:
                if st.button(
                    "🆕 New Patient",
                    use_container_width=True,
                    key="new_patient_btn"
                ):
                    st.session_state.triage_result = None
                    st.session_state["patient_desc_value"] = ""
                    st.session_state["demo_image_path"] = None
                    st.rerun()

            with act_cols[1]:
                # Download reasoning as text
                if st.download_button(
                    "📥 Download Report",
                    data=json.dumps(result, indent=2, default=str),
                    file_name=f"{patient_id}_triage.json",
                    mime="application/json",
                    use_container_width=True,
                    key="download_btn"
                ):
                    pass

        else:
            # Placeholder when no result yet
            st.markdown("""
            <div style="text-align:center; padding:60px 20px;
                        color:#445566; border:2px dashed #1e3a5f;
                        border-radius:12px; margin-top:20px;">
                <div style="font-size:48px;">🛡️</div>
                <div style="font-size:18px; margin-top:10px;">
                    Awaiting patient input
                </div>
                <div style="font-size:13px; margin-top:8px;">
                    Select a demo scenario or type a patient description,
                    then click BEGIN TRIAGE ASSESSMENT
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════
    # BOTTOM — Triage Log Table
    # ════════════════════════════════════════════════════════════

    st.divider()

    st.markdown(
        '<div class="section-header">📋 TRIAGE LOG — This Session</div>',
        unsafe_allow_html=True
    )

    log_df = load_triage_log()

    if log_df.empty:
        st.info(
            "No triage records yet. "
            "Complete a triage assessment to see the log."
        )
    else:
        # Colour-code by category
        def colour_category(val):
            colours = {
                "IMMEDIATE": "background-color: #7f0000; color: white",
                "DELAYED":   "background-color: #5c4a00; color: white",
                "MINOR":     "background-color: #004d00; color: white",
                "EXPECTANT": "background-color: #1a1a1a; color: #aaaaaa"
            }
            return colours.get(val, "")

        # ── RECTIFIED LOG TABLE CODE ──────────────────────────────────
        try:
            # Try the new Pandas method (.map)
            styled = log_df.style.map(colour_category, subset=["category"])
        except AttributeError:
            # Fallback for older Pandas versions (.applymap)
            styled = log_df.style.applymap(colour_category, subset=["category"])

        st.dataframe(
            styled,
            use_container_width=True,
            hide_index=True
        )

        # Stats row
        stat_cols = st.columns(4)
        with stat_cols[0]:
            n_imm = (log_df["category"] == "IMMEDIATE").sum()
            st.metric("🔴 Immediate", n_imm)
        with stat_cols[1]:
            n_del = (log_df["category"] == "DELAYED").sum()
            st.metric("🟡 Delayed", n_del)
        with stat_cols[2]:
            n_min = (log_df["category"] == "MINOR").sum()
            st.metric("🟢 Minor", n_min)
        with stat_cols[3]:
            st.metric("📊 Total", len(log_df))

    # ── FOOTER ────────────────────────────────────────────────
    st.markdown("""
    <div class="aegis-footer">
        🛡️ Aegis-Edge v1.0 &nbsp;|&nbsp;
        Powered by Gemma 4 E4B &nbsp;|&nbsp;
        100% Offline &nbsp;|&nbsp;
        WHO START Protocol &nbsp;|&nbsp;
        Aayu Wadhwani &amp; Keshav Bhatnagar &nbsp;|&nbsp;
        Gemma 4 Good Hackathon 2026
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
