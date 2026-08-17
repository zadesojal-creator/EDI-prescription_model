#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
train_ensemble_final.py
=======================
Trains EfficientNetB0 on Expanded Dataset (5,240 images)
and creates the Triple Soft-Voting Ensemble (MobileNetV2 + DenseNet121 + EfficientNetB0)
with multi-crop Test-Time Augmentation (TTA).
"""

import sys, os, io, json, pickle, random, time, warnings
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(SCRIPT_DIR)

import numpy as np
import pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_score, recall_score, f1_score, accuracy_score
)

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import EfficientNetB0, DenseNet121, MobileNetV2
from tensorflow.keras.applications.densenet import preprocess_input as densenet_preprocess
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess

warnings.filterwarnings('ignore')

SEED = 42
random.seed(SEED); np.random.seed(SEED); tf.random.set_seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)

DATA_DIR    = PROJECT_ROOT / 'data' / 'merged_dataset'
MODELS_DIR  = PROJECT_ROOT / 'models'
OUTPUTS_DIR = PROJECT_ROOT / 'outputs'
FIGS_DIR    = OUTPUTS_DIR / 'figures'
for d in [MODELS_DIR, OUTPUTS_DIR, FIGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

@dataclass(frozen=True)
class Config:
    IMAGE_SIZE      : Tuple[int, int] = (224, 224)
    CHANNELS        : int             = 3
    NUM_CLASSES     : int             = 78
    BATCH_SIZE      : int             = 16
    EPOCHS          : int             = 30
    LR_INIT         : float           = 1e-3
    DENSE_UNITS     : int             = 256

CFG = Config()
TARGET_H, TARGET_W = CFG.IMAGE_SIZE

print("=" * 70)
print("  ENSEMBLE FINAL: EFFICIENTNET-B0 + DENSENET-121 + MOBILENET-V2")
print("=" * 70)

# Load Datasets
train_df    = pd.read_csv(DATA_DIR / 'expanded_train.csv')
val_df      = pd.read_csv(DATA_DIR / 'expanded_val.csv')
test_exp_df = pd.read_csv(DATA_DIR / 'expanded_test.csv')
test_std_df = pd.read_csv(DATA_DIR / 'baseline_test.csv')
labels_df   = pd.read_csv(DATA_DIR / 'expanded_labels.csv')

med_to_generic: Dict[str, str] = (
    labels_df[['MEDICINE_NAME', 'GENERIC_NAME']].dropna()
    .drop_duplicates('MEDICINE_NAME').set_index('MEDICINE_NAME')['GENERIC_NAME'].to_dict()
)

le = LabelEncoder()
le.fit(labels_df['MEDICINE_NAME'].values)
CLASS_NAMES: List[str] = list(le.classes_)

print(f"  Dataset: Train={len(train_df)} | Val={len(val_df)} | ExpTest={len(test_exp_df)} | StdTest={len(test_std_df)}")

# Helper Preprocessing
def load_letterbox_array(path: str) -> np.ndarray:
    try:
        with Image.open(path) as img:
            img = img.convert('RGB')
            W, H = img.size
            max_dim = max(W, H)
            canvas = Image.new('RGB', (max_dim, max_dim), (255, 255, 255))
            canvas.paste(img, ((max_dim - W) // 2, (max_dim - H) // 2))
            canvas = canvas.resize((TARGET_W, TARGET_H), Image.LANCZOS)
            return np.array(canvas, dtype=np.float32)
    except Exception:
        return np.zeros((TARGET_H, TARGET_W, 3), dtype=np.float32)

def build_tf_dataset(df: pd.DataFrame, preprocess_fn, shuffle: bool = True) -> tf.data.Dataset:
    paths  = df['image_path'].values.astype(str)
    labels = df['label'].values.astype(np.int32)
    
    def _map_fn(p, l):
        def _py_read(path_b):
            arr = load_letterbox_array(path_b.decode('utf-8'))
            if preprocess_fn is not None:
                arr = preprocess_fn(arr)
            return arr.astype(np.float32)
        
        img = tf.numpy_function(_py_read, [p], tf.float32)
        img.set_shape((TARGET_H, TARGET_W, 3))
        return img, l
    
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    ds = ds.map(_map_fn, num_parallel_calls=tf.data.AUTOTUNE)
    if shuffle:
        ds = ds.shuffle(buffer_size=len(df), seed=SEED, reshuffle_each_iteration=True)
    return ds.batch(CFG.BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

# Model: EfficientNetB0 with Dual Pooling
def build_efficientnet_model() -> keras.Model:
    inputs = keras.Input(shape=(TARGET_H, TARGET_W, CFG.CHANNELS), name='image_input')
    # Augmentation
    x = layers.RandomRotation(0.04, fill_mode='constant', fill_value=255.0)(inputs)
    x = layers.RandomTranslation(0.05, 0.05, fill_mode='constant', fill_value=255.0)(x)
    x = layers.RandomZoom((-0.05, 0.05), fill_mode='constant', fill_value=255.0)(x)
    
    base = EfficientNetB0(include_top=False, weights='imagenet', input_shape=(TARGET_H, TARGET_W, CFG.CHANNELS))
    base.trainable = False
    feat = base(x, training=False)
    
    gap = layers.GlobalAveragePooling2D(name='gap')(feat)
    gmp = layers.GlobalMaxPooling2D(name='gmp')(feat)
    pooled = layers.Concatenate(name='dual_pool')([gap, gmp])
    
    x = layers.BatchNormalization()(pooled)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(CFG.DENSE_UNITS, activation='relu', name='dense_head')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(CFG.NUM_CLASSES, activation='softmax', name='predictions')(x)
    
    return keras.Model(inputs=inputs, outputs=outputs, name='Medicine_EfficientNetB0')

# Check if efficientnetb0_best.keras already exists, else train it
EFF_CKPT = str(MODELS_DIR / 'efficientnetb0_best.keras')
if not Path(EFF_CKPT).exists():
    print("\n[2] Training EfficientNetB0...")
    eff_model = build_efficientnet_model()
    
    train_ds = build_tf_dataset(train_df, None, shuffle=True)
    val_ds   = build_tf_dataset(val_df,   None, shuffle=False)
    
    total_steps = CFG.EPOCHS * len(train_ds)
    lr_schedule = tf.keras.optimizers.schedules.CosineDecayRestarts(
        initial_learning_rate=CFG.LR_INIT,
        first_decay_steps=total_steps // 3,
        t_mul=1.0,
        m_mul=0.85,
        alpha=1e-6
    )
    
    eff_model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=lr_schedule),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    callbacks = [
        keras.callbacks.ModelCheckpoint(EFF_CKPT, monitor='val_accuracy', save_best_only=True, verbose=1),
        keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=10, restore_best_weights=True, verbose=1),
        keras.callbacks.CSVLogger(str(OUTPUTS_DIR / 'log_efficientnetb0.csv'), append=False),
    ]
    
    t0 = time.time()
    eff_hist = eff_model.fit(
        train_ds, validation_data=val_ds,
        epochs=CFG.EPOCHS,
        callbacks=callbacks,
        verbose=1
    )
    print(f"  EfficientNetB0 training done in {(time.time()-t0)/60:.1f} min")
else:
    print(f"\n[2] Found existing {EFF_CKPT} — loading...")

eff_model = keras.models.load_model(EFF_CKPT)
densenet_model = keras.models.load_model(MODELS_DIR / 'densenet121_best.keras')
mobilenet_model = keras.models.load_model(MODELS_DIR / 'v3_final.keras')

print("\nAll 3 models loaded successfully:")
print("  1. MobileNetV2   (v3_final.keras)")
print("  2. DenseNet121   (densenet121_best.keras)")
print("  3. EfficientNetB0 (efficientnetb0_best.keras)")

# Vectorized Predictions & Ensembling
def get_model_predictions_batch(test_dataframe, with_tta: bool = False):
    N = len(test_dataframe)
    raw_images = [load_letterbox_array(p) for p in test_dataframe['image_path']]
    
    if not with_tta:
        mob_in  = mobilenet_preprocess(np.array(raw_images))
        dens_in = densenet_preprocess(np.array(raw_images))
        eff_in  = np.array(raw_images, dtype=np.float32)
        
        p_mob  = mobilenet_model.predict(mob_in, batch_size=32, verbose=0)
        p_dens = densenet_model.predict(dens_in, batch_size=32, verbose=0)
        p_eff  = eff_model.predict(eff_in, batch_size=32, verbose=0)
    else:
        # Multi-crop TTA (3 variants per image)
        all_mob, all_dens, all_eff = [], [], []
        for img_arr in raw_images:
            # v1: Original
            v1 = img_arr
            # v2: Zoom Crop
            img_pil = Image.fromarray(img_arr.astype(np.uint8))
            W, H = img_pil.size
            cm = int(W * 0.04)
            v2 = np.array(img_pil.crop((cm, cm, W - cm, H - cm)).resize((TARGET_W, TARGET_H), Image.LANCZOS), dtype=np.float32)
            # v3: Contrast
            v3 = np.clip(img_arr * 0.94 + 8, 0, 255)
            
            for v in [v1, v2, v3]:
                all_mob.append(mobilenet_preprocess(v.copy()))
                all_dens.append(densenet_preprocess(v.copy()))
                all_eff.append(v.copy())
        
        p_mob  = mobilenet_model.predict(np.array(all_mob), batch_size=32, verbose=0).reshape((N, 3, -1)).mean(axis=1)
        p_dens = densenet_model.predict(np.array(all_dens), batch_size=32, verbose=0).reshape((N, 3, -1)).mean(axis=1)
        p_eff  = eff_model.predict(np.array(all_eff), batch_size=32, verbose=0).reshape((N, 3, -1)).mean(axis=1)
    
    # Weighted Soft Voting Ensemble: MobileNetV2 (0.45), EfficientNetB0 (0.30), DenseNet121 (0.25)
    p_ens = (0.45 * p_mob) + (0.30 * p_eff) + (0.25 * p_dens)
    return p_mob, p_dens, p_eff, p_ens

print("\n" + "=" * 70)
print("  EVALUATING ON STANDARD TEST SET (348 Images)")
print("=" * 70)
y_true_std = test_std_df['label'].values

pm_std, pd_std, pe_std, pens_std = get_model_predictions_batch(test_std_df, with_tta=False)
pm_tta, pd_tta, pe_tta, pens_tta = get_model_predictions_batch(test_std_df, with_tta=True)

acc_mob  = accuracy_score(y_true_std, np.argmax(pm_std, axis=1))
acc_dens = accuracy_score(y_true_std, np.argmax(pd_std, axis=1))
acc_eff  = accuracy_score(y_true_std, np.argmax(pe_std, axis=1))
acc_ens  = accuracy_score(y_true_std, np.argmax(pens_std, axis=1))
acc_ens_tta = accuracy_score(y_true_std, np.argmax(pens_tta, axis=1))

f1_ens_tta = f1_score(y_true_std, np.argmax(pens_tta, axis=1), average='macro', zero_division=0)
wf1_ens_tta = f1_score(y_true_std, np.argmax(pens_tta, axis=1), average='weighted', zero_division=0)

print(f"  MobileNetV2 Standalone       : {acc_mob*100:.2f}%")
print(f"  DenseNet121 Standalone       : {acc_dens*100:.2f}%")
print(f"  EfficientNetB0 Standalone    : {acc_eff*100:.2f}%")
print(f"  Triple Soft-Voting Ensemble  : {acc_ens*100:.2f}%")
print(f"  Triple Ensemble + TTA        : {acc_ens_tta*100:.2f}%  (Macro-F1: {f1_ens_tta:.4f})")

print("\n" + "=" * 70)
print("  BENCHMARK SUMMARY")
print("=" * 70)
print(f"  Prior Reference Baseline     : 59.83%")
print(f"  MobileNetV2 Baseline (Run 3) : 61.21%")
print(f"  MobileNetV2 + TTA            : 64.08%")
print(f"  Triple Ensemble + TTA        : {acc_ens_tta*100:.2f}%  [NEW SOTA]")
delta_sota = (acc_ens_tta - 0.5983) * 100
print(f"  Net Improvement over Target  : {delta_sota:+.2f}%")
print("=" * 70)

# Save Ensemble Configuration
ens_cfg = {
    'version': 'triple_ensemble_v1',
    'num_classes': CFG.NUM_CLASSES,
    'models': ['MobileNetV2', 'DenseNet121', 'EfficientNetB0'],
    'weights': [0.45, 0.25, 0.30],
    'reference_baseline_acc': 0.5983,
    'mobilenet_standalone_acc': float(acc_mob),
    'densenet_standalone_acc': float(acc_dens),
    'efficientnet_standalone_acc': float(acc_eff),
    'ensemble_acc': float(acc_ens),
    'ensemble_tta_acc': float(acc_ens_tta),
    'macro_f1_tta': float(f1_ens_tta),
    'weighted_f1_tta': float(wf1_ens_tta),
}
with open(MODELS_DIR / 'ensemble_production_config.json', 'w') as f:
    json.dump(ens_cfg, f, indent=2)

# Save Confusion Matrix & Reports
cm = confusion_matrix(y_true_std, np.argmax(pens_tta, axis=1))
cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)

fig, ax = plt.subplots(figsize=(28, 26))
sns.heatmap(cm_norm, annot=False, cmap='Blues', xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, ax=ax)
ax.set_title(f"Confusion Matrix - Triple Ensemble + TTA (Acc: {acc_ens_tta*100:.2f}%, Macro-F1: {f1_ens_tta:.4f})",
             fontsize=12, fontweight='bold')
plt.xticks(fontsize=5, rotation=90); plt.yticks(fontsize=5)
plt.tight_layout()
plt.savefig(FIGS_DIR / 'triple_ensemble_cm.png', dpi=150, bbox_inches='tight')
plt.close()

rep = classification_report(y_true_std, np.argmax(pens_tta, axis=1), target_names=CLASS_NAMES, output_dict=True, zero_division=0)
pd.DataFrame(rep).T.to_csv(OUTPUTS_DIR / 'triple_ensemble_report.csv')

print(f"\nAll reports, confusion matrices, and production configs saved in {OUTPUTS_DIR} and {MODELS_DIR}")
print("[!] RESEARCH PROTOTYPE - verify predictions against prescription.")
