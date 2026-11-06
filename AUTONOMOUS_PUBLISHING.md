# TubeAutoma — Autonomous Psychology Channel

## Objective

Operate a faceless, synthetic-voice educational channel around everyday psychology, cognitive biases, social perception and human behaviour. The target channel title is **MARROW PSYCHOLOGY**.

The system creates original scripts, retrieves scholarly context, generates scene-specific illustrations, narrates them with Edge TTS, renders videos, validates the output, verifies the exact YouTube channel, uploads privately, waits for processing, uploads the thumbnail and only then schedules the video.

## Publishing cadence

- Four Shorts per week (Monday, Tuesday, Thursday and Saturday).
- One 8–10 minute documentary every Sunday.
- Target publish time: 6:00 PM America/New_York. Python's `zoneinfo` handles daylight-saving changes.
- Workflows serialize publishing to protect topic history and avoid overlapping renders.

## Zero-subscription design

- Gemini API: one configured free-tier model only (`gemini-3.8-flash`). Free-tier quota exhaustion stops the run; the application does not switch to another model or a paid provider.
- Narration: Edge TTS. ElevenLabs credentials are deliberately not passed to the publishing workflows.
- Research: free Europe PMC scholarly abstract lookup; relevant source links are added to video descriptions when available.
- Illustrations: Pollinations public image endpoint. Production fails closed if image generation fails; Pillow is used for test/preview fallback only.
- Editing: MoviePy, FFmpeg and Pillow on GitHub-hosted runners.
- Scheduling and source control: GitHub Actions on this public repository.
- Background music is off by default to avoid using music with unverified licensing.

This is designed to avoid paid subscriptions and API tiers. It cannot guarantee that third-party free services remain available or that an existing API key is configured without billing. Keep Google Cloud billing disabled for the Gemini project. The workflow requires `GEMINI_BILLING_DISABLED_CONFIRMED=true` as an operator attestation; code cannot independently inspect billing state. Free-tier quota exhaustion is intentionally fail-closed.

## Originality and quality controls

- Scripts use a distinct explanatory structure: relatable scenario, named concept, everyday example, nuance/limitation and practical reflection.
- Prompts prohibit invented studies, statistics, diagnoses, false certainty, fearbait and manipulation instructions.
- Script validation rejects malformed, too-short, overlong or repetitive narration and repeated visual directions.
- Psychology prompts use retrieved abstracts cautiously and prohibit fabricated study names, statistics and citations.
- Video validation checks file size, audio/video streams, H.264/AAC codecs, minimum resolution, orientation and duration (including a six-minute minimum for long-form).
- Missing narration or scene imagery stops the render. The video editor no longer silently substitutes blank or generic scenes.
- Used topics are recorded only after a successful upload.
- OAuth destination must match both the configured channel title and exact channel ID. Missing or mismatched identity stops the run.

These controls reduce avoidable failures; they cannot guarantee factual accuracy, viewer retention, YPP acceptance or revenue.

## Required existing GitHub secrets

The workflows reuse the repository's existing secrets:

- `GEMINI_API_KEY`
- `CURIOSITY_CLIENT_ID`
- `CURIOSITY_CLIENT_SECRET`
- `CURIOSITY_REFRESH_TOKEN`
- `YOUTUBE_EXPECTED_CHANNEL_ID`

The OAuth credentials must resolve to exactly one channel whose title and ID match the configured **MARROW PSYCHOLOGY** destination. The OAuth setup script prints the selected channel ID for the GitHub secret. The exact ID is supplied through the `YOUTUBE_EXPECTED_CHANNEL_ID` secret. Scheduling uses `youtube.force-ssl` because the YouTube API requires it for `videos.update`; this scope is not used for comments or unrelated account operations. Missing or mismatched identity stops the run. No credential values are stored in source control.

## Important monetization reality

YouTube reviews the channel as a whole. Mass-produced or repetitive template content can be ineligible even when AI tools are used. This project intentionally prioritizes fewer, distinct educational videos over high-volume generic uploads.

For ad revenue, the current full YPP threshold is 1,000 subscribers plus either 4,000 valid public long-form watch hours in 12 months or 10 million valid public Shorts views in 90 days. The expanded YPP tier has lower thresholds for certain fan-funding features, but it is not the same as full ad revenue eligibility. YouTube reviews channels before approval.

## Rollout

Before any Gemini call, the repository variable `GEMINI_BILLING_DISABLED_CONFIRMED` must be exactly `true`; this is an operator attestation, not a programmatic billing check. Scheduled workflows remain gated until the repository variable `YOUTUBE_AUTOPUBLISH_ENABLED` is exactly `true`. Manual workflow runs default to a private test upload with no public schedule. Enable public scheduling only after CI passes, the OAuth token has all required scopes, the exact channel ID is configured, and the private test video has finished processing and is inspected in YouTube Studio.


## Analytics reporting

The publishing engine optionally collects a 28-day video-level YouTube Analytics snapshot with views, watch time, average view duration, average percentage viewed and subscribers gained. The report exists only on the ephemeral workflow runner and is neither logged nor uploaded as an artifact nor committed to the repository. Thumbnail impressions and click-through rate are reviewed in YouTube Studio. Analytics failure is non-blocking; the system falls back to recent public video view counts. Analytics-ranked video titles and watch minutes are also fed into topic discovery when available.

The OAuth refresh token must include `https://www.googleapis.com/auth/yt-analytics.readonly`, and the YouTube Analytics API must be enabled in the same Google Cloud project. A code change cannot add permissions to an existing refresh token; reauthorize the intended channel and update the GitHub secret.


## Private audit artifacts

Each generation saves the research note, structured script and quality report under `output/` on the ephemeral runner for in-run audit. These drafts are not uploaded as artifacts or committed to the public repository. Use the private test upload in YouTube Studio to inspect the finished episode.
