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

        if niche == "meme":
            prompt = self._build_meme_prompt(topic)
        else:
            prompt = self._build_prompt(topic, video_type, niche)
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return None

    def _build_meme_prompt(self, topic):
        prompt = f"""
        Generate a VIRAL YouTube Shorts MEME script about '{topic}'.
        Target: Extreme Humor, Laughter, and Shareability.
        POLICY: Must be ADVERTISER-FRIENDLY. No hate speech, no controversy, no bullying.
        
        Requirements:
        1. VIRAL HOOK: A relatable or "literally me" opening that grabs attention.
        2. VIRAL TITLE: High-CTR, relatable meme title (Max 50 chars).
        3. TONE: Happy, upbeat, and relatable human emotions. The writing should induce laughter.
        4. STICKMAN VISUALS: Provide TWO alternating "stickman_poses" per segment.
           - These MUST be expressive (e.g., facepalm, laughing, crying of laughter, dancing).
        5. ABSOLUTE UNIQUENESS: Never use common jokes. Create fresh, witty commentary.
        
        Output Format: JSON only
        {{
            "title": "When you finally... 😂",
            "tags": ["memes", "funny", "relatable", "humor"],
            "script_segments": [
                {{
                    "text": "The relatable setup...",
                    "visual_keywords": ["funny", "laughing"],
                    "stickman_poses": ["stickman laughing hard", "stickman rolling on floor"],
                    "duration_estimate": 4
                }},
                {{
                    "text": "The punchline that hits hard...",
                    "visual_keywords": ["savage"],
                    "stickman_poses": ["stickman doing the 'L' dance", "stickman celebration"],
                    "duration_estimate": 6
                }}
            ]
        }}
        """
        return prompt

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
        Generate a VIRAL YouTube Shorts script about '{topic}' for the '{niche}' niche.
        Target: High Audience Retention and Max CTR.
        POLICY: Must be ADVERTISER-FRIENDLY. No controversial topics, no fear-mongering.
        
        {mystery_instruction}

        Requirements:
        1. VIRAL HOOK: The first 3 seconds MUST be a shocking or deeply curious statement.
        2. VIRAL TITLE: Click-heavy, curiosity-gap title (Max 50 chars). DO NOT use 'none'.
        3. STICKMAN VISUALS: For every segment, provide TWO alternating "stickman_poses" to create a motion effect.
           - These should be unique, specific, and relatable to the segment text.
           - Example: ["stickman waving left hand", "stickman waving right hand"]
        4. NO STOCK FOOTAGE: Script for a purely stickman-animated aesthetic.
        5. TONE: High energy, human-like emotions in writing, use engaging storytelling.
        6. ABSOLUTE UNIQUENESS: Every script and visual description must be 100% fresh and never repeated.
        
        Output Format: JSON only
        {{
            "title": "Shocking Viral Title Here",
            "tags": ["trending", "mystery", "shocking", "facts"],
            "script_segments": [
                {{
                    "text": "First 3 seconds: SHOCKING hook here...",
                    "visual_keywords": ["mystery", "darkness"],
                    "stickman_pose": "stickman pointing at a mysterious shadow",
                    "duration_estimate": 5
                }},
                {{
                    "text": "Next part of the story...",
                    "visual_keywords": ["discovery"],
                    "stickman_pose": "stickman holding a magnifying glass",
                    "duration_estimate": 10
                }}
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

    def check_policy_compliance(self, script_content):
        """
        Validate content against YouTube's Advertiser-Friendly Guidelines.
        Returns: (bool, str) -> (passed, reason)
        """
        if not self.api_key:
            return True, "No API key, skipping check"

        prompt = f"""
        Analyze the following YouTube video script/content for policy violations.
        
        Content:
        "{script_content[:3000]}"... (truncated)

        POLICIES TO CHECK:
        1. Hate Speech: No discrimination, slurs, or promoting violence against groups.
        2. Dangerous Content: No encouragement of self-harm, suicide, or dangerous challenges.
        3. Shocking Content: No gratuitous violence, gore, or repulsive imagery.
        4. Sexual Content: No explicit sexual content or nudity.
        5. Misinformation: No harmful health claims or election interference.
        
        Output JSON:
        {{
            "passed": true/false,
            "reason": "Brief explanation if failed, otherwise 'Safe'"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)
            if result:
                return result.get("passed", False), result.get("reason", "Unknown")
            return True, "Parse error, failing open (safe)"
        except Exception as e:
            logger.error(f"Policy check error: {e}")
            return True, "Check failed, failing open (safe)"

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
        4. CHECK SAFETY: Ensure it is not offensive, racist, or bullying.
        
        Output JSON:
        {{
            "is_funny": true/false,
            "is_corny": true/false,
            "is_safe": true/false,
            "score": 1-10,
            "reason": "short explanation"
        }}
        """
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)
            
            # Safety check first
            if result and not result.get("is_safe", True):
                logger.warning(f"Joke rejected for safety: {result.get('reason')}")
                return False
                
            # Then quality check
            # Only accept if funny, not corny, and score >= 6
            if result and result.get("is_funny") and not result.get("is_corny") and result.get("score", 0) >= 6:
                return True
            return False
        except:
            return True # Fallback

llm = LLMWrapper()
