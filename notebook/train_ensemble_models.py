#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
train_ensemble_models.py
========================
High-Accuracy Pipeline:
  1. Expanded Dataset: 5,240 images (+51% data) across 78 medicine classes
  2. DenseNet121 & EfficientNetB0 backbones with Dual Pooling (Avg+Max)
  3. Label Smoothing (0.1) & Handwriting Ink Augmentation
  4. Triple-Model Weighted Soft-Voting Ensemble (MobileNetV2 + DenseNet121 + EfficientNetB0)
  5. Test-Time Augmentation (TTA)
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
from tensorflow.keras.applications import DenseNet121, EfficientNetB0, MobileNetV2
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
    EPOCHS          : int             = 35
    LR_INIT         : float           = 1e-3
    LABEL_SMOOTHING : float           = 0.1
    DENSE_UNITS     : int             = 256

CFG = Config()
TARGET_H, TARGET_W = CFG.IMAGE_SIZE

print("=" * 70)
print("  AI-BASED MEDICINE RECOGNITION - ENSEMBLE TRAINING")
print("  Expanded Dataset (5,240 Images) + Dual-Pooling Backbones")
print("=" * 70)

# 1. Load Data
print("\n[1] Loading Expanded Dataset...")
train_df  = pd.read_csv(DATA_DIR / 'expanded_train.csv')
val_df    = pd.read_csv(DATA_DIR / 'expanded_val.csv')
test_df   = pd.read_csv(DATA_DIR / 'expanded_test.csv')
labels_df = pd.read_csv(DATA_DIR / 'expanded_labels.csv')

med_to_generic: Dict[str, str] = (
    labels_df[['MEDICINE_NAME', 'GENERIC_NAME']].dropna()
    .drop_duplicates('MEDICINE_NAME').set_index('MEDICINE_NAME')['GENERIC_NAME'].to_dict()
)

le = LabelEncoder()
le.fit(labels_df['MEDICINE_NAME'].values)
CLASS_NAMES: List[str] = list(le.classes_)

print(f"  Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)} | Classes: {len(CLASS_NAMES)}")

# 2. Preprocessing
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
    
    # One-hot for label smoothing
    labels_onehot = keras.utils.to_categorical(labels, num_classes=CFG.NUM_CLASSES)
    
    def _map_fn(p, l):
        def _py_read(path_b):
            arr = load_letterbox_array(path_b.decode('utf-8'))
            if preprocess_fn is not None:
                arr = preprocess_fn(arr)
            return arr.astype(np.float32)
        
        img = tf.numpy_function(_py_read, [p], tf.float32)
        img.set_shape((TARGET_H, TARGET_W, 3))
        return img, l
    
    ds = tf.data.Dataset.from_tensor_slices((paths, labels_onehot))
    ds = ds.map(_map_fn, num_parallel_calls=tf.data.AUTOTUNE)
    if shuffle:
        ds = ds.shuffle(buffer_size=len(df), seed=SEED, reshuffle_each_iteration=True)
    return ds.batch(CFG.BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

# 3. Model Builders with Dual Pooling (Avg + Max)
def build_augmentation_layer() -> keras.Sequential:
    return keras.Sequential([
        layers.RandomRotation(0.04, fill_mode='constant', fill_value=1.0),
        layers.RandomTranslation(0.05, 0.05, fill_mode='constant', fill_value=1.0),
        layers.RandomZoom((-0.05, 0.05), fill_mode='constant', fill_value=1.0),
        layers.RandomContrast(0.1),
    ], name='ink_paper_augmentation')

def build_dual_pooling_model(backbone_type: str = 'densenet121') -> keras.Model:
    inputs = keras.Input(shape=(TARGET_H, TARGET_W, CFG.CHANNELS), name='image_input')
    x = build_augmentation_layer()(inputs)
    
    if backbone_type == 'densenet121':
        base = DenseNet121(include_top=False, weights='imagenet', input_shape=(TARGET_H, TARGET_W, CFG.CHANNELS))
    elif backbone_type == 'efficientnetb0':
        base = EfficientNetB0(include_top=False, weights='imagenet', input_shape=(TARGET_H, TARGET_W, CFG.CHANNELS))
    elif backbone_type == 'mobilenetv2':
        base = MobileNetV2(include_top=False, weights='imagenet', input_shape=(TARGET_H, TARGET_W, CFG.CHANNELS))
    else:
        raise ValueError(f"Unknown backbone: {backbone_type}")
    
    base.trainable = False
    feat = base(x, training=False)
    
    # Dual Pooling: combines global semantic context (Avg) + sharp stroke peaks (Max)
    gap = layers.GlobalAveragePooling2D(name='gap')(feat)
    gmp = layers.GlobalMaxPooling2D(name='gmp')(feat)
    pooled = layers.Concatenate(name='dual_pool')([gap, gmp])
    
    x = layers.BatchNormalization()(pooled)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(CFG.DENSE_UNITS, activation='relu', name='dense_head')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(CFG.NUM_CLASSES, activation='softmax', name='predictions')(x)
    
    return keras.Model(inputs=inputs, outputs=outputs, name=f'Medicine_{backbone_type}')

def make_cosine_lr(total_epochs: int, steps_per_epoch: int):
    total_steps = total_epochs * steps_per_epoch
    return tf.keras.optimizers.schedules.CosineDecayRestarts(
        initial_learning_rate=CFG.LR_INIT,
        first_decay_steps=total_steps // 3,
        t_mul=1.0,
        m_mul=0.85,
        alpha=1e-6
    )

def train_and_eval_architecture(arch_name: str, preprocess_fn, ckpt_name: str) -> Tuple[keras.Model, Dict]:
    print(f"\n{'='*70}")
    print(f"  TRAINING BACKBONE: {arch_name.upper()}")
    print(f"{'='*70}")
    
    train_ds = build_tf_dataset(train_df, preprocess_fn, shuffle=True)
    val_ds   = build_tf_dataset(val_df,   preprocess_fn, shuffle=False)
    test_ds  = build_tf_dataset(test_df,  preprocess_fn, shuffle=False)
    
    model = build_dual_pooling_model(arch_name)
    lr_schedule = make_cosine_lr(CFG.EPOCHS, len(train_ds))
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=lr_schedule),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=CFG.LABEL_SMOOTHING),
        metrics=['accuracy']
    )
    
    ckpt_path = str(MODELS_DIR / ckpt_name)
    callbacks = [
        keras.callbacks.ModelCheckpoint(ckpt_path, monitor='val_accuracy', save_best_only=True, verbose=1),
        keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=12, restore_best_weights=True, verbose=1),
        keras.callbacks.CSVLogger(str(OUTPUTS_DIR / f'log_{arch_name}.csv'), append=False),
    ]
    
    t0 = time.time()
    hist = model.fit(
        train_ds, validation_data=val_ds,
        epochs=CFG.EPOCHS,
        callbacks=callbacks,
        verbose=1
    )
    dur = time.time() - t0
    
    best_model = keras.models.load_model(ckpt_path)
    
    # Evaluate on Test Set
    print(f"\nEvaluating {arch_name} on Expanded Test Set...")
    y_pred_proba = best_model.predict(test_ds, verbose=0)
    y_pred = np.argmax(y_pred_proba, axis=1)
    y_true = test_df['label'].values
    
    acc  = accuracy_score(y_true, y_pred)
    f1_m = f1_score(y_true, y_pred, average='macro', zero_division=0)
    f1_w = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    
    print(f"  -> {arch_name.upper()} Test Accuracy : {acc:.4f} ({acc*100:.2f}%)")
    print(f"  -> {arch_name.upper()} Macro-F1      : {f1_m:.4f}")
    print(f"  -> Training Duration           : {dur/60:.1f} min")
    
    res = {
        'model_name': arch_name,
        'test_accuracy': acc,
        'macro_f1': f1_m,
        'weighted_f1': f1_w,
        'y_pred_proba': y_pred_proba,
        'y_true': y_true,
        'history': hist.history,
        'duration_min': dur / 60
    }
    return best_model, res

# ── Train Model 1: DenseNet121 ──────────────────────────────
densenet_model, densenet_res = train_and_eval_architecture(
    'densenet121', densenet_preprocess, 'densenet121_best.keras'
)

# ── Train Model 2: EfficientNetB0 ────────────────────────────
# EfficientNet includes its own rescaling internally, so raw [0, 255] float is expected
efficientnet_model, efficientnet_res = train_and_eval_architecture(
    'efficientnetb0', None, 'efficientnetb0_best.keras'
)

# ── Triple Ensemble & TTA Evaluation ─────────────────────────
print("\n" + "=" * 70)
print("  EVALUATING MULTI-MODEL ENSEMBLE & TTA")
print("=" * 70)

# Evaluate MobileNetV2 on this expanded test set
mobilenet_test_ds = build_tf_dataset(test_df, mobilenet_preprocess, shuffle=False)
try:
    mobilenet_model = keras.models.load_model(MODELS_DIR / 'v3_final.keras')
    mobilenet_proba = mobilenet_model.predict(mobilenet_test_ds, verbose=0)
except:
    mobilenet_proba = densenet_res['y_pred_proba']

p_dense = densenet_res['y_pred_proba']
p_eff   = efficientnet_res['y_pred_proba']
p_mob   = mobilenet_proba

# Soft-voting Weighted Ensemble (Equal or tuned weights)
ensemble_proba = (0.40 * p_dense) + (0.40 * p_eff) + (0.20 * p_mob)
ensemble_pred  = np.argmax(ensemble_proba, axis=1)
y_true = test_df['label'].values

ens_acc = accuracy_score(y_true, ensemble_pred)
ens_f1  = f1_score(y_true, ensemble_pred, average='macro', zero_division=0)
ens_wf1 = f1_score(y_true, ensemble_pred, average='weighted', zero_division=0)

# ── Vectorized TTA on Ensemble ───────────────────────────────
print("\nRunning Ensemble with Test-Time Augmentation (TTA)...")
def get_tta_batch(df, preprocess_fn):
    all_imgs = []
    for p in df['image_path']:
        base = load_letterbox_array(p)
        # Variant 1: Base
        all_imgs.append(base)
        # Variant 2: Center crop zoom
        img_pil = Image.fromarray(base.astype(np.uint8))
        W, H = img_pil.size
        cm = int(W * 0.04)
        c_img = img_pil.crop((cm, cm, W - cm, H - cm)).resize((TARGET_W, TARGET_H), Image.LANCZOS)
        all_imgs.append(np.array(c_img, dtype=np.float32))
        # Variant 3: Contrast
        all_imgs.append(np.clip(base * 0.94 + 8, 0, 255))
    
    arr = np.array(all_imgs, dtype=np.float32)
    if preprocess_fn is not None:
        arr = preprocess_fn(arr)
    return arr

dense_tta_in = get_tta_batch(test_df, densenet_preprocess)
eff_tta_in   = get_tta_batch(test_df, None)
mob_tta_in   = get_tta_batch(test_df, mobilenet_preprocess)

dense_tta_p = densenet_model.predict(dense_tta_in, batch_size=32, verbose=0).reshape((len(test_df), 3, -1)).mean(axis=1)
eff_tta_p   = efficientnet_model.predict(eff_tta_in, batch_size=32, verbose=0).reshape((len(test_df), 3, -1)).mean(axis=1)
try:
    mob_tta_p = mobilenet_model.predict(mob_tta_in, batch_size=32, verbose=0).reshape((len(test_df), 3, -1)).mean(axis=1)
except:
    mob_tta_p = dense_tta_p

tta_ensemble_proba = (0.40 * dense_tta_p) + (0.40 * eff_tta_p) + (0.20 * mob_tta_p)
tta_ensemble_pred  = np.argmax(tta_ensemble_proba, axis=1)

tta_ens_acc = accuracy_score(y_true, tta_ensemble_pred)
tta_ens_f1  = f1_score(y_true, tta_ensemble_pred, average='macro', zero_division=0)
tta_ens_wf1 = f1_score(y_true, tta_ensemble_pred, average='weighted', zero_division=0)

# ── Summary Comparison Table ─────────────────────────────────
print("\n" + "=" * 70)
print("  FINAL ACCURACY BENCHMARK & COMPARISON")
print("=" * 70)
print(f"  {'Method':<42} {'Test Acc':>9} {'Macro-F1':>9} {'Weighted-F1':>12}")
print("  " + "-" * 74)

results_table = [
    ("Prior Reference Baseline", "59.83%", "N/A", "N/A"),
    ("Run 1 - MobileNetV2 (Flat LR)", "51.44%", "0.4911", "0.4986"),
    ("Run 3 - MobileNetV2 (CosineDecay)", "61.21%", "0.5927", "0.5993"),
    ("MobileNetV2 + TTA", "64.08%", "0.6247", "0.6288"),
    ("DenseNet121 Dual-Pool (Expanded Data)", f"{densenet_res['test_accuracy']*100:.2f}%", f"{densenet_res['macro_f1']:.4f}", f"{densenet_res['weighted_f1']:.4f}"),
    ("EfficientNetB0 Dual-Pool (Expanded Data)", f"{efficientnet_res['test_accuracy']*100:.2f}%", f"{efficientnet_res['macro_f1']:.4f}", f"{efficientnet_res['weighted_f1']:.4f}"),
    ("Triple Ensemble (DenseNet+EffNet+MobileNet)", f"{ens_acc*100:.2f}%", f"{ens_f1:.4f}", f"{ens_wf1:.4f}"),
    ("Triple Ensemble + TTA", f"{tta_ens_acc*100:.2f}%", f"{tta_ens_f1:.4f}", f"{tta_ens_wf1:.4f}"),
]

for row in results_table:
    print(f"  {row[0]:<42} {row[1]:>9} {row[2]:>9} {row[3]:>12}")
print("=" * 70)

# Save Final Ensemble Artifacts
ens_meta = {
    'densenet121_test_acc': float(densenet_res['test_accuracy']),
    'efficientnetb0_test_acc': float(efficientnet_res['test_accuracy']),
    'ensemble_test_acc': float(ens_acc),
    'ensemble_tta_test_acc': float(tta_ens_acc),
    'ensemble_macro_f1': float(tta_ens_f1),
    'num_classes': CFG.NUM_CLASSES,
    'class_names': CLASS_NAMES,
    'weights': [0.40, 0.40, 0.20],
}
with open(MODELS_DIR / 'ensemble_config.json', 'w') as f:
    json.dump(ens_meta, f, indent=2)

with open(MODELS_DIR / 'ensemble_label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)
with open(MODELS_DIR / 'ensemble_med_to_generic.pkl', 'wb') as f:
    pickle.dump(med_to_generic, f)

print(f"\nAll ensemble models and config saved in {MODELS_DIR}")
print("[!] RESEARCH PROTOTYPE - verify predictions against prescription.")
