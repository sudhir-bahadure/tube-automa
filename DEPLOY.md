# TubeAutoma Deployment

The current automated publishing design and rollout notes are maintained in
[AUTONOMOUS_PUBLISHING.md](AUTONOMOUS_PUBLISHING.md).

## Current development status

- Work is isolated on `feature/tube-automa-2.0`.
- Pull request: https://github.com/sudhir-bahadure/tube-automa/pull/1
- `main` has not been modified by this implementation.
- Do not enable scheduled publishing until CI passes and the configured YouTube OAuth credentials are confirmed to resolve to MARROW PSYCHOLOGY.

## Required GitHub Actions secrets

- `GEMINI_API_KEY`
- `CURIOSITY_CLIENT_ID`
- `CURIOSITY_CLIENT_SECRET`
- `CURIOSITY_REFRESH_TOKEN`

The workflow uses one configured Gemini free-tier model, Edge TTS, Pollinations with a local Pillow fallback, MoviePy and FFmpeg. ElevenLabs is not used by the scheduled publishing workflows.

## Cost and quota safety

Gemini free-tier quota exhaustion is handled by stopping the workflow; the code does not fall back to another model. To avoid unexpected charges, the Google API project must remain on a free-only configuration with billing disabled. GitHub Actions and third-party free services are subject to their own availability and usage limits.

## Validation

GitHub Actions CI compiles the Python package and runs the unit tests:

```bash
python -m compileall -q src
python -m unittest discover -s tests -v
```

A passing CI run is necessary but not sufficient. The first publishing run must also confirm the destination channel and complete a successful test upload before the schedule is considered operational.

## Important

Automated publishing does not guarantee views, YPP approval or income. YouTube can reject repetitive, mass-produced or reused content even when it was generated with AI tools. See the official [YouTube monetization policies](https://support.google.com/youtube/answer/1311392).


## Optional YouTube Analytics permission

The growth-engine branch can collect read-only video-level reports when the refresh token has the scope:

`https://www.googleapis.com/auth/yt-analytics.readonly`

Existing refresh tokens do not gain new permissions merely because code requests a new scope. If the Analytics API returns an insufficient-permissions error, reauthorize the intended channel with this read-only scope and update the relevant GitHub secret. Analytics collection is optional and does not block video production. Reports are uploaded as 14-day GitHub Actions artifacts and are not committed to the public repository.
