# Multi-Modal Evidence Review — Chat Transcript Summary

## Development conversation

This project was built in Cursor with the following approach:

### 1. Problem analysis
- Images are the **primary source of truth**
- User conversation defines what to verify
- User history adds **risk context only** (never overrides clear visual evidence)
- Evidence requirements define minimum image standards per object/issue type

### 2. Architecture decisions
- **Two-stage pipeline**: text extraction → per-image vision analysis → rule-based synthesis
- **OpenAI gpt-4o-mini** for cost-effective vision (configurable to gpt-4o)
- **Caching** by content hash to avoid duplicate API calls
- **Rate limiting** and retries for production safety
- **Mock mode** for offline development without API keys

### 3. Implementation steps
1. Defined Pydantic schemas for all allowed output enums
2. Built data loaders for claims, history, evidence requirements
3. Implemented `VisionAnalyzer` with OpenAI vision API + filename-aware mock fallback
4. Built `EvidenceChecker` against `evidence_requirements.csv`
5. Built `HistoryAnalyzer` for risk flags (`user_history_risk`, `manual_review_required`)
6. Orchestrated in `ClaimReviewer` with image-grounded justifications
7. Created evaluation script comparing predictions to `sample_claims.csv`
8. Generated synthetic dataset with labeled images for testing

### 4. Key prompts
- Claim extraction from chat transcript (JSON output)
- Per-image visual analysis with quality flags and support/contradict signal
- Final synthesis grounded in image IDs

### 5. Operational considerations (see evaluation/evaluation_report.md)
- ~24 model calls for 10 test claims (first run)
- ~$0.005 on gpt-4o-mini for full test set
- Caching reduces cost on re-runs to near zero

### 6. How to run
```bash
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY
python evaluation/evaluate.py   # sample evaluation
python main.py                  # produce output.csv
python main.py --mock           # offline mock mode
```

### 7. Files produced
- Full `src/` pipeline
- `dataset/` with CSVs and images
- `output.csv` predictions
- `evaluation/evaluate.py` + `evaluation_report.md`
