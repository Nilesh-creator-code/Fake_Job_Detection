# Fake Job and Internship Detection

An AI-powered URL analysis system that inspects job and internship postings and estimates whether they are legitimate or fraudulent.

Architecture:

`User URL -> Scraper -> Feature Extractor -> Rule Engine -> ML Classifier -> Explanation Engine -> Results Dashboard`

## What it does

- Scrapes a pasted job URL and extracts title, company, salary, contacts, recruiter signals, application links, and metadata.
- Detects fraud indicators such as payment requests, recruiter impersonation, domain mismatch, urgency tactics, remote-job scam language, and exploitative internship patterns.
- Combines expert rules with an interpretable ML-style weighted classifier.
- Produces explainable JSON plus a dashboard-ready decision report.

## Project structure

- [app.py](d:/Working_project/Fake_Job_Detection/app.py): entry point for the local server.
- [fake_job_detector/pipeline.py](d:/Working_project/Fake_Job_Detection/fake_job_detector/pipeline.py): end-to-end analysis flow.
- [fake_job_detector/scraper.py](d:/Working_project/Fake_Job_Detection/fake_job_detector/scraper.py): URL scraping and extraction.
- [fake_job_detector/features.py](d:/Working_project/Fake_Job_Detection/fake_job_detector/features.py): fraud signal extraction.
- [fake_job_detector/rules.py](d:/Working_project/Fake_Job_Detection/fake_job_detector/rules.py): expert rule engine.
- [fake_job_detector/classifier.py](d:/Working_project/Fake_Job_Detection/fake_job_detector/classifier.py): interpretable classifier and calibrated fake probability.
- [fake_job_detector/explain.py](d:/Working_project/Fake_Job_Detection/fake_job_detector/explain.py): human-readable explainability output.
- [static/index.html](d:/Working_project/Fake_Job_Detection/static/index.html): dashboard UI.

## API

Start the app:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:8000
```

Analyze a URL:

```http
POST /api/analyze
Content-Type: application/json

{
  "url": "https://example.com/jobs/data-analyst-intern"
}
```

Example output shape:

```json
{
  "overall_risk_score": 73.4,
  "risk_meter": "High",
  "fake_percentage": 78.2,
  "confidence_score": 84.1,
  "model_prediction": {
    "label": "High Probability Scam",
    "category": "advance_fee_scam"
  },
  "dashboard": {
    "recommendation": "Avoid / Likely Scam",
    "red_flags_checklist": [
      "training fee",
      "work from home",
      "Recruiter used free email domains."
    ]
  }
}
```

## Fraud scoring logic

- Rule engine:
  High-risk rules add large penalties for payment requests, spoofed recruiter identities, phishing-style domains, and exploitative internship language.
- ML classifier:
  A transparent weighted feature model converts extracted signals into fake probability and confidence.
- Fusion:
  `overall_risk = 0.45 * rule_score + 0.55 * fake_probability`
- Recommendation:
  `Legitimate -> Safe to Apply`
  `Suspicious -> Verify Before Applying`
  `Likely Fake / High Probability Scam -> Avoid / Likely Scam`

## Suggested datasets and models

- `Real or Fake Job Posting Prediction (EMSCAD / Kaggle)` for baseline supervised job scam detection.
- `Phishing URL / domain reputation datasets` for malicious infrastructure signals.
- `Enron or enterprise email corpora` for recruiter communication baselines.
- `O*NET / ESCO` for expected salary and role realism features.

Recommended production model path:

1. Start with calibrated Logistic Regression on tabular + text-derived features.
2. Add SHAP-backed Explainable Boosting or XGBoost if you need more recall.
3. Keep rule-based overrides for high-severity scams such as upfront-fee requests.

## Notes

- The current implementation prioritizes interpretability over black-box accuracy.
- Domain age and WHOIS enrichment are left as extension points because they depend on external services or registries.
- Tests cover the core scoring and explanation pipeline in [tests/test_pipeline.py](d:/Working_project/Fake_Job_Detection/tests/test_pipeline.py).
