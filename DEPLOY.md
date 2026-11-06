# TubeAutoma Deployment

The current automated publishing design and rollout notes are maintained in
[AUTONOMOUS_PUBLISHING.md](AUTONOMOUS_PUBLISHING.md).

## Current development status

- Work is isolated on `feature/tube-automa-2.0`.
- Pull request: https://github.com/sudhir-bahadure/tube-automa/pull/1
- `main` has not been modified by this implementation.
- Scheduled publishing is disabled unless the repository variable `YOUTUBE_AUTOPUBLISH_ENABLED` is exactly `true`. Before enabling it, pass CI, configure the exact `YOUTUBE_EXPECTED_CHANNEL_ID`, and complete a private test upload.

## Required GitHub Actions secrets

- `GEMINI_API_KEY`
- `CURIOSITY_CLIENT_ID`
- `CURIOSITY_CLIENT_SECRET`
- `CURIOSITY_REFRESH_TOKEN` (authorized with the scopes listed in `setup_youtube_auth.py`)
- `YOUTUBE_EXPECTED_CHANNEL_ID` (exact channel ID printed by the OAuth setup script)

The workflow uses one configured Gemini free-tier model, Edge TTS, Pollinations image generation, MoviePy and FFmpeg. Thumbnail generation uses original art plus a title overlay. No paid image, voice or video API is used.

## Cost and quota safety

Gemini free-tier quota exhaustion is handled by stopping the workflow; the code does not fall back to another model. To avoid unexpected charges, the Google API project must remain on a free-only configuration with billing disabled. GitHub Actions and third-party free services are subject to their own availability and usage limits.

## Validation

GitHub Actions CI compiles the Python package and runs the unit tests:

```bash
python -m compileall -q src
python -m unittest discover -s tests -v
```

A passing CI run is necessary but not sufficient. Run the manual workflow with `private_test_upload=true`, verify the private video, thumbnail, description, audio, visuals and processing in YouTube Studio, and only then set the repository variable `YOUTUBE_AUTOPUBLISH_ENABLED=true` to activate scheduled public releases.

## Important

Automated publishing does not guarantee views, YPP approval or income. YouTube can reject repetitive, mass-produced or reused content even when it was generated with AI tools. See the official [YouTube monetization policies](https://support.google.com/youtube/answer/1311392).
