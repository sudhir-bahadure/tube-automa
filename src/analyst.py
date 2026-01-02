import os
import json
import datetime
from youtube_uploader import get_authenticated_service

# Path to the directives file
ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets')
DIRECTIVES_FILE = os.path.join(ASSETS_DIR, 'analyst_directives.json')

def get_analytics_service():
    """Build Analytics Service using shared credentials logic"""
    # Reuse the uploader's auth logic but for analytics
    # Note: scopes were updated in youtube_uploader.py
    import googleapiclient.discovery
    import google_auth_oauthlib.flow
    import googleapiclient.errors
    from google.oauth2.credentials import Credentials
    
    # Load credentials from Environment Variables (GitHub Secrets)
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        print("Missing YouTube API Credentials. Skipping analytics.")
        return None

    # Construct Credentials object
    creds = Credentials(
        None, 
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        # We need the scopes list from youtube_uploader but just hardcode for safety here to match
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/yt-analytics.readonly"
        ]
    )
    
    return googleapiclient.discovery.build("youtubeAnalytics", "v2", credentials=creds)

def fetch_channel_performance():
    """Get basic channel stats for last 7 days"""
    analytics = get_analytics_service()
    if not analytics: return None
    
    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=7)
    
    try:
        print("[*] Analyst: Fetching 7-day performance...")
        response = analytics.reports().query(
            ids="channel==MINE",
            startDate=seven_days_ago.isoformat(),
            endDate=today.isoformat(),
            metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes",
            dimensions="day",
            sort="day"
        ).execute()
        
        # Also fetch top videos
        top_videos = analytics.reports().query(
            ids="channel==MINE",
            startDate=seven_days_ago.isoformat(),
            endDate=today.isoformat(),
            metrics="views,subscribersGained",
            dimensions="video",
            sort="-views",
            maxResults=5
        ).execute()
        
        return {"daily_stats": response, "top_videos": top_videos}
        
    except Exception as e:
        print(f"[!] Analytics Access Failed: {e}")
        print("    (Did you update the Refresh Token with the new scope?)")
        return None

def fetch_video_details(video_ids):
    """Get titles/tags for the top videos to understand WHY they worked"""
    if not video_ids: return {}
    
    youtube = get_authenticated_service() # Data API
    if not youtube: return {}
    
    try:
        response = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids)
        ).execute()
        return {item['id']: item['snippet'] for item in response.get('items', [])}
    except:
        return {}

def analyze_and_direct(performance_data):
    """Logic to decide what to do next"""
    if not performance_data:
        return {"status": "no_data", "directive": None}
    
    top_videos_data = performance_data.get('top_videos', {}).get('rows', [])
    
    if not top_videos_data:
        print("  [Analyst] No views in last 7 days. Analyzing generic strategy...")
        return {
            "status": "growth_mode", 
            "directive": None, # No specific data to steer yet
            "advice": "Post more consistently."
        }
        
    # Analyze Top Video
    # Row format: [videoId, views, subscribersGained]
    best_video_id = top_videos_data[0][0]
    best_views = top_videos_data[0][1]
    
    print(f"  [Analyst] Best video ({best_video_id}) got {best_views} views.")
    
    # Get Metadata
    details = fetch_video_details([best_video_id])
    if best_video_id in details:
        snippet = details[best_video_id]
        title = snippet['title']
        tags = snippet.get('tags', [])
        
        # Simple extraction: Find most common non-generic word in title
        # "Why Cats are funny" -> "Cats"
        ignore = {'are', 'the', 'why', 'what', 'how', 'video', 'shorts', 'funny'}
        keywords = [w for w in title.lower().split() if len(w) > 3 and w not in ignore]
        
        winning_topic = keywords[0] if keywords else "unknown"
        
        print(f"  [Analyst] Identified successful topic: '{winning_topic}'")
        
        directive = {
            "generated_at": datetime.datetime.now().isoformat(),
            "winning_topic": winning_topic,
            "origin_video": title,
            "action": "boost_topic", # Brain should prioritize this
            "reason": f"Video drove {best_views} views."
        }
        
        return directive
        
    return None

def main():
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
        
    data = fetch_channel_performance()
    directive = analyze_and_direct(data)
    
    if directive:
        with open(DIRECTIVES_FILE, 'w', encoding='utf-8') as f:
            json.dump(directive, f, indent=2)
        print(f"[*] Analyst: Directive saved to {DIRECTIVES_FILE}")
    else:
        print("[*] Analyst: No clear directive generated (Not enough data or auth failure).")

if __name__ == "__main__":
    main()
