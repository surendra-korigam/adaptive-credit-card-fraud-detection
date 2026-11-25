# Adaptive Credit Card Fraud Detection - Django Edition

This version replaces the previous Starlette/synthetic-data demo with a Django application trained on the real Kaggle ULB Credit Card Fraud Detection CSV.

## Dataset
Download `creditcard.csv` from Kaggle:
https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

Place it at `data/creditcard.csv`. The dataset contains 284,807 transactions and the `Class` target (0 = genuine, 1 = fraud). It has `Time`, `V1`â€“`V28`, `Amount`, and `Class`; it does **not** contain customer names, card numbers, merchant names, or geographic coordinates.

## Windows PowerShell setup
Use Python 3.11 or 3.12 recommended for broad ML package compatibility.

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `py -3.12` is unavailable, use `python -m venv venv` with an installed compatible Python version.

## Train
After placing `creditcard.csv` in `data`:

```powershell
python train_model.py
```

Training performs a stratified 80/20 train-test split, standardizes features, trains Decision Tree, Random Forest and Extra Trees base estimators, and combines them with a Logistic Regression stacking classifier. It saves `artifacts/fraud_model.joblib` and `artifacts/metrics.json`.

Metrics are calculated on the held-out test set. Accuracy alone can be misleading for this highly imbalanced dataset; review precision, recall, F1 and PR-AUC as well. Do not claim a target accuracy until you run training and see the resulting metrics.

## Run Django
```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```
Open http://127.0.0.1:8000/

Click **Start dataset replay** to stream rows from the CSV through the trained model. This is a replay-based real-time demonstration, not a live feed from a bank or payment gateway.

## API
- `GET /api/stats/`
- `GET /api/transactions/`
- `POST /api/stream/start/`
- `POST /api/stream/stop/`
- `POST /api/score/` â€” JSON with `Time`, `V1`..`V28`, `Amount`
- `POST /api/feedback/` â€” stores an analyst label; does not automatically retrain

## Important implementation notes
- The dashboard displays the dataset's `Class` label only as offline ground truth for demonstration/evaluation. A real-time production prediction would not have the ground-truth label at scoring time.
- Decision thresholds are demo defaults: APPROVE below 20%, REVIEW from 20% to below 50%, BLOCK at 50% and above. Tune thresholds using validation data and business costs before production.
- This Django edition currently implements Decision Tree, Random Forest, Extra Trees and a Stacking Classifier. CNN/LSTM are listed in the original presentation but are not implemented in this edition; do not claim they are implemented unless they are added and trained.
- This is an educational demo, not a production payment authorization system.
