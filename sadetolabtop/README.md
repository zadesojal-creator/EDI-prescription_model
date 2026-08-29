# Medicine Recognition Portable Package

This folder contains the Triple Ensemble + 3-crop TTA API reported at 82.47% accuracy.

## Run on another laptop

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn ensemble_api:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/docs` to test the API. Send an image to `POST /api/predict`.

The three `.keras` files, label encoder, ensemble configuration, and medicine mapping CSV are included in this folder. The TTA preprocessing is implemented in `ensemble_api.py`.