import requests
import random
import re
import feedparser
import os
import json
from datetime import datetime
from ypp_script_template import generate_ypp_safe_script, ensure_minimum_duration
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
    "AI Tools": ["ai", "tool", "free", "openai", "gemini", "chatgpt", "automation", "productivity", "software", "best ai", "top ai"],
    "Digital Productivity": ["efficiency", "hacks", "tips", "workflow", "optimize", "time saving", "digital", "remote work", "organization"],
    "Software Solutions": ["how to", "fix", "solution", "windows", "linux", "macos", "error", "problem", "solve", "tech support", "tutorial"],
    "Internet Culture": ["meme", "funny", "viral", "trend", "tiktok", "reddit", "twitter", "culture", "moment", "humor"]
}

# Tracking for used jokes to prevent repetition
USED_JOKES_FILE = os.path.join(os.path.dirname(__file__), '..', 'assets', 'used_jokes.json')

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


def load_daily_plan():
    """Load the strategic plan from The Brain"""
    import json
    import os
    plan_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'daily_plan.json')
    if os.path.exists(plan_path):
        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                plan = json.load(f)
            print(f"[*] Content Strat: Loaded plan for '{plan.get('today_topic', 'Unknown')}'")
            return plan
        except Exception as e:
            print(f"  [WARN] Failed to load daily plan: {e}")
            return None
    return None

def get_meme_theme():
    """Select a daily theme for potential viral reach"""
    themes = [
        {
            "id": "dad_jokes",
            "name": "Dad Jokes",
            "subreddit": "dadjokes",
            "title_template": "Dad Jokes That Actually Make You Laugh 🤣",
            "hashtags": "#DadJokes #Puns #Funny #Humor #Shorts #TryNotToLaugh",
            "intro": "Get ready to groan..."
        },
        {
            "id": "shower_thoughts",
            "name": "Shower Thoughts",
            "subreddit": "Showerthoughts",
            "title_template": "Shower Thoughts That Will Keep You Up At Night 🤯",
            "hashtags": "#ShowerThoughts #MindBlown #DeepThoughts #Facts #Shorts #Viral",
            "intro": "Think about this..."
        },
        {
            "id": "clean_jokes",
            "name": "Clean Comedy",
            "subreddit": "cleanjokes",
            "title_template": "Best Clean Jokes 2026 (Funny!) 😂",
            "hashtags": "#CleanComedy #Jokes #Wholesome #Funny #Shorts #DailyMeme",
            "intro": "Here is your daily dose of laughter..."
        }
    ]
    
    # Select predictable theme based on day of year to ensure variety
    # day_of_year = datetime.now().timetuple().tm_yday
    # theme = themes[day_of_year % len(themes)]
    
    # Or just random for now to keep it fresh
    theme = random.choice(themes)
    print(f"[*] Daily Theme Selected: {theme['name']}")
    return theme

def get_trending_memes_reddit(theme=None):
    """Fetch trending content based on theme or search"""
    jokes = []
    
    # --- BRAIN INTEGRATION: Support Search ---
    search_term = theme.get('search_term') if theme else None
    subreddit = theme['subreddit'] if theme else "memes"
    
    if theme:
        subreddits = [subreddit]
    else:
        subreddits = ['Jokes', 'dadjokes', 'cleanjokes']
    
    for subreddit in subreddits:
        try:
            if search_term:
                 # Search URL
                 url = f"https://www.reddit.com/r/{subreddit}/search.json?q={search_term}&restrict_sr=1&sort=top&limit=20"
                 print(f"  [BRAIN] Searching r/{subreddit} for '{search_term}'...")
            else:
                 # Standard Hot URL
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

                    # Theme specific parsing
                    if theme and theme['id'] == 'shower_thoughts':
                        # Shower thoughts are usually just the title
                        clean_title = title
                        # Remove "Shower thought:" prefix if present
                        if clean_title.lower().startswith("shower thought"):
                            clean_title = clean_title.split(":", 1)[1].strip()
                            
                        if len(clean_title) < 150: # Keep it shortish
                            jokes.append({
                                'setup': "Shower Thought...",
                                'punchline': clean_title
                            })
                    else:
                        # Standard Setup/Punchline format
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
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        trending_df = pytrends.trending_searches(pn='united_states')
        return trending_df[0].tolist()[:15]
    except Exception as e:
        print(f"Google Trends error: {e}")
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
    """Fetch "Fun" or "Weird" facts (Better for a Meme Channel)"""
    facts = []
    subreddits = ['weirdfacts', 'Unexpected', 'BeAmazed', 'rareinsults']
    
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
        "In 1923, a jockey named Frank Hayes won a race at Belmont Park despite being dead. He had suffered a heart attack mid-race!",
        "The probability of you drinking a glass of water that contains a molecule of water that also passed through a dinosaur is almost 100%.",
        "A group of flamingos is called a 'flamboyance'. Imagine being that extra just by existing.",
        "You can't hum while holding your nose. Go ahead, try it. I'll wait.",
        "There’s a company that turns dead people into ocean reefs. Talk about a permanent beach vacation.",
        "The first webcam was created just to check if a coffee pot at Cambridge University was full so people didn't walk there for nothing.",
        "A 'jiffy' is an actual unit of time. It's the time it takes for light to travel one centimeter in a vacuum.",
        "Sloths can hold their breath longer than dolphins can. That's a weird flex for a slow animal.",
        "The average person spends 6 months of their lifetime waiting for red lights to turn green.",
        "Cows have 'best friends' and they get stressed when they are separated. Peak relatable content."
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
    print("\n[*] Selecting Daily Theme...")
    
    # --- BRAIN INTEGRATION ---
    plan = load_daily_plan()
    theme = None
    
    if plan and 'meme' in plan:
        meme_strat = plan['meme']
        print(f"  [BRAIN] Executing Meme Strategy: {meme_strat.get('forced_topic', 'Random')}")
        
        # Construct theme object from brain data
        if meme_strat.get('backup_theme'):
            theme = {
                "id": "trending",
                "subreddit": meme_strat['backup_theme']['subreddit'],
                "title_template": f"Trending: {meme_strat.get('forced_topic')} Memes 🤣",
                "hashtags": meme_strat['backup_theme']['hashtags']
            }
            # Add specific search term instructions for the reddit fetcher if needed
            # (Assuming get_trending_memes_reddit can take a search term or we modify it)
            # For now, we rely on the subreddit or if we modify get_trending_memes_reddit to search
            theme['search_term'] = meme_strat.get('forced_topic')
    
    if not theme:
        theme = get_meme_theme()
    # -------------------------
    
    print(f"\n[*] Fetching trending content from r/{theme['subreddit']}...")
    
    # Try to get trending jokes from Reddit with theme
    # Pass search_term if present (requires update to get_trending_memes_reddit, or we just trust the subreddit)
    trending_jokes = get_trending_memes_reddit(theme)
    
    if trending_jokes and len(trending_jokes) >= 5:
        # Use trending jokes
        print(f"  [OK] Found {len(trending_jokes)} trending items")
        # Select 5 random jokes from trending
        import random
        selected_jokes = random.sample(trending_jokes, min(5, len(trending_jokes)))
        
        # Track used jokes
        for joke in selected_jokes:
            save_used_joke(joke['setup'])
        
        memes_list = selected_jokes
    else:
        # Fallback to local database (avoiding the 5-joke repetition)
        print(f"  [WARN] Reddit fetch failed/low. Using backup database.")
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'jokes_db.json')
            with open(db_path, 'r', encoding='utf-8') as f:
                all_backup_jokes = json.load(f)
            
            # Filter used jokes
            available_jokes = [j for j in all_backup_jokes if not is_joke_used(j['setup'])]
            
            if len(available_jokes) < 5:
                print("  [WARN] Running low on backup jokes! Resetting or re-using...")
                available_jokes = all_backup_jokes # Emergency reset
            
            # Select 5 random
            import random
            memes_list = random.sample(available_jokes, min(5, len(available_jokes)))
            
            # Track them
            for joke in memes_list:
                save_used_joke(joke['setup'])
                
        except Exception as e:
            print(f"  [ERROR] Could not load backup jokes: {e}")
            # Ultimate fail-safe (should rarely happen)
            memes_list = [
                {"setup": "Why don't scientists trust atoms?", "punchline": "Because they make up everything!"}
            ]

        theme = { # Generic theme for backup
            "title_template": "Daily Meme Therapy! 😂",
            "hashtags": "#Memes #Funny #DailyMemes #Humor #Shorts #Jokes #Compilation"
        }
    
    # Combine scripts for description/tts if needed, but generator will handle individual clips
    full_script_text = " ".join([f"{m['setup']} {m['punchline']}" for m in memes_list])
    
    # Dynamic Hashtags
    hashtags = f"{theme['hashtags']} #DailyMemeDose"
    
    return {
        "mode": "meme",
        "memes": memes_list,  # List of {setup, punchline}
        "text": full_script_text, # Legacy support
        "title": f"{theme['title_template']} ({len(memes_list)} Jokes)",
        "description": f"Enjoy these funny moments!\n\nSubscribe to Daily Meme Dose for more!\n\n{hashtags}",
        "tags": hashtags,
        "youtube_category": "23" # Comedy
    }


def get_hashtags(category="facts"):
    # Viral hashtags for Shorts/Reels
    tags = [
        "#Shorts", "#DidYouKnow", "#Facts", "#MindBlown", "#Interesting", 
        "#Knowledge", "#Trivia", "#DailyFacts", "#Viral", "#Trending",
        "#Science", "#History", "#LifeHacks", "#LearnSomethingNew"
    ]
    recommended = random.sample(tags, 8)
    return " ".join(recommended)

def get_video_metadata():
    """AI TOOL SPOTLIGHT (Formerly Daily Fact)"""
    print("\n[*] Fetching AI Tools for the spotlight...")
    
    plan = load_daily_plan()
    planned_topic = None
    is_part_2 = False
    if plan and 'fact' in plan:
        planned_topic = plan['fact'].get('topic')
        is_part_2 = plan.get('is_part_2', False)
        print(f"  [BRAIN] AI Strategy Topic: {planned_topic} (Part 2: {is_part_2})")
    
    # 1. Try to get AI tools from Reddit
    ai_tools = []
    # AI Focused Subreddits
    subreddits = ['AItools', 'software', 'productivity']
    search_query = planned_topic if planned_topic else "free ai"
    
    for sub in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub}/search.json?q={search_query}&restrict_sr=1&sort=top&limit=10"
            headers = {'User-Agent': 'TubeAutoma/1.0'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                posts = response.json()['data']['children']
                for post in posts:
                    title = post['data'].get('title', '')
                    content = post['data'].get('selftext', '')
                    # Filter for "Free" or "Open Source"
                    if any(kw in title.lower() for kw in ["free", "open source", "no cost", "api"]):
                        if len(title) < 150:
                            ai_tools.append({"title": title, "content": content})
        except:
            pass
    
    if ai_tools:
        # Pick a tool
        selected = random.choice(ai_tools)
        tool_name = selected['title']
        print(f"  [SELECTED TOOL] {tool_name}")
        
        # Format script for 45-60 sec Short
        fact_text = f"Looking for a free AI tool? Check out {tool_name}. It's absolute magic for {planned_topic if planned_topic else 'your daily tasks'}. Follow for more AI hacks!"
    else:
        # Fallback to high-value tech facts
        print(f"  [WARN] Fallback: Generic AI productivity hack")
        hacks = [
            "Did you know you can use Gemini and Claude for free to automate your entire spreadsheet workflow? Just ask for a Python script!",
            "Stop paying for AI image generators. Leonardo AI and SeaArt provide incredible daily free credits for high-end art.",
            "You can now run Llama 3 locally on your computer using Ollama for 100% private and free AI without a subscription."
        ]
        fact_text = random.choice(hacks)

    # --- Visual Keyword Extraction ---
    keyword = "technology" 
    if planned_topic: keyword = planned_topic.split()[0]
    
    # --- Professional Hook Integration ---
    from ypp_script_template import generate_hook
    hook = generate_hook(planned_topic if planned_topic else "AI Tools", is_part_2)
    fact_text = f"{hook} {fact_text}"
    
    hashtags = "#AI #ArtificialIntelligence #TechHacks #Productivity #Shorts"
    title_prefix = "PART 2: " if is_part_2 else "FREE AI Tool! 🤖 "
    title = f"{title_prefix}{tool_name[:25] if 'tool_name' in locals() else ''}"
    description = f"{fact_text}\n\n{hashtags}"
    
    return {
        "text": fact_text,
        "keyword": keyword,
        "title": title,
        "description": description,
        "tags": hashtags,
        "youtube_category": "28" # Science & Tech
    }

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

# ============================================================================
# NEW CURIOSITY/FACTS WORKFLOW
# ============================================================================

def get_curiosity_metadata():
    """
    4-Pillar Shorts Content Generator
    Pillars: Fact Shock, Internet Curiosity, Clean Meme Logic, Comparison Curiosity
    Structure: [0-2s Hook] [3-15s Build] [16-28s Reveal] [Last 3s Loop]
    Duration: 22-35 seconds
    """
    print("\n[*] Generating structured curiosity content...")
    
    # Select ONE pillar randomly
    pillars = [
        {
            "name": "Fact Shock",
            "sources": ["TodayILearned", "Damnthatsinteresting", "science"],
            "hook_templates": [
                "This sounds impossible.",
                "Most people get this wrong.",
                "This breaks common sense.",
                "Scientists were shocked."
            ],
            "build_prefix": "Here is what happened.",
            "reveal_prefix": "The truth is",
            "close_templates": [
                "Nature is fascinating.",
                "Reality is stranger.",
                "Science explains everything."
            ]
        },
        {
            "name": "Internet Curiosity",
            "sources": ["Showerthoughts", "explainlikeimfive"],
            "hook_templates": [
                "Think about this.",
                "This will change your view.",
                "Nobody notices this.",
                "This is everywhere."
            ],
            "build_prefix": "Consider the following.",
            "reveal_prefix": "When you realize",
            "close_templates": [
                "Mind expanded.",
                "Now you see it.",
                "Perspective shifted."
            ]
        },
        {
            "name": "Clean Meme Logic",
            "sources": ["Showerthoughts", "funny"],
            "hook_templates": [
                "This makes no sense.",
                "Wait for it.",
                "The irony is real.",
                "Logic has left."
            ],
            "build_prefix": "Think about it.",
            "reveal_prefix": "The funny part is",
            "close_templates": [
                "Makes you think.",
                "Life is weird.",
                "Perfectly illogical."
            ]
        },
        {
            "name": "Comparison Curiosity",
            "sources": ["todayilearned", "science"],
            "hook_templates": [
                "Compare these two things.",
                "One is bigger.",
                "The difference is massive.",
                "Size is deceiving."
            ],
            "build_prefix": "First item.",
            "reveal_prefix": "Second item is",
            "close_templates": [
                "Scale is everything.",
                "Perspective matters.",
                "Numbers tell stories."
            ]
        }
    ]
    
    selected_pillar = random.choice(pillars)
    print(f"  [PILLAR] {selected_pillar['name']}")
    
    # Fetch content from Reddit
    facts = []
    for subreddit in selected_pillar['sources']:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/top.json?t=week&limit=15"
            headers = {'User-Agent': 'TubeAutoma/1.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                posts = response.json()['data']['children']
                for post in posts:
                    data = post['data']
                    title = data.get('title', '')
                    
                    # Strict filtering
                    if len(title) < 40 or len(title) > 200:
                        continue
                    
                    blacklist = [
                        "police", "murder", "kill", "died", "death", "war", "abuse", "drug",
                        "sex", "assault", "racist", "politics", "trump", "biden", "religion",
                        "nsfw", "gore", "blood", "shoot", "attack", "victim", "hate"
                    ]
                    if any(bad in title.lower() for bad in blacklist):
                        continue
                    
                    # Clean prefixes
                    clean_title = title
                    for prefix in ["TIL ", "TIL that ", "TIL: ", "ELI5: ", "ELI5 "]:
                        if clean_title.startswith(prefix):
                            clean_title = clean_title[len(prefix):]
                    
                    if is_joke_used(clean_title):
                        continue
                    
                    facts.append(clean_title)
                    
        except Exception as e:
            print(f"  [WARN] Fetch error for r/{subreddit}: {e}")
    
    # Fallback content by pillar (Expanded for reliability)
    if not facts:
        print("  [FALLBACK] Using curated content")
        fallbacks = {
            "Fact Shock": [
                "A day on Venus is longer than a year on Venus. It takes 243 Earth days to rotate once but only 225 Earth days to orbit the Sun.",
                "Honey never spoils. Archaeologists found 3000 year old honey in Egyptian tombs that was still edible.",
                "Octopuses have three hearts and blue blood. Two hearts pump blood to the gills while one pumps to the body.",
                "The Eiffel Tower can be 15 cm taller during the summer. Thermal expansion causes the iron to expand when temperatures rise.",
                "Bananas are berries, but strawberries are not. Botanically, a berry has seeds inside the flesh.",
                "Wombat poop is cube-shaped. This prevents it from rolling away and marks their territory.",
                "Sharks existed before trees. Sharks are 400 million years old, while trees appeared 350 million years ago.",
                "Water can boil and freeze at the same time. It's called the triple point.",
                "A cloud can weigh more than a million pounds. The water droplets are just spread out.",
                "Your bones are four times stronger than concrete. A cubic inch of bone can bear a load of 19,000 lbs."
            ],
            "Internet Curiosity": [
                "You have never seen your face in person. Only reflections and photographs.",
                "Every photo of you is from the past. You have never seen yourself in real time.",
                "Your brain named itself. Then it got curious about how it works.",
                "You can't hum while holding your nose. Try it and look silly.",
                "The oldest person was born with a completely different set of humans. Everyone else has been replaced.",
                "You ignore your nose every second. Your brain just edits it out of your vision.",
                "Clapping is just hitting yourself because you like something. It is a weird human habit.",
                "Your future self is watching you right now through memories. Act accordingly.",
                "Reading is just staring at dead wood and hallucinating. A vivid hallucination shared by millions.",
                "Sleep is just a free trial of death. And we love it."
            ],
            "Clean Meme Logic": [
                "Whoever invented the knock knock joke deserves a no bell prize.",
                "Fireflies are the only creatures that can make light without heat. They are literally the coolest.",
                "The word bed actually looks like a bed.",
                "If you clean a vacuum cleaner, you become the vacuum cleaner. Think about it.",
                "Laziness is just resting before you get tired. It is efficient energy management.",
                "A dentist makes money from your bad teeth. Why trust the toothpaste they recommend?",
                "If two mind readers read each other's minds, whose mind are they reading?",
                "Nothing starts with N and ends with G. Nothing does.",
                "Maybe oxygen makes you live for 80 years but kills you slowly. It is a slow oxidation process.",
                "Why do we press harder on the remote when the batteries are dead? We hope determination powers it."
            ],
            "Comparison Curiosity": [
                "There are more trees on Earth than stars in the Milky Way galaxy. Three trillion trees versus 400 billion stars.",
                "The Pacific Ocean is larger than all land on Earth combined. It covers more area than all continents.",
                "A single teaspoon of neutron star weighs six billion tons. More than Mount Everest.",
                "Humans share 50% of their DNA with bananas. We are half fruit.",
                "Cleopatra lived closer to the iPhone than the Pyramids. Time is distorted in our minds.",
                "There are more fake flamingos in the world than real ones. Plastic birds are winning.",
                "Russia has a larger surface area than Pluto. A country bigger than a dwarf planet.",
                "A million seconds is 11 days. A billion seconds is 31 years.",
                "If you fold a paper 42 times, it would reach the moon. Exponential growth is scary.",
                "All the gold ever mined fits in a cube of 21 meters. It would fit under the Eiffel Tower."
            ]
        }
        facts = fallbacks.get(selected_pillar['name'], fallbacks["Fact Shock"])
    
    # Select content
    selected_fact = random.choice(facts)
    save_used_joke(selected_fact)
    
    # Build structured script (22-35 seconds target)
    hook = random.choice(selected_pillar['hook_templates'])
    build = f"{selected_pillar['build_prefix']} {selected_fact.split('.')[0]}."
    
    # Reveal (rest of fact or elaboration)
    fact_parts = selected_fact.split('.')
    if len(fact_parts) > 1:
        reveal = f"{selected_pillar['reveal_prefix']} {'. '.join(fact_parts[1:]).strip()}."
    else:
        reveal = f"{selected_pillar['reveal_prefix']} this is completely true."
    
    close = random.choice(selected_pillar['close_templates'])
    
    # Combine (NO questions, NO CTAs)
    script = f"{hook} {build} {reveal} {close}"
    
    # Clean up
    script = script.replace('..', '.').replace('  ', ' ').strip()
    if not script.endswith('.'):
        script += '.'
    
    print(f"  [SCRIPT] {script[:60]}...")
    
    # Generate on-screen text cues (max 6 words per line)
    text_cues = []
    words = script.split()
    for i in range(0, len(words), 6):
        chunk = ' '.join(words[i:i+6])
        if chunk:
            text_cues.append(chunk)
    
    # Visual keyword extraction
    visual_keyword = "abstract background"
    fact_words = selected_fact.split()
    if len(fact_words) > 2:
        # Extract subject (first 2-3 meaningful words)
        potential = ' '.join(fact_words[:3])
        if not potential.lower().startswith(('the ', 'a ', 'an ', 'this ', 'that ')):
            visual_keyword = potential
        elif len(fact_words) > 3:
            visual_keyword = ' '.join(fact_words[1:4])
    
    
    # Generate visual instructions (copyright-safe)
    visual_instructions = []
    segments = [
        {"timing": "0-2s", "type": "Hook", "visual": "Abstract particle effects or geometric patterns"},
        {"timing": "3-15s", "type": "Build", "visual": f"Stock footage: {visual_keyword} (nature/tech/abstract only)"},
        {"timing": "16-28s", "type": "Reveal", "visual": "Flowing motion graphics or light rays"},
        {"timing": "Last 3s", "type": "Close", "visual": "Minimal gradient fade"}
    ]
    visual_instructions = segments
    
    # Thumbnail specification
    thumbnail_spec = {
        "text": thumb_text[:25] if len(words) <= 4 else random.choice([
            "IMPOSSIBLE", "WAIT", "MIND BLOWN", "TRUTH"
        ]),
        "style": "High contrast, dark background, bright yellow/white text",
        "forbidden": "NO emojis, NO arrows, NO faces, NO copyrighted imagery",
        "background": "Abstract gradient or geometric patterns only"
    }
    
    print(f"  [VISUAL] {visual_keyword}")
    print(f"  [TEXT CUES] {len(text_cues)} segments")
    print(f"  [THUMB] {thumbnail_spec['text']}")
    
    return {
        "mode": "curiosity",
        "pillar": selected_pillar['name'],
        "text": script,
        "text_cues": text_cues,
        "visual_instructions": visual_instructions,
        "thumbnail_spec": thumbnail_spec,
        "keyword": visual_keyword,
        "topic": visual_keyword,
        "title": f"{selected_pillar['name']} - Shorts",
        "description": f"{selected_fact}\n\n#Shorts #Facts #Curiosity #Learning",
        "tags": "#Shorts #Facts #Curiosity #Learning #Education",
        "youtube_category": "27"
    }

def get_long_video_metadata():
    """TECH SOLUTIONS TUTORIAL (8+ Minutes)"""
    print(f"\n[*] Generating LONG FORM Tech Solution Tutorial...")
    
    plan = load_daily_plan()
    planned_topic = None
    is_part_2 = False
    if plan and 'long' in plan:
        planned_topic = plan['long'].get('topic')
        is_part_2 = plan.get('is_part_2', False)
        print(f"  [BRAIN] Tech Solution topic: {planned_topic} (Part 2: {is_part_2})")

    topic = planned_topic if planned_topic else "Optimizing Your PC"
    
    # 8-minute video needs ~1200 words. Refactored to use YPP-Safe Script Generator
    # Fetch Wikipedia content for depth
    wiki_data = fetch_wikipedia_content(topic)
    sentences = wiki_data.get('sentences', []) if wiki_data else []
    
    from ypp_script_template import generate_ypp_safe_script, ensure_minimum_duration
    segments = generate_ypp_safe_script(topic, sentences, is_part_2=is_part_2)
    segments = ensure_minimum_duration(segments, min_duration=480) # Ensure 8+ minutes
    
    # Ensure duration and title
    title_prefix = "PART 2: " if is_part_2 else "How to Fix "
    title = f"{title_prefix}{topic} (COMPLETE 2026 GUIDE) 💻"
    hashtags = "#TechSolutions #TechSupport #Fix #Software #Tutorial #Computer"
    description = f"Step-by-step masterclass on resolving {topic}.\n\n{hashtags}\n\nGenerated by TubeAutoma AI Support."

    return {
        "mode": "long",
        "topic": topic,
        "segments": segments,
        "title": title,
        "description": description,
        "tags": hashtags,
        "youtube_category": "28"  # Science & Tech
    }

# (Commented out old code to prevent errors if we didn't match perfectly)
'''
        
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
            "text": f"Thanks for watching this documentary on {topic}. If you enjoyed this, please subscribe to Daily Meme Dose for more fascinating content. What topic should we explore next? Let us know in the comments!",
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
                "text": f"Thank you so much for watching this complete documentary on {topic}. If you found this exploration fascinating and educational, please subscribe to Daily Meme Dose for more in-depth documentaries covering the most intriguing topics in science, history, and discovery. What topic should we explore next? Let us know in the comments below, and don't forget to like and share this video with anyone who loves learning about the mysteries of our universe! Your support helps us create more content and continue our mission of making complex scientific concepts accessible to everyone. Join our community of curious minds today!",
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
'''
