"""
core/agent_loop.py
Aegis-Edge — Optimized Agent Loop
FIXED: Using Structured Prompting for Ollama to prevent 500 Server Errors on low RAM.
"""

import json
import re
import os
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from core.model import run_inference, detect_backend, SYSTEM_PROMPT, load_model
from core.tools import TOOL_SCHEMA, TOOL_NAMES
from hardware.ble_simulator import execute_tool, init_database

console = Console()
MAX_TOOL_ITERATIONS = 6

def get_tool_descriptions():
    """Returns a text-based menu of tools for the model."""
    desc = "AVAILABLE TOOLS:\n"
    for t in TOOL_SCHEMA:
        fn = t["function"]
        desc += f"- {fn['name']}: {fn['description'][:100]}... (Args: {fn['parameters']['properties']})\n"
    return desc

# ═══════════════════════════════════════════════════════════════
# UNIFIED AGENT LOOP (The 'Safe' Way)
# ═══════════════════════════════════════════════════════════════

def run_agent_safe(patient_input: str, patient_id: str = "P-UNKNOWN", system_prompt: str = SYSTEM_PROMPT) -> dict:
    """
    A robust loop that doesn't rely on API tool-calling features.
    It uses 'Structured Prompting' which is stable on low-RAM systems.
    """
    tool_menu = get_tool_descriptions()
    prompt_header = f"{system_prompt}\n\n{tool_menu}\n\nTo call a tool, output EXACTLY:\nTOOL_CALL: {{\"name\": \"tool_name\", \"args\": {{\"param\": \"value\"}}}}\n\n"
    
    messages = []
    tool_results_log = []
    final_response = ""
    current_input = prompt_header + f"PATIENT CASE:\n{patient_input}"

    for iteration in range(MAX_TOOL_ITERATIONS):
        # Run inference using the basic run_inference (which is stable)
        response_text = run_inference(current_input, messages, system_prompt=system_prompt)
        
        # Check for the TOOL_CALL pattern
        match = re.search(r'TOOL_CALL:\s*(\{.*?\})', response_text, re.DOTALL)
        if match:
            try:
                call_data = json.loads(match.group(1))
                tool_name = call_data.get("name", "")
                tool_args = call_data.get("args", {})
                
                console.print(f"  [bold green]TOOL CALL:[/bold green] {tool_name}({tool_args})")
                res = execute_tool(tool_name, tool_args)
                tool_results_log.append({"tool": tool_name, "args": tool_args, "result": res})
                
                messages.append({"role": "assistant", "content": response_text})
                current_input = f"TOOL RESULT:\n{json.dumps(res)}\n\nContinue triage based on this data."
            except Exception as e:
                logger.error(f"Tool parse error: {e}")
                break
        else:
            final_response = response_text
            break

    return {
        "patient_id": patient_id, 
        "response": final_response, 
        "tools_called": [t["tool"] for t in tool_results_log], 
        "tool_results": tool_results_log, 
        "iterations": iteration + 1
    }

# ═══════════════════════════════════════════════════════════════
# RAG + VOICE INTEGRATION
# ═══════════════════════════════════════════════════════════════

def run_agent_with_rag(patient_input: str, patient_id: str = "P-UNKNOWN", tool_vitals: dict = None) -> dict:
    from core.rag import build_rag_system_prompt
    backend = detect_backend()
    console.print(Panel(f"[bold cyan]AEGIS-EDGE TRIAGE — RAG + TOOLS[/bold cyan]\nPatient: {patient_id} | Backend: {backend}", border_style="cyan"))

    # 1. Get RAG-augmented prompt
    augmented_system = build_rag_system_prompt(patient_input, tool_vitals)
    
    # 2. Run the 'Safe' loop
    return run_agent_safe(patient_input, patient_id, system_prompt=augmented_system)

def run_agent(patient_input: str, patient_id: str = "P-UNKNOWN") -> dict:
    return run_agent_safe(patient_input, patient_id)

def run_voice_agent(patient_id: str = "P-VOICE", record_duration: int = 8, patient_language: str = "auto") -> dict:
    from core.audio import record_and_transcribe, speak_text, get_triage_phrase

    print(f"\n{'='*60}\n  AEGIS-EDGE — VOICE AGENT MODE\n{'='*60}")
    
    print(f"\n🎙️  RECORDING... Speak now! ({record_duration}s)")
    result = record_and_transcribe(duration=record_duration, language=patient_language)
    text = result["text"]
    detected_lang = result["detected_language"]

    if not text.strip(): return {"error": "No speech detected"}

    print(f"\n   Detected Language: {result['language_name']}")
    print(f"   Transcription: {text}")

    # Run the RAG agent
    agent_result = run_agent_with_rag(patient_input=text, patient_id=patient_id)

    # Extract category for speech
    category = "ASSESSING"
    res_upper = agent_result.get("response", "").upper()
    for cat in ["IMMEDIATE", "DELAYED", "MINOR", "EXPECTANT"]:
        if cat in res_upper:
            category = cat
            break

    triage_phrase = get_triage_phrase(category, detected_lang)
    print(f"\n🔊 Speaking result in {result['language_name']}...")
    speak_text(triage_phrase)
    
    if category == "IMMEDIATE":
        speak_text(get_triage_phrase("calm_patient", detected_lang))

    agent_result["voice_transcript"] = text
    agent_result["detected_language"] = detected_lang
    agent_result["triage_category"] = category
    return agent_result

def display_result(result: dict):
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return
    
    response = result.get("response", "")
    tools = result.get("tools_called", [])
    resp_upper = response.upper()
    color = "red" if "IMMEDIATE" in resp_upper else "yellow" if "DELAYED" in resp_upper else "green" if "MINOR" in resp_upper else "white"
    
    if tools: console.print(f"\n[bold]Tools Used:[/bold] {' → '.join(tools)}")
    console.print(Panel(Markdown(response), title=f"[bold {color}]TRIAGE RESULT[/bold {color}]", border_style=color))