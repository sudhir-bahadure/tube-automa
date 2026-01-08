import google.generativeai as genai
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMWrapper:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables.")
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_script(self, topic, video_type="short", niche="curiosity"):
        if not self.api_key:
            return None

        prompt = self._build_prompt(topic, video_type, niche)
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return None

    def _build_prompt(self, topic, video_type, niche):
        duration = "60 seconds" if video_type == "short" else "8-10 minutes"
        
        prompt = f"""
        Generate a YouTube video script about '{topic}' for the '{niche}' niche.
        Target Duration: {duration}
        
        Requirements:
        1. High Retention: Start with a strong hook. For long videos, add retention hooks every 60 seconds.
        2. YPP Compliance: Use investigative and analytical language. Don't just list facts; provide interpretations and 'why it matters'.
        3. Visual/Script Sync: For every 5-10 seconds of script, provide 3-5 keywords for background footage selection.
        4. No repetitive visuals: Ensure keywords are specific and varied.
        
        Output Format: JSON only
        {{
            "title": "Catcy Title",
            "tags": ["tag1", "tag2"],
            "script_segments": [
                {{
                    "text": "The script text for this segment...",
                    "visual_keywords": ["keyword1", "keyword2", "keyword3"],
                    "duration_estimate": 8
                }},
                ...
            ]
        }}
        """
        return prompt

    def _parse_response(self, text):
        # Clean markdown if present
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None

llm = LLMWrapper()
