# MARROW PSYCHOLOGY — TubeAutoma

A zero-subscription-by-design publishing pipeline for **MARROW PSYCHOLOGY**.

The project is focused on original, evidence-aware psychology explainers. It is not a generic mass-upload bot. Other channel automations in this repository are hobby work and are not part of this production path.

## What it produces

- One original 8–12 minute landscape explainer each week.
- Four distinct vertical Shorts each week.
- English narration via Edge TTS.
- Original scene-specific illustrations and 16:9 title-overlaid thumbnails.
- Europe PMC research context and source links where available.
- Script, media and technical quality gates.
- Optional read-only YouTube Analytics feedback to inform future topic selection.

## Safety defaults

- No paid model, voice, image or video API fallback.
- Gemini generation stops unless the repository variable `GEMINI_BILLING_DISABLED_CONFIRMED=true` is set after the owner has manually disabled Google Cloud billing.
- YouTube upload requires both the exact channel title and `YOUTUBE_EXPECTED_CHANNEL_ID`.
- Manual workflow runs default to a private test upload.
- A video is uploaded privately, processing is awaited, the thumbnail is validated and uploaded, and only then can it be scheduled.
- Scheduled public publishing stays disabled unless `YOUTUBE_AUTOPUBLISH_ENABLED=true`.
- Failed narration, missing visuals, invalid video output or thumbnail failure stop publication.
- Private Analytics data is used only on the ephemeral workflow runner; it is not logged, uploaded as an artifact or committed to this public repository.

## Setup

1. Read [DEPLOY.md](DEPLOY.md) and [AUTONOMOUS_PUBLISHING.md](AUTONOMOUS_PUBLISHING.md).
2. Create a Google AI Studio API key for the free tier. Disable billing on the associated Google Cloud project before setting the billing confirmation variable.
3. Enable YouTube Data API v3 and YouTube Analytics API. Set the OAuth consent screen to Production (not Testing) and complete any required Google verification; Testing-mode refresh tokens expire after seven days. Run `python setup_youtube_auth.py` locally using the Google account that owns MARROW PSYCHOLOGY. Confirm the printed channel title and ID.
4. Add the required GitHub Actions secrets: `GEMINI_API_KEY`, `CURIOSITY_CLIENT_ID`, `CURIOSITY_CLIENT_SECRET`, `CURIOSITY_REFRESH_TOKEN`, and `YOUTUBE_EXPECTED_CHANNEL_ID`.
5. Add repository variable `GEMINI_BILLING_DISABLED_CONFIRMED=true` only after confirming billing is disabled.
6. Run the appropriate workflow manually with `private_test_upload=true`. Inspect the private video in YouTube Studio.
7. Only after successful inspection, set repository variable `YOUTUBE_AUTOPUBLISH_ENABLED=true` to activate the scheduled publishing workflows.

Do not commit API keys, refresh tokens, analytics snapshots or private drafts.

## Validation

Run `python -m compileall -q src` and `python -m unittest discover -s tests -v`.

The test suite includes an actual short MP4 render smoke test. CI passing is not a substitute for the first private upload and YouTube Studio inspection.

## Business strategy

See [GROWTH_STRATEGY_2026.md](GROWTH_STRATEGY_2026.md) for the 90-day publishing experiment, editorial standards, YPP targets and analytics interpretation.

YouTube monetization is not guaranteed. The channel must meet current YPP eligibility and pass whole-channel review. Original educational value—not upload volume—is the product.
