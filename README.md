# 🛡️ AEGIS-EDGE: Emergency Field Triage Assistant
**Deployed on Edge Devices for Zero-Internet Disaster Zones**

## 🌟 Project Vision
Aegis-Edge is a multimodal AI agent designed for first responders in mass casualty events. It replaces vague medical guessing with **authoritative WHO START protocols**, grounding every decision in real-time hardware data and official guidelines.

## 🚀 Technical Architecture
- **Core LLM:** Gemma 4 E4B (Quantized)
- **Inference:** Ollama / llama-cpp-python (Native Windows support)
- **RAG Pipeline:** ChromaDB Vector Store + Sentence-Transformers
- **Vision:** Multimodal projector (mmproj) for wound and burn analysis
- **Audio:** OpenAI Whisper (Offline) + pyttsx3 TTS
- **Hardware:** Simulated BLE Medical Suite (Pulse Ox, Thermometer, GPS, LoRa)

## 🛠️ Key Features
- [x] **Autonomous Tool Use:** Model decides when to read vitals or check drug interactions.
- [x] **WHO-Grounded RAG:** Every triage decision is cited from official WHO protocols.
- [x] **Multimodal Triage:** Combines Voice $\rightarrow$ Vision $\rightarrow$ Vitals $\rightarrow$ Logic.
- [x] **Multilingual Support:** Native transcription and spoken output in 6+ languages.
- [x] **Privacy First:** 100% offline execution. No data leaves the device.

## 📂 Project Structure
- `/core`: The brain (RAG, Model, Agent Loop, Vision, Audio)
- `/hardware`: BLE device simulators and database logic
- `/data`: WHO Protocol knowledge base and test assets
- `/tests`: Comprehensive unit and integration tests
- `/models`: Model weights and multimodal projectors

## 📈 Setup & Execution
1. Install dependencies: `pip install -r requirements.txt`
2. Start Ollama server: `ollama run gemma4:e4b`
3. Run the full pipeline: `python tests/test_agent_day2.py` (or `test_rag_day3.py`, `test_vision_day4.py`)