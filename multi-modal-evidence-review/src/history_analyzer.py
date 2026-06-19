"""Analyze user history for risk context."""

from typing import Dict, List, Optional

from src.data_loader import DataLoader


class HistoryAnalyzer:
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader

    def analyze(self, user_id: str) -> Dict:
        history = self.data_loader.get_user_history(user_id)
        if not history:
            return {
                "risk_flags": [],
                "history_flags": "",
                "history_summary": "",
                "manual_review_required": False,
            }

        flags: List[str] = []
        past_count = int(history.get("past_claim_count", 0) or 0)
        rejected = int(history.get("rejected_claim", 0) or 0)
        manual = int(history.get("manual_review_claim", 0) or 0)
        recent = int(history.get("last_90_days_claim_count", 0) or 0)
        history_flags = str(history.get("history_flags", "") or "")
        history_summary = str(history.get("history_summary", "") or "")

        if rejected >= 2 or (past_count > 0 and rejected / past_count > 0.4):
            flags.append("user_history_risk")

        if recent >= 3:
            flags.append("user_history_risk")

        if "fraud" in history_flags.lower() or "suspicious" in history_flags.lower():
            flags.append("user_history_risk")

        if manual >= 2:
            flags.append("manual_review_required")

        return {
            "risk_flags": flags,
            "history_flags": history_flags,
            "history_summary": history_summary,
            "manual_review_required": "manual_review_required" in flags,
            "past_claim_count": past_count,
            "rejected_claim": rejected,
        }
