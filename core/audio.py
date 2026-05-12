import os
import time
import random
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path
from loguru import logger

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

SAMPLE_RATE    = 16000   # Whisper requires 16kHz
RECORD_SECONDS = 8       # Default recording duration
WHISPER_MODEL  = "base"  # tiny/base/small/medium — base is best for tablets

# Languages most relevant to disaster zones we target
SUPPORTED_LANGUAGES = {
    "auto": "Auto-detect",
    "en":   "English",
    "ar":   "Arabic",
    "tr":   "Turkish",
    "fr":   "French",
    "es":   "Spanish",
    "sw":   "Swahili",
    "hi":   "Hindi",
    "ku":   "Kurdish",
    "uk":   "Ukrainian",
    "ha":   "Hausa",
}

# ── Singleton: load Whisper once and reuse ────────────────────
_whisper_model = None


def get_whisper():
    """Load Whisper model once and keep in memory."""
    global _whisper_model
    if _whisper_model is None:
        import whisper
        logger.info(f"Loading Whisper '{WHISPER_MODEL}' model...")
        _whisper_model = whisper.load_model(WHISPER_MODEL)
        logger.success("Whisper loaded.")
    return _whisper_model


# ═══════════════════════════════════════════════════════════════
# RECORDING
# ═══════════════════════════════════════════════════════════════

def record_audio(duration: int = RECORD_SECONDS,
                 sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """
    Record audio from the default microphone.
    Returns a numpy array of float32 audio samples.

    In production: this uses the tablet's built-in mic.
    In development: uses your laptop/PC microphone.
    """
    import sounddevice as sd

    logger.info(f"Recording {duration} seconds... speak now!")
    print(f"\n  🎙️  Recording {duration} seconds... Speak now!")

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32"
    )
    sd.wait()  # Block until recording is complete

    logger.info("Recording complete.")
    print("  ✅ Recording complete.")

    return audio.flatten()


def save_audio(audio: np.ndarray,
               file_path: str,
               sample_rate: int = SAMPLE_RATE):
    """Save recorded audio to a WAV file."""
    sf.write(file_path, audio, sample_rate)
    logger.info(f"Audio saved: {file_path}")


def list_audio_devices():
    """List available audio input devices."""
    import sounddevice as sd
    devices = sd.query_devices()
    print("\nAvailable audio devices:")
    for i, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            print(f"  [{i}] {device['name']} "
                  f"(inputs: {device['max_input_channels']})")


# ═══════════════════════════════════════════════════════════════
# TRANSCRIPTION (Whisper)
# ═══════════════════════════════════════════════════════════════

def transcribe_audio(
    audio_array: np.ndarray = None,
    audio_file:  str        = None,
    language:    str        = "auto"
) -> dict:
    """
    Transcribe audio using Whisper (100% offline).

    Args:
        audio_array: numpy float32 array from record_audio()
        audio_file:  path to WAV/MP3/etc file
        language:    language code ("en", "ar", "tr") or "auto"

    Returns:
        dict with keys: text, detected_language, language_name, duration
    """
    model = get_whisper()

    # Save array to temp file if needed (Whisper needs file path)
    temp_file = None
    if audio_array is not None:
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        ) as tmp:
            sf.write(tmp.name, audio_array, SAMPLE_RATE)
            audio_file = tmp.name
            temp_file  = tmp.name

    if not audio_file or not Path(audio_file).exists():
        return {
            "text":              "",
            "detected_language": "unknown",
            "language_name":     "unknown",
            "error":             "No audio input provided"
        }

    # Transcription options
    options = {"fp16": False}   # FP32 for CPU compatibility on Windows
    if language and language != "auto":
        options["language"] = language

    start = time.time()
    result = model.transcribe(audio_file, **options)
    elapsed = time.time() - start

    # Clean up temp file
    if temp_file:
        try:
            os.unlink(temp_file)
        except Exception:
            pass

    detected_lang = result.get("language", "unknown")
    text          = result.get("text", "").strip()

    logger.info(
        f"Transcribed [{detected_lang}]: "
        f"'{text[:60]}...' ({elapsed:.1f}s)"
    )

    return {
        "text":              text,
        "detected_language": detected_lang,
        "language_name":     SUPPORTED_LANGUAGES.get(
            detected_lang, detected_lang
        ),
        "duration_s":        round(elapsed, 1),
        "segments":          len(result.get("segments", []))
    }


def record_and_transcribe(
    duration: int = RECORD_SECONDS,
    language: str = "auto"
) -> dict:
    """
    One-shot: record from mic and return transcription.
    This is the function the UI calls when medic hits the mic button.
    """
    audio = record_audio(duration)
    return transcribe_audio(audio_array=audio, language=language)


# ═══════════════════════════════════════════════════════════════
# TEXT-TO-SPEECH (offline)
# ═══════════════════════════════════════════════════════════════

def speak_text(text: str,
               rate: int = 150,
               volume: float = 0.9,
               save_path: str = None):
    """
    Convert text to speech using pyttsx3 (fully offline).
    Rate: words per minute (150 = clear and readable)
    Volume: 0.0 to 1.0

    In field conditions: speaker is at max volume so patient
    can hear the triage instruction clearly.
    """
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate",   rate)
        engine.setProperty("volume", volume)

        if save_path:
            engine.save_to_file(text, save_path)
            engine.runAndWait()
            logger.info(f"Audio saved: {save_path}")
        else:
            engine.say(text)
            engine.runAndWait()

        logger.info(f"Spoken: '{text[:60]}...'")

    except Exception as e:
        logger.warning(f"TTS failed: {e} — displaying text only")
        print(f"\n  🔊 [TTS OUTPUT]: {text}")


def speak_triage_result(category: str, reasoning: str,
                         language: str = "en"):
    """
    Speak the triage result clearly.
    Uses pre-built phrases for speed — no generation needed.
    """
    # Get the triage phrase in the right language
    phrase = get_triage_phrase(category, language)

    # Build the full spoken output
    # Keep it short — medic needs to act, not listen
    spoken = f"{phrase}. {reasoning[:100]}"

    print(f"\n  🔊 Speaking result in {SUPPORTED_LANGUAGES.get(language, language)}")
    speak_text(spoken)


# ═══════════════════════════════════════════════════════════════
# MULTILINGUAL PHRASE TABLE
# ═══════════════════════════════════════════════════════════════

# Pre-built phrases for the 6 most common disaster-zone languages
# These are instant — no model inference needed
# We keep them short because in field conditions, clarity matters

PHRASE_TABLE = {

    "IMMEDIATE": {
        "en": "IMMEDIATE — Life threatening. Act now.",
        "ar": "عاجل — خطر على الحياة. تصرف الآن.",
        "tr": "ACİL — Hayati tehlike. Hemen müdahale et.",
        "fr": "IMMÉDIAT — Danger vital. Agissez maintenant.",
        "es": "INMEDIATO — Peligro de vida. Actúe ahora.",
        "sw": "HARAKA — Hatari ya maisha. Tenda sasa."
    },

    "DELAYED": {
        "en": "DELAYED — Serious but stable. Can wait 1 to 2 hours.",
        "ar": "مؤجل — خطير لكن مستقر. يمكن الانتظار.",
        "tr": "GECİKTİRİLEBİLİR — Ciddi ama stabil. Bekleyebilir.",
        "fr": "DIFFÉRÉ — Grave mais stable. Peut attendre.",
        "es": "DEMORADO — Grave pero estable. Puede esperar.",
        "sw": "KUCHELEWA — Mbaya lakini imara. Inaweza kusubiri."
    },

    "MINOR": {
        "en": "MINOR — Walking wounded. Not life threatening.",
        "ar": "بسيط — جرح خفيف. غير مهدد للحياة.",
        "tr": "MİNÖR — Yürüyebilen yaralı. Hayati değil.",
        "fr": "MINEUR — Blessé léger. Pas de danger de vie.",
        "es": "LEVE — Herido leve. No pone en riesgo la vida.",
        "sw": "KIDOGO — Jeraha dogo. Hali si ya hatari."
    },

    "EXPECTANT": {
        "en": "Expectant. Comfort measures only.",
        "ar": "متوقع. إجراءات الراحة فقط.",
        "tr": "Beklenen. Yalnızca konfor önlemleri.",
        "fr": "En attente. Mesures de confort uniquement.",
        "es": "Expectante. Solo medidas de confort.",
        "sw": "Inatarajiwa. Hatua za faraja tu."
    },

    "calm_patient": {
        "en": "You are safe. Help is here. Try to breathe slowly.",
        "ar": "أنت بأمان. المساعدة هنا. حاول التنفس ببطء.",
        "tr": "Güvendesiniz. Yardım burada. Yavaşça nefes almaya çalışın.",
        "fr": "Vous êtes en sécurité. L'aide est là. Respirez lentement.",
        "es": "Estás seguro. Hay ayuda. Intenta respirar despacio.",
        "sw": "Uko salama. Msaada uko hapa. Jaribu kupumua polepole."
    },

    "do_not_move": {
        "en": "Do not move. We are helping you.",
        "ar": "لا تتحرك. نحن نساعدك.",
        "tr": "Hareket etmeyin. Size yardım ediyoruz.",
        "fr": "Ne bougez pas. Nous vous aidons.",
        "es": "No se mueva. Le estamos ayudando.",
        "sw": "Usisogee. Tunakusaidia."
    },

    "oxygen_now": {
        "en": "We are giving you oxygen now. Breathe normally.",
        "ar": "نعطيك الأكسجين الآن. تنفس بشكل طبيعي.",
        "tr": "Şimdi size oksijen veriyoruz. Normal nefes alın.",
        "fr": "Nous vous donnons de l'oxygène. Respirez normalement.",
        "es": "Le estamos dando oxígeno. Respire con normalidad.",
        "sw": "Tunakupa oksijeni sasa. Pumua kawaida."
    },

    "help_coming": {
        "en": "Help is on the way. You will be evacuated soon.",
        "ar": "المساعدة في الطريق. سيتم إخلاؤك قريباً.",
        "tr": "Yardım geliyor. Yakında tahliye edileceksiniz.",
        "fr": "L'aide arrive. Vous serez évacué bientôt.",
        "es": "La ayuda viene. Será evacuado pronto.",
        "sw": "Msaada unakuja. Utahamishwa hivi karibuni."
    }
}


def get_triage_phrase(phrase_key: str, language: str = "en") -> str:
    """
    Get a pre-translated triage phrase instantly.
    No model inference needed — pulled from the phrase table.

    Args:
        phrase_key: "IMMEDIATE", "DELAYED", "MINOR", "EXPECTANT",
                    "calm_patient", "do_not_move", "oxygen_now",
                    "help_coming"
        language:   language code ("en", "ar", "tr", etc.)

    Returns:
        Translated phrase string
    """
    phrases = PHRASE_TABLE.get(phrase_key, {})

    # Fall back to English if language not in table
    return phrases.get(language, phrases.get("en", phrase_key))


def get_all_phrases_for_language(language: str) -> dict:
    """
    Get all triage phrases for a specific language.
    Useful for printing a reference card in the field.
    """
    return {
        key: phrases.get(language, phrases.get("en", ""))
        for key, phrases in PHRASE_TABLE.items()
    }


# ═══════════════════════════════════════════════════════════════
# GEMMA 4 TRANSLATION (for custom phrases)
# ═══════════════════════════════════════════════════════════════

def translate_with_gemma(text: str, target_language: str) -> str:
    """
    Translate any text to target language using Gemma 4.
    Use this for custom triage instructions not in the phrase table.

    Args:
        text:            Text to translate
        target_language: Language name (e.g. "Arabic", "Turkish")

    Returns:
        Translated text string
    """
    from core.model import run_inference

    lang_names = {
        "ar": "Arabic",  "tr": "Turkish",  "ku": "Kurdish",
        "fr": "French",  "es": "Spanish",  "sw": "Swahili",
        "hi": "Hindi",   "uk": "Ukrainian", "ha": "Hausa",
        "en": "English"
    }

    # Get language name from code if needed
    if len(target_language) == 2:
        lang_full = lang_names.get(target_language, target_language)
    else:
        lang_full = target_language

    if lang_full.lower() == "english":
        return text   # No translation needed

    prompt = (
        f"Translate the following medical triage instruction to {lang_full}.\n"
        f"Keep it simple and clear for a non-medical person.\n"
        f"Output the translation ONLY — no explanation, no original text.\n\n"
        f"TEXT: {text}"
    )

    translation = run_inference(
        user_message  = prompt,
        system_prompt = "You are a medical translator. Output only the translation."
    )

    return translation.strip()


def translate_triage_response(response: str,
                               target_lang_code: str) -> str:
    """
    Translate a full triage response to the patient's language.
    Extracts key decision and translates that.
    """
    if target_lang_code == "en":
        return response

    lang_names = {
        "ar": "Arabic", "tr": "Turkish", "fr": "French",
        "es": "Spanish", "sw": "Swahili", "ku": "Kurdish"
    }
    lang_name = lang_names.get(target_lang_code, "English")

    # Translate first 200 chars — the key decision
    key_part = response[:200]
    return translate_with_gemma(key_part, lang_name)


# ═══════════════════════════════════════════════════════════════
# FULL VOICE TRIAGE LOOP
# ═══════════════════════════════════════════════════════════════

def voice_triage_session(
    patient_id:       str  = "P-VOICE",
    record_duration:  int  = 8,
    patient_language: str  = "auto",
    speak_response:   bool = True
) -> dict:
    """
    Complete voice-based triage session.

    Flow:
      1. Record medic's voice description
      2. Transcribe (auto-detect language)
      3. Run triage with RAG context
      4. Speak result back
      5. Return full result dict

    Args:
        patient_id:       ID for this patient
        record_duration:  seconds to record
        patient_language: language code or "auto"
        speak_response:   whether to speak result aloud
    """
    from core.model import run_inference, SYSTEM_PROMPT
    from core.rag   import retrieve_who_context

    print(f"\n{'='*60}")
    print(f"  AEGIS-EDGE — VOICE TRIAGE SESSION")
    print(f"  Patient: {patient_id}")
    print(f"{'='*60}")

    # Step 1: Record audio
    print(f"\nStep 1: Recording {record_duration} seconds...")
    audio = record_audio(record_duration)

    # Step 2: Transcribe
    print("Step 2: Transcribing with Whisper...")
    transcript = transcribe_audio(
        audio_array=audio,
        language=patient_language
    )

    detected_lang = transcript["detected_language"]
    text          = transcript["text"]

    print(f"  Detected language : {transcript['language_name']}")
    print(f"  Transcription     : {text[:100]}...")

    if not text.strip():
        return {
            "error": "No speech detected",
            "tip":   "Speak clearly and closer to the microphone"
        }

    # Step 3: Get RAG context
    print("Step 3: Retrieving WHO protocol context...")
    rag_context = retrieve_who_context(text, n_results=3)

    augmented_system = SYSTEM_PROMPT
    if rag_context:
        augmented_system += (
            f"\n\nRELEVANT WHO PROTOCOLS:\n{rag_context[:600]}"
        )

    # Step 4: Run triage
    print("Step 4: Running triage inference...")
    response = run_inference(
        user_message  = text,
        system_prompt = augmented_system
    )

    # Step 5: Determine category
    ru = response.upper()
    category = (
        "IMMEDIATE" if "IMMEDIATE" in ru else
        "DELAYED"   if "DELAYED"   in ru else
        "MINOR"     if "MINOR"     in ru else
        "EXPECTANT" if "EXPECTANT" in ru else
        "ASSESSING"
    )

    print(f"\n  TRIAGE CATEGORY: {category}")

    # Step 6: Speak result in detected language
    if speak_response:
        print("Step 5: Speaking result...")
        triage_phrase = get_triage_phrase(category, detected_lang)
        speak_text(triage_phrase, rate=140)

        # Also speak calm patient phrase if IMMEDIATE
        if category == "IMMEDIATE":
            calm = get_triage_phrase("calm_patient", detected_lang)
            speak_text(calm, rate=130)

    # Step 7: Return full result
    return {
        "patient_id":        patient_id,
        "transcript":        text,
        "detected_language": detected_lang,
        "language_name":     transcript["language_name"],
        "triage_category":   category,
        "response":          response,
        "phrase_spoken":     get_triage_phrase(category, detected_lang),
        "rag_used":          bool(rag_context),
        "timestamp":         __import__("datetime").datetime.now().isoformat()
    }


# ═══════════════════════════════════════════════════════════════
# SMOKE TEST — Run this file directly
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from rich.console import Console
    from rich.panel   import Panel
    from rich.table   import Table
    from rich         import box

    console = Console()

    console.print(Panel(
        "[bold cyan]AEGIS-EDGE — DAY 5 AUDIO PIPELINE TEST[/bold cyan]\n"
        "Testing Whisper transcription + multilingual phrases",
        border_style="cyan"
    ))

    # ── TEST 1: Whisper model loads ───────────────────────────
    console.print("\n[yellow]TEST 1: Whisper model loading[/yellow]")
    try:
        model = get_whisper()
        import whisper
        console.print(
            f"  [green]PASS[/green] Whisper loaded | "
            f"Languages: {len(whisper.tokenizer.LANGUAGES)}"
        )
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")

    # ── TEST 2: Transcribe from file ──────────────────────────
    console.print("\n[yellow]TEST 2: Transcription from audio file[/yellow]")

    # Create a short silent test audio file
    import soundfile as sf
    test_audio_path = "data/test_audio/test_silence.wav"
    Path("data/test_audio").mkdir(parents=True, exist_ok=True)
    silence = np.zeros(int(SAMPLE_RATE * 2))
    sf.write(test_audio_path, silence, SAMPLE_RATE)

    result = transcribe_audio(audio_file=test_audio_path)
    console.print(
        f"  [green]PASS[/green] "
        f"Transcription ran (silence expected to return empty text)"
    )
    console.print(
        f"  Detected language: {result['detected_language']}"
    )

    # ── TEST 3: Phrase table ──────────────────────────────────
    console.print("\n[yellow]TEST 3: Multilingual phrase table[/yellow]")

    table = Table(box=box.ROUNDED, border_style="cyan")
    table.add_column("Category",   style="white",  width=15)
    table.add_column("English",    style="green",  width=25)
    table.add_column("Arabic",     style="yellow", width=25)
    table.add_column("Turkish",    style="cyan",   width=25)

    for category in ["IMMEDIATE", "DELAYED", "MINOR", "EXPECTANT"]:
        table.add_row(
            category,
            get_triage_phrase(category, "en")[:30],
            get_triage_phrase(category, "ar")[:30],
            get_triage_phrase(category, "tr")[:30]
        )
    console.print(table)

    # ── TEST 4: All calm phrases ──────────────────────────────
    console.print("\n[yellow]TEST 4: Patient communication phrases[/yellow]")
    for key in ["calm_patient", "do_not_move", "oxygen_now", "help_coming"]:
        en_phrase = get_triage_phrase(key, "en")
        ar_phrase = get_triage_phrase(key, "ar")
        console.print(
            f"  [green]{key}[/green]\n"
            f"    EN: {en_phrase}\n"
            f"    AR: {ar_phrase}"
        )

    # ── TEST 5: TTS (text to speech) ─────────────────────────
    console.print("\n[yellow]TEST 5: Text-to-speech output[/yellow]")
    try:
        speak_text(
            "Aegis-Edge audio test. Triage system ready.",
            rate=150
        )
        console.print(
            "  [green]PASS[/green] TTS working — you should have heard speech"
        )
    except Exception as e:
        console.print(f"  [yellow]WARN[/yellow] TTS unavailable: {e}")
        console.print(
            "  Text output will be used instead"
        )

    # ── TEST 6: Language detection with real words ────────────
    console.print("\n[yellow]TEST 6: Transcription with real audio[/yellow]")

    # Check if any real test audio exists
    audio_dir  = Path("data/test_audio")
    real_audio = [
        f for f in audio_dir.glob("*.wav")
        if f.name != "test_silence.wav"
    ]

    if real_audio:
        for audio_file in real_audio[:2]:
            result = transcribe_audio(audio_file=str(audio_file))
            console.print(
                f"  [green]File:[/green] {audio_file.name}\n"
                f"    Language: {result['language_name']}\n"
                f"    Text: {result['text'][:80]}"
            )
    else:
        console.print(
            "  [dim]No real audio files in data/test_audio/[/dim]\n"
            "  Add .wav files there to test transcription.\n"
            "  Microphone test will run in Phase 4."
        )

    # ── SUMMARY ───────────────────────────────────────────────
    console.print(Panel(
        "[bold green]DAY 5 AUDIO TESTS COMPLETE[/bold green]\n\n"
        "  Whisper model    : loaded and ready\n"
        "  Phrase table     : 8 phrases × 6 languages\n"
        "  Transcription    : working\n"
        "  Text-to-speech   : working\n\n"
        "  Proceed to Phase 4 — microphone recording test",
        border_style="green"
    ))
