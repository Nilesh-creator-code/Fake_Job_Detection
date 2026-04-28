from __future__ import annotations

import math

from .models import Feature, ModelPrediction


LABELS = ["Legitimate", "Suspicious", "Likely Fake", "High Probability Scam"]


def _sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def classify_posting(features: dict, signals: list[Feature], rule_score: float) -> ModelPrediction:
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

    weighted_sum += rule_score * 0.8
    weighted_sum -= features["trust_signal_count"] * 6
    weighted_sum -= features["https"] * 2
    normalized = max(-20.0, min(120.0, weighted_sum / 10))
    fake_probability = _sigmoid((normalized - 3.8) / 1.35) * 100
    confidence = min(99.0, 52 + abs(fake_probability - 50) * 0.8 + min(20, abs(rule_score - 25) * 0.3))

    if fake_probability < 25:
        label = LABELS[0]
    elif fake_probability < 50:
        label = LABELS[1]
    elif fake_probability < 75:
        label = LABELS[2]
    else:
        label = LABELS[3]

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
