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
    
    # Legacy/Long-form support would go here if needed, but we are focusing on MEMES.
    return None

if __name__ == "__main__":
    print(generate_content_metadata(mode="meme"))
