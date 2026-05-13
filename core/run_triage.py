from core.agent import TriageSession

def triage_text(patient_description: str, patient_id: str = None, speak: bool = True) -> dict:
    session = TriageSession(patient_id=patient_id)
    return session.run(text_input=patient_description, speak_output=speak)

def triage_image(patient_description: str, image_path: str, patient_id: str = None, speak: bool = True) -> dict:
    session = TriageSession(patient_id=patient_id)
    return session.run(text_input=patient_description, image_path=image_path, speak_output=speak)

def triage_voice(patient_id: str = None, duration: int = 8, speak: bool = True) -> dict:
    session = TriageSession(patient_id=patient_id)
    return session.run(use_voice=True, voice_duration=duration, speak_output=speak)
