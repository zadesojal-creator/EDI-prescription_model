"""
Integration and Unit Tests for Free Medicine Information API Integration (RxNorm + openFDA).
Verifies:
1. Exact medicine lookup (Paracetamol)
2. Brand medicine normalization (Dolo 650)
3. OCR spelling error fuzzy matching (Azithromicin -> Azithromycin)
4. Unknown medicine handling (xyzmedicine123)
5. Empty input handling ("")
6. API failure resilience (simulated timeout/offline fallback)
7. Missing FDA fields handling
8. SQLite cache persistence
"""

import pytest
from unittest.mock import patch, MagicMock
from src.medicine_info_service import MedicineInfoService

@pytest.fixture
def service(tmp_path):
    db_file = tmp_path / "test_medicine_info_cache.db"
    return MedicineInfoService(db_path=db_file)

def test_exact_medicine_lookup(service):
    """Test 1: Exact medicine name (e.g. Paracetamol)."""
    res = service.get_medicine_info("Paracetamol")
    assert res["status"] in ["SUCCESS", "LOW_CONFIDENCE"]
    assert res["normalized_name"].lower() in ["paracetamol", "acetaminophen"] or (res.get("generic_name") and "paracetamol" in res["generic_name"].lower())
    assert "input_name" in res
    assert "indications" in res
    assert "warnings" in res
    assert "contraindications" in res
    assert "adverse_reactions" in res

def test_brand_medicine_normalization(service):
    """Test 2: Brand medicine normalization (e.g. Dolo 650)."""
    res = service.get_medicine_info("Dolo 650")
    assert res["input_name"] == "Dolo 650"
    assert res["strength"] == "650" or "Dolo" in res["normalized_name"]
    assert res["match_confidence"] > 0.0

def test_ocr_spelling_error_fuzzy_matching(service):
    """Test 3: OCR spelling error (e.g. 'Azithromicin')."""
    res = service.get_medicine_info("Azithromicin")
    assert "Azithromycin" in res["normalized_name"] or res["match_confidence"] >= 0.70

def test_unknown_medicine_handling(service):
    """Test 4: Unknown or non-existent medicine (e.g. xyzmedicine123)."""
    res = service.get_medicine_info("xyzmedicine123")
    assert res["status"] in ["LOW_CONFIDENCE", "API_UNAVAILABLE"]
    assert res["requires_doctor_review"] is True
    assert res["match_confidence"] < 0.75

def test_empty_input_handling(service):
    """Test 5: Empty input ("")."""
    res = service.get_medicine_info("")
    assert res["status"] == "LOW_CONFIDENCE"
    assert res["requires_doctor_review"] is True
    assert res["input_name"] == ""

@patch("requests.get")
def test_api_failure_resilience(mock_get, service):
    """Test 6: API failure (simulated timeout / network failure)."""
    mock_get.side_effect = Exception("Simulated Network Timeout / RxNorm Offline")
    res = service.get_medicine_info("Paracetamol")
    
    assert res["status"] in ["SUCCESS", "API_UNAVAILABLE", "LOW_CONFIDENCE"]
    assert "requires_doctor_review" in res

def test_missing_fda_fields_handling(service):
    """Test 7: Missing FDA fields handling (must return empty lists without failing)."""
    clean_fda = service._clean_fda_text_list(None)
    assert clean_fda == []

    clean_fda_empty = service._clean_fda_text_list([])
    assert clean_fda_empty == []

def test_sqlite_cache_persistence(service):
    """Test 8: SQLite Caching layer (second lookup returns from_cache=True)."""
    res1 = service.get_medicine_info("Amoxicillin")
    assert res1 is not None

    res2 = service.get_medicine_info("Amoxicillin")
    assert res2.get("from_cache") is True
    assert res2["input_name"] == "Amoxicillin"
