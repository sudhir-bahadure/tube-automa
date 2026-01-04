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

def upload_video(file_path, title, description, tags, category_id="27", thumbnail_path=None, mode="unknown"):
    """
    Uploads a video to YouTube.
    category_id "27" is Education. "28" is Science & Tech.
    """
    
    youtube = get_authenticated_service()
    if not youtube:
        return False
        
    # --- MULTI-ACCOUNT STRUCTURAL LOCKDOWN (Scoped Version) ---
    print("[*] VERSION: Structural Isolation v2.2 (Scoped)")
    try:
        # Since 'youtube.upload' scope does not allow channels().list,
        # we identify the target account via safe Environment Verification.
        
        target_channel_env = os.environ.get("TARGET_CHANNEL")
        workflow_name = os.environ.get("GITHUB_WORKFLOW", "manual_run")
        
        # Verify identity intent
        is_curiobyte_intent = (target_channel_env == "curiosity")
        
        print(f"[*] Target intent: {'CurioByte' if is_curiobyte_intent else 'Old Channel'}")
        
        if is_curiobyte_intent:
            # RULE: CurioByte ONLY allows 'curiosity' mode and Shorts duration
            if mode != "curiosity":
                print(f"\n[SECURITY BLOCK] Intent Mismatch!")
                print(f"       Account: CurioByte (sudhirmturk@gmail.com)")
                print(f"       ERROR: CurioByte MUST ONLY receive curiosity content.")
                print(f"       ATTEMPTED: '{mode}' from '{workflow_name}'.")
                print(f"       ACTION: Upload Terminated structurally.")
                return None
            
            # Verifying source workflow (Curiositiy operations must come from Curiosity workflow)
            if "Curiosity" not in workflow_name and workflow_name != "manual_run":
                print(f"\n[SECURITY BLOCK] SOURCE Mismatch!")
                print(f"       ERROR: Curiosity uploads must come from the Whitelisted Curiosity Workflow.")
                return None

            # Shorts Duration Lock for CurioByte
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(file_path)
            duration = clip.duration
            clip.close()
            if duration > 60:
                print(f"\n[SECURITY BLOCK] Policy Violation: Non-Shorts content blocked for CurioByte.")
                return None
        else:
            # RULE: Old Channel MUST NOT receive 'curiosity' content
            if mode == "curiosity":
                print(f"\n[SECURITY BLOCK] Intent Mismatch!")
                print(f"       Account: Old Channel (sudhirt.bahadure@gmail.com)")
                print(f"       ERROR: Curiosity content must NOT go to the old channel.")
                print(f"       ACTION: Upload Terminated structurally.")
                return None

        print(f"[*] [GUARD] Identity Intent Confirmed. Access Granted.")

    except Exception as e:
        print(f"  [CRITICAL] Architectural Guard failure: {e}")
        print(f"  [ACTION] Safety Abort to prevent accidental upload.")
        return None
    # --- END STRUCTURAL LOCKDOWN ---      
    if not youtube: # This line was duplicated in the original, keeping it as is.
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
