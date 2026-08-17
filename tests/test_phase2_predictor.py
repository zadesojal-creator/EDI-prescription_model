import sys
from pathlib import Path
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.predictor import MedicinePredictor

def test_phase2():
    print("="*60)
    print("      PHASE 2: STANDALONE MEDICINE PREDICTOR VERIFICATION")
    print("="*60)

    print("\n1. Instantiating MedicinePredictor...")
    predictor = MedicinePredictor()
    print(f"   Model loaded successfully!")
    print(f"   Number of registered classes: {predictor.num_classes}")

    # Load a test image from dataset
    test_csv = PROJECT_ROOT / "data" / "merged_dataset" / "baseline_test.csv"
    df = pd.read_csv(test_csv)
    sample = df.iloc[0]
    image_path = sample['image_path']
    true_label_idx = sample['label']
    true_brand_name = predictor.class_names[true_label_idx]

    print(f"\n2. Running inference on test image: {image_path}")
    print(f"   Ground Truth Label: {true_brand_name}")

    result = predictor.predict(image_path, top_k=3)

    print("\n" + "-"*50)
    print("   PREDICTOR OUTPUT DICTIONARY:")
    print("-"*50)
    print(f"   Top Predicted Brand: {result['top_brand']}")
    print(f"   Top Confidence     : {result['top_confidence']*100:.2f}%")
    print("\n   Top-3 Candidates:")
    for i, candidate in enumerate(result['top_candidates'], 1):
        print(f"     [{i}] {candidate['brand_name']:<20} | Confidence: {candidate['confidence']*100:6.2f}%")
    print("-"*50)

    # Verification assertions
    assert result['top_brand'] == true_brand_name, f"Expected {true_brand_name}, got {result['top_brand']}"
    assert 0.0 <= result['top_confidence'] <= 1.0, "Confidence must be between 0 and 1"
    assert len(result['top_candidates']) == 3, "Should return exactly 3 top candidates"
    assert len(result['raw_probabilities']) == 78, "Should return 78 raw probabilities"

    print("\nPhase 2 Verification Passed Cleanly!")

if __name__ == "__main__":
    test_phase2()
