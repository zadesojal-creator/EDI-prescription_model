#!/usr/bin/env python
"""
Standalone script to train the medicine recognition model.
Extracted from medicine_recognition_e2e.ipynb
"""

import os
import sys
import json
import pickle
import random
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess_input
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt

# Set seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

# Configuration
@dataclass(frozen=True)
class Config:
    IMAGE_SIZE: tuple = (224, 224)
    BATCH_SIZE: int = 16
    NUM_CLASSES: int = 78
    EPOCHS: int = 30
    LR_BASELINE: float = 1e-3
    LR_FINETUNE: float = 1e-5
    DATA_ROOT: Path = Path("../data")
    MODELS_DIR: Path = Path("../models")
    OUTPUTS_DIR: Path = Path("../outputs")

CFG = Config()
os.chdir(Path(__file__).parent / "notebook")

print("=" * 80)
print("MEDICINE RECOGNITION MODEL TRAINING")
print("=" * 80)
print(f"\nTensorFlow version: {tf.__version__}")
print(f"Working directory: {Path.cwd()}")
print(f"Models directory: {CFG.MODELS_DIR.absolute()}")

# Create necessary directories
for directory in [CFG.MODELS_DIR, CFG.OUTPUTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Load training data
print("\n[1/5] Loading training data...")
try:
    baseline_train_df = pd.read_csv(CFG.DATA_ROOT / "merged_dataset" / "baseline_train.csv")
    baseline_val_df = pd.read_csv(CFG.DATA_ROOT / "merged_dataset" / "baseline_val.csv")
    baseline_test_df = pd.read_csv(CFG.DATA_ROOT / "merged_dataset" / "baseline_test.csv")
    
    expanded_train_df = pd.read_csv(CFG.DATA_ROOT / "merged_dataset" / "expanded_train.csv")
    expanded_val_df = pd.read_csv(CFG.DATA_ROOT / "merged_dataset" / "expanded_val.csv")
    expanded_test_df = pd.read_csv(CFG.DATA_ROOT / "merged_dataset" / "expanded_test.csv")
    
    print(f"  ✓ Baseline train: {len(baseline_train_df)} samples")
    print(f"  ✓ Baseline val: {len(baseline_val_df)} samples")
    print(f"  ✓ Baseline test: {len(baseline_test_df)} samples")
    print(f"  ✓ Expanded train: {len(expanded_train_df)} samples")
    print(f"  ✓ Expanded val: {len(expanded_val_df)} samples")
    print(f"  ✓ Expanded test: {len(expanded_test_df)} samples")
except Exception as e:
    print(f"  ✗ Error loading data: {e}")
    sys.exit(1)

print("\n[2/5] Creating image datasets...")

def preprocess_letterbox(img):
    """Preprocess image with letterboxing."""
    H, W = img.shape[:2]
    max_dim = max(H, W)
    pad_h = (max_dim - H) // 2
    pad_w = (max_dim - W) // 2
    padded = np.pad(img, ((pad_h, max_dim - H - pad_h), (pad_w, max_dim - W - pad_w), (0, 0)), mode='constant', constant_values=255)
    resized = tf.image.resize(padded, CFG.IMAGE_SIZE)
    return mobilenet_preprocess_input(resized)

def load_and_preprocess_image(path):
    try:
        from PIL import Image
        img = Image.open(path).convert('RGB')
        img_array = np.array(img, dtype=np.float32)
        return preprocess_letterbox(img_array)
    except:
        return np.zeros(CFG.IMAGE_SIZE + (3,), dtype=np.float32)

def make_dataset(df, preprocess_fn, shuffle=True, cache=True):
    def load_fn(path, label):
        img = tf.py_function(lambda p: load_and_preprocess_image(p.numpy().decode()), [path], tf.float32)
        img.set_shape(CFG.IMAGE_SIZE + (3,))
        return img, label
    
    ds = tf.data.Dataset.from_tensor_slices((df['image_path'].values, df['label'].values))
    ds = ds.map(load_fn, num_parallel_calls=tf.data.AUTOTUNE)
    if shuffle:
        ds = ds.shuffle(len(df))
    ds = ds.batch(CFG.BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    return ds

baseline_train_ds = make_dataset(baseline_train_df, preprocess_letterbox, shuffle=True)
baseline_val_ds = make_dataset(baseline_val_df, preprocess_letterbox, shuffle=False)
expanded_train_ds = make_dataset(expanded_train_df, preprocess_letterbox, shuffle=True)
expanded_val_ds = make_dataset(expanded_val_df, preprocess_letterbox, shuffle=False)

print("  ✓ Datasets created")

print("\n[3/5] Building model...")

def build_model(augment=True, trainable_base=False):
    inputs = keras.Input(shape=CFG.IMAGE_SIZE + (3,), name="image")
    
    if augment:
        x = keras.Sequential([
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.2),
            layers.RandomZoom(0.2),
        ], name="handwriting_augmentation")(inputs)
    else:
        x = inputs
    
    base = MobileNetV2(include_top=False, input_shape=CFG.IMAGE_SIZE + (3,))
    base.trainable = trainable_base
    x = base(x, training=trainable_base)
    
    x = layers.GlobalAveragePooling2D(name="global_average_pool")(x)
    x = layers.Dropout(0.5, name="head_dropout_1")(x)
    x = layers.Dense(128, activation="relu", name="head_dense")(x)
    x = layers.Dropout(0.3, name="head_dropout_2")(x)
    outputs = layers.Dense(CFG.NUM_CLASSES, activation="softmax", name="medicine")(x)
    
    model = keras.Model(inputs=inputs, outputs=outputs, name="medicine_mobilenetv2")
    return model

def compile_model(model, learning_rate):
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model

baseline_model = compile_model(build_model(augment=True, trainable_base=False), CFG.LR_BASELINE)
print("  ✓ Model built and compiled")
print(f"  Total params: {baseline_model.count_params():,}")

print("\n[4/5] Training baseline model...")
print(f"  Epochs: {CFG.EPOCHS}, Batch size: {CFG.BATCH_SIZE}")
print(f"  This will take approximately 30-60 minutes on CPU...\n")

try:
    baseline_history = baseline_model.fit(
        baseline_train_ds,
        validation_data=baseline_val_ds,
        epochs=CFG.EPOCHS,
        callbacks=[
            keras.callbacks.ModelCheckpoint(
                CFG.MODELS_DIR / "baseline_mobilenetv2.keras",
                monitor="val_accuracy",
                save_best_only=True,
                verbose=1
            ),
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy",
                patience=5,
                verbose=1,
                restore_best_weights=True
            )
        ],
        verbose=1
    )
    print("\n  ✓ Baseline training completed")
    
    # Save training history
    history_dict = {
        'loss': baseline_history.history['loss'],
        'val_loss': baseline_history.history['val_loss'],
        'accuracy': baseline_history.history['accuracy'],
        'val_accuracy': baseline_history.history['val_accuracy']
    }
    with open(CFG.OUTPUTS_DIR / "baseline_history.pkl", 'wb') as f:
        pickle.dump(history_dict, f)
    print(f"  ✓ Training history saved to {CFG.OUTPUTS_DIR / 'baseline_history.pkl'}")
    
except Exception as e:
    print(f"  ✗ Error during training: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[5/5] Training expanded model...")
print(f"  Training on {len(expanded_train_df)} samples...\n")

production_model = compile_model(build_model(augment=True, trainable_base=False), CFG.LR_BASELINE)

try:
    production_history_frozen = production_model.fit(
        expanded_train_ds,
        validation_data=expanded_val_ds,
        epochs=CFG.EPOCHS,
        callbacks=[
            keras.callbacks.ModelCheckpoint(
                CFG.MODELS_DIR / "production_mobilenetv2_frozen.keras",
                monitor="val_accuracy",
                save_best_only=True,
                verbose=1
            ),
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy",
                patience=5,
                verbose=1,
                restore_best_weights=True
            )
        ],
        verbose=1
    )
    print("\n  ✓ Production model (frozen base) training completed")
    
    # Fine-tune with unfrozen base layers
    print("\n  Fine-tuning with unfrozen base layers...")
    mobile_base = production_model.layers[2]  # MobileNetV2 layer
    mobile_base.trainable = True
    
    for layer in mobile_base.layers[:-30]:
        layer.trainable = False
    
    production_model = compile_model(production_model, CFG.LR_FINETUNE)
    
    production_history_finetune = production_model.fit(
        expanded_train_ds,
        validation_data=expanded_val_ds,
        epochs=CFG.EPOCHS,
        callbacks=[
            keras.callbacks.ModelCheckpoint(
                CFG.MODELS_DIR / "production_mobilenetv2.keras",
                monitor="val_accuracy",
                save_best_only=True,
                verbose=1
            ),
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy",
                patience=5,
                verbose=1,
                restore_best_weights=True
            )
        ],
        verbose=1
    )
    print("\n  ✓ Fine-tuning completed")
    
    # Save training histories
    history_dict = {
        'frozen': production_history_frozen.history,
        'finetune': production_history_finetune.history
    }
    with open(CFG.OUTPUTS_DIR / "production_history.pkl", 'wb') as f:
        pickle.dump(history_dict, f)
    print(f"  ✓ Training history saved to {CFG.OUTPUTS_DIR / 'production_history.pkl'}")
    
except Exception as e:
    print(f"  ✗ Error during production training: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("TRAINING COMPLETE!")
print("=" * 80)
print(f"\nModels saved to: {CFG.MODELS_DIR.absolute()}")
print(f"  - baseline_mobilenetv2.keras")
print(f"  - production_mobilenetv2_frozen.keras")
print(f"  - production_mobilenetv2.keras")
