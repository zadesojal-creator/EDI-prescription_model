# Model Files & Accuracy Summary

**Project:** AI-Based Handwritten Medicine Recognition & Generic Medicine Identification  
**Dataset:** 78 Medicine Brand Classes (5,240 Total Images)  
**Baseline Target:** 59.83% Test Accuracy  

---

## 📊 Summary of All Saved Models & Accuracies

| Model File Name | Architecture / Description | Dataset | Test Accuracy | Macro F1 | File Size | Relative Gain vs Baseline |
|---|---|---|---|---|---|---|
| **[`efficientnetb0_best.keras`](file:///d:/ediprjcursor/models/efficientnetb0_best.keras)** | **EfficientNetB0 (Dual-Pooling GAP+GMP + Ink Aug)** | Expanded (5,240 imgs) | **83.91%** | **0.8421** | 24.7 MB | **+24.08%** 🏆 *(BEST SOTA)* |
| **[`v3_final.keras`](file:///d:/ediprjcursor/models/v3_final.keras)** | **MobileNetV2 (CosineDecayRestarts + Dense 256)** | Baseline (3,472 imgs) | **61.21%** *(64.08% with TTA)* | **0.6087** | 13.5 MB | **+1.38%** (+4.25% TTA) |
| **[`densenet121_best.keras`](file:///d:/ediprjcursor/models/densenet121_best.keras)** | **DenseNet121 (Dual-Pooling GAP+GMP)** | Expanded (5,240 imgs) | **54.89%** | **0.5376** | 35.5 MB | -4.94% |
| **Triple Ensemble + TTA** | **MobileNetV2 + DenseNet121 + EfficientNetB0 (Soft Voting + TTA)** | Expanded (5,240 imgs) | **82.47%** | **0.8242** | — | **+22.64%** 🚀 |
| **Triple Ensemble Standard** | **MobileNetV2 + DenseNet121 + EfficientNetB0 (Soft Voting)** | Expanded (5,240 imgs) | **80.75%** | **0.8041** | — | **+20.92%** |

---

## 📁 Associated Production & Metadata Files

| File Name | Purpose / Content | Location |
|---|---|---|
| **`ensemble_production_config.json`** | Complete JSON metadata with model paths, weights, and all benchmark accuracy scores | [`models/ensemble_production_config.json`](file:///d:/ediprjcursor/models/ensemble_production_config.json) |
| **`model_accuracies.csv`** | Clean CSV table of all model names and their test accuracies | [`models/model_accuracies.csv`](file:///d:/ediprjcursor/models/model_accuracies.csv) |
| **`v3_label_encoder.pkl`** | Scikit-learn LabelEncoder with all 78 medicine brand class names | [`models/v3_label_encoder.pkl`](file:///d:/ediprjcursor/models/v3_label_encoder.pkl) |
| **`v3_med_to_generic.pkl`** | Python dictionary mapping each brand name to its generic formulation | [`models/v3_med_to_generic.pkl`](file:///d:/ediprjcursor/models/v3_med_to_generic.pkl) |
| **`triple_ensemble_report.csv`** | Per-class precision, recall, and F1-score breakdown for all 78 classes | [`outputs/triple_ensemble_report.csv`](file:///d:/ediprjcursor/outputs/triple_ensemble_report.csv) |
| **`triple_ensemble_cm.png`** | High-resolution confusion matrix plot | [`outputs/figures/triple_ensemble_cm.png`](file:///d:/ediprjcursor/outputs/figures/triple_ensemble_cm.png) |
