from __future__ import annotations

from .classifier import classify_posting
from .datasets import get_dataset_recommendations
from .explain import build_explanation
from .features import extract_features
from .models import AnalysisResult
from .rules import apply_rules
from .scraper import scrape_job_posting


def _risk_meter(score: float) -> str:
    if score < 25:
        return "Low"
    if score < 50:
        return "Medium"
    if score < 75:
        return "High"
    return "Critical"


def analyze_job_url(url: str) -> AnalysisResult:
    posting = scrape_job_posting(url)
    features, feature_signals = extract_features(posting)
    rule_flags, rule_score = apply_rules(features)
    prediction = classify_posting(features, feature_signals, rule_score)
    overall_risk_score = round(min(100.0, max(0.0, 0.45 * rule_score + 0.55 * prediction.fake_probability)), 2)
    explanation = build_explanation(posting, features, feature_signals, rule_flags, prediction, overall_risk_score)
    risk_meter = _risk_meter(overall_risk_score)

    dashboard = {
        "title": posting.title,
        "company": posting.company_name,
        "risk_score": overall_risk_score,
        "how_fake_percentage": prediction.fake_probability,
        "risk_meter": risk_meter,
        "classification": prediction.label,
        "recommendation": explanation.recommendation,
        "fraud_pattern_category": prediction.category,
        "red_flags_checklist": explanation.red_flags,
        "trust_signals": explanation.trust_signals,
        "explainability_report": {
            "summary": explanation.summary,
            "rule_matches": explanation.triggered_rules,
            "feature_triggers": explanation.triggered_features,
            "model_reasoning": explanation.model_reasoning,
        },
    }

    return AnalysisResult(
        input_url=url,
        posting=posting,
        features=features,
        feature_signals=feature_signals,
        rule_flags=rule_flags,
        rule_score=rule_score,
        model_prediction=prediction,
        overall_risk_score=overall_risk_score,
        risk_meter=risk_meter,
        fake_percentage=prediction.fake_probability,
        confidence_score=prediction.confidence,
        explanation=explanation,
        dashboard=dashboard,
        implementation_notes=get_dataset_recommendations(),
    )
