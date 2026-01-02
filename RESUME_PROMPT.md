# Resume Work Prompt

**Copy and paste the following prompt to resume work on the project:**

---

I am working on the "TubeAutoma" YouTube automation project (files are in `youtube automation` folder).

**Current Goal:** Fix the Daily Meme Video workflow which is failing locally and on GitHub Actions.

**Current Issue:**
When running the script locally with `python src/main.py --category meme`, it fails with:
```
Traceback (most recent call last):
  File ".../src/main.py", line 3, in <module>
    from content import get_video_metadata, get_meme_metadata, get_long_video_metadata
  File ".../src/content.py", line 6, in <module>
    from .ypp_script_template import generate_ypp_safe_script
ImportError: attempted relative import with no known parent package
```

**Context:**
- The error is caused by the relative import `from .ypp_script_template` in `src/content.py`.
- We need to fix the import structure or the way the script is executed so that both local execution and GitHub Actions work correctly.
- The `src` directory contains `main.py`, `content.py`, `ypp_script_template.py`, etc.

**Please perform the following:**
1. Fix the `ImportError` in `src/content.py` by adjusting the import statement or setting up the `src` package correctly.
2. Verify the fix by running the script locally.
3. Ensure the fix is compatible with the GitHub Actions workflow (`.github/workflows/daily_meme.yml`).
