import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.confidence import evaluate_confidence
from src.predictor import MedicinePredictor

def test_phase3():
    print("="*60)
    print("      PHASE 3: CONFIDENCE LEVELS & PRIORITY LOGIC TEST")
    print("="*60)

    # 1. Test Pure Function Rules
    print("\n1. Testing Rule Threshold Evaluation Logic:")
    
    # High Confidence Case (96%)
    res_high = evaluate_confidence(0.96)
    print(f"   [0.96 Confidence]: Status='{res_high['status']}' | Priority='{res_high['review_priority']}' | Verification Required={res_high['doctor_verification_required']}")
    assert res_high['status'] == "high_confidence"
    assert res_high['review_priority'] == "LOW"
    assert res_high['doctor_verification_required'] is False

    # Medium Confidence Case (78%)
    res_med = evaluate_confidence(0.78)
    print(f"   [0.78 Confidence]: Status='{res_med['status']}' | Priority='{res_med['review_priority']}' | Verification Required={res_med['doctor_verification_required']}")
    assert res_med['status'] == "medium_confidence"
    assert res_med['review_priority'] == "MEDIUM"
    assert res_med['doctor_verification_required'] is False

    # Low Confidence Case (42%)
    res_low = evaluate_confidence(0.42)
    print(f"   [0.42 Confidence]: Status='{res_low['status']}' | Priority='{res_low['review_priority']}' | Verification Required={res_low['doctor_verification_required']}")
    assert res_low['status'] == "doctor_verification_required"
    assert res_low['review_priority'] == "HIGH"
    assert res_low['doctor_verification_required'] is True

    # 2. Integration Test with MedicinePredictor
    print("\n2. Testing MedicinePredictor Integration on Image...")
    predictor = MedicinePredictor()
    test_csv = PROJECT_ROOT / "data" / "merged_dataset" / "baseline_test.csv"
    df = pd.read_csv(test_csv)
    image_path = df.iloc[0]['image_path']

    out = predictor.predict(image_path)
    print("\n   Predictor Output Snapshot:")
    print(f"   - Brand Display Name        : '{out['top_brand']}'")
    print(f"   - Top Candidate Confidence  : {out['top_confidence']*100:.2f}%")
    print(f"   - System Prediction Status  : '{out['status']}'")
    print(f"   - Doctor Review Priority    : '{out['review_priority']}'")
    print(f"   - Doctor Verification Req.  : {out['doctor_verification_required']}")
    print(f"   - User UX Instruction       : \"{out['user_message']}\"")

    assert 'status' in out
    assert 'review_priority' in out
    assert 'doctor_verification_required' in out

    print("\nPhase 3 Confidence & Priority Verification Passed Cleanly!")

if __name__ == "__main__":
    test_phase3()
