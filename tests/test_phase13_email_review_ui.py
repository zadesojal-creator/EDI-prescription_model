import sys
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.app import app
from src.email_service import DoctorEmailNotifier

def test_email_and_review_ui():
    print("="*60)
    print("      VERIFICATION: DOCTOR EMAIL & WEB REVIEW PORTAL")
    print("="*60)

    client = TestClient(app)

    # 1. Test POST /api/predict with doctor_email parameter
    print("\n1. Testing POST /api/predict with Doctor Email Notification...")
    test_csv = PROJECT_ROOT / "data" / "merged_dataset" / "baseline_test.csv"
    sample_img_path = pd.read_csv(test_csv).iloc[0]['image_path']

    with open(sample_img_path, "rb") as f:
        res_pred = client.post(
            "/api/predict?doctor_email=dr.smith@hospital.org",
            files={"file": ("prescription.jpg", f, "image/jpeg")}
        )

    print(f"   Response Status Code: {res_pred.status_code}")
    assert res_pred.status_code == 200
    data_pred = res_pred.json()

    print(f"   - Doctor Review Link : {data_pred['doctor_review_url']}")
    print(f"   - Email Sent To      : {data_pred['email_notification']['to']}")
    print(f"   - Email Subject      : {data_pred['email_notification']['subject']}")
    print(f"   - Email Status       : {data_pred['email_notification']['email_status']}")


    assert "email_notification" in data_pred
    assert data_pred["email_notification"]["to"] == "dr.smith@hospital.org"
    token = data_pred["secure_token"]

    # 2. Verify Email Log in data/sent_emails/doctor_emails.json
    print("\n2. Verifying Email Log Storage...")
    notifier = DoctorEmailNotifier()
    logs = notifier._read_logs()
    print(f"   Total Email Logs Saved: {len(logs)}")
    assert len(logs) >= 1
    assert logs[-1]["to"] == "dr.smith@hospital.org"

    # 3. Test GET /review/{token} (HTML Web Portal view for Doctor)
    print("\n3. Testing GET /review/{token} (Browser HTML Render)...")
    res_html = client.get(f"/review/{token}", headers={"accept": "text/html"})
    print(f"   Response Status Code: {res_html.status_code}")
    print(f"   Content Type: {res_html.headers.get('content-type')}")
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers.get("content-type", "")
    assert "Doctor Review Portal" in res_html.text
    assert "Prescription Verification" in res_html.text

    # 4. Test Doctor Submitting CONFIRM action via Web Portal Payload
    print("\n4. Testing Doctor Submitting CONFIRM Action...")
    fb_payload = {
        "token": token,
        "doctor_action": "CONFIRM",
        "doctor_verified_label": data_pred["prediction"]["top_brand"],
        "doctor_id": "dr_smith",
        "doctor_email": "dr.smith@hospital.org"
    }
    res_fb = client.post("/api/doctor/feedback", json=fb_payload)
    print(f"   Response Status Code: {res_fb.status_code}")
    assert res_fb.status_code == 200
    assert res_fb.json()["status"] == "SUCCESS"

    # 5. Verify Token Reused Rejection in Browser
    print("\n5. Verifying Used Token View in Browser...")
    res_html_used = client.get(f"/review/{token}", headers={"accept": "text/html"})
    assert "This review link has already been submitted" in res_html_used.text
    print("   Successfully rendered used token warning in browser HTML!")

    print("\nDoctor Email Notification & Interactive Web Portal Verification Passed Cleanly!")

if __name__ == "__main__":
    test_email_and_review_ui()
