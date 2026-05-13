import json
from pathlib import Path
from datasets import Dataset

# Training examples: Teaching the model to think in START steps
TRAINING_EXAMPLES = [
    {
        "instruction": "Patient: Adult female, 32 years old. Breathing 34 times per minute. No radial pulse palpable. Unresponsive to voice. What is the WHO START triage category?",
        "response": "TRIAGE: IMMEDIATE (Red)\n\nREASONING — WHO START Protocol:\nStep 2 — Respiratory Rate: 34/min > 30 threshold → IMMEDIATE\nStep 3 — Perfusion: No radial pulse → IMMEDIATE\nStep 4 — Mental Status: Unresponsive → IMMEDIATE\n\nActions: High-flow O2, IV access, fluid resuscitation, priority 1 evacuation.\n\n⚠️ All findings must be verified by trained personnel."
    },
    {
        "instruction": "Patient: Male, 28 years old. Walking toward me on his own. Cut on left hand, bleeding controlled. Alert, talking clearly, breathing normally.",
        "response": "TRIAGE: MINOR (Green)\n\nREASONING — WHO START Protocol:\nStep 0 — Walking Wounded: Patient walked to triage → MINOR\n\nActions: Direct to minor treatment area. Wound care when resources allow.\n\n⚠️ All findings must be verified by trained personnel."
    },
    {
        "instruction": "Patient: Female, 45 years old. Breathing 18 per minute. Radial pulse present. Cannot follow commands — does not squeeze my hand.",
        "response": "TRIAGE: IMMEDIATE (Red)\n\nREASONING — WHO START Protocol:\nStep 2 — RR: 18/min → PASS\nStep 3 — Perfusion: Radial pulse present → PASS\nStep 4 — Mental Status: Cannot follow commands → FAIL → IMMEDIATE\n\nActions: Neuro assessment, prepare for evacuation.\n\n⚠️ All findings must be verified by trained personnel."
    },
    {
        "instruction": "Patient: Male, 38 years old. Burns on chest and arms. 22% TBSA partial thickness. Facial burns present. Voice is hoarse. SpO2 91%.",
        "response": "TRIAGE: IMMEDIATE (Red) — AIRWAY EMERGENCY\n\nREASONING:\n1. INHALATION INJURY: Facial burns + hoarse voice = presumed inhalation injury.\n2. BURN SEVERITY: 22% TBSA > 20% adult threshold → IMMEDIATE.\n\nActions: Secure airway, high-flow O2, Parkland fluids.\n\n⚠️ All findings must be verified by trained personnel."
    },
    {
        "instruction": "Patient: Child, 6 years old. Breathing 28 per minute. Radial pulse present. Alert, following commands. Laceration on forehead.",
        "response": "TRIAGE: DELAYED (Yellow)\n\nREASONING — Pediatric JumpSTART Protocol:\nStep 2 — RR: 28/min (Normal for age 6 is 15-25, but < 30 threshold) → PASS\nStep 3 — Perfusion: Radial pulse present → PASS\nStep 4 — Mental Status: Following commands → PASS\n\nActions: Wound care, reassess frequently.\n\n⚠️ All findings must be verified by trained personnel."
    },
    {
        "instruction": "Patient: Male, 55 years old. Not breathing after head-tilt chin-lift repositioning. 40 other patients waiting.",
        "response": "TRIAGE: EXPECTANT (Black)\n\nREASONING — WHO START Protocol:\nStep 1 — Breathing: Not breathing after airway repositioning → EXPECTANT.\n\nActions: Comfort measures only. Document decision.\n\n⚠️ EXPECTANT is resource-dependent. Always reassess."
    },
    {
        "instruction": "Patient: Female, 29 years old. Breathing 22 per minute. Strong radial pulse. Closed fracture right forearm. Alert, following commands.",
        "response": "TRIAGE: DELAYED (Yellow)\n\nREASONING — WHO START Protocol:\nStep 2 — RR: 22/min → PASS\nStep 3 — Perfusion: Pulse strong → PASS\nStep 4 — Mental Status: Alert → PASS\n\nActions: Splint fracture, analgesia if available.\n\n⚠️ All findings must be verified by trained personnel."
    },
    {
        "instruction": "Patient: Male, 60 years old. Crushing chest pain. Sweating, pale skin. Breathing 24 per minute. Radial pulse irregular.",
        "response": "TRIAGE: IMMEDIATE (Red) — CLINICAL OVERRIDE\n\nREASONING:\nSTART Assessment: RR 24, Pulse present, Following commands → Technically DELAYED.\nCLINICAL OVERRIDE: Acute MI presentation (chest pain + pallor) → IMMEDIATE.\n\nActions: Aspirin 300mg, high-flow O2, priority cardiac evacuation.\n\n⚠️ Clinical override must be documented."
    }
]

def format_for_gemma(example):
    return {"text": f"<start_of_turn>user\n{example['instruction']}<end_of_turn>\n<start_of_turn>model\n{example['response']}<end_of_turn>"}

def build_and_save_dataset(output_path="data/training/aegis_triage_train.jsonl"):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    formatted = [format_for_gemma(ex) for ex in TRAINING_EXAMPLES]
    with open(output_path, "w", encoding="utf-8") as f:
        for item in formatted:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return Dataset.from_list(formatted)

if __name__ == "__main__":
    build_and_save_dataset()
    print("✅ Dataset ready for LoRA training.")
