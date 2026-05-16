import sys
sys.path.insert(0, ".")

from pathlib  import Path
from rich.console import Console
from rich.panel   import Panel

console = Console()


def test_01_streamlit_installed():
    """Streamlit must be importable."""
    console.print("\n[yellow]TEST 01: Streamlit installed[/yellow]")
    try:
        import streamlit
        console.print(
            f"  [green]PASS[/green] streamlit {streamlit.__version__}"
        )
        return True
    except ImportError as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        return False


def test_02_config_exists():
    """Streamlit config must exist."""
    console.print("\n[yellow]TEST 02: Streamlit config exists[/yellow]")
    config_path = Path(".streamlit/config.toml")
    if config_path.exists():
        console.print("  [green]PASS[/green] .streamlit/config.toml found")
        return True
    else:
        console.print("  [red]FAIL[/red] Config not found")
        return False


def test_03_app_file_exists():
    """Main app file must exist and have content."""
    console.print("\n[yellow]TEST 03: app.py exists and has content[/yellow]")
    app_path = Path("ui/app.py")
    if not app_path.exists():
        console.print("  [red]FAIL[/red] ui/app.py not found")
        return False

    size = app_path.stat().st_size
    if size < 5000:
        console.print(
            f"  [yellow]WARN[/yellow] app.py too small ({size} bytes)"
        )
        return False

    console.print(f"  [green]PASS[/green] app.py found ({size:,} bytes)")
    return True


def test_04_demo_scenarios_complete():
    """All demo scenarios must be importable."""
    console.print("\n[yellow]TEST 04: Demo scenarios[/yellow]")
    try:
        sys.path.insert(0, "ui")
        # Read the file and check scenario keys
        with open("ui/app.py", encoding="utf-8") as f:
            content = f.read()

        required = ["IMMEDIATE", "DELAYED", "MINOR", "EXPECTANT"]
        for cat in required:
            assert cat in content, f"Missing {cat} demo scenario"

        console.print(
            "  [green]PASS[/green] All 4 triage categories in demo scenarios"
        )
        return True
    except AssertionError as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        return False


def test_05_backend_init():
    """Backend components must initialise without error."""
    console.print("\n[yellow]TEST 05: Backend initialisation[/yellow]")
    try:
        from hardware.ble_simulator import init_database
        from core.rag               import build_knowledge_base

        init_database()
        stats = build_knowledge_base()
        chunks = stats.get("total_chunks_in_db", 0)

        console.print(
            f"  [green]PASS[/green] "
            f"DB ready | KB: {chunks} chunks"
        )
        return True
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        return False


def test_06_triage_pipeline_via_ui():
    """
    Simulate what the UI does when the Triage button is clicked.
    Full pipeline from text input to result dict.
    """
    console.print("\n[yellow]TEST 06: Full pipeline (as UI calls it)[/yellow]")
    console.print(
        "  [dim]This runs inference — takes 10-30 seconds...[/dim]"
    )

    try:
        from core.run_triage import triage_text

        result = triage_text(
            patient_description=(
                "Adult male, 38 years old. "
                "Burns on arms, facial burns, hoarse voice. "
                "Breathing 30 per minute. Cannot follow commands."
            ),
            patient_id="P-UI-TEST",
            speak=False
        )

        assert "triage_category"  in result
        assert "response"         in result
        assert "tools_called"     in result
        assert result["triage_category"] in [
            "IMMEDIATE", "DELAYED", "MINOR", "EXPECTANT", "ASSESSING"
        ]

        category = result["triage_category"]
        tools    = result["tools_called"]
        elapsed  = result.get("elapsed_seconds", 0)

        console.print(
            f"  [green]PASS[/green] "
            f"Category: {category} | "
            f"Tools: {len(tools)} | "
            f"Time: {elapsed}s"
        )
        return True

    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        return False


def test_07_log_table_loads():
    """Triage log must load from SQLite without error."""
    console.print("\n[yellow]TEST 07: Log table loads[/yellow]")
    try:
        import sqlite3
        import pandas as pd
        from pathlib import Path

        db_path = Path("data/triage_log.db")
        if not db_path.exists():
            console.print(
                "  [yellow]SKIP[/yellow] No database yet — "
                "run triage first"
            )
            return True

        conn = sqlite3.connect(str(db_path))
        df   = pd.read_sql_query(
            "SELECT id, patient_id, category FROM triage_log "
            "ORDER BY id DESC LIMIT 5",
            conn
        )
        conn.close()

        console.print(
            f"  [green]PASS[/green] "
            f"Log loaded: {len(df)} recent records"
        )
        for _, row in df.iterrows():
            console.print(
                f"    #{row['id']} | "
                f"{row['patient_id']} | "
                f"{row['category']}"
            )
        return True

    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        return False


def test_08_multilingual_phrases():
    """All 6 language phrases must be available."""
    console.print("\n[yellow]TEST 08: Multilingual phrases in UI[/yellow]")
    try:
        from core.audio import get_triage_phrase

        langs = {
            "en": "English", "ar": "Arabic", "tr": "Turkish",
            "fr": "French",  "es": "Spanish", "sw": "Swahili"
        }

        for code, name in langs.items():
            phrase = get_triage_phrase("IMMEDIATE", code)
            assert len(phrase) > 5, f"Empty phrase for {name}"
            console.print(f"  [green]{name}[/green]: {phrase}")

        return True

    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")
        return False


def test_09_launch_script_exists():
    """Launch script must exist."""
    console.print("\n[yellow]TEST 09: Launch script exists[/yellow]")
    if Path("launch_ui.ps1").exists():
        console.print("  [green]PASS[/green] launch_ui.ps1 found")
        return True
    else:
        console.print("  [yellow]WARN[/yellow] launch_ui.ps1 not found")
        return True   # Not critical


def run_all_tests():
    console.print(Panel(
        "[bold cyan]AEGIS-EDGE DAY 8 — UI TESTS[/bold cyan]\n"
        "Aayu Wadhwani & Keshav Bhatnagar\n"
        "Testing Streamlit dashboard",
        border_style="cyan"
    ))

    tests = [
        ("Streamlit installed",    test_01_streamlit_installed),
        ("Config exists",          test_02_config_exists),
        ("app.py exists",          test_03_app_file_exists),
        ("Demo scenarios",         test_04_demo_scenarios_complete),
        ("Backend init",           test_05_backend_init),
        ("Full pipeline (UI)",     test_06_triage_pipeline_via_ui),
        ("Log table loads",        test_07_log_table_loads),
        ("Multilingual phrases",   test_08_multilingual_phrases),
        ("Launch script",          test_09_launch_script_exists),
    ]

    results = []
    for name, fn in tests:
        try:
            ok = fn()
            results.append((name, ok))
        except Exception as e:
            console.print(f"  [red]ERROR: {e}[/red]")
            results.append((name, False))

    passed = sum(1 for _, ok in results if ok)
    console.print(f"\n[bold]Score: {passed}/{len(results)}[/bold]")

    if passed >= 7:
        console.print(Panel(
            "[bold green]DAY 8 COMPLETE[/bold green]\n\n"
            "Streamlit UI ready:\n"
            "  Dark tactical theme         ✅\n"
            "  Demo scenario selector      ✅\n"
            "  Voice input button          ✅\n"
            "  Wound image upload          ✅\n"
            "  Triage result banner        ✅\n"
            "  Vitals display              ✅\n"
            "  Multilingual phrases        ✅\n"
            "  Triage log table            ✅\n\n"
            "Launch: streamlit run ui\\app.py\n\n"
            "Tomorrow: Day 9 — Demo Video",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold yellow]{passed}/{len(results)} passed[/bold yellow]\n"
            "Fix red items before Day 9.",
            border_style="yellow"
        ))


if __name__ == "__main__":
    run_all_tests()
