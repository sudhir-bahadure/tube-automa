import requests
import random
import re
import feedparser
from datetime import datetime
from ypp_script_template import generate_ypp_safe_script, ensure_minimum_duration
from llm_wrapper import llm
from keyword_research import keyword_researcher
import json
import os

# ============================================================================
# MEME ENGINE CONFIGURATION (Loaded from channel_config.json)
# ============================================================================

try:
    with open("channel_config.json", "r") as f:
        CHANNEL_CONFIG = json.load(f)
        MEME_CONFIG = {
            "topic_engine": CHANNEL_CONFIG.get("topic_engine", {}),
            "script_engine": CHANNEL_CONFIG.get("script_engine", {}),
            "ctr_title_generator": CHANNEL_CONFIG.get("ctr_title_generator", {})
        }
except Exception as e:
    print(f"Warning: Could not load channel_config.json: {e}")
    # Fallback default
    MEME_CONFIG = {
        "topic_engine": {
            "emotion_pool": ["stress", "anxiety", "laziness"],
            "situation_pool": ["work", "sleep", "money"],
            "combine_randomly": True
        }
    }

# Tracking for used assets to prevent repetition
INVENTORY_FILE = "assets/used_inventory.json"
USED_JOKES_FILE = "assets/used_jokes.json"

def track_inventory(item_id, category):
    """Save used item to inventory"""
    if not os.path.exists("assets"):
        os.makedirs("assets")
        
    try:
        if os.path.exists(INVENTORY_FILE):
            with open(INVENTORY_FILE, 'r') as f:
                inventory = json.load(f)
        else:
            inventory = {}
            
        if category not in inventory:
            inventory[category] = []
            
        if item_id not in inventory[category]:
            inventory[category].append(item_id)
            with open(INVENTORY_FILE, 'w') as f:
                json.dump(inventory, f, indent=4)
            return True
    except Exception as e:
        print(f"Error tracking inventory: {e}")
    return False

def ensure_assets_dir():
    if not os.path.exists("assets"):
        os.makedirs("assets")

# Initialize directory
ensure_assets_dir()

def generate_viral_meme_topic():
    """
    Uses Gemini to brainstorm 1 absolute viral meme topic.
    Validates against 'assets/used_inventory.json' to ensure NO REPETITION.
    """
    if not os.path.exists(INVENTORY_FILE):
        track_inventory("init", "init")

    # Load used topics for context
    used_topics = []
    try:
        with open(INVENTORY_FILE, "r") as f:
            inv = json.load(f)
            used_topics = inv.get("meme_topics", [])
    except: pass
        
    prompt = f"""
    Act as a Viral Meme Researcher.
    Identify ONE "universal, relatable, painful" topic for a YouTube Short.
    Target Audience: Gen Z/Millennials (Students/Office Workers).
    Themes: Procrastination, Money, Sleep, awkward social interactions, adulthood.
    
    Constraint: CANNOT be one of these used topics: {used_topics[-50:]}
    
    Output ONLY the topic string (e.g. "When you forget your headphones").
    """
    
    topic = llm.generate(prompt).strip().replace('"', '')
    return topic

def generate_meme_script(topic):
    """
    Generates a high-retention script using the Hook -> Situation -> Escalation -> Punchline -> CTA structure.
    Strictly < 38 words.
    """
    prompt = f"""
    Write a script for a viral stickman animation meme about: "{topic}"
    
    Format (JSON):
    [
      {{"text": "Hook line (1-2s)", "visual": "Stickman doing X"}},
      {{"text": "Relatable situation (2-3s)", "visual": "Stickman doing Y"}},
      {{"text": "Escalation/Pain point (2-3s)", "visual": "Stickman reaction Z"}},
      {{"text": "Punchline/Ending (2s)", "visual": "Stickman giving up/crying"}},
      {{"text": "Subscribe for more pain", "visual": "Stickman pointing down"}}
    ]
    
    Rules:
    - TOTAL WORDS must be under 38.
    - Deadpan, relatable, cynical tone.
    - NO generic intros like "Hey guys".
    - The visuals descriptions must be expressive poses.
    - RESPONSE MUST BE PURE JSON.
    """
    
    response = llm.generate(prompt)
    try:
        # Extract JSON list
        json_str = re.search(r'\[.*\]', response, re.DOTALL).group()
        return json.loads(json_str)
    except:
        # Fallback manual parsing if LLM fails JSON
        print("[WARN] JSON parsing failed, using fallback script")
        return [
            {"text": f"POV: {topic}", "visual": "Stickman confused looking at phone"},
            {"text": "You know that feeling when...", "visual": "Stickman sighing deeply"},
            {"text": "And then it gets worse.", "visual": "Stickman facepalming"},
            {"text": "Why is life like this.", "visual": "Stickman lying on floor"},
            {"text": "Subscribe for more pain.", "visual": "Stickman pointing at subscribe button"}
        ]

def generate_content_metadata(mode="meme", tweak=""):
    """
    Main entry point for content generation.
    """
    if mode == "meme":
        topic = generate_viral_meme_topic()
        print(f"[*] Viral Topic Selected: {topic}")
        
        script_data = generate_meme_script(topic)
        
        # Track topic
        track_inventory(topic, "meme_topics")
        
        return {
            "mode": "meme",
            "category": "entertainment",
            "topic": topic,
            "title": f"POV: {topic} #shorts #meme",
            "description": f"Has this ever happened to you? {topic}\n\n#memes #relatable #shorts",
            "tags": ["memes", "relatable", "shorts", "animation", "stickman", "funny"],
            "script": script_data,
            "visual_style": "sketch_static"
        }
    
    elif mode == "noir":
        # Director Mode (Dark Psychology)
        # Tweak allows user override topic
        topic = tweak if tweak else "The Dark Triad in Everyday Life"
        
        print(f"[*] Director Mode Topic: {topic}")
        
        # We use the new LLM method for high-quality scripts
        # Ensure llm_wrapper has this method or use a generic fallback
        try:
            script_data = llm.generate_psychology_short_script(topic)
        except AttributeError:
            # Fallback if method missing in LLM wrapper (should not happen if synced)
            print("[!] LLM Wrapper missing 'generate_psychology_short_script'. Using generic.")
            script_data = generate_meme_script(topic) # Fallback

        if not script_data:
            print("[!] Failed to generate Noir script.")
            return None
            
        return {
            "mode": "noir",
            "category": "education",
            "topic": topic,
            "title": script_data.get("title", f"The Psychology of {topic}"),
            "description": script_data.get("description", "Deep dive."),
            "tags": script_data.get("tags", ["psychology", "noir"]),
            "script": script_data.get("scenes", []),
            "visual_style": "noir",
            "music_mood": script_data.get("music_mood", "tense")
        }

    # Legacy/Long-form support would go here if needed, but we are focusing on MEMES.
    return None

# ============================================================================
# ALIASES FOR COMPATIBILITY WITH main.py
# ============================================================================
def get_meme_metadata(tweak=None):
    return generate_content_metadata(mode="meme", tweak=tweak)

def get_fact(tweak=None):
    """
    Generates a viral psychological/curiosity fact.
    """
    # 1. Brainstorm a unique viral topic
    used_topics = []
    try:
        if os.path.exists(INVENTORY_FILE):
            with open(INVENTORY_FILE, "r") as f:
                inv = json.load(f)
                used_topics = inv.get("fact_topics", [])
    except: pass

    # Refined prompt for Psychology/Mind-blowing facts
    prompt_topic = f"""
    Act as a Mystery/Psychology Researcher.
    Brainstorm ONE "mind-blowing, unheard of, or deeply psychological" fact.
    Constraint: CANNOT be these: {used_topics[-50:]}
    Output ONLY the topic/fact summary (e.g. "The bystander effect in digital spaces").
    """
    topic = llm.generate(prompt_topic).strip().replace('"', '')
    track_inventory(topic, "fact_topics")

    # 2. Generate multi-segment script
    prompt_script = f"""
    Write a high-retention script for a 15-20s video about: "{topic}"
    Format (JSON List of 4-5 segments):
    [
      {{"text": "Hook line that stops the scroll", "visual": "Mysterious scene"}},
      {{"text": "The core fact or data point", "visual": "Data representation/Action"}},
      {{"text": "Why this matters or a twist", "visual": "Reaction/Surreal visual"}},
      {{"text": "Final mind-blowing conclusion", "visual": "Cinematic ending"}},
      {{"text": "Subscribe for more daily facts", "visual": "Subscribe reminder"}}
    ]
    Rules: Total words < 45. Pure JSON only.
    """
    
    response = llm.generate(prompt_script)
    try:
        json_str = re.search(r'\[.*\]', response, re.DOTALL).group()
        script_data = json.loads(json_str)
    except:
        script_data = [
            {"text": f"Did you know about {topic}?", "visual": "Confused emoji"},
            {"text": "It turns out everything we knew was wrong.", "visual": "Shocked pose"},
            {"text": "Stay tuned for more.", "visual": "Pointing finger"}
        ]

    return {
        "mode": "fact",
        "category": "education",
        "topic": topic,
        "title": f"The Mystery of {topic[:40]}... #facts #psychology",
        "description": f"Diving deep into {topic}. Did you know this?\n\n#facts #mystery #shorts",
        "tags": ["facts", "psychology", "mystery", "education", "shorts"],
        "script": script_data,
        "visual_style": "sketch_static"
    }

def get_video_metadata(tweak=None):
    return get_fact(tweak=tweak)

def get_long_video_metadata(tweak=None):
    # Stub
    print("[WARN] Long mode not fully implemented in robust overhaul.")
    return None

if __name__ == "__main__":
    print(generate_content_metadata(mode="meme"))
