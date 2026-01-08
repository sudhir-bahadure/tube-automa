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

def get_channel_handle(youtube):
    """Fetches the handle (@name) of the authenticated channel."""
    try:
        request = youtube.channels().list(
            part="snippet",
            mine=True
        )
        response = request.execute()
        if "items" in response and len(response["items"]) > 0:
            snippet = response["items"][0]["snippet"]
            # Handle can be in customUrl or title
            handle = snippet.get("customUrl") or snippet.get("title")
            return handle.lower()
    except Exception as e:
        print(f"[WARN] Could not fetch channel identity: {e}")
    return "unknown"

def upload_video(file_path, title, description, tags, category_id="27", thumbnail_path=None, mode="unknown"):
    """
    Uploads a video to YouTube.
    category_id "27" is Education. "28" is Science & Tech.
    """
    
    youtube = get_authenticated_service()
    if not youtube:
        return False
        
    # --- MULTI-ACCOUNT STRUCTURAL LOCKDOWN (Scoped Version) ---
    print("[*] VERSION: Structural Isolation v3.0 (Locked Refinement)")
    try:
        from datetime import datetime
        current_date = datetime.now()
        activation_date = datetime(2026, 1, 11)
        
        # Identity Investigation
        current_handle = get_channel_handle(youtube)
        expected_handle = os.environ.get("EXPECTED_HANDLE", "").lower()
        
        target_channel_env = os.environ.get("TARGET_CHANNEL")
        workflow_name = os.environ.get("GITHUB_WORKFLOW", "manual_run")
        
        print(f"[*] Identity Investigation:")
        print(f"    Authenticated as: {current_handle}")
        print(f"    Expected Handle:  {expected_handle if expected_handle else 'No restriction'}")
        
        # IDENTITY GUARD: Hard Block if handles don't match
        if expected_handle and expected_handle not in current_handle:
            print(f"\n[SECURITY BLOCK] IDENTITY MISMATCH DETECTED!")
            print(f"       ERROR: The provided credentials belong to '{current_handle}'.")
            print(f"       REQUIRED: '{expected_handle}'.")
            print(f"       ACTION: Upload Terminated to prevent cross-channel leak.")
            return None
        
        # Verify identity intent (Logical separation)
        is_curiobyte_intent = (target_channel_env == "curiosity")
        
        if is_curiobyte_intent:
            # RULE: CurioByte ONLY allows 'curiosity' mode
            if mode != "curiosity":
                print(f"\n[SECURITY BLOCK] Intent Mismatch!")
                print(f"       Account: CurioByte (@CurioByte143)")
                print(f"       ERROR: CurioByte MUST ONLY receive curiosity content.")
                print(f"       ATTEMPTED: '{mode}' mode.")
                print(f"       ACTION: Upload Terminated structurally.")
                return None
            
            # Whitelist: Only "Daily Curiosity Shorts Uploader" before activation
            if current_date < activation_date:
                if "Curiosity" not in workflow_name and workflow_name != "manual_run":
                    print(f"\n[SECURITY BLOCK] SOURCE Whitelist Failure!")
                    print(f"       ERROR: Only 'Daily Curiosity Shorts Uploader' permitted before Jan 11, 2026.")
                    return None

            # Shorts Duration Lock for CurioByte
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(file_path)
            duration = clip.duration
            clip.close()
            
            # Refinement 7: Long-form activation check
            if duration > 60:
                if current_date < activation_date:
                    print(f"\n[SECURITY BLOCK] Policy Violation: Long-form content DISABLED for CurioByte until Jan 11, 2026.")
                    return None
                else:
                    print(f"[*] [POLICY] Long-form content enabled for CurioByte (Active since Jan 11, 2026).")
        else:
            # RULE: Old Channel MUST NOT receive 'curiosity' content
            if mode == "curiosity":
                print(f"\n[SECURITY BLOCK] Isolation Breach!")
                print(f"       Account: Old Channel (Non-CurioByte)")
                print(f"       ERROR: Curiosity content is structurally isolated to CurioByte.")
                print(f"       ACTION: Upload Terminated structurally.")
                return None

        print(f"[*] [GUARD] Identity Intent & Refinement Compliance Confirmed. Access Granted.")

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
            except googleapiclient.errors.HttpError as e:
                # Handle "Forbidden" error (likely missing phone verification for custom thumbnails)
                if e.resp.status == 403:
                    print(f"\n[INFO] Thumbnail skipped: Phone verification is required for custom thumbnails on new accounts.")
                    print(f"       Action: Please verify your phone number at youtube.com/verify to enable thumbnails.")
                else:
                    print(f"[WARN] Thumbnail upload failed (HTTP {e.resp.status}): {e}")
            except Exception as e:
                print(f"[WARN] Thumbnail upload failed: {e}")
                
        return video_id
        
    except Exception as e:
        # HUMAN FRIENDLY ERROR HANDLING
        error_str = str(e)
        if "uploadLimitExceeded" in error_str:
            print(f"\n[!] YOUTUBE LIMIT REACHED: The channel has hit its daily upload limit.")
            print(f"    ACTION: Video generated but NOT uploaded. Try again in 24 hours.")
            return False
        elif "quotaExceeded" in error_str:
            print(f"\n[!] API QUOTA EXCEEDED: The project has used all 10,000 units.")
            print(f"    ACTION: Quota resets at Midnight Pacific Time.")
            return False
            
        print(f"  [ERROR] Upload failed: {e}")
        return False
