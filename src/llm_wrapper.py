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
            clean_text = text.replace("```json", "").replace("```", "").strip()
            # Basic JSON extraction if AI includes filler
            if "[" in clean_text:
                clean_text = clean_text[clean_text.find("["):clean_text.rfind("]")+1]
            return json.loads(clean_text)
        except Exception as e:
            print(f"Error parsing titles: {e}")
            return []

    def generate_psychology_script(self, title):
        """Generates a long-form psychology script with 25+ animated scenes."""
        prompt = f"""
        Title: {title}
        Act as a lead writer for a top-tier US psychology channel.
        
        STRICT RULES:
        1. Break the script into AT LEAST 25 detailed scenes for a high-quality visual experience.
        2. Visual Style: 'Surrealist Psychological Noir'. Use ink wash textures, moody watercolor, deep shadows, and metaphorical imagery.
        3. NO REAL HUMANS: Use silhouettes, faceless figures, metaphorical objects (clocks, keys, mirrors), or abstract anatomical sketches. THIS IS CRITICAL.
        4. Tone: Deep, narrative-driven, and emotionally resonant.
        5. Visual Continuity: Maintain a consistent atmospheric color palette throughout all scenes.

        STRICT OUTPUT FORMAT (Valid JSON ONLY):
        {{
            "title": "{title}",
            "description": "The professional description...",
            "scenes": [
                {{
                    "text": "The spoken narration...",
                    "visual_prompt": "A surrealist ink wash of [metaphor], psychological noir style, deep shadows, no real humans, high contrast, cinematic lighting, 8k"
                }},
                ... (repeat for 25+ scenes)
            ]
        }}
        """
        try:
            text = self._call_gemini(prompt)
            if not text: return None
            clean_text = text.replace("```json", "").replace("```", "").strip()
            if "{" in clean_text:
                clean_text = clean_text[clean_text.find("{"):clean_text.rfind("}")+1]
            return json.loads(clean_text)
        except Exception as e:
            print(f"Error parsing script: {e}")
            return None

    def generate_psychology_short_script(self, title):
        """Generates a 60-second viral psychology short script with 12 animated scenes."""
        prompt = f"""
        Title: {title}
        Objective: Create a 60-second viral psychology short script.
        
        STRICT RULES:
        1. Break the script into EXACTLY 18 scenes for fast-paced, high-engagement visuals.
        2. Visual Style: 'Surrealist Psychological Noir'. Ink wash, moody watercolor, metaphorical.
        3. NO REAL HUMANS: Use silhouettes, abstract figures, or metaphorical symbols. DO NOT INCLUDE FACES.
        4. Tone: Captivating and fast-paced.
        5. Visual Continuity: Ensure every scene feels like part of the same dark, surreal world.

        Return ONLY Valid JSON.
        {{
            "title": "{title}",
            "scenes": [
                {{
                    "text": "spoken text (approx 5 seconds)...",
                    "visual_prompt": "A cinematic, psychological noir illustration of [metaphor], surreal ink textures, no humans, atmospheric lighting, 8k"
                }},
                ... (repeat for 12 scenes)
            ]
        }}
        """
        try:
            text = self._call_gemini(prompt)
            if not text: return None
            clean_text = text.replace("```json", "").replace("```", "").strip()
            if "{" in clean_text:
                clean_text = clean_text[clean_text.find("{"):clean_text.rfind("}")+1]
            return json.loads(clean_text)
        except Exception as e:
            print(f"Error parsing short script: {e}")
            return None
    def generate_conversational_script(self, topic, type="short"):
        """Generates a high-SEO, human-like script with dynamic stickman movements."""
        char_count = "7000-9000" if type == "long" else "600-800"
        scene_count = 25 if type == "long" else 12
        
        prompt = f"""
        Topic: {topic}
        Role: A charismatic YouTube storyteller/psychologist who is funny, relatable, and high-energy.
        
        STRICT RULES:
        1. SEO Metadata: Provide a viral title, keyword-rich tags, and a detailed description.
        2. Chapters (Long-form only): Create curiosity-driven chapters starting at 00:00 (e.g., "00:00 Why do we feel this?"). Use questions.
        3. End Hook: The FINAL scene must be a powerful Call to Action (CTA) asking viewers to comment "Ready" if they reached the end.
        4. No Watermarks: NEVER mention text, QR codes, or watermarks in visual_prompt.
        5. Script-Aware Animation: Assign a 'vocal_action' to every scene from this list: [jumping, waving, bouncing, shaking, talking, thinking, walking].
        6. Vocal Emotions: Assign 'audio_mood' (excited, serious, whispering, curious, neutral). Use expressive punctuation.
        7. Tone: Conversational, simple, and funny.
        
        FORMAT (Valid JSON ONLY):
        {{
            "title": "{topic}",
            "description": "Premium SEO description with keywords...",
            "tags": ["psychology", "mindset", ...],
            "chapters": ["00:00 Hook", "01:30 The Secret", ...],
            "scenes": [
                {{
                    "text": "spoken narration...",
                    "audio_mood": "excited",
                    "vocal_action": "jumping",
                    "visual_prompt": "A minimalist black stick figure on PLAIN WHITE background [action], doodle style, clean lines, NO TEXT, NO QR CODE"
                }},
                ... (repeat for {scene_count} scenes)
            ]
        }}
        """
        try:
            text = self._call_gemini(prompt)
            if not text: return None
            clean_text = text.replace("```json", "").replace("```", "").strip()
            if "{" in clean_text:
                clean_text = clean_text[clean_text.find("{"):clean_text.rfind("}")+1]
            return json.loads(clean_text)
        except Exception as e:
            print(f"Error parsing conversational script: {e}")
            return None
