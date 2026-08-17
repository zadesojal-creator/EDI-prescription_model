import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.model_registry import ModelRegistryManager

def test_phase10():
    print("="*60)
    print("      PHASE 10: MODEL EVALUATION GATE & ROLLBACK TEST")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_registry_db = Path(tmp_dir) / "model_registry.json"
        reg_mgr = ModelRegistryManager(registry_db_path=str(tmp_registry_db))

        # 1. Verify Active Initial Model v1.0
        print("\n1. Verifying Initial Production Model v1.0:")
        init_prod = reg_mgr.get_active_production_model()
        print(f"   - Active Version : {init_prod['version']}")
        print(f"   - Model Name     : {init_prod['model_name']}")
        print(f"   - Accuracy       : {init_prod['accuracy']*100:.2f}%")
        print(f"   - Status         : {init_prod['status']}")
        assert init_prod['version'] == "v1.0"
        assert init_prod['status'] == "PRODUCTION"

        # 2. Register and Evaluate Superior Candidate v2.0 (87.3% Accuracy)
        print("\n2. Registering and Evaluating Superior Candidate v2.0 (87.3% Acc vs 83.91% Prod)...")
        cand_v2 = {
            "candidate_version": "v2.0",
            "model_name": "EfficientNetB0",
            "candidate_model_path": "models/efficientnetb0_v2.0.keras",
            "accuracy": 0.8730,
            "macro_f1": 0.8750,
            "dataset_samples_used": 120
        }
        reg_mgr.register_candidate_model(cand_v2)

        gate_eval_v2 = reg_mgr.evaluate_and_gate_candidate("v2.0")
        print(f"   - Gate Decision : {gate_eval_v2['decision']}")
        print(f"   - Gate Message  : \"{gate_eval_v2['message']}\"")
        assert gate_eval_v2['decision'] == "APPROVED"

        # 3. Promote v2.0 to Production
        print("\n3. Promoting APPROVED v2.0 to PRODUCTION...")
        prom_res = reg_mgr.promote_to_production("v2.0")
        print(f"   - Active Version : {prom_res['active_version']}")
        print(f"   - Status Message : \"{prom_res['message']}\"")
        assert reg_mgr.get_active_production_model()['version'] == "v2.0"

        # 4. Register and Evaluate Inferior Candidate v3.0 (79.0% Accuracy)
        print("\n4. Registering and Evaluating Inferior Candidate v3.0 (79.0% Acc vs 87.3% Prod)...")
        cand_v3 = {
            "candidate_version": "v3.0",
            "model_name": "EfficientNetB0",
            "candidate_model_path": "models/efficientnetb0_v3.0.keras",
            "accuracy": 0.7900,
            "macro_f1": 0.7700,
            "dataset_samples_used": 150
        }
        reg_mgr.register_candidate_model(cand_v3)

        gate_eval_v3 = reg_mgr.evaluate_and_gate_candidate("v3.0")
        print(f"   - Gate Decision : {gate_eval_v3['decision']}")
        print(f"   - Gate Message  : \"{gate_eval_v3['message']}\"")
        assert gate_eval_v3['decision'] == "REJECTED"
        assert reg_mgr.get_active_production_model()['version'] == "v2.0"  # Retained v2.0!

        # 5. Test Rollback from v2.0 back to v1.0
        print("\n5. Testing Rollback Trigger (v2.0 -> v1.0)...")
        rollback_res = reg_mgr.rollback_production("v1.0")
        print(f"   - Previous Version : {rollback_res['previous_version']}")
        print(f"   - Active Version   : {rollback_res['active_version']}")
        print(f"   - Rollback Message : \"{rollback_res['message']}\"")
        assert reg_mgr.get_active_production_model()['version'] == "v1.0"

        all_vers = reg_mgr.list_all_versions()
        print(f"\n   Total Registered Versions: {len(all_vers)}")
        for v in all_vers:
            print(f"     - Version {v['version']:<6} | Status: {v['status']:<12} | Accuracy: {v['accuracy']*100:.2f}%")

    print("\nPhase 10 Model Evaluation Gate & Rollback Verification Passed Cleanly!")

if __name__ == "__main__":
    test_phase10()
