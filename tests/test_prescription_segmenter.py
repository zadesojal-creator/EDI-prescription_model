import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.segmenter import PrescriptionLineSegmenter
from src.predictor import MedicinePredictor

def test_prescription_segmenter():
    print("="*60)
    print("      VERIFICATION: MULTI-LINE PRESCRIPTION SEGMENTER")
    print("="*60)

    sample_img = PROJECT_ROOT / "data" / "sample_prescription_multiline.png"
    assert sample_img.exists(), "Sample prescription image does not exist."

    # 1. Test PrescriptionLineSegmenter
    segmenter = PrescriptionLineSegmenter()
    res = segmenter.segment_prescription_lines(str(sample_img))

    print(f"1. Is Multi-Line Prescription: {res['is_multi_line']}")
    print(f"2. Total Medicines Detected  : {res['total_medicines_detected']}")
    assert res['is_multi_line'] is True
    assert res['total_medicines_detected'] >= 2

    # 2. Test MedicinePredictor.predict_full_prescription
    print("\n3. Testing Full Multi-Line Prescription Prediction...")
    predictor = MedicinePredictor()
    pred_res = predictor.predict_full_prescription(str(sample_img))

    print(f"   - Message: {pred_res['message']}")
    print(f"   - Total Medicines: {pred_res['total_medicines_detected']}")

    for m in pred_res["medicines"]:
        line_no = m["line_number"]
        top_b = m["prediction"]["top_brand"]
        conf = float(m["prediction"]["top_confidence"]) * 100
        g_name = m["prediction"].get("generic_name") or "N/A"
        print(f"   Line #{line_no}: Top Brand='{top_b}' ({conf:.1f}%), Generic='{g_name}'")

    print("\nMulti-Line Prescription Line Segmenter Verification Passed Cleanly!")

if __name__ == "__main__":
    test_prescription_segmenter()
