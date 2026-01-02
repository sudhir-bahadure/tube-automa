import feedparser
import json
import os
import random
import datetime

# Path to files
ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets')
PLAN_FILE = os.path.join(ASSETS_DIR, 'daily_plan.json')
DIRECTIVES_FILE = os.path.join(ASSETS_DIR, 'analyst_directives.json')

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
        
    return trends

def fetch_backup_trends():
    """Evergreen viral topics if live fetch fails"""
    return [
        "Artificial Intelligence", "Space Exploration", "Psychology Facts", 
        "Ancient Civilizations", "Deep Sea Mysteries", "Future Technology",
        "Human Behavior", "Life Hacks", "Optical Illusions"
    ]

def determine_strategy(trends):
    """Decide on the day's content strategy based on trends"""
    
    # 1. Select Main Topic (The "Hero" Topic)
    # Prefer topics that are substantive (good for long video/facts)
    if not trends:
        trends = fetch_backup_trends()
    
    hero_topic = random.choice(trends)
    
    # --- Analyst Integration ---
    if os.path.exists(DIRECTIVES_FILE):
        try:
            with open(DIRECTIVES_FILE, 'r', encoding='utf-8') as f:
                directives = json.load(f)
            
            # Check if directive is reasonably fresh (e.g., from last 7 days)
            gen_time_str = directives.get("generated_at")
            if gen_time_str:
                gen_time = datetime.datetime.fromisoformat(gen_time_str)
                now = datetime.datetime.now()
                if (now - gen_time).days < 8:
                    winning_topic = directives.get("winning_topic")
                    if winning_topic and winning_topic != "unknown":
                        print(f"[*] Brain: Analyst Directive Found! Pivoting to: '{winning_topic}'")
                        hero_topic = winning_topic
        except Exception as e:
            print(f"[!] Brain: Failed to read Analyst Directives: {e}")
    # ---------------------------

    print(f"[*] Brain: Selected Hero Topic of the Day: '{hero_topic}'")

    # 2. Plan Meme Content
    # Memes can ride variables of the trend or fallback to general humor
    meme_plan = {
        "theme_mode": "trending_or_random",
        "forced_topic": hero_topic,
        "backup_theme": {
             "subreddit": "memes",
             "hashtags": f"#{hero_topic.replace(' ', '')} #Trending #Viral #Funny"
        }
    }

    # 3. Plan Fact Content
    # Fact video MUST be about the hero topic to be relevant
    fact_plan = {
        "topic": hero_topic,
        "search_query": f"interesting facts about {hero_topic}"
    }

    # 4. Plan Long Video
    # Documentary style on the hero topic
    long_plan = {
        "topic": hero_topic,
        "title_concept": f"Why Everyone is Talking About {hero_topic}",
        "search_query": hero_topic
    }
    
    return {
        "generated_at": datetime.datetime.now().isoformat(),
        "today_topic": hero_topic,
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
    print(json.dumps(plan, indent=2))

if __name__ == "__main__":
    main()
