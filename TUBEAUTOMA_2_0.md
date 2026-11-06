# TubeAutoma 2.0 — Development Branch

This branch contains incremental reliability improvements. The production `main` branch is unchanged.

## Changes in this branch

- Adds a pre-upload quality gate using FFprobe to check that rendered videos exist, contain both audio and video streams, have valid duration and dimensions, and use portrait dimensions for Shorts.
- Records automatically selected topics only after the YouTube upload succeeds. A failed render or upload no longer consumes the topic.
- Fixes missing `os` imports in image cleanup and audio post-processing paths.
- Serializes the three meme matrix jobs to reduce concurrent writes to the shared topic-history file.
- Adds unit tests and a CI workflow for Python compilation and quality-gate tests.

## Automatic publishing

The existing workflow continues to upload and schedule videos automatically using the configured GitHub Actions secrets. The quality gate runs before the upload code. If validation fails, the job exits without uploading.

Required secrets remain the responsibility of the repository owner. Never commit API keys, OAuth refresh tokens, client secrets, or local `.env` files.

## Validation

CI runs:

```bash
python -m compileall -q src
python -m unittest discover -s tests -v
```

## Rollout

1. Review this branch and its CI results.
2. Run a manual workflow test with a test channel or controlled upload configuration.
3. Verify YouTube scheduling, thumbnails, and topic-history updates.
4. Merge the pull request only after those checks pass.

No claim of successful YouTube publishing is made by this code change alone; live publishing still depends on valid credentials, quota, channel status, and successful GitHub Actions runs.
