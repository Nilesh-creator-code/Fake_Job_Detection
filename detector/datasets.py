from __future__ import annotations


def get_dataset_recommendations() -> dict:
    return {
        "public_datasets": [
            {
                "name": "Real or Fake Job Posting Prediction",
                "source": "Kaggle / EMSCAD",
                "use": "Baseline supervised training for fake-vs-real job posts.",
            },
            {
                "name": "Phishing URL / Domain Reputation Datasets",
                "source": "UCI, Kaggle, PhishTank-derived corpora",
                "use": "Domain and URL risk enrichment for recruiter/application links.",
            },
            {
                "name": "Enron Email / enterprise email corpora",
                "source": "CMU Enron Dataset",
                "use": "Normal recruiter and corporate email language baselines.",
            },
            {
                "name": "O*NET / ESCO occupation data",
                "source": "Official labor taxonomies",
                "use": "Expected salary ranges, role norms, and qualification consistency checks.",
            },
        ],
        "recommended_features": [
            "URL and domain age, TLD risk, subdomain depth, HTTPS, redirect count",
            "Recruiter email domain match, free-email usage, contact completeness",
            "Salary anomaly score normalized by role and location",
            "Upfront-fee and payment language features",
            "Urgency, scarcity, and messaging-app contact patterns",
            "Posting text genericity, duplication, grammar quality, benefit realism",
            "Internship exploitation features: unpaid/full-time/vague deliverables",
            "Application destination mismatch and off-platform submission requests",
        ],
        "recommended_models": [
            "Logistic Regression with calibrated probabilities for the first production model",
            "Explainable Gradient Boosting or XGBoost with SHAP for richer tabular signals",
            "Linear SVM or Naive Bayes as simple baselines for text-heavy features",
        ],
        "scoring_logic": {
            "rule_engine": "0-100 additive expert score from high-, medium-, and low-risk indicators.",
            "ml_score": "Calibrated fake probability from interpretable feature weights or a trained logistic model.",
            "fusion": "overall_risk = 0.45 * rule_score + 0.55 * fake_probability, then clipped to 0-100.",
            "confidence": "Blend probability margin, rule agreement, and feature coverage.",
        },
    }
