<p align="center">

<svg width="100%" height="280" viewBox="0 0 1000 280" xmlns="http://www.w3.org/2000/svg">

  <!-- Definitions -->
  <defs>
    <!-- Dark Tech Background -->
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a0e27"/>
      <stop offset="50%" stop-color="#0d1b2a"/>
      <stop offset="100%" stop-color="#1b263b"/>
    </linearGradient>

    <!-- Neon Blue Glass Gradient -->
    <linearGradient id="glassGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="rgba(0, 194, 255, 0.25)"/>
      <stop offset="100%" stop-color="rgba(0, 112, 243, 0.1)"/>
    </linearGradient>

    <!-- Neon Glow -->
    <filter id="glow">
      <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <!-- Blur for orbs -->
    <filter id="blur">
      <feGaussianBlur stdDeviation="20" />
    </filter>
  </defs>

  <!-- Background -->
  <rect width="1000" height="280" fill="url(#bgGradient)" />

  <!-- Animated Neon Orbs -->
  <circle cx="150" cy="100" r="80" fill="#00c2ff" filter="url(#blur)" opacity="0.5">
    <animate attributeName="opacity" values="0.5;0.8;0.5" dur="3s" repeatCount="indefinite"/>
  </circle>
  <circle cx="850" cy="200" r="100" fill="#0070f3" filter="url(#blur)" opacity="0.4">
    <animate attributeName="opacity" values="0.4;0.7;0.4" dur="4s" repeatCount="indefinite"/>
  </circle>
  <circle cx="500" cy="50" r="60" fill="#00f2fe" filter="url(#blur)" opacity="0.3">
    <animate attributeName="opacity" values="0.3;0.6;0.3" dur="5s" repeatCount="indefinite"/>
  </circle>

  <!-- Grid Pattern (Tech Vibe) -->
  <defs>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(0, 194, 255, 0.1)" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="1000" height="280" fill="url(#grid)" />

  <!-- Glass Panel with Neon Border -->
  <rect x="120" y="70" rx="20" ry="20" width="760" height="150"
        fill="url(#glassGradient)"
        stroke="#00c2ff"
        stroke-width="2"
        filter="url(#glow)"
        opacity="0.95"/>

  <!-- Inner Glow Line -->
  <rect x="125" y="75" rx="17" ry="17" width="750" height="140"
        fill="none"
        stroke="rgba(0, 242, 254, 0.3)"
        stroke-width="1"/>

  <!-- AEGIS EDGE Title -->
  <text x="500" y="135"
        text-anchor="middle"
        font-size="68"
        font-family="'Arial Black', sans-serif"
        fill="#00f2fe"
        font-weight="900"
        letter-spacing="8"
        filter="url(#glow)">
    AEGIS EDGE
  </text>

  <!-- Tech Accent Line -->
  <line x1="280" y1="155" x2="720" y2="155" 
        stroke="#00c2ff" 
        stroke-width="2" 
        opacity="0.6"/>

  <!-- Subtitle -->
  <text x="500" y="185"
        text-anchor="middle"
        font-size="18"
        font-family="'Segoe UI', Tahoma, sans-serif"
        fill="#4cc9f0"
        letter-spacing="4"
        font-weight="300">
    NEXT‑GENERATION EDGE SECURITY FRAMEWORK
  </text>

  <!-- Corner Tech Details -->
  <circle cx="140" cy="90" r="3" fill="#00f2fe" opacity="0.8"/>
  <circle cx="860" cy="200" r="3" fill="#00f2fe" opacity="0.8"/>
  <rect x="135" y="208" width="20" height="2" fill="#00c2ff" opacity="0.5"/>
  <rect x="845" y="82" width="20" height="2" fill="#00c2ff" opacity="0.5"/>

</svg>

</p>

---

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-00c2ff.svg?style=for-the-badge&logo=opensourceinitiative&logoColor=white&labelColor=0a0e27)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-1.0.0-0070f3.svg?style=for-the-badge&logo=github&labelColor=0a0e27)](https://github.com/DyNATgIT/aegis-edge)
[![Status](https://img.shields.io/badge/Status-Active-00f2fe.svg?style=for-the-badge&logo=statuspage&labelColor=0a0e27)](https://github.com/DyNATgIT/aegis-edge)

</div>
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

