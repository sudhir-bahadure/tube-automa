# TubeAutoma 2.0

The current autonomous, faceless YouTube publishing design is documented in
[AUTONOMOUS_PUBLISHING.md](AUTONOMOUS_PUBLISHING.md).

This branch focuses on one educational channel and a controlled production pipeline:

- One original psychology Short per day.
- One long-form psychology documentary per week.
- Synthetic narration, original illustrated visuals and free scholarly source lookup.
- Free-tier-only Gemini usage with fail-closed quota handling.
- Script originality and rendered-video quality gates.
- YouTube destination verification before production and upload.
- Topic history recorded only after successful upload.
- No paid voice API or unverified background music.

See [DEPLOY.md](DEPLOY.md) for the development and rollout status. The branch is not live until the pull request is merged and the first CI and YouTube destination checks pass.
