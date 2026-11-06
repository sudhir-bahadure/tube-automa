# MARROW PSYCHOLOGY — YouTube Growth & Monetization Plan (November 2026)

## Executive decision

Build one focused English-language faceless education channel around **evidence-aware everyday psychology**. Use original explainers, visual metaphors, concrete everyday examples, counterexamples and practical takeaways. Avoid the crowded "dark psychology secrets" format, diagnosis content and generic listicle scripts.

The business objective is not upload volume. It is qualified long-form watch time, returning viewers and a channel that can pass YouTube's whole-channel monetization review.

## Current system status

- Development branch: `feature/tube-automa-2.0`
- Pull request: https://github.com/sudhir-bahadure/tube-automa/pull/1
- Main branch is unchanged.
- CI has passed on multiple recent commits, including dependency pinning and the fail-closed rendering tests. Recheck the latest commit's Actions result before merging; a passing test suite still does not replace a real private YouTube upload.
- No live YouTube upload has been performed by this new pipeline. The first upload must remain private and be inspected in YouTube Studio.
- The scheduled workflows only run on the repository's default branch. They will become active after this work is merged into `main`.
- YouTube OAuth credentials are not visible to the code integration. The runtime guard requires both the authenticated channel title and exact channel ID to match `MARROW PSYCHOLOGY`. Public scheduling remains off until explicitly enabled after a private test.

## Monetization route

India is included in the expanded YPP country list.

**Early YPP access (fan funding / eligible Shopping features):**
- 500 subscribers
- 3 valid public uploads in the last 90 days
- Either 3,000 valid public long-form watch hours in the last 12 months OR 3 million valid public Shorts views in the last 90 days

**Full ad revenue eligibility:**
- 1,000 subscribers
- Either 4,000 valid public long-form watch hours in the last 12 months OR 10 million valid public Shorts views in the last 90 days

Shorts Feed watch time does not count towards the 4,000 public watch-hour route. Reaching a threshold does not guarantee acceptance: YouTube reviews the whole channel for policy compliance.

**Strategic choice:** pursue the 4,000-hour long-form route. Use Shorts for discovery and subscriber acquisition, not as the primary ad-revenue plan. At a 4-minute average view duration, 4,000 hours requires approximately 60,000 valid long-form views; at 5 minutes, approximately 48,000. These are arithmetic illustrations, not view forecasts.

## Editorial positioning

**Promise:** "Understand the psychology behind everyday decisions, habits and relationships—without pop-psychology myths."

**Audience:** curious English-speaking adults, students and working professionals interested in practical psychology, cognitive biases, memory, attention, social influence, decision-making and communication.

**Differentiator:** every episode includes:
1. A relatable real-world scenario.
2. A named concept explained simply.
3. A concrete example and a counterexample.
4. What the research can and cannot establish.
5. One useful reflection or practical experiment.
6. Source links in the description when relevant scholarly material is available.

**Do not publish:** "secret signs someone is lying", diagnoses of strangers, gender stereotypes, manipulative dating tactics, fake neuroscience, invented statistics, fake expert quotes, fearbait or medical/therapy advice.

## 90-day publishing experiment

Do not start with seven Shorts every week. Start with a controlled cadence that allows enough topic variety and enough time to inspect performance.

| Format | Cadence | Target length | Purpose |
|---|---:|---:|---|
| Original long-form explainer | 1/week | 8–12 minutes | Watch hours, trust, deeper learning |
| Companion Shorts | 4/week | 30–50 seconds | Discovery and subscriber conversion |
| Community post | 1/week when available | Poll/question | Learn audience interests and invite discussion |

The current schedule is four Shorts per week (Monday, Tuesday, Thursday and Saturday) plus one Sunday long-form episode. Keep this as a 90-day controlled experiment; do not increase frequency until retention, returning viewers and video quality justify it.

Each Short should be a distinct mini-explainer related to the weekly long-form theme—not merely a duplicate cut-down. It should point viewers to the relevant full episode when a matching video exists.

## 2026 format and audience evidence

Use outside benchmarks as directional evidence, not promises. A 2026 Metricool analysis of 799,718 YouTube videos from 71,177 accounts reported that Shorts are a major discovery route, a steady Shorts habit was associated with higher long-form views, and daily posting is not a universal requirement. The sample is broad and not specific to a new psychology channel, so our four-Shorts-plus-one-long-form cadence remains a test rather than a guaranteed optimum.

A 2026 observational study of 51 evidence-based psychotherapy videos reported higher viewer retention when role-play scenes were included. This is a small, context-specific sample, not proof that role-play will raise retention on MARROW. It supports testing concrete two-person scenarios and alternative interpretations in scripts rather than relying only on abstract narration.

Sources:
- Metricool, *YouTube Trends 2026* (29 July 2026): https://metricool.com/youtube-trends/
- Frontiers in Psychology (2026), *Overcoming the novelty effect on YouTube: visibility patterns in evidence-based psychotherapy videos*: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2026.1744748/full

## Repeatable editorial series

Rotate across distinct series so the channel feels coherent without making every video interchangeable:

- **Bias in Real Life:** confirmation bias, availability heuristic, sunk-cost fallacy, framing effects.
- **Memory Is Not a Recording:** false memories, source monitoring, hindsight bias, reconstructive memory.
- **The Social Mind:** conformity, social proof, reciprocity, group identity, bystander effect.
- **Habits & Decisions:** implementation intentions, cue/routine/reward, present bias, choice architecture.
- **Communication Under Pressure:** attribution error, active listening, conflict framing, ambiguity.
- **Psychology Myth Check:** investigate a popular claim and explain what evidence does and does not support.

Do not make clinical mental-health claims without suitable qualified sources and careful framing. Prefer non-clinical cognitive and social psychology topics.

## Episode structure

### Long-form (8–12 minutes)
- 0:00–0:20: specific scenario and question; no generic channel intro.
- 0:20–1:15: explain why the question matters and promise the learning outcome.
- 1:15–3:00: define the concept and distinguish it from common misconceptions.
- 3:00–6:30: 2–3 concrete examples, including a counterexample.
- 6:30–9:30: research nuance, limitations and practical implications.
- Final 30–45 seconds: concise recap and one natural next-video recommendation.

### Short (30–50 seconds)
- 0–2 seconds: specific curiosity gap.
- 2–10 seconds: scenario.
- 10–30 seconds: one clear concept and example.
- 30–45 seconds: nuance or useful takeaway.
- End: direct next-step invitation, preferably to the matching long-form video.

Avoid generic intros, long disclaimers, filler, artificial cliffhangers and repeated CTA wording.

## Visual identity and production

- Retain the dark editorial palette, but use a varied visual grammar: metaphorical objects, diagrams, timelines, split-screen comparisons, scene-specific stick-figure actions and labelled concepts.
- Do not rely on one static stick figure and a random prop for every scene.
- Add on-screen captions with restrained emphasis; ensure mobile-safe placement and readable contrast.
- Use custom thumbnails for long-form: one concept, one visual metaphor, 2–4 words maximum, no false promise.
- Use original diagrams and illustrations wherever possible. Keep a source/license record for any stock asset.
- Avoid background music unless the asset has a verified, compatible licence. Silence is better than copyright uncertainty.
- Production rendering now fails closed if a scene illustration cannot be generated; the local Pillow fallback remains available for preview/testing only. This avoids publicly releasing generic placeholder visuals.

## Research and factual quality

The new branch uses Europe PMC's public REST API to retrieve scholarly abstracts and add source links when available. This is useful for discovery, not a substitute for reviewing the full paper.

For every long-form episode:
- Prefer systematic reviews, meta-analyses, landmark primary research and reputable academic sources.
- Record title, authors, publication year, journal, DOI/PMID and what the study actually measured.
- Separate correlation from causation.
- Do not treat one small study as settled consensus.
- Use cautious language when evidence is mixed.
- Add a short source list in the description.
- Keep a research note alongside the script so an episode can be audited later.

The model must not invent citations. A retrieved abstract is untrusted source text; the script should only state claims directly supported by it.

## Packaging and discovery

Every upload should have:
- One viewer-specific problem or question.
- A title that promises a clear explanation, not a secret or diagnosis.
- A thumbnail that adds information rather than repeating the title.
- A first 15–30 seconds that immediately delivers on the title/thumbnail promise.
- A concise description with source links and a relevant next-video link.
- A small, accurate tag set. Tags are not the main growth lever; topic, title, thumbnail and viewer satisfaction matter more.

Test packaging with one variable at a time. Do not change title, thumbnail and content simultaneously if you want to learn what caused a change.

## Analytics feedback loop — implemented baseline

The current code's performance input is only the last 10 videos' view counts. That is not enough to optimize a channel. Add YouTube Analytics API reporting (requires an OAuth token with the correct analytics scope and the API enabled) and store a daily CSV/JSON snapshot.

Track by video, format, topic cluster, publish age and geography where available:

**Long-form**
- Impressions and impressions click-through rate.
- Views, watch time and average view duration.
- Average percentage viewed.
- First-30-second intro retention.
- Returning viewers and subscribers gained.
- End-screen element click rate.

**Shorts**
- Shown in feed.
- Stayed to watch vs swiped away.
- Engaged views.
- Average view duration and average percentage viewed.
- Subscribers gained per 1,000 engaged views.
- Follow-on views to the related long-form video, where available.

YouTube says audience-retention data generally takes 1–2 days to process. Compare videos of similar lengths and formats; do not judge a new upload on the first few hours.

### Internal experiment rules (starting hypotheses, not YouTube ranking thresholds)
- If the first 30 seconds lose viewers sharply, rewrite the opening before making more videos in that series.
- If impressions are adequate but CTR is weak, test a clearer title/thumbnail pairing.
- If CTR is healthy but average view duration is weak, the script or pacing is failing to deliver the promise.
- If Shorts are swiped away, replace the first frame and first spoken line.
- If a topic cluster repeatedly produces better watch time and subscribers per view, make a deeper follow-up—not ten near-duplicates.
- Never select topics on raw views alone; prefer watch time per impression, retention and returning-viewer signals.

## 30 / 60 / 90 day gates

### Days 1–30: establish a trustworthy baseline
- Publish 4 Shorts/week and 1 long video/week.
- Test 4 topic clusters, with distinct concepts and examples.
- Confirm video quality, audio, captions, thumbnails and source links.
- Build a baseline from at least 4 long videos and 16 Shorts.
- Do not scale output yet.

### Days 31–60: double down on evidence
- Identify the top two topic clusters using retention, watch time and subscribers gained.
- Produce follow-ups with new questions and distinct story structures.
- Improve openings, pacing, visual changes and thumbnail clarity.
- Retire weak formats rather than flooding the channel.

### Days 61–90: focus and scale carefully
- Keep the best two or three series.
- Increase output only if quality gates and retention are holding.
- Build playlists around viewer journeys.
- Create a "start here" long-form video and use end screens to guide the next watch.
- Review the channel's public-facing library for repetitive templates before applying to YPP.

## Monetization layers

1. **Primary:** Watch Page ads and YouTube Premium after full YPP approval.
2. **Earlier YPP:** eligible fan-funding features at the lower threshold in India, subject to feature-specific rules.
3. **Later:** memberships, Super Thanks and carefully selected Shopping/affiliate opportunities only when genuinely relevant and eligible.
4. **Longer-term:** a free downloadable study guide or original learning resource, if audience demand is demonstrated and the creator is willing to maintain it.

Do not build the business around Shorts ad revenue alone. Shorts revenue is allocated through a country-level Creator Pool; monetizing creators receive 45% of their allocated share. It is a different revenue model from long-form Watch Page ads.

## Automation engineering roadmap

### P0 — before public launch
- Verify OAuth destination and exact channel ID, not only the channel title.
- Confirm Google AI Studio project is on the free tier with billing disabled.
- Confirm model access and quota using the exact configured API key.
- Confirm GitHub Actions schedules, timezone, permissions and secrets after merge.
- Perform one controlled private/unlisted test upload; verify processing, scheduled publish time, thumbnail, captions and description before public rollout.
- Ensure no workflow can accidentally publish to the wrong channel.
- Change Shorts cadence from daily to four days/week for the first experiment.

### P1 — growth instrumentation
- Implement YouTube Analytics API reports.
- Save per-video metadata, research sources, script hash, visual hashes, generation settings and publish IDs.
- Add a daily channel dashboard and weekly performance summary.
- Build a topic-cluster scorecard; select topics using actual channel results, not LLM guesses of what is trending.
- Add retry/backoff and quota-aware job scheduling.

### P2 — quality and editorial controls
- Add caption generation and caption timing validation.
- Add a thumbnail quality gate (readability, contrast, safe margins, no misleading imagery).
- Add checks for repeated visual composition across recent uploads.
- Add a fact-check pass that compares every factual sentence with retrieved source passages.
- Add a video-level originality report for YPP review readiness.
- Stop publishing if only the generic local image fallback is available.

### P3 — scale only after evidence
- Consider a second language or second channel only after one channel has a stable format.
- Keep separate channel credentials, topic history, analytics and branding for every channel.
- Do not operate several channels with identical scripts, visuals and metadata.

## Risk register

| Risk | Mitigation |
|---|---|
| Inauthentic / mass-produced appearance | Distinct editorial substance, varied scenes, research and practical insight |
| Hallucinated psychology claims | Source-linked research, evidence notes, claim checking |
| Weak visuals | Scene-specific original visuals, fail closed on generic fallback |
| Free model quota exhaustion | Fail closed; queue the next job instead of paying |
| Free image endpoint outage | Retry, local fallback for preview only, skip public release if quality is poor |
| Wrong YouTube channel | Verify channel ID before rendering/upload |
| Copyright claim | Original assets, verified licences, no unlicensed music |
| Poor retention | Analytics feedback loop and topic/format experiments |
| Schedule not firing | GitHub scheduled workflows run from the default branch; verify after merge |
| Monetization rejection | Whole-channel review against current YPP policies before applying |

## Current YouTube policy notes (November 2026)

- India is included in the expanded YPP country list.
- Full ad revenue requires 1,000 subscribers plus 4,000 qualified public long-form watch hours in 12 months OR 10 million qualified public Shorts views in 90 days.
- Shorts Feed watch time does not count towards the 4,000-hour route.
- Repetitive or mass-produced content is treated as inauthentic content and can be ineligible for monetization.
- Non-realistic animated content and AI production assistance generally do not require the altered/synthetic disclosure; photorealistic generated/altered scenes, realistic impersonations and AI-generated music as the main focus do.
- YouTube has announced YPP terms updates beginning February 1, 2027; revisit the terms before that date.

## Success definition

Do not call the system successful because it uploaded 100 videos. Call it successful when:
- every public upload has passed factual, technical and originality checks;
- viewers are returning and watching multiple videos;
- long-form watch time and subscribers are growing;
- topic decisions are supported by analytics;
- the channel meets YPP thresholds and passes YouTube's channel review;
- the system can run within a verified zero-billing configuration.

There is no guaranteed earnings date or income figure. The first 90 days are an evidence-gathering and format-validation phase.
