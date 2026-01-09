import os
import google_auth_oauthlib.flow

# Scopes: Upload + Manager (Force SSL)
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

def main():
    print("--- YouTube Engagement Auth Setup ---")
    print("This script will generate a new Refresh Token with 'force-ssl' scope.")
    print("This allows the bot to Comment and Heart comments.")
    
    client_id = input("Enter Client ID: ").strip()
    client_secret = input("Enter Client Secret: ").strip()
    
    # Create client config
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"]
        }
    }
    
    # Create temp file
    import json
    with open("client_secrets_temp.json", "w") as f:
        json.dump(client_config, f)
        
    try:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            "client_secrets_temp.json", SCOPES)
        
        creds = flow.run_local_server(port=8080, prompt='consent')
        
        print("\n\nSUCCESS! New Credentials:")
        print(f"YOUTUBE_REFRESH_TOKEN: {creds.refresh_token}")
        print("\nACTION REQUIRED: Update this Secret in GitHub Settings.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists("client_secrets_temp.json"):
            os.remove("client_secrets_temp.json")

if __name__ == "__main__":
    main()
