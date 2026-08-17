"""
Doctor Feedback System & Audit Schema Module
Captures doctor reviews (Confirmations, Corrections, OOD/Unknown medicines)
while strictly preserving full auditability and original AI predictions.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

class DoctorFeedbackManager:
    """
    Manages creation of doctor review tasks and recording of doctor feedback.
    Preserves original AI predictions, confidence scores, and model versions for auditability.
    """

    def __init__(self, feedback_db_path: str = None):
        project_root = Path(__file__).resolve().parent.parent
        self.db_path = Path(feedback_db_path) if feedback_db_path else project_root / "data" / "doctor_reviews.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        if not self.db_path.exists():
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_reviews(self) -> List[dict]:
        with open(self.db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_reviews(self, reviews: List[dict]):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(reviews, f, indent=2)

    def create_review_task(
        self,
        prediction_result: dict,
        image_reference: str,
        prescription_id: Optional[str] = None,
        model_version: str = "v1.0"
    ) -> dict:
        """
        Creates a new PENDING doctor review task from an AI prediction result.
        """
        review_id = f"rev_{uuid.uuid4().hex[:10]}"
        prediction_id = prediction_result.get("prediction_id", f"pred_{uuid.uuid4().hex[:10]}")
        p_id = prescription_id or f"rx_{uuid.uuid4().hex[:8]}"

        task = {
            "review_id": review_id,
            "prediction_id": prediction_id,
            "prescription_id": p_id,
            "image_reference": str(image_reference),
            "original_prediction": prediction_result.get("top_brand", "Unknown"),
            "original_confidence": float(prediction_result.get("top_confidence", 0.0)),
            "top_3_predictions": [
                {
                    "brand_name": c["brand_name"],
                    "confidence": float(c["confidence"]),
                    "generic_name": c.get("generic_name")
                }
                for c in prediction_result.get("top_candidates", [])[:3]
            ],
            "priority": prediction_result.get("review_priority", "HIGH"),
            "prediction_status": prediction_result.get("status", "doctor_verification_required"),
            "status": "PENDING",
            "doctor_verified_label": None,
            "known_class": None,
            "feedback_type": None,
            "doctor_id": None,
            "doctor_email": None,
            "model_version": model_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_at": None
        }

        reviews = self._read_reviews()
        reviews.append(task)
        self._write_reviews(reviews)
        return task

    def record_feedback(
        self,
        review_id: str,
        doctor_action: str,  # 'CONFIRM' or 'CORRECT'
        doctor_verified_label: str,
        known_class_list: List[str],
        doctor_id: str = "doc_default",
        doctor_email: str = "doctor@clinic.org"
    ) -> dict:
        """
        Records doctor feedback for a review task.
        Action:
          - 'CONFIRM': Doctor verifies AI prediction is correct.
          - 'CORRECT': Doctor supplies correct label (known 78 class or new OOD brand).
        """
        reviews = self._read_reviews()
        target_idx = None
        for i, r in enumerate(reviews):
            if r["review_id"] == review_id:
                target_idx = i
                break

        if target_idx is None:
            raise KeyError(f"Review task ID '{review_id}' not found.")

        task = reviews[target_idx]
        if task["status"] != "PENDING":
            raise ValueError(f"Review task '{review_id}' is already {task['status']}.")

        clean_doctor_label = str(doctor_verified_label).strip()
        is_known = clean_doctor_label in known_class_list

        if doctor_action.upper() == "CONFIRM":
            feedback_type = "CONFIRMED"
            status = "CONFIRMED"
            final_label = task["original_prediction"]
            is_known = True
        elif doctor_action.upper() == "CORRECT":
            feedback_type = "CORRECTED"
            status = "CORRECTED"
            final_label = clean_doctor_label
        else:
            raise ValueError("Invalid doctor_action. Must be 'CONFIRM' or 'CORRECT'.")

        # Update Task Record while preserving all original prediction data
        task["status"] = status
        task["doctor_verified_label"] = final_label
        task["known_class"] = is_known
        task["feedback_type"] = feedback_type
        task["doctor_id"] = doctor_id
        task["doctor_email"] = doctor_email
        task["reviewed_at"] = datetime.now(timezone.utc).isoformat()

        if not is_known and status == "CORRECTED":
            task["prediction_status"] = "unknown_ood"

        reviews[target_idx] = task
        self._write_reviews(reviews)
        return task

    def get_review_by_id(self, review_id: str) -> Optional[dict]:
        reviews = self._read_reviews()
        for r in reviews:
            if r["review_id"] == review_id:
                return r
        return None

    def get_pending_reviews(self, priority_filter: Optional[str] = None) -> List[dict]:
        reviews = self._read_reviews()
        pending = [r for r in reviews if r["status"] == "PENDING"]
        if priority_filter:
            pending = [r for r in pending if r["priority"] == priority_filter.upper()]

        # Sort by Priority: HIGH -> MEDIUM -> LOW
        priority_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        pending.sort(key=lambda x: priority_map.get(x["priority"], 99))
        return pending
