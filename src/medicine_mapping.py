"""
Generic Medicine Mapping Module
Maps handwritten medicine brand names to verified generic formulations.
"""

import pandas as pd
from pathlib import Path

class GenericMedicineMapper:
    """
    Manages lookup from medicine brand name to its corresponding generic formulation.
    Reads from verified reference dataset data/medicine_mapping.csv.
    """

    def __init__(self, mapping_csv_path: str = None):
        project_root = Path(__file__).resolve().parent.parent
        self.csv_path = Path(mapping_csv_path) if mapping_csv_path else project_root / "data" / "medicine_mapping.csv"
        self.mapping_dict = {}
        self._load_mapping()

    def _load_mapping(self):
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Medicine mapping CSV not found at {self.csv_path}")

        df = pd.read_csv(self.csv_path)
        for _, row in df.iterrows():
            brand = str(row['brand_name']).strip()
            generic = str(row['generic_name']).strip() if pd.notna(row['generic_name']) and str(row['generic_name']).strip() else None
            status = str(row['mapping_status']).strip() if pd.notna(row['mapping_status']) else ("VERIFIED" if generic else "UNVERIFIED")

            self.mapping_dict[brand] = {
                "generic_name": generic,
                "mapping_status": status
            }

    def get_generic_mapping(self, brand_name: str) -> dict:
        """
        Looks up the generic formulation for a given brand name.
        Returns:
            dict with 'generic_name' and 'mapping_status'.
        """
        if not brand_name or brand_name == "Unknown":
            return {
                "generic_name": None,
                "mapping_status": "UNVERIFIED"
            }

        brand_clean = str(brand_name).strip()
        if brand_clean in self.mapping_dict:
            return self.mapping_dict[brand_clean]
        else:
            return {
                "generic_name": None,
                "mapping_status": "UNKNOWN_BRAND"
            }
