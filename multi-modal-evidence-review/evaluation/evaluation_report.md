# Operational Analysis — Multi-Modal Evidence Review

## Processing assumptions

| Parameter | Sample set | Test set |
|-----------|------------|----------|
| Claims | 6 | 10 |
| Images per claim (avg) | 1.5 | 1.4 |
| Total images | ~9 | ~14 |

## Model calls per claim

| Step | Calls | Notes |
|------|-------|-------|
| Claim extraction | 1 text | Cached by conversation hash |
| Image analysis | N vision | One per image; cached by file path |
| Final synthesis | 0 | Rule-based in current implementation |

**Approximate total calls (test set, no cache):**

- Text calls: 10
- Vision calls: 14
- **Total: 24 model calls**

With cache on re-runs: 0 additional calls for unchanged inputs.

## Token usage estimates

| Call type | Input tokens (est.) | Output tokens (est.) |
|-----------|---------------------|----------------------|
| Text extraction | ~400 | ~100 |
| Vision per image | ~1,200 (incl. image tokens) | ~200 |

**Test set (first run):**

- Input: ~10 × 400 + 14 × 1,200 ≈ **20,800 tokens**
- Output: ~10 × 100 + 14 × 200 ≈ **3,800 tokens**

## Images processed

- Sample evaluation: **9 images**
- Full test set: **14 images**
- Vision detail level: `high` (better damage detection, higher cost)

## Cost estimate (test set)

Pricing assumptions (OpenAI, gpt-4o-mini):

| | Rate per 1M tokens |
|--|-------------------|
| Input | $0.15 |
| Output | $0.60 |

| Component | Cost |
|-----------|------|
| Input tokens (20,800) | ~$0.003 |
| Output tokens (3,800) | ~$0.002 |
| **Total per test run** | **~$0.005** |

If using `gpt-4o` for vision:

- Input ~$2.50/1M, output ~$10/1M → estimated **~$0.08–0.12** per test run.

Scaling to 1,000 claims (~1,400 images): **~$0.50** (mini) or **~$8–12** (4o).

## Latency / runtime

| Mode | Per claim | Full test (10) |
|------|-----------|----------------|
| Mock | ~0.1s | ~1s |
| API (mini) | ~3–8s | ~30–80s |
| API (4o) | ~5–12s | ~50–120s |

Bottleneck: sequential vision calls per image with rate limiting.

## TPM / RPM considerations

| Strategy | Implementation |
|----------|----------------|
| Rate limiting | `RateLimiter` — default 30 RPM |
| Retries | `tenacity` exponential backoff (3 attempts) |
| Caching | JSON cache in `.cache/` by content hash |
| Batching | Claims processed sequentially; images per claim sequential |
| Throttling | `REQUESTS_PER_MINUTE` env var |

### Recommendations for production

1. **Parallel image analysis** within a claim (respect RPM)
2. **Batch text extraction** for multiple claims in one call
3. **Downgrade to `low` image detail** for initial screening, `high` only when needed
4. **Pre-filter** corrupt/blurry images with lightweight CV before LLM
5. **Queue + worker pool** for large batches with shared rate limiter

## Evaluation results location

After running `python evaluation/evaluate.py`, see `evaluation/eval_results.json`.

## Summary

The system prioritizes **correctness over cost** with high-detail vision and per-image analysis, while caching and rate limiting keep repeated runs cheap and API-safe. For hackathon scale (10–100 claims), cost is negligible on gpt-4o-mini; latency is acceptable for batch offline processing.
