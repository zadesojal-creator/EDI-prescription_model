import pickle, numpy as np

with open('outputs/history_baseline.pkl','rb') as f:
    h = pickle.load(f)

print('=== BASELINE RUN 1 TRAINING HISTORY ===')
print(f'  Total epochs run : {len(h["accuracy"])}')
print(f'  Best val_acc     : {max(h["val_accuracy"]):.4f}  at epoch {np.argmax(h["val_accuracy"])+1}')
print(f'  Final train_acc  : {h["accuracy"][-1]:.4f}')
print(f'  Final val_acc    : {h["val_accuracy"][-1]:.4f}')
print()
print(f'  {"Ep":>3}  {"TrainAcc":>9}  {"ValAcc":>8}  {"LR":>10}')
print(f'  {"---":>3}  {"--------":>9}  {"------":>8}  {"----------":>10}')
lr_key = 'learning_rate' if 'learning_rate' in h else 'lr'
lrs = h[lr_key] if lr_key in h else [None]*len(h['accuracy'])
for i, (ta, va, lr) in enumerate(zip(h['accuracy'], h['val_accuracy'], lrs), 1):
    marker = ' <-- BEST' if va == max(h['val_accuracy']) else ''
    print(f'  {i:3d}  {ta:9.4f}  {va:8.4f}  {lr:10.2e}{marker}')
