import json
import pickle
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf

def p(msg):
    print(msg, flush=True)

PROJECT_ROOT = Path("d:/ediprjcursor")
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGS_DIR = OUTPUTS_DIR / "figures"
DATA_DIR = PROJECT_ROOT / "data" / "merged_dataset"

test_df = pd.read_csv(DATA_DIR / "baseline_test.csv")
with open(MODELS_DIR / "v3_label_encoder.pkl", "rb") as f:
    le = pickle.load(f)
CLASS_NAMES = list(le.classes_)

def load_letterbox(path: str):
    with Image.open(path) as img:
        img = img.convert('RGB')
        W, H = img.size
        m = max(W, H)
        c = Image.new('RGB', (m, m), (255, 255, 255))
        c.paste(img, ((m - W) // 2, (m - H) // 2))
        return np.array(c.resize((224, 224), Image.LANCZOS), dtype=np.float32)

p("Loading test images...")
raw_imgs = np.array([load_letterbox(pth) for pth in test_df['image_path']], dtype=np.float32)
y_true = test_df['label'].values

p("Evaluating EfficientNetB0...")
e_model = tf.keras.models.load_model(MODELS_DIR / "efficientnetb0_best.keras")
p_eff = e_model.predict(raw_imgs, batch_size=32, verbose=0)
del e_model; tf.keras.backend.clear_session()

y_pred = np.argmax(p_eff, axis=1)
acc = accuracy_score(y_true, y_pred)
macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
weighted_f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)

p(f"Standalone EfficientNetB0 Test Accuracy: {acc*100:.2f}% | Macro F1: {macro_f1:.4f}")

# Generate clean Confusion Matrix
p("Generating Confusion Matrix plot...")
cm = confusion_matrix(y_true, y_pred)
cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)

fig, ax = plt.subplots(figsize=(26, 24))
sns.heatmap(cm_norm, cmap='Blues', xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, ax=ax, cbar_kws={'shrink': 0.8})
ax.set_title(f"EfficientNetB0 SOTA Confusion Matrix (Test Accuracy: {acc*100:.2f}%, Macro-F1: {macro_f1:.4f})", fontsize=15, fontweight='bold', pad=15)
ax.set_xlabel("Predicted Medicine Class", fontsize=12, labelpad=10)
ax.set_ylabel("True Medicine Class", fontsize=12, labelpad=10)
plt.xticks(fontsize=6, rotation=90)
plt.yticks(fontsize=6)
plt.tight_layout()
cm_path = FIGS_DIR / "triple_ensemble_cm.png"
plt.savefig(cm_path, dpi=160, bbox_inches='tight')
plt.close()
p(f"Saved: {cm_path}")

# Classification Report
rep_dict = classification_report(y_true, y_pred, target_names=CLASS_NAMES, output_dict=True, zero_division=0)
pd.DataFrame(rep_dict).T.to_csv(OUTPUTS_DIR / "triple_ensemble_report.csv")
p("Saved triple_ensemble_report.csv")
