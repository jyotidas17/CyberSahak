"""Train a calibrated, conservative SMS spam signal and report held-out metrics."""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sms_spam_collection.tsv"
MODEL_DIR = ROOT / "models"
MODEL_VERSION = "sms-spam-uci-v1"


def main():
    if not DATA.is_file():
        raise SystemExit("Training data is missing. Run: python scripts/download_sms_dataset.py")
    frame = pd.read_csv(DATA, sep="\t", header=None, names=["label", "message"], quoting=csv_quoting())
    frame = frame.dropna().drop_duplicates(subset=["message"])
    if not set(frame["label"].unique()).issubset({"ham", "spam"}) or len(frame) < 1000:
        raise SystemExit("Training data failed label or size validation.")
    X, y = frame["message"].astype(str), frame["label"].astype(str)
    X_train, X_holdout, y_train, y_holdout = train_test_split(
        X, y, test_size=0.40, random_state=42, stratify=y
    )
    X_cal, X_test, y_cal, y_test = train_test_split(
        X_holdout, y_holdout, test_size=0.50, random_state=43, stratify=y_holdout
    )
    base = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=100_000,
                                  strip_accents="unicode", sublinear_tf=True)),
        ("classifier", LogisticRegression(max_iter=1500, random_state=42)),
    ])
    model = CalibratedClassifierCV(estimator=base, method="sigmoid", cv=5)
    model.fit(X_train, y_train)
    spam_index = list(model.classes_).index("spam")
    calibration_scores = model.predict_proba(X_cal)[:, spam_index]
    thresholds = np.linspace(0.50, 0.99, 100)
    candidates = []
    for threshold in thresholds:
        prediction = calibration_scores >= threshold
        precision = precision_score(y_cal == "spam", prediction, zero_division=0)
        recall = recall_score(y_cal == "spam", prediction, zero_division=0)
        if precision >= 0.90 and prediction.sum() >= 5:
            candidates.append((recall, float(threshold), float(precision)))
    threshold_found = bool(candidates)
    if candidates:
        recall_at_threshold, threshold, validation_precision = max(candidates, key=lambda row: row[0])
    else:
        threshold, validation_precision, recall_at_threshold = 1.0, 0.0, 0.0

    test_scores = model.predict_proba(X_test)[:, spam_index]
    y_pred = test_scores >= threshold
    y_true = y_test == "spam"
    report = {
        "dataset": "UCI SMS Spam Collection (CC BY 4.0)",
        "model_version": MODEL_VERSION,
        "rows_after_deduplication": int(len(frame)),
        "split": {"train": int(len(X_train)), "threshold_selection": int(len(X_cal)), "test": int(len(X_test))},
        "threshold_selection_precision_floor": 0.90,
        "decision_threshold": threshold,
        "threshold_found": threshold_found,
        "validation_precision_at_threshold": validation_precision,
        "validation_recall_at_threshold": recall_at_threshold,
        "test": {
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "confusion_matrix_labels_ham_spam": confusion_matrix(y_test, np.where(y_pred, "spam", "ham"), labels=["ham", "spam"]).tolist(),
        },
        "limitations": "General SMS spam data, not India-specific phishing labels; signal is supplementary and does not establish fraud.",
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "decision_threshold": threshold,
                 "threshold_found": threshold_found, "model_version": MODEL_VERSION},
                MODEL_DIR / "sms_spam_model.joblib")
    (MODEL_DIR / "sms_spam_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


def csv_quoting():
    import csv
    return csv.QUOTE_MINIMAL


if __name__ == "__main__":
    main()
