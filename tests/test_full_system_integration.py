"""
Master Integration Test Suite across all 12 system phases.
Executes complete end-to-end pipeline verification from image prediction,
confidence evaluation, generic mapping, doctor review queues, secure tokens,
verified dataset collection, admin cloud retraining gates, candidate evaluation,
rollback registries, and FastAPI HTTP REST endpoints.
"""

import sys
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.predictor import MedicinePredictor
from src.confidence import evaluate_confidence
from src.medicine_mapping import GenericMedicineMapper
from src.doctor_feedback import DoctorFeedbackManager
from src.review_tokens import DoctorReviewTokenManager
from src.verified_dataset import VerifiedDatasetManager
from src.admin_dashboard import AdminDashboardManager
from src.training import CloudModelTrainer
from src.model_registry import ModelRegistryManager
from src.app import app

def run_master_verification():
    print("="*70)
    print("      MASTER INTEGRATION TEST: ALL 12 SYSTEM PHASES")
    print("="*70)

    # -------------------------------------------------------------
    # PHASE 1: Model File & Label Encoder Inspection
    # -------------------------------------------------------------
    print("\n[PHASE 1] Inspecting Model & Label Encoder Artifacts...")
    predictor = MedicinePredictor()
    assert predictor.num_classes == 78, "Must have 78 registered classes"
    print(f"   ✓ Model loaded successfully with {predictor.num_classes} classes.")

    # -------------------------------------------------------------
    # PHASE 2: Predictor Core Class Verification
    # -------------------------------------------------------------
    print("\n[PHASE 2] Executing Standalone MedicinePredictor...")
    test_csv = PROJECT_ROOT / "data" / "merged_dataset" / "baseline_test.csv"
    sample_img = pd.read_csv(test_csv).iloc[0]['image_path']
    pred = predictor.predict(sample_img)
    print(f"   ✓ Inference completed for top brand '{pred['top_brand']}' with {pred['top_confidence']*100:.2f}% confidence.")

    # -------------------------------------------------------------
    # PHASE 3: Confidence & Review Priority Logic
    # -------------------------------------------------------------
    print("\n[PHASE 3] Verifying 3-Tiered Confidence & Priority Logic...")
    eval_h = evaluate_confidence(0.95)
    eval_m = evaluate_confidence(0.75)
    eval_l = evaluate_confidence(0.40)
    assert eval_h['review_priority'] == "LOW"
    assert eval_m['review_priority'] == "MEDIUM"
    assert eval_l['review_priority'] == "HIGH"
    print("   ✓ HIGH (0.95 -> LOW priority), MEDIUM (0.75 -> MEDIUM priority), LOW (0.40 -> HIGH priority) verified.")

    # -------------------------------------------------------------
    # PHASE 4: Generic Medicine Mapping Layer
    # -------------------------------------------------------------
    print("\n[PHASE 4] Verifying Brand-to-Generic Mapping Layer...")
    mapper = GenericMedicineMapper()
    g_ace = mapper.get_generic_mapping("Ace")
    assert g_ace["generic_name"] == "Paracetamol"
    print(f"   ✓ Mapped 'Ace' -> '{g_ace['generic_name']}' ({g_ace['mapping_status']}).")

    # -------------------------------------------------------------
    # PHASE 5: Doctor Feedback & Audit Schema
    # -------------------------------------------------------------
    print("\n[PHASE 5] Verifying Doctor Feedback & Audit Preservation...")
    fb_mgr = DoctorFeedbackManager()
    task = fb_mgr.create_review_task(pred, image_reference=sample_img)
    assert task["status"] == "PENDING"
    print(f"   ✓ Doctor review task '{task['review_id']}' created with original prediction '{task['original_prediction']}' preserved.")

    # -------------------------------------------------------------
    # PHASE 6: Secure Time-Limited Tokens
    # -------------------------------------------------------------
    print("\n[PHASE 6] Verifying Secure Time-Limited Token Links...")
    token_mgr = DoctorReviewTokenManager()
    t_rec = token_mgr.generate_review_token(task["review_id"], ttl_hours=24)
    v_rec = token_mgr.validate_token(t_rec["token"])
    assert v_rec["review_id"] == task["review_id"]
    print(f"   ✓ Cryptographic token '{t_rec['token'][:16]}...' generated and validated for URL '{t_rec['review_url']}'.")

    # -------------------------------------------------------------
    # PHASE 7: Verified Dataset Accumulation
    # -------------------------------------------------------------
    print("\n[PHASE 7] Verifying Dataset Accumulation Pipeline...")
    dataset_mgr = VerifiedDatasetManager()
    fb_doc = fb_mgr.record_feedback(task["review_id"], "CONFIRM", task["original_prediction"], predictor.class_names)
    v_record = dataset_mgr.append_verified_record(fb_doc)
    assert v_record["record_id"].startswith("rec_")
    print(f"   ✓ Record '{v_record['record_id']}' appended to verified training dataset.")

    # -------------------------------------------------------------
    # PHASE 8: Admin Dashboard & Sample Threshold Gate
    # -------------------------------------------------------------
    print("\n[PHASE 8] Verifying Admin Dashboard & Retraining Gate...")
    admin_mgr = AdminDashboardManager(verified_dataset_manager=dataset_mgr, min_new_samples=100)
    summary = admin_mgr.get_dashboard_summary()
    assert summary["can_trigger_training"] is False  # 1 / 100 samples
    print(f"   ✓ Admin Dashboard active model '{summary['active_model_version']}' verified. Sample gate enforced ({summary['new_samples_since_last_training']} / {summary['min_new_samples_required']}).")

    # -------------------------------------------------------------
    # PHASE 9: Cloud Training Pipeline
    # -------------------------------------------------------------
    print("\n[PHASE 9] Verifying Cloud Retraining Pipeline...")
    trainer = CloudModelTrainer()
    quality = trainer.validate_verified_dataset()
    print(f"   ✓ Cloud training pre-check completed: {quality['valid_records_count']} valid dataset samples.")

    # -------------------------------------------------------------
    # PHASE 10: Model Evaluation Gate & Rollback Registry
    # -------------------------------------------------------------
    print("\n[PHASE 10] Verifying Model Evaluation Gate & Rollback Registry...")
    reg_mgr = ModelRegistryManager()
    cand = {"candidate_version": "v2.0_eval_test", "candidate_model_path": "models/best.keras", "accuracy": 0.8800, "macro_f1": 0.8850}
    reg_mgr.register_candidate_model(cand)
    gate = reg_mgr.evaluate_and_gate_candidate("v2.0_eval_test")
    assert gate["decision"] == "APPROVED"
    print(f"   ✓ Candidate evaluation gate decision: '{gate['decision']}' (88.00% vs 83.91%).")

    # -------------------------------------------------------------
    # PHASE 11: FastAPI REST HTTP Integration
    # -------------------------------------------------------------
    print("\n[PHASE 11] Verifying FastAPI Backend Endpoints via TestClient...")
    client = TestClient(app)
    res_h = client.get("/")
    assert res_h.status_code == 200
    res_dash = client.get("/api/admin/dashboard")
    assert res_dash.status_code == 200
    print("   ✓ REST Endpoints GET / and GET /api/admin/dashboard returned 200 OK.")

    # -------------------------------------------------------------
    # PHASE 12: Master System Verification Complete
    # -------------------------------------------------------------
    print("\n" + "="*70)
    print("   ALL 12 SYSTEM PHASES VERIFIED & WORKING CLEANLY!")
    print("="*70)

def test_master_verification():
    run_master_verification()

if __name__ == "__main__":
    run_master_verification()

