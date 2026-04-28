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


def test_official_careers_posting_is_not_scored_like_a_scam():
    text = (
        "Google is proud to be an equal opportunity employer. "
        "Information collected and processed as part of your Google Careers profile "
        "is subject to Google's Applicant and Candidate Privacy Policy. "
        "Minimum qualifications include sales and client relationship experience. "
        "Preferred qualifications include stakeholder management and digital marketing knowledge."
    )
    posting = ScrapedJobPosting(
        source_url="https://www.google.com/about/careers/applications/jobs/results/123-account-executive",
        fetched_at="2026-04-28T00:00:00+00:00",
        title="Account Executive, Google Customer Solutions",
        company_name="Google",
        salary_text="",
        contact_details=ContactDetails(emails=[], phones=[], addresses=[]),
        application_links=["https://careers.google.com/apply/123"],
        domain_info=DomainInfo(
            url="https://www.google.com/about/careers/applications/jobs/results/123-account-executive",
            hostname="www.google.com",
            root_domain="google.com",
            is_https=True,
            tld="com",
            subdomain_depth=1,
            suspicious_tld=False,
            looks_like_corporate_domain=True,
            brand_mismatch=False,
        ),
        recruiter_details=RecruiterDetails(
            names=[],
            emails=[],
            free_email_count=0,
            spoofed_domain_emails=[],
        ),
        job_description=text,
        requirements="Bachelor's degree and experience in consultative sales.",
        metadata={"content_length": len(text)},
        raw_text=text,
    )
    features, signals = extract_features(posting)
    rules, rule_score = apply_rules(features)
    prediction = classify_posting(features, signals, rule_score)

    assert features["official_careers_host"] == 1
    assert prediction.fake_probability < 45
    assert prediction.label in {"Legitimate", "Suspicious"}
