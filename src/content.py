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
    subreddits = ['Jokes', 'dadjokes', 'cleanjokes']
    
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
        topics = [entry.title for entry in feed.entries[:20]]
        return topics
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
    
    # Fallback to curated topics
    print("\n[WARN] No trending matches found, using curated topics")
    return None, None

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
    print("\n[*] Fetching trending memes from Reddit...")
    
    # Try to get trending jokes from Reddit
    trending_jokes = get_trending_memes_reddit()
    
    if trending_jokes and len(trending_jokes) >= 5:
        # Use trending jokes
        print(f"  [OK] Found {len(trending_jokes)} trending jokes from Reddit")
        # Select 5 random jokes from trending
        import random
        selected_jokes = random.sample(trending_jokes, min(5, len(trending_jokes)))
        
        # Track used jokes
        for joke in selected_jokes:
            save_used_joke(joke['setup'])
        
        memes_list = selected_jokes
    else:
        # Fallback to curated jokes
        print(f"  [WARN] Using curated jokes (trending not available)")
        memes_list = [
            {"setup": "Why don't scientists trust atoms?", "punchline": "Because they make up everything!"},
            {"setup": "What do you call a bear with no teeth?", "punchline": "A gummy bear!"},
            {"setup": "Why did the scarecrow win an award?", "punchline": "He was outstanding in his field!"},
            {"setup": "What do you call fake spaghetti?", "punchline": "An impasta!"},
            {"setup": "Why don't eggs tell jokes?", "punchline": "They'd crack each other up!"}
        ]
    
    # Combine scripts for description/tts if needed, but generator will handle individual clips
    full_script_text = " ".join([f"{m['setup']} {m['punchline']}" for m in memes_list])
    
    # Hashtags
    hashtags = "#Memes #Funny #DailyMemes #Humor #Shorts #Jokes #Compilation"
    
    return {
        "mode": "meme",
        "memes": memes_list,  # List of {setup, punchline}
        "text": full_script_text, # Legacy support
        "title": f"Daily Meme Therapy! 😂 ({len(memes_list)} Jokes)",
        "description": f"Enjoy these funny jokes!\n\n{hashtags}",
        "tags": hashtags,
        "youtube_category": "23" # Comedy
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
            "keywords": [seg.get("visual_keywords", [topic]) for seg in ai_script.get("script_segments", [])]
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
                "keyword": random.choice(seg["visual_keywords"]) if seg.get("visual_keywords") else topic
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

def get_long_video_metadata():
    # Try to get trending topic first
    trending_topic, trending_niche = get_trending_video_topic()
    
    if trending_topic and trending_niche:
        # Use trending topic
        topic = trending_topic
        niche_name = trending_niche
        print(f"[*] Using TRENDING topic: {topic}")
    else:
        # Fallback to curated topics
        print(f"[*] Using CURATED topic (trending not available)")
        niches = {
            "Space & Universe": [
                "Black Holes", "Mars Exploration", 
                "Nebulas", "Heat Death of the Universe",
                "James Webb Space Telescope"
            ],
            "Mysteries & History": [
                "Atlantis", "Antikythera Mechanism",
                "Egyptian Pyramids", "Voynich Manuscript",
                "Roman Empire"
            ],
            "Future Tech & AI": [
                "Artificial Intelligence", "Quantum Computing",
                "Neuralink", "Humanoid Robots",
                "Autonomous Vehicles"
            ],
            "Nature & Deep Sea": [
                "Deep Sea Creatures", "Amazon Rainforest",
                "Evolution", "Volcanic Eruptions",
                "Mariana Trench"
            ]
        }
        
        niche_name = random.choice(list(niches.keys()))
        topic = random.choice(niches[niche_name])
    
    # Fetch Wikipedia content
    wiki_data = fetch_wikipedia_content(topic)
    
    # Enhanced structure for 10+ minute video (15 segments)
    # Each segment will be 40-50 seconds = ~10-12 minutes total
    segments = []
    
    if wiki_data and len(wiki_data['sentences']) >= 10:
        # We have good Wikipedia data - use it!
        sentences = wiki_data['sentences']
        
        # Opening Hook (30-40s)
        hook_options = [
            f"What if everything you thought you knew about {topic} was wrong? Today, we're uncovering the truth.",
            f"Imagine a world where {topic} holds the key to our future. This isn't science fiction. This is real.",
            f"Scientists have been studying {topic} for decades. But recent discoveries have changed everything.",
            f"You won't believe what we've discovered about {topic}. Prepare to have your mind blown."
        ]
        segments.append({
            "text": random.choice(hook_options),
            "keyword": topic
        })
        
        # Introduction (40-50s)
        intro_text = sentences[0] if sentences else f"{topic} is one of the most fascinating subjects in {niche_name}."
        segments.append({
            "text": f"Welcome to our complete documentary on {topic}. {intro_text}",
            "keyword": topic
        })
        
        # Historical Context (50-60s)
        if len(sentences) > 1:
            segments.append({
                "text": f"Let's start with the history. {sentences[1]} {sentences[2] if len(sentences) > 2 else ''}",
                "keyword": f"{topic} history"
            })
        
        # Key Discovery 1 (45-50s)
        if len(sentences) > 3:
            segments.append({
                "text": f"Here's something incredible. {sentences[3]} This discovery changed everything we knew.",
                "keyword": topic
            })
        
        # Key Discovery 2 (45-50s)
        if len(sentences) > 4:
            segments.append({
                "text": f"But that's not all. {sentences[4]} Scientists were amazed by these findings.",
                "keyword": topic
            })
        
        # Key Discovery 3 (45-50s)
        if len(sentences) > 5:
            segments.append({
                "text": f"And there's more. {sentences[5]} This is where things get really interesting.",
                "keyword": topic
            })
        
        # Scientific Explanation (60-70s)
        if len(sentences) > 6:
            segments.append({
                "text": f"Let me explain how this works. {sentences[6]} {sentences[7] if len(sentences) > 7 else ''} The science behind this is truly remarkable.",
                "keyword": f"{topic} science"
            })
        
        # Real-World Impact (50-60s)
        if len(sentences) > 8:
            segments.append({
                "text": f"So why does this matter to you? {sentences[8]} This has real implications for our future.",
                "keyword": topic
            })
        
        # Controversies/Debates (45-50s)
        controversy_text = sentences[9] if len(sentences) > 9 else f"Experts continue to debate various aspects of {topic}."
        segments.append({
            "text": f"Not everyone agrees on everything. {controversy_text} The debate continues today.",
            "keyword": f"{topic} debate"
        })
        
        # Recent Developments (50-60s)
        if len(sentences) > 10:
            segments.append({
                "text": f"In recent years, new discoveries have emerged. {sentences[10]} {sentences[11] if len(sentences) > 11 else ''}",
                "keyword": f"{topic} recent"
            })
        
        # Future Implications (50-60s)
        if len(sentences) > 12:
            segments.append({
                "text": f"What does the future hold? {sentences[12]} The possibilities are endless.",
                "keyword": f"{topic} future"
            })
        
        # Expert Perspectives (40-50s)
        expert_text = sentences[13] if len(sentences) > 13 else f"Leading researchers continue to study {topic} with great interest."
        segments.append({
            "text": f"Experts around the world are fascinated. {expert_text}",
            "keyword": f"{topic} research"
        })
        
        # Fascinating Details (40-50s)
        detail_text = sentences[14] if len(sentences) > 14 else f"There are many fascinating aspects of {topic} that most people don't know."
        segments.append({
            "text": f"Here's something you might not know. {detail_text} Isn't that amazing?",
            "keyword": topic
        })
        
        # Summary (35-40s)
        segments.append({
            "text": f"So let's recap what we've learned about {topic}. We've explored its history, discoveries, and future potential. The journey has been incredible.",
            "keyword": topic
        })
        
        # Call to Action (25-30s)
        segments.append({
            "text": f"Thanks for watching this documentary on {topic}. If you enjoyed this, please subscribe for more fascinating content. What topic should we explore next? Let us know in the comments!",
            "keyword": topic
        })
        
    else:
        # Fallback if Wikipedia fails - use enhanced placeholder content
        # IMPORTANT: Make these MUCH longer to hit 8+ minutes (need ~1200-1500 words total)
        print(f"Wikipedia fetch failed for {topic}, using fallback content")
        
        fallback_segments = [
            {
                "text": f"What if I told you that {topic} is far more mysterious and fascinating than you ever imagined? Today we're going to uncover the truth behind one of the most intriguing subjects in all of science and discovery. Get ready to have your mind completely blown by what we're about to reveal. This journey will take us through centuries of human curiosity and exploration, revealing secrets that have remained hidden for far too long.",
                "keyword": topic
            },
            {
                "text": f"Welcome to our complete documentary on {topic}. This subject has fascinated humanity for generations, capturing the imagination of scientists, researchers, and curious minds around the world. Throughout history, countless individuals have dedicated their lives to understanding the mysteries and complexities that surround this remarkable topic. Their tireless work has paved the way for the incredible knowledge we possess today, yet so much remains to be discovered.",
                "keyword": topic
            },
            {
                "text": f"The history of {topic} is filled with incredible discoveries and groundbreaking research that fundamentally changed our understanding of the world. From the earliest observations made by pioneering scientists to the cutting-edge technology we use today, every step of this journey has revealed something new and unexpected about the nature of our universe. Ancient civilizations first noticed patterns and phenomena that modern science would later explain in detail. The evolution of our understanding represents one of humanity's greatest intellectual achievements.",
                "keyword": f"{topic} history"
            },
            {
                "text": f"Scientists first began studying {topic} decades ago, but recent breakthroughs have revealed astonishing new information that challenges everything we thought we knew. These discoveries have opened up entirely new fields of research and raised questions that scientists are still working to answer today. The implications of these findings extend far beyond what anyone could have predicted. Each new piece of evidence adds another layer to our understanding, creating a rich tapestry of knowledge that continues to grow and evolve with each passing year.",
                "keyword": topic
            },
            {
                "text": f"One of the most remarkable aspects of {topic} is how it challenges our fundamental understanding of the world around us. The deeper scientists dig into this subject, the more they realize how much we still have to learn. Every answer leads to ten new questions, creating an endless cycle of discovery and wonder that continues to drive research forward. This perpetual quest for knowledge defines the human spirit and our insatiable curiosity about the universe we inhabit. The more we learn, the more we realize how vast and complex reality truly is.",
                "keyword": topic
            },
            {
                "text": f"Researchers have discovered that {topic} plays a crucial role in ways we never anticipated. The implications are truly profound and far-reaching. What started as simple curiosity has evolved into a comprehensive field of study that touches nearly every aspect of modern science and technology. The connections between {topic} and other areas of research continue to surprise and amaze experts. Interdisciplinary collaboration has revealed unexpected relationships that have revolutionized multiple fields simultaneously, demonstrating the interconnected nature of all scientific knowledge.",
                "keyword": topic
            },
            {
                "text": f"The science behind {topic} is incredibly complex and multifaceted, but understanding it helps us appreciate the incredible forces at work in our universe. From the smallest particles to the largest structures in space, everything is connected in ways that scientists are only beginning to understand. The mathematical models and theoretical frameworks used to study {topic} represent some of the most sophisticated thinking in all of science. These elegant equations and principles reveal the underlying order and beauty of nature, showing us that the universe operates according to fundamental laws that we can comprehend and describe.",
                "keyword": f"{topic} science"
            },
            {
                "text": f"The real-world applications of {topic} affect our daily lives in ways most people never realize. This is truly revolutionary and transformative. Technologies that we take for granted today would be impossible without the fundamental research conducted in this field. From medical breakthroughs to technological innovations, the impact of {topic} on modern society cannot be overstated. Practical applications continue to emerge as our theoretical understanding deepens, creating a virtuous cycle where basic research leads to applied technology, which in turn enables even more sophisticated research.",
                "keyword": topic
            },
            {
                "text": f"Experts continue to debate various theories about {topic}, and new evidence emerges regularly that reshapes our knowledge and understanding. These debates are not just academic exercises but represent genuine attempts to understand some of the most fundamental questions about our existence. Different schools of thought offer competing explanations, each supported by compelling evidence and rigorous analysis. The scientific method ensures that only the strongest theories survive, while weaker hypotheses are refined or discarded. This constant process of testing and refinement brings us ever closer to the truth.",
                "keyword": f"{topic} debate"
            },
            {
                "text": f"In recent years, technological advances have allowed us to study {topic} in unprecedented detail, revealing stunning new insights and discoveries. Instruments and techniques that didn't exist a decade ago now provide researchers with data that would have been unimaginable to earlier generations. This flood of new information is revolutionizing our understanding and opening up exciting new avenues for exploration. Supercomputers process vast amounts of data, artificial intelligence identifies patterns humans might miss, and advanced sensors detect phenomena at scales both infinitesimally small and cosmically large.",
                "keyword": f"{topic} recent"
            },
            {
                "text": f"Looking to the future, {topic} may hold the key to solving some of humanity's greatest challenges and mysteries. The potential applications and implications extend far beyond what we can currently imagine. As our understanding deepens and our technology improves, we may discover solutions to problems that have plagued humanity for centuries, or even unlock entirely new possibilities we haven't yet conceived. The next generation of researchers will build upon everything we've learned, taking human knowledge to heights we can barely imagine. What seems like science fiction today may become scientific fact tomorrow.",
                "keyword": f"{topic} future"
            },
            {
                "text": f"Leading researchers around the world are dedicating their careers to understanding {topic} and its far-reaching implications. These brilliant minds work tirelessly in laboratories, observatories, and research facilities across the globe, collaborating and competing to push the boundaries of human knowledge. Their dedication and passion drive the field forward, ensuring that each generation builds upon the discoveries of the last. International cooperation and the free exchange of ideas have accelerated progress, proving that science transcends national boundaries and cultural differences in the pursuit of universal truth.",
                "keyword": f"{topic} research"
            },
            {
                "text": f"Here's a fascinating detail most people don't know about {topic}. This discovery amazed even the most experienced scientists and researchers in the field. When the findings were first published, many experts were skeptical, but repeated experiments and observations have confirmed what once seemed impossible. This revelation has fundamentally altered our understanding and opened up entirely new areas of investigation. The story of this discovery demonstrates how science progresses through careful observation, rigorous testing, and the willingness to challenge established beliefs when evidence demands it.",
                "keyword": topic
            },
            {
                "text": f"To summarize everything we've explored today, we've journeyed through the history, science, and future possibilities of {topic}. The journey has revealed incredible insights into one of the most fascinating subjects in all of human knowledge. From ancient observations to cutting-edge research, we've seen how our understanding has evolved and deepened over time, and how much more there is still to discover. This documentary has only scratched the surface of this vast and complex field, but hopefully it has inspired you to learn more and appreciate the wonder of scientific discovery.",
                "keyword": topic
            },
            {
                "text": f"Thank you so much for watching this complete documentary on {topic}. If you found this exploration fascinating and educational, please subscribe to our channel for more in-depth documentaries covering the most intriguing topics in science, history, and discovery. What topic should we explore next? Let us know in the comments below, and don't forget to like and share this video with anyone who loves learning about the mysteries of our universe! Your support helps us create more content and continue our mission of making complex scientific concepts accessible to everyone. Join our community of curious minds today!",
                "keyword": topic
            }
        ]
        segments = fallback_segments
    
    # Create enhanced title and description
    title = f"{topic}: The Complete Documentary 🎥"
    hashtags = f"#Documentary #{niche_name.replace(' & ', '').replace(' ', '')} #Educational #Viral #Trending #Discovery"
    
    # Enhanced description with sources
    description = f"""Welcome back! Today we are exploring {topic}.

{hashtags}

Join us as we deep dive into the mysteries of {niche_name}.

📚 Sources & Research:
"""
    
    if wiki_data:
        description += f"- Wikipedia: {wiki_data['url']}\n"
    
    description += f"""- Public domain educational content

🎓 What You'll Learn:
- Historical background and discoveries
- Scientific explanations and research
- Real-world impact and applications
- Future implications and possibilities

🤖 Production:
- Video: Pexels API (royalty-free)
- Voice: Microsoft Edge TTS
- Research: Public domain sources

💬 What topic should we explore next? Comment below!
"""

    return {
        "mode": "long",
        "topic": topic,
        "segments": segments,
        "title": title,
        "description": description,
        "tags": hashtags,
        "youtube_category": "27" if "Space" in niche_name or "Tech" in niche_name else "28",
        "wiki_url": wiki_data['url'] if wiki_data else None
    }

if __name__ == "__main__":
    print(get_video_metadata())
