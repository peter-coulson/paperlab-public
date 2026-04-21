# API Rate Limits & Protections

Comprehensive guide to LLM API rate limiting behavior, protections, and configuration.

---

## Overview

Both Anthropic Claude and OpenAI APIs enforce rate limits to prevent abuse and ensure fair access. Our implementation includes comprehensive protections to handle rate limits gracefully.

**Key principle:** Fail gracefully with automatic retries, never crash on rate limit errors.

---

## API Tier Structure

### Anthropic Claude API Tiers

| Tier | Requests/Min | Tokens/Min | How to Qualify |
|------|-------------|------------|----------------|
| **Tier 1** (default) | 50 | 50,000 | Default for new accounts |
| **Tier 2** | 1,000 | 200,000 | Usage threshold + deposit |
| **Tier 3** | 2,000 | 400,000 | Higher usage threshold |
| **Tier 4** | 4,000 | 400,000 | Highest tier |

**Check your tier:** https://console.anthropic.com/settings/limits

### OpenAI API Tiers

| Tier | Requests/Min (GPT-4o) | Advancement Criteria |
|------|----------------------|---------------------|
| **Tier 1** (default) | 500 | Default for new accounts |
| **Tier 2** | 5,000 | $50 spent + 7 days |
| **Tier 3** | 10,000 | $100 spent + 7 days |
| **Tier 4** | 30,000 | $250 spent + 14 days |
| **Tier 5** | 60,000 | $1,000 spent + 30 days |

**Check your tier:** https://platform.openai.com/account/limits

### Google Gemini API Tiers

| Tier | Requests/Min | Tokens/Min | Pricing |
|------|-------------|------------|---------|
| **Free Tier** | 15 | 1,000,000 | Free (rate limited) |
| **Pay-as-you-go** | 2,000 | 4,000,000 | $0.10/1M input, $0.40/1M output |

**Gemini 2.0 Flash pricing:** ~25-37x cheaper than GPT-4o or Claude

**Check your quota:** https://aistudio.google.com/apikey

---

## Rate Limit Protection Mechanisms

### 1. Provider-Specific Worker Counts

**Configuration:** Automatic provider detection with optimized defaults

**Anthropic Claude:**
- `settings.batch_max_workers_anthropic = 5` (default for Tier 1)
- 5 workers × 2 requests/min/worker = ~10 requests/min average
- **Tier 1:** 50 req/min → 20% utilization (safe)

**OpenAI:**
- `settings.batch_max_workers_openai = 50` (default for Tier 1)
- 50 workers × 2 requests/min/worker = ~100 requests/min average
- **Tier 1:** 500 req/min → 20% utilization (safe)

**Google Gemini:**
- `settings.batch_max_workers_google = 200` (default for pay-as-you-go)
- 200 workers × 2 requests/min/worker = ~400 requests/min average
- **Pay-as-you-go:** 2000 req/min → 20% utilization (safe with headroom)
- Note: Free tier has 15 req/min limit; set workers to 2 if using free tier

**How it works:**
- BatchMarker auto-detects provider from `llm_client.provider_name`
- Selects appropriate worker count automatically
- No manual configuration needed for optimal performance

**Rationale:**
- OpenAI has 10x higher rate limits → can use 10x more workers
- Maintains same 20% safety margin for both providers
- Optimizes performance without risking rate limits

### 2. Exponential Backoff with Jitter

**Location:** `src/paperlab/services/llm_client.py:227-295`

**Retry behavior with random jitter:**
```
Attempt 1: Send request immediately
  └─ Rate limit error (429) → catch LLMRateLimitError

Attempt 2: Wait 0.5-1.5s (1s ± 50% jitter), retry
  └─ Rate limit error (429) → catch LLMRateLimitError

Attempt 3: Wait 1.0-3.0s (2s ± 50% jitter), retry
  └─ Rate limit error (429) → catch LLMRateLimitError

Attempt 4: Wait 2.0-6.0s (4s ± 50% jitter), retry
  └─ Success or final failure
```

**Key improvement: Random jitter prevents thundering herd**
- Multiple workers hitting rate limits don't retry simultaneously
- Workers naturally desynchronize after first retry
- Distributes load over time instead of synchronized bursts
- Industry standard (AWS, Google, Stripe all use jittered backoff)

**Configuration:**
- `settings.llm_max_retries = 3` (default)
- Retryable errors: `LLMRateLimitError`, `LLMTimeoutError`
- Non-retryable: `LLMAuthenticationError`, `LLMInvalidRequestError`

### 3. Per-Worker Independence

**Pattern:** Each worker handles its own retries independently

**Benefits:**
- Workers don't block each other during retries
- Rate limit recovery is distributed (not synchronized)
- Natural throttling as workers wait different durations

---

## Common Scenarios

### Normal Operation (Well Within Limits)

**Setup:** 50 test questions, default workers, Tier 1 limits

**Result:**
- Anthropic (5 workers): ~5 minutes, no rate limit hits
- OpenAI (50 workers): ~30 seconds, no rate limit hits

### Occasional Rate Limit Hit

**What happens:**
- Workers hit rate limit (429 error)
- Each waits jittered backoff time (0.7s, 1.1s, 1.3s different)
- Workers retry at staggered times (no thundering herd)
- Minor delays, batch continues successfully

**Result:** Workers naturally desynchronize, preventing cascading failures

### Sustained Rate Limiting (Misconfigured)

**Setup:** `max_workers` set too high for tier

**What happens:**
- Initial burst exceeds rate limit
- Multiple workers hit 429 errors
- Jittered backoff staggers retries
- Some succeed as earlier workers complete
- Failed questions reported in `BatchMarkingResult.failed`

**Result:** Partial failures, batch does NOT crash

---

## Configuration Guide

### For Tier 1 Users (Default - No Configuration Needed!)

**Automatic provider detection:**
- Anthropic: 5 workers (auto-detected)
- OpenAI: 50 workers (auto-detected)

**Manual override (optional):**
```bash
# .env file (only if you want to override defaults)
PAPERLAB_BATCH_MAX_WORKERS_ANTHROPIC=5   # Anthropic default
PAPERLAB_BATCH_MAX_WORKERS_OPENAI=50     # OpenAI default
```

**Expected performance:**
- Anthropic: 5x speedup, 50-question suite in ~5 minutes
- OpenAI: 50x speedup, 50-question suite in ~30 seconds

### For Tier 2+ Users (Higher Limits)

**Anthropic Tier 2:**
```bash
PAPERLAB_BATCH_MAX_WORKERS_ANTHROPIC=30  # 1000 req/min ÷ 30 = 33 req/min
```

**Anthropic Tier 3-4:**
```bash
PAPERLAB_BATCH_MAX_WORKERS_ANTHROPIC=60  # 2000-4000 req/min ÷ 60 = 33-66 req/min
```

**OpenAI Tier 2:**
```bash
PAPERLAB_BATCH_MAX_WORKERS_OPENAI=500  # 5000 req/min ÷ 500 = 100 req/min
```

**OpenAI Tier 3+:**
```bash
PAPERLAB_BATCH_MAX_WORKERS_OPENAI=1000  # 10000+ req/min ÷ 1000 = 100+ req/min
```

**Expected performance:**
- Anthropic Tier 2-4: 30-60x speedup, 50 questions in ~30-60 seconds
- OpenAI Tier 2+: 500-1000x speedup, 50 questions in ~6-12 seconds

### For Debugging Rate Limit Issues

**Temporary sequential execution:**
```bash
PAPERLAB_BATCH_MAX_WORKERS_ANTHROPIC=1  # Force sequential for Anthropic
PAPERLAB_BATCH_MAX_WORKERS_OPENAI=1     # Force sequential for OpenAI
```

**Purpose:** Isolate whether issue is rate-limiting or other problem, see exact order of operations

---

## Monitoring & Debugging

### Check Current Tier

**Anthropic:**
- Console: https://console.anthropic.com/settings/limits
- Shows: Current tier, limits, usage

**OpenAI:**
- Console: https://platform.openai.com/account/limits
- Shows: Current tier, limits, usage

### Rate Limit Errors in Logs

**Error pattern:**
```
LLMError: Failed after 4 attempts: Anthropic rate limit exceeded: ...
```

**Action:**
1. Check if `max_workers` too high for your tier
2. Reduce `PAPERLAB_BATCH_MAX_WORKERS` in `.env`
3. Verify no other processes using same API key concurrently
4. Check account limits in provider console

### Successful Retry Pattern

**Log output (normal):**
```
[Worker 3] Rate limit hit on attempt 1, retrying in 1s...
[Worker 3] Retry successful on attempt 2
```

**Action:** None needed, system working as designed

---

## Best Practices

1. **Use default `max_workers` unless you know your tier**
   - Default is safe for Tier 1
   - Only increase after confirming higher tier

2. **Set `max_workers` conservatively**
   - Use 20% of rate limit, not 100%
   - Leaves headroom for bursts and other operations

3. **Monitor failures in `BatchMarkingResult`**
   - Check `result.failed` for errors
   - Distinguish rate limits from other failures
   - Retry failed questions if needed

4. **Don't run multiple batch operations concurrently**
   - Each batch uses up to `max_workers` API connections
   - Two batches = 2× the request rate
   - Can exceed limits even with safe `max_workers`

5. **Test with small batches first**
   - Start with 5-10 questions
   - Verify no rate limit errors
   - Scale up gradually

---

## Summary

**Protection mechanisms:**
- ✅ Provider-specific worker counts (automatic detection)
  * Anthropic: 5 workers (Tier 1 default)
  * OpenAI: 5 workers (Tier 1 default)
  * Google: 200 workers (pay-as-you-go default)
- ✅ Exponential backoff with jitter (prevents thundering herd)
- ✅ Per-worker independence (distributed recovery)
- ✅ Error isolation (failures don't stop batch)
- ✅ Comprehensive error reporting

**Key improvements:**
- 🚀 **10x better OpenAI performance** (5 → 50 workers for Tier 1)
- 🎯 **No thundering herd** (jittered backoff desynchronizes workers)
- 🤖 **Zero configuration** (automatic provider detection)
- 📈 **Optimal defaults** (20% utilization for both providers)

**Guaranteed behavior:**
- ✅ Batch waits for ALL questions to complete
- ✅ Rate limit errors trigger automatic jittered retries
- ✅ Failed questions reported in result (never silent failure)
- ✅ No crashes on rate limits (graceful degradation)
- ✅ Workers naturally desynchronize on rate limit recovery
