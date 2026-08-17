"""
Complete FastAPI Application Entrypoint.
Integrates Prediction, Generic Mapping, Doctor Review Priority Queues,
Secure Tokens, Verified Dataset Accumulation, Admin Dashboard, and Model Rollback APIs.
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field

from src.predictor import MedicinePredictor
from src.doctor_feedback import DoctorFeedbackManager
from src.review_tokens import DoctorReviewTokenManager
from src.verified_dataset import VerifiedDatasetManager
from src.admin_dashboard import AdminDashboardManager
from src.model_registry import ModelRegistryManager

app = FastAPI(
    title="AI Handwritten Medicine Recognition & Continuous Learning System",
    description="Healthcare decision-support system featuring Top-3 candidate recognition, generic medicine mapping, human-in-the-loop doctor review priority queues, and admin cloud retraining orchestration.",
    version="1.0.0"
)

# Initialize Singletons
PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOADS_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

predictor = MedicinePredictor()
feedback_mgr = DoctorFeedbackManager()
token_mgr = DoctorReviewTokenManager()
dataset_mgr = VerifiedDatasetManager()
admin_mgr = AdminDashboardManager(verified_dataset_manager=dataset_mgr)
registry_mgr = ModelRegistryManager()

# Pydantic Input Schemas
class FeedbackSubmissionRequest(BaseModel):
    token: str = Field(..., description="Secure time-limited review token")
    doctor_action: str = Field(..., description="'CONFIRM' or 'CORRECT'")
    doctor_verified_label: str = Field(..., description="Doctor's verified medicine brand name")
    doctor_id: str = Field("doc_001", description="Identifier of reviewing doctor")
    doctor_email: str = Field("doctor@clinic.org", description="Email of reviewing doctor")

class RollbackRequest(BaseModel):
    target_version: str = Field(..., description="Target model version to roll back to (e.g. 'v1.0')")

class TrainModelRequest(BaseModel):
    force_override: bool = Field(False, description="Set True to bypass minimum sample requirement")

# API Endpoints

@app.get("/")
def health_check():
    active_model = registry_mgr.get_active_production_model()
    return {
        "system_status": "ONLINE",
        "active_model_version": active_model["version"],
        "active_model_name": active_model["model_name"],
        "active_model_accuracy": f"{active_model['accuracy']*100:.2f}%",
        "docs_url": "/docs"
    }

@app.post("/api/predict")
async def predict_prescription(file: UploadFile = File(...)):
    """
    Accepts an uploaded prescription image file.
    Runs Top-3 prediction, maps generic medicine, evaluates confidence level,
    and automatically queues a doctor review task with a secure token.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    file_ext = Path(file.filename).suffix or ".jpg"
    saved_filename = f"upload_{uuid.uuid4().hex[:10]}{file_ext}"
    saved_path = UPLOADS_DIR / saved_filename

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Run Inference
    prediction_result = predictor.predict(str(saved_path))
    active_model = registry_mgr.get_active_production_model()

    # 2. Create Doctor Review Task
    review_task = feedback_mgr.create_review_task(
        prediction_result=prediction_result,
        image_reference=str(saved_path),
        model_version=active_model["version"]
    )

    # 3. Generate Secure Time-Limited Token
    token_record = token_mgr.generate_review_token(review_task["review_id"], ttl_hours=24)

    return {
        "prediction": prediction_result,
        "review_id": review_task["review_id"],
        "review_priority": review_task["priority"],
        "doctor_review_url": token_record["review_url"],
        "secure_token": token_record["token"],
        "token_expires_at": token_record["expires_at"]
    }

@app.get("/api/doctor/reviews")
def get_doctor_reviews(priority: Optional[str] = Query(None, description="Filter by priority: HIGH, MEDIUM, LOW")):
    """
    Fetches all pending doctor review tasks sorted by priority (HIGH -> MEDIUM -> LOW).
    """
    return {
        "pending_reviews": feedback_mgr.get_pending_reviews(priority_filter=priority)
    }

@app.get("/review/{token}")
def get_review_by_token(token: str):
    """
    Resolves a secure time-limited review token and returns the review task details.
    """
    try:
        token_record = token_mgr.validate_token(token)
        review_task = feedback_mgr.get_review_by_id(token_record["review_id"])
        if not review_task:
            raise HTTPException(status_code=404, detail="Review task not found.")
        return {
            "token_valid": True,
            "token_used": token_record["used"],
            "review_task": review_task
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=410, detail=str(e))

@app.post("/api/doctor/feedback")
def submit_doctor_feedback(payload: FeedbackSubmissionRequest):
    """
    Submits doctor feedback (CONFIRM or CORRECT).
    Updates audit log, consumes token, and appends verified record to training dataset.
    """
    try:
        # Validate token
        token_record = token_mgr.validate_token(payload.token)
        if token_record["used"]:
            raise HTTPException(status_code=400, detail="This review token has already been submitted.")

        # Record Doctor Feedback
        updated_task = feedback_mgr.record_feedback(
            review_id=token_record["review_id"],
            doctor_action=payload.doctor_action,
            doctor_verified_label=payload.doctor_verified_label,
            known_class_list=predictor.class_names,
            doctor_id=payload.doctor_id,
            doctor_email=payload.doctor_email
        )

        # Consume Token
        token_mgr.consume_token(payload.token)

        # Append to Verified Dataset
        verified_record = dataset_mgr.append_verified_record(updated_task)

        return {
            "status": "SUCCESS",
            "message": f"Doctor feedback successfully recorded for task '{updated_task['review_id']}'.",
            "updated_review": updated_task,
            "verified_record_id": verified_record["record_id"]
        }
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/admin/dashboard")
def get_admin_dashboard():
    """
    Returns Admin Training Dashboard metrics, sample counts, and trainability status.
    """
    return admin_mgr.get_dashboard_summary()

@app.post("/api/admin/train-model")
def trigger_cloud_training(payload: TrainModelRequest):
    """
    Triggers cloud model retraining job if minimum sample threshold is met.
    """
    result = admin_mgr.trigger_train_model(force_override=payload.force_override)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result)
    return result

@app.get("/api/admin/model-registry")
def list_model_registry():
    """
    Returns list of all registered model versions, metrics, and statuses.
    """
    return {
        "active_production_version": registry_mgr.get_active_production_model()["version"],
        "versions": registry_mgr.list_all_versions()
    }

@app.post("/api/admin/rollback")
def rollback_model_version(payload: RollbackRequest):
    """
    Rolls back active production model to a target historical version.
    """
    try:
        res = registry_mgr.rollback_production(payload.target_version)
        admin_mgr.reset_training_lock("IDLE")
        return res
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
