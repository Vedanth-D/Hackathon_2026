"""Output schema and allowed value enums for claim review."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ClaimStatus(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    NOT_ENOUGH_INFORMATION = "not_enough_information"


class IssueType(str, Enum):
    DENT = "dent"
    SCRATCH = "scratch"
    CRACK = "crack"
    GLASS_SHATTER = "glass_shatter"
    BROKEN_PART = "broken_part"
    MISSING_PART = "missing_part"
    TORN_PACKAGING = "torn_packaging"
    CRUSHED_PACKAGING = "crushed_packaging"
    WATER_DAMAGE = "water_damage"
    STAIN = "stain"
    NONE = "none"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


RISK_FLAGS = {
    "none",
    "blurry_image",
    "cropped_or_obstructed",
    "low_light_or_glare",
    "wrong_angle",
    "wrong_object",
    "wrong_object_part",
    "damage_not_visible",
    "claim_mismatch",
    "possible_manipulation",
    "non_original_image",
    "text_instruction_present",
    "user_history_risk",
    "manual_review_required",
}

CAR_PARTS = {
    "front_bumper", "rear_bumper", "door", "hood", "windshield",
    "side_mirror", "headlight", "taillight", "fender", "quarter_panel",
    "body", "unknown",
}

LAPTOP_PARTS = {
    "screen", "keyboard", "trackpad", "hinge", "lid", "corner",
    "port", "base", "body", "unknown",
}

PACKAGE_PARTS = {
    "box", "package_corner", "package_side", "seal", "label",
    "contents", "item", "unknown",
}


OUTPUT_COLUMNS = [
    "user_id",
    "image_paths",
    "user_claim",
    "claim_object",
    "evidence_standard_met",
    "evidence_standard_met_reason",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "claim_status_justification",
    "supporting_image_ids",
    "valid_image",
    "severity",
]


class ExtractedClaim(BaseModel):
    """Structured extraction from user conversation."""
    damage_description: str
    claimed_issue_type: str
    claimed_object_part: str
    claimed_severity_hint: Optional[str] = None


class ImageAnalysis(BaseModel):
    """Per-image vision model analysis."""
    image_id: str
    valid_image: bool
    object_type_matches: bool
    visible_object_part: str
    issue_type: str
    damage_visible: bool
    severity: str
    quality_flags: List[str] = Field(default_factory=list)
    description: str
    supports_user_claim: Optional[bool] = None


class ClaimReviewResult(BaseModel):
    """Final review output for one claim."""
    user_id: str
    image_paths: str
    user_claim: str
    claim_object: str
    evidence_standard_met: bool
    evidence_standard_met_reason: str
    risk_flags: str
    issue_type: str
    object_part: str
    claim_status: str
    claim_status_justification: str
    supporting_image_ids: str
    valid_image: bool
    severity: str

    @field_validator("risk_flags")
    @classmethod
    def validate_risk_flags(cls, v: str) -> str:
        flags = [f.strip() for f in v.split(";") if f.strip()]
        for flag in flags:
            if flag not in RISK_FLAGS:
                raise ValueError(f"Invalid risk flag: {flag}")
        return v

    def to_row(self) -> dict:
        return {
            "user_id": self.user_id,
            "image_paths": self.image_paths,
            "user_claim": self.user_claim,
            "claim_object": self.claim_object,
            "evidence_standard_met": str(self.evidence_standard_met).lower(),
            "evidence_standard_met_reason": self.evidence_standard_met_reason,
            "risk_flags": self.risk_flags,
            "issue_type": self.issue_type,
            "object_part": self.object_part,
            "claim_status": self.claim_status,
            "claim_status_justification": self.claim_status_justification,
            "supporting_image_ids": self.supporting_image_ids,
            "valid_image": str(self.valid_image).lower(),
            "severity": self.severity,
        }
