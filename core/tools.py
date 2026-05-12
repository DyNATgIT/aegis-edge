TOOL_SCHEMA = [

    # ── TOOL 1: Pulse Oximeter ──────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "read_pulse_oximeter",
            "description": (
                "Read real-time SpO2 oxygen saturation percentage and heart rate "
                "from the BLE-connected pulse oximeter clipped to the patient's finger. "
                "Call this for ANY patient where breathing, circulation, or shock is "
                "a concern. SpO2 below 90% requires IMMEDIATE triage. "
                "SpO2 below 85% is critical. Normal range: 95-100%."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": (
                            "Unique patient identifier assigned at intake. "
                            "Format: P-XXXX (e.g. P-0042)"
                        )
                    }
                },
                "required": ["patient_id"]
            }
        }
    },

    # ── TOOL 2: Thermometer ─────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "read_thermometer",
            "description": (
                "Read body temperature from the BLE infrared non-contact thermometer. "
                "Temperature above 39.5°C suggests infection or sepsis. "
                "Temperature below 35°C indicates hypothermia — flag as IMMEDIATE. "
                "Call this for patients showing signs of infection, sepsis, "
                "or environmental exposure (flood, cold, fire)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "Unique patient identifier e.g. P-0042"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit. Default is celsius."
                    }
                },
                "required": ["patient_id"]
            }
        }
    },

    # ── TOOL 3: Camera ──────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "capture_wound_image",
            "description": (
                "Trigger the device camera to photograph a wound for AI visual analysis. "
                "Use this for burns, lacerations, crush injuries, skin discolouration, "
                "or any visible wound where depth, size, or severity is unclear. "
                "Returns the image path for multimodal analysis. "
                "Always use flash in low-light disaster conditions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "body_region": {
                        "type": "string",
                        "description": (
                            "Body area to photograph. Be specific. "
                            "Examples: 'left forearm', 'chest anterior', "
                            "'face and neck', 'right lower leg'"
                        )
                    },
                    "flash": {
                        "type": "boolean",
                        "description": "Enable camera flash. Default: true. "
                                       "Set false only in bright outdoor daylight."
                    }
                },
                "required": ["body_region"]
            }
        }
    },

    # ── TOOL 4: Triage Logger ───────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "log_triage_decision",
            "description": (
                "Log the final triage category and clinical rationale to the "
                "encrypted local SQLite database. ALWAYS call this after reaching "
                "a triage decision — every patient must be logged for post-event "
                "medical review and legal documentation. "
                "This is mandatory for every patient encounter."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "Unique patient identifier"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["IMMEDIATE", "DELAYED", "MINOR", "EXPECTANT"],
                        "description": (
                            "WHO START triage category. "
                            "IMMEDIATE=life-threatening act now, "
                            "DELAYED=serious but stable, "
                            "MINOR=walking wounded, "
                            "EXPECTANT=unsurvivable given resources"
                        )
                    },
                    "rationale": {
                        "type": "string",
                        "description": (
                            "Clinical reasoning for this triage decision. "
                            "Include all vital signs used and which START "
                            "protocol steps were applied."
                        )
                    },
                    "vitals": {
                        "type": "object",
                        "description": (
                            "Recorded vital signs as key-value pairs. "
                            "Include any of: spo2, heart_rate, temperature, "
                            "respiratory_rate, blood_pressure."
                        )
                    },
                    "confidence": {
                        "type": "number",
                        "description": (
                            "Your confidence in this triage decision from 0.0 to 1.0. "
                            "Be honest — low confidence should trigger human review."
                        )
                    }
                },
                "required": ["patient_id", "category", "rationale"]
            }
        }
    },

    # ── TOOL 5: LoRa Radio Broadcast ────────────────────────
    {
        "type": "function",
        "function": {
            "name": "broadcast_evacuation_request",
            "description": (
                "Transmit a priority evacuation request over the LoRa 868MHz mesh "
                "radio network to the field coordinator and nearest medical facility. "
                "Use ONLY for IMMEDIATE (priority 1) and DELAYED (priority 2) patients. "
                "Do NOT broadcast for MINOR patients — it wastes evacuation resources. "
                "The message is transmitted offline with no internet needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "Unique patient identifier"
                    },
                    "priority": {
                        "type": "integer",
                        "enum": [1, 2, 3],
                        "description": (
                            "Evacuation priority. "
                            "1=IMMEDIATE life threat act now, "
                            "2=DELAYED serious but stable, "
                            "3=MINOR routine transport"
                        )
                    },
                    "gps_coordinates": {
                        "type": "string",
                        "description": (
                            "Patient location as decimal lat,long. "
                            "Example: '37.5665,36.9261'. "
                            "Call get_gps_location() first if unsure."
                        )
                    },
                    "condition_summary": {
                        "type": "string",
                        "description": (
                            "Brief clinical summary for receiving medical team. "
                            "Include: mechanism, injuries, vitals, interventions done. "
                            "Maximum 200 characters — this goes over radio."
                        )
                    }
                },
                "required": ["patient_id", "priority", "condition_summary"]
            }
        }
    },

    # ── TOOL 6: Drug Interaction Checker ────────────────────
    {
        "type": "function",
        "function": {
            "name": "query_drug_interactions",
            "description": (
                "Query the local offline drug interaction database before recommending "
                "or administering any medication. ALWAYS call this before suggesting "
                "any drug administration. Returns safe dosage, contraindications, "
                "and known interactions. Works completely offline — no internet needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "drug_name": {
                        "type": "string",
                        "description": (
                            "Generic name of the medication to check. "
                            "Examples: morphine, aspirin, epinephrine, "
                            "ketamine, tranexamic acid, naloxone"
                        )
                    },
                    "patient_allergies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "List of known patient allergies. "
                            "Example: ['penicillin', 'sulfa', 'nsaids']"
                        )
                    },
                    "concurrent_medications": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Medications the patient is already taking or "
                            "has already received. Used for interaction checking."
                        )
                    }
                },
                "required": ["drug_name"]
            }
        }
    },

    # ── TOOL 7: GPS Location ────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_gps_location",
            "description": (
                "Get the current GPS coordinates of this device. "
                "Call this before broadcasting evacuation requests so the "
                "rescue team knows exactly where the patient is located. "
                "Returns latitude, longitude, accuracy, and altitude."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }

]

# ═══════════════════════════════════════════════════════════════
# TOOL NAMES — Quick reference list
# ═══════════════════════════════════════════════════════════════

TOOL_NAMES = [t["function"]["name"] for t in TOOL_SCHEMA]

# ═══════════════════════════════════════════════════════════════
# QUICK INSPECTION — Run this file directly to see the schema
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()

    # Print summary table
    table = Table(
        title="AEGIS-EDGE — Registered Tools",
        box=box.ROUNDED,
        border_style="cyan"
    )
    table.add_column("No.", style="dim", width=4)
    table.add_column("Tool Name",            style="green",  width=32)
    table.add_column("Required Args",        style="yellow", width=20)
    table.add_column("Description (short)",  style="white",  width=40)

    for i, tool in enumerate(TOOL_SCHEMA, 1):
        fn   = tool["function"]
        name = fn["name"]
        desc = fn["description"][:60] + "..."
        req  = ", ".join(fn["parameters"].get("required", []))
        table.add_row(str(i), name, req or "none", desc)

    console.print(table)
    console.print(f"\n[green]Total tools registered: {len(TOOL_SCHEMA)}[/green]")
    console.print("[dim]All tools are available to Gemma 4 E4B via native function calling.[/dim]")