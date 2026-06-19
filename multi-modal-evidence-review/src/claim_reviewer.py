"""Main claim review orchestrator."""

import json
import logging
from typing import List, Optional

from src.data_loader import DataLoader
from src.evidence_checker import EvidenceChecker
from src.history_analyzer import HistoryAnalyzer
from src.prompts import FINAL_SYNTHESIS_PROMPT
from src.schema import (
    CAR_PARTS,
    LAPTOP_PARTS,
    PACKAGE_PARTS,
    ClaimReviewResult,
    ClaimStatus,
    ImageAnalysis,
    ExtractedClaim,
)
from src.utils import (
    RateLimiter,
    UsageTracker,
    join_flags,
    closest_allowed,
    parse_image_paths,
    image_id_from_path,
    read_cache,
    write_cache,
)
from src.vision_analyzer import VisionAnalyzer, ISSUE_TYPES, SEVERITIES

logger = logging.getLogger(__name__)


class ClaimReviewer:
    def __init__(
        self,
        dataset_dir: Optional[str] = None,
        mock_mode: bool = False,
    ):
        self.data_loader = DataLoader(dataset_dir)
        self.usage = UsageTracker()
        self.rate_limiter = RateLimiter()
        self.vision = VisionAnalyzer(self.usage, self.rate_limiter, mock_mode)
        self.evidence_checker = EvidenceChecker(self.data_loader)
        self.history_analyzer = HistoryAnalyzer(self.data_loader)

    def _parts_for_object(self, claim_object: str) -> set:
        if claim_object == "car":
            return CAR_PARTS
        if claim_object == "laptop":
            return LAPTOP_PARTS
        if claim_object == "package":
            return PACKAGE_PARTS
        return {"unknown"}

    def review_claim(self, row: dict) -> ClaimReviewResult:
        user_id = row["user_id"]
        image_paths_str = row["image_paths"]
        user_claim = row["user_claim"]
        claim_object = row["claim_object"]

        extracted = self.vision.extract_claim(user_claim, claim_object)
        history = self.history_analyzer.analyze(user_id)

        paths = parse_image_paths(image_paths_str)
        analyses: List[ImageAnalysis] = []

        for rel_path in paths:
            full_path = self.data_loader.resolve_image_path(rel_path)
            image_id = image_id_from_path(rel_path)
            if not full_path.exists():
                logger.warning("Image not found: %s", full_path)
                analyses.append(
                    ImageAnalysis(
                        image_id=image_id,
                        valid_image=False,
                        object_type_matches=False,
                        visible_object_part="unknown",
                        issue_type="unknown",
                        damage_visible=False,
                        severity="unknown",
                        quality_flags=["damage_not_visible"],
                        description="Image file not found",
                        supports_user_claim=None,
                    )
                )
                continue
            analysis = self.vision.analyze_image(
                full_path, image_id, claim_object, extracted
            )
            analyses.append(analysis)

        valid_analyses = [a for a in analyses if a.valid_image]
        evidence_met, evidence_reason = self.evidence_checker.check_evidence_standard(
            claim_object,
            extracted.claimed_issue_type,
            analyses,
            valid_analyses,
        )

        requirement = self.evidence_checker.get_requirement_text(
            claim_object, extracted.claimed_issue_type
        )

        # Rule-based synthesis with optional LLM enhancement
        result = self._synthesize_decision(
            user_id=user_id,
            image_paths_str=image_paths_str,
            user_claim=user_claim,
            claim_object=claim_object,
            extracted=extracted,
            analyses=analyses,
            valid_analyses=valid_analyses,
            evidence_met=evidence_met,
            evidence_reason=evidence_reason,
            requirement=requirement or "No specific requirement found",
            history=history,
        )
        return result

    def _synthesize_decision(
        self,
        user_id: str,
        image_paths_str: str,
        user_claim: str,
        claim_object: str,
        extracted: ExtractedClaim,
        analyses: List[ImageAnalysis],
        valid_analyses: List[ImageAnalysis],
        evidence_met: bool,
        evidence_reason: str,
        requirement: str,
        history: dict,
    ) -> ClaimReviewResult:
        parts_set = self._parts_for_object(claim_object)
        risk_flags: List[str] = list(history.get("risk_flags", []))

        for a in analyses:
            risk_flags.extend(a.quality_flags)
            if not a.object_type_matches:
                risk_flags.append("wrong_object")
            if a.visible_object_part != "unknown" and a.visible_object_part != extracted.claimed_object_part:
                if extracted.claimed_object_part != "unknown":
                    risk_flags.append("wrong_object_part")
            if not a.damage_visible and a.valid_image:
                risk_flags.append("damage_not_visible")

        valid_image = any(a.valid_image for a in analyses)

        if not valid_image:
            return ClaimReviewResult(
                user_id=user_id,
                image_paths=image_paths_str,
                user_claim=user_claim,
                claim_object=claim_object,
                evidence_standard_met=False,
                evidence_standard_met_reason="No valid images for review",
                risk_flags=join_flags(risk_flags),
                issue_type="unknown",
                object_part="unknown",
                claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION.value,
                claim_status_justification="Submitted images are not usable for automated review.",
                supporting_image_ids="none",
                valid_image=False,
                severity="unknown",
            )

        if not evidence_met:
            return ClaimReviewResult(
                user_id=user_id,
                image_paths=image_paths_str,
                user_claim=user_claim,
                claim_object=claim_object,
                evidence_standard_met=False,
                evidence_standard_met_reason=evidence_reason,
                risk_flags=join_flags(risk_flags),
                issue_type=closest_allowed(
                    extracted.claimed_issue_type, ISSUE_TYPES
                ),
                object_part=closest_allowed(
                    extracted.claimed_object_part, parts_set
                ),
                claim_status=ClaimStatus.NOT_ENOUGH_INFORMATION.value,
                claim_status_justification=evidence_reason,
                supporting_image_ids="none",
                valid_image=True,
                severity="unknown",
            )

        supporting = []
        contradicting = []
        primary_issue = "unknown"
        primary_part = "unknown"
        max_severity = "none"
        severity_rank = {"none": 0, "low": 1, "medium": 2, "high": 3, "unknown": 1}

        for a in valid_analyses:
            if a.damage_visible:
                primary_issue = closest_allowed(a.issue_type, ISSUE_TYPES)
                primary_part = closest_allowed(a.visible_object_part, parts_set)
                if severity_rank.get(a.severity, 1) > severity_rank.get(max_severity, 0):
                    max_severity = closest_allowed(a.severity, SEVERITIES)

            if a.supports_user_claim is True:
                supporting.append(a.image_id)
            elif a.supports_user_claim is False:
                contradicting.append(a.image_id)

        # Determine claim status from visual evidence
        if supporting and not contradicting:
            claim_status = ClaimStatus.SUPPORTED.value
            justification = self._build_justification(
                supporting, analyses, "supports", extracted
            )
            supporting_ids = ";".join(supporting)
        elif contradicting and not supporting:
            claim_status = ClaimStatus.CONTRADICTED.value
            justification = self._build_justification(
                contradicting, analyses, "contradicts", extracted
            )
            supporting_ids = ";".join(contradicting)
            if "claim_mismatch" not in risk_flags:
                risk_flags.append("claim_mismatch")
        elif supporting and contradicting:
            claim_status = ClaimStatus.NOT_ENOUGH_INFORMATION.value
            justification = (
                "Images provide mixed signals; some support and some contradict the claim."
            )
            supporting_ids = ";".join(supporting)
            risk_flags.append("manual_review_required")
        else:
            # No explicit support/contradict - infer from damage visibility
            damage_analyses = [a for a in valid_analyses if a.damage_visible]
            if damage_analyses:
                claim_status = ClaimStatus.SUPPORTED.value
                supporting_ids = ";".join([a.image_id for a in damage_analyses])
                justification = self._build_justification(
                    [a.image_id for a in damage_analyses],
                    analyses,
                    "shows damage consistent with",
                    extracted,
                )
            else:
                no_damage = [a for a in valid_analyses if a.issue_type == "none"]
                if no_damage:
                    claim_status = ClaimStatus.CONTRADICTED.value
                    supporting_ids = ";".join([a.image_id for a in no_damage])
                    justification = (
                        f"Images {supporting_ids} show no visible damage on the claimed part."
                    )
                    risk_flags.append("claim_mismatch")
                else:
                    claim_status = ClaimStatus.NOT_ENOUGH_INFORMATION.value
                    justification = "Images do not clearly show or refute the claimed damage."
                    supporting_ids = "none"

        # Issue type none when no damage visible but part is visible
        if claim_status == ClaimStatus.CONTRADICTED.value and primary_issue == "unknown":
            primary_issue = "none"

        return ClaimReviewResult(
            user_id=user_id,
            image_paths=image_paths_str,
            user_claim=user_claim,
            claim_object=claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=evidence_reason,
            risk_flags=join_flags(risk_flags),
            issue_type=primary_issue,
            object_part=primary_part if primary_part != "unknown" else closest_allowed(
                extracted.claimed_object_part, parts_set
            ),
            claim_status=claim_status,
            claim_status_justification=justification,
            supporting_image_ids=supporting_ids,
            valid_image=True,
            severity=max_severity,
        )

    def _build_justification(
        self,
        image_ids: List[str],
        analyses: List[ImageAnalysis],
        verb: str,
        extracted: ExtractedClaim,
    ) -> str:
        parts = []
        for img_id in image_ids:
            match = next((a for a in analyses if a.image_id == img_id), None)
            if match:
                parts.append(f"{img_id}: {match.description}")
        detail = "; ".join(parts[:2])
        return (
            f"Image evidence {verb} the claim of {extracted.claimed_issue_type} "
            f"on {extracted.claimed_object_part}. {detail}"
        )

    def get_usage(self) -> dict:
        return self.usage.to_dict()
