# 🔥 Fire & Smoke Detection — Agentic RAG System

A deep learning pipeline that detects fire and smoke with **YOLOv8 segmentation**, then triggers an **Agentic RAG** decision loop to recommend suppression actions, log incidents, and serve data through a REST API.

---

## 🗂️ Project Structure

```
Fire and Smoke Detection/
│
├── best.pt                        # Trained YOLOv8 model (detection + segmentation)
│
├── real_rag_system.py             # ✅ TRUE RAG — FAISS + vector embeddings (SentenceTransformers)
├── fire_agent.py                  # Agentic loop — Groq LLM + tool use
├── fire_backend.py                # FastAPI backend — incidents, zones, SQLite DB
│
├── test_agent.py                  # End-to-end integration test
├── test_backend.py                # Backend unit test
│
├── fire_system.db                 # SQLite database (auto-created)
├── rag_documents/
│   └── documents.json             # Generated fire safety knowledge base
├── detection_images/              # Output images from detection events
│
├── final_fire_labels.zip          # Training dataset labels
├── fire_seg_final_results.zip     # YOLOv8 segmentation results
│
├── Fire.mp4                       # Demo video 1
├── Fire2.mp4                      # Demo video 2
│
├── .env                           # ⚠️  API keys — DO NOT commit to Git
├── .gitignore
│
└── _archive/                      # Old files kept for reference
    ├── last.pt                    # Last epoch weights (best.pt is preferred)
    ├── fire_rag_system.py         # Old keyword-only RAG (replaced by real_rag_system.py)
    ├── Fire.avi / Fire2.avi       # Duplicate videos (.mp4 versions kept)
    ├── test_fre.avi               # Raw test footage
    ├── README_v1_backend_setup.md
    ├── README_v2_agentic_rag.md
    └── README_v3_learning_guide.md
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DETECTION LAYER                          │
│   best.pt (YOLOv8)                                          │
│   Input: Video / Image frame                                │
│   Output: Bounding boxes + segmentation masks               │
└────────────────────────┬────────────────────────────────────┘
                         │ zone_id, coordinates, segment_area
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENTIC LAYER  (fire_agent.py)           │
│                                                             │
│   1. query_zone_procedure(zone_id)                          │
│   2. get_suppression_info(zone_id)                          │
│   3. query_rag(query)  ──►  real_rag_system.py             │
│   4. activate_suppression(zone_id, type, reason)            │
│   5. log_incident(...)                                      │
│                                                             │
│   LLM: Groq (Llama 3.1 70B) — loaded from .env             │
└────────────────────────┬────────────────────────────────────┘
                         │ incidents, decisions
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG LAYER  (real_rag_system.py)          │
│                                                             │
│   SentenceTransformers → 384-dim embeddings                 │
│   FAISS IndexFlatL2 → semantic nearest-neighbor search      │
│   Documents: NFPA 101, NFPA 13, NFPA 72, OSHA, Zone procs  │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND LAYER  (fire_backend.py)         │
│                                                             │
│   FastAPI + SQLite                                          │
│   /api/detections  /api/incidents  /api/zones               │
│   /api/dashboard/summary                                    │
│   Served on: http://localhost:8000                          │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Setup

### 1. Create virtual environment
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install fastapi uvicorn sqlalchemy pillow requests python-dotenv
pip install sentence-transformers faiss-cpu   # for real vector RAG
pip install ultralytics                        # for YOLOv8 (best.pt)
```

### 3. Configure API key
Edit `.env` and paste your Groq key (free at https://console.groq.com):
```
GROQ_API_KEY=gsk_your_key_here
```

---

## 🚀 Running the System

### Step 1 — Start the backend
```bash
python fire_backend.py
# API docs: http://localhost:8000/docs
```

### Step 2 — Run integration test (new terminal)
```bash
python test_agent.py
```

### Step 3 — Run backend test
```bash
python test_backend.py
```

---

## 🔑 Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/init/zones` | Create the 3 zones |
| POST | `/api/init/procedures` | Load safety procedures |
| POST | `/api/detections` | Log a fire detection |
| GET | `/api/detections` | Get all detections |
| POST | `/api/incidents` | Log agent decision |
| GET | `/api/incidents` | Get all incidents |
| PATCH | `/api/incidents/{id}/status` | Update incident status |
| GET | `/api/dashboard/summary` | High-level metrics |

---

## 🤖 RAG System

The project uses **true Retrieval-Augmented Generation** (not keyword matching):

| | Old (`fire_rag_system.py`) | New (`real_rag_system.py`) |
|--|--|--|
| Retrieval | Keyword matching | Vector similarity (FAISS) |
| Understanding | Exact words only | Semantic meaning |
| Example | "CO2" ≠ "carbon dioxide" | "CO2" ≈ "carbon dioxide" ✅ |
| Speed | Fast | ~1ms per query |

**Documents indexed:** NFPA 101 (Evacuation), NFPA 13 (Sprinklers), NFPA 72 (Detection), OSHA Emergency Procedures, Zone-specific protocols (Lobby, Server Room, Warehouse), Fire extinguisher classification.

---

## 🔬 Model Info

| Property | Value |
|----------|-------|
| Model | YOLOv8 (custom trained) |
| Task | Object detection + instance segmentation |
| Classes | Fire, Smoke |
| Weights | `best.pt` (best validation epoch) |
| Training labels | `final_fire_labels.zip` |
| Segmentation output | `fire_seg_final_results.zip` |

> `last.pt` (last epoch weights) is archived in `_archive/`. Always use `best.pt` for inference.

---

## ⚠️ Security Notes

- The Groq API key is loaded from `.env` — **never commit `.env` to Git**
- `.gitignore` already excludes `.env`, `*.pt`, `*.db`, and `__pycache__`

---

## 📋 Troubleshooting

| Error | Fix |
|-------|-----|
| `Address already in use` | `lsof -ti :8000 \| xargs kill -9` |
| `Database locked` | Delete `fire_system.db` and restart |
| `No module named sentence_transformers` | `pip install sentence-transformers faiss-cpu` |
| `GROQ_API_KEY not set` | Edit `.env`, add your key from console.groq.com |
| `Similarity scores low` | Adjust chunk size in `real_rag_system.py` |
