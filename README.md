# 🛡️ AEGIS-EDGE: Autonomous Field Triage Assistant
**"Sovereign Medical Intelligence for the Zero-Internet Frontier"**

**Developed by Team Frontier Mercy**

[![Model: Gemma 4 E4B](https://img.shields.io/badge/Model-Gemma%204%20E4B-blue)](https://huggingface.co/google)
[![Deployment: Edge Native](https://img.shields.io/badge/Deployment-Edge--Native-green)](#)
[![Protocol: WHO START](https://img.shields.io/badge/Protocol-WHO%20START-red)](https://www.who.int)
[![Status: Competition Ready](https://img.shields.io/badge/Status-Competition%20Ready-gold)](#)

---

## 🌌 THE VISION
In a mass-casualty disaster zone, the first 60 minutes (The Golden Hour) determine survival. Medics are overwhelmed, internet is non-existent, and language barriers are critical. 

**Team Frontier Mercy** created Aegis-Edge to solve the "Silence of the Frontier." It is a sovereign medical agent deployed on a ruggedized tablet that sees, hears, and reasons using authoritative WHO protocols to ensure that no patient is mis-triaged due to human fatigue or linguistic gaps.

---

## 🚀 CORE CAPABILITIES

### 🧠 1. Clinically Grounded Reasoning (RAG)
Aegis-Edge does not "guess." It utilizes a **Local RAG (Retrieval-Augmented Generation)** pipeline powered by **ChromaDB**. 
- **Knowledge Base:** Fully embedded WHO START and Pediatric triage protocols.
- **Evidence-Based:** Every triage decision is cited from the protocol, preventing AI hallucinations.
- **Zero-Latency:** 100% offline retrieval for instant decision support.

### 👁️ 2. Multimodal Vision Analysis
Integrated **Gemma 4 Vision Encoder** allowing the agent to "see" the patient.
- **Wound Classification:** Distinguishes between superficial, partial, and full-thickness burns.
- **Risk Detection:** Automatically flags **Inhalation Injury** by analyzing facial singeing and soot.
- **TBSA Estimation:** Uses a visual "Rule of Nines" to estimate burn surface area for fluid calculations.

### 🎙️ 3. Multilingual Voice Interface
A complete audio loop for hands-free operation in high-stress environments.
- **Sovereign Transcription:** Offline **OpenAI Whisper** for real-time speech-to-text.
- **Auto-Detection:** Detects patient language (Arabic, Turkish, Spanish, etc.) on the fly.
- **Patient Communication:** Text-to-Speech (TTS) outputs critical triage phrases in the patient's native tongue to maintain calm and cooperation.

### 🔧 4. Hardware Tool Integration (The "Hands")
Aegis-Edge interfaces with simulated BLE medical hardware to remove human error from vital signs.
- **Pulse Oximetry:** Real-time SpO2 and Heart Rate monitoring.
- **Thermometry:** Core body temperature tracking.
- **LoRa Radio:** Priority 1 evacuation broadcasts via 868MHz mesh network (Zero-Internet).
- **Medical DB:** Offline drug interaction and dosage checker.

---

## 🛠️ TECHNICAL ARCHITECTURE

### The Stack
- **LLM:** Gemma 4 E4B (Domain-Adapted via LoRA)
- **Vector DB:** ChromaDB (Sentence-Transformers EmbedL6)
- **Audio:** Whisper (Base) $\rightarrow$ Pyttsx3 (TTS)
- **Vision:** Multimodal Projector (mmproj)
- **UI:** Streamlit Tactical Dashboard
- **Backend:** Python 3.11 $\rightarrow$ llama-cpp-python (CUDA/CPU)

### Domain Adaptation (LoRA)
To move from "General AI" to "Triage Expert," **Team Frontier Mercy** implemented Parameter-Efficient Fine-Tuning (PEFT). By training on "Golden Examples" of WHO START reasoning, the model learned a specific clinical "reflex":
`Observation $\rightarrow$ Protocol Step $\rightarrow$ Threshold Check $\rightarrow$ Category`

---

## 📂 PROJECT STRUCTURE
```text
aegis-edge/
├── core/                # The Brain (Model, RAG, Agent, Vision, Audio)
├── hardware/            # The Hands (BLE Simulators, SQLite Logs)
├── data/                # The Knowledge (WHO Protocols, Test Assets)
├── adapters/             # LoRA Weights (Domain Adaptation)
├── ui/                  # The Face (Streamlit Dashboard)
├── tests/               # The Proof (Integration & Unit Tests)
└── demo.py              # One-Command Showcase
```

---

## 🏁 QUICK START
1. **Clone & Env:** 
   `git clone https://github.com/DyNATgIT/aegis-edge.git`
   `pip install -r requirements.txt`
2. **Launch Backend:** Start Ollama or load GGUF weights.
3. **Start Dashboard:** 
   `streamlit run ui/app.py`

---

## 👥 THE TEAM: FRONTIER MERCY
**Aayu Wadhwani & Keshav Bhatnagar**
*Developing the future of edge-native medical intelligence.*

[Kaggle Research Notebook](https://www.kaggle.com/code/aayuwadhwani/aegis-edge-autonomous-field-medic) | [GitHub Repository](https://github.com/DyNATgIT/aegis-edge)