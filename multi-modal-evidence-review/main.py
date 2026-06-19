"""CLI entry point for multi-modal evidence review."""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from src.config import DATASET_DIR, OUTPUT_PATH
from src.schema import OUTPUT_COLUMNS
from src.claim_reviewer import ClaimReviewer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def process_claims(
    input_file: str = "claims.csv",
    output_path: Path = OUTPUT_PATH,
    dataset_dir: Path = DATASET_DIR,
    mock_mode: bool = False,
    limit: int | None = None,
) -> pd.DataFrame:
    reviewer = ClaimReviewer(str(dataset_dir), mock_mode=mock_mode)
    claims_path = dataset_dir / input_file
    df = pd.read_csv(claims_path)

    if limit:
        df = df.head(limit)

    results = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing claims"):
        try:
            result = reviewer.review_claim(row.to_dict())
            results.append(result.to_row())
        except Exception as e:
            logger.error("Failed on user %s: %s", row.get("user_id"), e)
            results.append({
                "user_id": row["user_id"],
                "image_paths": row["image_paths"],
                "user_claim": row["user_claim"],
                "claim_object": row["claim_object"],
                "evidence_standard_met": "false",
                "evidence_standard_met_reason": f"Processing error: {e}",
                "risk_flags": "manual_review_required",
                "issue_type": "unknown",
                "object_part": "unknown",
                "claim_status": "not_enough_information",
                "claim_status_justification": "System could not process this claim.",
                "supporting_image_ids": "none",
                "valid_image": "false",
                "severity": "unknown",
            })

    out_df = pd.DataFrame(results, columns=OUTPUT_COLUMNS)
    out_df.to_csv(output_path, index=False)
    logger.info("Written %d rows to %s", len(out_df), output_path)

    usage = reviewer.get_usage()
    logger.info("Usage: %s", usage)
    return out_df


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Modal Evidence Review System"
    )
    parser.add_argument(
        "--input", default="claims.csv", help="Input CSV filename in dataset/"
    )
    parser.add_argument(
        "--output", default=str(OUTPUT_PATH), help="Output CSV path"
    )
    parser.add_argument(
        "--dataset-dir", default=str(DATASET_DIR), help="Dataset directory"
    )
    parser.add_argument(
        "--mock", action="store_true", help="Run without OpenAI API (mock mode)"
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit rows")
    args = parser.parse_args()

    process_claims(
        input_file=args.input,
        output_path=Path(args.output),
        dataset_dir=Path(args.dataset_dir),
        mock_mode=args.mock,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
