import json
import os
from pathlib import Path
from loguru import logger

ADAPTER_PATH = str(Path(".") / "adapters" / "aegis-lora-v1")

def check_adapter_exists() -> bool:
    return (Path(ADAPTER_PATH) / "adapter_config.json").exists()

def get_adapter_info() -> dict:
    config_path = Path(ADAPTER_PATH) / "adapter_config.json"
    if not config_path.exists(): return {"status": "not_found"}
    with open(config_path) as f:
        config = json.load(f)
    
    has_weights = any(Path(ADAPTER_PATH).glob("*.safetensors"))
    return {
        "status": "weights_ready" if has_weights else "config_only",
        "path": ADAPTER_PATH,
        "rank": config.get("r", "unknown"),
        "has_weights": has_weights
    }

def load_adapted_model(base_model_id: str = "google/gemma-4-e4b-it"):
    if not check_adapter_exists():
        raise FileNotFoundError("Adapter not found. Run training first.")
    
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    import torch

    bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
    base = AutoModelForCausalLM.from_pretrained(base_model_id, quantization_config=bnb_config, device_map="auto")
    model = PeftModel.from_pretrained(base, ADAPTER_PATH)
    tokenizer = AutoTokenizer.from_pretrained(ADAPTER_PATH)
    return model, tokenizer
