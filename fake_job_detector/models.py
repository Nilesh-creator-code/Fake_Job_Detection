from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ContactDetails:
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    addresses: list[str] = field(default_factory=list)


@dataclass
class DomainInfo:
    url: str
    hostname: str
    root_domain: str
    is_https: bool
    tld: str
    subdomain_depth: int
    suspicious_tld: bool
    looks_like_corporate_domain: bool
    brand_mismatch: bool
    age_days: int | None = None
    age_available: bool = False


@dataclass
class RecruiterDetails:
    names: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    free_email_count: int = 0
    spoofed_domain_emails: list[str] = field(default_factory=list)


@dataclass
class ScrapedJobPosting:
    source_url: str
    fetched_at: str
    title: str
    company_name: str
    salary_text: str
    contact_details: ContactDetails
    application_links: list[str]
    domain_info: DomainInfo
    recruiter_details: RecruiterDetails
    job_description: str
    requirements: str
    metadata: dict[str, Any]
    raw_text: str


@dataclass
class Feature:
    name: str
    value: Any
    weight: float
    evidence: str


@dataclass
class RuleFlag:
    rule_id: str
    severity: str
    score: float
    message: str
    evidence: str
    category: str


@dataclass
class ModelPrediction:
    label: str
    fake_probability: float
    confidence: float
    category: str
    class_scores: dict[str, float]
    top_contributors: list[Feature]


@dataclass
class ExplanationReport:
    summary: str
    red_flags: list[str]
    trust_signals: list[str]
    triggered_features: list[str]
    triggered_rules: list[str]
    model_reasoning: list[str]
    recommendation: str


@dataclass
class AnalysisResult:
    input_url: str
    posting: ScrapedJobPosting
    features: dict[str, Any]
    feature_signals: list[Feature]
    rule_flags: list[RuleFlag]
    rule_score: float
    model_prediction: ModelPrediction
    overall_risk_score: float
    risk_meter: str
    fake_percentage: float
    confidence_score: float
    explanation: ExplanationReport
    dashboard: dict[str, Any]
    implementation_notes: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
