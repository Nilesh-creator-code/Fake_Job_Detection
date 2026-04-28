# Fake Job and Internship Detection

An AI-powered URL analysis system that inspects job and internship postings and estimates whether they are legitimate or fraudulent.

Architecture:

`User URL -> Scraper -> Feature Extractor -> Rule Engine -> ML Classifier -> Explanation Engine -> Results Dashboard`

## Upgraded project structure

```text
fake-job-detector/
|
|- scraper/
|  |- scrape_jobs.py
|
|- detector/
|  |- rules.py
|  |- suspicious_keywords.py
|  |- features.py
|  |- explain.py
|  |- pipeline.py
|  `- models.py
|
|- ml_model/
|  |- train_model.py
|  |- classifier.py
|  `- model.pkl
|
|- api/
|  `- app.py
|
|- frontend/
|  |- index.html
|  |- app.js
|  `- styles.css
|
`- tests/
   `- test_pipeline.py
```

## What each folder does

- [scraper/scrape_jobs.py](/d:/Working_project/Fake_Job_Detection/scraper/scrape_jobs.py): fetches a pasted URL and extracts job content, recruiter signals, domain data, and metadata.
- [detector/rules.py](/d:/Working_project/Fake_Job_Detection/detector/rules.py): applies expert fraud rules and creates risk flags.
- [detector/suspicious_keywords.py](/d:/Working_project/Fake_Job_Detection/detector/suspicious_keywords.py): central keyword lists for payment scams, urgency, phishing-style recruiting, and exploitative internships.
- [ml_model/train_model.py](/d:/Working_project/Fake_Job_Detection/ml_model/train_model.py): generates the serialized model artifact.
- [ml_model/classifier.py](/d:/Working_project/Fake_Job_Detection/ml_model/classifier.py): loads `model.pkl` and produces fake probability, confidence, and class labels.
- [api/app.py](/d:/Working_project/Fake_Job_Detection/api/app.py): serves the API and the dashboard.
- [frontend/index.html](/d:/Working_project/Fake_Job_Detection/frontend/index.html): dashboard UI.

## Running the project

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Generate the model artifact:

```bash
python ml_model/train_model.py
```

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

## Fraud scoring logic

- Rule engine: high-risk rules add strong penalties for applicant payment requests, spoofed recruiter identities, phishing-style domains, and exploitative internship language.
- ML classifier: a transparent weighted model stored in `ml_model/model.pkl` converts extracted signals into fake probability and confidence.
- Fusion: `overall_risk = 0.45 * rule_score + 0.55 * fake_probability`
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

1. Start with calibrated Logistic Regression on tabular and text-derived features.
2. Add SHAP-backed Explainable Boosting or XGBoost if you need more recall.
3. Keep rule-based overrides for high-severity scams such as upfront-fee requests.

## Compatibility note

- The old `fake_job_detector/` package is still present as a compatibility layer, but the new canonical structure is `scraper/`, `detector/`, `ml_model/`, `api/`, and `frontend/`.
