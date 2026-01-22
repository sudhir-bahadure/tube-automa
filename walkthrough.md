# Robust High-CTR Meme Automation System

## Summary of Changes
Implemented a "Self-Healing" and "Viral-Focused" automation pipeline for the meme niche.
Legacy code (Pytrends, Reddit scraper, random PIL visuals) was purged/bypassed in favor of a robust Gemini-centric architecture.

## 1. Viral Content Engine
*   **Source:** Google Gemini (Brainstorming Mode).
*   **Logic:** Selects 1 "Universal/Painful" topic (e.g., "When you forget your headphones") to ensure high relatability.
*   **Validation:** Checks against `assets/used_inventory.json` to guarantee 0% topic repetition.
*   **Script:** Enforced **38-word limit** with strict structure:
    *   Hook (1.5s)
    *   Situation (3s)
    *   Escalation (2s)
    *   Punchline (2s)
    *   Subscribe Hook (1.5s)

## 2. Visual Engine (Hybrid)
*   **Primary:** Gemini Visuals (Imagen 3) via `src/gemini_visual_engine.py`.
*   **Style:** "Minimalist vector art stickman, expressive face, dynamic action pose".
*   **Animation:** FFmpeg templates (`slow_zoom`, `micro_shake`, `pan_lr`) applied programmatically to create kinetic energy.
*   **Fallback:** Programmatic PIL generation (if Gemini API quota is hit).

## 3. Human-Like Audio
*   **Provider:** Edge-TTS.
*   **Voice:** `en-US-GuyNeural` (preset: Rate +8%, Pitch -2Hz).
*   **Tone:** Chat/Conversational style required to avoid "Robot" feel.

## 4. Scheduling & Upload
*   **Frequency:** 3 Shorts/Day.
*   **Schedule:** Uploads as `private`, then sets `publishAt` to +30 minutes UTC.
*   **Location:** New York, USA (Target High CPM).
*   **Privacy:** Standard YouTube Policy Compliance check included.


## 5. Curiosity Workflow Repairs (Jan 2026)
*   **Git User Config:** Switched global git user to `sudhir-bahadure` to match the repository owner for correct access permissions during workflow runs.
*   **Authentication Fix:** Created `setup_youtube_auth.py` to correctly generate Refresh Tokens for the Curiosity Channel (CurioByte), isolated from the Meme channel credentials.
*   **Token Refresh:** Successfully refreshed the YouTube API token and updated GitHub Secrets (`CURIOSITY_REFRESH_TOKEN`).
*   **Validation:**
    *   Triggered `curiosity_automation.yml` (Run ID: 21207494308).
    *   Result: **Success** (Video generated and uploaded).

## 6. Meme Workflow Optimizations (Jan 2026)
*   **Targeted Tagging:** Updated the LLM prompt to generate high-relevance tags (`#relatable`, `#pov`, `#skit`, `#comedy`) instead of generic viral tags.
*   **Category Locking:** Hardcoded the YouTube Category to **Comedy (23)** for all stickman-style videos to better target the humor audience.
*   **Compliance:** Explicitly disabled the "Altered Content" (Synthetic Media) flag to comply with transparency requirements for AI-assisted but non-misleading content.
*   **Audience Targeting:** Improved the algorithm's understanding of the niche by focusing tags and category specifically on humor rather than general entertainment.

## 7. Pro-Grade Automation Upgrades (Jan 22, 2026)
*   **Visual Dynamicism (Point 3):**
    *   Implemented **Squash & Stretch** for stickman jumping/bouncing animations.
    *   Added **Background Particles** to keep pure white backgrounds active and high-quality.
    *   Introduced **Punchline Jitters**—the screen shakes during the funniest moments for maximum emphasis.
*   **Smart Topic Selection (Point 4):**
    *   The system now **fetches view counts** of the last 10 videos via the YouTube API.
    *   It identifies "Winning Angles" and feeds this performance data back to the AI for smarter content planning.
## 8. Views Optimizer & Stability (Jan 22, 2026)
*   **Analytics-Driven Pivoting:** The system now queries the YouTube API for recent view counts. If the channel is stuck at low views, it automatically shifts from niche topics to high-energy "Viral Reset" topics to break "Shorts Jail."
*   **Viral Hook Enforcement:** Every script is now strictly forced to start with an aggressive question or a shocking statement in the first 3 seconds.
*   **JSON Resilience:** Implemented regex-based JSON extraction and a 2-attempt failure recovery loop. If the AI makes a typo or gets rate-limited, the system automatically tries again or swaps models rather than crashing.
*   **Comment Permission Guard:** Refined the uploader to handle cases where the API token only has "Upload" scope, ensuring videos post successfully even if a pinned comment is rejected by permissions.
