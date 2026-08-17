# AI-Based Handwritten Medicine Recognition & Continuous Learning System

An end-to-end healthcare decision-support system featuring:
* **SOTA Handwritten Medicine Recognition**: EfficientNetB0 achieving **83.91% test accuracy** across 78 handwritten medicine classes.
* **Generic Medicine Identification**: Automatic lookup from brand names to verified generic chemical formulations.
* **3-Tiered Confidence & Priority Queue**: Categorizes predictions into `HIGH`, `MEDIUM`, and `LOW` confidence, assigning review priorities (`LOW`, `MEDIUM`, `HIGH`).
* **Human-in-the-Loop Doctor Review**: Captures doctor confirmations, corrections, and Out-of-Distribution (OOD) brand feedback without overwriting original AI predictions.
* **Secure Time-Limited Tokens**: Generates 24-hour cryptographic review URLs (`/review/{token}`).
* **Verified Dataset Accumulation**: Builds doctor-verified datasets under `data/doctor_verified/`.
* **Admin Training Dashboard & Sample Gates**: Enforces minimum sample thresholds (`MIN_NEW_SAMPLES`) and training locks.
* **Cloud Retraining & GitHub Actions**: Provider-independent background retraining without requiring your PC to stay ON.
* **Model Evaluation Gate & Rollback Registry**: Automatic performance gating and one-click model version rollbacks.
* **Production FastAPI Backend**: REST API web service.

---

## 🚀 Quick Start

### 1. Installation
```bash
git clone <your-repository-url>
cd <repository-folder>
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run All Tests
```bash
python tests/test_full_system_integration.py
```

### 3. Launch FastAPI Server
```bash
uvicorn src.app:app --reload --port 8000
```
Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser for interactive API documentation.

---

## 🛠 Project Structure

```text
├── src/
│   ├── predictor.py         # EfficientNetB0 core predictor & letterboxing
│   ├── confidence.py        # 3-tiered safety rules & review priority evaluator
│   ├── medicine_mapping.py  # Brand-to-generic formulation lookup
│   ├── doctor_feedback.py   # Doctor feedback manager & audit schema
│   ├── review_tokens.py     # Secure URL token generator & resolver
│   ├── verified_dataset.py  # Verified training dataset cataloger
│   ├── admin_dashboard.py   # Admin dashboard & sample gate controller
│   ├── training.py          # Cloud-compatible retraining pipeline
│   ├── model_registry.py    # Candidate evaluation gate & rollback registry
│   └── app.py               # Complete FastAPI REST API backend
├── models/
│   ├── efficientnetb0_best.keras # Production model (83.91% accuracy)
│   ├── v3_label_encoder.pkl      # 78-class encoder
│   └── model_registry.json       # Version registry
├── data/
│   └── medicine_mapping.csv # Mapped brand and generic formulations
├── tests/                   # Phase verification test suites
│   └── test_full_system_integration.py
└── .github/workflows/
    └── cloud_training.yml   # GitHub Actions cloud retraining workflow
```

---

## 📄 License & Disclaimer
This system is developed as a healthcare decision-support and research prototype. It is **NOT** a clinically safe autonomous prescribing system.
