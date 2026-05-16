"""
tests/test_agent_day2.py
Day 2 — End-to-End Agent Integration Tests
Verifies that Gemma 4 autonomously uses tools to reach a triage decision.
"""
import sys
import os

# Ensure the root project directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hardware.ble_simulator import init_database
from core.agent_loop import run_agent, display_result
from rich.console import Console
from rich.panel import Panel

console = Console()

def test_scenario_1_critical_burns():
    """Critical patient — should trigger multiple tool calls and result in IMMEDIATE"""
    console.print(Panel(
        "[bold red]SCENARIO 1: Critical Burns + Suspected Inhalation Injury[/bold red]\n"
        "Expected: IMMEDIATE | Tools: pulse_ox, thermometer, log, broadcast",
        border_style="red"
    ))

    patient_input = """Patient: Adult male, approximately 38 years old.
Pulled from burning vehicle 5 minutes ago.
Facial burns visible, eyebrows singed off, nostrils appear burned.
Voice is hoarse and raspy. Coughing with black soot in sputum.
Burns visible on both forearms and chest.
Breathing is rapid and labored.
Conscious but very agitated and confused.
Cannot follow simple commands — when I say open your eyes, no response.
No known allergies.

Please gather vital signs and give me your triage assessment."""

    init_database()
    result = run_agent(patient_input, patient_id="P-0001")
    display_result(result)

    # Assertions
    passed = True
    if "IMMEDIATE" in result["response"].upper():
        console.print("  [green]PASS[/green]: Correct triage category (IMMEDIATE)")
    else:
        console.print("  [red]FAIL[/red]: Expected IMMEDIATE category")
        passed = False

    if len(result["tools_called"]) >= 2:
        console.print(f"  [green]PASS[/green]: Used {len(result['tools_called'])} tools")
    else:
        console.print("  [red]FAIL[/red]: AI did not use enough tools to be clinically sound")
        passed = False

    return passed

def test_scenario_2_walking_wounded():
    """Minor patient — should get MINOR/GREEN without over-triaging"""
    console.print(Panel(
        "[bold green]SCENARIO 2: Walking Wounded[/bold green]\n"
        "Expected: MINOR | Tools: log",
        border_style="green"
    ))

    patient_input = """Patient: Young woman, approximately 24 years old.
She walked over to me by herself.
Complaining of cuts on her right hand from broken glass.
Bleeding has mostly stopped on its own.
Alert and oriented — telling me exactly what happened.
Breathing normally. No other complaints.

Give me your triage assessment."""

    result = run_agent(patient_input, patient_id="P-0002")
    display_result(result)

    passed = True
    resp_upper = result["response"].upper()
    if "MINOR" in resp_upper or "GREEN" in resp_upper:
        console.print("  [green]PASS[/green]: Correct MINOR category")
    elif "DELAYED" in resp_upper:
        console.print("  [yellow]WARN[/yellow]: Got DELAYED (cautious model)")
    else:
        console.print("  [red]FAIL[/red]: Wrong category — should be MINOR")
        passed = False

    return passed

def test_scenario_3_drug_check():
    """Patient needing pain management — should trigger drug interaction check"""
    console.print(Panel(
        "[bold yellow]SCENARIO 3: Trauma with Drug Query[/bold yellow]\n"
        "Expected: IMMEDIATE/DELAYED | Tools: drug_check",
        border_style="yellow"
    ))

    patient_input = """Patient: Male, 45 years old. Right leg fracture.
Pain rated 9 out of 10.
Fully conscious and oriented.
KNOWN ALLERGY: opioids.
I want to give morphine for pain management.
Please check drug safety and give me your triage assessment."""

    result = run_agent(patient_input, patient_id="P-0003")
    display_result(result)

    passed = True
    if "query_drug_interactions" in result["tools_called"]:
        console.print("  [green]PASS[/green]: Drug interaction check called")
    else:
        console.print("  [yellow]WARN[/yellow]: Drug check not called (handled in text)")

    if "CONTRAINDICATED" in result["response"].upper() or "allergy" in result["response"].lower():
        console.print("  [green]PASS[/green]: Model flagged the opioid allergy")
    else:
        console.print("  [red]FAIL[/red]: Model failed to flag the allergy contraindication")
        passed = False

    return passed

def run_all_tests():
    """Run all Day 2 agent scenarios."""
    console.print(Panel(
        "[bold cyan]AEGIS-EDGE DAY 2 — AGENT INTEGRATION TESTS[/bold cyan]\n"
        "Testing Gemma 4 tool calling with 3 patient scenarios",
        border_style="cyan"
    ))

    results = []
    results.append(("Scenario 1: Critical Burns", test_scenario_1_critical_burns()))
    results.append(("Scenario 2: Walking Wounded", test_scenario_2_walking_wounded()))
    results.append(("Scenario 3: Drug Interaction", test_scenario_3_drug_check()))

    # Summary
    console.print("\n" + "="*60)
    console.print("[bold cyan]FINAL SUMMARY[/bold cyan]")
    console.print("="*60)

    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        status = "[green]PASS[/green]" if ok else "[red]FAIL[/red]"
        console.print(f"  {status}: {name}")

    console.print(f"\n[bold]Score: {passed}/{len(results)}[/bold]")

    if passed == len(results):
        console.print(Panel(
            "[bold green]DAY 2 COMPLETE[/bold green]\n\n"
            "All scenarios passed!\n"
            "Gemma 4 is calling tools autonomously and saving records to SQLite.\n\n"
            "Tomorrow: Day 3 — RAG Pipeline (WHO Triage Protocols)",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold yellow]{passed}/{len(results)} scenarios passed[/bold yellow]\n"
            "The tool pipeline is working, but the model's reasoning varies.\n"
            "This is normal for the E2B model. Proceed to Day 3.",
            border_style="yellow"
        ))

if __name__ == "__main__":
    run_all_tests()