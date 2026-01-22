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
        """Generates a long-form psychology script with 25+ animated scenes."""
        prompt = f"""
        Title: {title}
        Act as a lead writer for a top-tier US psychology channel.
        
        STRICT RULES:
        1. Break the script into AT LEAST 25 detailed scenes.
        1. VIRAL HOOK: The first 5 seconds MUST use a shocking psychological fact or an intense curiosity-gap question.
        2. Visual Style: 'Surrealist Psychological Noir'. 
        
        STRICT OUTPUT FORMAT (Valid JSON ONLY):
        {{
            "title": "{title}",
            "description": "...",
            "scenes": [
                {{
                    "text": "spoken narration...",
                    "visual_prompt": "..."
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
        Role: A charismatic YouTube storyteller who is funny, relatable, and high-energy.
        
        STRICT RULES:
        1. {duration_note}
        2. VIRAL HOOK (0-3s): The first scene MUST be an aggressive question, a relatable 'POV', or a shocking statement. Zero fluff.
        3. Retention Hooks: Include 'Pattern Interrupts' at 33% and 66% marks.
        4. Scene Count: {scene_count}.
        5. Punchline: Mark the funniest scene as `"is_punchline": true`.
        6. JSON VALIDITY: Ensure all strings are correctly quoted and escaped. No trailing commas.
        
        FORMAT:
        {{
            "title": "{topic}",
            "description": "...",
            "scenes": [
                {{
                    "text": "spoken narration...",
                    "audio_mood": "excited",
                    "vocal_action": "talking",
                    "is_punchline": false,
                    "visual_prompt": "..."
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
