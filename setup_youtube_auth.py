import os
import google_auth_oauthlib.flow
from dotenv import load_dotenv

def get_authenticated_service():
    load_dotenv()
    
    print("YouTube API Refresh Token Generator - MEME WORKFLOW (yoDailyMemeDose)")
    print("-----------------------------------")
    print("IMPORTANT: We are generating a token for the MEME channel.")
    print("This token will unlock Views Analytics and Comment Pinning.")
    print("-----------------------------------")
    
    client_id = input("Enter your MEME YouTube Client ID: ").strip()
    client_secret = input("Enter your MEME YouTube Client Secret: ").strip()
        
    if not client_id or not client_secret:
        print("Error: Client ID and Client Secret are required.")
        return

    # Create a temporary client_secrets.json for the flow
    import json
    client_config = {
        "installed": {
            "client_id": client_id,
            "project_id": "youtube-automation", # Placeholder, doesn't really matter for this flow
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open("temp_client_secrets.json", "w") as f:
        json.dump(client_config, f)
        
    scopes = [
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/yt-analytics.readonly"
    ]
    
    try:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            "temp_client_secrets.json", scopes)
        
        # Use run_local_server for a local browser flow
        # This will open a window in the default browser
        credentials = flow.run_local_server(port=0)
        
        print("\nSUCCESS! Authentication complete.")
        print("-" * 60)
        print(f"Refresh Token: {credentials.refresh_token}")
        print("-" * 60)
        print("Please update your GitHub Repository Secrets with this token.")
        print("Secret Name: YOUTUBE_REFRESH_TOKEN (or CURIOSITY_REFRESH_TOKEN)")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        
    finally:
        if os.path.exists("temp_client_secrets.json"):
            os.remove("temp_client_secrets.json")

if __name__ == "__main__":
    get_authenticated_service()
    input("\nPress Enter to exit...")
