# GeoSignAI: Autonomous Multimodal Billboard Siting & Permitting Fleet

[![Google Cloud Run](https://img.shields.io/badge/Google%20Cloud-Cloud%20Run-blue?logo=googlecloud)](https://cloud.google.com/run)
[![Gemini 3.5 Flash](https://img.shields.io/badge/Gemini-3.5%20Flash-4285F4?logo=google)](https://deepmind.google/technologies/gemini/)
[![Hackathon](https://img.shields.io/badge/All%20Things%20Agentic-Devpost%202026-green)](https://allthingsagentichackathon.devpost.com/)

> **GeoSignAI** is an autonomous geospatial AI agent that turns a 6-month, manual billboard site-scouting process into a 90-second automated pipeline for the $40B Out-of-Home media market.

---

## 🌟 Key Features
- **Spatial Buffer & Spacing Math:** Enforces Texas Transportation Code § 391.031 and municipal sign codes by computing 500-foot buffer exclusion zones around existing billboard structures.
- **Multimodal Satellite Reasoning (Gemini 3.5 Flash):** Inspects high-resolution aerial imagery to detect tree canopy blockage, highway visibility cones, and utility power line access.
- **Instant Permit & Valuation Artifacts:** Automatically generates a ready-to-file Municipal Sign Permit draft and a Landowner Ground Lease Deck (PDF).
- **Interactive Dark-Mode Mission Control:** Real-time web map interface with live agent execution traces and color-coded site feasibility ratings.

---

## 🏗️ Architecture & Tech Stack

```
[Real TxDOT GIS & TCAD Parcels] ──► [Shapely 500-ft Buffer Engine] ──► [Gemini 3.5 Flash Vision] ──► [ReportLab 1-Page PDF]
                                                                                                            │
                                                                                                            ▼
                                                                                                [Google Cloud Run Container]
```

* **LLM & Vision:** Google Gemini 3.5 Flash (via Google GenAI SDK).
* **Backend:** Python 3.12, FastAPI, Shapely, ReportLab.
* **Frontend:** React, Leaflet, Tailwind CSS.
* **Cloud Infrastructure:** Google Cloud Run, Google Cloud Firestore, Google Cloud Storage.

---

## 🚀 Spin-Up Instructions (Local Development)

### 1. Clone & Install
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Tests
```bash
python test_spatial.py   # Tests 500-ft buffer math & zoning filters
python test_vision.py    # Tests Gemini 3.5 Flash multimodal vision
python test_pdf.py       # Tests 1-page PDF generator
python test_api.py       # Tests FastAPI REST endpoints
```

### 3. Start Local Server
```bash
uvicorn main:app --reload --port 8000
```
Open **`http://localhost:8000`** in your browser!

---

## ☁️ Google Cloud Run Deployment

```bash
# Build and submit container to Google Artifact Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/geosign-ai backend/

# Deploy container to Google Cloud Run
gcloud run deploy geosign-ai \
  --image gcr.io/YOUR_PROJECT_ID/geosign-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```
