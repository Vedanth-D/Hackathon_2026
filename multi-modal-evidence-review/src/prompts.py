"""Prompt templates for claim extraction and image analysis."""

CLAIM_EXTRACTION_PROMPT = """You are an insurance claims analyst. Extract the damage claim from this user conversation.

Object type: {claim_object}

User conversation:
{user_claim}

Return JSON with:
- damage_description: what the user says is damaged
- claimed_issue_type: one of dent, scratch, crack, glass_shatter, broken_part, missing_part, torn_packaging, crushed_packaging, water_damage, stain, none, unknown
- claimed_object_part: the part they claim is affected (use allowed parts for {claim_object})
- claimed_severity_hint: optional severity hint from conversation or null

Allowed car parts: front_bumper, rear_bumper, door, hood, windshield, side_mirror, headlight, taillight, fender, quarter_panel, body, unknown
Allowed laptop parts: screen, keyboard, trackpad, hinge, lid, corner, port, base, body, unknown
Allowed package parts: box, package_corner, package_side, seal, label, contents, item, unknown
"""

IMAGE_ANALYSIS_PROMPT = """You are a visual evidence reviewer for damage claims. Analyze this image objectively.

Context:
- Expected object type: {claim_object}
- User claims: {damage_description}
- Claimed issue: {claimed_issue_type} on {claimed_object_part}
- Image ID: {image_id}

Inspect the image and return JSON:
- image_id: "{image_id}"
- valid_image: true if image is usable (not corrupt, not blank); false otherwise
- object_type_matches: true if the image shows the expected object type
- visible_object_part: part visible in image (use allowed parts for {claim_object})
- issue_type: visible issue type from allowed list
- damage_visible: true if damage/issue is clearly visible
- severity: none, low, medium, high, or unknown
- quality_flags: list from blurry_image, cropped_or_obstructed, low_light_or_glare, wrong_angle, wrong_object, wrong_object_part, damage_not_visible, possible_manipulation, non_original_image, text_instruction_present (empty if none)
- description: brief factual description of what you see
- supports_user_claim: true if image supports claim, false if contradicts, null if unclear

Allowed issue types: dent, scratch, crack, glass_shatter, broken_part, missing_part, torn_packaging, crushed_packaging, water_damage, stain, none, unknown

Images are the primary source of truth. Be specific and ground observations in visible details.
"""

FINAL_SYNTHESIS_PROMPT = """Synthesize a final claim decision from image analyses and context.

Object: {claim_object}
User conversation: {user_claim}
Extracted claim: {extracted_claim}
Evidence requirement: {evidence_requirement}
User history flags: {history_flags}
Image analyses: {image_analyses}

Rules:
1. Images are primary source of truth; history adds risk context only
2. claim_status: supported, contradicted, or not_enough_information
3. evidence_standard_met: whether images suffice to evaluate
4. Select supporting_image_ids that ground the decision

Return JSON:
- evidence_standard_met: boolean
- evidence_standard_met_reason: short reason
- risk_flags: semicolon-separated from allowed list or "none"
- issue_type: from allowed list
- object_part: from allowed list
- claim_status: supported, contradicted, or not_enough_information
- claim_status_justification: concise, mention image IDs when helpful
- supporting_image_ids: semicolon-separated image IDs or "none"
- valid_image: boolean for overall image set usability
- severity: none, low, medium, high, unknown
"""
