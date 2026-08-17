import os
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image
import tensorflow as tf

PROJECT_ROOT = Path("d:/ediprjcursor")
MODEL_PATH = PROJECT_ROOT / "models" / "efficientnetb0_best.keras"
LABEL_ENCODER_PATH = PROJECT_ROOT / "models" / "v3_label_encoder.pkl"
TEST_CSV_PATH = PROJECT_ROOT / "data" / "merged_dataset" / "baseline_test.csv"

def inspect_model_pipeline():
    print("="*60)
    print("      PHASE 1: EXISTING MODEL & PREPROCESSING INSPECTION")
    print("="*60)

    # 1. Model Path
    print(f"1. Model Path: {MODEL_PATH}")
    assert MODEL_PATH.exists(), f"Model file not found at {MODEL_PATH}"
    print(f"   Model file exists. Size: {MODEL_PATH.stat().st_size / (1024*1024):.2f} MB")

    # 2. Load Model & Inspect Input Shape
    print("\n2. Loading Model & Inspecting Shape...")
    model = tf.keras.models.load_model(MODEL_PATH)
    input_shape = model.input_shape
    output_shape = model.output_shape
    print(f"   Model Input Shape : {input_shape}")
    print(f"   Model Output Shape: {output_shape}")

    # 3. Class Names & Label Encoder
    print("\n3. Class Names & Label Encoder Inspection...")
    assert LABEL_ENCODER_PATH.exists(), f"Label encoder not found at {LABEL_ENCODER_PATH}"
    with open(LABEL_ENCODER_PATH, "rb") as f:
        le = pickle.load(f)
    classes = list(le.classes_)
    num_classes = len(classes)
    print(f"   Number of Classes: {num_classes}")
    print(f"   First 5 Classes  : {classes[:5]}")
    print(f"   Last 5 Classes   : {classes[-5:]}")

    # 4. Preprocessing Strategy Confirmation
    print("\n4. Image Preprocessing Strategy:")
    print("   - Target Aspect Ratio: 1:1 Square via White-Canvas Letterboxing (255 background)")
    print("   - Resize Dimension   : 224 x 224 pixels (LANCZOS interpolation)")
    print("   - Normalization      : EfficientNetB0 has internal Rescaling layer; expects raw float32 [0, 255]")
    print("   - Color Channels     : RGB (3 channels)")

    # 5. Load a Test Image and Predict
    print("\n5. Running Single Test Image Prediction...")
    test_df = pd.read_csv(TEST_CSV_PATH)
    test_sample = test_df.iloc[0]
    img_path = test_sample['image_path']
    true_label_idx = test_sample['label']
    true_label_name = classes[true_label_idx]

    print(f"   Selected Test Image: {img_path}")
    print(f"   True Ground Truth Label: {true_label_name} (Index: {true_label_idx})")

    # Preprocess image
    with Image.open(img_path) as img:
        img = img.convert('RGB')
        W, H = img.size
        m = max(W, H)
        canvas = Image.new('RGB', (m, m), (255, 255, 255))
        canvas.paste(img, ((m - W) // 2, (m - H) // 2))
        resized = canvas.resize((224, 224), Image.LANCZOS)
        img_arr = np.expand_dims(np.array(resized, dtype=np.float32), axis=0)

    # Perform Inference
    probs = model.predict(img_arr, verbose=0)[0]
    top_3_indices = np.argsort(probs)[-3:][::-1]

    print("\n" + "-"*50)
    print("   PREDICTION RESULTS & TOP-3 CANDIDATES:")
    print("-"*50)
    for i, idx in enumerate(top_3_indices, 1):
        brand_name = classes[idx]
        prob_pct = probs[idx] * 100
        is_match = " (Ground Truth)" if idx == true_label_idx else ""
        print(f"   Top {i}: {brand_name:<20} | Probability: {prob_pct:6.2f}%{is_match}")
    print("-"*50)

    print("\nProbability Distribution Stats across all 78 classes:")
    print(f"   Max Prob: {np.max(probs)*100:.2f}%")
    print(f"   Min Prob: {np.min(probs)*100:.2f}%")
    print(f"   Mean Prob: {np.mean(probs)*100:.2f}%")
    print(f"   Sum of Probabilities: {np.sum(probs):.4f}")

    print("\nPhase 1 Inspection Completed Successfully!")

if __name__ == "__main__":
    inspect_model_pipeline()
