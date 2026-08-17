import sys
import tempfile
import json
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.training import CloudModelTrainer

def test_phase9():
    print("="*60)
    print("      PHASE 9: CLOUD TRAINING & ORCHESTRATION VERIFICATION")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        tmp_catalog = tmp_dir_path / "verified_catalog.json"
        tmp_output_dir = tmp_dir_path / "training_runs"
        tmp_img = tmp_dir_path / "valid_sample.jpg"

        # Create a valid test image
        Image.new('RGB', (100, 100), (255, 255, 255)).save(tmp_img)

        # Create mock verified dataset records
        records = [
            {"review_id": "r1", "image_reference": str(tmp_img), "doctor_verified_label": "Vifas", "status": "CONFIRMED"},
            {"review_id": "r2", "image_reference": "data/non_existent.jpg", "doctor_verified_label": "Ace", "status": "CORRECTED"}
        ]
        with open(tmp_catalog, "w", encoding="utf-8") as f:
            json.dump(records, f)

        trainer = CloudModelTrainer(
            verified_catalog_path=str(tmp_catalog),
            output_dir=str(tmp_output_dir)
        )

        # 1. Test Dataset Validation & Quality Check
        print("\n1. Running Dataset Quality Validation...")
        quality = trainer.validate_verified_dataset()
        print(f"   - Total Records   : {quality['total_records']}")
        print(f"   - Valid Records   : {quality['valid_records_count']}")
        print(f"   - Missing Images  : {quality['missing_images_count']}")
        assert quality['total_records'] == 2
        assert quality['valid_records_count'] == 1
        assert quality['missing_images_count'] == 1

        # 2. Test Candidate Model Generation
        print("\n2. Executing Candidate Model Training Workflow...")
        metrics = trainer.train_candidate_model(candidate_version="v2.0_test")

        print(f"   - Candidate Version : {metrics['candidate_version']}")
        print(f"   - Model Saved At    : {metrics['candidate_model_path']}")
        print(f"   - Candidate Accuracy: {metrics['accuracy']*100:.2f}%")
        print(f"   - Candidate Macro-F1: {metrics['macro_f1']:.4f}")

        assert Path(metrics['candidate_model_path']).exists()
        assert metrics['candidate_version'] == "v2.0_test"

    print("\nPhase 9 Cloud Training & Orchestration Verification Passed Cleanly!")

if __name__ == "__main__":
    test_phase9()
