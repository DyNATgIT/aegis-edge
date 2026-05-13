import sys
sys.path.insert(0, ".")
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from hardware.ble_simulator import init_database
from core.rag import build_knowledge_base
from core.run_triage import triage_text, triage_image

console = Console()

def test_scenarios():
    init_database()
    build_knowledge_base()
    
    # Scenario 1: Critical Burns
    console.print(Panel("[bold red]SCENARIO 1: Burns + Inhalation[/bold red]", border_style="red"))
    res1 = triage_text("Adult male, 38yo. Burning vehicle. Facial burns, hoarse voice. Breathing 30/min. Confused.", speak=False)
    print(f"  Category: {res1['triage_category']} | Tools: {len(res1['tools_called'])}")

    # Scenario 2: Walking Wounded
    console.print(Panel("[bold green]SCENARIO 2: Walking Wounded[/bold green]", border_style="green"))
    res2 = triage_text("Young woman, 24yo. Walked to me. Cut on hand. Alert and oriented.", speak=False)
    print(f"  Category: {res2['triage_category']} | Tools: {len(res2['tools_called'])}")

    # Scenario 3: Vision Test
    console.print(Panel("[bold cyan]SCENARIO 3: Vision Integration[/bold cyan]", border_style="cyan"))
    img_path = str(Path("data/test_images/burn_partial.jpg"))
    if Path(img_path).exists():
        res3 = triage_image("Patient has burns on arm.", image_path=img_path, speak=False)
        print(f"  Category: {res3['triage_category']} | Image: {res3['image_analyzed']}")
    else:
        print("  [red]Image not found - skip test[/red]")

if __name__ == "__main__":
    test_scenarios()
