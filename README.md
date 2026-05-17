<p align="center">

<svg width="100%" height="260" viewBox="0 0 1000 260" xmlns="http://www.w3.org/2000/svg">

  <!-- Background Gradient -->
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f2027"/>
      <stop offset="50%" stop-color="#203a43"/>
      <stop offset="100%" stop-color="#2c5364"/>
    </linearGradient>

    <!-- Glass Gradient -->
    <linearGradient id="glassGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(255,255,255,0.35)"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0.05)"/>
    </linearGradient>

    <!-- Blur Effect -->
    <filter id="blur">
      <feGaussianBlur stdDeviation="15" />
    </filter>
  </defs>

  <!-- Background -->
  <rect width="1000" height="260" fill="url(#bgGradient)" />

  <!-- Blurred Light Orbs -->
  <circle cx="200" cy="80" r="100" fill="#00f2fe" filter="url(#blur)" opacity="0.4"/>
  <circle cx="800" cy="180" r="120" fill="#4facfe" filter="url(#blur)" opacity="0.4"/>

  <!-- Glass Panel -->
  <rect x="150" y="60" rx="20" ry="20" width="700" height="140"
        fill="url(#glassGradient)"
        stroke="rgba(255,255,255,0.4)"
        stroke-width="1.5"/>

  <!-- Title -->
  <text x="500" y="125"
        text-anchor="middle"
        font-size="60"
        font-family="Segoe UI, sans-serif"
        fill="white"
        font-weight="bold"
        letter-spacing="3">
    AEGIS EDGE
  </text>

  <!-- Subtitle -->
  <text x="500" y="160"
        text-anchor="middle"
        font-size="20"
        font-family="Segoe UI, sans-serif"
        fill="rgba(255,255,255,0.85)">
    Next‑Generation Edge Security Framework
  </text>

</svg>

</p>
### *Sovereign Medical Intelligence for the Zero-Internet Frontier*
**Developed by Team Frontier Mercy**

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

