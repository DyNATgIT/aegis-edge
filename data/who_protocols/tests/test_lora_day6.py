import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from core.model import run_inference, SYSTEM_PROMPT
from core.adapter import get_adapter_info

console = Console()

def run_comparison():
    console.print(Panel("[bold cyan]DAY 6: DOMAIN ADAPTATION TEST[/bold cyan]", border_style="cyan"))

    test_patient = "Patient: Male, 41 years old. Earthquake survivor. Breathing 33 per minute. No radial pulse. Unconscious."

    # 1. Generic Response (No prompt)
    raw = run_inference(test_patient, system_prompt="You are a helpful assistant.")
    
    # 2. Adapted Response (Aegis System Prompt)
    adapted = run_inference(test_patient, system_prompt=SYSTEM_PROMPT)

    markers = ["step", "start", "immediate", "respiratory", "perfusion", "mental"]
    raw_score = sum(1 for m in markers if m in raw.lower())
    adapted_score = sum(1 for m in markers if m in adapted.lower())

    table = Table(title="Base vs Adapted Quality", box=box.ROUNDED, border_style="cyan")
    table.add_column("Strategy", style="white")
    table.add_column("Protocol Markers", style="yellow")
    table.add_column("Correct Triage?", style="green")

    table.add_row("Generic Assistant", f"{raw_score}/{len(markers)}", "NO" if "IMMEDIATE" not in raw.upper() else "YES")
    table.add_row("Aegis-Edge Domain", f"{adapted_score}/{len(markers)}", "YES" if "IMMEDIATE" in adapted.upper() else "NO")
    
    console.print(table)
    
    # --- REVISED CODE HERE ---
    info = None
    try:
        # Attempt to get info, handling the potential JSONDecodeError
        info = get_adapter_info()
    except json.decoder.JSONDecodeError as e:
        console.print(f"[bold red]ERROR: Could not load adapter configuration due to invalid JSON data.[/bold red]")
        console.print(f"Details: {e}")
        # Set a default failure state if the config fails
        info = {'status': 'error', 'message': 'Failed to load config'}


    if info:
        console.print(f"\nAdapter Status: {info.get('status', 'Unknown')}")
        if info.get('status') == "config_only":
            console.print("[yellow]Note: Using system-prompt adaptation as weights are mocked.[/yellow]")

if __name__ == "__main__":
    run_all_tests = run_comparison()
