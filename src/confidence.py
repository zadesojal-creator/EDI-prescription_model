"""
Confidence level evaluation and Doctor Review Priority assignment.
Enforces the 3-tiered safety rules for healthcare decision support.
"""

# Thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.90
MEDIUM_CONFIDENCE_THRESHOLD = 0.70

def evaluate_confidence(confidence: float) -> dict:
    """
    Evaluates raw prediction confidence (0.0 to 1.0) and assigns:
    - status
    - doctor_feedback_required
    - doctor_verification_required
    - review_priority
    - user_message / display instruction
    """
    if confidence >= HIGH_CONFIDENCE_THRESHOLD:
        return {
            "status": "high_confidence",
            "doctor_feedback_required": True,
            "doctor_verification_required": False,
            "review_priority": "LOW",
            "user_message": "AI prediction complete. Low-priority doctor feedback task queued.",
            "is_definitive_display": True
        }
    elif confidence >= MEDIUM_CONFIDENCE_THRESHOLD:
        return {
            "status": "medium_confidence",
            "doctor_feedback_required": True,
            "doctor_verification_required": False,
            "review_priority": "MEDIUM",
            "user_message": "AI prediction complete (Doctor verification recommended). Medium-priority review queued.",
            "is_definitive_display": True
        }
    else:
        return {
            "status": "doctor_verification_required",
            "doctor_feedback_required": True,
            "doctor_verification_required": True,
            "review_priority": "HIGH",
            "user_message": "Doctor Verification Required. The AI could not confidently identify the handwritten medicine.",
            "is_definitive_display": False
        }
