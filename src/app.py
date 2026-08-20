"""
Complete FastAPI Application Entrypoint.
Integrates Prediction, Generic Mapping, Doctor Review Priority Queues,
Secure Tokens, Email Notifications, Interactive Web Portal, Verified Dataset Accumulation,
Admin Dashboard, and Model Rollback APIs.
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

from src.predictor import MedicinePredictor
from src.doctor_feedback import DoctorFeedbackManager
from src.review_tokens import DoctorReviewTokenManager
from src.email_service import DoctorEmailNotifier
from src.verified_dataset import VerifiedDatasetManager
from src.admin_dashboard import AdminDashboardManager
from src.model_registry import ModelRegistryManager

app = FastAPI(
    title="AI Handwritten Medicine Recognition & Continuous Learning System",
    description="Healthcare decision-support system featuring Top-3 candidate recognition, generic medicine mapping, human-in-the-loop doctor review priority queues, email notifications, and admin cloud retraining orchestration.",
    version="1.0.0"
)

# Initialize Singletons
PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOADS_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

predictor = MedicinePredictor()
feedback_mgr = DoctorFeedbackManager()
token_mgr = DoctorReviewTokenManager()
email_notifier = DoctorEmailNotifier()
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
async def predict_prescription(
    file: UploadFile = File(...),
    doctor_email: Optional[str] = Query(None, description="Optional override doctor email for review notification")
):
    """
    Accepts an uploaded prescription image file.
    Runs Top-3 prediction, maps generic medicine, evaluates confidence level,
    queues doctor review task, generates 24h token, and dispatches email notification.
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

    # 4. Dispatch Doctor Email Notification (Non-blocking on failure)
    try:
        email_data = email_notifier.send_doctor_review_email(
            review_task=review_task,
            token_record=token_record,
            doctor_email=doctor_email
        )
    except Exception as err:
        email_data = {
            "email_status": "FAILED",
            "email_error": str(err),
            "message": f"Email service failure: {str(err)}"
        }

    return {
        "prediction": prediction_result,
        "review_id": review_task["review_id"],
        "review_priority": review_task["priority"],
        "doctor_review_url": token_record["review_url"],
        "secure_token": token_record["token"],
        "token_expires_at": token_record["expires_at"],
        "email_notification": email_data
    }


@app.get("/api/doctor/reviews")
def get_doctor_reviews(priority: Optional[str] = Query(None, description="Filter by priority: HIGH, MEDIUM, LOW")):
    """
    Fetches all pending doctor review tasks sorted by priority (HIGH -> MEDIUM -> LOW).
    """
    return {
        "pending_reviews": feedback_mgr.get_pending_reviews(priority_filter=priority)
    }

@app.get("/api/image/{filename}")
def serve_prescription_image(filename: str):
    """
    Serves uploaded prescription image file for browser display.
    """
    img_path = UPLOADS_DIR / filename
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found.")
    return FileResponse(str(img_path))

@app.get("/review/{token}")
def get_review_by_token(token: str, request: Request):
    """
    Resolves a secure time-limited review token.
    If requested by browser (text/html), renders interactive Doctor Review Web Page.
    Otherwise returns JSON task details.
    """
    try:
        token_record = token_mgr.validate_token(token)
        review_task = feedback_mgr.get_review_by_id(token_record["review_id"])
        if not review_task:
            raise HTTPException(status_code=404, detail="Review task not found.")

        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            return HTMLResponse(content=render_doctor_review_html(token, token_record, review_task, predictor.class_names))

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
        token_record = token_mgr.validate_token(payload.token)
        if token_record["used"]:
            raise HTTPException(status_code=400, detail="This review token has already been submitted.")

        updated_task = feedback_mgr.record_feedback(
            review_id=token_record["review_id"],
            doctor_action=payload.doctor_action,
            doctor_verified_label=payload.doctor_verified_label,
            known_class_list=predictor.class_names,
            doctor_id=payload.doctor_id,
            doctor_email=payload.doctor_email
        )

        token_mgr.consume_token(payload.token)
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
    return admin_mgr.get_dashboard_summary()

@app.post("/api/admin/train-model")
def trigger_cloud_training(payload: TrainModelRequest):
    result = admin_mgr.trigger_train_model(force_override=payload.force_override)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result)
    return result

@app.get("/api/admin/model-registry")
def list_model_registry():
    return {
        "active_production_version": registry_mgr.get_active_production_model()["version"],
        "versions": registry_mgr.list_all_versions()
    }

@app.post("/api/admin/rollback")
def rollback_model_version(payload: RollbackRequest):
    try:
        res = registry_mgr.rollback_production(payload.target_version)
        admin_mgr.reset_training_lock("IDLE")
        return res
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/admin/test-doctor-email")
def test_doctor_email_notification(doctor_email: Optional[str] = Query(None, description="Optional target doctor email")):
    """
    Controlled admin endpoint to test doctor email notification dispatch.
    Sends a test notification to configured DOCTOR_EMAIL without exposing real patient data.
    """
    mock_task = {
        "review_id": f"rev_test_{uuid.uuid4().hex[:6]}",
        "prescription_id": "rx_test_sample",
        "original_prediction": "Vifas (TEST)",
        "original_confidence": 0.42,
        "priority": "HIGH",
        "prediction_status": "doctor_verification_required",
        "top_3_predictions": [
            {"brand_name": "Vifas (TEST)", "confidence": 0.42, "generic_name": "Fexofenadine Hydrochloride"},
            {"brand_name": "Ace", "confidence": 0.31, "generic_name": "Paracetamol"},
            {"brand_name": "Filmet", "confidence": 0.12, "generic_name": "Metronidazole"}
        ]
    }
    mock_token = token_mgr.generate_review_token(mock_task["review_id"], ttl_hours=24)
    email_res = email_notifier.send_doctor_review_email(
        review_task=mock_task,
        token_record=mock_token,
        doctor_email=doctor_email,
        is_test=True
    )
    return {
        "status": "SUCCESS",
        "message": "Admin test doctor email dispatch completed.",
        "email_notification": email_res
    }



def render_doctor_review_html(token: str, token_record: dict, task: dict, known_classes: List[str]) -> str:
    """
    Renders an interactive, responsive HTML/JS Doctor Review Portal for browser view.
    """
    is_used = token_record.get("used", False)
    img_filename = Path(task["image_reference"]).name
    img_url = f"/api/image/{img_filename}"
    priority = task.get("priority", "HIGH")
    brand = task.get("original_prediction", "Unknown")
    conf = float(task.get("original_confidence", 0.0)) * 100

    options_html = "".join([f'<option value="{c}">{c}</option>' for c in sorted(known_classes)])

    candidates_rows = ""
    for idx, c in enumerate(task.get("top_3_predictions", []), 1):
        candidates_rows += f"""
        <tr>
          <td><strong>#{idx}</strong></td>
          <td>{c['brand_name']}</td>
          <td>{c.get('generic_name', 'N/A')}</td>
          <td>{float(c['confidence'])*100:.2f}%</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Doctor Review Portal | Prescription Verification</title>
      <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f0f4f8; margin: 0; padding: 20px; color: #2d3748; }}
        .card {{ max-width: 800px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #edf2f7; padding-bottom: 16px; margin-bottom: 20px; }}
        .badge {{ padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px; text-transform: uppercase; }}
        .badge-HIGH {{ background: #fed7d7; color: #9b2c2c; }}
        .badge-MEDIUM {{ background: #feebc8; color: #9c4221; }}
        .badge-LOW {{ background: #c6f6d5; color: #22543d; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
        @media (max-width: 600px) {{ .grid {{ grid-template-columns: 1fr; }} }}
        .img-box {{ background: #1a202c; border-radius: 8px; overflow: hidden; text-align: center; padding: 10px; }}
        .img-box img {{ max-width: 100%; max-height: 300px; object-fit: contain; border-radius: 4px; }}
        .info-box {{ background: #f7fafc; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #edf2f7; }}
        th {{ background: #edf2f7; }}
        .action-box {{ background: #ebf8ff; border: 1px solid #bee3f8; padding: 20px; border-radius: 8px; margin-top: 20px; }}
        .btn {{ display: inline-block; width: 100%; padding: 12px; border: none; border-radius: 6px; font-size: 15px; font-weight: 700; cursor: pointer; transition: 0.2s; margin-top: 10px; }}
        .btn-confirm {{ background: #38a169; color: white; }}
        .btn-confirm:hover {{ background: #2f855a; }}
        .btn-correct {{ background: #3182ce; color: white; }}
        .btn-correct:hover {{ background: #2b6cb0; }}
        .btn-ood {{ background: #dd6b20; color: white; }}
        .btn-ood:hover {{ background: #c05621; }}
        select, input[type="text"] {{ width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e0; margin-top: 8px; font-size: 14px; }}
        .alert {{ padding: 16px; border-radius: 8px; font-weight: bold; margin-bottom: 20px; display: none; }}
        .alert-success {{ background: #c6f6d5; color: #22543d; }}
        .alert-error {{ background: #fed7d7; color: #9b2c2c; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h2>Doctor Review Portal</h2>
          <span class="badge badge-{priority}">{priority} PRIORITY</span>
        </div>

        <div id="alert-box" class="alert"></div>

        {'<div class="alert alert-error" style="display:block;">⚠️ This review link has already been submitted and completed.</div>' if is_used else ''}

        <div class="grid">
          <div class="img-box">
            <p style="color:#a0aec0; font-size:12px; margin-top:0;">Prescription Handwriting Preview</p>
            <img src="{img_url}" alt="Prescription Image">
          </div>
          <div class="info-box">
            <h4 style="margin-top:0;">AI Prediction Summary</h4>
            <p><strong>Top Predicted Brand:</strong> <span style="font-size:18px; color:#2b6cb0;">{brand}</span></p>
            <p><strong>Top Confidence:</strong> {conf:.2f}%</p>
            <p><strong>Prescription ID:</strong> <code>{task['prescription_id']}</code></p>
            <p><strong>Task Status:</strong> {task['prediction_status']}</p>
          </div>
        </div>

        <div class="info-box">
          <h4 style="margin-top:0;">Top-3 AI Candidates</h4>
          <table>
            <thead>
              <tr><th>Rank</th><th>Brand Candidate</th><th>Generic Formulation</th><th>Confidence</th></tr>
            </thead>
            <tbody>
              {candidates_rows}
            </tbody>
          </table>
        </div>

        <div class="action-box" id="form-container" style="{'display:none;' if is_used else ''}">
          <h3 style="margin-top:0; color:#2c5282;">Doctor Feedback Verification</h3>
          <p style="font-size:14px; color:#4a5568;">Select your clinical decision below:</p>

          <!-- OPTION 1: CONFIRM -->
          <button class="btn btn-confirm" onclick="submitFeedback('CONFIRM', '{brand}')">
            ✓ CONFIRM AI PREDICTION ({brand})
          </button>

          <hr style="margin: 20px 0; border:0; border-top:1px solid #cbd5e0;">

          <!-- OPTION 2: CORRECT WITH KNOWN BRAND -->
          <label style="font-weight:bold; font-size:14px;">Option B: Correct with a Known Class</label>
          <select id="known-class-select">
            <option value="">-- Select Correct Medicine Brand --</option>
            {options_html}
          </select>
          <button class="btn btn-correct" onclick="submitKnownCorrection()">
            ✎ SUBMIT BRAND CORRECTION
          </button>

          <hr style="margin: 20px 0; border:0; border-top:1px solid #cbd5e0;">

          <!-- OPTION 3: UNKNOWN / OOD MEDICINE -->
          <label style="font-weight:bold; font-size:14px;">Option C: Identify Out-of-Distribution (OOD) Medicine</label>
          <input type="text" id="ood-input" placeholder="Type new medicine brand name outside 78 classes...">
          <button class="btn btn-ood" onclick="submitOODCorrection()">
            ⚠ SUBMIT NEW UNREGISTERED MEDICINE (OOD)
          </button>
        </div>
      </div>

      <script>
        const token = "{token}";

        async function submitFeedback(action, label) {{
          if (!label || label.trim() === "") {{
            showAlert("Please provide a valid medicine brand name.", "error");
            return;
          }}
          try {{
            const res = await fetch("/api/doctor/feedback", {{
              method: "POST",
              headers: {{ "Content-Type": "application/json" }},
              body: JSON.stringify({{
                token: token,
                doctor_action: action,
                doctor_verified_label: label,
                doctor_id: "doc_web_portal",
                doctor_email: "doctor@clinic.org"
              }})
            }});
            const data = await res.json();
            if (res.ok) {{
              showAlert("✓ Doctor feedback submitted successfully! Token consumed.", "success");
              document.getElementById("form-container").style.display = "none";
            }} else {{
              showAlert("Error: " + (data.detail || "Submission failed."), "error");
            }}
          }} catch (err) {{
            showAlert("Network error: " + err.message, "error");
          }}
        }}

        function submitKnownCorrection() {{
          const sel = document.getElementById("known-class-select").value;
          if (!sel) {{
            showAlert("Please select a brand from the dropdown list.", "error");
            return;
          }}
          submitFeedback("CORRECT", sel);
        }}

        function submitOODCorrection() {{
          const val = document.getElementById("ood-input").value;
          if (!val || val.trim() === "") {{
            showAlert("Please type the name of the new medicine.", "error");
            return;
          }}
          submitFeedback("CORRECT", val.trim());
        }}

        function showAlert(msg, type) {{
          const box = document.getElementById("alert-box");
          box.className = "alert alert-" + type;
          box.innerText = msg;
          box.style.display = "block";
        }}
      </script>
    </body>
    </html>
    """
