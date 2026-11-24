import os
import json
import logging
import math
from src.topic_bank import TOPIC_BANK

logger = logging.getLogger(__name__)


class TrendEngine:
    def __init__(self, used_topics_path="output/used_topics.json"):
        self.used_topics_path = used_topics_path
        self.used_topics = self._load_used_topics()

    def _load_used_topics(self):
        """Load topics already used by a successful upload."""
        if os.path.exists(self.used_topics_path):
            try:
                with open(self.used_topics_path, "r", encoding="utf-8") as handle:
                    topics = json.load(handle)
                return topics if isinstance(topics, list) else []
            except Exception as error:
                logger.error("Failed to load used topics: %s", error)
        return []

    def mark_used(self, topic):
        """Persist a topic only after its associated video uploads successfully."""
        if not topic or str(topic).casefold() in {str(item).casefold() for item in self.used_topics}:
            return
        self.used_topics.append(topic)
        try:
            directory = os.path.dirname(self.used_topics_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(self.used_topics_path, "w", encoding="utf-8") as handle:
                json.dump(self.used_topics, handle, indent=2)
            logger.info("Topic '%s' added to history.", topic)
        except Exception as error:
            logger.error("Failed to save used topic: %s", error)

    def get_viral_topic(self, llm=None, performance_context=None, competitor_context=None):
        """Pick an unused, curated topic without spending an LLM request.

        Recent channel and public competitor titles are weak category-level
        signals only. They do not supply titles to copy or prove search volume.
        """
        category_terms = {
            "attention": ("attention", "focus", "distraction", "notification", "task"),
            "memory": ("memory", "remember", "recall", "detail"),
            "decisions": ("decision", "choice", "estimate", "cost", "default"),
            "social influence": ("group", "comparison", "influence", "belonging"),
            "habits": ("habit", "routine", "cue", "repeat"),
            "motivation": ("motivation", "progress", "reward", "effort"),
            "emotion": ("stress", "emotion", "worry", "uncertainty", "anticipation"),
            "communication": ("message", "conversation", "tone", "feedback", "question"),
            "wellbeing": ("sleep", "rest", "break", "wellbeing"),
            "beliefs": ("belief", "expectation", "impression", "evidence", "confidence"),
            "social behaviour": ("bystander", "help", "responsibility", "notice"),
            "relationships": ("friendship", "relationship", "intent", "perspective"),
            "learning": ("learn", "learning", "practice", "feedback", "explain"),
        }
        categories = list(dict.fromkeys(category for _, category in TOPIC_BANK))
        used = {str(topic).casefold() for topic in self.used_topics}
        unused = [(topic, category) for topic, category in TOPIC_BANK if topic.casefold() not in used]
        if not unused:
            if not llm:
                logger.error("Curated topic queue exhausted and no text provider is configured.")
                return None
            prompt = (
                "Choose one original, evidence-aware everyday psychology question for an educational video. "
                "Avoid diagnoses, pop-psychology myths, fearbait, manipulation advice, and absolute claims. "
                "Do not repeat these used topics: "
                + json.dumps(self.used_topics[-100:], ensure_ascii=False)
                + "\nReturn only one concise question, without quotes or extra text."
            )
            try:
                candidate = (llm._call_gemini(prompt) or "").strip().strip('"')
                if candidate and candidate.casefold() not in used:
                    logger.info("Curated queue exhausted; obtained one fresh topic from the free provider chain.")
                    return candidate
            except Exception as error:
                logger.error("Free-provider topic request failed: %s", error)
            logger.error("Curated topic queue exhausted; refusing to repeat or invent a topic.")
            return None

        signals = {category: 0.0 for category in categories}
        for row in performance_context or []:
            title = str(row.get("title", "")).casefold()
            weight = math.log1p(max(0, int(row.get("views", 0) or 0)))
            for category in categories:
                if any(term in title for term in category_terms.get(category, ())):
                    signals[category] += weight
        for row in (competitor_context or [])[:8]:
            title = str(row.get("title", "")).casefold()
            weight = math.log1p(max(0, int(row.get("views_per_day", 0) or 0)))
            for category in categories:
                if any(term in title for term in category_terms.get(category, ())):
                    signals[category] += weight

        used_counts = {
            category: sum(
                1 for topic, topic_category in TOPIC_BANK
                if topic_category == category and topic.casefold() in used
            )
            for category in categories
        }
        category = max(
            categories,
            key=lambda value: (
                signals[value] - (used_counts[value] * 2.0),
                -categories.index(value),
            ),
        )
        selected = next((topic for topic, group in unused if group == category), unused[0][0])
        logger.info(
            "Selected an unused curated topic from the %s category; no LLM topic call was needed.",
            category,
        )
        return selected
