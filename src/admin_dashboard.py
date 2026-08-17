"""
Admin Training Dashboard & Status Interface.
Provides administrative monitoring of verified data collection, model version status,
and minimum-sample-protected 'TRAIN MODEL' trigger control.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

DEFAULT_MIN_NEW_SAMPLES = 100

class AdminDashboardManager:
    """
    Manages Admin Training Dashboard metrics, training locks, minimum sample gates,
    and trigger validation for cloud model retraining.
    """

    def __init__(
        self,
        verified_dataset_manager,
        status_db_path: str = None,
        min_new_samples: int = DEFAULT_MIN_NEW_SAMPLES
    ):
        self.dataset_mgr = verified_dataset_manager
        project_root = Path(__file__).resolve().parent.parent
        self.status_db_path = Path(status_db_path) if status_db_path else project_root / "data" / "admin_status.json"
        self.status_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.min_new_samples = min_new_samples
        self._init_status_db()

    def _init_status_db(self):
        if not self.status_db_path.exists():
            initial_state = {
                "active_model_version": "v1.0",
                "active_model_name": "EfficientNetB0",
                "current_accuracy": 0.8391,
                "current_macro_f1": 0.8421,
                "training_status": "IDLE",  # IDLE, RUNNING, COMPLETED, FAILED
                "active_job_id": None,
                "last_training_date": "2026-08-17T11:00:00Z",
                "samples_at_last_training": 0
            }
            self._write_status(initial_state)

    def _read_status(self) -> dict:
        with open(self.status_db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_status(self, status_dict: dict):
        with open(self.status_db_path, "w", encoding="utf-8") as f:
            json.dump(status_dict, f, indent=2)

    def get_dashboard_summary(self) -> dict:
        """
        Returns a complete summary for the Admin Dashboard view.
        """
        status_data = self._read_status()
        dataset_stats = self.dataset_mgr.get_dataset_stats()

        total_verified = dataset_stats["total_verified_samples"]
        last_training_samples = status_data.get("samples_at_last_training", 0)
        new_samples = max(0, total_verified - last_training_samples)
        remaining_needed = max(0, self.min_new_samples - new_samples)

        is_trainable = (new_samples >= self.min_new_samples) and (status_data["training_status"] == "IDLE")

        return {
            "active_model_version": status_data["active_model_version"],
            "active_model_name": status_data["active_model_name"],
            "current_accuracy": f"{status_data['current_accuracy']*100:.2f}%",
            "current_macro_f1": f"{status_data['current_macro_f1']:.4f}",
            "training_status": status_data["training_status"],
            "active_job_id": status_data["active_job_id"],
            "total_verified_samples": total_verified,
            "samples_at_last_training": last_training_samples,
            "new_samples_since_last_training": new_samples,
            "min_new_samples_required": self.min_new_samples,
            "remaining_samples_needed": remaining_needed,
            "confirmed_count": dataset_stats["confirmed_samples"],
            "corrected_count": dataset_stats["corrected_samples"],
            "ood_count": dataset_stats["ood_samples"],
            "last_training_date": status_data["last_training_date"],
            "can_trigger_training": is_trainable
        }

    def trigger_train_model(self, force_override: bool = False) -> dict:
        """
        Validates requirements and triggers the 'TRAIN MODEL' workflow.
        Checks:
        1. Training lock (blocks duplicate runs if status == RUNNING).
        2. Minimum new sample threshold.
        """
        status_data = self._read_status()

        # Check 1: Training Lock
        if status_data["training_status"] == "RUNNING":
            return {
                "success": False,
                "error_code": "TRAINING_IN_PROGRESS",
                "message": f"Training job '{status_data['active_job_id']}' is already running. Please wait for completion.",
                "dashboard": self.get_dashboard_summary()
            }

        # Check 2: Minimum Samples Gate
        summary = self.get_dashboard_summary()
        new_samples = summary["new_samples_since_last_training"]

        if new_samples < self.min_new_samples and not force_override:
            return {
                "success": False,
                "error_code": "INSUFFICIENT_NEW_DATA",
                "message": f"Not enough new verified data. Current new samples: {new_samples}. Required: {self.min_new_samples}. Remaining: {summary['remaining_samples_needed']}.",
                "dashboard": summary
            }

        # Acquisition Granted: Lock Training
        job_id = f"job_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        status_data["training_status"] = "RUNNING"
        status_data["active_job_id"] = job_id
        self._write_status(status_data)

        return {
            "success": True,
            "error_code": None,
            "job_id": job_id,
            "message": f"Training job '{job_id}' initiated successfully with {new_samples} new verified samples.",
            "dashboard": self.get_dashboard_summary()
        }

    def reset_training_lock(self, new_status: str = "IDLE", job_id: str = None):
        """
        Resets or updates training lock state after job completion or failure.
        """
        status_data = self._read_status()
        status_data["training_status"] = new_status
        if new_status == "IDLE" or new_status == "COMPLETED" or new_status == "FAILED":
            status_data["active_job_id"] = None
        self._write_status(status_data)
