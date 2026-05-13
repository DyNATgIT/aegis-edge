import json
import re
import os
import time
from pathlib import Path
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.panel   import Panel
from rich.markdown import Markdown

from core.model import run_inference, detect_backend, SYSTEM_PROMPT
from core.tools import TOOL_SCHEMA
from hardware.ble_simulator import execute_tool

console = Console()
MAX_ITERATIONS = 6

# ═══════════════════════════════════════════════════════════════
# ROBUST PARSER — The "Sledgehammer"
# ═══════════════════════════════════════════════════════════════

def robust_parse_tool(text: str) -> tuple[str, dict]:
    """
    Extremely robust tool parser. 
    If JSON fails, it uses Regex to extract name and patient_id.
    """
    # 1. Try standard JSON first
    try:
        # Remove markdown blocks
        clean_text = text.replace("```json", "").replace("```", "").strip()
        # Find first { and last }
        start = clean_text.find('{')
        end = clean_text.rfind('}') + 1
        if start != -1 and end != 0:
            data = json.loads(clean_text[start:end].replace("'", '"'))
            return data.get("name", ""), data.get("args", {})
    except:
        pass

    # 2. REGEX FALLBACK: Extract name and patient_id manually
    # Look for "name": "something"
    name_match = re.search(r'name["\']\s*:\s*["\']([^"\']+)["\']', text)
    # Look for "patient_id": "something"
    id_match = re.search(r'patient_id["\']\s*:\s*["\']([^"\']+)["\']', text)
    
    name = name_match.group(1) if name_match else "unknown"
    pid = id_match.group(1) if id_match else "P-UNKNOWN"
    
    return name, {"patient_id": pid}

# ═══════════════════════════════════════════════════════════════
# TRIAGE SESSION
# ═══════════════════════════════════════════════════════════════

class TriageSession:
    def __init__(self, patient_id: str = None):
        self.patient_id  = patient_id or f"P-{datetime.now().strftime('%H%M%S')}"
        self.start_time  = datetime.now()
        self.tools_called = []
        self.vitals       = {}
        self.rag_context  = ""
        self.vision_summary = ""
        self.transcript   = ""
        self.detected_lang = "en"
        self.triage_category = None
        self.final_response = ""
        self.errors       = []

    def collect_voice_input(self, duration: int = 8) -> str:
        try:
            from core.audio import record_audio, transcribe_audio
            audio = record_audio(duration)
            result = transcribe_audio(audio_array=audio, language="auto")
            self.transcript = result.get("text", "")
            self.detected_lang = result.get("detected_language", "en")
            console.print(f"  [green]Voice:[/green] [{result.get('language_name', 'unknown')}] {self.transcript[:80]}...")
            return self.transcript
        except Exception as e:
            self.errors.append(f"Voice failed: {e}")
            return ""

    def collect_image_input(self, image_path: str) -> str:
        if not image_path or not Path(image_path).exists(): return ""
        try:
            from core.vision import analyze_wound_image
            result = analyze_wound_image(image_path, clinical_context=self.transcript or "")
            self.vision_summary = f"WOUND ANALYSIS: {result.get('severity')}. Details: {result.get('analysis', '')[:200]}"
            return self.vision_summary
        except Exception as e:
            self.errors.append(f"Vision failed: {e}")
            return ""

    def retrieve_protocols(self, query: str) -> str:
        try:
            from core.rag import retrieve_context
            self.rag_context = retrieve_context(query, n_results=3)
            return self.rag_context
        except Exception as e:
            self.errors.append(f"RAG failed: {e}")
            return ""

    def build_system_prompt(self) -> str:
        from core.model import SYSTEM_PROMPT
        final_prompt = str(SYSTEM_PROMPT)
        if self.rag_context:
            final_prompt += f"\n\n[WHO PROTOCOLS]\n{self.rag_context}\n"
        if self.vision_summary:
            final_prompt += f"\n\n[VISION ANALYSIS]\n{self.vision_summary}\n"
        
        tool_menu = "AVAILABLE TOOLS:\n"
        for t in TOOL_SCHEMA:
            fn = t["function"]
            tool_menu += f"- {fn['name']}: {fn['description'][:60]}...\n"
        
        final_prompt += (
            f"\n{tool_menu}\n"
            "CRITICAL: To call a tool, you MUST output exactly: "
            "TOOL_CALL: {\"name\": \"tool_name\", \"args\": {\"patient_id\": \"ID\"}}"
        )
        return final_prompt

    def run_agent_loop(self, patient_input: str) -> str:
        system_prompt = self.build_system_prompt()
        messages = []
        tool_results_log = []
        final_response = ""
        current_input = f"PATIENT CASE:\n{patient_input}"

        for iteration in range(MAX_ITERATIONS):
            console.print(f"  [dim]Agent iteration {iteration + 1}/{MAX_ITERATIONS}[/dim]")
            response_text = run_inference(current_input, messages, system_prompt=system_prompt)
            
            match = re.search(r'TOOL_CALL:\s*(\{.*?\})', response_text, re.DOTALL)
            if match:
                # Use our ROBUST parser instead of json.loads
                tool_name, tool_args = robust_parse_tool(match.group(1))
                
                if tool_name == "unknown":
                    console.print(f"  [red]Parser failed to find tool name. Skipping...[/red]")
                    break

                console.print(f"  [bold green]🔧 TOOL:[/bold green] {tool_name}")
                try:
                    res = execute_tool(tool_name, tool_args)
                    self.tools_called.append(tool_name)
                    if tool_name == "read_pulse_oximeter":
                        self.vitals["spo2"] = res.get("spo2_percent")
                        self.vitals["hr"] = res.get("heart_rate_bpm")
                    elif tool_name == "read_thermometer":
                        self.vitals["temp"] = res.get("temperature")

                    messages.append({"role": "assistant", "content": response_text})
                    current_input = f"TOOL RESULT:\n{json.dumps(res)}\n\nContinue triage."
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    break
            else:
                final_response = response_text
                break

        return final_response

    def extract_category(self, response: str) -> str:
        ru = response.upper()
        for cat in ["IMMEDIATE", "DELAYED", "MINOR", "EXPECTANT"]:
            if cat in ru: return cat
        return "ASSESSING"

    def auto_log_and_broadcast(self):
        from hardware.ble_simulator import execute_tool
        if self.triage_category in ["IMMEDIATE", "DELAYED", "MINOR", "EXPECTANT"]:
            execute_tool("log_triage_decision", {
                "patient_id": self.patient_id, "category": self.triage_category,
                "rationale": self.final_response[:300], "vitals": self.vitals, "confidence": 0.9
            })
        if self.triage_category == "IMMEDIATE":
            execute_tool("broadcast_evacuation_request", {
                "patient_id": self.patient_id, "priority": 1,
                "condition_summary": self.final_response[:100]
            })

    def speak_result(self):
        try:
            from core.audio import get_triage_phrase, speak_text
            phrase = get_triage_phrase(self.triage_category, self.detected_lang)
            speak_text(phrase)
        except: pass

    def run(self, text_input="", image_path=None, use_voice=False, voice_duration=8, speak_output=True) -> dict:
        elapsed_start = time.time()
        if use_voice:
            self.transcript = self.collect_voice_input(voice_duration)
            patient_input = self.transcript if self.transcript else text_input
        else:
            patient_input = text_input

        if image_path: self.collect_image_input(image_path)
        self.retrieve_protocols(patient_input)
        self.final_response = self.run_agent_loop(patient_input)
        self.triage_category = self.extract_category(self.final_response)
        self.auto_log_and_broadcast()
        if speak_output: self.speak_result()

        res = {
            "patient_id": self.patient_id, "triage_category": self.triage_category,
            "response": self.final_response, "tools_called": self.tools_called,
            "vitals": self.vitals, "rag_used": bool(self.rag_context),
            "image_analyzed": bool(self.vision_summary), "elapsed_seconds": round(time.time()-elapsed_start, 1),
            "detected_language": self.detected_lang
        }
        self.display_result(res)
        return res

    def display_result(self, result: dict):
        color = "red" if result["triage_category"] == "IMMEDIATE" else "yellow" if result["triage_category"] == "DELAYED" else "green"
        console.print(Panel(Markdown(result["response"]), title=f"[bold {color}]TRIAGE: {result['triage_category']}[/bold {color}]", border_style=color))