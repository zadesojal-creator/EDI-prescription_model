import pickle
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path("d:/ediprjcursor")
LABEL_ENCODER_PATH = PROJECT_ROOT / "models" / "v3_label_encoder.pkl"
MED_MAP_PKL_PATH = PROJECT_ROOT / "models" / "v3_med_to_generic.pkl"
CSV_OUTPUT_PATH = PROJECT_ROOT / "data" / "medicine_mapping.csv"

CSV_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(LABEL_ENCODER_PATH, "rb") as f:
    le = pickle.load(f)

with open(MED_MAP_PKL_PATH, "rb") as f:
    med_map = pickle.load(f)

rows = []
for brand in le.classes_:
    generic = med_map.get(brand, None)
    if generic and str(generic).strip() != "" and str(generic).lower() != "none":
        status = "VERIFIED"
        gen_val = str(generic).strip()
    else:
        status = "UNVERIFIED"
        gen_val = ""

    rows.append({
        "brand_name": brand,
        "generic_name": gen_val,
        "mapping_status": status
    })

df = pd.DataFrame(rows)
df.to_csv(CSV_OUTPUT_PATH, index=False)
print(f"Generated {len(df)} rows in {CSV_OUTPUT_PATH}")
print(f"Verified mappings: {(df['mapping_status'] == 'VERIFIED').sum()}")
print(f"Unverified mappings: {(df['mapping_status'] == 'UNVERIFIED').sum()}")
