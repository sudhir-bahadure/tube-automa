import requests
import random
import re
import feedparser
from datetime import datetime
from ypp_script_template import generate_ypp_safe_script, ensure_minimum_duration
from llm_wrapper import llm
import json
import os

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("Warning: pytrends not available, using fallback trending detection")

# ============================================================================
# TRENDING TOPIC DETECTION (100% FREE)
# ============================================================================

NICHE_KEYWORDS = {
    "Space & Universe": ["space", "mars", "nasa", "telescope", "galaxy", "planet", "asteroid", "moon", "star", "universe", "cosmic"],
    "Mysteries & History": ["ancient", "mystery", "history", "civilization", "artifact", "pyramid", "archaeological", "historical"],
    "Future Tech & AI": ["ai", "robot", "tech", "quantum", "future", "innovation", "artificial intelligence", "machine learning"],
    "Nature & Deep Sea": ["ocean", "sea", "nature", "wildlife", "volcano", "earth", "animal", "marine", "rainforest"]
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

def is_in_inventory(item_id, category):
    """Check if item is already in inventory"""
    if not os.path.exists(INVENTORY_FILE):
        return False
    try:
        with open(INVENTORY_FILE, 'r') as f:
            inventory = json.load(f)
            return item_id in inventory.get(category, [])
    except:
        return False

def load_used_jokes():
    """Load used jokes to prevent repetition"""
    import json
    import os
    from datetime import datetime, timedelta
    
    if os.path.exists(USED_JOKES_FILE):
        try:
            with open(USED_JOKES_FILE, 'r') as f:
                data = json.load(f)
                # Clean old entries (>30 days for jokes)
                cutoff = (datetime.now() - timedelta(days=30)).isoformat()
                cleaned = {k: v for k, v in data.items() if v > cutoff}
                if len(cleaned) < len(data):
                    with open(USED_JOKES_FILE, 'w') as fw:
                        json.dump(cleaned, fw, indent=2)
                return cleaned
        except:
            return {}
    return {}

def save_used_joke(joke_text):
    """Track a used joke"""
    import json
    import os
    from datetime import datetime
    
    used_jokes = load_used_jokes()
    # Use first 50 chars as key
    joke_key = joke_text[:50].lower().strip()
    used_jokes[joke_key] = datetime.now().isoformat()
    try:
        with open(USED_JOKES_FILE, 'w') as f:
            json.dump(used_jokes, f, indent=2)
    except Exception as e:
        print(f"  [WARN] Could not save joke tracking: {e}")

def is_joke_used(joke_text):
    """Check if joke was already used"""
    used_jokes = load_used_jokes()
    joke_key = joke_text[:50].lower().strip()
    return joke_key in used_jokes

def ensure_assets_dir():
    if not os.path.exists("assets"):
        os.makedirs("assets")

# Initialize directory
ensure_assets_dir()

def get_trending_memes_reddit():
    """Fetch trending jokes from Reddit (Free, No API Key)"""
    jokes = []
    subreddits = ['WhitePeopleTwitter', 'NonPoliticalTwitter', 'meirl', 'rareinsults']
    
    for subreddit in subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25"
            headers = {'User-Agent': 'TubeAutoma/1.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                posts = response.json()['data']['children']
                for post in posts:
                    data = post['data']
                    title = data.get('title', '')
                    selftext = data.get('selftext', '')
                    
                    # Skip if already used
                    if is_joke_used(title):
                        continue
                    
                    # Format as setup/punchline
                    if selftext and selftext != '[removed]' and selftext != '[deleted]':
                        jokes.append({
                            'setup': title,
                            'punchline': selftext
                        })
                    elif '?' in title:  # Question format
                        parts = title.split('?', 1)
                        if len(parts) == 2:
                            jokes.append({
                                'setup': parts[0] + '?',
                                'punchline': parts[1].strip()
                            })
        except Exception as e:
            print(f"  [WARN] Reddit r/{subreddit} error: {e}")
            continue
    
    return jokes

def get_google_trends():
    """Fetch trending topics from Google Trends (Free, No API Key)"""
    if not PYTRENDS_AVAILABLE:
        return []
    
    regions = ['united_states', 'india', 'united_kingdom']
    for region in regions:
        try:
            print(f"  [*] Attempting to fetch trends for {region}...")
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
            trending_df = pytrends.trending_searches(pn=region)
            if not trending_df.empty:
                return trending_df[0].tolist()[:15]
        except Exception as e:
            print(f"  [WARN] Google Trends error for {region}: {e}")
            continue
    return []

def get_youtube_trending():
    """Fetch trending topics from YouTube RSS (Free, No API Key)"""
    try:
        url = "https://www.youtube.com/feeds/trending.rss"
        feed = feedparser.parse(url)
        # Filter for topics not already in inventory
        topics = [entry.title for entry in feed.entries if not is_in_inventory(entry.title, "topics")]
        print(f"  - YouTube RSS: Found {len(topics)} new trending topics")
        return topics[:20]
    except Exception as e:
        print(f"YouTube RSS error: {e}")
        return []

def get_reddit_trending(subreddits=['science', 'space', 'Futurology', 'nature']):
    """Fetch trending topics from Reddit (Free, No API Key)"""
    topics = []
    for subreddit in subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
            headers = {'User-Agent': 'TubeAutoma/1.0'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                posts = response.json()['data']['children']
                topics.extend([post['data']['title'] for post in posts])
        except Exception as e:
            print(f"Reddit error for r/{subreddit}: {e}")
            continue
    return topics

def match_topic_to_niche(topic):
    """Match a trending topic to our niches"""
    topic_lower = topic.lower()
    best_match = None
    best_score = 0
    
    for niche, keywords in NICHE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in topic_lower)
        if score > best_score:
            best_score = score
            best_match = niche
    
    return best_match if best_score > 0 else None

def get_trending_video_topic():
    """Get a trending topic that matches our niches (100% Free)"""
    print("\n[*] Fetching trending topics from multiple sources...")
    
    all_topics = []
    
    # 1. Try Google Trends
    try:
        trends = get_google_trends()
        if trends:
            print(f"  - Google Trends: {len(trends)} topics")
            all_topics.extend(trends)
    except:
        pass
    
    # 2. Try YouTube RSS
    try:
        yt_topics = get_youtube_trending()
        if yt_topics:
            print(f"  - YouTube RSS: {len(yt_topics)} topics")
            all_topics.extend(yt_topics)
    except:
        pass
    
    # 3. Try Reddit
    try:
        reddit_topics = get_reddit_trending()
        if reddit_topics:
            print(f"  - Reddit: {len(reddit_topics)} topics")
            all_topics.extend(reddit_topics)
    except:
        pass
    
    # Match topics to our niches
    matched_topics = []
    for topic in all_topics:
        niche = match_topic_to_niche(topic)
        if niche:
            matched_topics.append((topic, niche))
    
    if matched_topics:
        # Select from top matches
        selected = random.choice(matched_topics[:10])
        print(f"\n[OK] Selected trending topic: '{selected[0]}' (Niche: {selected[1]})")
        return selected[0], selected[1]
    
    # Fallback to high-quality viral fact niches
    viral_fallback_topics = [
        ("The mystery of the Voynich Manuscript", "Mysteries & History"),
        ("Why time might be an illusion", "Future Tech & AI"),
        ("The secret life of deep sea creatures", "Nature & Deep Sea"),
        ("How AI will change the world in 2026", "Future Tech & AI"),
        ("The engineering marvel of the Great Pyramids", "Mysteries & History")
    ]
    selected_fallback = random.choice(viral_fallback_topics)
    print(f"\n[OK] Using robust fallback topic: '{selected_fallback[0]}'")
    return selected_fallback[0], selected_fallback[1]

# ============================================================================
# EXISTING FUNCTIONS
# ============================================================================

def get_trending_facts_reddit():
    """Fetch trending facts from Reddit science/TIL (Free, No API Key)"""
    facts = []
    subreddits = ['todayilearned', 'science', 'Damnthatsinteresting']
    
    for subreddit in subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=20"
            headers = {'User-Agent': 'TubeAutoma/1.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                posts = response.json()['data']['children']
                for post in posts:
                    data = post['data']
                    title = data.get('title', '')
                    
                    # Skip if already used
                    if is_joke_used(title):  # Reuse joke tracking for facts
                        continue
                    
                    # Clean up TIL prefix
                    if title.startswith('TIL '):
                        title = title[4:]
                    elif title.startswith('TIL: '):
                        title = title[5:]
                    
                    # Only include if it's educational/interesting
                    if len(title) > 30 and len(title) < 200:
                        facts.append(title)
        except Exception as e:
            print(f"  [WARN] Reddit r/{subreddit} error: {e}")
            continue
    
    return facts

def get_fact():
    # Fallback facts if API fails
    facts = [
        "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.",
        "Octopuses have three hearts. Two pump blood to the gills, while the third pumps it to the rest of the body.",
        "Bananas are berries, but strawberries aren't. Botanically speaking, true berries arise from a single flower with one ovary.",
        "A day on Venus is longer than a year on Venus. It takes Venus 243 Earth days to rotate once on its axis, but only 225 Earth days to orbit the Sun.",
        "There are more trees on Earth than stars in the Milky Way. Estimates suggest 3 trillion trees vs. 100-400 billion stars.",
        "The Eiffel Tower can be 15 cm taller during the summer. Thermal expansion causes the iron structure to grow when it gets hot.",
        "Wombat poop is cube-shaped. This prevents it from rolling away and marks their territory effectively.",
        "Human teeth are the only part of the body that cannot heal themselves. They lack the cells necessary for regeneration.",
        "The shortest war in history lasted 38 to 45 minutes. It was between Britain and Zanzibar on August 27, 1896.",
        "A cloud weighs around a million tonnes. A typical cumulus cloud has a volume of about one cubic kilometer."
    ]
    
    # Fetch 3 unique facts to make the video longer (~40s)
    facts_collection = []
    
    # Attempt to fetch 5 times to get 3 unique facts
    for _ in range(5):
        if len(facts_collection) >= 3:
            break
        try:
            response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=5)
            if response.status_code == 200:
                text = response.json()['text']
                if text not in facts_collection:
                    facts_collection.append(text)
        except:
            pass
            
    # Fallback if API fails
    if len(facts_collection) < 3:
        needed = 3 - len(facts_collection)
        facts_collection.extend(random.sample(facts, needed))
        
    # Combine with transitions
    transitions = [
        " And did you know...",
        " Here is another mind-blowing fact.",
        " Also...",
        " Listen to this.",
        " You won't believe this next one."
    ]
    
    final_script = facts_collection[0]
    for i in range(1, len(facts_collection)):
        final_script += f"{random.choice(transitions)} {facts_collection[i]}"
        
    return final_script

def get_meme_metadata():
    print("\n[*] Fetching high-quality memes from Reddit...")
    
    # Try to get trending jokes from Reddit
    raw_jokes = get_trending_memes_reddit()
    
    memes_list = []
    if raw_jokes:
        print(f"  [PROCESS] Filtering {len(raw_jokes)} jokes for humor quality...")
        random.shuffle(raw_jokes)
        for joke in raw_jokes:
            # Check if used
            if is_joke_used(joke['setup']):
                continue
                
            # AI Humor Verification (only for non-dad joke subreddits)
            if llm.verify_humor(f"{joke['setup']} {joke['punchline']}"):
                memes_list.append(joke)
                save_used_joke(joke['setup'])
                if len(memes_list) >= 5:
                    break
        
    if len(memes_list) < 5:
        # Fallback to high-quality curated modern humor
        print(f"  [OK] Supplementing with curated modern humor...")
        fallback_pool = [
            {"setup": "My boss told me to have a good day.", "punchline": "So I went home."},
            {"setup": "I put my phone on airplane mode.", "punchline": "It's been 2 hours and it still hasn't flown anywhere. Scammed."},
            {"setup": "Me: I need to save money.", "punchline": "Also me: *buys something I don't need* 'Self care is important.'"},
            {"setup": "I followed my heart today.", "punchline": "It led me straight to the fridge."},
            {"setup": "I told my doctor I broke my arm in two places.", "punchline": "He told me to stop going to those places."},
            {"setup": "My bank account is basically a 'Don't Open, Dead Inside' meme.", "punchline": "I'm scared of my own balance."},
            {"setup": "I have a lot of jokes about unemployed people.", "punchline": "But none of them work."},
            {"setup": "I didn't think for a second that I would be this tired.", "punchline": "And yet, here I am, exhausted after doing absolutely nothing."}
        ]
        needed = 5 - len(memes_list)
        available_fallbacks = [f for f in fallback_pool if not is_joke_used(f['setup'])]
        if len(available_fallbacks) < needed:
            available_fallbacks = fallback_pool # Reset if exhausted
        memes_list.extend(random.sample(available_fallbacks, needed))
    
    # Combined script text
    full_script_text = " ".join([f"{m['setup']} {m['punchline']}" for m in memes_list])
    
    # Hashtags
    hashtags = "#Memes #Funny #Relatable #ModernHumor #Shorts #DailyMeme #Comedy"
    
    return {
        "mode": "meme",
        "memes": memes_list,
        "text": full_script_text,
        "title": f"Daily Meme Therapy! 😂 High-Res Humor",
        "description": f"Audience choice! These memes are actually funny.\n\n{hashtags}",
        "tags": hashtags,
        "youtube_category": "23" 
    }


def get_video_metadata():
    """Get high-quality video metadata using AI (Shorts)"""
    print("\n[*] Generating high-quality metadata using AI...")
    topic_result = get_trending_video_topic()
    if isinstance(topic_result, tuple):
        topic, category = topic_result
    else:
        topic, category = topic_result, "curiosity"
    
    if not topic:
        topic = "the mystery of time"
    
    # Check if we already used this exact topic recently
    if is_in_inventory(topic, "topics"):
        # Try once more for a fresh topic
        topic_result = get_trending_video_topic()
        if isinstance(topic_result, tuple):
            topic, category = topic_result
            
    ai_script = llm.generate_script(topic, video_type="short", niche=category)
    
    if ai_script:
        track_inventory(topic, "topics")
        return {
            "title": ai_script.get("title", f"The Truth About {topic}"),
            "topic": topic,
            "script": [
                {
                    "text": seg["text"],
                    "type": "context",
                    "keyword": random.choice(seg["visual_keywords"]) if seg.get("visual_keywords") else topic
                } for seg in ai_script.get("script_segments", [])
            ],
            "tags": " ".join([f"#{t.replace(' ', '')}" for t in ai_script.get("tags", ["facts", topic])]),
            "keywords": [seg.get("visual_keywords", [topic]) for seg in ai_script.get("script_segments", [])],
            "stickman_poses": [seg.get("stickman_poses", ["standing normally", "standing relaxed"]) for seg in ai_script.get("script_segments", [])]
        }
    
    # Fallback if AI fails
    print("  [WARN] AI generation failed, using fallback templates")
    import wikipedia
    try:
        page = wikipedia.page(topic, auto_suggest=False)
        sentences = page.summary.split('.')
        script = generate_ypp_safe_script(topic, sentences)
        return {
            "title": f"The Untold Story of {topic}",
            "topic": topic,
            "script": script,
            "tags": f"#facts #{topic.replace(' ', '')} #education"
        }
    except:
        return None

def get_long_video_metadata():
    """Get high-retention long-form video metadata using AI"""
    print("\n[*] Generating high-retention long-form metadata using AI...")
    topic_result = get_trending_video_topic()
    if isinstance(topic_result, tuple):
        topic, category = topic_result
    else:
        topic, category = topic_result, "documentary"

    if not topic:
        topic = "the evolution of intelligence"

    ai_script = llm.generate_script(topic, video_type="long", niche=category)
    
    if ai_script:
        track_inventory(topic, "topics")
        segments = [
            {
                "text": seg["text"],
                "keyword": random.choice(seg["visual_keywords"]) if seg.get("visual_keywords") else topic,
                "stickman_poses": seg.get("stickman_poses", ["standing normally", "standing relaxed"])
            } for seg in ai_script.get("script_segments", [])
        ]
        
        title = ai_script.get("title", f"{topic}: The Complete Story")
        hashtags = " ".join([f"#{t.replace(' ', '')}" for t in ai_script.get("tags", ["documentary", topic])])
        
        return {
            "mode": "long",
            "topic": topic,
            "segments": segments,
            "title": f"{title} 🎥",
            "description": f"{title}\n\n{hashtags}\n\nJoin us as we deep dive into {topic}.",
            "tags": hashtags,
            "youtube_category": "27" if "Space" in str(category) or "Tech" in str(category) else "28"
        }

    # Fallback is handled by legacy logic if needed (already in file)
    return None

def fetch_wikipedia_content(topic):
    """
    Fetch Wikipedia content for a given topic.
    Returns a dictionary with summary, sections, and key facts.
    """
    try:
        # Wikipedia API endpoint
        search_url = "https://en.wikipedia.org/w/api.php"
        
        # First, search for the topic to get the exact page title
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": topic,
            "format": "json",
            "srlimit": 1
        }
        
        search_response = requests.get(search_url, params=search_params, timeout=10)
        if search_response.status_code != 200:
            return None
            
        search_data = search_response.json()
        if not search_data.get('query', {}).get('search'):
            return None
            
        page_title = search_data['query']['search'][0]['title']
        
        # Now fetch the page content
        content_params = {
            "action": "query",
            "prop": "extracts|info",
            "exintro": False,
            "explaintext": True,
            "titles": page_title,
            "format": "json",
            "inprop": "url"
        }
        
        content_response = requests.get(search_url, params=content_params, timeout=10)
        if content_response.status_code != 200:
            return None
            
        content_data = content_response.json()
        pages = content_data.get('query', {}).get('pages', {})
        
        if not pages:
            return None
            
        page = list(pages.values())[0]
        extract = page.get('extract', '')
        wiki_url = page.get('fullurl', '')
        
        # Split into sentences for processing
        sentences = re.split(r'(?<=[.!?])\s+', extract)
        
        # Filter out very short sentences and section headers
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30 and not s.strip().endswith('==')]
        
        return {
            "title": page_title,
            "url": wiki_url,
            "sentences": sentences[:50],  # Limit to first 50 good sentences
            "full_text": extract[:3000]  # First 3000 chars
        }
        
    except Exception as e:
        print(f"Wikipedia fetch error: {e}")
        return None


if __name__ == "__main__":
    print(get_video_metadata())
