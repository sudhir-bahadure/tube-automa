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
            # Using gemini-flash-latest as it's the verified working version for this API key
            self.model = genai.GenerativeModel('gemini-flash-latest')

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
        
        # Specialized instruction for "curiosity/mystery" niche
        mystery_instruction = ""
        if niche in ["curiosity", "mystery", "discovery"]:
            mystery_instruction = """
            TONE: Mysterious, investigative, and intellectually stimulating.
            HOOK: Start with an enigma or a 'what if' scenario that challenges reality.
            STORYTELLING: Unfold the topic like a detective story, revealing layers of complexity.
            HOOKS: Use cliffhangers at the end of segments to bridge to the next one.
            """

        prompt = f"""
        Generate a professional YouTube video script about '{topic}' for the '{niche}' niche.
        Target Duration: {duration}
        
        {mystery_instruction}

        Requirements:
        1. High Retention: Start with a powerful hook. For long videos (8-10 mins), provide at least 15-20 segments.
        2. YPP Compliance: Use investigative and analytical language. Provide unique interpretations and 'why it matters' from a modern perspective.
        3. Visual/Script Sync: For every segment, provide 3-5 keywords for background footage selection.
        4. Structure: 
           - INTRO: High-stakes hook.
           - BODY: Deep investigation with analytical transitions.
           - OUTRO: Philosophical synthesis and call to action.
        
        Output Format: JSON only
        {{
            "title": "Catcy Mystery Title",
            "tags": ["mystery", "curiosity", "analysis", "discovery"],
            "script_segments": [
                {{
                    "text": "The script text for this segment (approx 20-30 seconds of speech)...",
                    "visual_keywords": ["specific keyword 1", "keyword 2", "keyword 3"],
                    "duration_estimate": 25
                }},
                ...
            ]
        }}
        """
        return prompt

    def _parse_response(self, text):
        # Clean markdown if present and handle potential "thought" blocks
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Remove any leading/trailing garbage
        text = text.strip()
        
        try:
            return json.loads(text)
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {text[:200]}...")
            return None

    def verify_humor(self, joke_text):
        """Verify if a joke is actually funny and high-engagement (not corny)."""
        if not self.api_key:
            return True # Fallback to true if no API key
            
        prompt = f"""
        Evaluate the following joke/meme text for a modern YouTube audience. 
        Audience Feedback: "not funny", "didn't even smile", "cornball".
        
        Joke Text: "{joke_text}"
        
        Your Task:
        1. Determine if this is a "Dad Joke" or "Corny" joke.
        2. Determine if it has "Viral Potential" for a meme channel.
        3. Rate from 1-10.
        
        Output JSON:
        {{
            "is_funny": true/false,
            "is_corny": true/false,
            "score": 1-10,
            "reason": "short explanation"
        }}
        """
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)
            # Only accept if funny, not corny, and score >= 6
            if result and result.get("is_funny") and not result.get("is_corny") and result.get("score", 0) >= 6:
                return True
            return False
        except:
            return True # Fallback

llm = LLMWrapper()
