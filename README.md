<p align="center">
  <img width="100%" src="https://capsule-render.vercel.app/api?type=rect&height=300&color=0b0e14&text=AEGIS%20EDGE&fontSize=90&fontColor=ffffff&fontAlignY=35&desc=Sovereign%20Medical%20Intelligence%20for%20the%20Zero-Internet%20Frontier&descAlignY=58&descSize=20&descColor=60e3ff&stroke=ffffff&strokeWidth=1">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/DEVELOPED_BY-TEAM_FRONTIER_MERCY-ffffff?style=for-the-badge&labelColor=004e92&color=00e5ff" />
</p>

<p align="center">
  <br>
  <i>"Sovereign Medical Intelligence for the Zero-Internet Frontier"</i>
  <br>
  <strong>Developed by Team Frontier Mercy</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/MISSION-CRITICAL-red?style=flat-square" />
  <img src="https://img.shields.io/badge/OFFLINE-ENABLED-green?style=flat-square" />
  <img src="https://img.shields.io/badge/ENCRYPTION-ZERO_TRUST-blue?style=flat-square" />
</p>

---

<p align="center">
  <img src="https://img.shields.io/badge/Model-Gemma%204%20E4B-blue?style=for-the-badge" alt="Gemma 4">
  <img src="https://img.shields.io/badge/Deployment-Edge--Native-green?style=for-the-badge" alt="Edge Native">
  <img src="https://img.shields.io/badge/Protocol-WHO%20START-red?style=for-the-badge" alt="WHO START">
  <img src="https://img.shields.io/badge/Status-Competition%20Ready-gold?style=for-the-badge" alt="Ready">
</p>

---

## 🌌 THE VISION
In the immediate aftermath of a catastrophe, the first 60 minutes—**The Golden Hour**—determine survival. In these zones, the internet is dead, the grid is silent, and medics are overwhelmed.

**Team Frontier Mercy** created **Aegis-Edge** to solve the "Silence of the Frontier." It is not a chatbot; it is a **Sovereign Medical Agent**. Deployed on a ruggedized edge tablet, it sees, hears, and reasons using authoritative WHO protocols to ensure that no patient is mis-triaged due to human fatigue or language barriers.

---

## 🚀 CORE CAPABILITIES

### 🧠 I. Clinically Grounded Reasoning (RAG)
Aegis-Edge eliminates "AI guessing" by utilizing a **Local RAG (Retrieval-Augmented Generation)** pipeline.
- **Knowledge Base:** Fully embedded WHO START and Pediatric triage protocols via **ChromaDB**.
- **Evidence-Based:** Every decision is cited directly from the protocol, preventing hallucinations.
- **Zero-Latency:** 100% offline retrieval for split-second decision support.

### 👁️ II. Multimodal Vision Analysis
Equipped with the **Gemma 4 Vision Encoder**, the agent "sees" the injury to quantify severity.
- **Wound Classification:** Distinguishes between superficial, partial, and full-thickness burns.
- **Risk Detection:** Automatically flags **Inhalation Injury** by analyzing facial singeing and soot.
- **TBSA Estimation:** Implements the "Rule of Nines" to calculate burn surface area for fluid resuscitation.

### 🎙️ III. Multilingual Voice Interface
A hands-free loop designed for the chaos of a disaster site.
- **Sovereign Transcription:** Offline **OpenAI Whisper** for real-time speech-to-text.
- **Auto-Detection:** Instant detection of patient language (Arabic, Turkish, Spanish, French, etc.).
- **Patient Communication:** TTS (Text-to-Speech) outputs critical triage phrases in the patient's native tongue.

### 🔧 IV. Hardware Tool Integration (The "Hands")
Aegis-Edge interacts with the physical world through a native tool-registry.
- **BLE Medical Sensors:** Real-time SpO2 and Heart Rate monitoring.
- **LoRa Mesh Radio:** Priority 1 evacuation broadcasts via 868MHz network (Zero-Internet).
- **Medical DB:** Offline drug interaction and dosage verification.

---

## 🛠️ TECHNICAL ARCHITECTURE

### The Stack
| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Brain** | `Gemma 4 E4B` | Domain-Adapted via LoRA |
| **Memory** | `ChromaDB` | WHO Protocol Vector Store |
| **Senses** | `Whisper` + `mmproj` | Offline Audio & Vision |
| **Interface** | `Streamlit` | Tactical Dark Dashboard |
| **Backend** | `llama-cpp-python` | CUDA/CPU Hardware Acceleration |

### Domain Adaptation (LoRA)
To transform a general LLM into a triage expert, **Team Frontier Mercy** implemented Parameter-Efficient Fine-Tuning (PEFT). We trained the model on "Golden Examples" of WHO reasoning, creating a clinical reflex:
`Observation` $\rightarrow$ `Protocol Step` $\rightarrow$ `Threshold Check` $\rightarrow$ `Category`

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

### 1. Environment Setup
```powershell
git clone https://github.com/YOUR_USERNAME/aegis-edge.git
cd aegis-edge
# Activate your venv and install
pip install -r requirements.txt
```

### 2. Launch the Intelligence
Start the Ollama server (or load GGUF weights) and run the dashboard:
```powershell
streamlit run ui/app.py
```

---

## 👥 THE TEAM: FRONTIER MERCY
**Aayu Wadhwani & Keshav Bhatnagar**  
*Engineering the future of edge-native medical intelligence.*

👉 **[Kaggle Research Notebook](https://www.kaggle.com/code/aayuwadhwani/aegis-edge-autonomous-field-medic)** | **[Project Repository](https://github.com/DyNATgIT/aegis-edge)**
```

