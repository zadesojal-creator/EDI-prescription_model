import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess

PROJECT_ROOT = Path("d:/ediprjcursor")
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data" / "merged_dataset"

test_df = pd.read_csv(DATA_DIR / "baseline_test.csv")
model = tf.keras.models.load_model(MODELS_DIR / "v3_final.keras")

def get_letterbox_image(image_path, target_size=(224, 224)):
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        W, H = img.size
        max_dim = max(W, H)
        canvas = Image.new('RGB', (max_dim, max_dim), (255, 255, 255))
        canvas.paste(img, ((max_dim - W) // 2, (max_dim - H) // 2))
        canvas = canvas.resize(target_size, Image.LANCZOS)
        return canvas

print("Preparing batch data for fast evaluation...")
all_std_imgs = []
all_tta_imgs = [] # 3 variants per sample

for idx, row in test_df.iterrows():
    base_img = get_letterbox_image(row['image_path'])
    base_arr = np.array(base_img, dtype=np.float32)
    all_std_imgs.append(base_arr)
    
    # TTA 1: Base
    all_tta_imgs.append(base_arr)
    
    # TTA 2: Center crop slight zoom
    W, H = base_img.size
    cm = int(W * 0.04)
    crop_img = base_img.crop((cm, cm, W - cm, H - cm)).resize((224, 224), Image.LANCZOS)
    all_tta_imgs.append(np.array(crop_img, dtype=np.float32))
    
    # TTA 3: Mild contrast tweak
    all_tta_imgs.append(np.clip(base_arr * 0.93 + 10, 0, 255))

std_batch = mobilenet_preprocess(np.array(all_std_imgs))
tta_batch = mobilenet_preprocess(np.array(all_tta_imgs))

print("Predicting standard batch...")
std_preds = model.predict(std_batch, batch_size=32, verbose=1)

print("Predicting TTA batch...")
tta_raw_preds = model.predict(tta_batch, batch_size=32, verbose=1)
# Reshape and average across the 3 variants
tta_preds = tta_raw_preds.reshape((len(test_df), 3, -1)).mean(axis=1)

y_true = test_df['label'].values
std_y_pred = np.argmax(std_preds, axis=1)
tta_y_pred = np.argmax(tta_preds, axis=1)

std_acc = accuracy_score(y_true, std_y_pred)
std_f1 = f1_score(y_true, std_y_pred, average='macro', zero_division=0)

tta_acc = accuracy_score(y_true, tta_y_pred)
tta_f1 = f1_score(y_true, tta_y_pred, average='macro', zero_division=0)

print("="*60)
print(f"Standard Test Accuracy: {std_acc:.4f} ({std_acc*100:.2f}%) | Macro-F1: {std_f1:.4f}")
print(f"TTA Test Accuracy     : {tta_acc:.4f} ({tta_acc*100:.2f}%) | Macro-F1: {tta_f1:.4f}")
print(f"Delta from TTA        : {(tta_acc - std_acc)*100:+.2f}%")
print("="*60)
