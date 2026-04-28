from __future__ import annotations

import re
from collections import Counter

from .models import Feature, ScrapedJobPosting
from .suspicious_keywords import (
    EXPLOITATION_TERMS,
    REMOTE_SCAM_TERMS,
    TRUST_TERMS,
    UPFRONT_PAYMENT_TERMS,
    URGENCY_TERMS,
)


def _count_terms(text: str, terms: set[str]) -> tuple[int, list[str]]:
    hits = [term for term in terms if term in text]
    return len(hits), sorted(hits)


def _salary_value(salary_text: str) -> float:
    nums = [float(token.replace(",", "")) for token in re.findall(r"\d[\d,]*(?:\.\d+)?", salary_text)]
    return max(nums) if nums else 0.0


def _grammar_error_ratio(text: str) -> float:
    words = re.findall(r"[A-Za-z']+", text)
    if not words:
        return 0.0
    suspicious = sum(1 for word in words if len(word) > 12 and not re.search(r"[aeiou]", word.lower()))
    repeated_punct = len(re.findall(r"[!?]{2,}", text))
    return min(1.0, (suspicious + repeated_punct) / max(10, len(words) / 20))


def _genericity_score(text: str) -> float:
    words = re.findall(r"[A-Za-z]{3,}", text.lower())
    if not words:
        return 0.0
    counts = Counter(words)
    top_repeat = counts.most_common(10)
    repetition = sum(count for _, count in top_repeat) / len(words)
    unique_ratio = len(counts) / len(words)
    return max(0.0, min(1.0, repetition * 0.7 + (1 - unique_ratio) * 0.3))


def extract_features(posting: ScrapedJobPosting) -> tuple[dict, list[Feature]]:
    text = posting.raw_text.lower()
    source_url = posting.source_url.lower()
    salary_max = _salary_value(posting.salary_text)
    payment_count, payment_hits = _count_terms(text, UPFRONT_PAYMENT_TERMS)
    urgency_count, urgency_hits = _count_terms(text, URGENCY_TERMS)
    remote_count, remote_hits = _count_terms(text, REMOTE_SCAM_TERMS)
    exploitation_count, exploitation_hits = _count_terms(text, EXPLOITATION_TERMS)
    trust_count, trust_hits = _count_terms(text, TRUST_TERMS)
    grammar_ratio = _grammar_error_ratio(posting.raw_text)
    genericity = _genericity_score(posting.job_description)
    missing_company = int(not posting.company_name or posting.company_name.lower() in {"company", "confidential"})
    missing_requirements = int(len(posting.requirements) < 40)
    external_apply_ratio = 0.0
    if posting.application_links:
        external = 0
        for link in posting.application_links:
            if posting.domain_info.root_domain not in link:
                external += 1
        external_apply_ratio = external / len(posting.application_links)

    unrealistic_salary = int(salary_max >= 250000 or ("intern" in posting.title.lower() and salary_max >= 80000))
    internship_role = int("intern" in posting.title.lower() or "internship" in text)
    official_careers_host = int(
        posting.domain_info.is_https
        and not posting.domain_info.suspicious_tld
        and any(
            token in source_url
            for token in (
                "/careers",
                "/jobs",
                "greenhouse.io",
                "lever.co",
                "workdayjobs",
                "myworkdayjobs",
            )
        )
    )
    corporate_trust_alignment = int(
        posting.domain_info.looks_like_corporate_domain
        and posting.domain_info.is_https
        and not posting.domain_info.suspicious_tld
    )
    policy_signal = int(
        any(
            term in text
            for term in (
                "equal opportunity employer",
                "applicant and candidate privacy policy",
                "privacy policy",
                "how we hire",
            )
        )
    )
    feature_dict = {
        "suspicious_tld": int(posting.domain_info.suspicious_tld),
        "brand_mismatch": int(posting.domain_info.brand_mismatch),
        "free_email_count": posting.recruiter_details.free_email_count,
        "spoofed_email_count": len(posting.recruiter_details.spoofed_domain_emails),
        "upfront_payment_count": payment_count,
        "urgency_count": urgency_count,
        "remote_scam_count": remote_count,
        "internship_exploitation_count": exploitation_count,
        "trust_signal_count": trust_count,
        "grammar_error_ratio": round(grammar_ratio, 3),
        "genericity_score": round(genericity, 3),
        "missing_company": missing_company,
        "missing_requirements": missing_requirements,
        "external_apply_ratio": round(external_apply_ratio, 3),
        "unrealistic_salary": unrealistic_salary,
        "salary_max": salary_max,
        "internship_role": internship_role,
        "https": int(posting.domain_info.is_https),
        "subdomain_depth": posting.domain_info.subdomain_depth,
        "content_length": posting.metadata.get("content_length", 0),
        "official_careers_host": official_careers_host,
        "corporate_trust_alignment": corporate_trust_alignment,
        "policy_signal": policy_signal,
    }

    signals = [
        Feature("payment_requests", payment_count, 18.0, ", ".join(payment_hits) or "No payment requests found."),
        Feature("urgent_pressure", urgency_count, 9.0, ", ".join(urgency_hits) or "No urgency language found."),
        Feature("remote_scam_terms", remote_count, 10.0, ", ".join(remote_hits) or "No common remote scam terms found."),
        Feature("internship_exploitation", exploitation_count, 12.0, ", ".join(exploitation_hits) or "No exploitation phrases found."),
        Feature("free_email_accounts", posting.recruiter_details.free_email_count, 11.0, "Recruiter used free email domains."),
        Feature("spoofed_email_domains", len(posting.recruiter_details.spoofed_domain_emails), 15.0, ", ".join(posting.recruiter_details.spoofed_domain_emails) or "No spoofed email domains found."),
        Feature("brand_mismatch", feature_dict["brand_mismatch"], 14.0, f"Company '{posting.company_name}' vs domain '{posting.domain_info.root_domain}'."),
        Feature("unrealistic_salary", unrealistic_salary, 8.0, posting.salary_text or "No salary extracted."),
        Feature("missing_company_info", missing_company, 12.0, "Company identity missing or overly generic."),
        Feature("grammar_spelling_flags", round(grammar_ratio, 3), 10.0, f"Estimated grammar anomaly ratio: {grammar_ratio:.2f}."),
        Feature("generic_description", round(genericity, 3), 12.0, f"Genericity score: {genericity:.2f}."),
        Feature("trust_signals", trust_count, -7.0, ", ".join(trust_hits) or "Few explicit trust signals found."),
        Feature("external_application_links", round(external_apply_ratio, 3), 8.0, f"External application ratio: {external_apply_ratio:.2f}."),
        Feature("official_careers_host", official_careers_host, -12.0, "Posting is on an HTTPS careers/jobs host."),
        Feature("corporate_trust_alignment", corporate_trust_alignment, -10.0, "Domain and company identity align cleanly."),
        Feature("policy_signal", policy_signal, -8.0, "Applicant privacy or hiring policy language is present."),
    ]
    return feature_dict, signals
