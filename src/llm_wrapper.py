import time
import json
from google import genai
from .config import Config

class LLMWrapper:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Explicitly use v1 API for stability
        self.client = genai.Client(
            api_key=Config.GEMINI_API_KEY,
            http_options={'api_version': 'v1'}
        )
        
        # Priority list of models based on confirmed availability in logs (Jan 2026)
        self.preferred_models = [
            'models/gemini-1.5-flash',
            'models/gemini-2.0-flash',
            'models/gemini-flash-latest',
            'models/gemini-1.5-flash-002',
            'models/gemini-1.5-pro',
            'models/gemini-2.0-flash-lite',
            'models/gemini-pro'
        ]
        self.available_gen_models = []
        self._refresh_available_models()

    def _refresh_available_models(self):
        """Fetches and filters models that support content generation."""
        try:
            print("Refreshing available generative models...")
            models = list(self.client.models.list())
            self.available_gen_models = [m.name for m in models if 'generateContent' in m.supported_actions]
            print(f"DEBUG: Confirmed Generative Models: {self.available_gen_models}")
        except Exception as e:
            print(f"Warning: Could not list models, will use hardcoded defaults: {e}")
            self.available_gen_models = self.preferred_models

    def _call_gemini(self, prompt, max_retries=10):
        """Ultra-robust caller that swaps models if one is rate-limited or missing."""
        
        # Build an ordered list of models to try for THIS call
        candidate_models = []
        for p in self.preferred_models:
            if p in self.available_gen_models:
                candidate_models.append(p)
        
        # Add any other available models that aren't in our preference list
        for a in self.available_gen_models:
            if a not in candidate_models:
                candidate_models.append(a)
        
        if not candidate_models:
            candidate_models = ['models/gemini-1.5-flash'] # Final desperation

        model_index = 0
        for i in range(max_retries):
            # Cycle through models if we keep hitting limits
            current_model = candidate_models[model_index % len(candidate_models)]
            
            try:
                # Disable AFC to speed up and save tokens
                config = {'automatic_function_calling': {'disable': True}}
                response = self.client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=config
                )
                if not response or not response.text:
                    raise ValueError("Empty response")
                return response.text
                
            except Exception as e:
                err_msg = str(e).lower()
                
                # If 404, the model name is definitely wrong or retired, move to next model immediately
                if "404" in err_msg or "not found" in err_msg:
                    print(f"Model {current_model} NOT FOUND (404). Swapping...")
                    model_index += 1
                    continue
                
                # If 429 or Quota, wait and then try the NEXT model to spread load
                if "429" in err_msg or "resource_exhausted" in err_msg or "quota" in err_msg:
                    wait_time = min(5 * (2 ** (i // 2)), 60) # 5, 5, 10, 10, 20, 20... capping at 60s
                    print(f"Rate Limited on {current_model}. Attempt {i+1}/{max_retries}. Swapping models and waiting {wait_time}s...")
                    model_index += 1
                    time.sleep(wait_time)
                    continue
                
                # If it's a different error (like safety), we might need to stop
                print(f"Gemini API Error on {current_model}: {e}")
                if i < 3: # Try a few times even for unknown errors
                    model_index += 1
                    continue
                return None
        return None

    def _extract_json(self, text):
        """Robustly Extracts and cleans JSON from LLM response using regex and balance checks."""
        import re
        try:
            # 1. Strip markdown blocks
            text = text.replace("```json", "").replace("```", "").strip()
            
            # 2. Find anything between { } or [ ]
            json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
            if json_match:
                candidate = json_match.group(1)
                # 3. Final validation
                return json.loads(candidate)
            return json.loads(text)
        except Exception as e:
            print(f"JSON Extraction Error: {e}")
            return None

    def generate_psychology_titles(self):
        """Generates 20 viral psychology titles."""
        prompt = """
        Objective: Write exactly 20 highly clickable, emotionally intense YouTube psychology titles.
        Return ONLY Valid JSON. A simple list of strings.
        ["Title 1", "Title 2", ...]
        """
        try:
            text = self._call_gemini(prompt)
            if not text: return []
            return self._extract_json(text) or []
        except:
            return []

    def generate_psychology_script(self, title):
        """Generates a high-retention psychology script with noir-style visuals."""
        prompt = f"""
        Title: {title}
        Role: A lead writer for a top-tier Psychology & Insight channel.
        Tone: Mysterious, authoritative, and deeply engaging (Psychological Noir).
        
        STRICT RULES:
        1. VIRAL HOOK (0-5s): Start with a shocking psychological paradox or a "Curiosity Gap" question that forces them to stay.
        2. Content: Focus on "Deep Social Truths" or "Hidden Human Behaviors" (e.g. why we fear silence, the dark side of kindness).
        3. Visual Style: 'Surrealist Psychological Noir' - cinematic, dark, moody, ink wash textures, dramatic shadows.
        4. Scene Count: 30-40 detailed scenes for a long-form deep dive.
        
        STRICT OUTPUT FORMAT (Valid JSON ONLY):
        {{
            "title": "Title",
            "description": "Exploding the hidden truths of {{title}}. #Psychology #HumanBehavior #Wisdom",
            "tags": ["Psychology", "Human Behavior", "Mental Health", "Mindset", "Deep Truths", "Noir"],
            "music_mood": "dark", // Choice: dark, suspenseful, chill, tense
            "deduced_angle": "Brief explanation of the psychological angle",
            "scenes": [
                {{
                    "text": "spoken narration...",
                    "visual_prompt": "moody cinematic ink wash illustration of..."
                }},
                ...
            ]
        }}
        """
        try:
            text = self._call_gemini(prompt)
            if not text: return None
            return self._extract_json(text)
        except:
            return None

    def generate_psychology_short_script(self, title):
        """Generates a high-retention psychology SHORT script (Noir)."""
        prompt = f"""
        Title: {title}
        Role: A mysterious storyteller revealing the "Darker Side" of human behavior.
        Format: YouTube Short (10-12 scenes, max 50 seconds).
        Visual Style: Surrealist Psychological Noir (Ink & Wash, Moody, Cinematic).
        
        STRICT RULES:
        1. THE HOOK: The first sentence must be a punch to the gut. Something like "Psychology says if they do X, they are lying to you."
        2. THE REVEAL: Explain the 'Why' using deep psychological theory (Dark Triad, Jungian Shadows, etc.) but keep it fast-paced.
        3. PATTERN INTERRUPTS: Every 3 scenes, change the visual intensity.
        4. PUNCHLINE: End with a question that makes them rethink their entire life.
        
        STRICT OUTPUT FORMAT (Valid JSON ONLY):
        {{
            "title": "{title}",
            "description": "The hidden psychology of {title}. #Psychology #DarkPsychology #Shorts",
            "tags": ["Psychology", "Dark Psychology", "Social Facts", "Shorts", "Noir", "Human Nature"],
            "music_mood": "tense",
            "scenes": [
                {{
                    "text": "spoken narration...",
                    "visual_prompt": "Surrealist noir ink drawing of..."
                }},
                ...
            ]
        }}
        """
        try:
            text = self._call_gemini(prompt)
            if not text: return None
            return self._extract_json(text)
        except:
            return None

    def generate_relatable_comedy_script(self, topic):
        """
        Generates a script focused on Relatable Day-to-Day Comedy (POV style).
        Focus: Observational humor, "That feeling when...", "POV: You just...".
        """
        prompt = f"""
        Topic: {topic}
        Role: A relatable observational comedian who finds the funny in everyday struggle.
        
        STRICT RULES:
        1. CRITICAL: Total video MUST be under 60 seconds (10 scenes).
        2. VIRAL HOOK (0-3s): Start with "POV:..." or "We all know that feeling when..." or "Why does every [topic] do this?"
        3. RELATABILITY: Focus on the small, annoying, or awkward things humans do in daily life.
        4. COMEDIC TIMING: Use ellipses (...) and shorter sentences for comedic beats.
        5. Visuals: MUST be "flat minimalist character icon [ACTION]" (e.g., a cute robot, emoji face, or simple person) that VISUALLY shows the joke.
        6. VIBRANT STYLE: Each scene should have a "bg_color" that is vibrant (Red, Blue, Green, Yellow, etc.). The character must be centered on this solid background.
        7. Style: Fun, slightly sarcastic, human-to-human vibe. NO AI SLOP.
        
        FORMAT:
        {{
            "title": "POV: {topic}",
            "description": "Honestly, why is this so real? 😂 #Relatable #DailyLife #Memes #POV",
            "music_mood": "funny", // Choice: funny, upbeat, chill, tense
            "bg_color": "#FF0000", // A single vibrant hex color for the whole video's theme or mood
            "scenes": [
                {{
                    "text": "spoken narration...",
                    "audio_mood": "neutral", // or funny, energetic
                    "vocal_action": "talking", // choice: jumping, shaking, bouncing, talking
                    "visual_prompt": "flat minimalist white character icon [doing something relatable] on a solid {topic} themed background"
                }},
                ... (10 scenes total)
            ]
        }}
        """
        try:
            text = self._call_gemini(prompt)
            if not text: return None
            return self._extract_json(text)
        except Exception as e:
            print(f"Error parsing relatable comedy script: {e}")
            return None

    def generate_conversational_script(self, topic, type="short"):
        """Generates a high-SEO, human-like script with dynamic stickman movements."""
        
        if type == "short":
            char_count = "500-600"
            scene_count = 10
            duration_note = "CRITICAL: Total video MUST be under 60 seconds."
        else:
            char_count = "7000-9000"
            scene_count = 25
            duration_note = "Target 8-10 minute duration."
        
        prompt = f"""
        Topic: {topic}
        Role: A charismatic Psychology Storyteller who reveals hidden social secrets.
        
        STRICT RULES:
        1. {duration_note}
        2. VIRAL HOOK (0-3s): Start with "Did you know..." or "Psychology says..." or a "POV" that hits a social pain point.
        3. Psychology Focus: Make it about relatable social hacks, human nature, or dark truths.
        4. Pattern Interrupts: Mark scenes at 25%, 50%, and 75% with `vocal_action: "jumping"` or `"shaking"` for visual pop.
        5. Scene Count: {scene_count}.
        6. JSON VALIDITY: Ensure all strings are correctly quoted and escaped.
        
        FORMAT:
        {{
            "title": "{topic}",
            "description": "Deep psychological insights about {topic}. #Insight #SelfImprovement #Shorts",
            "music_mood": "chill", // Choice: upbeat, funny, chill, tense
            "scenes": [
                {{
                    "text": "spoken narration...",
                    "audio_mood": "serious",
                    "vocal_action": "talking",
                    "visual_prompt": "minimalist stickman illustration of..."
                }},
                ...
            ]
        }}
        """
        try:
            text = self._call_gemini(prompt)
            if not text: return None
            return self._extract_json(text)
        except Exception as e:
            print(f"Error parsing conversational script: {e}")
            return None

    def generate_psychology_stickman_script(self, topic):
        """
        Generates a high-retention psychology script with STICKMAN visuals.
        Requested by user feedback: Natural punctuation, stickman synced visuals.
        """
        scene_count = 10
        duration_note = "CRITICAL: Total video MUST be under 60 seconds."
        
        prompt = f"""
        Topic: {topic}
        Role: A charismatic Psychology Storyteller who reveals hidden social secrets.
        
        STRICT RULES:
        1. {duration_note}
        2. VIRAL HOOK (0-3s): Start with "Did you know..." or "Psychology says..." or a "POV" that hits a social pain point.
        3. NATURAL PUNCTUATION: You MUST use commas, periods, and ellipses (...) specifically to guide the AI Voiceover's breathing and pacing. Do not write run-on sentences.
        4. Psychology Focus: Make it about relatable social hacks, human nature, or dark truths.
        5. Visual Synced Animation: {scene_count} scenes.
           - `visual_prompt`: MUST be "minimalist stickman [ACTION]" (e.g. "minimalist stickman holding head in pain", "minimalist stickman running fast").
           - `vocal_action`: Use "jumping", "shaking", "bouncing" or "talking" to match the emotion.
        6. JSON VALIDITY: Ensure all strings are correctly quoted and escaped.
        
        FORMAT:
        {{
            "title": "{topic}",
            "description": "Deep psychological insights about {topic}. #Insight #SelfImprovement #Shorts",
            "music_mood": "chill", // Choice: upbeat, funny, chill, tense
            "scenes": [
                {{
                    "text": "spoken narration with breathing room...",
                    "audio_mood": "serious",
                    "vocal_action": "talking",
                    "visual_prompt": "minimalist stickman illustration of..."
                }},
                ...
            ]
        }}
        """
        try:
            text = self._call_gemini(prompt)
            if not text: return None
            return self._extract_json(text)
        except Exception as e:
            print(f"Error parsing psychology stickman script: {e}")
            return None

# Singleton Instance
try:
    llm = LLMWrapper()
except Exception as e:
    print(f"LLM Init Warning: {e}")
    llm = None
