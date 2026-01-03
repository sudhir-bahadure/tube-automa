import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]

def get_authenticated_service():
    # Load credentials from Environment Variables (GitHub Secrets)
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        print("Missing YouTube API Credentials. Skipping upload.")
        return None

    # Construct Credentials object from Refresh Token
    creds = Credentials(
        None, # access_token (will be refreshed)
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def upload_video(file_path, title, description, tags, category_id="27", thumbnail_path=None):
    """
    Uploads a video to YouTube.
    category_id "27" is Education. "28" is Science & Tech.
    """
    youtube = get_authenticated_service()
    if not youtube:
        return False
        
    print(f"Uploading to YouTube: {title}")
    
    body = {
        "snippet": {
            "title": title[:100], # Max 100 chars
            "description": description[:5000], # Max 5000 chars
            "tags": tags.split(), # List of strings
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": "public", # 'private', 'unlisted', or 'public'
            "selfDeclaredMadeForKids": False
        }
    }
    
    try:
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")
        
        print(f"Upload Complete! Video ID: {response.get('id')}")
        video_id = response.get('id')
        
        # 4. Upload Thumbnail if provided
        if video_id and thumbnail_path and os.path.exists(thumbnail_path):
            try:
                print(f"[*] Uploading Thumbnail: {thumbnail_path}")
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                print("[SUCCESS] Thumbnail uploaded!")
            except Exception as e:
                print(f"[WARN] Thumbnail upload failed: {e}")
                
        return video_id
        
    except googleapiclient.errors.HttpError as e:
        print(f"An HTTP error occurred: {e.resp.status} {e.content}")
        return None
    except Exception as e:
        print(f"Upload Failed: {e}")
        return None
