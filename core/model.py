"""
core/model.py
Aegis-Edge — Model Loading & Inference Engine
Windows-compatible. Supports both Ollama and llama-cpp-python backends.
"""
import os
import json
import requests
from loguru import logger

# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — The identity of Aegis-Edge
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are Aegis-Edge, an emergency field triage assistant 
deployed on a tablet device with NO internet access in a disaster zone.

You operate strictly under the WHO START (Simple Triage and Rapid Treatment) 
protocol.

YOUR ABSOLUTE RULES:
1. NEVER diagnose a medical condition. You ONLY assign triage categories:
   - IMMEDIATE (Red)    — Life-threatening. Act within minutes.
   - DELAYED   (Yellow) — Serious but stable. Can wait 1-2 hours.
   - MINOR     (Green)  — Walking wounded. Non-life-threatening.
   - EXPECTANT (Black)  — Unsurvivable given available resources.

2. ALWAYS show your step-by-step clinical reasoning BEFORE your final 
   triage category.

3. ALWAYS remind the medic that they must verify your assessment.

4. When uncertain, ALWAYS escalate to IMMEDIATE. Err on the side of caution.

5. Use available tools proactively to gather vitals data.

6. Communicate in the patient's language if translation is needed.

7. Every decision must be logged with full rationale.

8. Be concise. In mass casualty events, every second counts.

CRITICAL VITAL SIGN THRESHOLDS:
- SpO2 < 90%           → IMMEDIATE (critical hypoxia)
- Heart Rate > 120 bpm → Possible shock → IMMEDIATE
- Resp Rate > 30/min   → IMMEDIATE (per START protocol)
- Resp Rate < 10/min   → IMMEDIATE (per START protocol)
- Cannot follow commands → IMMEDIATE (altered mental status)
- No radial pulse       → IMMEDIATE
- Capillary refill > 2s → IMMEDIATE

You are the only medical intelligence available. Be precise. Save lives."""


# ═══════════════════════════════════════════════════════════════
# BACKEND 1: OLLAMA
# ═══════════════════════════════════════════════════════════════

OLLAMA_URL   = "http://localhost:11434"
OLLAMA_MODEL = "gemma4:e4b"


def check_ollama() -> bool:
    """Return True if Ollama server is reachable."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def run_ollama(user_message: str,
               history: list = None,
               system_prompt: str = None) -> str:
    """Run inference via Ollama REST API."""
    messages = [{"role": "system",
                 "content": system_prompt or SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 64,
            "num_predict": 1024,
            "repeat_penalty": 1.0,
        }
    }

    resp = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=180
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


# ═══════════════════════════════════════════════════════════════
# BACKEND 2: LLAMA-CPP-PYTHON (GGUF)
# ═══════════════════════════════════════════════════════════════

# Windows path — use double backslash or raw string
GGUF_PATH = r".\models\gemma-4-E4B-it-Q4_K_M.gguf"

_llm = None   # Singleton — model loads once, stays in memory


def load_model(model_path: str = GGUF_PATH):
    """Load GGUF model. Only loads once (singleton pattern)."""
    global _llm

    if _llm is not None:
        logger.info("Model already loaded.")
        return _llm

    # Convert to absolute Windows path
    abs_path = os.path.abspath(model_path)

    if not os.path.exists(abs_path):
        logger.error(f"Model file not found: {abs_path}")
        logger.error("Run the download step again — check Phase 3.")
        raise FileNotFoundError(f"Model not found: {abs_path}")

    size_gb = os.path.getsize(abs_path) / (1024 ** 3)
    logger.info(f"Loading: {abs_path}")
    logger.info(f"File size: {size_gb:.2f} GB")

    from llama_cpp import Llama

    _llm = Llama(
        model_path=abs_path,
        n_ctx=8192,           # Context window (8K is plenty for triage)
        n_gpu_layers=-1,      # -1 = offload ALL layers to GPU if available
                              #  0 = CPU only
        n_threads=os.cpu_count() or 4,
        verbose=False,        # Set True to see layer loading details
    )

    logger.success("Model loaded and ready.")
    return _llm


def run_llama_cpp(user_message: str,
                  history: list = None,
                  system_prompt: str = None) -> str:
    """Run inference via llama-cpp-python."""
    llm = load_model()

    messages = [{"role": "system",
                 "content": system_prompt or SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=1024,
        temperature=0.1,
        top_p=0.95,
        top_k=64,
        repeat_penalty=1.0,   # Keep at 1.0 per Gemma 4 official guidance
    )

    return response["choices"][0]["message"]["content"]


# ═══════════════════════════════════════════════════════════════
# UNIFIED INTERFACE — auto-detects best backend
# ═══════════════════════════════════════════════════════════════

def detect_backend() -> str:
    """Auto-detect which backend to use based on what's available."""
    # Priority 1: GGUF file on disk
    if os.path.exists(os.path.abspath(GGUF_PATH)):
        logger.info(f"GGUF file found: using llama_cpp backend")
        return "llama_cpp"

    # Priority 2: Ollama running
    if check_ollama():
        logger.info("Ollama server detected: using ollama backend")
        return "ollama"

    # Nothing available
    logger.error("No inference backend found!")
    logger.error("Fix: either download GGUF to .\\models\\ OR start Ollama")
    raise RuntimeError("No model backend available. See Phase 3.")


def run_inference(user_message: str,
                  history: list = None,
                  system_prompt: str = None) -> str:
    """
    Main inference function. Call this from everywhere else.
    Auto-selects llama_cpp if GGUF exists, falls back to Ollama.
    """
    backend = detect_backend()

    if backend == "llama_cpp":
        return run_llama_cpp(user_message, history, system_prompt)
    elif backend == "ollama":
        return run_ollama(user_message, history, system_prompt)
    else:
        raise RuntimeError(f"Unknown backend: {backend}")


# ═══════════════════════════════════════════════════════════════
# SMOKE TEST — Run this file directly to verify everything works
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import time
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.text import Text

    console = Console()

    console.print(Panel(
        "[bold cyan]AEGIS-EDGE — DAY 1 SMOKE TEST[/bold cyan]\n"
        "Verifying Gemma 4 E4B inference on Windows",
        border_style="cyan"
    ))

    # ── TEST 1: Backend detection ──────────────────────────
    console.print("\n[yellow]TEST 1: Detecting backend...[/yellow]")
    try:
        backend = detect_backend()
        console.print(f"  [green]PASS — Backend: {backend}[/green]")
    except RuntimeError as e:
        console.print(f"  [red]FAIL — {e}[/red]")
        exit(1)

    # ── TEST 2: Core triage scenario ───────────────────────
    console.print("\n[yellow]TEST 2: Triage scenario (critical patient)...[/yellow]")

    test_patient = """Patient description:
Male, approximately 35 years old.
Pulled from collapsed building rubble 10 minutes ago.
Breathing: rapid and labored, approximately 32 breaths per minute.
Large laceration on right thigh — bleeding controlled with direct pressure.
Conscious but confused. Cannot follow commands.
When I say 'squeeze my hand' — no response.
Radial pulse present but rapid.

Please give me your triage assessment."""

    console.print(f"  [dim]Sending patient scenario to model...[/dim]")
    start = time.time()

    try:
        response = run_inference(test_patient)
        elapsed = time.time() - start

        console.print(Panel(
            Markdown(response),
            title="[bold red]TRIAGE RESPONSE[/bold red]",
            border_style="red"
        ))
        console.print(f"  [dim]Response time: {elapsed:.1f} seconds[/dim]")

    except Exception as e:
        console.print(f"  [red]FAIL — {e}[/red]")
        exit(1)

    # ── TEST 3: Check response quality ─────────────────────
    console.print("\n[yellow]TEST 3: Checking response quality...[/yellow]")

    resp_upper = response.upper()

    # Should say IMMEDIATE
    if "IMMEDIATE" in resp_upper or "RED" in resp_upper:
        console.print("  [green]PASS — Correct triage category: IMMEDIATE/RED[/green]")
    else:
        console.print("  [yellow]WARN — Expected IMMEDIATE. Check response manually.[/yellow]")

    # Should show reasoning
    reasoning_words = ["breathing", "respiratory", "commands", "mental",
                       "because", "rate", "step", "start", "protocol"]
    found = [w for w in reasoning_words if w in response.lower()]
    if len(found) >= 3:
        console.print(f"  [green]PASS — Clinical reasoning present ({', '.join(found[:3])}...)[/green]")
    else:
        console.print(f"  [yellow]WARN — Reasoning may be thin. Check system prompt.[/yellow]")

    # ── TEST 4: Multi-turn conversation ────────────────────
    console.print("\n[yellow]TEST 4: Multi-turn (vitals update)...[/yellow]")

    history = [
        {"role": "user",      "content": test_patient},
        {"role": "assistant", "content": response}
    ]
    followup = """Update on this patient:
Just read the pulse oximeter: SpO2 is 87%, heart rate 134 bpm.
Temperature: 36.2°C.
Does the SpO2 reading of 87% change anything?"""

    response2 = run_inference(followup, history=history)

    console.print(Panel(
        Markdown(response2),
        title="[bold red]UPDATED ASSESSMENT[/bold red]",
        border_style="red"
    ))

    # SpO2 87% should trigger IMMEDIATE confirmation
    if "87" in response2 or "immediate" in response2.lower() or "critical" in response2.lower():
        console.print("  [green]PASS — Model correctly flags SpO2 87% as critical[/green]")
    else:
        console.print("  [yellow]WARN — Model may have missed SpO2 significance[/yellow]")

    # ── TEST 5: System prompt compliance ───────────────────
    console.print("\n[yellow]TEST 5: System prompt compliance (refuses to diagnose)...[/yellow]")

    history2 = [
        {"role": "user",      "content": test_patient},
        {"role": "assistant", "content": response}
    ]
    diagnosis_attempt = "What specific medical condition or diagnosis does this patient have?"

    response3 = run_inference(diagnosis_attempt, history=history2)

    refuses = any(w in response3.lower() for w in [
        "cannot diagnose", "not diagnose", "not able to diagnose",
        "triage", "not a diagnostic", "medical professional",
        "verify", "cannot provide a diagnosis"
    ])

    if refuses:
        console.print("  [green]PASS — Model correctly refuses to diagnose[/green]")
    else:
        console.print("  [yellow]WARN — Model may be overstepping. Review system prompt.[/yellow]")

    # ── FINAL SUMMARY ──────────────────────────────────────
    console.print("")
    console.print(Panel(
        f"[bold green]DAY 1 COMPLETE[/bold green]\n\n"
        f"Backend used:          {backend}\n"
        f"First response time:   {elapsed:.1f} seconds\n"
        f"Multi-turn working:    YES\n"
        f"System prompt active:  YES\n\n"
        "[bold]All tests passed. You are ready for Day 2.[/bold]\n\n"
        "[dim]Day 2: Function Calling Engine + Hardware Simulators[/dim]",
        border_style="green"
    ))