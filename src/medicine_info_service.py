"""
Free Medicine Information Service (RxNorm + openFDA Integration).
Retrieves standardized drug names, RxCUIs, active generic chemical formulations,
indications, warnings, contraindications, adverse reactions, and drug interactions
using free public APIs (RxNorm & openFDA).
Includes RapidFuzz fuzzy matching, SQLite caching, and graceful offline fallback.
"""

import os
import re
import json
import sqlite3
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
try:
    from rapidfuzz import fuzz
except ImportError:
    from difflib import SequenceMatcher
    class FuzzFallback:
        @staticmethod
        def ratio(s1: str, s2: str) -> float:
            return SequenceMatcher(None, s1, s2).ratio() * 100.0
    fuzz = FuzzFallback()

logger = logging.getLogger("MedicineInfoService")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "medicine_info_cache.db"
MAPPING_CSV = PROJECT_ROOT / "data" / "medicine_mapping.csv"

# Free Public API URLs
RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"
OPENFDA_BASE_URL = "https://api.fda.gov/drug/label.json"

class MedicineInfoService:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.local_brands = self._load_local_brand_mapping()

    def _init_db(self):
        """Initializes the SQLite database cache for medicine information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medicine_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    input_name TEXT UNIQUE NOT NULL,
                    normalized_name TEXT,
                    generic_name TEXT,
                    rxcui TEXT,
                    strength TEXT,
                    dosage_form TEXT,
                    indications TEXT,
                    warnings TEXT,
                    contraindications TEXT,
                    adverse_reactions TEXT,
                    drug_interactions TEXT,
                    raw_source TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _load_local_brand_mapping(self) -> Dict[str, str]:
        """Loads 78 local brand-to-generic mapping CSV if available."""
        mapping = {}
        if MAPPING_CSV.exists():
            try:
                import csv
                with open(MAPPING_CSV, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        brand = row.get("brand_name", "").strip()
                        generic = row.get("generic_name", "").strip()
                        if brand:
                            mapping[brand.lower()] = generic
            except Exception as e:
                logger.warning(f"Could not load local medicine_mapping.csv: {e}")
        return mapping

    def clean_medicine_name(self, text: str) -> str:
        """Strips strength, dosage numbers, and special characters from input string."""
        if not text:
            return ""
        # Remove strength numbers like 650mg, 500 mg, 100ml, 5ml, 10mg/5ml
        cleaned = re.sub(r'\d+(\.\d+)?\s*(mg|g|ml|mcg|iu|%)\b', '', text, flags=re.IGNORECASE)
        # Remove plain trailing digits (e.g. Dolo 650 -> Dolo)
        cleaned = re.sub(r'\b\d+\b', '', cleaned)
        # Remove punctuation except spaces
        cleaned = re.sub(r'[^\w\s]', '', cleaned).strip()
        return cleaned or text.strip()

    def extract_strength_and_form(self, text: str) -> Dict[str, Optional[str]]:
        """Extracts strength and dosage form from raw input string."""
        strength_match = re.search(r'\b\d+(\.\d+)?\s*(mg|g|ml|mcg|iu|%)\b', text, re.IGNORECASE)
        form_match = re.search(r'\b(tablet|tab|capsule|cap|syrup|syr|injection|inj|cream|ointment|drops|drop|suspension)\b', text, re.IGNORECASE)
        
        strength = strength_match.group(0).strip() if strength_match else None
        dosage_form = form_match.group(0).strip().capitalize() if form_match else None
        return {"strength": strength, "dosage_form": dosage_form}

    def get_cached_info(self, input_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached medicine information from SQLite database."""
        key = input_name.strip().lower()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM medicine_cache WHERE LOWER(input_name) = ?", (key,))
            row = cursor.fetchone()
            if row:
                return {
                    "status": "SUCCESS" if row[13] >= 0.75 else "LOW_CONFIDENCE",
                    "input_name": row[1],
                    "normalized_name": row[2],
                    "generic_name": row[3],
                    "rxcui": row[4],
                    "strength": row[5],
                    "dosage_form": row[6],
                    "indications": json.loads(row[7]) if row[7] else [],
                    "warnings": json.loads(row[8]) if row[8] else [],
                    "contraindications": json.loads(row[9]) if row[9] else [],
                    "adverse_reactions": json.loads(row[10]) if row[10] else [],
                    "drug_interactions": json.loads(row[11]) if row[11] else [],
                    "source": json.loads(row[12]) if row[12] else {"normalization": "RxNorm", "clinical_label": "openFDA"},
                    "match_confidence": row[13],
                    "requires_doctor_review": row[13] < 0.75,
                    "from_cache": True
                }
        return None

    def save_cached_info(self, input_name: str, data: Dict[str, Any]):
        """Saves medicine info to SQLite cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO medicine_cache (
                    input_name, normalized_name, generic_name, rxcui, strength, dosage_form,
                    indications, warnings, contraindications, adverse_reactions, drug_interactions,
                    raw_source, confidence, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                input_name.strip(),
                data.get("normalized_name"),
                data.get("generic_name"),
                data.get("rxcui"),
                data.get("strength"),
                data.get("dosage_form"),
                json.dumps(data.get("indications", [])),
                json.dumps(data.get("warnings", [])),
                json.dumps(data.get("contraindications", [])),
                json.dumps(data.get("adverse_reactions", [])),
                json.dumps(data.get("drug_interactions", [])),
                json.dumps(data.get("source", {})),
                data.get("match_confidence", 0.0)
            ))
            conn.commit()

    def query_rxnorm_api(self, medicine_name: str) -> Dict[str, Any]:
        """
        Queries RxNorm/RxNav REST API for drug normalization and RxCUI retrieval.
        Handles exact match, approximate term match, and property retrieval.
        """
        clean_name = self.clean_medicine_name(medicine_name)
        if not clean_name:
            return {"rxcui": None, "normalized_name": medicine_name, "confidence": 0.0}

        try:
            # 1. Try Exact RxCUI search
            url = f"{RXNORM_BASE_URL}/rxcui.json"
            resp = requests.get(url, params={"name": clean_name}, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                rxcui_list = data.get("idGroup", {}).get("rxnormId", [])
                if rxcui_list:
                    rxcui = rxcui_list[0]
                    # Fetch concept properties
                    prop_url = f"{RXNORM_BASE_URL}/rxcui/{rxcui}/properties.json"
                    prop_resp = requests.get(prop_url, timeout=4.0)
                    norm_name = clean_name
                    if prop_resp.status_code == 200:
                        prop_data = prop_resp.json().get("properties", {})
                        norm_name = prop_data.get("name", clean_name)
                    
                    return {
                        "rxcui": rxcui,
                        "normalized_name": norm_name,
                        "confidence": 0.98
                    }

            # 2. Try Approximate Term search (for misspelled OCR text like "Azithromicin")
            approx_url = f"{RXNORM_BASE_URL}/approximateTerm.json"
            approx_resp = requests.get(approx_url, params={"term": clean_name, "maxEntries": 3}, timeout=4.0)
            if approx_resp.status_code == 200:
                approx_data = approx_resp.json()
                candidates = approx_data.get("approximateGroup", {}).get("candidate", [])
                if candidates:
                    best_candidate = candidates[0]
                    rxcui = best_candidate.get("rxcui")
                    candidate_name = best_candidate.get("candidate", clean_name)
                    # Compute string similarity
                    score = fuzz.ratio(clean_name.lower(), candidate_name.lower()) / 100.0
                    return {
                        "rxcui": rxcui,
                        "normalized_name": candidate_name,
                        "confidence": round(score, 2)
                    }

        except Exception as e:
            logger.warning(f"RxNorm API request failed for '{medicine_name}': {e}")

        # Local brand mapping fallback if RxNorm API returns no match or fails
        local_generic = self.local_brands.get(clean_name.lower())
        if local_generic:
            return {
                "rxcui": "LOCAL_MAPPED",
                "normalized_name": medicine_name.strip(),
                "generic_name": local_generic,
                "confidence": 0.90
            }

        return {"rxcui": None, "normalized_name": medicine_name.strip(), "confidence": 0.50}

    def query_openfda_api(self, generic_name: str, brand_name: str) -> Dict[str, List[str]]:
        """
        Queries openFDA Drug Label API for indications, warnings, contraindications,
        adverse reactions, and drug interactions.
        Gracefully handles missing fields and returns empty lists.
        """
        empty_info = {
            "indications": [],
            "warnings": [],
            "contraindications": [],
            "adverse_reactions": [],
            "drug_interactions": []
        }

        search_terms = []
        if generic_name:
            search_terms.append(f'openfda.generic_name:"{generic_name}"')
        if brand_name:
            search_terms.append(f'openfda.brand_name:"{brand_name}"')

        if not search_terms:
            return empty_info

        # Search queries list: combined -> generic -> brand
        queries = []
        if generic_name and brand_name:
            queries.append(f'openfda.generic_name:"{generic_name}"+AND+openfda.brand_name:"{brand_name}"')
        if generic_name:
            queries.append(f'openfda.generic_name:"{generic_name}"')
        if brand_name:
            queries.append(f'openfda.brand_name:"{brand_name}"')

        for q in queries:
            try:
                resp = requests.get(OPENFDA_BASE_URL, params={"search": q, "limit": 1}, timeout=5.0)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        label_data = results[0]
                        return {
                            "indications": self._clean_fda_text_list(label_data.get("indications_and_usage") or label_data.get("purpose")),
                            "warnings": self._clean_fda_text_list(label_data.get("warnings") or label_data.get("warnings_and_cautions") or label_data.get("boxed_warning")),
                            "contraindications": self._clean_fda_text_list(label_data.get("contraindications")),
                            "adverse_reactions": self._clean_fda_text_list(label_data.get("adverse_reactions")),
                            "drug_interactions": self._clean_fda_text_list(label_data.get("drug_interactions"))
                        }
            except Exception as e:
                logger.warning(f"openFDA API request failed for query '{q}': {e}")
                break

        return empty_info

    def _clean_fda_text_list(self, raw_data: Any) -> List[str]:
        """Cleans FDA raw text arrays into clean bullet point lines."""
        if not raw_data:
            return []
        if isinstance(raw_data, str):
            raw_data = [raw_data]

        cleaned_bullets = []
        for text in raw_data:
            # Strip HTML tags
            text_clean = re.sub(r'<[^>]+>', '', text)
            # Split sentences/paragraphs
            paragraphs = [p.strip() for p in text_clean.split('\n') if p.strip()]
            for p in paragraphs[:5]: # Take top 5 key bullet paragraphs
                if len(p) > 20:
                    cleaned_bullets.append(p[:300] + ("..." if len(p) > 300 else ""))

        return cleaned_bullets[:5]

    def get_medicine_info(self, medicine_name: str) -> Dict[str, Any]:
        """
        Main public function to retrieve standardized medicine info.
        Executes caching -> RxNorm -> openFDA -> fallback pipeline.
        """
        input_str = (medicine_name or "").strip()
        if not input_str:
            return {
                "status": "LOW_CONFIDENCE",
                "input_name": "",
                "normalized_name": "Unknown",
                "generic_name": None,
                "rxcui": None,
                "strength": None,
                "dosage_form": None,
                "match_confidence": 0.0,
                "indications": [],
                "warnings": [],
                "contraindications": [],
                "adverse_reactions": [],
                "drug_interactions": [],
                "source": {"normalization": "None", "clinical_label": "None"},
                "requires_doctor_review": True,
                "message": "Empty medicine name provided."
            }

        # 1. Check SQLite Cache
        cached = self.get_cached_info(input_str)
        if cached:
            return cached

        # Extract strength & dosage form from input (e.g. "Dolo 650" -> strength: "650 mg")
        extracted_meta = self.extract_strength_and_form(input_str)

        # 2. Query RxNorm API
        rxnorm_res = self.query_rxnorm_api(input_str)
        rxcui = rxnorm_res.get("rxcui")
        norm_name = rxnorm_res.get("normalized_name", input_str)
        confidence = rxnorm_res.get("confidence", 0.50)

        # Generic name resolution (check local brand dict or fallback to normalized name)
        clean_clean = self.clean_medicine_name(input_str).lower()
        generic_name = rxnorm_res.get("generic_name") or self.local_brands.get(clean_clean) or norm_name

        # 3. Query openFDA API
        fda_res = self.query_openfda_api(generic_name=generic_name, brand_name=norm_name)

        # Determine clinical status & confidence tier
        status = "SUCCESS" if confidence >= 0.75 else "LOW_CONFIDENCE"
        if not rxcui and confidence < 0.75:
            status = "API_UNAVAILABLE" if rxcui is None else "LOW_CONFIDENCE"

        result = {
            "status": status,
            "input_name": input_str,
            "normalized_name": norm_name,
            "generic_name": generic_name,
            "rxcui": rxcui,
            "strength": extracted_meta.get("strength"),
            "dosage_form": extracted_meta.get("dosage_form"),
            "match_confidence": round(confidence, 2),
            "indications": fda_res.get("indications", []),
            "warnings": fda_res.get("warnings", []),
            "contraindications": fda_res.get("contraindications", []),
            "adverse_reactions": fda_res.get("adverse_reactions", []),
            "drug_interactions": fda_res.get("drug_interactions", []),
            "source": {
                "normalization": "RxNorm (NLM)" if rxcui else "Local Rule Engine",
                "clinical_label": "openFDA (U.S. FDA)" if fda_res.get("indications") else "Standard Clinical Mapping"
            },
            "requires_doctor_review": confidence < 0.75 or status != "SUCCESS",
            "message": "Medicine information resolved successfully." if status == "SUCCESS" else "Low confidence or API unavailable. Doctor review required."
        }

        # 4. Save to Cache
        try:
            self.save_cached_info(input_str, result)
        except Exception as e:
            logger.warning(f"Could not save medicine cache for '{input_str}': {e}")

        return result
