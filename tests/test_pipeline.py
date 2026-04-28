from detector.explain import build_explanation
from detector.features import extract_features
from detector.models import ContactDetails, DomainInfo, RecruiterDetails, ScrapedJobPosting
from detector.rules import apply_rules
from ml_model.classifier import classify_posting


def build_posting(text: str, title: str = "Marketing Intern") -> ScrapedJobPosting:
    return ScrapedJobPosting(
        source_url="https://jobs-brand-careers.xyz/open-role",
        fetched_at="2026-04-27T00:00:00+00:00",
        title=title,
        company_name="Brand Labs",
        salary_text="$120000 per year",
        contact_details=ContactDetails(emails=["hr.brandlabs@gmail.com"], phones=[], addresses=[]),
        application_links=["https://telegram.example/apply"],
        domain_info=DomainInfo(
            url="https://jobs-brand-careers.xyz/open-role",
            hostname="jobs-brand-careers.xyz",
            root_domain="brand-careers.xyz",
            is_https=True,
            tld="xyz",
            subdomain_depth=1,
            suspicious_tld=True,
            looks_like_corporate_domain=False,
            brand_mismatch=True,
        ),
        recruiter_details=RecruiterDetails(
            names=["Alex Brown"],
            emails=["hr.brandlabs@gmail.com"],
            free_email_count=1,
            spoofed_domain_emails=[],
        ),
        job_description=text,
        requirements="No experience required",
        metadata={"content_length": len(text)},
        raw_text=text,
    )


def test_scam_signals_raise_risk():
    text = (
        "Urgent hiring work from home internship. "
        "Pay registration fee and security deposit today. "
        "No experience needed. Join immediately."
    )
    posting = build_posting(text)
    features, signals = extract_features(posting)
    rules, rule_score = apply_rules(features)
    prediction = classify_posting(features, signals, rule_score)

    assert rule_score >= 40
    assert prediction.fake_probability >= 60
    assert prediction.label in {"Likely Fake", "High Probability Scam"}
    assert any(rule.category == "advance_fee_scam" for rule in rules)


def test_explanation_contains_recommendation():
    text = "Equal opportunity employer with benefits and official careers page."
    posting = build_posting(text, title="Software Engineer")
    features, signals = extract_features(posting)
    rules, rule_score = apply_rules(features)
    prediction = classify_posting(features, signals, rule_score)
    explanation = build_explanation(posting, features, signals, rules, prediction, 25)

    assert explanation.recommendation in {
        "Safe to Apply",
        "Verify Before Applying",
        "Avoid / Likely Scam",
    }
    assert explanation.summary
