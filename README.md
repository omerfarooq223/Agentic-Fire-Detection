# FireWatch AI: Autonomous Fire & Smoke Incident Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-00A6ED?style=for-the-badge&logo=yolo)](https://ultralytics.com/)
[![Llama 3.3](https://img.shields.io/badge/LLM-Llama_3.3_70B-818cf8?style=for-the-badge&logo=meta)](https://groq.com/)
[![Gmail API](https://img.shields.io/badge/Alerts-Gmail_API-e11d48?style=for-the-badge&logo=gmail)](https://developers.google.com/gmail/api)

FireWatch AI is a production-grade, high-fidelity monitoring ecosystem designed for autonomous fire and smoke detection. It integrates state-of-the-art computer vision (YOLOv8) with a sophisticated **Hybrid Emergency Coordinator** and a high-end Cyber HUD dashboard.

![System Demo](./demo.gif)

---

## 🚀 System Capabilities

### 1. Hybrid Emergency Response (0-Latency)
The system utilizes a dual-engine response architecture for maximum speed and intelligence:
- **Direct Response (Speed):** A pure Python engine dispatches the first critical email alert the **millisecond** a fire is detected.
- **Agentic Coordination (Intelligence):** A Llama 3.3-powered agent performs post-incident reasoning and RAG procedure lookups.
- **Precision GPS Pinpointing:** Integrates browser-level Geolocation APIs to capture **exact GPS coordinates** for "One-Click Rescue" navigation.

### 2. Cyber HUD Visual Overlay
A sophisticated, canvas-based particle engine that transforms raw video feeds into actionable intelligence with heat-maps and real-time tactical overlays.

### 3. Agentic RAG Assistant
Integrated **Retrieval-Augmented Generation (RAG)** system built on FAISS for NFPA and OSHA safety standard consultation.

---

## 📂 Project Structure

```text
.
├── fire_backend.py      # Core FastAPI Server & Frame Processing
├── fire_agent.py        # AI Management Agent (Reasoning & Alerts)
├── real_rag_system.py   # RAG Vector Search (NFPA Safety Docs)
├── models/
│   └── best.pt          # YOLOv8 Weights (Fire/Smoke)
├── frontend/            # React + Vite Tactical Dashboard
│   ├── src/
│   │   ├── App.jsx      # Dashboard Logic & GPS Capture
│   │   └── index.css    # Cyber HUD Styles
├── fire_system.db       # Incident History & Zone Database
├── credentials.json     # Google Cloud Auth (Required)
└── .env                 # API Keys & Configuration
```

---

## 🏛️ System Architecture & Data Flow

FireWatch AI is built on a modular, asynchronous architecture designed for high availability and low-latency response.

### 1. Perception Layer (Computer Vision)
- **Engine:** YOLOv8 (Segmentation Model)
- **Task:** Real-time analysis of video frames to identify fire and smoke polygons.

### 2. Hybrid Response Engine (Dual-Path)
- **Fast-Path (Pure Python):** Triggered on the very first detection frame to ensure emails are sent in < 500ms.
- **Analytical-Path (AI Agent):** Triggered in the background to initiate a multi-step reasoning loop and incident logging.

### 3. Intelligence Layer (Agentic & RAG)
- **AI Agent:** A ReAct-style agent that uses tools to interact with the system.
- **RAG System:** A FAISS vector database containing specialized fire safety procedures.

### 4. Communication Layer
- **Gmail API:** Secure OAuth2-based email dispatching using premium HTML templates.
- **Geolocation:** High-accuracy browser-based GPS capturing for pinpoint rescue.

---

## 🛠️ Setup & Configuration

### 1) Prerequisites
- Python 3.10+, Node.js 18+
- Google Cloud Console Project (Gmail API enabled)
- Groq API Key

### 2) Environment Setup (`.env`)
```env
GROQ_API_KEY=your_key_here
FIRE_DETECT_MODEL=./models/best.pt
REMINDER_EMAIL_SENDER=your_gmail@gmail.com
REMINDER_EMAIL_RECEIVERS=stakeholder1@email.com
```

### 3) Gmail API Authentication
Place `credentials.json` in the root directory and run the system once to authorize and generate `token.json`.

---

## 👤 Credits

<div align="center">
  <p>Designed and Developed with precision by</p>
  <h3><strong>Muhammad Umar Farooq</strong></h3>
  <a href="https://omerfarooq223.github.io">
    <img src="https://img.shields.io/badge/View_Portfolio-00A6ED?style=for-the-badge&logo=react&logoColor=white" alt="Portfolio" />
  </a>
  <br/><br/>
  <i>"Building the future of autonomous safety systems."</i>
</div>
