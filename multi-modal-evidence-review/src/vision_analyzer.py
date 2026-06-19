"""Vision model integration for image analysis."""

import base64
import json
import logging
from pathlib import Path
from typing import List, Optional

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEXT_MODEL
from src.prompts import CLAIM_EXTRACTION_PROMPT, IMAGE_ANALYSIS_PROMPT
from src.schema import ExtractedClaim, ImageAnalysis
from src.utils import (
    RateLimiter,
    read_cache,
    UsageTracker,
    write_cache,
    closest_allowed,
    image_id_from_path,
)
from src.schema import IssueType, Severity

logger = logging.getLogger(__name__)

ISSUE_TYPES = {e.value for e in IssueType}
SEVERITIES = {e.value for e in Severity}


class VisionAnalyzer:
    def __init__(
        self,
        usage: UsageTracker,
        rate_limiter: RateLimiter,
        mock_mode: bool = False,
    ):
        self.usage = usage
        self.rate_limiter = rate_limiter
        self.mock_mode = mock_mode or not OPENAI_API_KEY
        self.client = OpenAI(api_key=OPENAI_API_KEY) if not self.mock_mode else None

    def _encode_image(self, path: Path) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _call_text(self, prompt: str, cache_key: str) -> dict:
        cached = read_cache(cache_key)
        if cached:
            self.usage.cache_hits += 1
            return cached

        if self.mock_mode:
            return self._mock_text_response(prompt)

        self.rate_limiter.wait()
        response = self._api_text_call(prompt)
        data = json.loads(response)
        write_cache(cache_key, data)
        return data

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _api_text_call(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=OPENAI_TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        self.usage.record(
            input_tokens=response.usage.prompt_tokens or 0,
            output_tokens=response.usage.completion_tokens or 0,
        )
        return response.choices[0].message.content

    def _call_vision(
        self, prompt: str, image_path: Path, cache_key: str
    ) -> dict:
        cached = read_cache(cache_key)
        if cached:
            self.usage.cache_hits += 1
            return cached

        if self.mock_mode:
            return self._mock_vision_response(prompt, image_path)

        self.rate_limiter.wait()
        b64 = self._encode_image(image_path)
        ext = image_path.suffix.lower().replace(".", "")
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext

        response = self._api_vision_call(prompt, b64, mime)
        data = json.loads(response)
        write_cache(cache_key, data)
        return data

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _api_vision_call(self, prompt: str, b64: str, mime: str) -> str:
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{mime};base64,{b64}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=800,
        )
        self.usage.record(
            input_tokens=response.usage.prompt_tokens or 0,
            output_tokens=response.usage.completion_tokens or 0,
            images=1,
        )
        return response.choices[0].message.content

    def extract_claim(self, user_claim: str, claim_object: str) -> ExtractedClaim:
        prompt = CLAIM_EXTRACTION_PROMPT.format(
            claim_object=claim_object,
            user_claim=user_claim,
        )
        cache_key = f"extract:{claim_object}:{hash(user_claim)}"
        data = self._call_text(prompt, cache_key)
        return ExtractedClaim(
            damage_description=data.get("damage_description", user_claim),
            claimed_issue_type=closest_allowed(
                data.get("claimed_issue_type", "unknown"), ISSUE_TYPES
            ),
            claimed_object_part=data.get("claimed_object_part", "unknown"),
            claimed_severity_hint=data.get("claimed_severity_hint"),
        )

    def analyze_image(
        self,
        image_path: Path,
        image_id: str,
        claim_object: str,
        extracted: ExtractedClaim,
    ) -> ImageAnalysis:
        prompt = IMAGE_ANALYSIS_PROMPT.format(
            claim_object=claim_object,
            damage_description=extracted.damage_description,
            claimed_issue_type=extracted.claimed_issue_type,
            claimed_object_part=extracted.claimed_object_part,
            image_id=image_id,
        )
        cache_key = f"vision:{image_path}"
        data = self._call_vision(prompt, image_path, cache_key)

        quality_flags = data.get("quality_flags", [])
        if not isinstance(quality_flags, list):
            quality_flags = []

        return ImageAnalysis(
            image_id=image_id,
            valid_image=bool(data.get("valid_image", False)),
            object_type_matches=bool(data.get("object_type_matches", False)),
            visible_object_part=data.get("visible_object_part", "unknown"),
            issue_type=closest_allowed(
                data.get("issue_type", "unknown"), ISSUE_TYPES
            ),
            damage_visible=bool(data.get("damage_visible", False)),
            severity=closest_allowed(
                data.get("severity", "unknown"), SEVERITIES
            ),
            quality_flags=quality_flags,
            description=data.get("description", ""),
            supports_user_claim=data.get("supports_user_claim"),
        )

    def _mock_text_response(self, prompt: str) -> dict:
        self.usage.record(input_tokens=200, output_tokens=80)
        prompt_lower = prompt.lower()
        issue = "scratch"
        part = "door"
        if "laptop" in prompt_lower:
            part = "screen"
            if "crack" in prompt_lower:
                issue = "crack"
        elif "package" in prompt_lower:
            part = "box"
            if "crush" in prompt_lower:
                issue = "crushed_packaging"
            elif "torn" in prompt_lower:
                issue = "torn_packaging"
        elif "dent" in prompt_lower:
            issue = "dent"
        elif "scratch" in prompt_lower:
            issue = "scratch"
        elif "windshield" in prompt_lower or "glass" in prompt_lower:
            issue = "glass_shatter"
            part = "windshield"
        return {
            "damage_description": "User reported damage as described in conversation",
            "claimed_issue_type": issue,
            "claimed_object_part": part,
            "claimed_severity_hint": None,
        }

    def _mock_vision_response(self, prompt: str, image_path: Path) -> dict:
        self.usage.record(input_tokens=500, output_tokens=150, images=1)
        image_id = image_id_from_path(str(image_path))
        stem = image_path.stem.lower()

        # Parse synthetic image metadata from filename if present
        issue = "unknown"
        part = "unknown"
        severity = "medium"
        damage_visible = True
        supports = True
        valid = True
        object_match = True
        quality_flags: List[str] = []

        if "no_damage" in stem or "clean" in stem:
            issue = "none"
            damage_visible = False
            severity = "none"
            supports = False
        if "context" in stem:
            damage_visible = False
            supports = None
            if issue == "unknown":
                issue = "none"
        if "blur" in stem:
            quality_flags.append("blurry_image")
            valid = False
        if "wrong" in stem:
            quality_flags.append("wrong_object")
            object_match = False
            supports = False
            damage_visible = False
            issue = "unknown"
        if "dent" in stem:
            issue = "dent"
        if "scratch" in stem:
            issue = "scratch"
        if "crack" in stem:
            issue = "crack"
        if "shatter" in stem:
            issue = "glass_shatter"
        if "torn" in stem:
            issue = "torn_packaging"
        if "crush" in stem:
            issue = "crushed_packaging"
        if "water" in stem:
            issue = "water_damage"
        if "keyboard" in stem or "broken" in stem:
            issue = "broken_part"
        if "bumper" in stem:
            part = "front_bumper"
        if "hood" in stem:
            part = "hood"
        if "windshield" in stem:
            part = "windshield"
        if "door" in stem:
            part = "door"
        if "screen" in stem:
            part = "screen"
        if "keyboard" in stem:
            part = "keyboard"
        if "box" in stem or "package" in stem:
            part = "box"

        return {
            "image_id": image_id,
            "valid_image": valid,
            "object_type_matches": object_match,
            "visible_object_part": part,
            "issue_type": issue,
            "damage_visible": damage_visible,
            "severity": severity,
            "quality_flags": quality_flags,
            "description": f"Mock analysis of {image_path.name}",
            "supports_user_claim": supports if damage_visible else False,
        }
