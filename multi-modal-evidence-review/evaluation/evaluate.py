"""Evaluate system against labeled sample claims."""

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from src.config import DATASET_DIR, PROJECT_ROOT
from src.schema import OUTPUT_COLUMNS
from main import process_claims

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KEY_FIELDS = [
    "claim_status",
    "issue_type",
    "object_part",
    "evidence_standard_met",
    "valid_image",
    "severity",
]


def evaluate(
    dataset_dir: Path = DATASET_DIR,
    mock_mode: bool = False,
    output_dir: Path = PROJECT_ROOT / "evaluation",
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    sample_output = output_dir / "sample_predictions.csv"

    process_claims(
        input_file="sample_claims.csv",
        output_path=sample_output,
        dataset_dir=dataset_dir,
        mock_mode=mock_mode,
    )

    sample_df = pd.read_csv(dataset_dir / "sample_claims.csv")
    pred_df = pd.read_csv(sample_output)

    # Align by user_id + image_paths if possible
    if "user_id" in sample_df.columns:
        merge_keys = ["user_id", "image_paths"]
    else:
        merge_keys = list(range(min(len(sample_df), len(pred_df))))

    metrics = {"total": len(pred_df), "field_accuracy": {}}

    for field in KEY_FIELDS:
        if field not in sample_df.columns:
            continue
        if field in ("evidence_standard_met", "valid_image"):
            expected = sample_df[field].astype(str).str.lower()
            predicted = pred_df[field].astype(str).str.lower()
        else:
            expected = sample_df[field].astype(str)
            predicted = pred_df[field].astype(str)

        correct = (expected.values == predicted.values).sum()
        metrics["field_accuracy"][field] = {
            "correct": int(correct),
            "total": len(expected),
            "accuracy": round(correct / len(expected), 4) if len(expected) else 0,
        }

    if "claim_status" in sample_df.columns:
        status_match = (
            sample_df["claim_status"].astype(str).values
            == pred_df["claim_status"].astype(str).values
        ).sum()
        metrics["claim_status_accuracy"] = round(status_match / len(sample_df), 4)

    results_path = output_dir / "eval_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.info("Evaluation results: %s", metrics)
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default=str(DATASET_DIR))
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    evaluate(Path(args.dataset_dir), mock_mode=args.mock)


if __name__ == "__main__":
    main()
