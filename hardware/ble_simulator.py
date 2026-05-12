"""
hardware/ble_simulator.py
Aegis-Edge — Hardware Simulators + Tool Router

Every function here simulates a real piece of medical hardware.
In production, swap the body of each function with real BLE/USB calls.
The interface (function name, arguments, return format) stays identical.

Hardware mapped to each tool:
  read_pulse_oximeter       → BLE pulse oximeter (e.g. Masimo MightySat)
  read_thermometer          → BLE infrared thermometer (e.g. Braun No Touch)
  capture_wound_image       → Device rear camera (via Android Camera2 API)
  log_triage_decision       → Local SQLite database (encrypted)
  broadcast_evacuation_req  → LoRa SX1276 module via USB serial
  query_drug_interactions   → Offline SQLite drug database
  get_gps_location          → Device GPS chip (via Android Location API)
"""

import json
import random
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from loguru import logger

# ═══════════════════════════════════════════════════════════════
# DATABASE SETUP
# ═══════════════════════════════════════════════════════════════

# Windows-compatible path using pathlib (handles separators automatically)
DB_PATH = Path(".") / "data" / "triage_log.db"


def init_database():
    """
    Initialize the local SQLite triage log database.
    Creates tables if they do not exist.
    Safe to call multiple times — only creates once.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Main triage log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS triage_log (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id     TEXT    NOT NULL,
            timestamp      TEXT    NOT NULL,
            category       TEXT,
            rationale      TEXT,
            vitals         TEXT,
            confidence     REAL    DEFAULT 0.0,
            evacuated      INTEGER DEFAULT 0,
            image_analyzed INTEGER DEFAULT 0,
            session_id     TEXT
        )
    """)

    # Tool call audit log (for demo — shows all tool calls made)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_call_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id  TEXT,
            timestamp   TEXT NOT NULL,
            tool_name   TEXT NOT NULL,
            arguments   TEXT,
            result      TEXT,
            duration_ms REAL
        )
    """)

    conn.commit()
    conn.close()
    logger.info(f"Database ready: {DB_PATH.resolve()}")


def _log_tool_call(patient_id: str, tool_name: str,
                    arguments: dict, result: dict, duration_ms: float):
    """Internal: log every tool call to audit table."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tool_call_log
            (patient_id, timestamp, tool_name, arguments, result, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            datetime.now().isoformat(),
            tool_name,
            json.dumps(arguments),
            json.dumps(result),
            round(duration_ms, 2)
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Tool call logging failed: {e}")


# ═══════════════════════════════════════════════════════════════
# TOOL 1: PULSE OXIMETER
# ═══════════════════════════════════════════════════════════════

def read_pulse_oximeter(patient_id: str) -> dict:
    """
    Simulate BLE pulse oximeter reading.
    Returns SpO2 percentage and heart rate.
    """
    start = time.time()
    time.sleep(random.uniform(0.4, 0.8))

    # Weighted random: 60% chance of abnormal values in disaster context
    scenario = random.choices(
        ["critical", "serious", "stable"],
        weights=[35, 30, 35]
    )[0]

    vitals = {
        "critical": {
            "spo2_percent":    random.randint(78, 89),
            "heart_rate_bpm":  random.randint(118, 148),
            "perfusion_index": round(random.uniform(0.1, 0.8), 2),
            "signal_quality":  random.choice(["poor", "fair"])
        },
        "serious": {
            "spo2_percent":    random.randint(90, 94),
            "heart_rate_bpm":  random.randint(102, 118),
            "perfusion_index": round(random.uniform(0.8, 2.0), 2),
            "signal_quality":  "good"
        },
        "stable": {
            "spo2_percent":    random.randint(96, 100),
            "heart_rate_bpm":  random.randint(62, 98),
            "perfusion_index": round(random.uniform(2.0, 8.0), 2),
            "signal_quality":  "excellent"
        }
    }[scenario]

    spo2 = vitals["spo2_percent"]
    hr   = vitals["heart_rate_bpm"]

    if spo2 < 85:
        interpretation = "CRITICAL HYPOXIA — immediate oxygen therapy required"
        flag = "CRITICAL"
    elif spo2 < 90:
        interpretation = "Significant hypoxia — oxygen therapy required"
        flag = "IMMEDIATE"
    elif spo2 < 94:
        interpretation = "Mild hypoxia — monitor closely, consider oxygen"
        flag = "MONITOR"
    else:
        interpretation = "SpO2 within acceptable range"
        flag = "NORMAL"

    if hr > 120:
        interpretation += " | Tachycardia — consider hemorrhage or shock"
    elif hr < 50:
        interpretation += " | Bradycardia — cardiac concern"

    result = {
        "status":          "success",
        "device":          "Masimo MightySat (Simulated)",
        "patient_id":      patient_id,
        "spo2_percent":    spo2,
        "heart_rate_bpm":  hr,
        "perfusion_index": vitals["perfusion_index"],
        "signal_quality":  vitals["signal_quality"],
        "flag":            flag,
        "interpretation":  interpretation,
        "timestamp":       datetime.now().isoformat(),
        "reading_time_ms": round((time.time() - start) * 1000, 1)
    }

    logger.info(f"PULSE OX [{patient_id}] SpO2: {spo2}% | HR: {hr} bpm | Flag: {flag}")
    _log_tool_call(patient_id, "read_pulse_oximeter", {"patient_id": patient_id}, result, (time.time() - start) * 1000)
    return result


# ═══════════════════════════════════════════════════════════════
# TOOL 2: THERMOMETER
# ═══════════════════════════════════════════════════════════════

def read_thermometer(patient_id: str, unit: str = "celsius") -> dict:
    """Simulate BLE infrared thermometer reading."""
    start = time.time()
    time.sleep(random.uniform(0.2, 0.5))

    temp_c = round(random.choices(
        [random.uniform(32.0, 34.9), random.uniform(35.0, 36.4), 
         random.uniform(36.5, 37.5), random.uniform(37.6, 38.9), random.uniform(39.0, 41.5)],
        weights=[10, 15, 40, 20, 15]
    )[0], 1)

    temp_display = round(temp_c * 9 / 5 + 32, 1) if unit == "fahrenheit" else temp_c

    if temp_c < 35.0:
        flag, interpretation = "CRITICAL", f"HYPOTHERMIA ({temp_c}°C) — IMMEDIATE warming required"
    elif temp_c < 36.0:
        flag, interpretation = "LOW", f"Below normal ({temp_c}°C) — monitor for hypothermia"
    elif temp_c <= 37.5:
        flag, interpretation = "NORMAL", f"Normal temperature ({temp_c}°C)"
    elif temp_c <= 38.9:
        flag, interpretation = "FEVER", f"Low-grade fever ({temp_c}°C) — monitor for infection"
    else:
        flag, interpretation = "HIGH_FEVER", f"High fever ({temp_c}°C) — consider sepsis or heat injury"

    result = {
        "status": "success", "device": "Braun No Touch (Simulated)", "patient_id": patient_id,
        "temperature": temp_display, "temperature_c": temp_c, "unit": unit, "flag": flag,
        "interpretation": interpretation, "fever": temp_c > 37.5, "hypothermia": temp_c < 35.0,
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"THERMOMETER [{patient_id}] Temp: {temp_display}°{unit[0].upper()} | Flag: {flag}")
    _log_tool_call(patient_id, "read_thermometer", {"patient_id": patient_id, "unit": unit}, result, (time.time() - start) * 1000)
    return result


# ═══════════════════════════════════════════════════════════════
# TOOL 3: CAMERA
# ═══════════════════════════════════════════════════════

def capture_wound_image(body_region: str, flash: bool = True) -> dict:
    """Updated to use real test images from Day 4."""
    start = time.time()
    time.sleep(random.uniform(0.8, 1.5))

    image_directory = Path(".") / "data" / "test_images"
    image_directory.mkdir(parents=True, exist_ok=True)

    body_lower = body_region.lower()

    # Updated image map — now uses real generated images
    image_map = {
        "forearm":  "burn_partial.jpg",
        "arm":      "burn_partial.jpg",
        "chest":    "laceration_deep.jpg",
        "torso":    "laceration_deep.jpg",
        "face":     "burn_facial_inhalation.jpg",
        "head":     "burn_facial_inhalation.jpg",
        "neck":     "burn_facial_inhalation.jpg",
        "leg":      "crush_injury_leg.jpg",
        "thigh":    "crush_injury_leg.jpg",
        "knee":     "crush_injury_leg.jpg",
        "foot":     "crush_injury_leg.jpg",
        "hand":     "laceration_deep.jpg",
        "back":     "burn_full_thickness.jpg",
        "abdomen":  "laceration_deep.jpg",
    }

    matched_file = "burn_partial.jpg"
    for key, filename in image_map.items():
        if key in body_lower:
            img_path = image_directory / filename
            if img_path.exists():
                matched_file = filename
                break

    image_path = str(image_directory / matched_file)

    # Only create placeholder if image truly doesn't exist
    if not Path(image_path).exists():
        logger.warning(
            f"Image not found: {image_path}. "
            "Run: python scripts\\generate_test_images.py"
        )

    result = {
        "status":              "captured",
        "device":              "Samsung Galaxy Tab Active4 Pro Camera",
        "patient_body_region": body_region,
        "image_path":          image_path,
        "image_file":          matched_file,
        "flash_used":          flash,
        "resolution":          "4032x3024",
        "format":              "JPEG",
        "file_size_kb":        random.randint(120, 180),
        "timestamp":           datetime.now().isoformat()
    }

    logger.info(f"CAMERA [{body_region}] → {image_path}")
    return result

# ═══════════════════════════════════════════════════════════════
# TOOL 4: TRIAGE LOGGER
# ═══════════════════════════════════════════════════════════════

def log_triage_decision(patient_id: str, category: str, rationale: str, vitals: dict = None, confidence: float = 0.0) -> dict:
    """Log triage decision to local SQLite database."""
    start = time.time()
    valid_categories = ["IMMEDIATE", "DELAYED", "MINOR", "EXPECTANT"]
    if category not in valid_categories:
        return {"status": "error", "message": f"Invalid category '{category}'"}

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO triage_log (patient_id, timestamp, category, rationale, vitals, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (patient_id, datetime.now().isoformat(), category, rationale, json.dumps(vitals or {}), round(confidence, 3)))
    conn.commit()
    record_id = cursor.lastrowid
    cursor.execute("SELECT COUNT(*) FROM triage_log")
    total = cursor.fetchone()[0]
    conn.close()

    result = {"status": "logged", "record_id": record_id, "patient_id": patient_id, "category": category, "total_patients_logged": total, "timestamp": datetime.now().isoformat()}
    logger.info(f"TRIAGE LOG [{patient_id}] Category: {category} | Record ID: {record_id}")
    _log_tool_call(patient_id, "log_triage_decision", {"patient_id": patient_id, "category": category}, result, (time.time() - start) * 1000)
    return result


# ═══════════════════════════════════════════════════════════════
# TOOL 5: LORA RADIO BROADCAST
# ═══════════════════════════════════════════════════════════════

def broadcast_evacuation_request(patient_id: str, priority: int, condition_summary: str, gps_coordinates: str = None) -> dict:
    """Simulate LoRa mesh radio evacuation broadcast."""
    start = time.time()
    if priority not in [1, 2, 3]: return {"status": "error", "message": "Priority must be 1, 2, or 3"}
    if not gps_coordinates:
        gps_result = get_gps_location()
        gps_coordinates = gps_result.get("coordinates", "GPS_UNAVAILABLE")

    time.sleep(random.uniform(0.6, 1.2))
    ack = random.choice(["COORD-ACK: Received. ETA 12min.", "COORD-ACK: En route. ETA 8min."]) if priority == 1 else "COORD-ACK: Logged."

    result = {"status": "broadcast_sent", "channel": "LoRa 868MHz Mesh", "packet_bytes": len(condition_summary), "ack_received": ack, "timestamp": datetime.now().isoformat()}
    logger.warning(f"LORA BROADCAST [{patient_id}] Priority {priority} | ACK: {ack}")
    _log_tool_call(patient_id, "broadcast_evacuation_request", {"patient_id": patient_id, "priority": priority}, result, (time.time() - start) * 1000)
    return result


# ═══════════════════════════════════════════════════════════════
# TOOL 6: DRUG INTERACTION DATABASE
# ═══════════════════════════════════════════════════════════════

DRUG_DATABASE = {
    "morphine": {"category": "Opioid Analgesic", "contraindicated_allergies": ["opioids", "morphine"], "interactions": ["benzodiazepines"], "dosage_adult": "0.1 mg/kg IV/IM", "dosage_pediatric": "0.05-0.1 mg/kg", "contraindications": ["respiratory depression"], "notes": "Have naloxone available."},
    "aspirin": {"category": "NSAID", "contraindicated_allergies": ["nsaids", "aspirin"], "interactions": ["warfarin"], "dosage_adult": "300 mg PO", "dosage_pediatric": "AVOID", "contraindications": ["active GI bleeding"], "notes": "Chew, do not swallow."},
    "epinephrine": {"category": "Vasopressor", "contraindicated_allergies": [], "interactions": ["beta-blockers"], "dosage_adult": "0.3-0.5 mg IM", "dosage_pediatric": "0.01 mg/kg IM", "contraindications": [], "notes": "Preferred site: lateral thigh."},
    "ketamine": {"category": "Dissociative", "contraindicated_allergies": ["ketamine"], "interactions": ["benzodiazepines"], "dosage_adult": "1-2 mg/kg IV", "dosage_pediatric": "4-6 mg/kg IM", "contraindications": ["severe hypertension"], "notes": "Maintains airway reflexes."},
    "naloxone": {"category": "Opioid Antagonist", "contraindicated_allergies": ["naloxone"], "interactions": ["opioids"], "dosage_adult": "0.4-2 mg IV/IM", "dosage_pediatric": "0.01 mg/kg", "contraindications": [], "notes": "Reversal agent."},
    "tranexamic acid": {"category": "Antifibrinolytic", "contraindicated_allergies": ["tranexamic acid"], "interactions": [], "dosage_adult": "1 g IV", "dosage_pediatric": "15 mg/kg IV", "contraindications": ["> 3 hours since injury"], "notes": "Time-critical."},
    "amoxicillin": {"category": "Antibiotic", "contraindicated_allergies": ["penicillin"], "interactions": [], "dosage_adult": "500 mg PO TID", "dosage_pediatric": "25-45 mg/kg/day", "contraindications": ["penicillin allergy"], "notes": "Cross-reactivity with cephalosporins."},
    "salbutamol": {"category": "Bronchodilator", "contraindicated_allergies": ["salbutamol"], "interactions": ["beta-blockers"], "dosage_adult": "2.5 mg nebuliser", "dosage_pediatric": "2.5 mg nebulised", "contraindications": [], "notes": "Use for severe asthma."},
    "diazepam": {"category": "Benzodiazepine", "contraindicated_allergies": ["benzodiazepines"], "interactions": ["opioids"], "dosage_adult": "5-10 mg IV", "dosage_pediatric": "0.2-0.5 mg/kg PR", "contraindications": ["respiratory depression"], "notes": "Use with extreme caution."},
    "glucose": {"category": "Carbohydrate", "contraindicated_allergies": [], "interactions": ["insulin"], "dosage_adult": "50 mL of 50% dextrose", "dosage_pediatric": "2 mL/kg 10% dextrose", "contraindications": ["hyperglycaemia"], "notes": "Check blood glucose first."},
    "furosemide": {"category": "Diuretic", "contraindicated_allergies": ["sulfonamides"], "interactions": ["aminoglycosides"], "dosage_adult": "20-80 mg IV", "dosage_pediatric": "1-2 mg/kg", "contraindications": ["anuria"], "notes": "Avoid in unstable trauma."},
    "atropine": {"category": "Anticholinergic", "contraindicated_allergies": ["atropine"], "interactions": ["digoxin"], "dosage_adult": "0.5 mg IV", "dosage_pediatric": "0.02 mg/kg", "contraindications": ["tachycardia"], "notes": "Doses < 0.1 mg may cause paradoxical bradycardia."}
}

def query_drug_interactions(drug_name: str, patient_allergies: list = None, concurrent_medications: list = None) -> dict:
    """Query local offline drug interaction database."""
    start = time.time()
    allergies = [a.lower() for a in (patient_allergies or [])]
    drug_lower = drug_name.lower().strip()
    matched_drug = next((d for d in DRUG_DATABASE if drug_lower in d), None)

    if not matched_drug:
        result = {"status": "not_found", "drug": drug_name, "warning": "Drug not found in local DB."}
        _log_tool_call("unknown", "query_drug_interactions", {"drug": drug_name}, result, (time.time() - start) * 1000)
        return result

    drug_data = DRUG_DATABASE[matched_drug]
    allergy_contra = [f"Allergy '{a}' matches '{c}'" for a in allergies for c in drug_data["contraindicated_allergies"] if a in c or c in a]
    
    safety_status = "CONTRAINDICATED" if allergy_contra else "CLEAR"
    result = {"status": safety_status, "drug": matched_drug, "allergy_contraindicated": allergy_contra, "dosage_adult": drug_data["dosage_adult"], "timestamp": datetime.now().isoformat()}
    
    logger.info(f"DRUG DB [{matched_drug}] Status: {safety_status}")
    _log_tool_call("unknown", "query_drug_interactions", {"drug": drug_name}, result, (time.time() - start) * 1000)
    return result


# ═══════════════════════════════════════════════════════════════
# TOOL 7: GPS LOCATION
# ═══════════════════════════════════════════════════════════════

def get_gps_location() -> dict:
    """Get current GPS location."""
    DEMO_GPS = [("37.0660", "37.3781", "Gaziantep City Centre"), ("37.1347", "36.8468", "Killis Province")]
    lat, lon, name = random.choice(DEMO_GPS)
    result = {"status": "locked", "coordinates": f"{lat},{lon}", "latitude": float(lat), "longitude": float(lon), "location_name": name, "timestamp": datetime.now().isoformat()}
    logger.info(f"GPS: {lat},{lon} | {name}")
    return result


# ═══════════════════════════════════════════════════════════════
# TOOL ROUTER
# ═══════════════════════════════════════════════════════════════

TOOL_REGISTRY = {
    "read_pulse_oximeter": read_pulse_oximeter,
    "read_thermometer": read_thermometer,
    "capture_wound_image": capture_wound_image,
    "log_triage_decision": log_triage_decision,
    "broadcast_evacuation_request": broadcast_evacuation_request,
    "query_drug_interactions": query_drug_interactions,
    "get_gps_location": get_gps_location
}

def execute_tool(tool_name: str, tool_args: dict) -> dict:
    """Route a function call from the model to the correct handler."""
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Tool '{tool_name}' not found"}
    try:
        return TOOL_REGISTRY[tool_name](**tool_args)
    except Exception as e:
        return {"error": f"Tool '{tool_name}' failed: {e}"}