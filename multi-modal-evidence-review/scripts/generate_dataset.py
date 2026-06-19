"""Generate synthetic dataset for testing the evidence review pipeline."""

import os
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
SAMPLE_IMG_DIR = DATASET_DIR / "images" / "sample"
TEST_IMG_DIR = DATASET_DIR / "images" / "test"


def make_image(
    path: Path,
    label: str,
    color: tuple = (180, 180, 180),
    damage_color: tuple = (200, 50, 50),
):
    img = Image.new("RGB", (640, 480), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([80, 80, 560, 400], fill=color, outline=(60, 60, 60), width=3)
    draw.text((100, 100), label, fill=(20, 20, 20))
    if "dent" in label.lower() or "scratch" in label.lower():
        draw.ellipse([300, 200, 380, 280], fill=damage_color)
    if "crack" in label.lower() or "shatter" in label.lower():
        draw.line([250, 150, 400, 350], fill=damage_color, width=4)
        draw.line([280, 140, 350, 360], fill=damage_color, width=3)
    if "crush" in label.lower() or "torn" in label.lower():
        draw.polygon([(200, 200), (350, 180), (400, 350), (180, 320)], fill=damage_color)
    if "no_damage" in label.lower() or "clean" in label.lower():
        pass  # no damage marks
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "JPEG")


def write_evidence_requirements():
    rows = [
        ("req_car_dent", "car", "dent or scratch", "Close-up showing dent or scratch with surrounding body panel context"),
        ("req_car_glass", "car", "glass shatter", "Clear image of windshield or glass with shatter pattern visible"),
        ("req_laptop_screen", "laptop", "crack", "Screen image showing crack pattern; lid open if possible"),
        ("req_laptop_body", "laptop", "dent or scratch", "Close-up of laptop body damage with corner or lid visible"),
        ("req_pkg_torn", "package", "torn packaging", "Image showing torn outer packaging and seal area"),
        ("req_pkg_crush", "package", "crushed packaging", "Multiple angles showing crushed box corners and contents if opened"),
        ("req_pkg_water", "package", "water damage", "Stains or warping on box; label and contents if wet"),
        ("req_all_blurry", "all", "dent or scratch", "At least one clear close-up where damage is readable"),
    ]
    df = pd.DataFrame(
        rows,
        columns=["requirement_id", "claim_object", "applies_to", "minimum_image_evidence"],
    )
    df.to_csv(DATASET_DIR / "evidence_requirements.csv", index=False)


def write_user_history():
    rows = [
        ("user_001", 2, 2, 0, 0, 1, "none", "Low claim history, previously accepted"),
        ("user_002", 5, 3, 1, 1, 2, "repeat_claims", "Multiple claims in 90 days"),
        ("user_003", 8, 2, 3, 3, 4, "high_rejection;suspicious", "High rejection rate, flagged suspicious"),
        ("user_004", 1, 1, 0, 0, 1, "none", "First-time claimant"),
        ("user_005", 4, 1, 2, 1, 3, "manual_review", "Frequent manual reviews"),
        ("user_006", 0, 0, 0, 0, 0, "none", "New user"),
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "user_id", "past_claim_count", "accept_claim", "manual_review_claim",
            "rejected_claim", "last_90_days_claim_count", "history_flags", "history_summary",
        ],
    )
    df.to_csv(DATASET_DIR / "user_history.csv", index=False)


def create_sample_dataset():
    cases = [
        {
            "user_id": "user_001",
            "case": "case_s01",
            "images": ["img_1_door_scratch.jpg", "img_2_door_context.jpg"],
            "user_claim": "User: My car door got scratched in parking.\nAgent: Can you share a photo?\nUser: Here are two pictures of the scratch on the driver door.",
            "claim_object": "car",
            "expected": {
                "evidence_standard_met": "true",
                "issue_type": "scratch",
                "object_part": "door",
                "claim_status": "supported",
                "valid_image": "true",
                "severity": "low",
            },
        },
        {
            "user_id": "user_002",
            "case": "case_s02",
            "images": ["img_1_bumper_dent.jpg"],
            "user_claim": "User: Front bumper has a big dent from a fender bender.\nAgent: Please upload bumper photos.\nUser: Attached one photo.",
            "claim_object": "car",
            "expected": {
                "evidence_standard_met": "true",
                "issue_type": "dent",
                "object_part": "front_bumper",
                "claim_status": "supported",
                "valid_image": "true",
                "severity": "medium",
            },
        },
        {
            "user_id": "user_004",
            "case": "case_s03",
            "images": ["img_1_screen_crack.jpg"],
            "user_claim": "User: Laptop screen cracked when bag fell.\nAgent: Send screen photo.\nUser: Here is the cracked screen.",
            "claim_object": "laptop",
            "expected": {
                "evidence_standard_met": "true",
                "issue_type": "crack",
                "object_part": "screen",
                "claim_status": "supported",
                "valid_image": "true",
                "severity": "high",
            },
        },
        {
            "user_id": "user_006",
            "case": "case_s04",
            "images": ["img_1_box_crush.jpg", "img_2_box_corner.jpg"],
            "user_claim": "User: Package arrived crushed.\nAgent: Photos of box?\nUser: Two angles of crushed corners.",
            "claim_object": "package",
            "expected": {
                "evidence_standard_met": "true",
                "issue_type": "crushed_packaging",
                "object_part": "box",
                "claim_status": "supported",
                "valid_image": "true",
                "severity": "medium",
            },
        },
        {
            "user_id": "user_001",
            "case": "case_s05",
            "images": ["img_1_door_clean.jpg"],
            "user_claim": "User: Door is badly scratched.\nAgent: Photo of scratch?\nUser: See attached.",
            "claim_object": "car",
            "expected": {
                "evidence_standard_met": "true",
                "issue_type": "none",
                "object_part": "door",
                "claim_status": "contradicted",
                "valid_image": "true",
                "severity": "none",
            },
        },
        {
            "user_id": "user_003",
            "case": "case_s06",
            "images": ["img_1_blur.jpg"],
            "user_claim": "User: Windshield shattered.\nAgent: Clear photo needed.\nUser: This is all I have.",
            "claim_object": "car",
            "expected": {
                "evidence_standard_met": "false",
                "issue_type": "unknown",
                "object_part": "unknown",
                "claim_status": "not_enough_information",
                "valid_image": "false",
                "severity": "unknown",
            },
        },
    ]

    rows = []
    for c in cases:
        case_dir = SAMPLE_IMG_DIR / c["case"]
        paths = []
        for img_name in c["images"]:
            label = img_name.replace(".jpg", "").replace("_", " ")
            make_image(case_dir / img_name, label)
            paths.append(f"images/sample/{c['case']}/{img_name}")

        row = {
            "user_id": c["user_id"],
            "image_paths": ";".join(paths),
            "user_claim": c["user_claim"],
            "claim_object": c["claim_object"],
            **c["expected"],
            "evidence_standard_met_reason": "labeled sample",
            "risk_flags": "none",
            "claim_status_justification": "labeled sample",
            "supporting_image_ids": c["images"][0].replace(".jpg", "").split("_")[0] + "_" + c["images"][0].replace(".jpg", "").split("_")[1],
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(DATASET_DIR / "sample_claims.csv", index=False)


def create_test_dataset():
    cases = [
        ("user_001", "case_001", ["img_1_door_scratch.jpg", "img_2_door_context.jpg"],
         "User: Scratch on rear door from shopping cart.\nAgent: Please share photos.\nUser: Attached door scratch images.", "car"),
        ("user_002", "case_002", ["img_1_bumper_dent.jpg"],
         "User: Hit a pole, front bumper dented.\nAgent: Bumper photo?\nUser: One bumper picture.", "car"),
        ("user_004", "case_003", ["img_1_screen_crack.jpg"],
         "User: Screen has crack line across display.\nAgent: Upload screen photo.\nUser: Photo attached.", "laptop"),
        ("user_005", "case_004", ["img_1_box_torn.jpg"],
         "User: Outer box torn open on delivery.\nAgent: Packaging photos?\nUser: Torn seal photo.", "package"),
        ("user_006", "case_005", ["img_1_box_crush.jpg", "img_2_box_corner.jpg"],
         "User: Box completely crushed.\nAgent: Multiple angles help.\nUser: Two crushed box photos.", "package"),
        ("user_003", "case_006", ["img_1_windshield_shatter.jpg"],
         "User: Windshield shattered in storm.\nAgent: Glass damage photo?\nUser: Shattered windshield image.", "car"),
        ("user_001", "case_007", ["img_1_hood_clean.jpg"],
         "User: Hood has deep scratch.\nAgent: Hood photo?\nUser: Attached hood image.", "car"),
        ("user_002", "case_008", ["img_1_keyboard_damage.jpg"],
         "User: Keyboard keys broken after drop.\nAgent: Keyboard photo?\nUser: Broken key photo.", "laptop"),
        ("user_005", "case_009", ["img_1_blur.jpg"],
         "User: Package water damaged.\nAgent: Clear photos of stains?\nUser: Blurry photo only.", "package"),
        ("user_004", "case_010", ["img_1_wrong_object.jpg"],
         "User: Laptop corner dented.\nAgent: Laptop photo?\nUser: Attached image.", "laptop"),
    ]

    rows = []
    for user_id, case, images, claim, obj in cases:
        case_dir = TEST_IMG_DIR / case
        paths = []
        for img_name in images:
            label = img_name.replace(".jpg", "").replace("_", " ")
            if "blur" in img_name:
                make_image(case_dir / img_name, "blurry unreadable", color=(100, 100, 100))
            elif "wrong" in img_name:
                make_image(case_dir / img_name, "wrong object phone not laptop", color=(50, 150, 200))
            elif "clean" in img_name:
                make_image(case_dir / img_name, "hood no_damage clean", color=(160, 160, 160))
            elif "torn" in img_name:
                make_image(case_dir / img_name, "box torn packaging", color=(200, 180, 140))
            elif "keyboard" in img_name:
                make_image(case_dir / img_name, "keyboard broken_part", color=(80, 80, 90))
            elif "shatter" in img_name:
                make_image(case_dir / img_name, "windshield glass_shatter", color=(150, 180, 200))
            else:
                make_image(case_dir / img_name, label)
            paths.append(f"images/test/{case}/{img_name}")

        rows.append({
            "user_id": user_id,
            "image_paths": ";".join(paths),
            "user_claim": claim,
            "claim_object": obj,
        })

    df = pd.DataFrame(rows)
    df.to_csv(DATASET_DIR / "claims.csv", index=False)


def main():
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    write_evidence_requirements()
    write_user_history()
    create_sample_dataset()
    create_test_dataset()
    print(f"Dataset created at {DATASET_DIR}")


if __name__ == "__main__":
    main()
