#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
train_medicine_model.py
=======================
End-to-end training script for:
  "AI-Based Handwritten Medicine Recognition and Generic Medicine
   Identification Using Deep Learning"

Architecture : MobileNetV2 (frozen) → fine-tune
Preprocessing: Letterbox aspect-ratio-preserving padding
Dataset      : 3,458 images / 78 classes (baseline_train/val/test.csv)
Hardware     : AMD Ryzen 5 5600H + 8 GB RAM (CPU training)

Run from project root:
    python notebook\\train_medicine_model.py

Outputs written to:
    models\\   — .keras checkpoints
    outputs\\  — history pkl, CSV logs, figures, reports
"""

# ──────────────────────────────────────────────────────────────
# 0.  Bootstrap — add project root to sys.path
# ──────────────────────────────────────────────────────────────
import sys
import os
import io
from pathlib import Path

# Force UTF-8 output so Unicode chars work on Windows cp1252 consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Resolve root regardless of cwd
SCRIPT_DIR   = Path(__file__).resolve().parent   # notebook/
PROJECT_ROOT = SCRIPT_DIR.parent                 # ediprjcursor/
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(SCRIPT_DIR)

# ──────────────────────────────────────────────────────────────
# SECTION 1: IMPORTS
# ──────────────────────────────────────────────────────────────
import json
import pickle
import random
import warnings
import time
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')          # non-interactive backend (safe for scripts)
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
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess

warnings.filterwarnings('ignore')

print("=" * 70)
print("  AI-BASED HANDWRITTEN MEDICINE RECOGNITION")
print("  Deep Learning Training Script")
print("=" * 70)
print(f"\nPython     : {sys.version.split()[0]}")
print(f"TensorFlow : {tf.__version__}")
print(f"NumPy      : {np.__version__}")

gpus = tf.config.list_physical_devices('GPU')
print(f"GPUs       : {len(gpus)}")
if gpus:
    for g in gpus:
        try:
            tf.config.experimental.set_memory_growth(g, True)
            print(f"  {g.name} — memory growth enabled")
        except RuntimeError as e:
            print(f"  {g.name} — {e}")
else:
    print("  Running on CPU (AMD Ryzen 5 5600H)")

# ──────────────────────────────────────────────────────────────
# SECTION 2: CONFIGURATION
# ──────────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)

DATA_DIR    = PROJECT_ROOT / 'data'
MERGED_DIR  = DATA_DIR / 'merged_dataset'
MODELS_DIR  = PROJECT_ROOT / 'models'
OUTPUTS_DIR = PROJECT_ROOT / 'outputs'
FIGS_DIR    = OUTPUTS_DIR / 'figures'

for d in [MODELS_DIR, OUTPUTS_DIR, FIGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

@dataclass(frozen=True)
class Config:
    IMAGE_SIZE        : Tuple[int, int] = (224, 224)
    CHANNELS          : int             = 3
    NUM_CLASSES       : int             = 78
    BATCH_SIZE        : int             = 16
    # Baseline (frozen)
    EPOCHS_BASELINE   : int             = 30
    LR_BASELINE       : float           = 1e-3
    PATIENCE_BASELINE : int             = 10
    # Fine-tune — gentler: fewer unfrozen layers, lower LR, more patience
    EPOCHS_FINETUNE   : int             = 20
    LR_FINETUNE       : float           = 5e-6
    PATIENCE_FINETUNE : int             = 8
    FINETUNE_LAYERS   : int             = 15
    # Head
    DROPOUT_1         : float           = 0.4
    DROPOUT_2         : float           = 0.3
    DENSE_UNITS       : int             = 128
    # Augmentation
    AUG_ROTATION      : float           = 0.03
    AUG_TRANSLATE     : float           = 0.05
    AUG_ZOOM          : float           = 0.05

CFG = Config()
TARGET_H, TARGET_W = CFG.IMAGE_SIZE

print(f"\nConfig:")
print(f"  Image size      : {CFG.IMAGE_SIZE}")
print(f"  Num classes     : {CFG.NUM_CLASSES}")
print(f"  Batch size      : {CFG.BATCH_SIZE}")
print(f"  Baseline epochs : {CFG.EPOCHS_BASELINE}  (patience={CFG.PATIENCE_BASELINE})")
print(f"  Finetune epochs : {CFG.EPOCHS_FINETUNE}  (patience={CFG.PATIENCE_FINETUNE})")
print(f"  LR baseline/ft  : {CFG.LR_BASELINE} / {CFG.LR_FINETUNE}")

# ──────────────────────────────────────────────────────────────
# SECTION 3: DATASET LOADING
# ──────────────────────────────────────────────────────────────
print("\n" + "-" * 50)
print("[3] Loading dataset splits...")

train_df  = pd.read_csv(MERGED_DIR / 'baseline_train.csv')
val_df    = pd.read_csv(MERGED_DIR / 'baseline_val.csv')
test_df   = pd.read_csv(MERGED_DIR / 'baseline_test.csv')
labels_df = pd.read_csv(MERGED_DIR / 'baseline_labels.csv')

print(f"  Train  : {len(train_df):>5} rows")
print(f"  Val    : {len(val_df):>5} rows")
print(f"  Test   : {len(test_df):>5} rows")
print(f"  Labels : {len(labels_df):>5} rows")
print(f"  Total  : {len(train_df)+len(val_df)+len(test_df):>5} images")

# Medicine → Generic mapping
med_to_generic: Dict[str, str] = (
    labels_df[['MEDICINE_NAME', 'GENERIC_NAME']]
    .dropna()
    .drop_duplicates(subset='MEDICINE_NAME')
    .set_index('MEDICINE_NAME')['GENERIC_NAME']
    .to_dict()
)

# ──────────────────────────────────────────────────────────────
# SECTION 4: LABEL ENCODING
# ──────────────────────────────────────────────────────────────
print("\n[4] Building label encoder...")

le = LabelEncoder()
le.fit(labels_df['MEDICINE_NAME'].values)
CLASS_NAMES: List[str] = list(le.classes_)

print(f"  Classes  : {len(CLASS_NAMES)}")
print(f"  Sample   : {CLASS_NAMES[:5]} ...")

# ──────────────────────────────────────────────────────────────
# SECTION 5: DATASET VERIFICATION
# ──────────────────────────────────────────────────────────────
print("\n[5] Verifying splits...")

for df, name in [(train_df, 'train'), (val_df, 'val'), (test_df, 'test')]:
    classes_in = df['MEDICINE_NAME'].nunique()
    missing    = 0
    for p in df['image_path']:
        if not Path(p).exists():
            missing += 1
    symbol = 'OK' if (classes_in == CFG.NUM_CLASSES and missing == 0) else 'WARN'
    print(f"  [{symbol}] {name:6s}: {len(df)} rows, {classes_in} classes, {missing} missing files")

# ──────────────────────────────────────────────────────────────
# SECTION 7: IMAGE PREPROCESSING
# ──────────────────────────────────────────────────────────────

def preprocess_letterbox(image_path: str) -> np.ndarray:
    """
    Load image → RGB → pad to square (white bg) → resize 224×224
    → MobileNetV2 normalization to [-1, 1].
    Preserves natural aspect ratio of handwritten words.
    """
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            W, H = img.size
            max_dim = max(W, H)
            canvas = Image.new('RGB', (max_dim, max_dim), (255, 255, 255))
            canvas.paste(img, ((max_dim - W) // 2, (max_dim - H) // 2))
            canvas = canvas.resize((TARGET_W, TARGET_H), Image.LANCZOS)
            arr = np.array(canvas, dtype=np.float32)
        return mobilenet_preprocess(arr)
    except Exception:
        return np.zeros((TARGET_H, TARGET_W, 3), dtype=np.float32)


def tf_preprocess_letterbox(path_tensor: tf.Tensor) -> tf.Tensor:
    def _fn(p):
        return preprocess_letterbox(p.numpy().decode()).astype(np.float32)
    result = tf.py_function(_fn, [path_tensor], tf.float32)
    result.set_shape((TARGET_H, TARGET_W, 3))
    return result

# ──────────────────────────────────────────────────────────────
# SECTION 8: tf.data PIPELINE
# ──────────────────────────────────────────────────────────────
print("\n[8] Building tf.data pipelines...")

def make_dataset(df: pd.DataFrame, shuffle: bool = True) -> tf.data.Dataset:
    paths  = df['image_path'].values.astype(str)
    labels = df['label'].values.astype(np.int32)

    ds = tf.data.Dataset.from_tensor_slices((paths, labels))

    def map_fn(path, label):
        img = tf_preprocess_letterbox(path)
        return img, label

    ds = ds.map(map_fn, num_parallel_calls=tf.data.AUTOTUNE)
    if shuffle:
        ds = ds.shuffle(buffer_size=len(df), seed=SEED, reshuffle_each_iteration=True)
    ds = ds.batch(CFG.BATCH_SIZE)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds


train_ds = make_dataset(train_df, shuffle=True)
val_ds   = make_dataset(val_df,   shuffle=False)
test_ds  = make_dataset(test_df,  shuffle=False)

# Verify shape
for imgs, labs in train_ds.take(1):
    print(f"  Batch shape  : images={imgs.shape}, labels={labs.shape}")
    print(f"  Pixel range  : [{imgs.numpy().min():.2f}, {imgs.numpy().max():.2f}]")

print(f"  Batches — train:{len(train_ds)}, val:{len(val_ds)}, test:{len(test_ds)}")

# ──────────────────────────────────────────────────────────────
# SECTION 10: MODEL DEFINITION
# ──────────────────────────────────────────────────────────────
print("\n[10] Building MobileNetV2 model...")

def build_augmentation_layer(name: str = 'data_augmentation') -> keras.Sequential:
    """
    Moderate augmentation for handwritten medicine names.
    No horizontal flip (would corrupt letter shapes).
    """
    return keras.Sequential([
        layers.RandomRotation(
            factor=CFG.AUG_ROTATION,
            fill_mode='constant',
            fill_value=1.0,   # white padding matches letterbox background
        ),
        layers.RandomTranslation(
            height_factor=CFG.AUG_TRANSLATE,
            width_factor=CFG.AUG_TRANSLATE,
            fill_mode='constant',
            fill_value=1.0,
        ),
        layers.RandomZoom(
            height_factor=(-CFG.AUG_ZOOM, CFG.AUG_ZOOM),
            fill_mode='constant',
            fill_value=1.0,
        ),
    ], name=name)


def build_medicine_model(
    augment:        bool = True,
    trainable_base: bool = False,
    name:           str  = 'MedicineRecognizer'
) -> keras.Model:
    """
    Input 224×224×3
    → data_augmentation
    → MobileNetV2(include_top=False, imagenet)
    → GlobalAveragePooling2D
    → Dropout(0.4) → Dense(128, relu) → Dropout(0.3) → Dense(78, softmax)
    """
    inputs = keras.Input(shape=(TARGET_H, TARGET_W, CFG.CHANNELS), name='image_input')
    x = build_augmentation_layer()(inputs) if augment else inputs

    base = MobileNetV2(
        include_top=False,
        weights='imagenet',
        input_shape=(TARGET_H, TARGET_W, CFG.CHANNELS)
    )
    base.trainable = trainable_base
    x = base(x, training=trainable_base)

    x = layers.GlobalAveragePooling2D(name='gap')(x)
    x = layers.Dropout(CFG.DROPOUT_1,   name='dropout_1')(x)
    x = layers.Dense(CFG.DENSE_UNITS, activation='relu', name='dense_128')(x)
    x = layers.Dropout(CFG.DROPOUT_2,   name='dropout_2')(x)
    outputs = layers.Dense(CFG.NUM_CLASSES, activation='softmax', name='predictions')(x)

    return keras.Model(inputs=inputs, outputs=outputs, name=name)


def compile_model(model: keras.Model, lr: float) -> keras.Model:
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=lr),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


model = build_medicine_model(augment=True, trainable_base=False)
compile_model(model, CFG.LR_BASELINE)

trainable_params     = sum(tf.size(w).numpy() for w in model.trainable_weights)
non_trainable_params = sum(tf.size(w).numpy() for w in model.non_trainable_weights)
print(f"  Trainable params     : {trainable_params:,}")
print(f"  Non-trainable params : {non_trainable_params:,}")

# ──────────────────────────────────────────────────────────────
# SECTION 11: TRAINING — BASELINE (FROZEN)
# ──────────────────────────────────────────────────────────────
BASELINE_CKPT = str(MODELS_DIR / 'best_mobilenetv2_baseline.keras')

def get_callbacks(ckpt_path: str, patience: int, log_name: str) -> list:
    return [
        keras.callbacks.ModelCheckpoint(
            filepath=ckpt_path,
            monitor='val_accuracy',
            save_best_only=True,
            save_weights_only=False,
            verbose=1
        ),
        keras.callbacks.EarlyStopping(
            monitor='val_accuracy',
            patience=patience,
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=max(patience // 2, 3),
            min_lr=1e-7,
            verbose=1
        ),
        keras.callbacks.CSVLogger(
            str(OUTPUTS_DIR / log_name),
            append=False
        ),
    ]


print("\n" + "=" * 70)
print("[11] BASELINE TRAINING  (MobileNetV2 frozen)")
print(f"     Epochs={CFG.EPOCHS_BASELINE}  LR={CFG.LR_BASELINE}  Batch={CFG.BATCH_SIZE}")
print("=" * 70)


t0 = time.time()
history_baseline = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=CFG.EPOCHS_BASELINE,
    callbacks=get_callbacks(BASELINE_CKPT, CFG.PATIENCE_BASELINE, 'log_baseline.csv'),
    verbose=1
)
baseline_duration = time.time() - t0

with open(OUTPUTS_DIR / 'history_baseline.pkl', 'wb') as f:
    pickle.dump(history_baseline.history, f)

best_val_acc_baseline = max(history_baseline.history['val_accuracy'])
print(f"\n  Baseline training done in {baseline_duration/60:.1f} min")
print(f"  Best val accuracy : {best_val_acc_baseline:.4f}")
print(f"  Reference baseline: 0.6301")

# ──────────────────────────────────────────────────────────────
# SECTION 12 & 13: EVALUATION HELPERS
# ──────────────────────────────────────────────────────────────

def evaluate_model(
    model: keras.Model,
    ds: tf.data.Dataset,
    class_names: List[str],
    name: str
) -> Dict:
    print(f"\n  Evaluating [{name}]...")
    y_pred_proba = model.predict(ds, verbose=0)
    y_pred = np.argmax(y_pred_proba, axis=1)
    y_true = np.concatenate([y for _, y in ds], axis=0)

    acc     = accuracy_score(y_true, y_pred)
    prec    = precision_score(y_true, y_pred, average='macro', zero_division=0)
    rec     = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1_mac  = f1_score(y_true, y_pred, average='macro', zero_division=0)
    f1_wt   = f1_score(y_true, y_pred, average='weighted', zero_division=0)

    print(f"    Test Accuracy    : {acc:.4f}")
    print(f"    Macro Precision  : {prec:.4f}")
    print(f"    Macro Recall     : {rec:.4f}")
    print(f"    Macro F1         : {f1_mac:.4f}")
    print(f"    Weighted F1      : {f1_wt:.4f}")

    return {
        'experiment'      : name,
        'test_accuracy'   : acc,
        'macro_precision' : prec,
        'macro_recall'    : rec,
        'macro_f1'        : f1_mac,
        'weighted_f1'     : f1_wt,
        'y_true'          : y_true,
        'y_pred'          : y_pred,
        'y_pred_proba'    : y_pred_proba,
    }


def save_classification_report(results: Dict, class_names: List[str]) -> pd.DataFrame:
    report_dict = classification_report(
        results['y_true'], results['y_pred'],
        target_names=class_names, output_dict=True, zero_division=0
    )
    df = pd.DataFrame(report_dict).T
    out = OUTPUTS_DIR / f"report_{results['experiment'].replace(' ', '_')}.csv"
    df.to_csv(out)

    print(f"\n  Per-class report saved → {out.name}")
    # Print worst 10 by F1
    class_df = df.loc[class_names].sort_values('f1-score')
    print(f"\n  Worst 10 classes by F1-score:")
    print(class_df[['precision', 'recall', 'f1-score', 'support']].head(10).to_string())
    return df


# ──────────────────────────────────────────────────────────────
# SECTION 14: CONFUSION MATRIX HELPERS
# ──────────────────────────────────────────────────────────────

def save_confusion_matrix(results: Dict, class_names: List[str], tag: str) -> np.ndarray:
    cm = confusion_matrix(results['y_true'], results['y_pred'])
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)

    fig, ax = plt.subplots(figsize=(28, 26))
    sns.heatmap(cm_norm, annot=False, cmap='Blues',
                xticklabels=class_names, yticklabels=class_names,
                ax=ax, cbar_kws={'label': 'Normalized Recall'})
    ax.set_xlabel('Predicted', fontsize=10)
    ax.set_ylabel('True', fontsize=10)
    ax.set_title(
        f"Confusion Matrix — {results['experiment']}\n"
        f"(Test acc: {results['test_accuracy']:.4f}, Macro-F1: {results['macro_f1']:.4f})",
        fontsize=11, fontweight='bold'
    )
    plt.xticks(fontsize=5, rotation=90)
    plt.yticks(fontsize=5, rotation=0)
    plt.tight_layout()
    path = FIGS_DIR / f'confusion_matrix_{tag}.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Confusion matrix saved → {path.name}")

    # Top-20 confusion pairs
    pairs = []
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            if i != j and cm[i, j] > 0:
                pairs.append({
                    'True'     : class_names[i],
                    'Predicted': class_names[j],
                    'Count'    : cm[i, j],
                    'Rate'     : cm[i, j] / cm[i].sum(),
                })
    pairs_df = (pd.DataFrame(pairs)
                .sort_values('Count', ascending=False)
                .head(20)
                .reset_index(drop=True))
    print(f"\n  Top-20 confusion pairs:")
    print(pairs_df.to_string(index=False))
    pairs_df.to_csv(OUTPUTS_DIR / f'top20_confusions_{tag}.csv', index=False)
    return cm


# ──────────────────────────────────────────────────────────────
# SECTION 17: TRAINING CURVES HELPER
# ──────────────────────────────────────────────────────────────

def save_training_curves(history_dict: Dict, title: str, tag: str) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    epochs = range(1, len(history_dict['accuracy']) + 1)

    ax1.plot(epochs, history_dict['accuracy'],     'b-o', ms=4, label='Train')
    ax1.plot(epochs, history_dict['val_accuracy'], 'r-s', ms=4, label='Val')
    best_ep  = int(np.argmax(history_dict['val_accuracy'])) + 1
    best_val = max(history_dict['val_accuracy'])
    ax1.axvline(best_ep, color='green', ls='--', lw=1,
                label=f'Best={best_val:.3f} (ep {best_ep})')
    ax1.set_xlabel('Epoch'); ax1.set_ylabel('Accuracy')
    ax1.set_title('Accuracy'); ax1.legend(fontsize=8); ax1.grid(True, alpha=0.3)

    ax2.plot(epochs, history_dict['loss'],     'b-o', ms=4, label='Train')
    ax2.plot(epochs, history_dict['val_loss'], 'r-s', ms=4, label='Val')
    ax2.set_xlabel('Epoch'); ax2.set_ylabel('Loss')
    ax2.set_title('Loss'); ax2.legend(fontsize=8); ax2.grid(True, alpha=0.3)

    plt.suptitle(title, fontsize=13, fontweight='bold')
    plt.tight_layout()
    path = FIGS_DIR / f'curves_{tag}.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Training curves saved → {path.name}")


# ──────────────────────────────────────────────────────────────
# RUN BASELINE EVALUATION
# ──────────────────────────────────────────────────────────────
print("\n" + "-" * 50)
print("[12-14] BASELINE EVALUATION")

results_baseline = evaluate_model(model, test_ds, CLASS_NAMES, 'MobileNetV2-Frozen-Letterbox')
save_classification_report(results_baseline, CLASS_NAMES)
cm_baseline = save_confusion_matrix(results_baseline, CLASS_NAMES, 'baseline')
save_training_curves(history_baseline.history, 'Baseline — MobileNetV2 Frozen', 'baseline')

# ──────────────────────────────────────────────────────────────
# SECTION 16: FINE-TUNING
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("[16] FINE-TUNING  (unfreeze last 30 MobileNetV2 layers)")
print(f"     Epochs={CFG.EPOCHS_FINETUNE}  LR={CFG.LR_FINETUNE}")
print("=" * 70)


# Load best baseline checkpoint
model_ft = keras.models.load_model(BASELINE_CKPT)

# Find and partially unfreeze the MobileNetV2 sub-model
base_model_ft = None
for layer in model_ft.layers:
    if isinstance(layer, keras.Model) and 'mobilenet' in layer.name.lower():
        base_model_ft = layer
        break

if base_model_ft is None:
    raise RuntimeError("MobileNetV2 sub-model not found in loaded checkpoint.")

base_model_ft.trainable = True
for layer in base_model_ft.layers[: -CFG.FINETUNE_LAYERS]:
    layer.trainable = False

trainable_now = sum(tf.size(w).numpy() for w in model_ft.trainable_weights)
print(f"  Trainable params after unfreezing: {trainable_now:,}")

model_ft.compile(
    optimizer=keras.optimizers.Adam(learning_rate=CFG.LR_FINETUNE),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

FINETUNE_CKPT = str(MODELS_DIR / 'best_mobilenetv2_finetune.keras')

t0 = time.time()
history_finetune = model_ft.fit(
    train_ds,
    validation_data=val_ds,
    epochs=CFG.EPOCHS_FINETUNE,
    callbacks=get_callbacks(FINETUNE_CKPT, CFG.PATIENCE_FINETUNE, 'log_finetune.csv'),
    verbose=1
)
finetune_duration = time.time() - t0

with open(OUTPUTS_DIR / 'history_finetune.pkl', 'wb') as f:
    pickle.dump(history_finetune.history, f)

best_val_acc_ft = max(history_finetune.history['val_accuracy'])
print(f"\n  Fine-tune done in {finetune_duration/60:.1f} min")
print(f"  Best val accuracy : {best_val_acc_ft:.4f}")

# ──────────────────────────────────────────────────────────────
# FINE-TUNE EVALUATION
# ──────────────────────────────────────────────────────────────
print("\n[12-14] FINE-TUNE EVALUATION")

results_finetune = evaluate_model(model_ft, test_ds, CLASS_NAMES, 'MobileNetV2-FineTuned-Letterbox')
save_classification_report(results_finetune, CLASS_NAMES)
cm_finetune = save_confusion_matrix(results_finetune, CLASS_NAMES, 'finetune')
save_training_curves(history_finetune.history, 'Fine-Tune — MobileNetV2 (last 30 layers)', 'finetune')

# ──────────────────────────────────────────────────────────────
# SECTION 15: ERROR ANALYSIS — KNOWN CONFUSION PAIRS
# ──────────────────────────────────────────────────────────────
KNOWN_CONFUSIONS = [
    ('Maxpro',     'Disopan'),
    ('Ketotab',    'Ketocon'),
    ('Napa Extend','Rivotril'),
    ('Zithrin',    'Diflu'),
    ('Monas',      'Napa'),
    ('Maxima',     'Atrizin'),
    ('Progut',     'Flugal'),
    ('Cetisoft',   'Opton'),
    ('Candinil',   'Azithrocin'),
    ('Azithrocin', 'Atrizin'),
]

print("\n[15] ERROR ANALYSIS -- Known Confusion Pairs")
print(f"  {'True':20s} {'Predicted':20s} {'Count':>6} {'Rate':>8}")
print("  " + "-" * 58)
name_to_idx = {n: i for i, n in enumerate(CLASS_NAMES)}
for true_n, pred_n in KNOWN_CONFUSIONS:
    if true_n in name_to_idx and pred_n in name_to_idx:
        ti, pi = name_to_idx[true_n], name_to_idx[pred_n]
        count  = cm_baseline[ti, pi]
        total  = cm_baseline[ti].sum()
        rate   = count / total if total else 0
        print(f"  {true_n:20s} {pred_n:20s} {count:>6}  {rate:>7.1%}")
    else:
        print(f"  {true_n:20s} {pred_n:20s}   N/A  (class not in test set)")

# ──────────────────────────────────────────────────────────────
# SECTION 17: EXPERIMENT COMPARISON TABLE
# ──────────────────────────────────────────────────────────────
print("\n[17] EXPERIMENT COMPARISON")
print("=" * 70)

comparison_data = [
    {
        'Experiment'      : 'Reference Baseline (prior run)',
        'Test Accuracy'   : '0.5983',
        'Macro-F1'        : 'N/A',
        'Weighted-F1'     : 'N/A',
    },
    {
        'Experiment'      : results_baseline['experiment'],
        'Test Accuracy'   : f"{results_baseline['test_accuracy']:.4f}",
        'Macro-F1'        : f"{results_baseline['macro_f1']:.4f}",
        'Weighted-F1'     : f"{results_baseline['weighted_f1']:.4f}",
    },
    {
        'Experiment'      : results_finetune['experiment'],
        'Test Accuracy'   : f"{results_finetune['test_accuracy']:.4f}",
        'Macro-F1'        : f"{results_finetune['macro_f1']:.4f}",
        'Weighted-F1'     : f"{results_finetune['weighted_f1']:.4f}",
    },
]
comp_df = pd.DataFrame(comparison_data)
print(comp_df.to_string(index=False))
comp_df.to_csv(OUTPUTS_DIR / 'experiment_comparison.csv', index=False)

# Delta vs reference
delta = results_finetune['test_accuracy'] - 0.5983
best_model_name = (
    'fine-tuned' if best_val_acc_ft >= best_val_acc_baseline else 'baseline'
)
print(f"\n  Delta Test Accuracy vs reference baseline: {delta:+.4f}")
print(f"  Best model to deploy: {best_model_name}")

# ──────────────────────────────────────────────────────────────
# SECTION 18 & 20: SAVE BEST MODEL + ARTEFACTS
# ──────────────────────────────────────────────────────────────
print("\n[20] SAVING ARTEFACTS...")

best_model = (
    keras.models.load_model(FINETUNE_CKPT)
    if best_val_acc_ft >= best_val_acc_baseline
    else keras.models.load_model(BASELINE_CKPT)
)

FINAL_MODEL_PATH = MODELS_DIR / 'medicine_recognizer_final.keras'
best_model.save(str(FINAL_MODEL_PATH))
print(f"  [SAVED] Final model   -> {FINAL_MODEL_PATH.name}")

with open(MODELS_DIR / 'label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)
print(f"  [SAVED] LabelEncoder  -> label_encoder.pkl")

with open(MODELS_DIR / 'med_to_generic.pkl', 'wb') as f:
    pickle.dump(med_to_generic, f)
print(f"  [SAVED] Generic map   -> med_to_generic.pkl")

config_export = {
    'num_classes'    : CFG.NUM_CLASSES,
    'image_size'     : list(CFG.IMAGE_SIZE),
    'batch_size'     : CFG.BATCH_SIZE,
    'lr_baseline'    : CFG.LR_BASELINE,
    'lr_finetune'    : CFG.LR_FINETUNE,
    'finetune_layers': CFG.FINETUNE_LAYERS,
    'seed'           : SEED,
    'class_names'    : CLASS_NAMES,
    'baseline'       : {
        'test_accuracy': float(results_baseline['test_accuracy']),
        'macro_f1'     : float(results_baseline['macro_f1']),
        'weighted_f1'  : float(results_baseline['weighted_f1']),
    },
    'finetune'       : {
        'test_accuracy': float(results_finetune['test_accuracy']),
        'macro_f1'     : float(results_finetune['macro_f1']),
        'weighted_f1'  : float(results_finetune['weighted_f1']),
    },
    'best_model'     : best_model_name,
}
with open(MODELS_DIR / 'config.json', 'w') as f:
    json.dump(config_export, f, indent=2)
print(f"  [SAVED] Config        -> config.json")

# ──────────────────────────────────────────────────────────────
# SECTION 18: PREDICTION FUNCTION DEMO
# ──────────────────────────────────────────────────────────────
print("\n[18] PREDICTION FUNCTION DEMO")

def predict_medicine(
    image_path: str,
    model: keras.Model = None,
    class_names: List[str] = None,
    generic_map: Dict[str, str] = None,
    top_k: int = 5,
    verbose: bool = True
) -> Dict:
    """
    ⚠ RESEARCH PROTOTYPE — FOR DECISION SUPPORT ONLY.
    Verify all predictions against the original prescription.
    """
    if model       is None: model       = best_model
    if class_names is None: class_names = CLASS_NAMES
    if generic_map is None: generic_map = med_to_generic

    arr   = preprocess_letterbox(image_path)
    batch = np.expand_dims(arr, 0)
    proba = model.predict(batch, verbose=0)[0]
    top_i = np.argsort(proba)[::-1][:top_k]

    top_preds = [(class_names[i], generic_map.get(class_names[i], 'N/A'), float(proba[i]))
                 for i in top_i]
    top_med, top_gen, top_prob = top_preds[0]

    if verbose:
        print(f"\n  Predicted medicine : {top_med}")
        print(f"  Generic (INN)      : {top_gen}")
        print(f"  Confidence         : {top_prob:.2%}")
        print(f"  Top-{top_k}:")
        for r, (m, g, p) in enumerate(top_preds, 1):
            print(f"    {r}. {m:20s} -> {g:28s} ({p:.2%})")
        print(f"\n  [!] RESEARCH PROTOTYPE -- verify against original prescription.")

    return {
        'predicted_medicine': top_med,
        'predicted_generic' : top_gen,
        'confidence'        : top_prob,
        'top_k_predictions' : top_preds,
    }


# Run on first test image
demo_path = str(test_df['image_path'].iloc[0])
demo_true = test_df['MEDICINE_NAME'].iloc[0]
print(f"  Demo image: {Path(demo_path).name}  (true label: {demo_true})")
predict_medicine(demo_path, model=best_model)

# ──────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ──────────────────────────────────────────────────────────────
total_time = baseline_duration + finetune_duration
print("\n" + "=" * 70)
print("  TRAINING COMPLETE")
print("=" * 70)
print(f"\n  Reference baseline test accuracy : 59.83%")
print(f"  Baseline (frozen)  test accuracy : {results_baseline['test_accuracy']:.2%}")
print(f"  Fine-tuned         test accuracy : {results_finetune['test_accuracy']:.2%}")
print(f"  Delta vs reference               : {delta:+.2%}")
print(f"\n  Total training time : {total_time/60:.1f} min")
print(f"  Best model saved    : {FINAL_MODEL_PATH}")
print(f"\n  All outputs in      : {OUTPUTS_DIR}")
print(f"  All figures in      : {FIGS_DIR}")
print("\n  [!] RESEARCH PROTOTYPE -- all predictions must be verified by a")
print("      qualified pharmacist against the original prescription.")
print("=" * 70)
