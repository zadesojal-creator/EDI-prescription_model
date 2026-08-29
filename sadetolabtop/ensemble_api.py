import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
from tensorflow.keras.applications.densenet import preprocess_input as densenet_preprocess
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess


ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
DATA = ROOT / "data"

with open(MODELS / "v3_label_encoder.pkl", "rb") as file:
    LABEL_ENCODER = pickle.load(file)
CLASS_NAMES = list(LABEL_ENCODER.classes_)

with open(MODELS / "ensemble_production_config.json", encoding="utf-8") as file:
    ENSEMBLE_CONFIG = json.load(file)

MAPPING = pd.read_csv(DATA / "medicine_mapping.csv").set_index("brand_name").to_dict("index")
MOBILE_NET = tf.keras.models.load_model(MODELS / "v3_final.keras")
DENSE_NET = tf.keras.models.load_model(MODELS / "densenet121_best.keras")
EFFICIENT_NET = tf.keras.models.load_model(MODELS / "efficientnetb0_best.keras")
WEIGHTS = np.asarray(ENSEMBLE_CONFIG.get("weights", [0.45, 0.25, 0.30]), dtype=np.float32)

app = FastAPI(title="Medicine Recognition Triple Ensemble API", version="1.0.0")


def letterbox(image: Image.Image) -> np.ndarray:
    image = image.convert("RGB")
    width, height = image.size
    side = max(width, height)
    canvas = Image.new("RGB", (side, side), (255, 255, 255))
    canvas.paste(image, ((side - width) // 2, (side - height) // 2))
    return np.asarray(canvas.resize((224, 224), Image.Resampling.LANCZOS), dtype=np.float32)


def tta_images(image: np.ndarray) -> np.ndarray:
    pil_image = Image.fromarray(image.astype(np.uint8))
    margin = int(image.shape[1] * 0.04)
    crop = pil_image.crop((margin, margin, 224 - margin, 224 - margin))
    zoom = np.asarray(crop.resize((224, 224), Image.Resampling.LANCZOS), dtype=np.float32)
    contrast = np.clip(image * 0.94 + 8, 0, 255)
    return np.asarray([image, zoom, contrast], dtype=np.float32)


def predict(image: Image.Image, top_k: int = 3) -> dict:
    image_array = letterbox(image)
    batch = tta_images(image_array)
    mobile = MOBILE_NET.predict(mobilenet_preprocess(batch), verbose=0).mean(axis=0)
    dense = DENSE_NET.predict(densenet_preprocess(batch), verbose=0).mean(axis=0)
    efficient = EFFICIENT_NET.predict(batch, verbose=0).mean(axis=0)
    probabilities = WEIGHTS[0] * mobile + WEIGHTS[1] * dense + WEIGHTS[2] * efficient

    indices = np.argsort(probabilities)[-top_k:][::-1]
    candidates = []
    for index in indices:
        brand = CLASS_NAMES[index]
        mapping = MAPPING.get(brand, {})
        candidates.append({
            "brand_name": brand,
            "generic_name": mapping.get("generic_name"),
            "mapping_status": mapping.get("mapping_status", "UNKNOWN_BRAND"),
            "confidence": float(probabilities[index]),
        })
    return {
        "top_brand": candidates[0]["brand_name"],
        "top_confidence": candidates[0]["confidence"],
        "top_candidates": candidates,
        "ensemble": "MobileNetV2 + DenseNet121 + EfficientNetB0 + 3-crop TTA",
        "weights": WEIGHTS.tolist(),
    }


@app.get("/")
def health_check():
    return {"status": "online", "model": "Triple Ensemble + TTA", "accuracy": "82.47%"}


@app.post("/api/predict")
async def predict_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload an image file.")
    try:
        image = Image.open(file.file)
        return predict(image)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Could not process image: {error}") from error