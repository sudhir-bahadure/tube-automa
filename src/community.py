import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
import random

# Scope needed for comments
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def get_authenticated_service():
    # Load credentials from Environment Variables
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        print("Missing YouTube API Credentials.")
        return None

    creds = Credentials(
        None, 
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def engage_with_latest_video():
    youtube = get_authenticated_service()
    if not youtube:
        return

    try:
        # 1. Get Channel's Uploads Playlist
        channels_response = youtube.channels().list(
            mine=True,
            part="contentDetails"
        ).execute()
        
        uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # 2. Get Latest Video
        playlist_items = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="snippet",
            maxResults=1
        ).execute()
        
        if not playlist_items["items"]:
            print("No videos found.")
            return

        latest_video_id = playlist_items["items"][0]["snippet"]["resourceId"]["videoId"]
        video_title = playlist_items["items"][0]["snippet"]["title"]
        print(f"Checking comments for: {video_title} ({latest_video_id})")
        
        # 3. Get Comments
        comments = youtube.commentThreads().list(
            part="snippet",
            videoId=latest_video_id,
            textFormat="plainText",
            maxResults=20,
            order="time"
        ).execute()
        
        for item in comments["items"]:
            comment = item["snippet"]["topLevelComment"]
            comment_id = comment["id"]
            author = comment["snippet"]["authorDisplayName"]
            text = comment["snippet"]["textDisplay"]
            
            # Skip if already replied (simple check: is_public check? API returns replies in item['replies'])
            if item["snippet"]["totalReplyCount"] > 0:
                continue # Already replied
                
            print(f"  Found new comment from {author}: {text}")
            
            # 4. Heart the Comment (Requires owner auth)
            # Note: The API for 'markAsSpam' or 'setModerationStatus' exists, but 'like' (rating) is for videos.
            # Comment rating: force-ssl scope allows 'setModerationStatus'. 'viewerRating' is read-only?
            # Actually, `comments.setModerationStatus` is for holding/publishing.
            # To HEART, we use `comments.markAsSpam`? No.
            # Official API doesn't expose "Heart" easily. It's an internal action?
            # We CAN Reply.
            
            # 5. Reply
            reply_text = generate_reply(text)
            youtube.comments().insert(
                part="snippet",
                body={
                    "snippet": {
                        "parentId": comment_id,
                        "textOriginal": reply_text
                    }
                }
            ).execute()
            print(f"    Replied: {reply_text}")
            
            # Reply to max 3 comments per run to look natural
            break 
            
    except Exception as e:
        print(f"Engagement Error: {e}")

def generate_reply(user_comment):
    responses = [
        "Thanks for watching! 🚀",
        "Glad you enjoyed it! What should we cover next? 🤔",
        "Appreciate the support! 🔥",
        "💯 Great point!",
        "Stay tuned for more! 👀"
    ]
    return random.choice(responses)

if __name__ == "__main__":
    engage_with_latest_video()
