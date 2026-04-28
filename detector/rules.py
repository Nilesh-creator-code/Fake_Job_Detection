from __future__ import annotations

from .models import RuleFlag


def apply_rules(features: dict) -> tuple[list[RuleFlag], float]:
    flags: list[RuleFlag] = []

    def add(rule_id: str, severity: str, score: float, message: str, evidence: str, category: str) -> None:
        flags.append(
            RuleFlag(
                rule_id=rule_id,
                severity=severity,
                score=score,
                message=message,
                evidence=evidence,
                category=category,
            )
        )

    if features["upfront_payment_count"] > 0:
        add(
            "RULE-PAYMENT-001",
            "high",
            28,
            "The posting requests money from applicants.",
            f"Detected {features['upfront_payment_count']} fee-related phrases.",
            "advance_fee_scam",
        )
    if features["spoofed_email_count"] > 0:
        add(
            "RULE-EMAIL-002",
            "high",
            22,
            "Recruiter email domain does not match the hiring domain.",
            f"Spoofed email count: {features['spoofed_email_count']}.",
            "identity_spoofing",
        )
    if features["free_email_count"] > 0:
        add(
            "RULE-EMAIL-003",
            "medium",
            12,
            "Recruiter uses free email providers instead of a company domain.",
            f"Free email count: {features['free_email_count']}.",
            "recruiter_impersonation",
        )
    if features["suspicious_tld"] == 1 or features["brand_mismatch"] == 1:
        add(
            "RULE-DOMAIN-004",
            "medium",
            15,
            "The job is hosted on a suspicious or mismatched domain.",
            "Suspicious TLD or company/domain mismatch detected.",
            "phishing_infrastructure",
        )
    if features["unrealistic_salary"] == 1:
        add(
            "RULE-SALARY-005",
            "medium",
            11,
            "The compensation appears unusually high for the role.",
            f"Extracted salary value: {features['salary_max']}.",
            "too_good_to_be_true",
        )
    if features["remote_scam_count"] >= 2 and features["urgency_count"] >= 1:
        add(
            "RULE-REMOTE-006",
            "high",
            17,
            "The post mixes remote-work bait with pressure tactics.",
            (
                f"Remote scam count: {features['remote_scam_count']}, "
                f"urgency count: {features['urgency_count']}."
            ),
            "remote_recruitment_scam",
        )
    if features["internship_role"] == 1 and features["internship_exploitation_count"] > 0:
        add(
            "RULE-INTERN-007",
            "high",
            18,
            "The internship language suggests exploitative unpaid labor.",
            f"Exploitation signal count: {features['internship_exploitation_count']}.",
            "internship_exploitation",
        )
    if features["missing_company"] == 1 and features["genericity_score"] >= 0.45:
        add(
            "RULE-CONTENT-008",
            "medium",
            13,
            "The posting lacks clear company identity and reads generically.",
            (
                f"Missing company: {features['missing_company']}, "
                f"genericity score: {features['genericity_score']}."
            ),
            "content_farm_posting",
        )
    if features["trust_signal_count"] >= 2 and features["free_email_count"] == 0 and features["spoofed_email_count"] == 0:
        add(
            "RULE-TRUST-009",
            "low",
            -10,
            "The posting shows several trust signals.",
            f"Trust signal count: {features['trust_signal_count']}.",
            "trust_signal",
        )
    if features["official_careers_host"] == 1 and features["corporate_trust_alignment"] == 1:
        add(
            "RULE-TRUST-010",
            "low",
            -12,
            "The posting appears on an official corporate careers surface.",
            "HTTPS careers host and company-domain alignment both look legitimate.",
            "official_careers_surface",
        )

    total = max(0.0, min(100.0, sum(flag.score for flag in flags) + (5 if not flags else 0)))
    return flags, round(total, 2)
