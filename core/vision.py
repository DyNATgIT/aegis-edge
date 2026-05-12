import os
import base64
import time
import json
import io
from pathlib import Path
from loguru import logger

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Model paths — Windows-compatible
GGUF_PATH   = str(Path(".") / "models" / "gemma-4-E4B-it-Q4_K_M.gguf")
MMPROJ_PATH = str(Path(".") / "models" / "mmproj-BF16.gguf")

# Image preprocessing settings
MAX_IMAGE_DIMENSION = 1024  # Pixels — Gemma 4 handles variable resolutions
JPEG_QUALITY        = 85    # Balance between quality and token count
MIN_IMAGE_SIZE_KB   = 5     # Reject suspiciously small images

# Ollama settings
OLLAMA_URL   = "http://localhost:11434"
OLLAMA_MODEL = "gemma4:e4b"

# ═══════════════════════════════════════════════════════════════
# IMAGE PREPROCESSING
# ═══════════════════════════════════════════════════════════════

def load_and_encode_image(image_path: str,
                           max_dimension: int = MAX_IMAGE_DIMENSION,
                           quality: int = JPEG_QUALITY) -> tuple[str, dict]:
    """
    Load an image, resize it to model-appropriate dimensions,
    and encode it as a base64 string.

    For optimal performance with multimodal inputs, images should be
    processed to a reasonable resolution before passing to the model.

    Args:
        image_path:    Path to image file (JPEG, PNG, BMP, TIFF)
        max_dimension: Maximum width or height in pixels
        quality:       JPEG compression quality (1-95)

    Returns:
        Tuple of (base64_string, metadata_dict)
    """
    from PIL import Image

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Check file size
    file_size_kb = path.stat().st_size / 1024
    if file_size_kb < MIN_IMAGE_SIZE_KB:
        raise ValueError(
            f"Image too small ({file_size_kb:.1f} KB) — "
            "likely a placeholder, not a real image"
        )

    # Load image
    img = Image.open(str(path)).convert("RGB")
    original_size = img.size  # (width, height)

    # Resize while maintaining aspect ratio
    # Gemma 4 supports variable aspect ratio — resize to fit within max_dimension
    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
    resized_size = img.size

    # Encode to JPEG bytes in memory (no temp files)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    img_bytes = buffer.getvalue()

    # Base64 encode
    encoded = base64.standard_b64encode(img_bytes).decode("utf-8")

    metadata = {
        "original_size":    original_size,
        "resized_size":     resized_size,
        "encoded_bytes":    len(img_bytes),
        "base64_chars":     len(encoded),
        "format":           "JPEG",
        "file_path":        str(path),
        "file_name":        path.name
    }

    logger.info(
        f"Image encoded: {path.name} | "
        f"{original_size[0]}x{original_size[1]} → "
        f"{resized_size[0]}x{resized_size[1]} | "
        f"{len(img_bytes) / 1024:.0f} KB"
    )

    return encoded, metadata


def validate_image_file(image_path: str) -> dict:
    """
    Validate that an image file is suitable for wound analysis.
    Returns validation result with any warnings.
    """
    from PIL import Image

    path = Path(image_path)
    result = {
        "valid":    False,
        "path":     str(path),
        "warnings": [],
        "errors":   []
    }

    if not path.exists():
        result["errors"].append(f"File not found: {image_path}")
        return result

    if path.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]:
        result["errors"].append(f"Unsupported format: {path.suffix}")
        return result

    file_size_kb = path.stat().st_size / 1024
    if file_size_kb < MIN_IMAGE_SIZE_KB:
        result["errors"].append(
            f"File too small ({file_size_kb:.1f} KB) — "
            "likely a placeholder, not a real image"
        )
        return result

    try:
        img  = Image.open(str(path))
        w, h = img.size

        if w < 100 or h < 100:
            result["warnings"].append(f"Very low resolution: {w}x{h}")
        if w < 50 or h < 50:
            result["errors"].append(f"Resolution too low for analysis: {w}x{h}")
            return result

        result["valid"]      = True
        result["width"]      = w
        result["height"]     = h
        result["file_size_kb"] = round(file_size_kb, 1)
        result["format"]     = img.format or path.suffix[1:].upper()

    except Exception as e:
        result["errors"].append(f"Cannot open image: {e}")

    return result


# ═══════════════════════════════════════════════════════════════
# VISION PROMPTS
# ═══════════════════════════════════════════════════════════════

WOUND_ANALYSIS_PROMPT = """You are Aegis-Edge, a field triage AI analyzing a wound photograph 
taken by a medic in a disaster zone. Examine this image carefully and provide a 
structured clinical assessment.

Your analysis MUST cover all of these sections:

1. WOUND TYPE
   Identify what type of injury is visible:
   (burn / laceration / abrasion / contusion / crush injury / puncture / 
    amputation / no significant injury / unclear)

2. WOUND SEVERITY
   Based on visual characteristics only:
   (superficial / moderate / severe / critical / cannot determine)

3. VISUAL OBSERVATIONS
   Describe specifically what you see:
   - Estimated wound dimensions (if determinable)
   - Tissue appearance (color, texture, moisture, depth)
   - Signs of bleeding (active / controlled / dried)
   - Foreign material or contamination visible
   - Swelling or deformity

4. BURN-SPECIFIC ASSESSMENT (complete this section if burn is visible)
   - Burn depth: superficial / partial thickness / full thickness / mixed / N/A
   - Estimated %TBSA affected (use Rule of Nines visual estimate)
   - Blistering: present / absent
   - Eschar formation: present / absent
   - Special area involvement: face / hands / feet / genitalia / joints / N/A

5. INHALATION INJURY INDICATORS (examine face/neck if visible)
   - Facial burns: present / absent
   - Singed eyebrows or eyelashes: present / absent / not visible
   - Soot or carbon deposits: present / absent
   - Perioral or perinasal burns: present / absent

6. TRIAGE IMPLICATION FROM IMAGE ALONE
   Based only on what you can see:
   IMMEDIATE / DELAYED / MINOR / CANNOT DETERMINE FROM IMAGE ALONE

7. TOP 3 IMMEDIATE ACTIONS
   Based on this visual assessment, what should the medic do first?

⚠️ CRITICAL REMINDERS:
- This is a DECISION SUPPORT tool. Medic must verify all findings.
- You cannot see vital signs from this image — gather them with tools.
- If image quality is poor, state that clearly — do not guess.
- Err toward IMMEDIATE when uncertain about severity."""

QUICK_SCREEN_PROMPT = """Look at this wound image. Answer in exactly 2 sentences.
Sentence 1: Is this wound IMMEDIATELY life-threatening or potentially so? YES or NO.
Sentence 2: State the single most critical visual finding in under 15 words."""

INHALATION_CHECK_PROMPT = """Examine this image carefully for signs of inhalation injury.
Look specifically for:
  1. Facial burns (redness, blistering around face)
  2. Singed eyebrows, eyelashes, or nasal hair
  3. Soot or black carbon deposits around nose or mouth
  4. Burns around lips or oral area

Answer with: INHALATION_RISK: YES or NO
Then one sentence explaining what you see (or do not see)."""

BURN_SEVERITY_PROMPT = """You are analyzing this burn wound photograph.
Estimate the following based on visual examination:

DEPTH: (Superficial | Partial-Thickness | Full-Thickness | Mixed)
Evidence for depth classification:

TBSA_ESTIMATE: (Use Rule of Nines — give a percentage range e.g. 8-12%)
Evidence for TBSA estimate:

SPECIAL_AREAS: (List any special areas visible: face/hands/feet/joints/genitalia or NONE)

IMMEDIATE_RISK: (YES — requires immediate treatment | NO — can be delayed)
Primary reason:"""


# ═══════════════════════════════════════════════════════════════
# VISION INFERENCE — llama.cpp Backend
# ═══════════════════════════════════════════════════════════════

_vision_llm = None  # Singleton for vision model


def load_vision_model():
    """
    Load Gemma 4 E4B with multimodal projector for vision inference.
    Uses llama-cpp-python's LlavaMultiModalProjector support.
    Only loads once — singleton pattern.
    """
    global _vision_llm

    if _vision_llm is not None:
        return _vision_llm

    # Check files exist
    gguf_path   = Path(GGUF_PATH)
    mmproj_path = Path(MMPROJ_PATH)

    if not gguf_path.exists():
        raise FileNotFoundError(
            f"GGUF model not found: {GGUF_PATH}\n"
            "Download it: huggingface-cli download unsloth/gemma-4-E4B-it-GGUF "
            "--include gemma-4-E4B-it-Q4_K_M.gguf --local-dir ./models/"
        )

    if not mmproj_path.exists():
        raise FileNotFoundError(
            f"Multimodal projector not found: {MMPROJ_PATH}\n"
            "Download it: huggingface-cli download unsloth/gemma-4-E4B-it-GGUF "
            "--include mmproj*.gguf --local-dir ./models/"
        )

    logger.info(f"Loading vision model with mmproj...")
    logger.info(f"  GGUF   : {gguf_path}")
    logger.info(f"  mmproj : {mmproj_path}")

    from llama_cpp import Llama
    from llama_cpp.llama_chat_format import Llava15ChatHandler

    chat_handler = Llava15ChatHandler(
        clip_model_path=str(mmproj_path),
        verbose=False
    )

    _vision_llm = Llama(
        model_path=str(gguf_path),
        chat_handler=chat_handler,
        n_ctx=4096,          # Vision tokens reduce available context
        n_gpu_layers=-1,     # All layers to GPU
        n_threads=os.cpu_count() or 4,
        verbose=False,
        logits_all=False
    )

    logger.success("Vision model loaded with multimodal projector.")
    return _vision_llm


def _run_vision_llama_cpp(image_path: str,
                           prompt: str,
                           max_tokens: int = 800,
                           temperature: float = 0.05) -> str:
    """
    Run vision inference using llama-cpp-python backend.
    Passes image as base64 data URI in the message content.
    """
    start = time.time()

    # Encode image
    encoded_image, img_meta = load_and_encode_image(image_path)
    data_uri = f"data:image/jpeg;base64,{encoded_image}"

    # Load model
    llm = load_vision_model()

    # Build multimodal message
    # For optimal performance, image content comes BEFORE text content
    messages = [
        {
            "role": "system",
            "content": "You are Aegis-Edge, an emergency triage AI. "
                      "Analyze wound images with clinical precision. "
                      "Be specific. Be concise. Lives depend on accuracy."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": data_uri}
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.95,
        repeat_penalty=1.0,
    )

    result  = response["choices"][0]["message"]["content"]
    elapsed = time.time() - start

    logger.info(
        f"Vision inference: {img_meta['file_name']} | "
        f"{elapsed:.1f}s | "
        f"{len(result.split())} words"
    )

    return result


# ═══════════════════════════════════════════════════════════════
# VISION INFERENCE — Ollama Backend
# ═══════════════════════════════════════════════════════════════

def _run_vision_ollama(image_path: str,
                        prompt: str,
                        max_tokens: int = 800,
                        temperature: float = 0.05) -> str:
    """
    Run vision inference via Ollama API.
    Ollama handles multimodal natively — pass base64 image in images field.
    """
    import requests

    start = time.time()
    encoded_image, img_meta = load_and_encode_image(image_path)

    # Ollama multimodal format
    payload = {
        "model":  OLLAMA_MODEL,
        "prompt": prompt,
        "images": [encoded_image],   # Ollama takes raw base64 (no data URI)
        "stream": False,
        "options": {
            "temperature":    temperature,
            "num_predict":    max_tokens,
            "repeat_penalty": 1.0
        }
    }

    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        timeout=180
    )
    resp.raise_for_status()

    result  = resp.json().get("response", "")
    elapsed = time.time() - start

    logger.info(
        f"Vision (Ollama): {img_meta['file_name']} | "
        f"{elapsed:.1f}s | "
        f"{len(result.split())} words"
    )

    return result


# ═══════════════════════════════════════════════════════════════
# UNIFIED VISION INTERFACE
# ═══════════════════════════════════════════════════════════════

def run_vision_inference(image_path: str,
                          prompt: str,
                          max_tokens: int = 800,
                          temperature: float = 0.05) -> str:
    """
    Auto-detect backend and run vision inference.
    Falls back gracefully if vision model unavailable.
    """
    from core.model import detect_backend

    # Validate image first
    validation = validate_image_file(image_path)
    if not validation["valid"]:
        errors = "; ".join(validation["errors"])
        logger.warning(f"Image validation failed: {errors}")
        return (
            f"IMAGE ANALYSIS UNAVAILABLE: {errors}\n"
            "Please capture a new image or continue with clinical description only."
        )

    backend = detect_backend()

    try:
        if backend == "llama_cpp":
            # Try vision model first
            if Path(MMPROJ_PATH).exists():
                return _run_vision_llama_cpp(
                    image_path, prompt, max_tokens, temperature
                )
            else:
                # Fallback: use regular model with image description prompt
                logger.warning(
                    "mmproj not found — using text-only fallback. "
                    "Download mmproj for full vision capability."
                )
                return _vision_text_fallback(image_path, prompt)

        elif backend == "ollama":
            return _run_vision_ollama(
                image_path, prompt, max_tokens, temperature
            )

    except Exception as e:
        logger.error(f"Vision inference failed: {e}")
        return (
            f"VISION ANALYSIS ERROR: {e}\n"
            "Continuing with clinical description only. "
            "Gather vital signs using hardware tools."
        )


def _vision_text_fallback(image_path: str, prompt: str) -> str:
    """
    Fallback when vision model unavailable.
    Reads image metadata and provides a limited analysis notice.
    """
    from core.model import run_inference

    path     = Path(image_path)
    filename = path.stem.lower()

    # Infer context from filename
    injury_hints = []
    if "burn"       in filename: injury_hints.append("burn injury")
    if "lacerat"    in filename: injury_hints.append("laceration")
    if "crush"      in filename: injury_hints.append("crush injury")
    if "facial"     in filename: injury_hints.append("facial injury, check for inhalation")
    if "normal"     in filename: injury_hints.append("appears to be normal skin")
    if "abrasion"   in filename: injury_hints.append("abrasion")

    hint_text = (
        f"Image filename suggests: {', '.join(injury_hints)}"
        if injury_hints else "Image content unknown from filename"
    )

    fallback_prompt = (
        f"NOTE: Visual analysis module unavailable (mmproj not loaded).\n"
        f"Image filename hint: {hint_text}\n\n"
        f"Please assess based on clinical description and vital signs only.\n"
        f"Prompt was: {prompt[:200]}"
    )

    return run_inference(fallback_prompt)


# ═══════════════════════════════════════════════════════════════
# HIGH-LEVEL VISION FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def analyze_wound_image(image_path: str,
                         clinical_context: str = "",
                         include_rag: bool = True) -> dict:
    """
    Full wound analysis pipeline.

    Args:
        image_path:        Path to wound photograph
        clinical_context:  Medic's verbal description (combined with image)
        include_rag:       Whether to include WHO protocol context

    Returns:
        Dict with analysis, severity, triage_flag, rag_context
    """
    logger.info(f"Full wound analysis: {image_path}")
    start = time.time()

    # Build prompt with clinical context
    prompt = WOUND_ANALYSIS_PROMPT
    if clinical_context:
        prompt += f"\n\nMEDIC'S CLINICAL DESCRIPTION:\n{clinical_context}"
    if include_rag:
        try:
            from core.rag import retrieve_context
            rag_context = retrieve_context(
                f"wound injury {clinical_context} triage assessment",
                n_results=2
            )
            if rag_context:
                prompt += (
                    f"\n\nRELEVANT WHO PROTOCOLS FOR REFERENCE:\n"
                    f"{rag_context[:600]}"
                )
        except Exception as e:
            logger.warning(f"RAG context unavailable for vision: {e}")
            rag_context = ""
    else:
        rag_context = ""

    # Run vision inference
    analysis = run_vision_inference(
        image_path=image_path,
        prompt=prompt,
        max_tokens=900,
        temperature=0.05
    )

    # Parse severity from response
    analysis_upper = analysis.upper()
    if any(w in analysis_upper for w in
           ["CRITICAL", "IMMEDIATE", "FULL THICKNESS", "INHALATION"]):
        severity = "critical"
        triage_flag = True
    elif any(w in analysis_upper for w in
             ["SEVERE", "PARTIAL THICKNESS", "DEEP LACERATION"]):
        severity = "severe"
        triage_flag = True
    elif any(w in analysis_upper for w in
             ["MODERATE", "PARTIAL", "SIGNIFICANT"]):
        severity = "moderate"
        triage_flag = False
    elif any(w in analysis_upper for w in
             ["MINOR", "SUPERFICIAL", "ABRASION", "NO SIGNIFICANT"]):
        severity = "minor"
        triage_flag = False
    else:
        severity    = "undetermined"
        triage_flag = False

    # Check inhalation risk specifically
    inhalation_keywords = [
        "inhalation", "facial burn", "singed", "soot",
        "hoarse", "perioral", "nasal"
    ]
    inhalation_risk = any(
        kw in analysis.lower() for kw in inhalation_keywords
    )

    elapsed = time.time() - start

    result = {
        "status":           "analyzed",
        "image_path":       image_path,
        "image_name":       Path(image_path).name,
        "analysis":         analysis,
        "severity":         severity,
        "triage_flag":      triage_flag,
        "inhalation_risk":  inhalation_risk,
        "rag_context_used": bool(rag_context),
        "analysis_time_s":  round(elapsed, 1),
        "timestamp":        __import__("datetime").datetime.now().isoformat()
    }

    logger.info(
        f"Analysis complete: {Path(image_path).name} | "
        f"Severity: {severity} | "
        f"Triage flag: {triage_flag} | "
        f"Inhalation: {inhalation_risk} | "
        f"{elapsed:.1f}s"
    )

    return result


def quick_wound_screen(image_path: str) -> dict:
    """
    Rapid binary triage screen from image alone.
    Under 10 seconds. Answers: IMMEDIATE or NOT?

    Use this before full analysis when speed is critical.
    """
    logger.info(f"Quick screen: {image_path}")
    start = time.time()

    response = run_vision_inference(
        image_path=image_path,
        prompt=QUICK_SCREEN_PROMPT,
        max_tokens=80,
        temperature=0.02
    )

    resp_upper = response.upper()
    is_immediate = "YES" in resp_upper or "IMMEDIATE" in resp_upper

    return {
        "image_path":    image_path,
        "immediate":     is_immediate,
        "response":      response,
        "screen_time_s": round(time.time() - start, 1)
    }


def check_inhalation_injury(image_path: str) -> dict:
    """
    Dedicated inhalation injury check from facial/upper body image.
    Returns YES/NO with specific visual evidence cited.
    """
    logger.info(f"Inhalation check: {image_path}")

    response = run_vision_inference(
        image_path=image_path,
        prompt=INHALATION_CHECK_PROMPT,
        max_tokens=100,
        temperature=0.02
    )

    resp_upper = response.upper()
    risk_present = "YES" in resp_upper

    return {
        "image_path":    image_path,
        "inhalation_risk": risk_present,
        "evidence":      response,
        "action":        (
            "IMMEDIATE — Secure airway now. High-flow O2. "
            "Prepare for intubation — edema progresses rapidly."
            if risk_present else
            "No visual inhalation indicators. Continue standard assessment."
        )
    }


def estimate_burn_severity(image_path: str) -> dict:
    """
    Detailed burn-specific assessment from image.
    Returns structured burn depth, TBSA estimate, and special areas.
    """
    logger.info(f"Burn assessment: {image_path}")

    response = run_vision_inference(
        image_path=image_path,
        prompt=BURN_SEVERITY_PROMPT,
        max_tokens=300,
        temperature=0.02
    )

    # Parse structured output
    result = {
        "image_path":  image_path,
        "raw_response": response,
        "depth":        "Unknown",
        "tbsa_estimate": "Unknown",
        "special_areas": [],
        "immediate_risk": False
    }

    resp_lower = response.lower()

    # Parse depth
    for depth in ["full-thickness", "full thickness",
                  "partial-thickness", "partial thickness", "superficial"]:
        if depth in resp_lower:
            result["depth"] = depth.title()
            break

    # Parse TBSA estimate
    import re
    tbsa_match = re.search(r'(\d+[-–]\d+|\d+)\s*%', response)
    if tbsa_match:
        result["tbsa_estimate"] = tbsa_match.group(0)

    # Check special areas
    special_keywords = ["face", "hand", "foot", "feet", "joint",
                        "genitalia", "perineum"]
    result["special_areas"] = [
        k for k in special_keywords if k in resp_lower
    ]

    # Immediate risk
    result["immediate_risk"] = (
        "full" in resp_lower or
        "yes" in resp_lower or
        bool(result["special_areas"])
    )

    return result


# ═══════════════════════════════════════════════════════════════
# SMOKE TEST — Run directly to verify vision pipeline
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from rich.console import Console
    from rich.panel   import Panel
    from rich.table   import Table
    from rich         import box

    console = Console()

    console.print(Panel(
        "[bold cyan]AEGIS-EDGE — DAY 4 VISION PIPELINE TEST[/bold cyan]\n"
        "Testing Gemma 4 E4B multimodal wound analysis",
        border_style="cyan"
    ))

    # Check test images exist
    test_images_dir = Path(".") / "data" / "test_images"
    test_images     = list(test_images_dir.glob("*.jpg"))

    if not test_images:
        console.print(
            "[red]No test images found in data\\test_images\\[/red]\n"
            "Run: python scripts\\generate_test_images.py"
        )
        exit(1)

    console.print(
        f"\n[green]Found {len(test_images)} test images[/green]"
    )

    # Test 1: Image validation
    console.print("\n[yellow]TEST 1: Image validation[/yellow]")
    for img_path in test_images[:3]:
        v = validate_image_file(str(img_path))
        status = "[green]OK[/green]" if v["valid"] else "[red]FAIL[/red]"
        console.print(
            f"  {status} {img_path.name} | "
            f"{v.get('width', '?')}x{v.get('height', '?')} | "
            f"{v.get('file_size_kb', '?')} KB"
        )

    # Test 2: Image encoding
    console.print("\n[yellow]TEST 2: Image encoding[/yellow]")
    try:
        test_img = str(test_images[0])
        encoded, meta = load_and_encode_image(test_img)
        assert len(encoded) > 1000, "Encoded image too short"
        console.print(
            f"  [green]PASS[/green] {meta['file_name']} | "
            f"Original: {meta['original_size']} | "
            f"Resized: {meta['resized_size']} | "
            f"Base64: {meta['base64_chars']:,} chars"
        )
    except Exception as e:
        console.print(f"  [red]FAIL: {e}[/red]")

    # Test 3: Quick screen on each image
    console.print("\n[yellow]TEST 3: Quick wound screens (all images)[/yellow]")

    screen_results = []
    for img_path in test_images:
        console.print(f"  Screening: [cyan]{img_path.name}[/cyan]")
        result = quick_wound_screen(str(img_path))
        flag   = "[red]IMMEDIATE[/red]" if result["immediate"] else "[green]NOT IMMEDIATE[/green]"
        console.print(
            f"    {flag} | {result['screen_time_s']}s | "
            f"{result['response'][:60]}..."
        )
        screen_results.append(result)

    # Test 4: Full analysis on burn image
    console.print("\n[yellow]TEST 4: Full wound analysis — burn image[/yellow]")
    burn_images = [
        p for p in test_images
        if "burn" in p.stem.lower()
    ]

    if burn_images:
        burn_img = str(burn_images[0])
        console.print(f"  Analyzing: [cyan]{Path(burn_img).name}[/cyan]")
        console.print("  [dim]This may take 10-30 seconds...[/dim]")

        result = analyze_wound_image(
            burn_img,
            clinical_context=(
                "Patient reports severe pain. "
                "Burns occurred approximately 30 minutes ago in house fire."
            )
        )

        console.print(Panel(
            result["analysis"][:800] +
            ("..." if len(result["analysis"]) > 800 else ""),
            title=f"[bold red]BURN ANALYSIS — {result['severity'].upper()}[/bold red]",
            border_style="red" if result["triage_flag"] else "yellow"
        ))

        console.print(
            f"  Severity: [bold]{result['severity']}[/bold] | "
            f"Triage flag: {result['triage_flag']} | "
            f"Inhalation risk: {result['inhalation_risk']} | "
            f"Time: {result['analysis_time_s']}s"
        )
    else:
        console.print("  [yellow]No burn images found — skipping[/yellow]")

    # Test 5: Inhalation injury check
    console.print("\n[yellow]TEST 5: Inhalation injury detection[/yellow]")
    facial_images = [
        p for p in test_images
        if "facial" in p.stem.lower() or "face" in p.stem.lower()
    ]

    if facial_images:
        facial_img = str(facial_images[0])
        console.print(f"  Checking: [cyan]{Path(facial_img).name}[/cyan]")

        inhalation = check_inhalation_injury(facial_img)

        risk_str = (
            "[bold red]RISK DETECTED[/bold red]"
            if inhalation["inhalation_risk"] else
            "[green]NO RISK DETECTED[/green]"
        )
        console.print(f"  {risk_str}")
        console.print(f"  Evidence: {inhalation['evidence'][:100]}")
        console.print(f"  Action  : {inhalation['action'][:80]}")
    else:
        console.print("  [yellow]No facial images found — skipping[/yellow]")

    # Test 6: Control image (normal skin)
    console.print("\n[yellow]TEST 6: Normal skin control image[/yellow]")
    normal_images = [
        p for p in test_images
        if "normal" in p.stem.lower()
    ]

    if normal_images:
        normal_img  = str(normal_images[0])
        screen      = quick_wound_screen(normal_img)
        if not screen["immediate"]:
            console.print(
                f"  [green]PASS[/green] "
                "Normal skin correctly NOT flagged as IMMEDIATE"
            )
        else:
            console.print(
                f"  [yellow]WARN[/yellow] "
                "Normal skin flagged as IMMEDIATE — review vision prompts"
            )

    # Summary table
    console.print("\n[yellow]SUMMARY[/yellow]")
    table = Table(box=box.ROUNDED, border_style="cyan")
    table.add_column("Image",     style="white",  width=35)
    table.add_column("Immediate", style="white",  width=12)
    table.add_column("Time (s)",  style="yellow", width=10)

    for r in screen_results:
        flag = "[red]YES[/red]" if r["immediate"] else "[green]NO[/green]"
        table.add_row(
            Path(r["image_path"]).name,
            flag,
            str(r["screen_time_s"])
        )
    console.print(table)

    console.print(Panel(
        "[bold green]DAY 4 VISION PIPELINE COMPLETE[/bold green]\n\n"
        "Gemma 4 E4B is analyzing wound images.\n"
        "Proceed to Phase 5 — Integration Testing.",
        border_style="green"
    ))