"""
Verified Dataset Accumulation Pipeline.
Stores doctor-verified prescription image records under data/doctor_verified/
and builds structured dataset catalogs for model retraining.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

class VerifiedDatasetManager:
    """
    Manages collection of doctor-verified training records under data/doctor_verified/.
    Supports confirmed predictions, corrected errors, and OOD samples.
    """

    def __init__(self, verified_dir_path: str = None):
        project_root = Path(__file__).resolve().parent.parent
        self.verified_dir = Path(verified_dir_path) if verified_dir_path else project_root / "data" / "doctor_verified"
        self.images_dir = self.verified_dir / "images"
        self.catalog_file = self.verified_dir / "verified_catalog.json"

        self.verified_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self._init_catalog()

    def _init_catalog(self):
        if not self.catalog_file.exists():
            with open(self.catalog_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_catalog(self) -> List[dict]:
        with open(self.catalog_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_catalog(self, records: List[dict]):
        with open(self.catalog_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def append_verified_record(self, doctor_review: dict) -> dict:
        """
        Appends a completed doctor review into the verified dataset catalog.
        Copies the original prescription image into data/doctor_verified/images/.
        """
        if doctor_review.get("status") not in ["CONFIRMED", "CORRECTED"]:
            raise ValueError(f"Review task '{doctor_review.get('review_id')}' is not confirmed or corrected.")

        review_id = doctor_review["review_id"]

        # Handle image copying
        src_img = Path(doctor_review["image_reference"])
        dest_filename = f"{review_id}_{src_img.name}" if src_img.exists() else f"{review_id}_sample.jpg"
        dest_img_path = self.images_dir / dest_filename

        if src_img.exists():
            shutil.copy2(src_img, dest_img_path)

        record = {
            "record_id": f"rec_{review_id}",
            "review_id": review_id,
            "prediction_id": doctor_review["prediction_id"],
            "prescription_id": doctor_review["prescription_id"],
            "image_reference": str(dest_img_path),
            "original_prediction": doctor_review["original_prediction"],
            "original_confidence": float(doctor_review["original_confidence"]),
            "top_3_predictions": doctor_review["top_3_predictions"],
            "doctor_verified_label": doctor_review["doctor_verified_label"],
            "feedback_type": doctor_review["feedback_type"],
            "known_class": bool(doctor_review["known_class"]),
            "model_version": doctor_review["model_version"],
            "doctor_id": doctor_review["doctor_id"],
            "doctor_email": doctor_review["doctor_email"],
            "added_to_dataset_at": datetime.now(timezone.utc).isoformat()
        }

        catalog = self._read_catalog()
        for existing in catalog:
            if existing["review_id"] == review_id:
                return existing

        catalog.append(record)
        self._write_catalog(catalog)
        return record

    def get_dataset_stats(self) -> dict:
        """
        Returns statistical summary of verified samples collected so far.
        """
        catalog = self._read_catalog()
        total_samples = len(catalog)
        confirmed_count = sum(1 for r in catalog if r["feedback_type"] == "CONFIRMED")
        corrected_count = sum(1 for r in catalog if r["feedback_type"] == "CORRECTED")
        known_class_count = sum(1 for r in catalog if r["known_class"] is True)
        ood_class_count = sum(1 for r in catalog if r["known_class"] is False)

        class_counts = {}
        for r in catalog:
            lbl = r["doctor_verified_label"]
            class_counts[lbl] = class_counts.get(lbl, 0) + 1

        return {
            "total_verified_samples": total_samples,
            "confirmed_samples": confirmed_count,
            "corrected_samples": corrected_count,
            "known_class_samples": known_class_count,
            "ood_samples": ood_class_count,
            "unique_labels_count": len(class_counts),
            "class_distribution": class_counts
        }

    def get_all_records(self) -> List[dict]:
        return self._read_catalog()
