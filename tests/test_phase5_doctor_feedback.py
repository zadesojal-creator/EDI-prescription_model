import sys
import tempfile
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.doctor_feedback import DoctorFeedbackManager
from src.predictor import MedicinePredictor

def test_phase5():
    print("="*60)
    print("      PHASE 5: DOCTOR FEEDBACK & AUDIT SCHEMA VERIFICATION")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_db = Path(tmp_dir) / "test_reviews.json"
        fb_mgr = DoctorFeedbackManager(feedback_db_path=str(tmp_db))
        predictor = MedicinePredictor()

        known_classes = predictor.class_names

        # 1. Create Review Tasks for Different Confidence Scenarios
        print("\n1. Creating Doctor Review Tasks...")

        # High Confidence Prediction
        pred_high = {
            "prediction_id": "pred_001",
            "top_brand": "Vifas",
            "top_confidence": 0.96,
            "top_candidates": [
                {"brand_name": "Vifas", "confidence": 0.96, "generic_name": "Fexofenadine Hydrochloride"},
                {"brand_name": "Ace", "confidence": 0.02, "generic_name": "Paracetamol"},
                {"brand_name": "Filmet", "confidence": 0.01, "generic_name": "Metronidazole"}
            ],
            "status": "high_confidence",
            "review_priority": "LOW"
        }
        task_high = fb_mgr.create_review_task(pred_high, image_reference="data/prescriptions/img_high.jpg", model_version="v1.0")

        # Low Confidence Prediction
        pred_low = {
            "prediction_id": "pred_002",
            "top_brand": "Unknown",
            "top_confidence": 0.42,
            "top_candidates": [
                {"brand_name": "Vifas", "confidence": 0.42, "generic_name": "Fexofenadine Hydrochloride"},
                {"brand_name": "Ace", "confidence": 0.31, "generic_name": "Paracetamol"},
                {"brand_name": "Filmet", "confidence": 0.11, "generic_name": "Metronidazole"}
            ],
            "status": "doctor_verification_required",
            "review_priority": "HIGH"
        }
        task_low = fb_mgr.create_review_task(pred_low, image_reference="data/prescriptions/img_low.jpg", model_version="v1.0")

        # Medium Confidence Prediction
        pred_med = {
            "prediction_id": "pred_003",
            "top_brand": "Alatrol",
            "top_confidence": 0.78,
            "top_candidates": [
                {"brand_name": "Alatrol", "confidence": 0.78, "generic_name": "Cetirizine Hydrochloride"},
                {"brand_name": "Atrizin", "confidence": 0.15, "generic_name": "Cetirizine Hydrochloride"},
                {"brand_name": "Ace", "confidence": 0.04, "generic_name": "Paracetamol"}
            ],
            "status": "medium_confidence",
            "review_priority": "MEDIUM"
        }
        task_med = fb_mgr.create_review_task(pred_med, image_reference="data/prescriptions/img_med.jpg", model_version="v1.0")

        # 2. Test Doctor Priority Queue Sorting
        print("\n2. Testing Priority Queue Sorting (Expect HIGH -> MEDIUM -> LOW):")
        pending_queue = fb_mgr.get_pending_reviews()
        priorities_in_queue = [r["priority"] for r in pending_queue]
        print(f"   Queue Priorities: {priorities_in_queue}")
        assert priorities_in_queue == ["HIGH", "MEDIUM", "LOW"], "Queue must sort HIGH -> MEDIUM -> LOW"

        # 3. Test Action 1: Doctor CONFIRM (High Confidence Task)
        print("\n3. Testing Action 1: Doctor CONFIRM...")
        fb_confirm = fb_mgr.record_feedback(
            review_id=task_high["review_id"],
            doctor_action="CONFIRM",
            doctor_verified_label="Vifas",
            known_class_list=known_classes,
            doctor_id="doc_smith",
            doctor_email="dr.smith@clinic.org"
        )
        print(f"   - Status                : {fb_confirm['status']}")
        print(f"   - Original AI Prediction : {fb_confirm['original_prediction']} ({fb_confirm['original_confidence']*100:.1f}%)")
        print(f"   - Doctor Verified Label  : {fb_confirm['doctor_verified_label']}")
        print(f"   - Feedback Type         : {fb_confirm['feedback_type']}")
        assert fb_confirm['feedback_type'] == "CONFIRMED"
        assert fb_confirm['original_prediction'] == "Vifas"  # Original preserved!

        # 4. Test Action 2: Doctor CORRECT with Known Class (Low Confidence Task)
        print("\n4. Testing Action 2: Doctor CORRECT with Known Class...")
        fb_correct = fb_mgr.record_feedback(
            review_id=task_low["review_id"],
            doctor_action="CORRECT",
            doctor_verified_label="Ace",
            known_class_list=known_classes,
            doctor_id="doc_jones",
            doctor_email="dr.jones@clinic.org"
        )
        print(f"   - Status                : {fb_correct['status']}")
        print(f"   - Original AI Prediction : {fb_correct['original_prediction']} ({fb_correct['original_confidence']*100:.1f}%)")
        print(f"   - Doctor Verified Label  : {fb_correct['doctor_verified_label']}")
        print(f"   - Feedback Type         : {fb_correct['feedback_type']}")
        print(f"   - Known Class           : {fb_correct['known_class']}")
        assert fb_correct['feedback_type'] == "CORRECTED"
        assert fb_correct['original_prediction'] == "Unknown"  # Original preserved!
        assert fb_correct['doctor_verified_label'] == "Ace"
        assert fb_correct['known_class'] is True

        # 5. Test Action 3: Doctor CORRECT with UNKNOWN/OOD Brand
        print("\n5. Testing Action 3: Doctor CORRECT with UNKNOWN/OOD Brand...")
        fb_ood = fb_mgr.record_feedback(
            review_id=task_med["review_id"],
            doctor_action="CORRECT",
            doctor_verified_label="Medicine Z (Unregistered OOD)",
            known_class_list=known_classes,
            doctor_id="doc_smith",
            doctor_email="dr.smith@clinic.org"
        )
        print(f"   - Status                : {fb_ood['status']}")
        print(f"   - Original AI Prediction : {fb_ood['original_prediction']} ({fb_ood['original_confidence']*100:.1f}%)")
        print(f"   - Doctor Verified Label  : {fb_ood['doctor_verified_label']}")
        print(f"   - Feedback Type         : {fb_ood['feedback_type']}")
        print(f"   - Known Class           : {fb_ood['known_class']}")
        print(f"   - Prediction Status     : {fb_ood['prediction_status']}")
        assert fb_ood['feedback_type'] == "CORRECTED"
        assert fb_ood['known_class'] is False
        assert fb_ood['prediction_status'] == "unknown_ood"

        # 6. Audit Preservation Verification
        print("\n6. Verifying Audit Trail Integrity...")
        rec = fb_mgr.get_review_by_id(task_high["review_id"])
        assert rec["original_prediction"] == "Vifas"
        assert rec["original_confidence"] == 0.96
        assert rec["model_version"] == "v1.0"
        assert rec["reviewed_at"] is not None
        print("   All audit fields intact and preserved without overwriting original AI predictions!")

    print("\nPhase 5 Doctor Feedback & Audit Schema Verification Passed Cleanly!")

if __name__ == "__main__":
    test_phase5()
