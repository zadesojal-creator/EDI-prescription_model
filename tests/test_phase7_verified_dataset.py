import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.verified_dataset import VerifiedDatasetManager
from src.doctor_feedback import DoctorFeedbackManager
from src.predictor import MedicinePredictor

def test_phase7():
    print("="*60)
    print("      PHASE 7: VERIFIED DATASET ACCUMULATION VERIFICATION")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_verified_dir = Path(tmp_dir) / "doctor_verified"
        tmp_review_db = Path(tmp_dir) / "doctor_reviews.json"

        dataset_mgr = VerifiedDatasetManager(verified_dir_path=str(tmp_verified_dir))
        fb_mgr = DoctorFeedbackManager(feedback_db_path=str(tmp_review_db))
        predictor = MedicinePredictor()

        # 1. Create and Record 3 Doctor Reviews
        print("\n1. Generating Doctor Reviews...")

        # Record 1: Confirmed Prediction
        p1 = {"top_brand": "Vifas", "top_confidence": 0.96, "top_candidates": [{"brand_name": "Vifas", "confidence": 0.96}], "status": "high_confidence", "review_priority": "LOW"}
        t1 = fb_mgr.create_review_task(p1, image_reference="data/prescriptions/img1.jpg")
        fb1 = fb_mgr.record_feedback(t1["review_id"], "CONFIRM", "Vifas", predictor.class_names)

        # Record 2: Corrected Prediction (Known class Ace)
        p2 = {"top_brand": "Unknown", "top_confidence": 0.42, "top_candidates": [{"brand_name": "Vifas", "confidence": 0.42}], "status": "doctor_verification_required", "review_priority": "HIGH"}
        t2 = fb_mgr.create_review_task(p2, image_reference="data/prescriptions/img2.jpg")
        fb2 = fb_mgr.record_feedback(t2["review_id"], "CORRECT", "Ace", predictor.class_names)

        # Record 3: Corrected Prediction (OOD Brand: Medicine Z)
        p3 = {"top_brand": "Alatrol", "top_confidence": 0.75, "top_candidates": [{"brand_name": "Alatrol", "confidence": 0.75}], "status": "medium_confidence", "review_priority": "MEDIUM"}
        t3 = fb_mgr.create_review_task(p3, image_reference="data/prescriptions/img3.jpg")
        fb3 = fb_mgr.record_feedback(t3["review_id"], "CORRECT", "Medicine Z (OOD)", predictor.class_names)

        # 2. Append to Verified Dataset
        print("\n2. Appending Reviews to Verified Dataset Catalog...")
        r1 = dataset_mgr.append_verified_record(fb1)
        r2 = dataset_mgr.append_verified_record(fb2)
        r3 = dataset_mgr.append_verified_record(fb3)

        assert r1["feedback_type"] == "CONFIRMED"
        assert r2["feedback_type"] == "CORRECTED" and r2["known_class"] is True
        assert r3["feedback_type"] == "CORRECTED" and r3["known_class"] is False

        # 3. Test Dataset Statistics Summary
        print("\n3. Calculating Dataset Statistics Summary...")
        stats = dataset_mgr.get_dataset_stats()

        print(f"   - Total Verified Samples : {stats['total_verified_samples']}")
        print(f"   - Confirmed Samples      : {stats['confirmed_samples']}")
        print(f"   - Corrected Samples      : {stats['corrected_samples']}")
        print(f"   - Known Class Samples    : {stats['known_class_samples']}")
        print(f"   - OOD Samples            : {stats['ood_samples']}")
        print(f"   - Unique Labels Count    : {stats['unique_labels_count']}")

        assert stats['total_verified_samples'] == 3
        assert stats['confirmed_samples'] == 1
        assert stats['corrected_samples'] == 2
        assert stats['known_class_samples'] == 2
        assert stats['ood_samples'] == 1

        # 4. Verify Unreviewed Task Rejection
        print("\n4. Verifying Unreviewed Task Rejection...")
        t_pending = fb_mgr.create_review_task(p1, image_reference="data/prescriptions/pending.jpg")
        try:
            dataset_mgr.append_verified_record(t_pending)
            assert False, "Should reject appending PENDING task to dataset"
        except ValueError as e:
            print(f"   Successfully caught expected error: '{e}'")

    print("\nPhase 7 Verified Dataset Accumulation Verification Passed Cleanly!")

if __name__ == "__main__":
    test_phase7()
