import os
import google_auth_oauthlib.flow

# Scopes: Upload is main requirement
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    print("--- New Channel (Curiosity) Auth Setup ---")
    print("This script will generate a Refresh Token for your SECOND channel.")
    
    # Pre-fill client ID if user wants, but better to ask
    default_client_id = "134780437780-fnvpe4bqc11s6k9648cbcr0cibj9qc7f.apps.googleusercontent.com"
    print(f"Default Client ID: {default_client_id}")
    
    client_id = input(f"Enter Client ID [Press Enter to use Default]: ").strip()
    if not client_id:
        client_id = default_client_id
        
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
    
    import json
    with open("client_secrets_new.json", "w") as f:
        json.dump(client_config, f)
        
    try:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            "client_secrets_new.json", SCOPES)
        
        creds = flow.run_local_server(port=8080, prompt='consent')
        
        print("\n\nSUCCESS! Copy these values to GitHub Secrets:")
        print("--------------------------------------------------")
        print(f"NEW_CHANNEL_CLIENT_ID:     {client_id}")
        print(f"NEW_CHANNEL_CLIENT_SECRET: {client_secret}")
        print(f"NEW_CHANNEL_REFRESH_TOKEN: {creds.refresh_token}")
        print("--------------------------------------------------")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists("client_secrets_new.json"):
            os.remove("client_secrets_new.json")

if __name__ == "__main__":
    main()
