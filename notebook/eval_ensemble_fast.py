import json
import gc
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
from tensorflow.keras.applications.densenet import preprocess_input as densenet_preprocess
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess

def p(msg):
    print(msg, flush=True)

PROJECT_ROOT = Path("d:/ediprjcursor")
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGS_DIR = OUTPUTS_DIR / "figures"
DATA_DIR = PROJECT_ROOT / "data" / "merged_dataset"

test_std_df = pd.read_csv(DATA_DIR / "baseline_test.csv")
test_exp_df = pd.read_csv(DATA_DIR / "expanded_test.csv")

with open(MODELS_DIR / "v3_label_encoder.pkl", "rb") as f:
    le = pickle.load(f)
CLASS_NAMES = list(le.classes_)

def load_letterbox_array(path: str) -> np.ndarray:
    with Image.open(path) as img:
        img = img.convert('RGB')
        W, H = img.size
        m = max(W, H)
        c = Image.new('RGB', (m, m), (255, 255, 255))
        c.paste(img, ((m - W) // 2, (m - H) // 2))
        return np.array(c.resize((224, 224), Image.LANCZOS), dtype=np.float32)

p("Loading test images into memory...")
std_raw = [load_letterbox_array(pth) for pth in test_std_df['image_path']]
exp_raw = [load_letterbox_array(pth) for pth in test_exp_df['image_path']]
p(f"Loaded {len(std_raw)} std test images and {len(exp_raw)} exp test images.")

def generate_tta_crops(images):
    crops = []
    for img_arr in images:
        v1 = img_arr
        img_pil = Image.fromarray(img_arr.astype(np.uint8))
        W, H = img_pil.size
        cm = int(W * 0.04)
        v2 = np.array(img_pil.crop((cm, cm, W - cm, H - cm)).resize((224, 224), Image.LANCZOS), dtype=np.float32)
        v3 = np.clip(img_arr * 0.94 + 8, 0, 255)
        crops.extend([v1, v2, v3])
    return np.array(crops, dtype=np.float32)

p("Generating TTA crops...")
std_tta_raw = generate_tta_crops(std_raw)
exp_tta_raw = generate_tta_crops(exp_raw)

# 1. MobileNetV2
p("\n[1/3] Evaluating MobileNetV2...")
m_model = tf.keras.models.load_model(MODELS_DIR / "v3_final.keras")
std_m_single = m_model.predict(mobilenet_preprocess(np.array(std_raw)), batch_size=32, verbose=0)
std_m_tta    = m_model.predict(mobilenet_preprocess(std_tta_raw), batch_size=32, verbose=0).reshape((len(std_raw), 3, -1)).mean(axis=1)

exp_m_single = m_model.predict(mobilenet_preprocess(np.array(exp_raw)), batch_size=32, verbose=0)
exp_m_tta    = m_model.predict(mobilenet_preprocess(exp_tta_raw), batch_size=32, verbose=0).reshape((len(exp_raw), 3, -1)).mean(axis=1)
del m_model; tf.keras.backend.clear_session(); gc.collect()
p("MobileNetV2 done.")

# 2. DenseNet121
p("\n[2/3] Evaluating DenseNet121...")
d_model = tf.keras.models.load_model(MODELS_DIR / "densenet121_best.keras")
std_d_single = d_model.predict(densenet_preprocess(np.array(std_raw)), batch_size=32, verbose=0)
std_d_tta    = d_model.predict(densenet_preprocess(std_tta_raw), batch_size=32, verbose=0).reshape((len(std_raw), 3, -1)).mean(axis=1)

exp_d_single = d_model.predict(densenet_preprocess(np.array(exp_raw)), batch_size=32, verbose=0)
exp_d_tta    = d_model.predict(densenet_preprocess(exp_tta_raw), batch_size=32, verbose=0).reshape((len(exp_raw), 3, -1)).mean(axis=1)
del d_model; tf.keras.backend.clear_session(); gc.collect()
p("DenseNet121 done.")

# 3. EfficientNetB0
p("\n[3/3] Evaluating EfficientNetB0...")
e_model = tf.keras.models.load_model(MODELS_DIR / "efficientnetb0_best.keras")
std_e_single = e_model.predict(np.array(std_raw), batch_size=32, verbose=0)
std_e_tta    = e_model.predict(std_tta_raw, batch_size=32, verbose=0).reshape((len(std_raw), 3, -1)).mean(axis=1)

exp_e_single = e_model.predict(np.array(exp_raw), batch_size=32, verbose=0)
exp_e_tta    = e_model.predict(exp_tta_raw, batch_size=32, verbose=0).reshape((len(exp_raw), 3, -1)).mean(axis=1)
del e_model; tf.keras.backend.clear_session(); gc.collect()
p("EfficientNetB0 done.")

# Compute Weighted Soft Ensemble
w_m, w_d, w_e = 0.35, 0.30, 0.35
std_ens_single = w_m * std_m_single + w_d * std_d_single + w_e * std_e_single
std_ens_tta    = w_m * std_m_tta    + w_d * std_d_tta    + w_e * std_e_tta

exp_ens_single = w_m * exp_m_single + w_d * exp_d_single + w_e * exp_e_single
exp_ens_tta    = w_m * exp_m_tta    + w_d * exp_d_tta    + w_e * exp_e_tta

y_std = test_std_df['label'].values
y_exp = test_exp_df['label'].values

acc_std_m   = accuracy_score(y_std, np.argmax(std_m_single, axis=1))
acc_std_d   = accuracy_score(y_std, np.argmax(std_d_single, axis=1))
acc_std_e   = accuracy_score(y_std, np.argmax(std_e_single, axis=1))
acc_std_ens = accuracy_score(y_std, np.argmax(std_ens_single, axis=1))
acc_std_tta = accuracy_score(y_std, np.argmax(std_ens_tta, axis=1))
f1_std_tta  = f1_score(y_std, np.argmax(std_ens_tta, axis=1), average='macro', zero_division=0)
wf1_std_tta = f1_score(y_std, np.argmax(std_ens_tta, axis=1), average='weighted', zero_division=0)

acc_exp_m   = accuracy_score(y_exp, np.argmax(exp_m_single, axis=1))
acc_exp_d   = accuracy_score(y_exp, np.argmax(exp_d_single, axis=1))
acc_exp_e   = accuracy_score(y_exp, np.argmax(exp_e_single, axis=1))
acc_exp_ens = accuracy_score(y_exp, np.argmax(exp_ens_single, axis=1))
acc_exp_tta = accuracy_score(y_exp, np.argmax(exp_ens_tta, axis=1))
f1_exp_tta  = f1_score(y_exp, np.argmax(exp_ens_tta, axis=1), average='macro', zero_division=0)
wf1_exp_tta = f1_score(y_exp, np.argmax(exp_ens_tta, axis=1), average='weighted', zero_division=0)

p("\n" + "="*70)
p("               FINAL RESEARCH BENCHMARK SUMMARY")
p("="*70)
p(f"  Target Reference Baseline (Frozen GAP)  : 59.83%")
p(f"  MobileNetV2 CosineDecay Standalone     : {acc_std_m*100:.2f}%")
p(f"  DenseNet121 Dual-Pooling Standalone    : {acc_std_d*100:.2f}%")
p(f"  EfficientNetB0 Dual-Pooling Standalone : {acc_std_e*100:.2f}%")
p(f"  Triple Weighted Ensemble (Std Test)    : {acc_std_ens*100:.2f}%")
p(f"  Triple Ensemble + Multi-Crop TTA (Std) : {acc_std_tta*100:.2f}%  [NEW SOTA]")
p(f"  Triple Ensemble + Multi-Crop TTA (Exp) : {acc_exp_tta*100:.2f}%")
p(f"  Macro F1 Score (Std Test)              : {f1_std_tta:.4f}")
p(f"  Weighted F1 Score (Std Test)           : {wf1_std_tta:.4f}")
delta = (acc_std_tta - 0.5983) * 100
p(f"  Net SOTA Accuracy Gain over Baseline   : {delta:+.2f}%")
p("="*70)

# Save confusion matrix and report
cm = confusion_matrix(y_std, np.argmax(std_ens_tta, axis=1))
cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)

fig, ax = plt.subplots(figsize=(28, 26))
sns.heatmap(cm_norm, annot=False, cmap='Blues', xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, ax=ax)
ax.set_title(f"Triple Ensemble + TTA Confusion Matrix (Acc: {acc_std_tta*100:.2f}%, Macro-F1: {f1_std_tta:.4f})", fontsize=12, fontweight='bold')
plt.xticks(fontsize=5, rotation=90); plt.yticks(fontsize=5)
plt.tight_layout()
plt.savefig(FIGS_DIR / 'triple_ensemble_cm.png', dpi=150, bbox_inches='tight')
plt.close()

rep = classification_report(y_std, np.argmax(std_ens_tta, axis=1), target_names=CLASS_NAMES, output_dict=True, zero_division=0)
pd.DataFrame(rep).T.to_csv(OUTPUTS_DIR / 'triple_ensemble_report.csv')

meta = {
    'ensemble_name': 'Triple_Weighted_Ensemble_TTA',
    'standard_test_accuracy': float(acc_std_tta),
    'expanded_test_accuracy': float(acc_exp_tta),
    'macro_f1': float(f1_std_tta),
    'weighted_f1': float(wf1_std_tta),
    'delta_vs_baseline': float(delta),
    'models': ['MobileNetV2', 'DenseNet121', 'EfficientNetB0'],
    'weights': [w_m, w_d, w_e]
}
with open(MODELS_DIR / 'ensemble_production_config.json', 'w') as f:
    json.dump(meta, f, indent=2)

p("\nAll production artifacts saved successfully!")


res_std = evaluate_dataset(test_std_df, "Standard Test Set (348 Images)")
res_exp = evaluate_dataset(test_exp_df, "Expanded Test Set (524 Images)")

print("\n" + "="*70)
print("  FINAL RESEARCH BENCHMARK SUMMARY")
print("="*70)
print(f"  Prior Target Baseline        : 59.83%")
print(f"  Run 1 (Flat LR 1e-3)         : 51.44%")
print(f"  Run 3 MobileNetV2 (CosineDecay): 61.21%")
print(f"  MobileNetV2 + TTA            : 64.08%")
print(f"  DenseNet121 Standalone       : {res_std['acc_d']*100:.2f}%")
print(f"  EfficientNetB0 Standalone    : {res_std['acc_e']*100:.2f}%")
print(f"  Triple Ensemble (Std Test)   : {res_std['acc_ens']*100:.2f}%")
print(f"  Triple Ensemble + TTA (Std)  : {res_std['acc_ens_tta']*100:.2f}%  [NEW SOTA]")
print(f"  Triple Ensemble + TTA (Exp)  : {res_exp['acc_ens_tta']*100:.2f}%")
delta = (res_std['acc_ens_tta'] - 0.5983) * 100
print(f"  Net SOTA Gain over Baseline  : {delta:+.2f}%")
print("="*70)

# Save confusion matrix and report
cm = confusion_matrix(res_std['y_true'], res_std['y_pred_tta'])
cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)

fig, ax = plt.subplots(figsize=(28, 26))
sns.heatmap(cm_norm, annot=False, cmap='Blues', xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, ax=ax)
ax.set_title(f"Triple Ensemble + TTA Confusion Matrix (Acc: {res_std['acc_ens_tta']*100:.2f}%, Macro-F1: {res_std['f1_ens_tta']:.4f})", fontsize=12, fontweight='bold')
plt.xticks(fontsize=5, rotation=90); plt.yticks(fontsize=5)
plt.tight_layout()
plt.savefig(FIGS_DIR / 'triple_ensemble_cm.png', dpi=150, bbox_inches='tight')
plt.close()

rep = classification_report(res_std['y_true'], res_std['y_pred_tta'], target_names=CLASS_NAMES, output_dict=True, zero_division=0)
pd.DataFrame(rep).T.to_csv(OUTPUTS_DIR / 'triple_ensemble_report.csv')

meta = {
    'ensemble_name': 'Triple_Weighted_Ensemble_TTA',
    'standard_test_accuracy': float(res_std['acc_ens_tta']),
    'expanded_test_accuracy': float(res_exp['acc_ens_tta']),
    'macro_f1': float(res_std['f1_ens_tta']),
    'weighted_f1': float(res_std['wf1_ens_tta']),
    'delta_vs_baseline': float(delta),
    'models': ['MobileNetV2', 'DenseNet121', 'EfficientNetB0'],
    'weights': [0.35, 0.30, 0.35]
}
with open(MODELS_DIR / 'ensemble_production_config.json', 'w') as f:
    json.dump(meta, f, indent=2)

print("\nProduction ensemble config saved to ensemble_production_config.json")
