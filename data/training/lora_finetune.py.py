import os
import sys
import json
import gc
from pathlib import Path

import torch

# ── Configuration ─────────────────────────────────────────────

# Recommended for T4 GPU
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

DATASET_PATH = "data/training/aegis_triage_train.jsonl"
OUTPUT_DIR = "adapters/aegis-lora-v1"

HF_TOKEN_PATH = ".env"

# ── LoRA Hyperparameters ──────────────────────────────────────

LORA_RANK = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05

# ── Training Hyperparameters ──────────────────────────────────

EPOCHS = 3
BATCH_SIZE = 1
GRAD_ACCUM = 4
LEARNING_RATE = 2e-4
MAX_SEQ_LEN = 512


# ── Utilities ─────────────────────────────────────────────────

def load_hf_token():
    """Load HuggingFace token from .env or environment."""
    env_path = Path(HF_TOKEN_PATH)

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("HF_TOKEN="):
                    return line.split("=", 1)[1].strip()

    return os.environ.get("HF_TOKEN")


def check_gpu():
    """Check GPU availability."""
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9

        print(f"GPU  : {name}")
        print(f"VRAM : {vram:.1f} GB")

        if vram < 10:
            print("WARNING: Low VRAM detected")

        return True

    print("No GPU detected")
    return False


# ── Main Training Function ────────────────────────────────────

def train():

    from datasets import Dataset

    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        BitsAndBytesConfig,
        TrainingArguments,
    )

    from peft import (
        LoraConfig,
        get_peft_model,
        prepare_model_for_kbit_training,
        TaskType,
    )

    from trl import SFTTrainer

    print("=" * 60)
    print("AEGIS EDGE — LoRA Fine-Tuning")
    print("=" * 60)
    print()

    # ── Environment Check ─────────────────────────────────────

    print("Checking environment...")
    has_gpu = check_gpu()
    print()

    hf_token = load_hf_token()

    if hf_token:
        print("HF Token loaded")
    else:
        print("HF Token not found")
        print("Model downloads may be rate-limited")

    print()

    # ── Dataset Check ─────────────────────────────────────────

    dataset_path = Path(DATASET_PATH)

    if not dataset_path.exists():
        print(f"Dataset not found: {DATASET_PATH}")
        sys.exit(1)

    print("Loading dataset...")

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = [json.loads(line) for line in f]

    dataset = Dataset.from_list(data)

    print(f"Examples loaded: {len(dataset)}")
    print()

    # ── Quantization Setup ────────────────────────────────────

    print("Configuring 4-bit quantization...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    # ── Tokenizer ─────────────────────────────────────────────

    print("Loading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        token=hf_token,
        trust_remote_code=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    tokenizer.padding_side = "right"

    print(f"Tokenizer vocab size: {tokenizer.vocab_size}")
    print()

    # ── Model ─────────────────────────────────────────────────

    print("Loading base model...")
    print("First run may take several minutes")
    print()

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16,
        token=hf_token,
        trust_remote_code=True,
        attn_implementation="eager",
    )

    model.config.use_cache = False

    if has_gpu:
        used_vram = torch.cuda.memory_allocated(0) / 1e9
        print(f"VRAM used after load: {used_vram:.1f} GB")

    print()

    # ── Prepare Model for QLoRA ───────────────────────────────

    print("Preparing model for QLoRA training...")

    model = prepare_model_for_kbit_training(model)

    # ── LoRA Config ───────────────────────────────────────────

    compatible_modules = [
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
    ]

    print("Applying LoRA adapters...")
    print(f"Target modules: {compatible_modules}")

    lora_config = LoraConfig(
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        target_modules=compatible_modules,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )

    model = get_peft_model(model, lora_config)

    print()
    model.print_trainable_parameters()
    print()

    # ── Output Directory ──────────────────────────────────────

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # ── Training Arguments ────────────────────────────────────

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,

        num_train_epochs=EPOCHS,

        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,

        learning_rate=LEARNING_RATE,

        warmup_steps=5,

        logging_steps=1,

        save_strategy="epoch",

        fp16=True,

        gradient_checkpointing=True,

        optim="paged_adamw_8bit",

        report_to="none",

        remove_unused_columns=True,

        dataloader_pin_memory=False,
    )

    print("Training Configuration")
    print("-" * 40)

    print(f"Model                : {MODEL_ID}")
    print(f"Epochs               : {EPOCHS}")
    print(f"Batch Size           : {BATCH_SIZE}")
    print(f"Gradient Accum       : {GRAD_ACCUM}")
    print(f"Effective Batch Size : {BATCH_SIZE * GRAD_ACCUM}")
    print(f"Learning Rate        : {LEARNING_RATE}")
    print(f"Max Sequence Length  : {MAX_SEQ_LEN}")
    print(f"Output Directory     : {OUTPUT_DIR}")

    print()
    print("Estimated T4 runtime: ~5–20 minutes")
    print()

    # ── Trainer ───────────────────────────────────────────────

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
        packing=False,
        args=training_args,
    )

    # ── Training ──────────────────────────────────────────────

    print("=" * 60)
    print("Starting Training")
    print("=" * 60)
    print()

    result = trainer.train()

    print()
    print("=" * 60)
    print("Training Complete")
    print("=" * 60)

    print(f"Final Loss : {result.training_loss:.4f}")
    print(f"Steps      : {result.global_step}")

    runtime = result.metrics.get("train_runtime", 0)

    print(f"Runtime    : {runtime:.0f} seconds")
    print()

    # ── Save Adapter ──────────────────────────────────────────

    print(f"Saving adapter to: {OUTPUT_DIR}")

    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    saved_files = list(Path(OUTPUT_DIR).glob("*"))

    total_size = (
        sum(f.stat().st_size for f in saved_files)
        / (1024 * 1024)
    )

    print()
    print(f"Saved {len(saved_files)} files")
    print(f"Total size: {total_size:.1f} MB")
    print()

    for f in sorted(saved_files):
        size_kb = f.stat().st_size // 1024
        print(f"{f.name:<35} {size_kb:>8} KB")

    # ── Cleanup ───────────────────────────────────────────────

    print()
    print("Cleaning up memory...")

    del trainer
    del model

    gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print()
    print("=" * 60)
    print("LoRA Fine-Tuning Complete")
    print("=" * 60)

    print(f"Adapter saved at:")
    print(Path(OUTPUT_DIR).resolve())


# ── Entry Point ───────────────────────────────────────────────

if __name__ == "__main__":
    train()