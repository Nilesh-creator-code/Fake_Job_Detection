from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .models import ContactDetails, DomainInfo, RecruiterDetails, ScrapedJobPosting

FREE_EMAIL_PROVIDERS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
}

SUSPICIOUS_TLDS = {
    "xyz",
    "top",
    "click",
    "live",
    "work",
    "shop",
    "info",
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def _extract_json_ld(soup: BeautifulSoup) -> dict:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            if isinstance(item, dict) and item.get("@type") in {"JobPosting", "Internship"}:
                return item
    return {}


def _extract_emails(text: str) -> list[str]:
    return sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)))


def _extract_phones(text: str) -> list[str]:
    pattern = r"(\+?\d[\d\s().-]{7,}\d)"
    return sorted(set(match.strip() for match in re.findall(pattern, text)))


def _extract_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    links = []
    for tag in soup.select("a[href]"):
        href = tag.get("href", "").strip()
        if not href:
            continue
        absolute = urljoin(base_url, href)
        if absolute.startswith(("http://", "https://")):
            links.append(absolute)
    return sorted(set(links))


def _extract_requirements(text: str) -> str:
    match = re.search(
        r"(requirements|qualifications|what you need|eligibility)\s*:?(.{0,1500})",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    return _normalize_text(match.group(2)) if match else ""


def _extract_company_name(soup: BeautifulSoup, json_ld: dict, hostname: str) -> str:
    company = json_ld.get("hiringOrganization", {})
    if isinstance(company, dict) and company.get("name"):
        return _normalize_text(company["name"])

    selectors = [
        '[data-testid*="company"]',
        '[class*="company"]',
        '[id*="company"]',
        'meta[property="og:site_name"]',
    ]
    for selector in selectors:
        found = soup.select_one(selector)
        if found:
            content = found.get("content") if found.name == "meta" else found.get_text(" ", strip=True)
            if content:
                return _normalize_text(content)
    return hostname.split(".")[0].replace("-", " ").title()


def _extract_title(soup: BeautifulSoup, json_ld: dict) -> str:
    if json_ld.get("title"):
        return _normalize_text(json_ld["title"])
    for selector in ["h1", 'meta[property="og:title"]', "title"]:
        found = soup.select_one(selector)
        if found:
            content = found.get("content") if found.name == "meta" else found.get_text(" ", strip=True)
            if content:
                return _normalize_text(content)
    return "Unknown role"


def _extract_salary(text: str, json_ld: dict) -> str:
    salary = json_ld.get("baseSalary")
    if isinstance(salary, dict):
        value = salary.get("value")
        if isinstance(value, dict):
            minimum = value.get("minValue")
            maximum = value.get("maxValue")
            currency = value.get("currency", "")
            if minimum or maximum:
                return f"{currency} {minimum or ''}-{maximum or ''}".strip()
    match = re.search(
        r"([$€£]\s?\d[\d,]*(?:\.\d+)?(?:\s?[-to]{1,3}\s?[$€£]?\d[\d,]*(?:\.\d+)?)?(?:\s?(?:per|/)\s?(?:hour|month|year|week))?)",
        text,
        re.IGNORECASE,
    )
    return _normalize_text(match.group(1)) if match else ""


def _extract_recruiter_names(text: str) -> list[str]:
    names = set()
    patterns = [
        r"(?:recruiter|hiring manager|talent partner)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        r"(?:contact|reach out to)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text):
            names.add(match.strip())
    return sorted(names)


def _extract_domain_info(url: str, company_name: str) -> DomainInfo:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    parts = hostname.split(".")
    root_domain = ".".join(parts[-2:]) if len(parts) >= 2 else hostname
    tld = parts[-1] if parts else ""
    brand_token = re.sub(r"[^a-z0-9]", "", company_name.lower())
    domain_token = re.sub(r"[^a-z0-9]", "", parts[-2].lower()) if len(parts) >= 2 else hostname.lower()
    looks_like_corporate_domain = domain_token in brand_token or brand_token in domain_token if brand_token else False
    return DomainInfo(
        url=url,
        hostname=hostname,
        root_domain=root_domain,
        is_https=parsed.scheme == "https",
        tld=tld,
        subdomain_depth=max(0, len(parts) - 2),
        suspicious_tld=tld in SUSPICIOUS_TLDS,
        looks_like_corporate_domain=looks_like_corporate_domain,
        brand_mismatch=bool(company_name) and not looks_like_corporate_domain,
    )


def _detect_spoofed_recruiter_emails(emails: list[str], domain_info: DomainInfo) -> tuple[int, list[str]]:
    free_count = 0
    spoofed = []
    for email in emails:
        domain = email.split("@")[-1].lower()
        if domain in FREE_EMAIL_PROVIDERS:
            free_count += 1
        elif domain != domain_info.root_domain.lower():
            spoofed.append(email)
    return free_count, spoofed


def scrape_job_posting(url: str, timeout: int = 15) -> ScrapedJobPosting:
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    json_ld = _extract_json_ld(soup)
    body_text = _normalize_text(soup.get_text(" ", strip=True))
    title = _extract_title(soup, json_ld)
    company_name = _extract_company_name(soup, json_ld, urlparse(url).hostname or "")
    domain_info = _extract_domain_info(url, company_name)
    emails = _extract_emails(body_text)
    phones = _extract_phones(body_text)
    recruiter_names = _extract_recruiter_names(body_text)
    recruiter_emails = [email for email in emails if any(token in body_text.lower() for token in ["recruit", "talent", "hiring"])]
    free_email_count, spoofed_domain_emails = _detect_spoofed_recruiter_emails(emails, domain_info)
    requirements = _extract_requirements(body_text)
    salary_text = _extract_salary(body_text, json_ld)

    return ScrapedJobPosting(
        source_url=url,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        title=title,
        company_name=company_name,
        salary_text=salary_text,
        contact_details=ContactDetails(
            emails=emails,
            phones=phones,
            addresses=[],
        ),
        application_links=_extract_links(soup, url),
        domain_info=domain_info,
        recruiter_details=RecruiterDetails(
            names=recruiter_names,
            emails=recruiter_emails,
            free_email_count=free_email_count,
            spoofed_domain_emails=spoofed_domain_emails,
        ),
        job_description=body_text[:6000],
        requirements=requirements[:2000],
        metadata={
            "page_title": soup.title.get_text(strip=True) if soup.title else "",
            "meta_description": (
                soup.find("meta", attrs={"name": "description"}).get("content", "")
                if soup.find("meta", attrs={"name": "description"})
                else ""
            ),
            "json_ld_present": bool(json_ld),
            "content_length": len(body_text),
        },
        raw_text=body_text,
    )
