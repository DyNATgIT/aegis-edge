<p align="center">

<svg width="100%" height="320" viewBox="0 0 1200 320" xmlns="http://www.w3.org/2000/svg">

  <defs>

    <!-- Background -->
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#050816"/>
      <stop offset="50%" stop-color="#0a1026"/>
      <stop offset="100%" stop-color="#07131f"/>
    </linearGradient>

    <!-- Neon Glow -->
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="18" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Glass -->
    <linearGradient id="glass" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="rgba(255,255,255,0.18)"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0.04)"/>
    </linearGradient>

    <!-- Grid Pattern -->
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(0,255,255,0.08)" stroke-width="1"/>
    </pattern>

  </defs>

  <!-- Background -->
  <rect width="1200" height="320" fill="url(#bg)"/>

  <!-- Grid -->
  <rect width="1200" height="320" fill="url(#grid)"/>

  <!-- Neon Orbs -->
  <circle cx="250" cy="90" r="120" fill="#00e5ff" opacity="0.22" filter="url(#glow)"/>
  <circle cx="950" cy="220" r="140" fill="#0066ff" opacity="0.22" filter="url(#glow)"/>

  <!-- Decorative Lines -->
  <line x1="140" y1="70" x2="320" y2="70" stroke="#00f0ff" stroke-width="2" opacity="0.7"/>
  <line x1="880" y1="250" x2="1060" y2="250" stroke="#00f0ff" stroke-width="2" opacity="0.7"/>

  <!-- Glass Panel -->
  <rect x="140" y="60"
        width="920"
        height="200"
        rx="28"
        fill="url(#glass)"
        stroke="rgba(0,255,255,0.35)"
        stroke-width="1.5"/>

  <!-- Neon Border Glow -->
  <rect x="140" y="60"
        width="920"
        height="200"
        rx="28"
        fill="none"
        stroke="#00e5ff"
        stroke-width="2"
        opacity="0.7"
        filter="url(#glow)"/>

  <!-- Small Tech Dots -->
  <circle cx="190" cy="100" r="4" fill="#00f0ff"/>
  <circle cx="205" cy="100" r="4" fill="#00f0ff" opacity="0.7"/>
  <circle cx="220" cy="100" r="4" fill="#00f0ff" opacity="0.4"/>

  <!-- Main Title -->
  <text x="600"
        y="145"
        text-anchor="middle"
        font-size="68"
        font-family="Segoe UI, Orbitron, sans-serif"
        font-weight="700"
        letter-spacing="6"
        fill="#dffcff"
        filter="url(#glow)">
    AEGIS EDGE
  </text>

  <!-- Subtitle -->
  <text x="600"
        y="190"
        text-anchor="middle"
        font-size="22"
        font-family="Segoe UI, sans-serif"
        letter-spacing="2"
        fill="rgba(220,245,255,0.85)">
    NEXT‑GENERATION EDGE SECURITY FRAMEWORK
  </text>

  <!-- Bottom Accent -->
  <line x1="420" y1="220" x2="780" y2="220"
        stroke="#00e5ff"
        stroke-width="2"
        opacity="0.8"/>

</svg>

</p>
## *Sovereign Medical Intelligence for the Zero-Internet Frontier*
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

