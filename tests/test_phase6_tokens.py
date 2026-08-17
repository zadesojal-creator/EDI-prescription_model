import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.review_tokens import DoctorReviewTokenManager
from src.doctor_feedback import DoctorFeedbackManager

def test_phase6():
    print("="*60)
    print("      PHASE 6: SECURE TIME-LIMITED TOKENS VERIFICATION")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_token_db = Path(tmp_dir) / "test_tokens.json"
        tmp_review_db = Path(tmp_dir) / "test_reviews.json"

        token_mgr = DoctorReviewTokenManager(token_db_path=str(tmp_token_db))
        fb_mgr = DoctorFeedbackManager(feedback_db_path=str(tmp_review_db))

        # 1. Create a Review Task
        print("\n1. Creating Doctor Review Task...")
        pred = {
            "top_brand": "Vifas",
            "top_confidence": 0.42,
            "top_candidates": [{"brand_name": "Vifas", "confidence": 0.42}],
            "status": "doctor_verification_required",
            "review_priority": "HIGH"
        }
        task = fb_mgr.create_review_task(pred, image_reference="data/prescriptions/sample.jpg")
        print(f"   Created Task ID: {task['review_id']}")

        # 2. Generate Secure Token Link
        print("\n2. Generating Secure Review Token Link...")
        token_info = token_mgr.generate_review_token(task['review_id'], ttl_hours=24)
        print(f"   Generated Token: {token_info['token']}")
        print(f"   Review Link    : {token_info['review_url']}")
        print(f"   Expires At     : {token_info['expires_at']}")

        assert token_info['review_url'].startswith("/review/")
        assert len(token_info['token']) > 20

        # 3. Validate Token Resolution
        print("\n3. Validating Token Resolution...")
        valid_rec = token_mgr.validate_token(token_info['token'])
        assert valid_rec['review_id'] == task['review_id']
        fetched_task = fb_mgr.get_review_by_id(valid_rec['review_id'])
        print(f"   Resolved Review Task: ID={fetched_task['review_id']} | Brand={fetched_task['original_prediction']} | Priority={fetched_task['priority']}")
        assert fetched_task['priority'] == "HIGH"

        # 4. Test Expired Token Handling
        print("\n4. Testing Expired Token Rejection...")
        expired_token_info = token_mgr.generate_review_token(task['review_id'], ttl_hours=-1)  # Expired 1h ago
        try:
            token_mgr.validate_token(expired_token_info['token'])
            assert False, "Should have thrown ValueError for expired token"
        except ValueError as e:
            print(f"   Successfully caught expected expiration error: '{e}'")

        # 5. Test Invalid Token Handling
        print("\n5. Testing Invalid Token Handling...")
        try:
            token_mgr.validate_token("invalid_token_string_123")
            assert False, "Should have thrown KeyError for invalid token"
        except KeyError as e:
            print(f"   Successfully caught expected invalid token error: {e}")

        # 6. Test Consuming Token
        print("\n6. Testing Consuming Token on Feedback Submission...")
        consumed = token_mgr.consume_token(token_info['token'])
        print(f"   Token Consumed: used={consumed['used']} | used_at={consumed['used_at']}")
        assert consumed['used'] is True

    print("\nPhase 6 Secure Tokens & Review Interface Verification Passed Cleanly!")

if __name__ == "__main__":
    test_phase6()
