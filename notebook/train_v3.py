#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
train_v3.py
===========
Run 3 - targeted improvements over Run 1 (51.44% test acc):

Root-cause fixes:
  1. LR schedule: use CosineDecayRestarts instead of relying on
     ReduceLROnPlateau (which never fired in Run 1 since val_loss
     kept fluctuating). This gives smooth, guaranteed LR decay.
  2. Dropout reduced: 0.4->0.3 and 0.3->0.2 (model was underfitting,
     not overfitting - train acc ~= val acc throughout).
  3. Dense head doubled: 128->256 to add capacity.
  4. Longer training: patience=12 (was 8).
  5. Fine-tune: only unfreeze last 15 layers (not 30), LR=5e-6,
     patience=8. Load BEST baseline checkpoint before fine-tuning.
  6. ReduceLROnPlateau min_delta=0.001 so it actually triggers.
"""

import sys, os, io, json, pickle, random, time, warnings
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple

# Force UTF-8 output on Windows cp1252
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
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess

warnings.filterwarnings('ignore')

# ── Seeds ────────────────────────────────────────────────────
SEED = 42
random.seed(SEED); np.random.seed(SEED); tf.random.set_seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)

# ── Paths ────────────────────────────────────────────────────
DATA_DIR    = PROJECT_ROOT / 'data'
MERGED_DIR  = DATA_DIR / 'merged_dataset'
MODELS_DIR  = PROJECT_ROOT / 'models'
OUTPUTS_DIR = PROJECT_ROOT / 'outputs'
FIGS_DIR    = OUTPUTS_DIR / 'figures'
for d in [MODELS_DIR, OUTPUTS_DIR, FIGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Config ────────────────────────────────────────────────────
@dataclass(frozen=True)
class Config:
    IMAGE_SIZE        : Tuple[int, int] = (224, 224)
    CHANNELS          : int             = 3
    NUM_CLASSES       : int             = 78
    BATCH_SIZE        : int             = 16
    # Baseline
    EPOCHS_BASELINE   : int             = 40        # extra budget
    LR_BASELINE       : float           = 1e-3
    PATIENCE_BASELINE : int             = 12        # was 8
    # Fine-tune
    EPOCHS_FINETUNE   : int             = 25
    LR_FINETUNE       : float           = 5e-6      # gentler
    PATIENCE_FINETUNE : int             = 8
    FINETUNE_LAYERS   : int             = 15        # was 30
    # Head - reduced dropout for underfitting model
    DROPOUT_1         : float           = 0.3       # was 0.4
    DROPOUT_2         : float           = 0.2       # was 0.3
    DENSE_UNITS       : int             = 256       # was 128
    # Augmentation (unchanged - already moderate)
    AUG_ROTATION      : float           = 0.03
    AUG_TRANSLATE     : float           = 0.05
    AUG_ZOOM          : float           = 0.05

CFG = Config()
TARGET_H, TARGET_W = CFG.IMAGE_SIZE

print("=" * 70)
print("  MEDICINE RECOGNITION - RUN 3 (Targeted Improvements)")
print("=" * 70)
print(f"  Reference baseline  : 59.83%")
print(f"  Run 1 test acc      : 51.44%  (LR never decayed, head too small)")
print(f"  Run 3 fixes         : CosineDecay LR, larger head, reduced dropout")
print(f"  Python : {sys.version.split()[0]}   TF : {tf.__version__}")
gpus = tf.config.list_physical_devices('GPU')
print(f"  GPUs   : {len(gpus)} {'(CPU mode)' if not gpus else ''}")
for g in gpus:
    try: tf.config.experimental.set_memory_growth(g, True)
    except: pass
print()

# ── Load data ────────────────────────────────────────────────
print("[1] Loading data...")
train_df  = pd.read_csv(MERGED_DIR / 'baseline_train.csv')
val_df    = pd.read_csv(MERGED_DIR / 'baseline_val.csv')
test_df   = pd.read_csv(MERGED_DIR / 'baseline_test.csv')
labels_df = pd.read_csv(MERGED_DIR / 'baseline_labels.csv')

med_to_generic: Dict[str, str] = (
    labels_df[['MEDICINE_NAME', 'GENERIC_NAME']].dropna()
    .drop_duplicates('MEDICINE_NAME').set_index('MEDICINE_NAME')['GENERIC_NAME'].to_dict()
)
le = LabelEncoder()
le.fit(labels_df['MEDICINE_NAME'].values)
CLASS_NAMES: List[str] = list(le.classes_)

print(f"  Train={len(train_df)}  Val={len(val_df)}  Test={len(test_df)}  Classes={len(CLASS_NAMES)}")

# ── Preprocessing ────────────────────────────────────────────
def preprocess_letterbox(image_path: str) -> np.ndarray:
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
    r = tf.py_function(_fn, [path_tensor], tf.float32)
    r.set_shape((TARGET_H, TARGET_W, 3))
    return r

# ── tf.data pipeline ─────────────────────────────────────────
print("[2] Building pipelines...")
def make_dataset(df: pd.DataFrame, shuffle: bool) -> tf.data.Dataset:
    paths  = df['image_path'].values.astype(str)
    labels = df['label'].values.astype(np.int32)
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    ds = ds.map(lambda p, l: (tf_preprocess_letterbox(p), l),
                num_parallel_calls=tf.data.AUTOTUNE)
    if shuffle:
        ds = ds.shuffle(len(df), seed=SEED, reshuffle_each_iteration=True)
    return ds.batch(CFG.BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

train_ds = make_dataset(train_df, shuffle=True)
val_ds   = make_dataset(val_df,   shuffle=False)
test_ds  = make_dataset(test_df,  shuffle=False)

# ── Model ────────────────────────────────────────────────────
print("[3] Building model...")
def build_augmentation_layer() -> keras.Sequential:
    return keras.Sequential([
        layers.RandomRotation(CFG.AUG_ROTATION, fill_mode='constant', fill_value=1.0),
        layers.RandomTranslation(CFG.AUG_TRANSLATE, CFG.AUG_TRANSLATE,
                                  fill_mode='constant', fill_value=1.0),
        layers.RandomZoom((-CFG.AUG_ZOOM, CFG.AUG_ZOOM),
                           fill_mode='constant', fill_value=1.0),
    ], name='augmentation')

def build_medicine_model(trainable_base: bool = False) -> keras.Model:
    inputs = keras.Input(shape=(TARGET_H, TARGET_W, CFG.CHANNELS), name='image_input')
    x = build_augmentation_layer()(inputs)
    base = MobileNetV2(include_top=False, weights='imagenet',
                        input_shape=(TARGET_H, TARGET_W, CFG.CHANNELS))
    base.trainable = trainable_base
    x = base(x, training=trainable_base)
    x = layers.GlobalAveragePooling2D(name='gap')(x)
    x = layers.Dropout(CFG.DROPOUT_1, name='dropout_1')(x)
    x = layers.Dense(CFG.DENSE_UNITS, activation='relu', name='dense_head')(x)
    x = layers.Dropout(CFG.DROPOUT_2, name='dropout_2')(x)
    outputs = layers.Dense(CFG.NUM_CLASSES, activation='softmax', name='predictions')(x)
    return keras.Model(inputs=inputs, outputs=outputs, name='MedicineV3')

# ── LR Schedule: Cosine Decay with Warm Restarts ─────────────
# Guarantees LR actually decays, unlike ReduceLROnPlateau which
# never triggered in Run 1 because val_loss fluctuated too much.
steps_per_epoch = len(train_ds)

def make_cosine_lr(initial_lr: float, total_epochs: int, t_mul: float = 1.0):
    total_steps = total_epochs * steps_per_epoch
    return tf.keras.optimizers.schedules.CosineDecayRestarts(
        initial_learning_rate=initial_lr,
        first_decay_steps=total_steps // 3,   # restart every ~13 epochs
        t_mul=t_mul,
        m_mul=0.9,                             # slightly reduce peak on each restart
        alpha=1e-6                             # floor LR
    )

# ── Callbacks ────────────────────────────────────────────────
def get_callbacks(ckpt_path: str, patience: int, log_name: str,
                  use_rlrp: bool = True) -> list:
    """
    use_rlrp=False when optimizer uses a LearningRateSchedule object
    (e.g. CosineDecayRestarts), since ReduceLROnPlateau cannot set the
    LR on a schedule-based optimizer and will raise a TypeError.
    """
    cbs = [
        keras.callbacks.ModelCheckpoint(
            ckpt_path, monitor='val_accuracy',
            save_best_only=True, verbose=1
        ),
        keras.callbacks.EarlyStopping(
            monitor='val_accuracy', patience=patience,
            restore_best_weights=True, verbose=1
        ),
        keras.callbacks.CSVLogger(str(OUTPUTS_DIR / log_name), append=False),
    ]
    if use_rlrp:
        cbs.insert(2, keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5,
            patience=4, min_delta=0.005,
            min_lr=1e-7, verbose=1
        ))
    return cbs

# ── Baseline Training (frozen base) ──────────────────────────
model = build_medicine_model(trainable_base=False)
model.compile(
    optimizer=keras.optimizers.Adam(
        learning_rate=make_cosine_lr(CFG.LR_BASELINE, CFG.EPOCHS_BASELINE)
    ),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

tp = sum(tf.size(w).numpy() for w in model.trainable_weights)
np_ = sum(tf.size(w).numpy() for w in model.non_trainable_weights)
print(f"  Trainable={tp:,}   Non-trainable={np_:,}")
print(f"  Head: Dense({CFG.DENSE_UNITS}) + Dropout({CFG.DROPOUT_1},{CFG.DROPOUT_2})")

BASELINE_CKPT = str(MODELS_DIR / 'v3_baseline.keras')
print(f"\n{'='*70}")
print(f"[BASELINE] Epochs={CFG.EPOCHS_BASELINE}  LR=CosineDecay(1e-3)  Patience={CFG.PATIENCE_BASELINE}")
print(f"{'='*70}")

t0 = time.time()
history_bl = model.fit(
    train_ds, validation_data=val_ds,
    epochs=CFG.EPOCHS_BASELINE,
    callbacks=get_callbacks(BASELINE_CKPT, CFG.PATIENCE_BASELINE, 'v3_log_baseline.csv',
                             use_rlrp=False),   # CosineDecay schedule: cannot use RLRP
    verbose=1
)
bl_time = time.time() - t0

with open(OUTPUTS_DIR / 'v3_history_baseline.pkl', 'wb') as f:
    pickle.dump(history_bl.history, f)

best_bl_val = max(history_bl.history['val_accuracy'])
best_bl_ep  = int(np.argmax(history_bl.history['val_accuracy'])) + 1
print(f"\n  Baseline done in {bl_time/60:.1f} min")
print(f"  Best val_acc = {best_bl_val:.4f}  at epoch {best_bl_ep}")

# ── Evaluate baseline ────────────────────────────────────────
def evaluate_model(mdl, ds, name):
    print(f"\n  Evaluating [{name}]...")
    yp  = mdl.predict(ds, verbose=0)
    y_pred = np.argmax(yp, axis=1)
    y_true = np.concatenate([y for _, y in ds])
    acc   = accuracy_score(y_true, y_pred)
    f1mac = f1_score(y_true, y_pred, average='macro',    zero_division=0)
    f1wt  = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    prec  = precision_score(y_true, y_pred, average='macro', zero_division=0)
    rec   = recall_score(y_true, y_pred, average='macro',    zero_division=0)
    print(f"    Accuracy : {acc:.4f}")
    print(f"    Macro-F1 : {f1mac:.4f}   Weighted-F1 : {f1wt:.4f}")
    print(f"    Precision: {prec:.4f}   Recall      : {rec:.4f}")
    return dict(experiment=name, test_accuracy=acc,
                macro_f1=f1mac, weighted_f1=f1wt,
                macro_precision=prec, macro_recall=rec,
                y_true=y_true, y_pred=y_pred, y_pred_proba=yp)

def save_cm(results, tag):
    cm = confusion_matrix(results['y_true'], results['y_pred'])
    cm_n = cm.astype(float) / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(28, 26))
    sns.heatmap(cm_n, annot=False, cmap='Blues',
                xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, ax=ax)
    ax.set_title(f"Confusion Matrix - {results['experiment']}\nAcc={results['test_accuracy']:.4f}  F1={results['macro_f1']:.4f}",
                 fontsize=11, fontweight='bold')
    plt.xticks(fontsize=5, rotation=90); plt.yticks(fontsize=5)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / f'v3_cm_{tag}.png', dpi=150, bbox_inches='tight')
    plt.close()
    # Top-20 pairs
    pairs = [(CLASS_NAMES[i], CLASS_NAMES[j], int(cm[i,j]), cm[i,j]/cm[i].sum())
             for i in range(len(CLASS_NAMES)) for j in range(len(CLASS_NAMES))
             if i != j and cm[i,j] > 0]
    pdf = pd.DataFrame(pairs, columns=['True','Predicted','Count','Rate'])
    top20 = pdf.sort_values('Count', ascending=False).head(20)
    print(f"\n  Top-20 confusions ({tag}):")
    print(top20.to_string(index=False))
    top20.to_csv(OUTPUTS_DIR / f'v3_top20_confusions_{tag}.csv', index=False)
    return cm

def save_report(results, tag):
    rep = classification_report(results['y_true'], results['y_pred'],
                                target_names=CLASS_NAMES, output_dict=True, zero_division=0)
    df = pd.DataFrame(rep).T
    df.to_csv(OUTPUTS_DIR / f'v3_report_{tag}.csv')
    worst10 = df.loc[CLASS_NAMES].sort_values('f1-score').head(10)
    print(f"\n  Worst 10 classes by F1 ({tag}):")
    print(worst10[['precision','recall','f1-score','support']].to_string())

def save_curves(hist, title, tag):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    eps = range(1, len(hist['accuracy'])+1)
    ax1.plot(eps, hist['accuracy'], 'b-o', ms=4, label='Train')
    ax1.plot(eps, hist['val_accuracy'], 'r-s', ms=4, label='Val')
    best_ep = int(np.argmax(hist['val_accuracy']))+1
    best_va = max(hist['val_accuracy'])
    ax1.axvline(best_ep, color='green', ls='--', lw=1, label=f'Best={best_va:.3f}@ep{best_ep}')
    ax1.axhline(0.5983, color='orange', ls=':', lw=1.5, label='Reference 59.83%')
    ax1.set_xlabel('Epoch'); ax1.set_ylabel('Accuracy'); ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3); ax1.set_title('Accuracy')
    ax2.plot(eps, hist['loss'], 'b-o', ms=4, label='Train')
    ax2.plot(eps, hist['val_loss'], 'r-s', ms=4, label='Val')
    ax2.set_xlabel('Epoch'); ax2.set_ylabel('Loss'); ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3); ax2.set_title('Loss')
    plt.suptitle(title, fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(FIGS_DIR / f'v3_curves_{tag}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Curves saved -> v3_curves_{tag}.png")

print("\n[EVAL] Baseline")
res_bl = evaluate_model(model, test_ds, 'V3-Baseline-Frozen')
save_cm(res_bl, 'baseline')
save_report(res_bl, 'baseline')
save_curves(history_bl.history, 'Run 3 - Baseline (Frozen MobileNetV2)', 'baseline')

# ── Fine-Tuning ───────────────────────────────────────────────
print(f"\n{'='*70}")
print(f"[FINE-TUNE] Load best baseline, unfreeze last {CFG.FINETUNE_LAYERS} layers")
print(f"           LR={CFG.LR_FINETUNE}  Patience={CFG.PATIENCE_FINETUNE}")
print(f"{'='*70}")

model_ft = keras.models.load_model(BASELINE_CKPT)
base_ft = next((l for l in model_ft.layers
                if isinstance(l, keras.Model) and 'mobilenet' in l.name.lower()), None)
if base_ft is None:
    raise RuntimeError("MobileNetV2 sub-model not found.")

base_ft.trainable = True
for layer in base_ft.layers[:-CFG.FINETUNE_LAYERS]:
    layer.trainable = False

tp_ft = sum(tf.size(w).numpy() for w in model_ft.trainable_weights)
print(f"  Trainable params after unfreeze: {tp_ft:,}")

# Use constant low LR for fine-tune (no cosine restart needed over ~25 epochs)
model_ft.compile(
    optimizer=keras.optimizers.Adam(learning_rate=CFG.LR_FINETUNE),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

FINETUNE_CKPT = str(MODELS_DIR / 'v3_finetune.keras')
t0 = time.time()
history_ft = model_ft.fit(
    train_ds, validation_data=val_ds,
    epochs=CFG.EPOCHS_FINETUNE,
    callbacks=get_callbacks(FINETUNE_CKPT, CFG.PATIENCE_FINETUNE, 'v3_log_finetune.csv',
                             use_rlrp=True),    # constant float LR: RLRP can fire here
    verbose=1
)
ft_time = time.time() - t0

with open(OUTPUTS_DIR / 'v3_history_finetune.pkl', 'wb') as f:
    pickle.dump(history_ft.history, f)

best_ft_val = max(history_ft.history['val_accuracy'])
best_ft_ep  = int(np.argmax(history_ft.history['val_accuracy'])) + 1
print(f"\n  Fine-tune done in {ft_time/60:.1f} min")
print(f"  Best val_acc = {best_ft_val:.4f}  at epoch {best_ft_ep}")

print("\n[EVAL] Fine-tuned")
res_ft = evaluate_model(model_ft, test_ds, 'V3-FineTuned')
save_cm(res_ft, 'finetune')
save_report(res_ft, 'finetune')
save_curves(history_ft.history, 'Run 3 - Fine-Tuned (last 15 layers)', 'finetune')

# ── Select & Save Best Model ──────────────────────────────────
print("\n[SAVE] Selecting best model...")
best_model_tag = 'finetune' if best_ft_val >= best_bl_val else 'baseline'
best_model = keras.models.load_model(
    FINETUNE_CKPT if best_model_tag == 'finetune' else BASELINE_CKPT
)
best_res = res_ft if best_model_tag == 'finetune' else res_bl

FINAL_PATH = MODELS_DIR / 'v3_final.keras'
best_model.save(str(FINAL_PATH))

with open(MODELS_DIR / 'v3_label_encoder.pkl', 'wb') as f: pickle.dump(le, f)
with open(MODELS_DIR / 'v3_med_to_generic.pkl', 'wb') as f: pickle.dump(med_to_generic, f)

config_out = {
    'version': 'v3', 'num_classes': CFG.NUM_CLASSES,
    'image_size': list(CFG.IMAGE_SIZE), 'batch_size': CFG.BATCH_SIZE,
    'dense_units': CFG.DENSE_UNITS, 'dropout': [CFG.DROPOUT_1, CFG.DROPOUT_2],
    'lr_schedule': 'CosineDecayRestarts', 'finetune_layers': CFG.FINETUNE_LAYERS,
    'best_model': best_model_tag, 'class_names': CLASS_NAMES,
    'baseline': {k: float(v) for k, v in res_bl.items()
                 if k in ('test_accuracy','macro_f1','weighted_f1')},
    'finetune': {k: float(v) for k, v in res_ft.items()
                 if k in ('test_accuracy','macro_f1','weighted_f1')},
}
with open(MODELS_DIR / 'v3_config.json', 'w') as f:
    json.dump(config_out, f, indent=2)

print(f"  Best model : {best_model_tag}")
print(f"  Saved      : {FINAL_PATH.name}")

# ── Comparison Table ──────────────────────────────────────────
total_time = bl_time + ft_time
print(f"\n{'='*70}")
print("  RUN 3 COMPLETE")
print(f"{'='*70}")
print(f"\n  {'Experiment':<35} {'TestAcc':>8} {'MacroF1':>8} {'WeightedF1':>11}")
print(f"  {'-'*65}")
rows = [
    ('Reference Baseline (prior run)',    0.5983, None,  None),
    ('Run 1 - Frozen (LR never decayed)', 0.5144, 0.4911, 0.4986),
    (f'Run 3 - Baseline (CosineDecay)',   res_bl['test_accuracy'], res_bl['macro_f1'], res_bl['weighted_f1']),
    (f'Run 3 - Fine-tuned',               res_ft['test_accuracy'], res_ft['macro_f1'], res_ft['weighted_f1']),
]
for name, acc, f1, wf1 in rows:
    f1_s  = f'{f1:.4f}'  if f1  is not None else '  N/A  '
    wf1_s = f'{wf1:.4f}' if wf1 is not None else '  N/A  '
    print(f"  {name:<35} {acc:>8.4f} {f1_s:>8} {wf1_s:>11}")

best_acc = best_res['test_accuracy']
delta    = best_acc - 0.5983
print(f"\n  Delta vs reference : {delta:+.4f} ({delta*100:+.2f}%)")
print(f"  Total time         : {total_time/60:.1f} min")
print(f"\n  [!] RESEARCH PROTOTYPE - verify all predictions against prescription.")
print(f"{'='*70}")

# ── Prediction demo ───────────────────────────────────────────
demo_path = str(test_df['image_path'].iloc[0])
demo_true = test_df['MEDICINE_NAME'].iloc[0]
arr   = preprocess_letterbox(demo_path)
proba = best_model.predict(np.expand_dims(arr, 0), verbose=0)[0]
top5  = np.argsort(proba)[::-1][:5]
print(f"\n  DEMO: {Path(demo_path).name}  (True: {demo_true})")
for r, i in enumerate(top5, 1):
    print(f"    {r}. {CLASS_NAMES[i]:20s} -> {med_to_generic.get(CLASS_NAMES[i],'N/A'):28s} ({proba[i]:.1%})")
