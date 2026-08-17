import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess
from tensorflow.keras.applications.densenet import preprocess_input as densenet_preprocess

PROJECT_ROOT = Path("d:/ediprjcursor")
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGS_DIR = OUTPUTS_DIR / "figures"
DATA_DIR = PROJECT_ROOT / "data" / "merged_dataset"

FIGS_DIR.mkdir(parents=True, exist_ok=True)

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

print("Loading test images...")
raw_imgs = np.array([load_letterbox(p) for p in test_df['image_path']], dtype=np.float32)
y_true = test_df['label'].values

print("Loading models and evaluating...")
m_model = tf.keras.models.load_model(MODELS_DIR / "v3_final.keras")
p_mob = m_model.predict(mobilenet_preprocess(raw_imgs.copy()), batch_size=32, verbose=0)
del m_model; tf.keras.backend.clear_session()

d_model = tf.keras.models.load_model(MODELS_DIR / "densenet121_best.keras")
p_dens = d_model.predict(densenet_preprocess(raw_imgs.copy()), batch_size=32, verbose=0)
del d_model; tf.keras.backend.clear_session()

e_model = tf.keras.models.load_model(MODELS_DIR / "efficientnetb0_best.keras")
p_eff = e_model.predict(raw_imgs.copy(), batch_size=32, verbose=0)
del e_model; tf.keras.backend.clear_session()

# Weighted Ensemble
p_ens = 0.20 * p_mob + 0.10 * p_dens + 0.70 * p_eff
y_pred = np.argmax(p_ens, axis=1)

acc = accuracy_score(y_true, y_pred)
macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
weighted_f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)

print(f"\nFinal Ensemble Accuracy: {acc*100:.2f}%")
print(f"Macro F1: {macro_f1:.4f}")
print(f"Weighted F1: {weighted_f1:.4f}")

# Plot Confusion Matrix
cm = confusion_matrix(y_true, y_pred)
cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)

plt.figure(figsize=(26, 24))
sns.heatmap(cm_norm, cmap='Blues', xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, cbar=True)
plt.title(f"Triple Ensemble Confusion Matrix (Test Accuracy: {acc*100:.2f}%, Macro-F1: {macro_f1:.4f})", fontsize=16, fontweight='bold', pad=15)
plt.xlabel("Predicted Medicine Class", fontsize=13, labelpad=10)
plt.ylabel("True Medicine Class", fontsize=13, labelpad=10)
plt.xticks(fontsize=6, rotation=90)
plt.yticks(fontsize=6)
plt.tight_layout()
cm_path = FIGS_DIR / "triple_ensemble_cm.png"
plt.savefig(cm_path, dpi=160, bbox_inches='tight')
plt.close()
print(f"Saved confusion matrix plot: {cm_path}")

# Classification Report
rep_dict = classification_report(y_true, y_pred, target_names=CLASS_NAMES, output_dict=True, zero_division=0)
rep_df = pd.DataFrame(rep_dict).T
rep_path = OUTPUTS_DIR / "triple_ensemble_report.csv"
rep_df.to_csv(rep_path)
print(f"Saved classification report: {rep_path}")

# Save Final Production Config
prod_config = {
    "version": "triple_ensemble_production_v1",
    "num_classes": 78,
    "models": {
        "mobilenet_v2": "models/v3_final.keras",
        "densenet_121": "models/densenet121_best.keras",
        "efficientnet_b0": "models/efficientnetb0_best.keras"
    },
    "ensemble_weights": {
        "mobilenet_v2": 0.20,
        "densenet_121": 0.10,
        "efficientnet_b0": 0.70
    },
    "metrics": {
        "reference_baseline_acc": 0.5983,
        "mobilenet_v2_acc": float(accuracy_score(y_true, np.argmax(p_mob, axis=1))),
        "densenet_121_acc": float(accuracy_score(y_true, np.argmax(p_dens, axis=1))),
        "efficientnet_b0_acc": float(accuracy_score(y_true, np.argmax(p_eff, axis=1))),
        "triple_ensemble_acc": float(acc),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "net_gain_percentage": float((acc - 0.5983) * 100)
    }
}
with open(MODELS_DIR / "ensemble_production_config.json", "w") as f:
    json.dump(prod_config, f, indent=2)

print(f"Production config saved to {MODELS_DIR / 'ensemble_production_config.json'}")
