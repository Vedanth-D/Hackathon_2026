# Multi-Modal Evidence Review

A hackathon system that verifies damage claims using **images** (primary source of truth), **user conversation**, **user history** (risk context), and **minimum evidence requirements**.

Supports three object types: `car`, `laptop`, `package`.

## Architecture

```
claims.csv + images + user_history + evidence_requirements
                    │
                    ▼
            ┌───────────────┐
            │ ClaimReviewer │
            └───────┬───────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
 Extract claim   Vision analyze   History risk
 (text LLM)      (per image)      flags
                    │
                    ▼
         Evidence standard check
                    │
                    ▼
         Rule-based synthesis + output.csv
```

### Pipeline per claim

1. **Extract claim** from conversation (issue type, object part, description)
2. **Analyze each image** with vision model (damage, part, quality flags, support/contradict)
3. **Check evidence requirements** from `evidence_requirements.csv`
4. **Apply user history** for risk flags (does not override clear visual evidence)
5. **Synthesize decision**: `supported`, `contradicted`, or `not_enough_information`

### Cost optimizations

- **Caching**: Image and text analyses cached by content hash in `.cache/`
- **Rate limiting**: Configurable RPM via `REQUESTS_PER_MINUTE`
- **Retries**: Exponential backoff on API failures (`tenacity`)
- **Mock mode**: Run full pipeline without API for development

## Setup

```bash
cd multi-modal-evidence-review
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env           # Add OPENAI_API_KEY
```

### Generate synthetic dataset (if not provided)

```bash
python scripts/generate_dataset.py
```

Place official hackathon `dataset/` files (CSV + images) in the project root if you have them.

## Usage

### Evaluate on sample claims (labeled)

```bash
python evaluation/evaluate.py
```

### Produce final predictions

```bash
python main.py
# or with mock mode (no API key):
python main.py --mock
```

Output: `output.csv` with all required columns.

### Options

```bash
python main.py --input claims.csv --output output.csv --dataset-dir dataset --mock --limit 5
```

## Output columns

| Column | Description |
|--------|-------------|
| `evidence_standard_met` | Images sufficient to evaluate |
| `evidence_standard_met_reason` | Why evidence is/isn't sufficient |
| `risk_flags` | Semicolon-separated quality/history flags |
| `issue_type` | Visible issue from allowed enum |
| `object_part` | Relevant part from allowed enum |
| `claim_status` | `supported`, `contradicted`, `not_enough_information` |
| `claim_status_justification` | Image-grounded explanation |
| `supporting_image_ids` | Image IDs backing the decision |
| `valid_image` | Image set usable for automation |
| `severity` | `none`, `low`, `medium`, `high`, `unknown` |

## Project structure

```
multi-modal-evidence-review/
├── main.py                 # CLI entry point
├── requirements.txt
├── output.csv              # Generated predictions
├── src/
│   ├── claim_reviewer.py   # Main orchestrator
│   ├── vision_analyzer.py  # OpenAI vision + mock
│   ├── evidence_checker.py
│   ├── history_analyzer.py
│   ├── data_loader.py
│   ├── prompts.py
│   ├── schema.py
│   └── utils.py
├── evaluation/
│   ├── evaluate.py
│   └── evaluation_report.md
├── scripts/
│   └── generate_dataset.py
└── dataset/
    ├── claims.csv
    ├── sample_claims.csv
    ├── user_history.csv
    ├── evidence_requirements.csv
    └── images/
```

## Models

- **Vision**: `gpt-4o-mini` (default) or `gpt-4o` via `OPENAI_MODEL`
- **Text extraction**: `gpt-4o-mini` via `OPENAI_TEXT_MODEL`

Set in `.env`:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEXT_MODEL=gpt-4o-mini
```

## Submission checklist

| File | Status |
|------|--------|
| `code.zip` | Full repo with `evaluation/` |
| `output.csv` | `python main.py` |
| `chat_transcript` | Cursor chat export |

## License

Hackathon submission — MIT
