import os
import google.generativeai as genai
import time
import random

# Configure Logger
import logging
logger = logging.getLogger(__name__)

class GeminiWrapper:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.is_active = False
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Updated to latest model (gemini-pro is deprecated)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.is_active = True
                print("  [AI] Gemini API configured successfully.")
            except Exception as e:
                print(f"  [AI] Failed to configure Gemini: {e}")
        else:
            print("  [AI] No GEMINI_API_KEY found. Using static content.")

    def generate_script(self, topic, mood="viral_shock"):
        """
        Generates a 30-40s YouTube Short script using Gemini.
        Returns a dictionary or None if failed.
        """
        if not self.is_active:
            return None

        # RATE LIMIT SAFETY (15 RPM for Free Tier)
        # We assume this isn't called in a tight loop, but a small sleep helps.
        time.sleep(2) 

        prompt = self._get_prompt(topic, mood)
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            print(f"  [AI] Generation failed: {e}")
            return None

    def _get_prompt(self, topic, mood):
        """Constructs safe, high-quality prompts."""
        if mood == "viral_shock":
            return f"""
            Write a VIRAL YouTube Short script (approx 30-40 seconds) about: "{topic}".
            
            STRICT RULES:
            1.  **Hook**: Must be a ONE-LINE shocker/question. Start with "Did you know" or "What if".
            2.  **Accuracy**: STRICTLY FACTUAL. Do not hallucinate.
            3.  **Engagement Architecture**:
                - **0-3s**: Hook (Visual/Audio shock)
                - **3-15s**: The "Build Up" (Create mystery)
                - **15-25s**: The "Twist/Reveal" (The pay-off)
                - **25-30s**: **The Comment Bait**: Ask a specific question related to the topic (e.g., "Would you try this?" or "Type YES if you knew").
                - **30s+**: CTA: "Subscribe for more!"
            4.  **Formatting**: Return raw text with [PAUSE Xs] tags.
            5.  **Tone**: Energetic, Viral, High-Retention.
            
            OUTPUT FORMAT ONLY (No other text):
            Hook: [Insert Hook]
            Body: [Insert Body with Pauses]
            CTA: [Insert Comment Question + Subscribe]
            Keyword: [Single Visual Keyword]
            """
        elif mood == "meme":
            return f"""
            Write a FUNNY/MEME YouTube Short script (30-40s) about: "{topic}".
            
            STRICT RULES:
            1.  **Tone**: HILARIOUS, Relatable, Casual, "Gen Z" humor allowed.
            2.  **Structure**: 
                - Setup (Relatable situation)
                - Punchline (The twist/joke)
                - "Comment Bait": Ask "Who else does this?" or "Tag a friend who..."
            3.  **Context**: Topic is "{topic}". Make it a joke or funny observation.
            4.  **Formatting**: Return raw text with [PAUSE Xs] tags.
            
            OUTPUT FORMAT ONLY:
            Hook: [Funny One-Liner]
            Body: [The Joke/Story with Pauses]
            CTA: [Funny CTA]
            Keyword: [Visual Vibe]
            """
        elif mood == "tech_tutorial":
            return f"""
            Write a high-quality TECH EXPLAINER script (approx 60-90 seconds) about: "{topic}".
            
            STRICT RULES:
            1.  **Goal**: Explain a complex tech concept or solve a specific PC/Software problem simply.
            2.  **Tone**: Professional, Helpful, Authoritative but Accessible.
            3.  **Structure**:
                - Problem: "Is your PC slow?" / "What is Quantum Computing?"
                - Solution/Explanation: Step-by-step or clear analogy.
                - Value: Why this matters.
                - CTA: "Save this for later."
            4.  **Formatting**: Return raw text with [PAUSE Xs] tags.
            
            OUTPUT FORMAT ONLY:
            Hook: [Problem Statement]
            Body: [The Solution/Explanation]
            CTA: [Helpful CTA]
            Keyword: [Technical Keyword]
            """
        elif mood == "meme_history":
            return f"""
            Write a deep-dive INTERNET CULTURE / MEME HISTORY script (approx 90 seconds) about: "{topic}".
            
            STRICT RULES:
            1.  **Goal**: Analyze why a specific meme, trend, or internet moment became iconic.
            2.  **Tone**: Analytical, Energetic, Slightly "Insider" tone (uses internet slang correctly).
            3.  **Structure**:
                - Origin: Where did it start?
                - Viral Moment: Why did it explode?
                - Impact: How did it change the internet?
                - CTA: "Drop a 👀 if you remember this era."
            4.  **Formatting**: Return raw text with [PAUSE Xs] tags.
            
            OUTPUT FORMAT ONLY:
            Hook: [The Hook]
            Body: [The Analytical Breakdown]
            CTA: [Engagement CTA]
            Keyword: [Vibe/Nostalgia Keyword]
            """
        return ""

    def _parse_response(self, text):
        """Parses the text output into a structured dict."""
        lines = text.split('\n')
        data = {"hook": "", "script": "", "cta": "", "keyword": ""}
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith("Hook"):
                current_section = "hook"
                data["hook"] = line.split(":", 1)[1].strip()
            elif line.startswith("Body"):
                current_section = "script"
                data["script"] = line.split(":", 1)[1].strip()
            elif line.startswith("CTA"):
                current_section = "cta"
                data["cta"] = line.split(":", 1)[1].strip()
            elif line.startswith("Keyword"):
                data["keyword"] = line.split(":", 1)[1].strip()
            elif current_section:
                # Append continuation lines
                data[current_section] += " " + line
        
        # Validation
        if data["hook"] and data["script"]:
            return {
                "category": "AI GENERATED",
                "concept": data["hook"], # Used for 'topic' tracking
                "image_keyword": data["keyword"] or topic,
                **data
            }
        return None

if __name__ == "__main__":
    # Test
    gemini = GeminiWrapper()
    if gemini.is_active:
        print(gemini.generate_script("Quantum Physics"))
