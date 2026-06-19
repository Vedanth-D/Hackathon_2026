"""Evaluate evidence requirements against image analyses."""

from typing import Dict, List, Optional

from src.data_loader import DataLoader
from src.schema import ImageAnalysis
from src.utils import normalize_issue_family


class EvidenceChecker:
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader

    def get_requirement_text(
        self, claim_object: str, issue_type: str
    ) -> Optional[str]:
        family = normalize_issue_family(issue_type)
        reqs = self.data_loader.get_requirements_for(claim_object, family)
        if not reqs:
            reqs = self.data_loader.get_requirements_for("all", family)
        if not reqs:
            return None
        return reqs[0].get("minimum_image_evidence", "")

    def check_evidence_standard(
        self,
        claim_object: str,
        claimed_issue: str,
        analyses: List[ImageAnalysis],
        valid_images: List[ImageAnalysis],
    ) -> tuple[bool, str]:
        if not analyses:
            return False, "No images submitted"

        if not valid_images:
            return False, "No usable images for automated review"

        requirement = self.get_requirement_text(claim_object, claimed_issue)
        if not requirement:
            if any(a.damage_visible for a in valid_images):
                return True, "Damage visible in submitted images"
            return False, "Minimum evidence requirements not met for issue type"

        damage_visible_count = sum(1 for a in valid_images if a.damage_visible)
        part_visible_count = sum(
            1 for a in valid_images if a.visible_object_part != "unknown"
        )

        req_lower = requirement.lower()
        needs_closeup = "close" in req_lower or "detail" in req_lower
        needs_context = "context" in req_lower or "wide" in req_lower or "full" in req_lower
        needs_multiple = "multiple" in req_lower or "two" in req_lower or "both" in req_lower

        if needs_multiple and len(valid_images) < 2:
            return False, f"Requirement needs multiple images: {requirement}"

        if damage_visible_count == 0:
            return False, f"Damage not visible; requirement: {requirement}"

        if needs_closeup and damage_visible_count < 1:
            return False, f"Close-up damage evidence required: {requirement}"

        if needs_context and part_visible_count < 1:
            return False, f"Context/wide shot required: {requirement}"

        return True, f"Image evidence meets requirement: {requirement}"
