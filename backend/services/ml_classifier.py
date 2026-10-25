"""Optional local SMS spam classifier; rule-based analysis remains available without it."""
from functools import lru_cache
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "sms_spam_model.joblib"


@lru_cache(maxsize=1)
def _load_artifact():
    if not MODEL_PATH.is_file():
        return None
    try:
        import joblib
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def is_available():
    return _load_artifact() is not None


def classify_spam_like(message):
    """Return a conservative label, never a user-facing probability."""
    artifact = _load_artifact()
    if not artifact or not artifact.get("threshold_found"):
        return None
    model = artifact["model"]
    spam_index = list(model.classes_).index("spam")
    calibrated_score = float(model.predict_proba([message])[0][spam_index])
    return {
        "is_spam_like": calibrated_score >= artifact["decision_threshold"],
        "model_version": artifact["model_version"],
    }
