import os
import json
import logging
from src.config import Config

logger = logging.getLogger(__name__)

class TrendEngine:
    def __init__(self, used_topics_path="output/used_topics.json"):
        self.used_topics_path = used_topics_path
        self.used_topics = self._load_used_topics()

    def _load_used_topics(self):
        """Loads the list of already used topics to ensure zero repetition."""
        if os.path.exists(self.used_topics_path):
            try:
                with open(self.used_topics_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load used topics: {e}")
        return []

    def mark_used(self, topic):
        """Persist a topic after its associated video uploads successfully."""
        if not topic or topic in self.used_topics:
            return
        self._save_used_topic(topic)

    def _save_used_topic(self, topic):
        """Persists a new topic to the used list."""
        self.used_topics.append(topic)
        try:
            os.makedirs(os.path.dirname(self.used_topics_path), exist_ok=True)
            with open(self.used_topics_path, 'w', encoding='utf-8') as f:
                json.dump(self.used_topics, f, indent=2)
            logger.info(f"Topic '{topic}' added to persistence.")
        except Exception as e:
            logger.error(f"Failed to save used topic: {e}")

    def get_viral_topic(self, llm, performance_context=None, competitor_context=None):
        """
        Interacts with LLM to fetch trending topics based on the configured niche and returns the best unused one.
        """
        niche = Config.NICHE
        logger.info(f"Generating candidate topic ideas for {niche}...")
        
        performance_str = ""
        if performance_context:
            perf_list = [
                f"'{p['title']}' ({p.get('views', 0)} public views)"
                for p in performance_context if p.get("title")
            ]
            performance_str = (
                "RECENT CHANNEL PERFORMANCE (prioritize topics with strong watch time and viewer interest; directional evidence only):\n"
                + ", ".join(perf_list) + "\n"
            )

        competitor_str = ""
        if competitor_context:
            competitor_rows = []
            for item in competitor_context[:8]:
                if item.get("title"):
                    competitor_rows.append(
                        f"- {item['title']} ({item.get('views', 0)} public views; "
                        f"{item.get('views_per_day', 0)} views/day; "
                        f"{item.get('channel_title', 'unknown channel')})"
                    )
            if competitor_rows:
                competitor_str = (
                    "RECENT PUBLIC COMPETITOR SEARCH SAMPLE (directional demand signals only; "
                    "not search-volume data or proof of causal growth):\n"
                    + "\n".join(competitor_rows)
                    + "\nUse these only to identify viewer questions that deserve a different, "
                    "evidence-aware angle. Never copy titles, scripts, or packaging.\n"
                )

        prompt = f"""
        You are the editorial researcher for an original educational channel about
        everyday psychology, human behaviour, cognitive biases and social perception.

        Generate 20 DISTINCT video-topic ideas with strong curiosity but honest framing.
        Prefer concepts that can be explained accurately using established psychology,
        such as cognitive biases, memory, attention, social influence, habits and decision
        making. Each idea must support a useful explanation, a concrete everyday example,
        and a nuance or limitation.

        Do not claim that a topic is currently trending unless you have verified evidence.
        Avoid pop-psychology myths, diagnoses, "secret signs" claims, fearbait, manipulation
        instructions, gender stereotypes and claims that one behaviour proves intent.
        Do not repeat these previously used topics:
        {json.dumps(self.used_topics[-100:] if self.used_topics else [])}

        {performance_str}
        {competitor_str}
        Rank ideas by specific audience problem, clarity, evidence availability, originality, and potential to sustain a distinct series. Prefer a fresh angle on a proven viewer question over a generic topic.
        Return ONLY a JSON list of 20 short, distinct topic strings, best first. No numbering or prose.
        """
        try:
            response = llm._call_gemini(prompt)
            if not response:
                return None
            
            candidates = llm._extract_json(response)
            if not candidates or not isinstance(candidates, list):
                return None
            
            # Filter out used topics
            unused = [c for c in candidates if c not in self.used_topics]
            
            if not unused:
                logger.warning("All discovered trends were already used. Forcing a new angle...")
                return self._get_fallback_topic(llm)
                
            selected = unused[0] # Pick the top one
            # Reserve only after the video uploads successfully.
            return selected
            
        except Exception as e:
            logger.error(f"Trend Engine discovery failed: {e}")
            return None

    def _get_fallback_topic(self, llm):
        """Force a unique topic if everything else is repeated."""
        niche = Config.NICHE
        prompt = f"Give me one original, specific {niche} topic that differs from common topics. Return only the string."
        return llm._call_gemini(prompt).strip().replace('"', '')
