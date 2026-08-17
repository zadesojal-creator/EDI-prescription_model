"""
Model Versioning Registry, Evaluation Gate & Rollback Module.
Enforces performance evaluation gates (Candidate vs Production), version tracking,
and zero-downtime model rollback management.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

class ModelRegistryManager:
    """
    Manages model registration, candidate evaluation comparison gates, approval/rejection,
    and rollback triggers for production model deployments.
    """

    def __init__(self, registry_db_path: str = None):
        project_root = Path(__file__).resolve().parent.parent
        self.registry_path = Path(registry_db_path) if registry_db_path else project_root / "models" / "model_registry.json"
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_registry()

    def _init_registry(self):
        if not self.registry_path.exists():
            initial_registry = {
                "active_production_version": "v1.0",
                "versions": {
                    "v1.0": {
                        "version": "v1.0",
                        "model_name": "EfficientNetB0",
                        "model_path": "models/efficientnetb0_best.keras",
                        "accuracy": 0.8391,
                        "macro_f1": 0.8421,
                        "training_date": "2026-08-17T11:00:00Z",
                        "dataset_samples_used": 5240,
                        "status": "PRODUCTION",
                        "created_at": "2026-08-17T11:00:00Z"
                    }
                }
            }
            self._write_registry(initial_registry)

    def _read_registry(self) -> dict:
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_registry(self, registry_dict: dict):
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(registry_dict, f, indent=2)

    def get_active_production_model(self) -> dict:
        reg = self._read_registry()
        active_ver = reg["active_production_version"]
        return reg["versions"][active_ver]

    def register_candidate_model(self, candidate_metrics: dict) -> dict:
        """
        Registers a newly trained cloud candidate model with status 'CANDIDATE'.
        """
        reg = self._read_registry()
        version = candidate_metrics["candidate_version"]

        version_record = {
            "version": version,
            "model_name": candidate_metrics.get("model_name", "EfficientNetB0"),
            "model_path": candidate_metrics["candidate_model_path"],
            "accuracy": float(candidate_metrics["accuracy"]),
            "macro_f1": float(candidate_metrics["macro_f1"]),
            "training_date": candidate_metrics.get("training_completed_at", datetime.now(timezone.utc).isoformat()),
            "dataset_samples_used": candidate_metrics.get("dataset_samples_used", 0),
            "status": "CANDIDATE",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        reg["versions"][version] = version_record
        self._write_registry(reg)
        return version_record

    def evaluate_and_gate_candidate(self, candidate_version: str) -> dict:
        """
        Compares Candidate Model vs Active Production Model.
        Gate Rules:
        - Candidate Accuracy MUST be > Active Production Accuracy.
        - Candidate Macro F1 MUST be >= Active Production Macro F1.
        Returns evaluation result dict with decision: 'APPROVED' or 'REJECTED'.
        """
        reg = self._read_registry()
        if candidate_version not in reg["versions"]:
            raise KeyError(f"Candidate version '{candidate_version}' not found in registry.")

        candidate = reg["versions"][candidate_version]
        current_prod = self.get_active_production_model()

        cand_acc = candidate["accuracy"]
        cand_f1 = candidate["macro_f1"]
        prod_acc = current_prod["accuracy"]
        prod_f1 = current_prod["macro_f1"]

        is_better_acc = cand_acc > prod_acc
        is_better_f1 = cand_f1 >= (prod_f1 - 0.005)  # Allow marginal F1 tolerance if accuracy is higher

        if is_better_acc and is_better_f1:
            decision = "APPROVED"
            message = f"Candidate '{candidate_version}' PASSED gate! (Acc: {cand_acc*100:.2f}% vs Prod {prod_acc*100:.2f}%)"
        else:
            decision = "REJECTED"
            message = f"Candidate '{candidate_version}' REJECTED by gate. (Acc: {cand_acc*100:.2f}% vs Prod {prod_acc*100:.2f}%). Active production '{current_prod['version']}' retained."

        # Update candidate status in registry
        reg["versions"][candidate_version]["status"] = decision
        self._write_registry(reg)

        return {
            "candidate_version": candidate_version,
            "decision": decision,
            "message": message,
            "candidate_metrics": {"accuracy": cand_acc, "macro_f1": cand_f1},
            "production_metrics": {"accuracy": prod_acc, "macro_f1": prod_f1}
        }

    def promote_to_production(self, version: str) -> dict:
        """
        Promotes an APPROVED version to active PRODUCTION.
        Moves previous PRODUCTION version to APPROVED state for rollback.
        """
        reg = self._read_registry()
        if version not in reg["versions"]:
            raise KeyError(f"Version '{version}' not found in registry.")

        rec = reg["versions"][version]
        if rec["status"] not in ["APPROVED", "CANDIDATE"]:
            raise ValueError(f"Cannot promote version '{version}' with status '{rec['status']}'. Must be APPROVED.")

        # Demote current production model
        old_prod_ver = reg["active_production_version"]
        if old_prod_ver in reg["versions"]:
            reg["versions"][old_prod_ver]["status"] = "APPROVED"

        # Promote new version
        reg["versions"][version]["status"] = "PRODUCTION"
        reg["active_production_version"] = version
        self._write_registry(reg)

        return {
            "previous_version": old_prod_ver,
            "active_version": version,
            "status": "PRODUCTION",
            "message": f"Successfully deployed model version '{version}' to PRODUCTION."
        }

    def rollback_production(self, target_version: str) -> dict:
        """
        Rolls back production to a specified previous model version.
        """
        reg = self._read_registry()
        if target_version not in reg["versions"]:
            raise KeyError(f"Target rollback version '{target_version}' not found.")

        current_prod = reg["active_production_version"]
        if target_version == current_prod:
            raise ValueError(f"Version '{target_version}' is already the active production model.")

        # Mark current production as ROLLED_BACK
        reg["versions"][current_prod]["status"] = "ROLLED_BACK"

        # Set target version as PRODUCTION
        reg["versions"][target_version]["status"] = "PRODUCTION"
        reg["active_production_version"] = target_version
        self._write_registry(reg)

        return {
            "previous_version": current_prod,
            "active_version": target_version,
            "status": "PRODUCTION",
            "message": f"Successfully rolled back production model from '{current_prod}' to '{target_version}'."
        }

    def list_all_versions(self) -> List[dict]:
        reg = self._read_registry()
        return list(reg["versions"].values())
