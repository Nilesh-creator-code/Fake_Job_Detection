from __future__ import annotations

import pickle
from pathlib import Path

MODEL_PATH = Path(__file__).with_name("model.pkl")

DEFAULT_MODEL = {
    "name": "interpretable_weighted_job_scam_model",
    "version": "1.0",
    "labels": ["Legitimate", "Suspicious", "Likely Fake", "High Probability Scam"],
    "signal_adjustments": {
        "trust_signal_penalty": 3.5,
        "https_penalty": 1.5,
        "rule_score_multiplier": 0.72,
        "official_careers_bonus": 10.0,
        "corporate_alignment_bonus": 8.0,
        "policy_signal_bonus": 6.0,
    },
    "sigmoid_center": 4.2,
    "sigmoid_scale": 1.5,
}


def train_and_save_model() -> Path:
    with MODEL_PATH.open("wb") as model_file:
        pickle.dump(DEFAULT_MODEL, model_file, protocol=4)
    return MODEL_PATH


if __name__ == "__main__":
    path = train_and_save_model()
    print(f"Model saved to {path}")
