import os
import sys
import json
import torch
import gc
from pathlib import Path
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from trl import SFTTrainer

MODEL_ID = "google/gemma-4-e4b-pt"
DATASET_PATH = "data/training/aegis_triage_train.jsonl"
OUTPUT_DIR = "adapters/aegis-lora-v1"

def train():
    # 1. Setup Quantization for low VRAM
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16
    )

    # 2. Load Dataset
    with open(DATASET_PATH, encoding="utf-8") as f:
        data = [json.loads(line) for line in f]
    dataset = Dataset.from_list(data)

    # 3. Load Model & Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, quantization_config=bnb_config, device_map="auto"
    )

    # 4. Apply LoRA
    model = prepare_model_for_kbit_training(model)
    lora_config = LoraConfig(
        r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM
    )
    model = get_peft_model(model, lora_config)

    # 5. Train
    args = TrainingArguments(
        output_dir=OUTPUT_DIR, num_train_epochs=3, per_device_train_batch_size=1,
        gradient_accumulation_steps=4, learning_rate=2e-4, fp16=True,
        logging_steps=1, save_strategy="epoch", optim="paged_adamw_8bit"
    )

    trainer = SFTTrainer(
        model=model, tokenizer=tokenizer, train_dataset=dataset,
        dataset_text_field="text", max_seq_length=512, args=args
    )

    trainer.train()
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("✅ LoRA Adapter Saved Successfully.")

if __name__ == "__main__":
    train()
