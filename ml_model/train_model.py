from __future__ import annotations

import pickle
from pathlib import Path

MODEL_PATH = Path(__file__).with_name("model.pkl")

DEFAULT_MODEL = {
    "name": "interpretable_weighted_job_scam_model",
    "version": "1.0",
    "labels": ["Legitimate", "Suspicious", "Likely Fake", "High Probability Scam"],
    "signal_adjustments": {
        "trust_signal_penalty": 6.0,
        "https_penalty": 2.0,
        "rule_score_multiplier": 0.8,
    },
    "sigmoid_center": 3.8,
    "sigmoid_scale": 1.35,
}


def train_and_save_model() -> Path:
    with MODEL_PATH.open("wb") as model_file:
        pickle.dump(DEFAULT_MODEL, model_file, protocol=4)
    return MODEL_PATH


if __name__ == "__main__":
    path = train_and_save_model()
    print(f"Model saved to {path}")
