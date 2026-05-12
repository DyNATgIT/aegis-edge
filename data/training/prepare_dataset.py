import json
from pathlib import Path
from datasets import Dataset

# ── Training examples ─────────────────────────────────────────
# Covers all 4 categories + special cases
TRAINING_EXAMPLES = [

    # Case 1 — IMMEDIATE: all three steps fail
    # Most critical scenario — put first in training
    {
        "instruction": (
            "Patient: Adult female, 32 years old. "
            "Breathing 34 times per minute. "
            "No radial pulse palpable. "
            "Unresponsive to voice. "
            "What is the WHO START triage category?"
        ),
        "response": (
            "TRIAGE: IMMEDIATE (Red)\n\n"
            "REASONING — WHO START Protocol:\n"
            "Step 2 — Respiratory Rate: 34/min > 30 threshold → IMMEDIATE\n"
            "Step 3 — Perfusion: No radial pulse → IMMEDIATE\n"
            "Step 4 — Mental Status: Unresponsive → IMMEDIATE\n\n"
            "Three independent IMMEDIATE triggers confirmed.\n"
            "This patient needs intervention within minutes.\n\n"
            "Actions: High-flow O2, IV access, "
            "fluid resuscitation, priority 1 evacuation.\n\n"
            "⚠️ All findings must be verified by trained personnel."
        )
    },

    # Case 2 — MINOR: walking wounded test
    # Step 0 exists in START — many people forget it
    {
        "instruction": (
            "Patient: Male, 28 years old. "
            "Walking toward me on his own. "
            "Cut on left hand, bleeding controlled with his shirt. "
            "Alert, talking clearly, breathing normally."
        ),
        "response": (
            "TRIAGE: MINOR (Green)\n\n"
            "REASONING — WHO START Protocol:\n"
            "Step 0 — Walking Wounded: Patient walked to triage → MINOR\n\n"
            "Per START, any ambulatory patient is MINOR. "
            "Step 0 is applied before individual assessment begins.\n\n"
            "Actions: Direct to minor treatment area. "
            "Wound care when resources allow. "
            "Reassess in 30 minutes — MINOR can deteriorate.\n\n"
            "⚠️ All findings must be verified by trained personnel."
        )
    },

    # Case 3 — IMMEDIATE: mental status fails, vitals look fine
    # The tricky case — stable vitals but altered consciousness
    {
        "instruction": (
            "Patient: Female, 45 years old. "
            "Breathing 18 per minute. Radial pulse present. "
            "Capillary refill 1.5 seconds. "
            "Cannot follow commands — does not squeeze my hand. "
            "Suspected closed femur fracture."
        ),
        "response": (
            "TRIAGE: IMMEDIATE (Red)\n\n"
            "REASONING — WHO START Protocol:\n"
            "Step 2 — RR: 18/min (10-30 range) → PASS\n"
            "Step 3 — Perfusion: Radial pulse present, CRT 1.5s → PASS\n"
            "Step 4 — Mental Status: Cannot follow commands → FAIL → IMMEDIATE\n\n"
            "Key insight: Even with stable vitals, altered mental status "
            "alone triggers IMMEDIATE. "
            "A femur fracture can hide 1-2L internal blood loss — "
            "this patient may be in compensated shock.\n\n"
            "Actions: Traction splint, IV access, "
            "neuro assessment, prepare for evacuation.\n\n"
            "⚠️ All findings must be verified by trained personnel."
        )
    },

    # Case 4 — Burns + inhalation injury
    # The scenario our entire demo is built around
    {
        "instruction": (
            "Patient: Male, 38 years old. Burns on chest and arms. "
            "Estimated 22 percent TBSA partial thickness. "
            "Facial burns present. Voice is hoarse. "
            "Breathing 26 per minute. SpO2 reads 91 percent."
        ),
        "response": (
            "TRIAGE: IMMEDIATE (Red) — AIRWAY EMERGENCY\n\n"
            "REASONING:\n"
            "1. INHALATION INJURY SUSPECTED:\n"
            "   Facial burns + hoarse voice = presumed inhalation injury.\n"
            "   Airway edema can close the airway within 30-60 minutes.\n\n"
            "2. BURN SEVERITY:\n"
            "   22% TBSA > 20% adult IMMEDIATE threshold (WHO burns).\n"
            "   Parkland formula: 4 x weight(kg) x 22 = 24h fluid need.\n\n"
            "3. HYPOXIA:\n"
            "   SpO2 91% borderline. CO poisoning gives falsely normal "
            "   SpO2 — treat with 100% O2 regardless.\n\n"
            "Actions:\n"
            "1. Secure airway immediately — do not wait\n"
            "2. High-flow O2 via non-rebreather mask 15L/min\n"
            "3. Two large-bore IVs, start Parkland fluids\n"
            "4. Priority 1 evacuation to burns unit\n\n"
            "⚠️ All findings must be verified by trained personnel."
        )
    },

    # Case 5 — Pediatric case
    # Different vital sign thresholds for children
    {
        "instruction": (
            "Patient: Child, approximately 6 years old. "
            "Breathing 28 per minute. Radial pulse present. "
            "Alert, following commands, crying loudly. "
            "Laceration on forehead, bleeding controlled."
        ),
        "response": (
            "TRIAGE: DELAYED (Yellow)\n\n"
            "REASONING — Pediatric JumpSTART Protocol:\n"
            "Step 2 — RR: 28/min. "
            "PEDIATRIC NOTE: Normal RR for age 6 is 15-25/min. "
            "Mildly elevated but below 30/min IMMEDIATE threshold.\n"
            "Step 3 — Perfusion: Radial pulse present → PASS\n"
            "Step 4 — Mental Status: Following commands → PASS\n\n"
            "All steps pass → DELAYED.\n\n"
            "PEDIATRIC WARNING: Children compensate well then "
            "crash suddenly without warning. "
            "Reassess every 10-15 minutes.\n\n"
            "Actions: Wound care, reassess frequently.\n\n"
            "⚠️ All findings must be verified by trained personnel."
        )
    },

    # Case 6 — EXPECTANT
    # The hardest decision in mass casualty triage
    {
        "instruction": (
            "Patient: Male, 55 years old. "
            "Not breathing after head-tilt chin-lift repositioning. "
            "Multiple critical injuries from building collapse. "
            "40 other patients are waiting for assessment."
        ),
        "response": (
            "TRIAGE: EXPECTANT (Black)\n\n"
            "REASONING — WHO START Protocol:\n"
            "Step 1 — Breathing: Not breathing after "
            "airway repositioning → EXPECTANT.\n\n"
            "IMPORTANT: EXPECTANT does not mean this patient "
            "cannot survive under normal hospital conditions. "
            "It means: with 40 patients waiting and limited "
            "resources, diverting resources here costs other "
            "survivable patients their lives.\n\n"
            "Actions: Comfort measures only. "
            "Document time and decision. "
            "Reassess immediately if additional responders arrive.\n\n"
            "⚠️ EXPECTANT is resource-dependent. Always reassess."
        )
    },

    # Case 7 — DELAYED: clean stable case
    {
        "instruction": (
            "Patient: Female, 29 years old. "
            "Breathing 22 per minute. Strong radial pulse. "
            "Capillary refill 1.8 seconds. "
            "Closed fracture right forearm with visible deformity. "
            "Alert, following all commands. Pain 6 out of 10."
        ),
        "response": (
            "TRIAGE: DELAYED (Yellow)\n\n"
            "REASONING — WHO START Protocol:\n"
            "Step 2 — RR: 22/min (10-30) → PASS\n"
            "Step 3 — Perfusion: Pulse strong, CRT 1.8s < 2s → PASS\n"
            "Step 4 — Mental Status: Alert, following commands → PASS\n\n"
            "All START steps pass → DELAYED.\n\n"
            "Closed forearm fracture is serious but not life-threatening. "
            "Patient can safely wait 1-2 hours.\n\n"
            "Actions: Splint the fracture, elevate, "
            "analgesia if available. Reassess every 15-30 minutes.\n\n"
            "⚠️ All findings must be verified by trained personnel."
        )
    },

    # Case 8 — Clinical override: cardiac emergency in START
    # START was designed for trauma — medical emergencies need override
    {
        "instruction": (
            "Patient: Male, 60 years old. "
            "Crushing chest pain radiating to left arm. "
            "Sweating heavily, pale skin. "
            "Breathing 24 per minute. Radial pulse present but irregular. "
            "SpO2 94 percent. Following commands."
        ),
        "response": (
            "TRIAGE: IMMEDIATE (Red) — CLINICAL OVERRIDE\n\n"
            "REASONING:\n"
            "START Assessment: RR 24 PASS, Pulse present PASS, "
            "Following commands PASS → technically DELAYED.\n\n"
            "CLINICAL OVERRIDE TO IMMEDIATE:\n"
            "Crushing chest pain + left arm radiation + diaphoresis + "
            "pallor + irregular pulse = acute MI presentation. "
            "START was designed for trauma. "
            "Medical emergencies require clinical judgment override. "
            "This patient will arrest without intervention.\n\n"
            "Actions: Aspirin 300mg chewed immediately, "
            "high-flow O2, IV access, complete rest, "
            "priority cardiac evacuation.\n\n"
            "⚠️ Clinical override must be documented with rationale."
        )
    },
]


def format_for_gemma(example: dict) -> dict:
    """
    Format training example in Gemma 4 chat template format.
    Uses start_of_turn / end_of_turn tokens.
    """
    return {
        "text": (
            f"<start_of_turn>user\n"
            f"{example['instruction']}"
            f"<end_of_turn>\n"
            f"<start_of_turn>model\n"
            f"{example['response']}"
            f"<end_of_turn>"
        )
    }


def build_and_save_dataset(
    output_path: str = "data/training/aegis_triage_train.jsonl"
) -> Dataset:
    """
    Format all examples and save as JSONL.
    Returns HuggingFace Dataset object.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    formatted = [format_for_gemma(ex) for ex in TRAINING_EXAMPLES]

    # Save as JSONL
    with open(output_path, "w", encoding="utf-8") as f:
        for item in formatted:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    dataset = Dataset.from_list(formatted)

    print(f"Dataset saved: {len(formatted)} examples")
    print(f"Location: {output_path}")
    print(f"\nCategories covered:")

    categories = {}
    for ex in TRAINING_EXAMPLES:
        for cat in ["IMMEDIATE", "DELAYED", "MINOR", "EXPECTANT"]:
            if cat in ex["response"]:
                categories[cat] = categories.get(cat, 0) + 1
                break

    for cat, count in categories.items():
        print(f"  {cat}: {count} examples")

    print(f"\nSpecial cases covered:")
    print(f"  Burns + inhalation injury : yes")
    print(f"  Pediatric (JumpSTART)     : yes")
    print(f"  Cardiac override          : yes")
    print(f"  EXPECTANT decision        : yes")

    return dataset


if __name__ == "__main__":
    dataset = build_and_save_dataset()

    print(f"\nSample formatted example (first 300 chars):")
    print(dataset[0]["text"][:300] + "...")
    print()
    print("✅ Dataset ready for LoRA training")