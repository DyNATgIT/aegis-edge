"""
tests/test_tools.py
Day 2 — Tool Unit Tests
Verifies that all hardware simulators return correctly structured data.
"""
import sys
import os

# Ensure the root project directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hardware.ble_simulator import (
    init_database, execute_tool,
    read_pulse_oximeter, read_thermometer, capture_wound_image,
    log_triage_decision, broadcast_evacuation_request,
    query_drug_interactions, get_gps_location, TOOL_REGISTRY
)
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

def run_all_tool_tests():
    console.print(Panel(
        "[bold cyan]AEGIS-EDGE — DAY 2 TOOL TESTS[/bold cyan]\n"
        "Testing all 7 hardware simulators independently",
        border_style="cyan"
    ))

    # Initialize database before testing the logger
    init_database()
    results = []

    # ── TEST 1: Pulse Oximeter ──────────────────────────────
    console.print("\n[yellow]TEST 1: Pulse Oximeter[/yellow]")
    try:
        r = read_pulse_oximeter("P-TEST-001")
        assert "spo2_percent" in r, "Missing spo2_percent"
        assert "heart_rate_bpm" in r, "Missing heart_rate_bpm"
        assert r["status"] == "success"
        console.print(f"  [green]PASS[/green] SpO2: {r['spo2_percent']}% | HR: {r['heart_rate_bpm']} bpm")
        results.append(("read_pulse_oximeter", True, ""))
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        results.append(("read_pulse_oximeter", False, str(e)))

    # ── TEST 2: Thermometer ─────────────────────────────────
    console.print("\n[yellow]TEST 2: Thermometer[/yellow]")
    try:
        r = read_thermometer("P-TEST-001", "celsius")
        assert "temperature" in r
        assert r["status"] == "success"
        console.print(f"  [green]PASS[/green] Temp: {r['temperature']}°C | Flag: {r['flag']}")
        results.append(("read_thermometer", True, ""))
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        results.append(("read_thermometer", False, str(e)))

    # ── TEST 3: Camera Capture ──────────────────────────────
    console.print("\n[yellow]TEST 3: Camera Capture[/yellow]")
    try:
        r = capture_wound_image("left forearm")
        assert r["status"] == "captured"
        assert "image_path" in r
        console.print(f"  [green]PASS[/green] Image: {r['image_file']} | Path: {r['image_path']}")
        results.append(("capture_wound_image", True, ""))
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        results.append(("capture_wound_image", False, str(e)))

    # ── TEST 4: Triage Logger ───────────────────────────────
    console.print("\n[yellow]TEST 4: Triage Logger (SQLite)[/yellow]")
    try:
        r = log_triage_decision(
            patient_id="P-TEST-001",
            category="IMMEDIATE",
            rationale="Unit Test: Validating DB write",
            confidence=0.95
        )
        assert r["status"] == "logged"
        assert r["record_id"] > 0
        console.print(f"  [green]PASS[/green] Record ID: {r['record_id']} saved to database")
        results.append(("log_triage_decision", True, ""))
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        results.append(("log_triage_decision", False, str(e)))

    # ── TEST 5: LoRa Broadcast ──────────────────────────────
    console.print("\n[yellow]TEST 5: LoRa Radio Broadcast[/yellow]")
    try:
        r = broadcast_evacuation_request(
            patient_id="P-TEST-001",
            priority=1,
            condition_summary="Test broadcast: Critical patient",
            gps_coordinates="37.0660,37.3781"
        )
        assert r["status"] == "broadcast_sent"
        assert "ack_received" in r
        console.print(f"  [green]PASS[/green] ACK Received: {r['ack_received']}")
        results.append(("broadcast_evacuation_request", True, ""))
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        results.append(("broadcast_evacuation_request", False, str(e)))

    # ── TEST 6: Drug Database ──────────────────────────────
    console.print("\n[yellow]TEST 6: Drug Database[/yellow]")
    try:
        r = query_drug_interactions("morphine", patient_allergies=["opioids"])
        assert r["status"] == "CONTRAINDICATED"
        console.print(f"  [green]PASS[/green] Correctly flagged: {r['drug']} as CONTRAINDICATED")
        results.append(("drug_db_check", True, ""))
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        results.append(("drug_db_check", False, str(e)))

    # ── TEST 7: GPS Location ───────────────────────────────
    console.print("\n[yellow]TEST 7: GPS Location[/yellow]")
    try:
        r = get_gps_location()
        assert r["status"] == "locked"
        assert "coordinates" in r
        console.print(f"  [green]PASS[/green] Coords: {r['coordinates']} | {r['location_name']}")
        results.append(("get_gps_location", True, ""))
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        results.append(("get_gps_location", False, str(e)))

    # ── TEST 8: Router Test ───────────────────────────────
    console.print("\n[yellow]TEST 8: Tool Router (execute_tool)[/yellow]")
    try:
        r = execute_tool("get_gps_location", {})
        assert r["status"] == "locked"
        console.print("  [green]PASS[/green] Router successfully dispatched call.")
        results.append(("execute_tool_router", True, ""))
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        results.append(("execute_tool_router", False, str(e)))

    # ── FINAL SUMMARY ───────────────────────────────────────
    console.print("")
    table = Table(
        title="DAY 2 TOOL TEST RESULTS",
        box=box.ROUNDED,
        border_style="cyan"
    )
    table.add_column("Tool", style="white")
    table.add_column("Result", style="white")
    table.add_column("Note", style="dim")

    passed = 0
    for name, ok, note in results:
        if ok:
            table.add_row(name, "[green]PASS[/green]", note)
            passed += 1
        else:
            table.add_row(name, "[red]FAIL[/red]", note)

    console.print(table)
    
    if passed == len(results):
        console.print(Panel("[bold green]ALL TOOLS WORKING[/bold green]\nProceed to Phase 5.", border_style="green"))
    else:
        console.print(Panel(f"[bold red]FAILED: {len(results)-passed} tests failed[/bold red]", border_style="red"))

if __name__ == "__main__":
    run_all_tool_tests()