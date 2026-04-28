from __future__ import annotations

from .models import ExplanationReport, Feature, ModelPrediction, RuleFlag, ScrapedJobPosting

RECOMMENDATION_BY_LABEL = {
    "Legitimate": "Safe to Apply",
    "Suspicious": "Verify Before Applying",
    "Likely Fake": "Avoid / Likely Scam",
    "High Probability Scam": "Avoid / Likely Scam",
}


def build_explanation(
    posting: ScrapedJobPosting,
    features: dict,
    signals: list[Feature],
    rules: list[RuleFlag],
    prediction: ModelPrediction,
    risk_score: float,
) -> ExplanationReport:
    red_flags = []
    trust_signals = []
    triggered_features = []
    triggered_rules = []
    model_reasoning = []

    for signal in signals:
        numeric_value = signal.value if isinstance(signal.value, (int, float)) else 0
        if signal.weight > 0 and numeric_value:
            triggered_features.append(f"{signal.name}: {signal.evidence}")
            red_flags.append(signal.evidence)
        if signal.weight < 0 and numeric_value:
            trust_signals.append(signal.evidence)

    for rule in rules:
        triggered_rules.append(f"{rule.rule_id} [{rule.severity}]: {rule.message}")

    for contributor in prediction.top_contributors:
        direction = "increased" if contributor.weight > 0 else "reduced"
        model_reasoning.append(
            f"{contributor.name} {direction} scam probability because {contributor.evidence}"
        )

    summary = (
        f"The posting for '{posting.title}' at '{posting.company_name}' is classified as "
        f"'{prediction.label}' with a fake probability of {prediction.fake_probability}%. "
        f"The strongest signals came from {prediction.category.replace('_', ' ')} patterns."
    )
    if not red_flags:
        red_flags.append("No strong red flags were triggered by the current rule set.")
    if not trust_signals:
        trust_signals.append("Few explicit trust signals were found, so manual verification is still wise.")

    return ExplanationReport(
        summary=summary,
        red_flags=red_flags[:8],
        trust_signals=trust_signals[:6],
        triggered_features=triggered_features[:10],
        triggered_rules=triggered_rules[:10],
        model_reasoning=model_reasoning[:8],
        recommendation=RECOMMENDATION_BY_LABEL[prediction.label],
    )
