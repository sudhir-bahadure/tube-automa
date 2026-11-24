# Free AI fallback setup

Tube Automa routes script requests through this order:

1. Gemini 3.8 Flash.
2. Gemini 3.5 Flash-Lite, if the Google project exposes it.
3. Groq `openai/gpt-oss-20b`, only when `GROQ_API_KEY` and the repository variable `GROQ_FREE_TIER_CONFIRMED=true` are present.
4. Cloudflare Workers AI `@cf/zai-org/glm-4.7-flash`, only when the account ID, API token, and `CLOUDFLARE_WORKERS_FREE_CONFIRMED=true` are present.

Gemini uses one script-generation request per video. Topic selection comes from the curated queue in `src/topic_bank.py`, avoiding a separate model request. The queue uses past successful topics to prevent repeats and may use recent channel/competitor titles only as broad category signals. It does not claim that a topic is currently trending.

## Cost safeguards

- Keep the Gemini API project on its Free tier with Google Cloud billing disabled. The workflow already requires `GEMINI_BILLING_DISABLED_CONFIRMED=true` when a Gemini key is configured.
- Only add Groq credentials while the account is on Groq's Free tier. Do not upgrade it or add a payment method for this automation. Set `GROQ_FREE_TIER_CONFIRMED=true` only after checking the account.
- Groq free quotas are organization-level and may change. Check the [current rate-limit table](https://console.groq.com/docs/rate-limits) before relying on a limit; the current `openai/gpt-oss-20b` free quota is 30 requests/minute, 1,000 requests/day, 8,000 tokens/minute, and 200,000 tokens/day. A 429 is not retried against the same provider; the code continues to the next configured free route.
- Only add Cloudflare credentials while using Workers Free and a model that does not require a paid plan. Set `CLOUDFLARE_WORKERS_FREE_CONFIRMED=true` only after checking the account. If the daily free allocation is exhausted, the free plan should fail the request instead of upgrading automatically.
- Workers AI Free currently includes 10,000 Neurons per day; on Workers Free, requests fail after the free allocation rather than switching to paid usage. Check [Cloudflare Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) before changing plans or models.
- The Cloudflare fallback uses `@cf/zai-org/glm-4.7-flash`. The previously configured Llama 3.1 model is deprecated; recheck the [model catalog](https://developers.cloudflare.com/workers-ai/models/) periodically.
- Do not put credentials in source files, logs, or chat. Add API credentials as GitHub Actions secrets; add the confirmation flags as repository variables.
- Never enable a paid fallback. If every configured free route is unavailable, generation stops and no video is uploaded.

Free quotas and model availability can change. Check each provider's current account page and pricing before adding credentials. Code-level flags are safeguards against accidental activation, not proof of an account's billing tier.

## GitHub repository settings

Optional secrets:

- `GROQ_API_KEY`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`

Optional variables, each defaulting to disabled:

- `GROQ_FREE_TIER_CONFIRMED`
- `CLOUDFLARE_WORKERS_FREE_CONFIRMED`

Keep `GEMINI_BILLING_DISABLED_CONFIRMED=true` only while the Gemini project's billing remains disabled. Keep `YOUTUBE_AUTOPUBLISH_ENABLED` unset or `false` until the private test and quality review are complete.
