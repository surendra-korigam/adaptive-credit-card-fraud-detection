import json
import logging
import math
import threading
import random

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import Transaction
from .ml import DATA, FEATURES, load_artifact, predict_row

logger = logging.getLogger(__name__)
_stream = {"running": False, "index": 0}
_lock = threading.Lock()



def dashboard(request):
    bundle = load_artifact()
    metrics = bundle["metrics"] if bundle else None
    response = render(request, "monitor/dashboard.html", {
        "metrics": metrics,
        "model_ready": bundle is not None,
        "dataset_exists": DATA.exists(),
    })
    response["Cache-Control"] = "no-store"
    return response



@require_GET
def stats(request):
    total = Transaction.objects.count()
    blocked = Transaction.objects.filter(decision="BLOCK").count()
    reviewed = Transaction.objects.filter(decision="REVIEW").count()
    fraud = Transaction.objects.filter(actual_class=1).count()
    response = JsonResponse({
        "total": total, "blocked": blocked, "review": reviewed,
        "actual_fraud": fraud, "streaming": _stream["running"],
        "model_ready": load_artifact() is not None,
    })
    response["Cache-Control"] = "no-store"
    return response



def _replay_batch(batch_size=8):
    bundle = load_artifact()
    if bundle is None:
        return

    # Use the Kaggle dataset when it is available.
    if DATA.exists():
        with _lock:
            start = _stream["index"]
            try:
                df = pd.read_csv(
                    DATA,
                    skiprows=range(1, start + 1),
                    nrows=batch_size
                )
            except Exception:
                logger.exception("Dataset replay failed")
                return

            if df.empty:
                _stream["index"] = 0
                return

            _stream["index"] += len(df)

        rows = []
        for _, row in df.iterrows():
            values = {key: float(row[key]) for key in FEATURES}
            try:
                probability, decision = predict_row(values, bundle)
                rows.append(Transaction(
                    dataset_time=float(row["Time"]),
                    amount=float(row["Amount"]),
                    fraud_probability=probability,
                    decision=decision,
                    actual_class=int(row["Class"]),
                    source="dataset",
                ))
            except Exception:
                logger.exception("Could not score a replay row")

    else:
        # Safe synthetic demo data when the Kaggle CSV is unavailable.
        with _lock:
            if _stream["index"] >= 100:
                _stream["running"] = False
                return

            start = _stream["index"]
            count = min(batch_size, 100 - start)
            _stream["index"] += count

        rows = []
        for i in range(count):
            values = {}
            for key in FEATURES:
                if key == "Time":
                    values[key] = float(start + i)
                elif key == "Amount":
                    values[key] = round(random.uniform(1, 500), 2)
                else:
                    values[key] = random.gauss(0, 1)

            try:
                probability, decision = predict_row(values, bundle)
                rows.append(Transaction(
                    dataset_time=values.get("Time"),
                    amount=values["Amount"],
                    fraud_probability=probability,
                    decision=decision,
                    actual_class=None,
                    source="synthetic",
                ))
            except Exception:
                logger.exception("Could not score a synthetic demo row")

    if rows:
        Transaction.objects.bulk_create(rows)



@require_GET
def transactions(request):
    if _stream["running"]:
        _replay_batch()
    queryset = Transaction.objects.order_by("-id")[:100]
    data = [{
        "id": transaction.id,
        "time": transaction.created_at.strftime("%H:%M:%S"),
        "amount": round(transaction.amount, 2),
        "risk": round(transaction.fraud_probability * 100, 2),
        "decision": transaction.decision,
        "actual": "FRAUD" if transaction.actual_class == 1 else (
            "GENUINE" if transaction.actual_class == 0 else "UNKNOWN"
        ),
        "source": transaction.source,
    } for transaction in queryset]
    response = JsonResponse({"transactions": data})
    response["Cache-Control"] = "no-store"
    return response



@require_POST
def start_stream(request):
    _stream["running"] = True
    return JsonResponse({"running": True, "message": "Dataset replay started"})



@require_POST
def stop_stream(request):
    _stream["running"] = False
    return JsonResponse({"running": False})


@login_required
@require_POST
def score_transaction(request):
    try:
        payload = json.loads(request.body or b"{}")
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object.")
        missing = [key for key in FEATURES if key not in payload]
        if missing:
            raise ValueError("Missing required transaction features.")
        values = {}
        for key in FEATURES:
            value = float(payload[key])
            if not math.isfinite(value):
                raise ValueError("Feature values must be finite numbers.")
            values[key] = value
        probability, decision = predict_row(values)
        transaction = Transaction.objects.create(
            amount=values["Amount"], fraud_probability=probability,
            decision=decision, source="manual",
        )
        return JsonResponse({
            "id": transaction.id, "risk": round(probability * 100, 2),
            "decision": decision,
        })
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid transaction payload or feature values."}, status=400)
    except Exception:
        logger.exception("Transaction scoring failed")
        return JsonResponse({"error": "Unable to score transaction at this time."}, status=500)


@login_required
@require_POST
def feedback(request):
    try:
        payload = json.loads(request.body or b"{}")
        if not isinstance(payload, dict):
            raise ValueError
        transaction_id = int(payload["transaction_id"])
        label = int(payload["is_fraud"])
        if label not in (0, 1):
            raise ValueError
        transaction = Transaction.objects.get(pk=transaction_id)
        transaction.feedback_class = label
        transaction.save(update_fields=["feedback_class"])
        return JsonResponse({
            "status": "saved",
            "note": "Feedback is stored for review; it does not silently retrain the model.",
        })
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, Transaction.DoesNotExist):
        return JsonResponse({"error": "Invalid feedback request."}, status=400)
