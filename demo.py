import sys
import argparse
sys.path.insert(0, ".")
from hardware.ble_simulator import init_database
from core.rag import build_knowledge_base
from core.run_triage import triage_text, triage_image, triage_voice

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", action="store_true")
    parser.add_argument("--image", action="store_true")
    args = parser.parse_args()

    init_database()
    build_knowledge_base()

    if args.voice:
        triage_voice(patient_id="DEMO-VOICE")
    elif args.image:
        triage_image("Patient has severe burns on forearm.", "data/test_images/burn_partial.jpg", patient_id="DEMO-IMG")
    else:
        triage_text("Adult male, 38yo. House fire. Facial burns, hoarse voice. Breathing 30/min.", patient_id="DEMO-TEXT")

if __name__ == "__main__":
    main()
