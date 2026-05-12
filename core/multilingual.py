from core.audio import (
    PHRASE_TABLE,
    SUPPORTED_LANGUAGES,
    get_triage_phrase,
    get_all_phrases_for_language,
    translate_with_gemma,
    translate_triage_response
)


def print_language_reference_card(language_code: str):
    """
    Print a reference card for a specific language.
    Useful for giving medics a quick cheat sheet.
    """
    lang_name = SUPPORTED_LANGUAGES.get(language_code, language_code)
    phrases   = get_all_phrases_for_language(language_code)

    print(f"\n{'='*50}")
    print(f"  AEGIS-EDGE REFERENCE CARD — {lang_name.upper()}")
    print(f"{'='*50}")
    for key, phrase in phrases.items():
        print(f"  {key:<20} : {phrase}")
    print(f"{'='*50}\n")


def get_language_from_name(language_name: str) -> str:
    """
    Convert language name to code.
    e.g. 'Arabic' → 'ar', 'Turkish' → 'tr'
    """
    name_to_code = {v.lower(): k for k, v in SUPPORTED_LANGUAGES.items()}
    return name_to_code.get(language_name.lower(), "en")


def format_bilingual_triage(
    category: str,
    response: str,
    patient_language: str
) -> dict:
    """
    Format triage result in both English (for medic)
    and patient's language (for patient).

    Returns dict with:
      english_output  : full reasoning for medic
      patient_phrase  : short phrase for patient
      patient_language: language code used
    """
    # Get pre-built phrase for patient
    patient_phrase = get_triage_phrase(category, patient_language)

    # Get calm patient phrase
    calm_phrase = get_triage_phrase("calm_patient", patient_language)

    return {
        "english_output":  response,
        "patient_phrase":  patient_phrase,
        "calm_phrase":     calm_phrase,
        "patient_language": patient_language,
        "language_name":   SUPPORTED_LANGUAGES.get(
            patient_language, patient_language
        )
    }


if __name__ == "__main__":
    # Print reference cards for all 6 languages
    for code in ["en", "ar", "tr", "fr", "es", "sw"]:
        print_language_reference_card(code)

    print("✅ Multilingual module working")