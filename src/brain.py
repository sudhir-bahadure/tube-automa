import feedparser
import json
import os
import random
import datetime

# Path to files
ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets')
PLAN_FILE = os.path.join(ASSETS_DIR, 'daily_plan.json')
DIRECTIVES_FILE = os.path.join(ASSETS_DIR, 'analyst_directives.json')
HISTORY_FILE = os.path.join(ASSETS_DIR, 'strategy_history.json')

# Niche Weighting (Focus on Meme/Internet Culture)
# Niche Weighting (Focus on High-CPM AI & Tech Solutions)
NICHE_WEIGHTS = {
    "AI Agents": 2.0,
    "Large Language Models": 1.8,
    "Generative AI": 1.7,
    "OpenAI News": 1.6,
    "Nvidia Blackwell": 1.6,
    "AI Productivity Tools": 1.5,
    "Software Solutions": 1.3,
    "Internet Culture": 1.2,
    "Tech Trends": 1.3,
    "Cybersecurity": 1.1
}

def fetch_google_trends():
    """Fetch top daily trending searches from Google Trends RSS (US)"""
    print("[*] Brain: Scanning Google Trends (US)...")
    trends = []
    try:
        # Google Trends RSS for United States
        feed_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        feed = feedparser.parse(feed_url)
        
        if feed.entries:
            for entry in feed.entries[:15]: # Top 15 trends
                trends.append(entry.title)
    except Exception as e:
        print(f"[!] Brain: Google Trends fetch failed: {e}")
        
    # Priority AI Keywords to inject if trends are unrelated
    ai_keywords = ["AI Agent", "LLM", "Generative AI", "Nvidia", "OpenAI", "ChatGPT", "Claude AI"]
    for kw in ai_keywords:
        trends.insert(0, kw)
        
    return trends

def fetch_backup_trends():
    """Evergreen viral AI and tech problem topics if live fetch fails"""
    return [
        "Best Free AI Video Editors", "How to Fix Windows Update Errors", "Top 5 Chrome Extensions for Productivity", 
        "Free ChatGPT Alternatives", "How to Recover Deleted Files", "Best AI Image Generators for Free",
        "How to Speed Up Slow Laptop", "Secret Mac Shortcuts", "Easy AI Branding Tools"
    ]

def load_history():
    """Load selection history to avoid over-repetition and evolve strategy"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(history):
    """Save selection history"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"[!] Brain: Failed to save history: {e}")

def evolve_trends(trends, history):
    """Evolve trend selection based on history and weights"""
    today_str = datetime.date.today().isoformat()
    
    # 1. Score each trend
    scored_trends = []
    for t in trends:
        score = 1.0
        # Apply Niche Weight if recognized
        score *= NICHE_WEIGHTS.get(t, 1.0)
        
        # Penalize if used recently (Recency bias)
        times_used = history.get("topics", {}).get(t, {}).get("count", 0)
        last_used = history.get("topics", {}).get(t, {}).get("last_used")
        
        if last_used:
            days_since = (datetime.date.today() - datetime.date.fromisoformat(last_used)).days
            if days_since < 14: # Penalize if used in last 2 weeks
                score *= 0.1 # Heavy penalty to ensure variety
            elif days_since < 30:
                score *= 0.5
        
        # Reward if it's a "trending" trend (not a backup)
        if t not in fetch_backup_trends():
            score *= 2.0 
            
        scored_trends.append((t, score))
    
    # Sort and pick
    scored_trends.sort(key=lambda x: x[1], reverse=True)
    
    # Evolution part: Return top 5 potential candidates, determine_strategy will pick the best
    return scored_trends[:5]

def determine_strategy(trends):
    """Decide on the day's content strategy based on trends and evolution"""
    history = load_history()
    
    # 1. Select Main Topic (The "Hero" Topic)
    if not trends:
        trends = fetch_backup_trends()
    
    # Evolve the trends list
    candidates = evolve_trends(trends, history)
    hero_topic = candidates[0][0] if candidates else random.choice(trends)
    
    # --- PART 2 DETECTION ---
    is_part_2 = False
    times_used = history.get("topics", {}).get(hero_topic, {}).get("count", 0)
    if times_used > 0:
        print(f"[*] Brain: Topic '{hero_topic}' has been used before. Marking as PART 2.")
        is_part_2 = True
    # -------------------------
    # --- Analyst Integration (The Ultimate Evolution Signal) ---
    is_analyst_pick = False
    if os.path.exists(DIRECTIVES_FILE):
        try:
            with open(DIRECTIVES_FILE, 'r', encoding='utf-8') as f:
                directives = json.load(f)
            
            gen_time_str = directives.get("generated_at")
            if gen_time_str:
                gen_time = datetime.datetime.fromisoformat(gen_time_str)
                now = datetime.datetime.now()
                if (now - gen_time).days < 8:
                    winning_topic = directives.get("winning_topic")
                    if winning_topic and winning_topic != "unknown":
                        print(f"[*] Brain: Analyst Directive Found! Pivoting to: '{winning_topic}'")
                        hero_topic = winning_topic
                        is_analyst_pick = True
        except Exception as e:
            print(f"[!] Brain: Failed to read Analyst Directives: {e}")
    # ---------------------------

    print(f"[*] Brain: Selected Hero Topic of the Day: '{hero_topic}'")
    
    # Update History
    history.setdefault("topics", {})
    history["topics"].setdefault(hero_topic, {"count": 0, "last_used": ""})
    history["topics"][hero_topic]["count"] += 1
    history["topics"][hero_topic]["last_used"] = datetime.date.today().isoformat()
    history["last_updated"] = datetime.datetime.now().isoformat()
    save_history(history)

    # 2. Plan Meme Content
    meme_plan = {
        "theme_mode": "trending_or_random",
        "forced_topic": hero_topic,
        "is_analyst_pick": is_analyst_pick,
        "backup_theme": {
             "subreddit": "memes",
             "hashtags": f"#{hero_topic.replace(' ', '')} #Trending #Viral #Funny"
        }
    }

    # 3. Plan Fact Content
    fact_plan = {
        "topic": hero_topic,
        "search_query": f"interesting facts about {hero_topic}"
    }

    # 4. Plan Long Video
    long_plan = {
        "topic": hero_topic,
        "title_concept": f"Why Everyone is Talking About {hero_topic}",
        "search_query": hero_topic
    }
    
    return {
        "generated_at": datetime.datetime.now().isoformat(),
        "today_topic": hero_topic,
        "is_analyst_boosted": is_analyst_pick,
        "is_part_2": is_part_2,
        "all_trends_snapshot": trends,
        "meme": meme_plan,
        "fact": fact_plan,
        "long": long_plan
    }

def main():
    # Ensure assets dir exists
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)

    # 1. Fetch
    trends = fetch_google_trends()
    
    # 2. Plan
    plan = determine_strategy(trends)
    
    # 3. Save
    with open(PLAN_FILE, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
        
    print(f"[*] Brain: Daily Plan Generated & Saved to {PLAN_FILE}")
    # print(json.dumps(plan, indent=2))

if __name__ == "__main__":
    main()
