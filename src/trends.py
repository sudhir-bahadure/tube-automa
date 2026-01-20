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

    def get_viral_topic(self, llm):
        """
        Interacts with LLM to fetch trending topics based on the configured niche and returns the best unused one.
        """
        niche = Config.NICHE
        logger.info(f"Discovering viral {niche} trends...")
        
        # We ask the LLM for many titles to increase the chance of finding an unused one
        prompt = f"""
        Objective: Identify the top 20 viral, trending topics related to "{niche}" currently exploding in the USA.
        Target: YouTube audience (high CTR, curious, conversational).
        
        EXCLUSION LIST (DO NOT RETURN THESE):
        {json.dumps(self.used_topics[-50:] if self.used_topics else [])}
        
        Format: Return ONLY a JSON list of strings.
        ["Viral Title 1", "Viral Title 2", ...]
        """
        
        try:
            response = llm._call_gemini(prompt)
            if not response:
                return None
            
            # Clean and parse JSON
            clean_text = response.replace("```json", "").replace("```", "").strip()
            if "[" in clean_text:
                clean_text = clean_text[clean_text.find("["):clean_text.rfind("]")+1]
            
            candidates = json.loads(clean_text)
            
            # Filter out used topics (just in case LLM ignored the exclusion list)
            unused = [c for c in candidates if c not in self.used_topics]
            
            if not unused:
                logger.warning("All discovered trends were already used. Forcing a new angle...")
                # Fallback: Ask for a completely unique niche angle
                return self._get_fallback_topic(llm)
                
            selected = unused[0] # Pick the top one
            self._save_used_topic(selected)
            return selected
            
        except Exception as e:
            logger.error(f"Trend Engine discovery failed: {e}")
            return None

    def _get_fallback_topic(self, llm):
        """Force a unique topic if everything else is repeated."""
        niche = Config.NICHE
        prompt = f"Give me one unique, viral {niche} topic that is completely different from common ones. Return only the string."
        return llm._call_gemini(prompt).strip().replace('"', '')
