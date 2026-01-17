import google.generativeai as genai
import os
import json
import logging
from local_brain import local_brain

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

    def _call_gemini_with_retry(self, prompt, retries=2, base_delay=5):
        """Calls Gemini with exponential backoff to handle quota/rate limits."""
        import time
        import random
        for i in range(retries):
            try:
                return self.model.generate_content(prompt)
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    delay = base_delay * (2 ** i) + random.uniform(0, 1)
                    logger.warning(f"Quota exceeded. Retrying in {delay:.1f}s... (Attempt {i+1}/{retries})")
                    time.sleep(delay)
                else:
                    raise e
        return None

    def generate_script(self, topic, video_type="short", niche="curiosity"):
        if not self.api_key:
            return None

        if niche == "meme":
            prompt = self._build_meme_prompt(topic)
        else:
            prompt = self._build_prompt(topic, video_type, niche)
        
        try:
            response = self._call_gemini_with_retry(prompt)
            if not response:
                # FALLBACK TO LOCAL BRAIN (Offline Mode)
                return local_brain.generate_offline_script(topic, video_type, niche)
            data = self._parse_response(response.text)
            
            if not data:
                return local_brain.generate_offline_script(topic, video_type, niche)
            # These cause the TTS to read things like "(whispering)" literally.
            if data and 'script_segments' in data:
                import re
                for seg in data['script_segments']:
                    if 'text' in seg:
                        # Remove content in parentheses ( ) or brackets [ ]
                        seg['text'] = re.sub(r'[\(\[].*?[\)\]]', '', seg['text']).strip()
                        # Clean up double spaces
                        seg['text'] = re.sub(r'\s+', ' ', seg['text'])
            return data
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return None

    def _build_meme_prompt(self, topic):
        prompt = f"""
        Generate a HILARIOUS and RELATABLE YouTube Shorts meme script about '{topic}'.
        Target: 10/10 Humor, High Shareability.
        
        STRICT RULES:
        1. NO LISTICLES: Do not list "Top 5" or "3 Reasons". This is a single, relatable narrative.
        2. CONVERSATIONAL PIVOTS: Use phrases like "So, I was thinking...", "Wait, tell me this hasn't happened to you...", "And then, of course...", "The audacity of...".
        3. NO AI-ISMS: Avoid "In a world", "Ever wondered", "Meet Joe". Talk like a real person venting on social media.
        4. LENGTH: Must be 40-50 SECONDS long.
        5. SEGMENTS: provide 6-8 fast-paced segments.
        
        Requirements:
        1. SHOCKING HOOK: The first sentence must be a "Wait, what?" moment.
        2. TONE: Sarcastic, self-deprecating, deeply relatable "Human-to-Human" vibe.
        3. PUNCHLINE: End with a sharp, unexpected twist or a relatable sigh.
        
        Output Format: JSON only
        {{
            "title": "Shocking Viral Title Here",
            "tags": ["memes", "funny", "relatable", "shorts"],
            "script_segments": [
                {{
                    "text": "The setup (3-5 seconds)...",
                    "visual_keywords": ["funny"],
                    "stickman_poses": ["stickman laughing", "stickman rolling on floor"],
                    "duration_estimate": 7
                }},
                ... (5-7 segments total summing to 35-45 seconds)
            ]
        }}
        """
        return prompt

    def _build_prompt(self, topic, video_type, niche):
        # Target durations
        if video_type == "short":
            target_duration = "35-45 seconds"
            segments_required = "5-7 segments"
        else:
            target_duration = "8-10 minutes"
            segments_required = "15-20 segments"
            
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
        Generate a VIRAL YouTube {'Shorts' if video_type == 'short' else 'Video'} script about '{topic}' for the '{niche}' niche.
        Target: High Audience Retention and Max CTR.
        POLICY: Must be ADVERTISER-FRIENDLY. No controversial topics, no fear-mongering.
        
        STRICT RULES:
        1. NO LISTICLES: Focus on ONE deep narrative or a single analytical story.
        2. NO INTRODUCTIONS: Don't say "Hi guys" or "Welcome back". Start in the middle of the action/thought.
        3. Conversational "Wait, listen to this..." or "This is where it gets weird..." patterns.
        4. TARGET LENGTH: {target_duration} total.
        5. SEGMENTS: Provide {segments_required} minimum.
        
        {mystery_instruction}

        Requirements:
        1. VIRAL HOOK: Start with a declaration that challenges the viewer's current belief.
        2. TONE: Intellectual yet punchy. Like a high-budget documentary but with "Street Wisdom".
        3. NO AI-ISMS: Ban phrases like "The significance of...", "It is important to note...", "In conclusion...". Instead use: "Basically...", "This changes everything because...", "And honestly...".
        
        Output Format: JSON only
        {{
            "title": "Shocking Viral Title Here",
            "tags": ["trending", "mystery", "shocking", "facts"],
            "script_segments": [
                {{
                    "text": "First 3 seconds: SHOCKING hook here...",
                    "visual_keywords": ["mystery", "darkness"],
                    "stickman_poses": ["stickman pointing left", "stickman pointing right"],
                    "duration_estimate": 5
                }},
                ... ({segments_required} total summing to {target_duration})
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
            response = self._call_gemini_with_retry(prompt)
            if not response:
                return True, "API Failure, failing open (safe)"
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
            response = self._call_gemini_with_retry(prompt)
            if not response:
                return True # Fallback
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

    def refine_script_for_quality(self, script_json, niche="curiosity"):
        """
        Act as a professional YouTube Script Editor to polish the script.
        Target: Increase emotional connection, remove robotic phrasing, ensure value.
        """
        if not self.api_key:
            return script_json

        # Serialize input for the prompt
        script_text = json.dumps(script_json, indent=2)

        prompt = f"""
        You are a Master YouTube Script Editor (Human connection expert).
        Your Job: Polishing an AI-generated script to make it feel deeply human and valuable.
        
        Input Script (JSON):
        {script_text}
        
        CRITIQUE GUIDELINES:
        1. HOOK: Is the first 3 seconds generic? Make it personal ("You", "We", "I"). 
           - Bad: "Black holes are mysterious."
           - Good: "You shouldn't exist right now, and black holes are the reason why."
        2. FLOW: Remove "transition words" like "However", "Furthermore", "In conclusion". Use natural speech.
        3. VALUE: Ensure every sentence respects the viewer's time. Cut fluff.
        4. EMOTION: Add emotional context. Why should the viewer *care*?
        
        ACTION:
        - Rewrite the "text" fields in the JSON.
        - Keep the JSON structure EXACTLY the same.
        - Do not change keywords or stickman poses unless they don't match the new text.
        
        Output: The Polished JSON ONLY.
        """
        
        try:
            response = self._call_gemini_with_retry(prompt)
            if not response:
                return script_json
            result = self._parse_response(response.text)
            if result:
                logger.info("Script refined for quality successfully.")
                return result
            return script_json # Fallback to original
        except Exception as e:
            logger.error(f"Quality refinement error: {e}")
            return script_json # Fallback to original

    def generate_viral_title(self, topic, keywords=None, max_chars=65):
        """
        Generate VidIQ-style viral title optimized for CTR.
        Returns the best title from multiple AI-generated options.
        """
        if not self.api_key:
            return f"{topic[:max_chars]}"

        keywords_str = ", ".join([kw['keyword'] for kw in (keywords or [])[:3]])

        prompt = f"""
        Generate 5 viral YouTube video titles for the topic: "{topic}"
        
        REQUIREMENTS:
        1. Maximum {max_chars} characters (strict limit)
        2. Incorporate these high-value keywords naturally: {keywords_str}
        3. Use proven NARRATIVE CTR patterns:
           - Curiosity gap ("The Secret...", "What Nobody Tells You...")
           - Urgency ("Before It's Too Late", "Right Now")
           - Personal address ("You", "Your")
           - Philosophical/Analytical ("Why we were wrong about...", "The truth of...")
        4. ABSOLUTELY NO LISTICLES: Do not use numbers like "Top 5" or "3 Reasons".
        5. HONESTY: Title must match a narrative analysis, not a list of facts.
        6. Front-load the main keyword
        
        Output JSON:
        {{
            "titles": [
                {{"title": "Example Title Here", "ctr_score": 85}},
                {{"title": "Another Title", "ctr_score": 78}},
                ...
            ]
        }}
        
        Score each title 0-100 for predicted CTR.
        """
        
        try:
            response = self._call_gemini_with_retry(prompt)
            if not response:
                return local_brain.generate_offline_title(topic)
            result = self._parse_response(response.text)
            if result and 'titles' in result:
                # Sort by CTR score and return best
                titles = sorted(result['titles'], key=lambda x: x.get('ctr_score', 0), reverse=True)
                best_title = titles[0]['title'][:max_chars]  # Enforce limit
                logger.info(f"Generated viral title: {best_title} (CTR: {titles[0].get('ctr_score')})") 
                return best_title
        except Exception as e:
            logger.error(f"Viral title generation error: {e}")
        
        # Fallback to local brain
        return local_brain.generate_offline_title(topic)

    def generate_thumbnail_text(self, topic, keywords=None):
        """
        Generate high-CTR, VidIQ-style thumbnail text (Max 3-5 words).
        """
        if not self.api_key:
            return topic.upper()[:20]

        keywords_str = ", ".join([kw['keyword'] for kw in (keywords or [])[:3]])
        
        prompt = f"""
        Generate 5 high-CTR text overlays for a YouTube thumbnail about: "{topic}"
        
        VIDIQ RULES:
        1. MAX 3-5 WORDS. Short and punchy.
        2. DO NOT repeat the Title. Complement it.
        3. EMOTION: Use Shock, Disbelief, or "Impossible" vibes.
        4. TEXT ONLY. No descriptions of images.
        5. EXAMPLES:
           - "THEY LIED?"
           - "DON'T DO THIS"
           - "IMPOSSIBLE."
           - "SECRET REVEALED"
           - "WHY??"
           
        Keywords context: {keywords_str}
        
        Output JSON:
        {{
            "texts": ["TEXT 1", "TEXT 2", ...]
        }}
        """
        try:
            response = self._call_gemini_with_retry(prompt)
            if not response:
                return topic.upper()[:20]
            result = self._parse_response(response.text)
            if result and 'texts' in result:
                import random
                best_text = random.choice(result['texts']).upper()
                logger.info(f"Generated thumbnail text: {best_text}")
                return best_text
        except Exception as e:
            logger.error(f"Thumbnail text gen error: {e}")
        
        return keywords[0]['keyword'].upper() if keywords else topic.upper()[:20]


    def generate_optimized_tags(self, topic, keywords=None):
        """
        Generate VidIQ-style optimized tags (15-20 tags, max 500 chars total).
        Mixes broad + specific tags, includes misspellings.
        """
        if not self.api_key:
            return f"#{topic.replace(' ', '')} #shorts #viral"

        keywords_str = ", ".join([kw['keyword'] for kw in (keywords or [])[:5]])

        prompt = f"""
        Generate optimized YouTube tags for: "{topic}"
        High-value keywords: {keywords_str}
        
        REQUIREMENTS:
        1. Generate 15-20 tags total
        2. Mix:
           - 3-5 broad tags (e.g., "facts", "education")
           - 8-12 specific long-tail tags (e.g., "how black holes work")
           - 2-3 common misspellings of main keywords
        3. Prioritize high-value keywords first
        4. Total character count must be under 500 chars
        5. No irrelevant tags
        
        Output JSON:
        {{
            "tags": ["tag1", "tag2", "tag3", ...]
        }}
        """
        
        try:
            response = self._call_gemini_with_retry(prompt)
            if not response:
                return local_brain.generate_offline_tags(topic)
            result = self._parse_response(response.text)
            if result and 'tags' in result:
                tags = result['tags'][:20]  # Max 20
                # Validate total length
                tags_str = " ".join([f"#{t.replace(' ', '')}" for t in tags])
                if len(tags_str) > 500:
                    # Trim to fit
                    tags = tags[:15]
                    tags_str = " ".join([f"#{t.replace(' ', '')}" for t in tags])
                logger.info(f"Generated {len(tags)} optimized tags")
                return tags_str
        except Exception as e:
            logger.error(f"Tag generation error: {e}")
        
        # Fallback
        return local_brain.generate_offline_tags(topic)

    def optimize_description(self, title, script_segments, keywords=None):
        """
        Generate SEO-optimized description.
        Keywords in first 150 chars, timestamps for long videos, CTA.
        """
        if not self.api_key:
            return f"{title}\n\nWatch to learn more!"

        keywords_str = ", ".join([kw['keyword'] for kw in (keywords or [])[:3]])
        script_preview = " ".join([seg.get('text', '')[:50] for seg in script_segments[:3]])

        prompt = f"""
        Generate an SEO-optimized YouTube video description.
        
        Title: {title}
        Script Preview: {script_preview}...
        Keywords: {keywords_str}
        
        REQUIREMENTS:
        1. First 150 characters: Hook + main keywords naturally integrated
        2. Brief summary (2-3 sentences)
        3. Call-to-action (subscribe, like, comment)
        4. Hashtags (3-5 relevant)
        5. AI Disclaimer: "Content generated with the help of AI."
        6. Keep total under 5000 characters
        
        Output: Plain text description (not JSON)
        """
        
        try:
            response = self._call_gemini_with_retry(prompt)
            if not response:
                return local_brain.generate_offline_description(topic, title)
            description = response.text.strip()
            # Remove any markdown artifacts
            description = description.replace('```', '').strip()
            logger.info("Generated optimized description")
            return description[:5000]  # YouTube limit
        except Exception as e:
            logger.error(f"Description optimization error: {e}")
        
        # Fallback
        return local_brain.generate_offline_description(topic, title)

llm = LLMWrapper()
