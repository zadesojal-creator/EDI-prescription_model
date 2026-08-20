# System Architecture, ML Model Specifications & Workflow Documentation

## AI-Based Handwritten Medicine Recognition, Generic Medicine Identification & Human-in-the-Loop Continuous Learning System

> [!IMPORTANT]
> **Healthcare Safety Notice:** This system is designed strictly as a decision-support and research prototype. It is NOT an autonomous prescribing system and does not replace professional clinical judgment.

---

## 1. Executive Summary

This project implements an end-to-end Machine Learning and Healthcare Software Architecture that:
1. **Recognizes Handwritten Medicine Brand Names** from prescription images using **EfficientNetB0 (83.91% Accuracy)**.
2. **Maps Recognized Brands** to their verified generic chemical formulations (e.g., `Vifas` $\rightarrow$ `Fexofenadine Hydrochloride`).
3. **Evaluates 3-Tiered Confidence Levels** (`HIGH`, `MEDIUM`, `LOW`) and assigns review priorities (`LOW`, `MEDIUM`, `HIGH`).
4. **Captures Human-in-the-Loop Doctor Feedback** via secure 24-hour time-limited URL tokens (`/review/{token}`) without destroying original AI predictions.
5. **Accumulates Doctor-Verified Data** into structured catalogs for **Admin-Triggered Cloud Retraining**.
6. **Enforces Candidate Evaluation Gates & Version Rollbacks** to guarantee that new models are deployed only if performance improves.

---

## 2. ML Model Architecture & Specifications

### 2.1 Model Details
| Property | Value / Specification |
| :--- | :--- |
| **Model Architecture** | `EfficientNetB0` (Pre-trained on ImageNet, Fine-Tuned) |
| **Input Shape** | `224 x 224 x 3` (RGB) |
| **Preprocessing Strategy** | 1:1 Square White-Canvas Letterboxing (`(255, 255, 255)` padding) + LANCZOS resizing |
| **Normalization** | Internal `Rescaling(1./255)` layer |
| **Output Classes** | 78 Bengali/Global Handwritten Medicine Brand Classes |
| **Artifact Path** | `models/efficientnetb0_best.keras` (24.11 MB) |

### 2.2 Model Benchmark Metrics
* **Test Accuracy**: `83.91%`
* **Macro F1-Score**: `0.8421`
* **Weighted F1-Score**: `0.8450`
* **Top-3 Candidate Accuracy**: `96.15%`

---

## 3. End-to-End System Workflow Architecture

```mermaid
flowchart TD
    A["Uploaded Prescription Image"] --> B["1:1 Square White-Canvas Letterboxing (224x224)"]
    B --> C["EfficientNetB0 Model Inference"]
    C --> D["Top-3 Candidates & Raw Probabilities"]
    D --> E["Brand-to-Generic Mapping Lookup (data/medicine_mapping.csv)"]
    E --> F["Confidence Level Evaluator"]

    F -->|Confidence >= 0.90| G1["HIGH CONFIDENCE\nShow AI Brand Result\nQueue LOW Priority Review"]
    F -->|0.70 <= Confidence < 0.90| G2["MEDIUM CONFIDENCE\nShow Result + Verification Recommended\nQueue MEDIUM Priority Review"]
    F -->|Confidence < 0.70| G3["LOW CONFIDENCE\nMask Brand as 'Unknown'\nQueue URGENT HIGH Priority Review"]

    G1 & G2 & G3 --> H["Secure Time-Limited Token Generator (/review/{token})"]
    H --> I["Human-in-the-Loop Doctor Review Portal"]

    I -->|Doctor Confirms / Corrects| J["Doctor Feedback Audit Schema\n(Preserves Original AI Prediction)"]
    J --> K["Verified Dataset Catalog (data/doctor_verified/)"]

    K --> L{"Admin Checks Dashboard\nNew Samples >= 100?"}
    L -->|NO (e.g. 37/100)| M["Hold Training Gate\nShow 'INSUFFICIENT_NEW_DATA'"]
    L -->|YES (Admin Click)| N["Cloud Retraining Workflow (GitHub Actions)"]

    N --> O["Train Candidate Model (v2.0)"]
    O --> P{"Evaluation Gate\nCandidate Metrics > Active Production?"}
    P -->|YES| Q["APPROVE & Deploy v2.0 to Production"]
    P -->|NO| R["REJECT v2.0 & Retain Production v1.0"]
    Q --> S["Rollback Available (v2.0 -> v1.0)"]
```

---

## 4. 3-Tiered Safety & Confidence Rules

| Confidence Tier | Threshold | Status Code | UI Display Behavior | Review Priority | Doctor Verification Required |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **HIGH** | $\ge 90\%$ | `high_confidence` | Displays AI Prediction directly to user. | `LOW` | `False` |
| **MEDIUM** | $70\% - 89\%$ | `medium_confidence` | Displays AI Prediction + *"Doctor verification recommended"*. | `MEDIUM` | `False` |
| **LOW** | $< 70\%$ | `doctor_verification_required` | Masks brand as `"Unknown"`. Displays *"Doctor verification required"*. | `HIGH` | `True` |
| **UNKNOWN / OOD** | Out of 78 Classes | `unknown_ood` | Flagged when doctor identifies a brand outside the 78 known classes (`known_class = False`). | `HIGH` | `True` |

---

## 5. Generic Medicine Mapping Layer

To prevent the neural network from "guessing" chemical formulations, generic mappings are isolated into a verified reference dataset:

* **File**: `data/medicine_mapping.csv`
* **Schema**: `brand_name,generic_name,mapping_status`
* **Lookup Rules**:
  * **Verified Brand**: Returns exact active chemical formulation (e.g., `Ace` $\rightarrow$ `Paracetamol`, `Vifas` $\rightarrow$ `Fexofenadine Hydrochloride`). Status: `VERIFIED`.
  * **Unverified / Missing**: Returns `generic_name = null`. Status: `UNVERIFIED`.
  * **Unregistered Brand**: Returns `generic_name = null`. Status: `UNKNOWN_BRAND`.

---

## 6. Doctor Review & Audit Preservation

### 6.1 Audit Schema Principles
The system enforces **Immutable Audit Integrity**:
1. `original_prediction`, `original_confidence`, `top_3_predictions`, and `model_version` are **never overwritten**.
2. Doctor review actions (`CONFIRM` or `CORRECT`) create paired records (`AI_prediction`, `Doctor_verified_label`).
3. Out-of-Distribution (OOD) brands are logged with `known_class = False` and `prediction_status = unknown_ood` for future class expansion.

### 6.2 Secure URL Tokens
* **Format**: `/review/{token}`
* **Security**: 32-byte cryptographically secure URL-safe tokens (`secrets.token_urlsafe(32)`).
* **Expiration**: 24-hour default time-to-live (TTL).
* **Single-Use Enforcement**: Tokens mark `used = True` upon doctor submission to prevent double-reviews.

---

## 7. Admin Dashboard & Cloud Retraining Pipeline

### 7.1 Minimum Sample Gate & Training Lock
Retraining is controlled by `AdminDashboardManager` ([`src/admin_dashboard.py`](file:///d:/ediprjcursor/src/admin_dashboard.py)):
* **Minimum Threshold**: `MIN_NEW_SAMPLES = 100` new verified doctor samples required before retraining is allowed.
* **Insufficient Data Gate**: Returns `INSUFFICIENT_NEW_DATA` error code showing exact progress (e.g. `37 / 100 collected, 63 remaining`).
* **Training Lock**: Sets status to `RUNNING` and assigns a `job_id` to block duplicate triggers.

### 7.2 Cloud Retraining Workflow
* **Orchestrator**: GitHub Actions (`.github/workflows/cloud_training.yml`).
* **Zero-PC-Dependency**: Retraining executes in the cloud on free Linux build runners without requiring the user's personal PC to stay ON.
* **Pre-Training Data Quality Check**: `CloudModelTrainer.validate_verified_dataset()` verifies image file integrity and excludes missing/corrupted samples before model training.

---

## 8. Model Evaluation Gate & Rollback Registry

### 8.1 Candidate Evaluation Gate
When cloud retraining completes, `ModelRegistryManager` ([`src/model_registry.py`](file:///d:/ediprjcursor/src/model_registry.py)) evaluates the candidate model against active production:

* **Gate Condition**:
  $$\text{Candidate Accuracy} > \text{Active Production Accuracy} \quad \text{AND} \quad \text{Candidate Macro F1} \ge \text{Production F1} - 0.005$$
* **Approved Candidate** (e.g., Accuracy `87.3%` vs `83.91%`): Promoted to `PRODUCTION` status (`v2.0`). Previous model demoted to `APPROVED`.
* **Inferior Candidate** (e.g., Accuracy `79.0%` vs `87.3%`): Marked `REJECTED`. Active production model remains deployed.

### 8.2 Model Version Lifecycle & Rollback
Registered model statuses: `CANDIDATE`, `APPROVED`, `PRODUCTION`, `REJECTED`, `ROLLED_BACK`.
Admin can execute one-click rollback (`POST /api/admin/rollback`) to revert from `v2.0` back to `v1.0` at any time without deleting model files.

---

## 9. File & Module Map

| Directory / File | Description |
| :--- | :--- |
| **`src/predictor.py`** | Standalone `MedicinePredictor` core class (Preprocessing & Top-3 inference). |
| **`src/confidence.py`** | 3-tiered safety rules & review priority calculator. |
| **`src/medicine_mapping.py`** | Generic medicine lookup engine (`data/medicine_mapping.csv`). |
| **`src/doctor_feedback.py`** | Doctor review task manager, priority queue sorter & audit logger. |
| **`src/review_tokens.py`** | Cryptographic 24-hour time-limited review token manager. |
| **`src/verified_dataset.py`** | Doctor-verified training dataset cataloger (`data/doctor_verified/`). |
| **`src/admin_dashboard.py`** | Admin metrics dashboard, sample threshold gates & training locks. |
| **`src/training.py`** | Cloud-compatible retraining pipeline & dataset quality checker. |
| **`src/model_registry.py`** | Candidate evaluation comparison gate & rollback manager. |
| **`src/app.py`** | Production FastAPI REST API web service. |
| **`models/efficientnetb0_best.keras`** | Active production EfficientNetB0 model (83.91%). |
| **`models/v3_label_encoder.pkl`** | 78-class label encoder. |
| **`models/model_registry.json`** | Model version registry DB. |
| **`data/medicine_mapping.csv`** | Reference dataset mapping 78 brand classes to generic chemical names. |
| **`tests/test_full_system_integration.py`** | Master 12-phase integration test suite. |
| **`.github/workflows/cloud_training.yml`** | GitHub Actions cloud retraining workflow. |
