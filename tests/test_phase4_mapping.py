import sys
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.medicine_mapping import GenericMedicineMapper
from src.predictor import MedicinePredictor

def test_phase4():
    print("="*60)
    print("      PHASE 4: GENERIC MEDICINE MAPPING VERIFICATION")
    print("="*60)

    # 1. Verify CSV Data File
    csv_path = PROJECT_ROOT / "data" / "medicine_mapping.csv"
    print(f"\n1. Verifying Mapping CSV File at {csv_path}...")
    assert csv_path.exists(), "mapping CSV file must exist!"
    df = pd.read_csv(csv_path)
    print(f"   Total Mapped Brand Rows: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    assert len(df) == 78, "CSV must contain all 78 classes"
    assert "brand_name" in df.columns and "generic_name" in df.columns, "CSV structure invalid"

    # 2. Test Standalone GenericMedicineMapper
    print("\n2. Testing Standalone GenericMedicineMapper Class:")
    mapper = GenericMedicineMapper()

    # Known Verified Brand Lookups
    ace_info = mapper.get_generic_mapping("Ace")
    print(f"   Lookup 'Ace': {ace_info}")
    assert ace_info["generic_name"] == "Paracetamol"
    assert ace_info["mapping_status"] == "VERIFIED"

    vifas_info = mapper.get_generic_mapping("Vifas")
    print(f"   Lookup 'Vifas': {vifas_info}")
    assert vifas_info["generic_name"] == "Fexofenadine Hydrochloride"
    assert vifas_info["mapping_status"] == "VERIFIED"

    alatrol_info = mapper.get_generic_mapping("Alatrol")
    print(f"   Lookup 'Alatrol': {alatrol_info}")
    assert alatrol_info["generic_name"] == "Cetirizine Hydrochloride"

    # Unknown Brand Lookup
    unknown_info = mapper.get_generic_mapping("NonExistentDrug99")
    print(f"   Lookup 'NonExistentDrug99': {unknown_info}")
    assert unknown_info["generic_name"] is None
    assert unknown_info["mapping_status"] == "UNKNOWN_BRAND"

    # 3. Test Integration with MedicinePredictor
    print("\n3. Testing Integrated Predictor Output with Generic Mapping:")
    predictor = MedicinePredictor()
    test_csv = PROJECT_ROOT / "data" / "merged_dataset" / "baseline_test.csv"
    sample = pd.read_csv(test_csv).iloc[0]
    image_path = sample['image_path']

    res = predictor.predict(image_path)
    print("\n   Integrated Predictor Result Snapshot:")
    print(f"   - Brand Display Name   : '{res['top_brand']}'")
    print(f"   - Generic Formulation  : '{res['generic_name']}'")
    print(f"   - Mapping Status       : '{res['mapping_status']}'")
    print(f"   - Top Confidence       : {res['top_confidence']*100:.2f}%")
    print(f"   - Prediction Status    : '{res['status']}'")
    print("\n   Top-3 Candidates with Generic Formulations:")
    for i, cand in enumerate(res['top_candidates'], 1):
        print(f"     [{i}] Brand: {cand['brand_name']:<15} | Generic: {cand['generic_name']:<30} | Conf: {cand['confidence']*100:6.2f}%")

    assert res['generic_name'] is not None
    assert res['mapping_status'] == "VERIFIED"
    assert res['top_candidates'][0]['generic_name'] == res['generic_name']

    print("\nPhase 4 Generic Medicine Mapping Verification Passed Cleanly!")

if __name__ == "__main__":
    test_phase4()
