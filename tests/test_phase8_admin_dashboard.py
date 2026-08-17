import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.admin_dashboard import AdminDashboardManager
from src.verified_dataset import VerifiedDatasetManager
from src.doctor_feedback import DoctorFeedbackManager
from src.predictor import MedicinePredictor

def test_phase8():
    print("="*60)
    print("      PHASE 8: ADMIN DASHBOARD & TRAINING TRIGGER TEST")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_verified_dir = Path(tmp_dir) / "doctor_verified"
        tmp_review_db = Path(tmp_dir) / "doctor_reviews.json"
        tmp_admin_db = Path(tmp_dir) / "admin_status.json"

        dataset_mgr = VerifiedDatasetManager(verified_dir_path=str(tmp_verified_dir))
        fb_mgr = DoctorFeedbackManager(feedback_db_path=str(tmp_review_db))
        predictor = MedicinePredictor()

        # Instantiate Admin Manager with MIN_NEW_SAMPLES = 5 for test purposes
        admin_mgr = AdminDashboardManager(
            verified_dataset_manager=dataset_mgr,
            status_db_path=str(tmp_admin_db),
            min_new_samples=5
        )

        # 1. Fetch Initial Dashboard Summary
        print("\n1. Fetching Initial Admin Dashboard Summary...")
        summary = admin_mgr.get_dashboard_summary()
        print(f"   - Active Model Version   : {summary['active_model_version']} ({summary['active_model_name']})")
        print(f"   - Current Metrics        : Accuracy={summary['current_accuracy']} | Macro-F1={summary['current_macro_f1']}")
        print(f"   - Training Status        : {summary['training_status']}")
        print(f"   - Verified Samples       : {summary['new_samples_since_last_training']} / {summary['min_new_samples_required']} required")
        print(f"   - Can Trigger Training?  : {summary['can_trigger_training']}")

        assert summary['training_status'] == "IDLE"
        assert summary['can_trigger_training'] is False  # 0 / 5 samples

        # 2. Attempt 'TRAIN MODEL' Trigger when Insufficient Samples Exist
        print("\n2. Attempting 'TRAIN MODEL' Trigger with Insufficient Data (0 / 5)...")
        trig_fail = admin_mgr.trigger_train_model()
        print(f"   - Trigger Success? : {trig_fail['success']}")
        print(f"   - Error Code       : {trig_fail['error_code']}")
        print(f"   - Rejection Msg    : \"{trig_fail['message']}\"")
        assert trig_fail['success'] is False
        assert trig_fail['error_code'] == "INSUFFICIENT_NEW_DATA"

        # 3. Add 5 Verified Samples to Dataset
        print("\n3. Adding 5 Verified Doctor Samples to Dataset...")
        for i in range(5):
            p = {"top_brand": "Vifas", "top_confidence": 0.95, "top_candidates": [{"brand_name": "Vifas", "confidence": 0.95}], "status": "high_confidence", "review_priority": "LOW"}
            t = fb_mgr.create_review_task(p, image_reference=f"data/prescriptions/sample_{i}.jpg")
            fb = fb_mgr.record_feedback(t["review_id"], "CONFIRM", "Vifas", predictor.class_names)
            dataset_mgr.append_verified_record(fb)

        summary_updated = admin_mgr.get_dashboard_summary()
        print(f"   - Updated Samples  : {summary_updated['new_samples_since_last_training']} / {summary_updated['min_new_samples_required']} required")
        print(f"   - Can Trigger Training?  : {summary_updated['can_trigger_training']}")
        assert summary_updated['can_trigger_training'] is True

        # 4. Trigger 'TRAIN MODEL' with Sufficient Samples
        print("\n4. Triggering 'TRAIN MODEL' with Sufficient Data (5 / 5)...")
        trig_pass = admin_mgr.trigger_train_model()
        print(f"   - Trigger Success? : {trig_pass['success']}")
        print(f"   - Assigned Job ID  : {trig_pass['job_id']}")
        print(f"   - Training Status  : {trig_pass['dashboard']['training_status']}")
        assert trig_pass['success'] is True
        assert trig_pass['dashboard']['training_status'] == "RUNNING"

        # 5. Verify Training Lock Blocks Duplicate Triggers
        print("\n5. Verifying Training Lock Blocks Duplicate Trigger Attempt...")
        trig_lock = admin_mgr.trigger_train_model()
        print(f"   - Trigger Success? : {trig_lock['success']}")
        print(f"   - Error Code       : {trig_lock['error_code']}")
        print(f"   - Lock Msg         : \"{trig_lock['message']}\"")
        assert trig_lock['success'] is False
        assert trig_lock['error_code'] == "TRAINING_IN_PROGRESS"

        # 6. Reset Lock Back to IDLE
        print("\n6. Resetting Training Lock back to IDLE...")
        admin_mgr.reset_training_lock("IDLE")
        assert admin_mgr.get_dashboard_summary()['training_status'] == "IDLE"
        print("   Lock reset cleanly!")

    print("\nPhase 8 Admin Dashboard & Training Trigger Verification Passed Cleanly!")

if __name__ == "__main__":
    test_phase8()
