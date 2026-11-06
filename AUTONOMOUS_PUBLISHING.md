# TubeAutoma — Autonomous Psychology Channel

## Objective

Operate a faceless, synthetic-voice educational channel around everyday psychology, cognitive biases, social perception and human behaviour. The target channel title is **MARROW PSYCHOLOGY**.

The system creates original scripts, generates illustrated scenes, narrates them with Edge TTS, renders videos, validates output, verifies the YouTube destination, uploads and schedules automatically.

## Publishing cadence

- One Short every day.
- One 8–10 minute documentary every Sunday.
- Target publish time: 6:00 PM America/New_York. Python's `zoneinfo` handles daylight-saving changes.
- Workflows serialize publishing to protect topic history and avoid overlapping renders.

## Zero-subscription design

- Gemini API: one configured free-tier model only (`models/gemini-3.8-flash`). Free-tier quota exhaustion stops the run; the application does not switch to another model or a paid provider.
- Narration: Edge TTS. ElevenLabs credentials are deliberately not passed to the publishing workflows.
- Illustrations: Pollinations public image endpoint with a locally generated Pillow fallback.
- Editing: MoviePy, FFmpeg and Pillow on GitHub-hosted runners.
- Scheduling and source control: GitHub Actions on this public repository.
- Background music is off by default to avoid using music with unverified licensing.

This is designed to avoid paid subscriptions and API tiers. It cannot guarantee that third-party free services remain available or that an existing API key is configured without billing. Keep Gemini billing disabled in Google AI Studio/Cloud if an absolute zero-charge guarantee is required; free-tier quota exhaustion is intentionally fail-closed.

## Originality and quality controls

- Scripts use a distinct explanatory structure: relatable scenario, named concept, everyday example, nuance/limitation and practical reflection.
- Prompts prohibit invented studies, statistics, diagnoses, false certainty, fearbait and manipulation instructions.
- Script validation rejects malformed, too-short, overlong or repetitive narration and repeated visual directions.
- Video validation checks file size, audio/video streams, duration and portrait orientation for Shorts.
- Missing narration stops the run. Missing generated imagery falls back to original local illustrations.
- Used topics are recorded only after a successful upload.
- OAuth destination is checked against the configured channel title before production/upload.

These controls reduce avoidable failures; they cannot guarantee factual accuracy, viewer retention, YPP acceptance or revenue.

## Required existing GitHub secrets

The workflows reuse the repository's existing secrets:

- `GEMINI_API_KEY`
- `CURIOSITY_CLIENT_ID`
- `CURIOSITY_CLIENT_SECRET`
- `CURIOSITY_REFRESH_TOKEN`

The OAuth credentials must resolve to a YouTube channel whose title is exactly **MARROW PSYCHOLOGY** (case-insensitive). If they resolve to another channel, the workflow stops before generating or uploading. No credential values are stored in source control.

## Important monetization reality

YouTube reviews the channel as a whole. Mass-produced or repetitive template content can be ineligible even when AI tools are used. This project intentionally prioritizes fewer, distinct educational videos over high-volume generic uploads.

For ad revenue, the current full YPP threshold is 1,000 subscribers plus either 4,000 valid public long-form watch hours in 12 months or 10 million valid public Shorts views in 90 days. The expanded YPP tier has lower thresholds for certain fan-funding features, but it is not the same as full ad revenue eligibility. YouTube reviews channels before approval.

## Rollout

This branch is not live until the pull request is merged. Before enabling scheduled publishing, confirm that the existing OAuth secrets point to MARROW PSYCHOLOGY and that the first GitHub Actions run passes. The code will stop rather than silently publish to a different channel.
