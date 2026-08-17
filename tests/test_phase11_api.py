import sys
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.app import app

def test_phase11():
    print("="*60)
    print("      PHASE 11: COMPLETE FASTAPI BACKEND VERIFICATION")
    print("="*60)

    client = TestClient(app)

    # 1. Health Check
    print("\n1. Testing GET / (Health Check)...")
    res_health = client.get("/")
    print(f"   Response ({res_health.status_code}): {res_health.json()}")
    assert res_health.status_code == 200
    assert res_health.json()["system_status"] == "ONLINE"

    # 2. Prescription Prediction Endpoint POST /api/predict
    print("\n2. Testing POST /api/predict (Prescription Upload & Prediction)...")
    test_csv = PROJECT_ROOT / "data" / "merged_dataset" / "baseline_test.csv"
    sample_img_path = pd.read_csv(test_csv).iloc[0]['image_path']

    with open(sample_img_path, "rb") as f:
        res_pred = client.post("/api/predict", files={"file": ("prescription.jpg", f, "image/jpeg")})

    print(f"   Response Status Code: {res_pred.status_code}")
    data_pred = res_pred.json()
    print(f"   - Brand Output       : '{data_pred['prediction']['top_brand']}'")
    print(f"   - Generic Formulation: '{data_pred['prediction']['generic_name']}'")
    print(f"   - Confidence         : {data_pred['prediction']['top_confidence']*100:.2f}%")
    print(f"   - System Status      : '{data_pred['prediction']['status']}'")
    print(f"   - Review Priority    : '{data_pred['review_priority']}'")
    print(f"   - Doctor Review Link : {data_pred['doctor_review_url']}")

    assert res_pred.status_code == 200
    assert "prediction" in data_pred
    assert "secure_token" in data_pred
    token = data_pred["secure_token"]

    # 3. Doctor Priority Queue Endpoint GET /api/doctor/reviews
    print("\n3. Testing GET /api/doctor/reviews (Doctor Priority Queue)...")
    res_queue = client.get("/api/doctor/reviews")
    print(f"   Response Status Code: {res_queue.status_code}")
    pending_list = res_queue.json()["pending_reviews"]
    print(f"   Pending Review Queue Length: {len(pending_list)}")
    assert res_queue.status_code == 200
    assert len(pending_list) >= 1

    # 4. Resolve Secure Token GET /review/{token}
    print(f"\n4. Testing GET /review/{token} (Secure Token Resolution)...")
    res_token = client.get(f"/review/{token}")
    print(f"   Response Status Code: {res_token.status_code}")
    token_data = res_token.json()
    print(f"   - Token Valid : {token_data['token_valid']}")
    print(f"   - Token Used  : {token_data['token_used']}")
    print(f"   - Review ID   : {token_data['review_task']['review_id']}")
    assert res_token.status_code == 200
    assert token_data["token_valid"] is True

    # 5. Doctor Feedback Submission POST /api/doctor/feedback
    print("\n5. Testing POST /api/doctor/feedback (Doctor Submission)...")
    fb_payload = {
        "token": token,
        "doctor_action": "CONFIRM",
        "doctor_verified_label": "Esonix",
        "doctor_id": "dr_evans",
        "doctor_email": "dr.evans@hospital.org"
    }
    res_fb = client.post("/api/doctor/feedback", json=fb_payload)
    print(f"   Response Status Code: {res_fb.status_code}")
    data_fb = res_fb.json()
    print(f"   - Submission Message : \"{data_fb['message']}\"")
    print(f"   - Verified Record ID : {data_fb['verified_record_id']}")
    assert res_fb.status_code == 200
    assert data_fb["status"] == "SUCCESS"

    # Verify Consumed Token Rejection
    res_reused = client.post("/api/doctor/feedback", json=fb_payload)
    print(f"   - Token Reuse Rejection Status Code: {res_reused.status_code} (Expected 400)")
    assert res_reused.status_code == 400

    # 6. Admin Dashboard Endpoint GET /api/admin/dashboard
    print("\n6. Testing GET /api/admin/dashboard...")
    res_dash = client.get("/api/admin/dashboard")
    print(f"   Response Status Code: {res_dash.status_code}")
    dash_data = res_dash.json()
    print(f"   - Active Model     : {dash_data['active_model_version']}")
    print(f"   - Verified Samples : {dash_data['total_verified_samples']}")
    print(f"   - Confirmed Count  : {dash_data['confirmed_count']}")
    assert res_dash.status_code == 200

    # 7. Admin Retraining Trigger Gate POST /api/admin/train-model
    print("\n7. Testing POST /api/admin/train-model (Minimum Sample Protection)...")
    res_train = client.post("/api/admin/train-model", json={"force_override": False})
    print(f"   Response Status Code: {res_train.status_code} (Expected 400 for insufficient samples)")
    assert res_train.status_code == 400

    # 8. Admin Model Registry GET /api/admin/model-registry
    print("\n8. Testing GET /api/admin/model-registry...")
    res_reg = client.get("/api/admin/model-registry")
    print(f"   Response Status Code: {res_reg.status_code}")
    reg_data = res_reg.json()
    print(f"   - Active Version: {reg_data['active_production_version']}")
    print(f"   - Registered Versions Count: {len(reg_data['versions'])}")
    assert res_reg.status_code == 200

    print("\nPhase 11 FastAPI Backend Verification Passed Cleanly!")

if __name__ == "__main__":
    test_phase11()
