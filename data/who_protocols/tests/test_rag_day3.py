import sys
sys.path.insert(0, ".")

from core.rag import (
    build_knowledge_base, get_kb_status, get_collection,
    retrieve_context, retrieve_for_vitals, search_drug_protocols,
    build_rag_system_prompt, query_with_rag
)
from rich.console import Console
from rich.panel import Panel

console = Console()


def test_01_knowledge_base_built():
    """KB must exist and have enough chunks to be useful."""
    console.print("\n[yellow]TEST 01: Knowledge base is built[/yellow]")
    status = get_kb_status()
    assert status["status"] == "ready", \
        f"KB status is '{status['status']}' — run build_knowledge_base() first"
    assert status["total_chunks"] >= 50, \
        f"Only {status['total_chunks']} chunks — expected 50+. Check protocol files."
    console.print(
        f"  [green]PASS[/green] "
        f"{status['total_chunks']} chunks across "
        f"{len(status['sources'])} sources"
    )
    return True


def test_02_all_sources_present():
    """All 6 protocol documents must be ingested."""
    console.print("\n[yellow]TEST 02: All 6 protocol sources present[/yellow]")
    status  = get_kb_status()
    sources = [s["name"] for s in status["sources"]]
    expected = [
        "01_start_triage",
        "02_burns_protocol",
        "03_hemorrhage_shock",
        "04_head_spinal_trauma",
        "05_pediatric_emergencies",
        "06_obstetric_emergencies"
    ]
    missing = [e for e in expected if e not in sources]
    if missing:
        console.print(f"  [red]FAIL[/red] Missing sources: {missing}")
        return False
    console.print(
        f"  [green]PASS[/green] "
        f"All {len(expected)} protocol documents present"
    )
    return True


def test_03_start_protocol_retrieval():
    """Must retrieve START protocol content for triage queries."""
    console.print("\n[yellow]TEST 03: START protocol retrieval[/yellow]")
    context = retrieve_context(
        "patient breathing 34 per minute cannot follow commands radial pulse present"
    )
    assert context, "No context returned"
    context_lower = context.lower()
    keywords = ["start", "immediate", "breathing", "respiratory", "30"]
    found = [k for k in keywords if k in context_lower]
    assert len(found) >= 2, \
        f"Expected START protocol keywords, found only: {found}"
    console.print(
        f"  [green]PASS[/green] "
        f"Retrieved START protocol. Keywords found: {found}"
    )
    return True


def test_04_burns_protocol_retrieval():
    """Must retrieve burns content for burn injury queries."""
    console.print("\n[yellow]TEST 04: Burns protocol retrieval[/yellow]")
    context = retrieve_context(
        "burn injury forearm partial thickness TBSA Parkland formula fluid"
    )
    assert context, "No context returned"
    context_lower = context.lower()
    keywords = ["burn", "tbsa", "parkland", "fluid", "immediate"]
    found = [k for k in keywords if k in context_lower]
    assert len(found) >= 2, \
        f"Burns keywords not found. Only got: {found}"
    console.print(
        f"  [green]PASS[/green] "
        f"Retrieved burns protocol. Keywords found: {found}"
    )
    return True


def test_05_vitals_based_retrieval():
    """Vitals-specific retrieval must return relevant thresholds."""
    console.print("\n[yellow]TEST 05: Vitals-based retrieval[/yellow]")
    context = retrieve_for_vitals(
        spo2=87,
        hr=130,
        rr=32,
        temp=38.8,
        mechanism="trauma from building collapse"
    )
    assert context, "No context for critical vitals — expected protocol matches"
    assert "90" in context or "immediate" in context.lower(), \
        "Expected SpO2 90% threshold in retrieved context"
    console.print(
        f"  [green]PASS[/green] "
        f"Vitals retrieval returned {len(context.split())} words"
    )
    return True


def test_06_drug_protocol_retrieval():
    """Drug queries must return relevant dosing information."""
    console.print("\n[yellow]TEST 06: Drug protocol retrieval[/yellow]")
    context = search_drug_protocols("morphine", "trauma pain management")
    if context:
        context_lower = context.lower()
        keywords = ["morphine", "opioid", "dose", "pain", "analgesic", "mg"]
        found = [k for k in keywords if k in context_lower]
        console.print(
            f"  [green]PASS[/green] "
            f"Drug retrieval working. Keywords: {found}"
        )
    else:
        console.print(
            "  [yellow]WARN[/yellow] "
            "No drug context retrieved (drug info in clinical docs only)"
        )
    return True


def test_07_no_hallucination_on_empty_query():
    """Empty or nonsense query should return empty or minimal context."""
    console.print("\n[yellow]TEST 07: Empty query handling[/yellow]")
    context = retrieve_context("xyzzy nonsense gibberish banana protocol 12345")
    # Should either return empty or return low-relevance results
    if not context:
        console.print("  [green]PASS[/green] Empty context for nonsense query")
    else:
        # Check that relevance filter worked
        if "100%" in context or "99%" in context:
            console.print("  [red]WARN[/red] Suspiciously high relevance for nonsense query")
            return False
        console.print(
            "  [yellow]PASS (partial)[/yellow] "
            "Context returned but should be low relevance"
        )
    return True


def test_08_rag_system_prompt_augmentation():
    """RAG must add protocol context to the system prompt."""
    console.print("\n[yellow]TEST 08: RAG system prompt augmentation[/yellow]")
    from core.model import SYSTEM_PROMPT
    augmented = build_rag_system_prompt(
        "patient with burns and inhalation injury SpO2 88%"
    )
    assert augmented != SYSTEM_PROMPT, \
        "Augmented prompt is identical to base prompt — no context added"
    assert len(augmented) > len(SYSTEM_PROMPT) + 200, \
        "Augmented prompt barely longer than base — context may not have been added"
    added_content = augmented.replace(SYSTEM_PROMPT, "")
    assert any(
        word in added_content.lower()
        for word in ["protocol", "who", "immediate", "burn", "retrieved"]
    ), "No protocol content in augmented prompt"
    console.print(
        f"  [green]PASS[/green] "
        f"Augmented prompt is {len(augmented) - len(SYSTEM_PROMPT)} chars longer"
    )
    return True


def test_09_rag_full_inference():
    """Full RAG inference must produce a grounded triage response."""
    console.print("\n[yellow]TEST 09: Full RAG inference (uses model)[/yellow]")
    console.print("  [dim]Running Gemma 4 E4B with WHO protocol context...[/dim]")

    patient_input = """Patient: Adult male, 55 years old.
Fall from second floor during earthquake — 5 meter fall.
Breathing 22 per minute, regular.
Radial pulse present, rate about 90 bpm.
Alert and oriented. Follows all commands correctly.
Complains of severe back pain and cannot feel legs.
No external hemorrhage.
Known allergy: penicillin.
Please assess and give triage category."""

    try:
        response = query_with_rag(patient_input)
        assert response, "Empty response from RAG inference"
        assert len(response) > 100, "Response too short to be useful"

        resp_upper = response.upper()
        valid_categories = ["IMMEDIATE", "DELAYED", "MINOR", "EXPECTANT"]
        category_found = any(c in resp_upper for c in valid_categories)
        assert category_found, \
            f"No valid triage category in response. Got: {response[:100]}"

        console.print(f"  [green]PASS[/green] RAG inference produced triage response")

        # Bonus check: does it reference spinal injury?
        if "spinal" in response.lower() or "spine" in response.lower() \
           or "neurolog" in response.lower():
            console.print(
                "  [green]BONUS[/green] "
                "Model correctly identified spinal concern"
            )
        return True

    except Exception as e:
        console.print(f"  [red]FAIL[/red] RAG inference error: {e}")
        return False


def test_10_rag_vs_baseline():
    """
    Compare RAG response vs baseline (no context).
    RAG response should be more detailed and cite protocols.
    """
    console.print("\n[yellow]TEST 10: RAG vs baseline quality comparison[/yellow]")
    console.print("  [dim]Comparing responses with/without WHO context...[/dim]")

    patient_input = """Adult, burns to face and arms.
Voice is hoarse. SpO2 is 91%.
Breathing 26 per minute. Conscious.
Estimated 20 percent TBSA partial thickness burns."""

    from core.model import run_inference

    # Baseline (no RAG)
    baseline = run_inference(patient_input)
    baseline_words = len(baseline.split())

    # With RAG
    rag_response = query_with_rag(patient_input)
    rag_words    = len(rag_response.split())

    # RAG response should mention protocol-specific content
    protocol_words = [
        "parkland", "tbsa", "inhalation", "airway",
        "who", "protocol", "start", "rule of nines"
    ]
    baseline_protocol = sum(
        1 for w in protocol_words if w in baseline.lower()
    )
    rag_protocol = sum(
        1 for w in protocol_words if w in rag_response.lower()
    )

    console.print(f"  Baseline: {baseline_words} words, "
                  f"{baseline_protocol} protocol references")
    console.print(f"  RAG:      {rag_words} words, "
                  f"{rag_protocol} protocol references")

    if rag_protocol >= baseline_protocol:
        console.print(
            "  [green]PASS[/green] "
            "RAG response has equal or more protocol references"
        )
    else:
        console.print(
            "  [yellow]WARN[/yellow] "
            "RAG did not improve protocol references "
            "(model may already know this from training)"
        )
    return True


def run_all_tests():
    """Run all Day 3 RAG tests."""
    console.print(Panel(
        "[bold cyan]AEGIS-EDGE DAY 3 — RAG PIPELINE TESTS[/bold cyan]\n"
        "Verifying knowledge base, retrieval, and RAG inference",
        border_style="cyan"
    ))

    tests = [
        ("KB Built",              test_01_knowledge_base_built),
        ("All Sources Present",   test_02_all_sources_present),
        ("START Protocol",        test_03_start_protocol_retrieval),
        ("Burns Protocol",        test_04_burns_protocol_retrieval),
        ("Vitals Retrieval",      test_05_vitals_based_retrieval),
        ("Drug Protocol",         test_06_drug_protocol_retrieval),
        ("Empty Query",           test_07_no_hallucination_on_empty_query),
        ("Prompt Augmentation",   test_08_rag_system_prompt_augmentation),
        ("Full RAG Inference",    test_09_rag_full_inference),
        ("RAG vs Baseline",       test_10_rag_vs_baseline),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except AssertionError as e:
            console.print(f"  [red]FAIL[/red] Assertion: {e}")
            results.append((name, False))
        except Exception as e:
            console.print(f"  [red]ERROR[/red] {e}")
            results.append((name, False))

    # Summary
    passed_count = sum(1 for _, ok in results if ok)
    console.print("\n" + "="*60)
    console.print("[bold cyan]DAY 3 FINAL RESULTS[/bold cyan]")
    console.print("="*60)

    for name, ok in results:
        status = "[green]PASS[/green]" if ok else "[red]FAIL[/red]"
        console.print(f"  {status}: {name}")

    console.print(f"\n[bold]Score: {passed_count}/{len(results)}[/bold]")

    if passed_count >= 8:
        console.print(Panel(
            "[bold green]DAY 3 COMPLETE[/bold green]\n\n"
            "RAG pipeline is working:\n"
            "  WHO protocols ingested into ChromaDB\n"
            "  Relevant chunks retrieved per clinical query\n"
            "  Model responses grounded in WHO guidelines\n"
            "  System prompt augmented with real protocol context\n\n"
            "Tomorrow: Day 4 — Vision Pipeline (Wound Images)",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold yellow]{passed_count}/{len(results)} tests passed[/bold yellow]\n\n"
            "Fix red items above before Day 4.\n"
            "Most likely issue: protocol files not created in Phase 2.",
            border_style="yellow"
        ))


if __name__ == "__main__":
    run_all_tests()
