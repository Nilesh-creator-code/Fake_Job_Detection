from __future__ import annotations

import math
import pickle
from pathlib import Path

from detector.models import Feature, ModelPrediction

MODEL_PATH = Path(__file__).with_name("model.pkl")
DEFAULT_MODEL = {
    "labels": ["Legitimate", "Suspicious", "Likely Fake", "High Probability Scam"],
    "signal_adjustments": {
        "trust_signal_penalty": 3.5,
        "https_penalty": 1.5,
        "rule_score_multiplier": 0.72,
        "official_careers_bonus": 10.0,
        "corporate_alignment_bonus": 8.0,
        "policy_signal_bonus": 6.0,
    },
    "sigmoid_center": 4.2,
    "sigmoid_scale": 1.5,
}


def _load_model() -> dict:
    if MODEL_PATH.exists():
        with MODEL_PATH.open("rb") as model_file:
            return pickle.load(model_file)
    return DEFAULT_MODEL


def _sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def classify_posting(features: dict, signals: list[Feature], rule_score: float) -> ModelPrediction:
    model = _load_model()
    labels = model["labels"]
    adjustments = model["signal_adjustments"]

    weighted_sum = 0.0
    contributors: list[Feature] = []
    for signal in signals:
        magnitude = float(signal.value) if isinstance(signal.value, (int, float)) else 0.0
        contribution = signal.weight * magnitude
        weighted_sum += contribution
        if abs(contribution) > 1:
            contributors.append(
                Feature(
                    name=signal.name,
                    value=round(magnitude, 3),
                    weight=round(contribution, 3),
                    evidence=signal.evidence,
                )
            )

    weighted_sum += rule_score * adjustments["rule_score_multiplier"]
    weighted_sum -= features["trust_signal_count"] * adjustments["trust_signal_penalty"]
    weighted_sum -= features["https"] * adjustments["https_penalty"]
    weighted_sum -= features.get("official_careers_host", 0) * adjustments["official_careers_bonus"]
    weighted_sum -= features.get("corporate_trust_alignment", 0) * adjustments["corporate_alignment_bonus"]
    weighted_sum -= features.get("policy_signal", 0) * adjustments["policy_signal_bonus"]
    normalized = max(-20.0, min(120.0, weighted_sum / 10))
    fake_probability = _sigmoid((normalized - model["sigmoid_center"]) / model["sigmoid_scale"]) * 100
    confidence = min(99.0, 52 + abs(fake_probability - 50) * 0.8 + min(20, abs(rule_score - 25) * 0.3))

    if fake_probability < 25:
        label = labels[0]
    elif fake_probability < 50:
        label = labels[1]
    elif fake_probability < 75:
        label = labels[2]
    else:
        label = labels[3]

    category_scores = {
        "advance_fee_scam": features["upfront_payment_count"] * 20 + features["free_email_count"] * 6,
        "phishing_recruitment": features["spoofed_email_count"] * 18 + features["brand_mismatch"] * 14,
        "remote_job_scam": features["remote_scam_count"] * 8 + features["urgency_count"] * 6,
        "internship_exploitation": features["internship_exploitation_count"] * 16 + features["internship_role"] * 4,
        "generic_fraudulent_posting": features["genericity_score"] * 25 + features["missing_company"] * 12,
    }
    top_category = max(category_scores, key=category_scores.get)

    base = fake_probability / 100
    class_scores = {
        "Legitimate": round(max(0.0, 1 - base * 1.3), 3),
        "Suspicious": round(max(0.0, 1 - abs(base - 0.35) * 2.2), 3),
        "Likely Fake": round(max(0.0, 1 - abs(base - 0.65) * 2.2), 3),
        "High Probability Scam": round(max(0.0, base * 1.25 - 0.1), 3),
    }

    top_contributors = sorted(contributors, key=lambda item: abs(item.weight), reverse=True)[:6]

    return ModelPrediction(
        label=label,
        fake_probability=round(fake_probability, 2),
        confidence=round(confidence, 2),
        category=top_category,
        class_scores=class_scores,
        top_contributors=top_contributors,
    )
