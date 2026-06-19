"""Load CSV datasets."""

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.config import DATASET_DIR


class DataLoader:
    def __init__(self, dataset_dir: Path = DATASET_DIR):
        self.dataset_dir = Path(dataset_dir)

    def load_claims(self, filename: str = "claims.csv") -> pd.DataFrame:
        return pd.read_csv(self.dataset_dir / filename)

    def load_user_history(self) -> pd.DataFrame:
        return pd.read_csv(self.dataset_dir / "user_history.csv")

    def load_evidence_requirements(self) -> pd.DataFrame:
        return pd.read_csv(self.dataset_dir / "evidence_requirements.csv")

    def load_sample_claims(self) -> pd.DataFrame:
        return pd.read_csv(self.dataset_dir / "sample_claims.csv")

    def get_user_history(self, user_id: str) -> Optional[Dict]:
        df = self.load_user_history()
        row = df[df["user_id"] == user_id]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def resolve_image_path(self, relative_path: str) -> Path:
        path = Path(relative_path)
        if path.is_absolute() and path.exists():
            return path
        candidate = self.dataset_dir.parent / relative_path
        if candidate.exists():
            return candidate
        candidate = self.dataset_dir / relative_path
        if candidate.exists():
            return candidate
        return self.dataset_dir.parent / relative_path

    def get_requirements_for(
        self, claim_object: str, issue_family: str
    ) -> List[Dict]:
        df = self.load_evidence_requirements()
        mask = (
            (df["claim_object"] == claim_object) | (df["claim_object"] == "all")
        ) & (df["applies_to"].str.lower() == issue_family.lower())
        return df[mask].to_dict("records")
