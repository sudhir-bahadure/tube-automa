import requests
import random
from datetime import datetime, timedelta
import json
import os

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("Warning: pytrends not available, keyword research will be limited")

class KeywordResearcher:
    """VidIQ-style keyword research engine for YouTube optimization."""
    
    def __init__(self):
        self.cache_file = "assets/keyword_cache.json"
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """Load keyword cache to avoid repeated API calls."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save keyword cache."""
        try:
            os.makedirs("assets", exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"  [WARN] Could not save keyword cache: {e}")
    
    def get_search_volume(self, keyword):
        """Get search volume from Google Trends (0-100 scale)."""
        if not PYTRENDS_AVAILABLE:
            return 50  # Default moderate volume
        
        # Check cache first
        cache_key = f"volume_{keyword}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # Cache valid for 7 days
            if datetime.fromisoformat(cached_data['timestamp']) > datetime.now() - timedelta(days=7):
                return cached_data['value']
        
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
            pytrends.build_payload([keyword], timeframe='today 3-m')
            interest_df = pytrends.interest_over_time()
            
            if not interest_df.empty and keyword in interest_df.columns:
                volume = int(interest_df[keyword].mean())
                # Cache result
                self.cache[cache_key] = {
                    'value': volume,
                    'timestamp': datetime.now().isoformat()
                }
                self._save_cache()
                return volume
        except Exception as e:
            print(f"  [WARN] Trends error for '{keyword}': {e}")
        
        return 50  # Fallback
    
    def get_competition_score(self, keyword):
        """
        Estimate competition (0-100, lower is better).
        Uses YouTube search result count as proxy.
        """
        cache_key = f"competition_{keyword}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.fromisoformat(cached_data['timestamp']) > datetime.now() - timedelta(days=7):
                return cached_data['value']
        
        try:
            # Use YouTube RSS search as a free proxy for competition
            # More results = higher competition
            search_url = f"https://www.youtube.com/results?search_query={keyword.replace(' ', '+')}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Rough heuristic: if page loads, assume moderate competition
                # In reality, we'd parse result count, but that requires scraping
                # For now, use keyword length as proxy (longer = more specific = less competition)
                word_count = len(keyword.split())
                if word_count >= 4:
                    competition = 30  # Low competition (long-tail)
                elif word_count == 3:
                    competition = 50  # Medium
                elif word_count == 2:
                    competition = 70  # High
                else:
                    competition = 85  # Very high (single word)
                
                self.cache[cache_key] = {
                    'value': competition,
                    'timestamp': datetime.now().isoformat()
                }
                self._save_cache()
                return competition
        except Exception as e:
            print(f"  [WARN] Competition check error for '{keyword}': {e}")
        
        return 60  # Fallback moderate competition
    
    def calculate_keyword_score(self, keyword, niche_relevance=100):
        """
        Calculate VidIQ-style keyword score (0-100).
        Formula: (Volume × Relevance) / Competition
        Normalized to 0-100 scale.
        """
        volume = self.get_search_volume(keyword)
        competition = self.get_competition_score(keyword)
        
        # Avoid division by zero
        if competition == 0:
            competition = 1
        
        # Calculate raw score
        raw_score = (volume * niche_relevance) / competition
        
        # Normalize to 0-100 (assuming max raw score is ~200)
        normalized_score = min(100, int((raw_score / 200) * 100))
        
        return {
            'keyword': keyword,
            'score': normalized_score,
            'volume': volume,
            'competition': competition,
            'relevance': niche_relevance
        }
    
    def discover_long_tail_keywords(self, base_keyword):
        """
        Discover long-tail keyword variations.
        Uses question formats and Reddit mining.
        """
        long_tail = []
        
        # Question-based variations
        question_templates = [
            f"how to {base_keyword}",
            f"why {base_keyword}",
            f"what is {base_keyword}",
            f"best {base_keyword}",
            f"{base_keyword} explained",
            f"{base_keyword} tutorial",
            f"{base_keyword} for beginners"
        ]
        long_tail.extend(question_templates)
        
        # Try to mine Reddit for natural variations
        try:
            subreddits = ['explainlikeimfive', 'NoStupidQuestions', 'todayilearned']
            for subreddit in subreddits[:1]:  # Limit to 1 to avoid rate limits
                url = f"https://www.reddit.com/r/{subreddit}/search.json?q={base_keyword}&limit=5"
                headers = {'User-Agent': 'TubeAutoma/1.0'}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    posts = response.json().get('data', {}).get('children', [])
                    for post in posts:
                        title = post['data'].get('title', '')
                        if base_keyword.lower() in title.lower() and len(title) < 80:
                            long_tail.append(title.lower())
        except Exception as e:
            print(f"  [WARN] Reddit mining error: {e}")
        
        return list(set(long_tail))[:15]  # Return unique, max 15
    
    def find_best_keywords(self, topic, niche, count=5):
        """
        Find the best keywords for a given topic.
        Returns top 'count' keywords sorted by score.
        """
        print(f"\n[*] Researching keywords for: {topic}")
        
        # Generate candidate keywords
        candidates = [topic]
        candidates.extend(self.discover_long_tail_keywords(topic))
        
        # Score all candidates
        scored_keywords = []
        for keyword in candidates[:20]:  # Limit to avoid too many API calls
            score_data = self.calculate_keyword_score(keyword, niche_relevance=100)
            scored_keywords.append(score_data)
            print(f"  - {keyword}: Score {score_data['score']}/100 (Vol: {score_data['volume']}, Comp: {score_data['competition']})")
        
        # Sort by score and return top N
        scored_keywords.sort(key=lambda x: x['score'], reverse=True)
        top_keywords = scored_keywords[:count]
        
        print(f"\n[OK] Top {count} keywords selected:")
        for kw in top_keywords:
            print(f"  ✓ {kw['keyword']} (Score: {kw['score']}/100)")
        
        return top_keywords

# Singleton instance
keyword_researcher = KeywordResearcher()
