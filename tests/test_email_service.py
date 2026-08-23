import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.email_service import DoctorEmailNotifier

def test_email_service_unit():
    print("="*60)
    print("      UNIT TESTS: DOCTOR EMAIL NOTIFICATION SERVICE")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_log = Path(tmp_dir) / "test_sent_emails.json"
        notifier = DoctorEmailNotifier(email_log_path=str(tmp_log))

        mock_task_high = {
            "review_id": "rev_high_001",
            "prescription_id": "rx_001",
            "original_prediction": "Vifas",
            "original_confidence": 0.42,
            "priority": "HIGH",
            "prediction_status": "doctor_verification_required",
            "top_3_predictions": [
                {"brand_name": "Vifas", "confidence": 0.42, "generic_name": "Fexofenadine Hydrochloride"},
                {"brand_name": "Ace", "confidence": 0.31, "generic_name": "Paracetamol"},
                {"brand_name": "Filmet", "confidence": 0.12, "generic_name": "Metronidazole"}
            ]
        }
        mock_token = {"token": "test_token_1234567890", "review_url": "/review/test_token_1234567890"}

        # 1. Subject for HIGH Priority
        print("\n1. Testing Priority Subjects:")
        subj_h = notifier.get_subject_for_priority("HIGH")
        print(f"   - HIGH Subject   : '{subj_h}'")
        assert subj_h == "URGENT — Medicine Verification Required"

        subj_m = notifier.get_subject_for_priority("MEDIUM")
        print(f"   - MEDIUM Subject : '{subj_m}'")
        assert subj_m == "Medicine Verification Review Required"

        subj_l = notifier.get_subject_for_priority("LOW")
        print(f"   - LOW Subject    : '{subj_l}'")
        assert subj_l == "Medicine Prediction Confirmation Request"

        # 2. Email Body & Content Generation
        print("\n2. Testing Email Body Generation:")
        content = notifier.generate_email_content("doc@example.com", mock_task_high, mock_token)

        assert content["to"] == "doc@example.com"
        assert content["subject"] == "URGENT — Medicine Verification Required"
        assert "http://localhost:8000/review/test_token_1234567890" in content["review_url"]
        assert "Vifas" in content["plain_body"]
        assert "42.0%" in content["plain_body"]

        # Verify no unnecessary patient PII
        for pii in ["patient_name", "ssn", "phone", "address"]:
            assert pii not in content["plain_body"].lower()

        print("   ✓ Email body, URLs, and privacy checks passed.")

        # 3. Test EMAIL_ENABLED=false (Mock mode)
        print("\n3. Testing EMAIL_ENABLED=false Dev/Test Mode:")
        with patch.dict(os.environ, {"EMAIL_ENABLED": "false", "DOCTOR_EMAIL": "doc@example.com"}):
            res_disabled = notifier.send_doctor_review_email(mock_task_high, mock_token)
            print(f"   - Status: {res_disabled['email_status']}")
            assert res_disabled["email_status"] == "DISABLED"

        # 4. Test Duplicate Email Prevention
        print("\n4. Testing Duplicate Email Prevention:")
        mock_task_dup = {"review_id": "rev_dup_002", "priority": "MEDIUM", "original_prediction": "Ace", "original_confidence": 0.80}

        # First Dispatch (In mock/disabled mode)
        with patch.dict(os.environ, {"EMAIL_ENABLED": "false"}):
            res_1 = notifier.send_doctor_review_email(mock_task_dup, mock_token, force_resend=True)
            assert res_1["notification_status"] in ["DISABLED", "LOGGED_LOCAL_MOCK"]

        # Manually mark as SENT in log file to test duplicate detection
        logs = notifier._read_logs()
        logs[-1]["notification_status"] = "SENT"
        notifier._write_logs(logs)

        # Second Dispatch attempt (Should be blocked as SKIPPED_DUPLICATE)
        with patch.dict(os.environ, {"EMAIL_ENABLED": "false"}):
            res_2 = notifier.send_doctor_review_email(mock_task_dup, mock_token)
            print(f"   - Second Dispatch Status: {res_2['email_status']} ({res_2['message']})")
            assert res_2["email_status"] == "SKIPPED_DUPLICATE"


        # 5. Test Non-crashing SMTP Failure Handling
        print("\n5. Testing Non-Crashing SMTP Failure Handling:")
        with patch.dict(os.environ, {
            "EMAIL_ENABLED": "true",
            "SMTP_HOST": "invalid_smtp_server_domain_9999.xyz",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test_user",
            "SMTP_PASSWORD": "test_password"
        }):
            mock_task_fail = {"review_id": "rev_fail_003", "priority": "LOW", "original_prediction": "Alatrol"}
            res_fail = notifier.send_doctor_review_email(mock_task_fail, mock_token)
            print(f"   - Failure Status: {res_fail['email_status']}")
            print(f"   - Caught Error  : \"{res_fail['email_error']}\"")
            assert res_fail["email_status"] == "FAILED"
            assert res_fail["email_error"] is not None

        print("\nAll Doctor Email Notification Service Unit Tests Passed Cleanly!")

if __name__ == "__main__":
    test_email_service_unit()
